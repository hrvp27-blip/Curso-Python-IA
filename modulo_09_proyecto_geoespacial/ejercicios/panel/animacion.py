"""Mapa animado de la reproducción: la interpolación entre horas la hace el navegador.

Con ``st.pydeck_chart`` cada hora nueva es un mapa nuevo que manda Python, y
eso se nota como un salto. Aquí el mapa recibe de una vez todas las horas del
periodo y, fotograma a fotograma, interpola los valores de las estaciones,
recalcula la superficie IDW y mueve las columnas (``recursos/mapa_animado.html``).

Python y el navegador usan el mismo reloj: la hora en curso es
``desde + segundos desde t0 / paso``. Así las tarjetas y el mapa van a la par.
"""

import json
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from estaciones import escalas

from . import capas
from . import datos as fuente

PLANTILLA = Path(__file__).parent.parent / "recursos" / "mapa_animado.html"


def horas_del_periodo(datos: fuente.Datos) -> pd.DatetimeIndex:
    """Todas las horas del periodo, de las 0:00 del primer día al último momento."""
    inicio = datetime.combine(datos.primer_dia, datetime.min.time())
    return pd.date_range(inicio, datos.ultimo_momento, freq="h")


def empezar(datos: fuente.Datos) -> None:
    """Pone en marcha el reloj de la reproducción desde la hora elegida."""
    horas = horas_del_periodo(datos)
    st.session_state["reproduccion"] = {
        "t0": time.time(), "desde": int(horas.get_indexer([fuente.momento()])[0]) % len(horas)}


def parar() -> None:
    """Detiene el reloj; la hora elegida se queda donde iba."""
    st.session_state.pop("reproduccion", None)


def sincronizar(datos: fuente.Datos) -> None:
    """Coloca el día y la hora elegidos en la hora que marca el reloj de la reproducción."""
    if "reproduccion" not in st.session_state:
        empezar(datos)
    reloj = st.session_state["reproduccion"]
    horas = horas_del_periodo(datos)
    indice = int(reloj["desde"] + (time.time() - reloj["t0"]) / capas.PASO_REPRODUCCION_S)
    actual = horas[indice % len(horas)]
    st.session_state["dia"], st.session_state["hora"] = actual.date(), actual.hour


@st.cache_data(max_entries=20)
def _valores(clave: str, variable: str, _datos: fuente.Datos) -> list[list[float | None]]:
    """Matriz hora x estación (en el orden de la red); ``None`` donde falta el dato."""
    codigos = [e.codigo for e in _datos.red]
    ancha = _datos.tabla.pivot_table(index="fecha_hora", columns="codigo", values=variable)
    ancha = ancha.reindex(index=horas_del_periodo(_datos), columns=codigos).round(1)
    return [[None if pd.isna(v) else float(v) for v in fila] for fila in ancha.to_numpy()]


def html(datos: fuente.Datos, variable: str, zona: str, exageracion: float, alto: int) -> str:
    """La página del mapa animado, con todos los datos dentro."""
    escala = escalas.escala(variable)
    vista = capas.vista_inclinada(capas.ZONAS[zona], alto=alto)
    reloj = st.session_state["reproduccion"]
    carga = {
        "estaciones": [{"nombre": e.nombre, "provincia": e.provincia, "lat": e.lat, "lon": e.lon}
                       for e in datos.red],
        "valores": _valores(datos.clave, variable, datos),
        "celdas": [[lon, lat] for lat, lon in fuente.puntos_tierra()],
        "mitad": fuente.PASO_REJILLA / 2,
        "contorno": [[*anillo, anillo[0]] for anillo in fuente.contorno()],
        "escala": {"cortes": list(escala["cortes"]), "rango": list(escala["rango"]),
                   "colores": [list(escalas.rgb(c)) for c in escala["colores"]],
                   "fondo": list(escalas.FONDO), "unidad": escala["unidad"]},
        "altura": {"minima": capas.ALTURA_MINIMA_M, "maxima": capas.ALTURA_MAXIMA_M,
                   "exageracion": exageracion},
        "radio": capas.RADIO_COLUMNA_M, "halo": capas.RADIO_HALO_M, "opacidad": 175, "potencia": 2,
        "vista": {"latitude": vista.latitude, "longitude": vista.longitude, "zoom": vista.zoom,
                  "pitch": vista.pitch, "bearing": vista.bearing},
        "t0": reloj["t0"], "desde": reloj["desde"], "paso": capas.PASO_REPRODUCCION_S,
    }
    # "</" escapado para que ningún texto pueda cerrar la etiqueta <script>
    texto = json.dumps(carga, ensure_ascii=False).replace("</", "<\\/")
    return PLANTILLA.read_text(encoding="utf-8").replace("__DATOS__", texto)


def mapa(datos: fuente.Datos, variable: str, zona: str, exageracion: float,
         alto: int = 620) -> None:
    """Dibuja el mapa animado. Mientras no cambien variable, zona o altura, el HTML es
    idéntico en cada refresco y Streamlit no lo vuelve a cargar: la animación sigue."""
    st.iframe(html(datos, variable, zona, exageracion, alto), height=alto)
