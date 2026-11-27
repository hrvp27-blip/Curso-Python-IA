"""La red de estaciones: consultas espaciales sobre el conjunto (hito 2)."""

from collections import Counter
from datetime import datetime

from . import geo
from .excepciones import DatosNoValidos, EstacionNoEncontrada
from .modelos import VARIABLES, Estacion, Medicion


class RedEstaciones:
    """Conjunto de estaciones, guardadas por código, con sus mediciones."""

    def __init__(self, estaciones: list[Estacion] | None = None):
        """Crea la red, opcionalmente con una lista inicial de estaciones."""
        self._estaciones: dict[str, Estacion] = {}
        self._mediciones: list[Medicion] = []
        for estacion in estaciones or []:
            self.anadir(estacion)

    def __len__(self) -> int:
        """Número de estaciones de la red."""
        return len(self._estaciones)

    def __iter__(self):
        """Recorre las estaciones ordenadas por código."""
        return iter(sorted(self._estaciones.values(), key=lambda estacion: estacion.codigo))

    def anadir(self, estacion: Estacion) -> None:
        """Añade una estación. Lanza ``DatosNoValidos`` si el código ya existe."""
        if estacion.codigo in self._estaciones:
            raise DatosNoValidos(f"Ya existe la estación {estacion.codigo}")
        self._estaciones[estacion.codigo] = estacion

    def obtener(self, codigo: str) -> Estacion:
        """Devuelve la estación con ese código (sin distinguir mayúsculas) o lanza ``EstacionNoEncontrada``."""
        try:
            return self._estaciones[codigo.strip().upper()]
        except KeyError as error:
            raise EstacionNoEncontrada(codigo) from error

    def registrar(self, medicion: Medicion) -> None:
        """Guarda una medición. Lanza ``EstacionNoEncontrada`` si su estación no está en la red."""
        self.obtener(medicion.codigo)
        self._mediciones.append(medicion)

    def mediciones(self, codigo: str | None = None) -> list[Medicion]:
        """Mediciones de una estación, o de todas si ``codigo`` es None, ordenadas por fecha.

        Lanza ``EstacionNoEncontrada`` si el código no existe.
        """
        if codigo is not None:
            codigo = self.obtener(codigo).codigo
        elegidas = [m for m in self._mediciones if codigo is None or m.codigo == codigo]
        return sorted(elegidas, key=lambda medicion: medicion.fecha_hora)

    def cercanas(self, lat: float, lon: float, radio_km: float) -> list[tuple[Estacion, float]]:
        """Estaciones a ``radio_km`` o menos del punto, como ``(estacion, distancia)`` de la más cercana a la más lejana."""
        geo.validar_coordenada(lat, lon)
        distancias = [(estacion, estacion.distancia_a(lat, lon)) for estacion in self]
        return sorted([par for par in distancias if par[1] <= radio_km], key=lambda par: par[1])

    def mas_cercana(self, lat: float, lon: float) -> tuple[Estacion, float]:
        """La estación más cercana al punto y su distancia. Lanza ``DatosNoValidos`` si la red está vacía."""
        geo.validar_coordenada(lat, lon)
        if not self._estaciones:
            raise DatosNoValidos("La red no tiene estaciones")
        return min(((estacion, estacion.distancia_a(lat, lon)) for estacion in self),
                   key=lambda par: par[1])

    def en_zona(self, caja: tuple[float, float, float, float]) -> list[Estacion]:
        """Estaciones dentro de la caja ``(lat_min, lon_min, lat_max, lon_max)``, ordenadas por código."""
        return [estacion for estacion in self if geo.en_caja(estacion.lat, estacion.lon, caja)]

    def por_provincia(self) -> dict[str, int]:
        """Cuántas estaciones hay en cada provincia."""
        return dict(Counter(estacion.provincia for estacion in self))

    def muestras(self, variable: str, momento: datetime) -> list[tuple[float, float, float]]:
        """Los ``(lat, lon, valor)`` de las estaciones con dato de ``variable`` a la hora ``momento``.

        Lanza ``DatosNoValidos`` si la variable no existe.
        """
        if variable not in VARIABLES:
            raise DatosNoValidos(f"Variable no válida: {variable}")
        return [(*self._estaciones[m.codigo].coordenadas, getattr(m, variable))
                for m in self._mediciones
                if m.fecha_hora == momento and getattr(m, variable) is not None]

    def estimar(self, lat: float, lon: float, variable: str, momento: datetime) -> float:
        """Estima ``variable`` en el punto a la hora ``momento`` interpolando por IDW las estaciones con dato.

        Lanza ``DatosNoValidos`` si la variable no existe o ninguna estación
        tiene dato a esa hora.
        """
        geo.validar_coordenada(lat, lon)
        muestras = self.muestras(variable, momento)
        if not muestras:
            raise DatosNoValidos(f"No hay datos de {variable} el {momento:%d/%m/%Y a las %H:%M}")
        return geo.idw(lat, lon, muestras)
