"""Datos del dashboard: la fuente activa (ejemplo o CSV subidos) y los cálculos en caché."""

import hashlib
import io
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from estaciones import almacen, analisis, geo, prediccion
from estaciones.excepciones import DatosNoValidos
from estaciones.red import RedEstaciones

CARPETA_DATOS = Path(__file__).parent.parent.parent / "datos"
PASO_REJILLA = 0.1
NOMBRE_EJEMPLO = "Datos de ejemplo · septiembre-noviembre 2026"


@dataclass
class Datos:
    """Todo lo que necesitan las páginas sobre la fuente de datos activa."""

    clave: str
    nombre: str
    red: RedEstaciones
    tabla: pd.DataFrame

    @property
    def primer_dia(self) -> date:
        return self.tabla["fecha_hora"].min().date()

    @property
    def ultimo_dia(self) -> date:
        return self.tabla["fecha_hora"].max().date()

    @property
    def ultimo_momento(self) -> datetime:
        return self.tabla["fecha_hora"].max().to_pydatetime()


def _texto(contenido: bytes) -> io.StringIO:
    """Bytes de un CSV subido como texto listo para ``csv``; admite UTF-8 con BOM (Excel)."""
    return io.StringIO(contenido.decode("utf-8-sig"), newline="")


@st.cache_resource(max_entries=4, show_spinner="Cargando la red de estaciones…")
def _preparar(clave: str, nombre: str, _estaciones: bytes | None,
              _mediciones: bytes | None) -> Datos:
    """Carga la red y construye la tabla. ``clave`` identifica la fuente en la caché."""
    if _estaciones is None:
        red = almacen.cargar_red(CARPETA_DATOS / "estaciones.csv",
                                 CARPETA_DATOS / "mediciones.csv")
    else:
        red = almacen.red_desde(almacen.leer_estaciones(_texto(_estaciones)),
                                almacen.leer_mediciones(_texto(_mediciones)))
    tabla = analisis.a_tabla(red.mediciones(), list(red))
    if tabla.empty:
        raise DatosNoValidos("No hay ninguna medición")
    return Datos(clave, nombre, red, tabla)


def actuales() -> Datos:
    """Los datos de la fuente activa."""
    fuente = st.session_state.get("fuente")
    if fuente is None:
        return _preparar("ejemplo", NOMBRE_EJEMPLO, None, None)
    return _preparar(fuente["clave"], fuente["nombre"], fuente["estaciones"],
                     fuente["mediciones"])


def usar_ficheros(estaciones: bytes, mediciones: bytes, nombre: str) -> Datos:
    """Valida y activa unos CSV subidos. Lanza ``ErrorDeEstaciones`` si no valen."""
    clave = hashlib.sha1(estaciones + b"|" + mediciones).hexdigest()[:12]
    datos = _preparar(clave, nombre, estaciones, mediciones)
    st.session_state["fuente"] = {"clave": clave, "nombre": nombre,
                                  "estaciones": estaciones, "mediciones": mediciones}
    colocar_momento(datos, forzar=True)
    return datos


def usar_ejemplo() -> None:
    """Vuelve a los datos de ejemplo."""
    st.session_state.pop("fuente", None)
    colocar_momento(actuales(), forzar=True)


def colocar_momento(datos: Datos, forzar: bool = False) -> None:
    """Pone el día y la hora elegidos dentro del periodo de los datos."""
    dia = st.session_state.get("dia")
    if forzar or dia is None or not datos.primer_dia <= dia <= datos.ultimo_dia:
        # Un día reciente: 20 antes del final (o el primero, si el periodo es corto)
        st.session_state["dia"] = max(datos.primer_dia, datos.ultimo_dia - timedelta(days=20))
        st.session_state["hora"] = 8


def momento() -> datetime:
    """La fecha y hora elegidas en el centro de control."""
    return datetime.combine(st.session_state["dia"], time(st.session_state["hora"]))


def valores(datos: Datos, variable: str, cuando: datetime) -> dict[str, float]:
    """El valor de cada estación a una hora; las que no tienen dato no aparecen."""
    filas = analisis.en_momento(datos.tabla, cuando).dropna(subset=[variable])
    return dict(zip(filas["codigo"], filas[variable]))


# --- Cálculos pesados en caché ------------------------------------------------

@st.cache_data
def contorno() -> list[list[tuple[float, float]]]:
    """Polígonos simplificados de la península, Baleares y Canarias."""
    return almacen.cargar_contorno(CARPETA_DATOS / "espana_contorno.geojson")


@st.cache_data
def puntos_tierra() -> list[tuple[float, float]]:
    """Centros de las celdas de la rejilla que caen dentro de España."""
    return geo.rejilla_en_tierra(contorno(), PASO_REJILLA)


@st.cache_data(max_entries=600)
def superficie(muestras: tuple[tuple[float, float, float], ...]) -> pd.DataFrame:
    """Valor interpolado por IDW en cada celda de tierra a partir de ``(lat, lon, valor)``.

    Es la misma cuenta que ``geo.rejilla_idw`` (haversine y pesos 1/d²), pero con
    NumPy para todas las celdas a la vez: con 60 estaciones y unas 5 400 celdas,
    la versión a mano tarda más de un segundo por hora y esta, milésimas.
    """
    celdas = np.radians(np.array(puntos_tierra()))
    estaciones = np.array(muestras)
    lat1, lon1 = celdas[:, [0]], celdas[:, [1]]
    lat2, lon2 = np.radians(estaciones[:, 0]), np.radians(estaciones[:, 1])
    a = (np.sin((lat2 - lat1) / 2) ** 2
         + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2)
    distancia = 2 * geo.RADIO_TIERRA_KM * np.arcsin(np.sqrt(a))
    # Distancia 0 da peso infinito (y 0/0 en esa fila): esa celda se corrige justo después
    with np.errstate(divide="ignore", invalid="ignore"):
        pesos = 1 / distancia ** 2
        valor = (pesos * estaciones[:, 2]).sum(axis=1) / pesos.sum(axis=1)
    # Una celda que coincide con una estación toma su valor, como en geo.idw
    coincide = distancia == 0
    if coincide.any():
        filas, columnas = np.nonzero(coincide)
        valor[filas] = estaciones[columnas, 2]
    grados = np.degrees(celdas)
    return pd.DataFrame({"lat": grados[:, 0], "lon": grados[:, 1], "valor": valor})


@st.cache_data(max_entries=60)
def prevision(clave: str, variable: str, desde: datetime, horas: int,
              _tabla: pd.DataFrame) -> pd.DataFrame:
    """Predicción de las ``horas`` siguientes a ``desde`` para todas las estaciones."""
    return prediccion.predecir(prediccion.ajustar(_tabla, variable, desde), horas)


@st.cache_data(max_entries=20)
def validacion(clave: str, variable: str, _tabla: pd.DataFrame) -> pd.DataFrame:
    """Error medio por horizonte del modelo y de las dos referencias."""
    return prediccion.validar(_tabla, variable)
