"""Cálculos geográficos sobre coordenadas WGS84 (grados decimales).

Todo está programado a mano con ``math``, sin librerías GIS: la Tierra se
trata como una esfera de radio ``RADIO_TIERRA_KM``. Para distancias dentro de
España el error frente al elipsoide es menor del 0,5 %.
"""

from math import asin, atan2, cos, degrees, floor, radians, sin, sqrt

from .excepciones import CoordenadaNoValida, DatosNoValidos

RADIO_TIERRA_KM = 6371.0
PUNTOS_CARDINALES = ("N", "NE", "E", "SE", "S", "SO", "O", "NO")


def validar_coordenada(lat: float, lon: float) -> None:
    """Lanza ``CoordenadaNoValida`` si la latitud no está en [-90, 90] o la longitud en [-180, 180]."""
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise CoordenadaNoValida(lat, lon)


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distancia en kilómetros entre dos puntos siguiendo la superficie terrestre.

    >>> round(haversine(0, 0, 0, 1), 2)
    111.19
    """
    fi1, fi2 = radians(lat1), radians(lat2)
    incremento_fi = radians(lat2 - lat1)
    incremento_lambda = radians(lon2 - lon1)
    a = sin(incremento_fi / 2) ** 2 + cos(fi1) * cos(fi2) * sin(incremento_lambda / 2) ** 2
    return 2 * RADIO_TIERRA_KM * asin(sqrt(a))


def rumbo(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Rumbo inicial en grados [0, 360) para ir del punto 1 al punto 2. 0 es el norte, 90 el este.

    >>> rumbo(0, 0, 1, 0), rumbo(0, 0, 0, 1)
    (0.0, 90.0)
    """
    fi1, fi2 = radians(lat1), radians(lat2)
    incremento_lambda = radians(lon2 - lon1)
    x = sin(incremento_lambda) * cos(fi2)
    y = cos(fi1) * sin(fi2) - sin(fi1) * cos(fi2) * cos(incremento_lambda)
    return (degrees(atan2(x, y)) + 360) % 360


def a_sexagesimal(grados: float, es_latitud: bool) -> str:
    """Convierte grados decimales en grados, minutos y segundos con su hemisferio.

    >>> a_sexagesimal(40.4215, True), a_sexagesimal(-3.6823, False)
    ('40° 25′ 17″ N', '3° 40′ 56″ O')
    """
    hemisferio = ("N" if grados >= 0 else "S") if es_latitud else ("E" if grados >= 0 else "O")
    segundos_totales = round(abs(grados) * 3600)
    minutos_totales, segundos = divmod(segundos_totales, 60)
    enteros, minutos = divmod(minutos_totales, 60)
    return f"{enteros}° {minutos:02d}′ {segundos:02d}″ {hemisferio}"


def punto_cardinal(grados: float) -> str:
    """Convierte un rumbo en grados en uno de los ocho puntos de ``PUNTOS_CARDINALES``.

    >>> punto_cardinal(10), punto_cardinal(100), punto_cardinal(350)
    ('N', 'E', 'N')
    """
    return PUNTOS_CARDINALES[int(grados / 45 + 0.5) % 8]


def centroide(puntos: list[tuple[float, float]]) -> tuple[float, float]:
    """Media de las latitudes y de las longitudes de una lista de puntos ``(lat, lon)``.

    Es una aproximación válida para zonas del tamaño de un país. Lanza
    ``DatosNoValidos`` si la lista está vacía.
    """
    if not puntos:
        raise DatosNoValidos("No hay puntos para calcular el centroide")
    latitudes, longitudes = zip(*puntos)
    return sum(latitudes) / len(latitudes), sum(longitudes) / len(longitudes)


def en_caja(lat: float, lon: float, caja: tuple[float, float, float, float]) -> bool:
    """Indica si el punto cae dentro de la caja ``(lat_min, lon_min, lat_max, lon_max)``, bordes incluidos."""
    lat_min, lon_min, lat_max, lon_max = caja
    return lat_min <= lat <= lat_max and lon_min <= lon <= lon_max


def idw(lat: float, lon: float, muestras: list[tuple[float, float, float]],
        potencia: float = 2) -> float:
    """Interpola un valor en ``(lat, lon)`` por inverso de la distancia (IDW).

    ``muestras`` es una lista de ``(lat, lon, valor)``. Cada muestra pesa
    ``1 / distancia ** potencia``: las cercanas influyen más. Si el punto
    coincide con una muestra, devuelve su valor. Lanza ``DatosNoValidos`` si
    no hay muestras.
    """
    pesos = []
    for muestra_lat, muestra_lon, valor in muestras:
        distancia = haversine(lat, lon, muestra_lat, muestra_lon)
        if distancia == 0:
            return valor
        pesos.append((1 / distancia ** potencia, valor))
    if not pesos:
        raise DatosNoValidos("No hay muestras para interpolar")
    total = sum(peso for peso, _ in pesos)
    return sum(peso * valor for peso, valor in pesos) / total


def punto_en_poligono(lat: float, lon: float, anillo: list[tuple[float, float]]) -> bool:
    """Indica si el punto está dentro del polígono ``anillo`` (vértices ``(lon, lat)`` como en GeoJSON).

    Algoritmo de lanzamiento de rayo: se traza una semirrecta hacia el este
    desde el punto y se cuentan los lados que corta. Si el número es impar,
    el punto está dentro.

    >>> cuadrado = [(0, 0), (2, 0), (2, 2), (0, 2)]
    >>> punto_en_poligono(1, 1, cuadrado), punto_en_poligono(3, 1, cuadrado)
    (True, False)
    """
    dentro = False
    for (x1, y1), (x2, y2) in zip(anillo, [*anillo[1:], anillo[0]]):
        if (y1 > lat) != (y2 > lat):
            corte = x1 + (lat - y1) * (x2 - x1) / (y2 - y1)
            if lon < corte:
                dentro = not dentro
    return dentro


def caja_de(anillo: list[tuple[float, float]]) -> tuple[float, float, float, float]:
    """La caja ``(lat_min, lon_min, lat_max, lon_max)`` que envuelve un polígono ``(lon, lat)``."""
    longitudes, latitudes = zip(*anillo)
    return min(latitudes), min(longitudes), max(latitudes), max(longitudes)


def en_tierra(lat: float, lon: float, poligonos: list[list[tuple[float, float]]]) -> bool:
    """Indica si el punto cae dentro de alguno de los ``poligonos``.

    Antes del cálculo completo descarta los polígonos cuya caja no contiene
    el punto, que es mucho más rápido.
    """
    return any(en_caja(lat, lon, caja_de(anillo)) and punto_en_poligono(lat, lon, anillo)
               for anillo in poligonos)


def rejilla(caja: tuple[float, float, float, float], paso: float) -> list[tuple[float, float]]:
    """Puntos ``(lat, lon)`` de una rejilla regular separados ``paso`` grados dentro de ``caja``."""
    lat_min, lon_min, lat_max, lon_max = caja
    filas = int((lat_max - lat_min) / paso) + 1
    columnas = int((lon_max - lon_min) / paso) + 1
    return [(round(lat_min + fila * paso, 6), round(lon_min + columna * paso, 6))
            for fila in range(filas) for columna in range(columnas)]


def rejilla_en_tierra(poligonos: list[list[tuple[float, float]]],
                      paso: float) -> list[tuple[float, float]]:
    """Los puntos de una rejilla de ``paso`` grados que caen dentro de los ``poligonos``.

    La rejilla de cada polígono empieza en un múltiplo de ``paso``, así todas
    las celdas encajan entre sí.
    """
    resultado = []
    for anillo in poligonos:
        lat_min, lon_min, lat_max, lon_max = caja_de(anillo)
        alineada = (floor(lat_min / paso) * paso, floor(lon_min / paso) * paso, lat_max, lon_max)
        resultado += [(lat, lon) for lat, lon in rejilla(alineada, paso)
                      if punto_en_poligono(lat, lon, anillo)]
    return resultado


def rejilla_idw(muestras: list[tuple[float, float, float]], puntos: list[tuple[float, float]],
                potencia: float = 2) -> list[tuple[float, float, float]]:
    """Interpola por IDW cada punto ``(lat, lon)`` y devuelve ``(lat, lon, valor)``."""
    return [(lat, lon, idw(lat, lon, muestras, potencia)) for lat, lon in puntos]
