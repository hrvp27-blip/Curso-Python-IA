"""Modelo de dominio: las estaciones de medición y sus mediciones."""

from bisect import bisect_left
from dataclasses import dataclass
from datetime import datetime

from . import geo
from .excepciones import DatosNoValidos

CAMPOS_ESTACION = ["codigo", "nombre", "provincia", "lat", "lon", "altitud"]
CAMPOS_MEDICION = ["codigo", "fecha_hora", "temperatura", "humedad", "pm25", "no2"]
VARIABLES = ("temperatura", "humedad", "pm25", "no2")
CONTAMINANTES = ("pm25", "no2")

# Valores guía de la OMS (2021) para la media de 24 horas, en µg/m³
UMBRALES_OMS = {"pm25": 15, "no2": 25}

# Índice Nacional de Calidad del Aire (ICA) del MITECO, igual que el índice
# europeo de la AEMA. Límites superiores de cada categoría en µg/m³; por
# encima del último, "Extremadamente desfavorable".
CATEGORIAS_ICA = ("Buena", "Razonablemente buena", "Regular", "Desfavorable",
                  "Muy desfavorable", "Extremadamente desfavorable")
LIMITES_ICA = {
    "no2": (40, 90, 120, 230, 340),
    "pm25": (10, 20, 25, 50, 75),
}

# Rangos físicamente posibles: fuera de ellos la lectura es un error del sensor
RANGOS = {
    "temperatura": (-50, 60),
    "humedad": (0, 100),
    "pm25": (0, 1000),
    "no2": (0, 1000),
}


def categoria_ica(contaminante: str, valor: float) -> str:
    """Categoría del ICA para un valor del contaminante; cada límite pertenece a su categoría.

    El ICA oficial usa medias móviles para las partículas; aquí se aplica al
    valor que se le pase. Lanza ``DatosNoValidos`` si el contaminante no tiene ICA.

    >>> categoria_ica("no2", 40), categoria_ica("no2", 40.1), categoria_ica("pm25", 80)
    ('Buena', 'Razonablemente buena', 'Extremadamente desfavorable')
    """
    if contaminante not in LIMITES_ICA:
        raise DatosNoValidos(f"Contaminante no válido: {contaminante}")
    return CATEGORIAS_ICA[bisect_left(LIMITES_ICA[contaminante], valor)]


def _a_numero(texto: str) -> float | None:
    """Convierte una celda del CSV en número; la cadena vacía es un dato ausente."""
    return float(texto) if texto.strip() else None


def _a_texto(valor: float | None) -> str:
    """Convierte un número en celda del CSV; un dato ausente es la cadena vacía."""
    return "" if valor is None else str(valor)


@dataclass
class Estacion:
    """Una estación de medición situada en un punto (lat, lon) con su altitud en metros."""

    codigo: str
    nombre: str
    provincia: str
    lat: float
    lon: float
    altitud: float = 0.0

    def __post_init__(self):
        """Limpia los textos, pasa el código a mayúsculas y valida los datos.

        Lanza ``DatosNoValidos`` si falta el código, el nombre o la provincia,
        y ``CoordenadaNoValida`` si las coordenadas están fuera de rango.
        """
        self.codigo = self.codigo.strip().upper()
        self.nombre = self.nombre.strip()
        self.provincia = self.provincia.strip()
        for campo in ("codigo", "nombre", "provincia"):
            if not getattr(self, campo):
                raise DatosNoValidos(f"El campo {campo} es obligatorio")
        geo.validar_coordenada(self.lat, self.lon)

    @property
    def coordenadas(self) -> tuple[float, float]:
        """La posición de la estación como ``(lat, lon)``."""
        return self.lat, self.lon

    def distancia_a(self, lat: float, lon: float) -> float:
        """Distancia en kilómetros desde la estación hasta el punto ``(lat, lon)``."""
        return geo.haversine(self.lat, self.lon, lat, lon)

    def a_fila(self) -> dict[str, str]:
        """Devuelve la estación como diccionario de cadenas con las claves de ``CAMPOS_ESTACION``."""
        return {campo: str(getattr(self, campo)) for campo in CAMPOS_ESTACION}

    @classmethod
    def desde_fila(cls, fila: dict[str, str]) -> "Estacion":
        """Crea una estación a partir de un diccionario de cadenas como el de ``a_fila``.

        Lanza ``DatosNoValidos`` si falta una clave o un número no lo es,
        encadenando la excepción original.
        """
        try:
            lat, lon, altitud = float(fila["lat"]), float(fila["lon"]), float(fila["altitud"])
            codigo, nombre, provincia = fila["codigo"], fila["nombre"], fila["provincia"]
        except KeyError as error:
            raise DatosNoValidos(f"Falta el campo {error}") from error
        except ValueError as error:
            raise DatosNoValidos(f"Número no válido en la estación: {error}") from error
        return cls(codigo, nombre, provincia, lat, lon, altitud)


@dataclass
class Medicion:
    """Lo que mide una estación en un momento. Una variable puede faltar (``None``)."""

    codigo: str
    fecha_hora: datetime
    temperatura: float | None = None
    humedad: float | None = None
    pm25: float | None = None
    no2: float | None = None

    def __post_init__(self):
        """Pasa el código a mayúsculas y comprueba que cada valor presente está en ``RANGOS``.

        Lanza ``DatosNoValidos`` con el mensaje "El código de estación es
        obligatorio" o "<variable> fuera de rango: <valor>".
        """
        self.codigo = self.codigo.strip().upper()
        if not self.codigo:
            raise DatosNoValidos("El código de estación es obligatorio")
        for variable, (minimo, maximo) in RANGOS.items():
            valor = getattr(self, variable)
            if valor is not None and not minimo <= valor <= maximo:
                raise DatosNoValidos(f"{variable} fuera de rango: {valor}")

    def supera_umbral(self, contaminante: str) -> bool:
        """Indica si el valor horario del contaminante supera su umbral de la OMS.

        La guía de la OMS es para la media diaria, así que esto es solo un
        aviso horario; el cálculo diario se hace en ``analisis``. Un valor
        ausente no supera nada. Lanza ``DatosNoValidos`` si el contaminante no
        está en ``CONTAMINANTES``.
        """
        if contaminante not in CONTAMINANTES:
            raise DatosNoValidos(f"Contaminante no válido: {contaminante}")
        valor = getattr(self, contaminante)
        return valor is not None and valor > UMBRALES_OMS[contaminante]

    def a_fila(self) -> dict[str, str]:
        """Devuelve la medición como diccionario de cadenas con las claves de ``CAMPOS_MEDICION``.

        La fecha va en formato ISO (``2026-11-01T08:00``) y un valor ausente
        es la cadena vacía.
        """
        valores = {variable: _a_texto(getattr(self, variable)) for variable in VARIABLES}
        return {"codigo": self.codigo,
                "fecha_hora": self.fecha_hora.isoformat(timespec="minutes"),
                **valores}

    @classmethod
    def desde_fila(cls, fila: dict[str, str]) -> "Medicion":
        """Crea una medición a partir de un diccionario de cadenas como el de ``a_fila``.

        Lanza ``DatosNoValidos`` si falta una clave, la fecha no es ISO o un
        valor no es numérico, encadenando la excepción original.
        """
        try:
            fecha_hora = datetime.fromisoformat(fila["fecha_hora"])
            valores = {variable: _a_numero(fila[variable]) for variable in VARIABLES}
            codigo = fila["codigo"]
        except KeyError as error:
            raise DatosNoValidos(f"Falta el campo {error}") from error
        except ValueError as error:
            raise DatosNoValidos(f"Dato no válido en la medición: {error}") from error
        return cls(codigo, fecha_hora, **valores)
