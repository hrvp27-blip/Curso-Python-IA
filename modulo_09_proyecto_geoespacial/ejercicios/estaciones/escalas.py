"""Escalas de color oficiales de cada variable.

- NO₂ y PM2.5: las seis categorías y colores del Índice Nacional de Calidad
  del Aire (ICA) del MITECO, iguales a las del índice europeo de la AEMA.
- Temperatura y humedad: clases de 4 °C y de 10 % con colores al estilo de
  los mapas de AEMET.
"""

from bisect import bisect_left

from .excepciones import DatosNoValidos
from .modelos import CATEGORIAS_ICA, LIMITES_ICA, categoria_ica

COLORES_ICA = ("#50F0E6", "#50CCAA", "#F0E641", "#FF5050", "#960032", "#7D2181")

ESCALAS = {
    "no2": {
        "nombre": "NO₂", "unidad": "µg/m³", "cortes": LIMITES_ICA["no2"],
        "colores": COLORES_ICA, "etiquetas": CATEGORIAS_ICA, "rango": (0, 120),
        "fuente": "Índice Nacional de Calidad del Aire (MITECO)",
    },
    "pm25": {
        "nombre": "PM2.5", "unidad": "µg/m³", "cortes": LIMITES_ICA["pm25"],
        "colores": COLORES_ICA, "etiquetas": CATEGORIAS_ICA, "rango": (0, 50),
        "fuente": "Índice Nacional de Calidad del Aire (MITECO)",
    },
    "temperatura": {
        "nombre": "Temperatura", "unidad": "°C",
        "cortes": (-4, 0, 4, 8, 12, 16, 20, 24, 28, 32, 36),
        "colores": ("#5B2C83", "#3F51B5", "#1E88E5", "#29B6F6", "#4DD0E1", "#66BB6A",
                    "#C0CA33", "#FDD835", "#FFB300", "#FB8C00", "#E53935", "#8E0000"),
        "etiquetas": None, "rango": (-10, 40),
        "fuente": "Clases de 4 °C, colores al estilo de AEMET",
    },
    "humedad": {
        "nombre": "Humedad", "unidad": "%", "cortes": (20, 30, 40, 50, 60, 70, 80, 90),
        "colores": ("#8D5524", "#B07D3C", "#D4A656", "#E8D27A", "#B8DB8C", "#7CC6A8",
                    "#4FA8D1", "#2B7BC0", "#1A4C9C"),
        "etiquetas": None, "rango": (0, 100),
        "fuente": "Clases de 10 %, colores al estilo de AEMET",
    },
}


def escala(variable: str) -> dict:
    """La escala de una variable. Lanza ``DatosNoValidos`` si no existe."""
    try:
        return ESCALAS[variable]
    except KeyError as error:
        raise DatosNoValidos(f"Variable no válida: {variable}") from error


def indice_clase(variable: str, valor: float) -> int:
    """Posición de la clase del valor; cada corte pertenece a la clase de abajo.

    >>> indice_clase("no2", 40), indice_clase("no2", 41), indice_clase("temperatura", 19)
    (0, 1, 6)
    """
    return bisect_left(escala(variable)["cortes"], valor)


def color(variable: str, valor: float) -> str:
    """Color hexadecimal oficial de la clase del valor."""
    return escala(variable)["colores"][indice_clase(variable, valor)]


def rgb(color_hex: str) -> tuple[int, int, int]:
    """Convierte ``"#50F0E6"`` en ``(80, 240, 230)``.

    >>> rgb("#50F0E6")
    (80, 240, 230)
    """
    return tuple(int(color_hex[i:i + 2], 16) for i in (1, 3, 5))


FONDO = (11, 17, 32)


def limites_clase(variable: str, indice: int) -> tuple[float, float]:
    """Valores inicial y final de una clase; las abiertas se cierran con el ``rango`` de la escala."""
    datos = escala(variable)
    cortes = datos["cortes"]
    minimo, maximo = datos["rango"]
    inferior = cortes[indice - 1] if indice > 0 else min(minimo, cortes[0] - 1)
    superior = cortes[indice] if indice < len(cortes) else max(maximo, cortes[-1] + 1)
    return inferior, superior


def rgb_matizado(variable: str, valor: float) -> tuple[int, int, int]:
    """Color oficial de la clase, más oscuro en la parte baja de la clase y pleno en la alta.

    Así se ven las diferencias dentro de una misma clase (por ejemplo, entre
    10 y 35 µg/m³, ambos "Buena") sin cambiar el tono oficial.

    >>> rgb_matizado("no2", 40) == rgb(color("no2", 40))
    True
    """
    indice = indice_clase(variable, valor)
    inferior, superior = limites_clase(variable, indice)
    posicion = min(1.0, max(0.0, (valor - inferior) / (superior - inferior)))
    intensidad = 0.45 + 0.55 * posicion
    return tuple(round(f + (c - f) * intensidad)
                 for c, f in zip(rgb(escala(variable)["colores"][indice]), FONDO))


def etiquetas(variable: str) -> list[str]:
    """Nombre de cada clase: las categorías del ICA o los intervalos de la escala.

    >>> etiquetas("humedad")[:2], etiquetas("humedad")[-1]
    (['≤ 20', '20 a 30'], '> 90 %')
    """
    datos = escala(variable)
    if datos["etiquetas"]:
        return list(datos["etiquetas"])
    cortes = datos["cortes"]
    intermedias = [f"{a} a {b}" for a, b in zip(cortes, cortes[1:])]
    return [f"≤ {cortes[0]}", *intermedias, f"> {cortes[-1]} {datos['unidad']}"]


def clase(variable: str, valor: float) -> str:
    """Nombre de la clase del valor."""
    return etiquetas(variable)[indice_clase(variable, valor)]


def describir(variable: str, valor: float) -> str:
    """El valor con su unidad y, si es un contaminante, su categoría ICA.

    >>> describir("no2", 77.6), describir("temperatura", 9.04)
    ('77.6 µg/m³ · Razonablemente buena', '9.0 °C')
    """
    texto = f"{valor:.1f} {escala(variable)['unidad']}"
    if variable in LIMITES_ICA:
        return f"{texto} · {categoria_ica(variable, valor)}"
    return texto


def proporcion(variable: str, valor: float) -> float:
    """Posición del valor dentro del ``rango`` de la escala, entre 0 y 1."""
    minimo, maximo = escala(variable)["rango"]
    return min(1.0, max(0.0, (valor - minimo) / (maximo - minimo)))
