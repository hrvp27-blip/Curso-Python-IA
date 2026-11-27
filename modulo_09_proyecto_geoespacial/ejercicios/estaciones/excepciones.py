"""Excepciones de la red de estaciones.

Jerarquía:

    ErrorDeEstaciones (Exception)       base de todos los errores de la aplicación
    ├── DatosNoValidos                  un dato de una estación o medición no vale
    │   └── CoordenadaNoValida          latitud o longitud fuera de rango
    ├── EstacionNoEncontrada            no existe una estación con ese código
    └── ErrorDeAlmacen                  un fichero de datos no se puede leer

Al heredar todas de ``ErrorDeEstaciones``, el menú puede capturar cualquier
error de la aplicación con un solo ``except``.
"""


class ErrorDeEstaciones(Exception):
    """Base de todos los errores de la aplicación."""


class DatosNoValidos(ErrorDeEstaciones):
    """Un dato de una estación o de una medición no es válido."""


class CoordenadaNoValida(DatosNoValidos):
    """La latitud o la longitud están fuera de rango."""

    def __init__(self, lat, lon):
        super().__init__(f"Coordenada fuera de rango: lat={lat}, lon={lon}")
        self.lat = lat
        self.lon = lon


class EstacionNoEncontrada(ErrorDeEstaciones):
    """No existe una estación con el código indicado."""

    def __init__(self, codigo):
        super().__init__(f"No existe la estación {codigo}")
        self.codigo = codigo


class ErrorDeAlmacen(ErrorDeEstaciones):
    """Un fichero de datos no se puede leer."""
