"""Mapas con pydeck: columnas 3D sobre la superficie interpolada.

La superficie va plana sobre el terreno como una imagen (un píxel por celda de
la rejilla, como un ráster), con el color oficial matizado dentro de cada
clase. Cada estación es una columna fina cuya altura es su valor.
"""

import base64
import io
import math

import numpy as np
import pandas as pd
import pydeck as pdk
import streamlit as st
from PIL import Image

from estaciones import escalas
from estaciones.excepciones import DatosNoValidos
from estaciones.red import RedEstaciones

from . import datos as fuente

ZONAS = {
    "Península y Baleares": (35.6, -9.6, 44.0, 4.6),
    "Canarias": (27.5, -18.3, 29.5, -13.2),
    "Baleares": (38.5, 1.0, 40.2, 4.5),
}
CIAN = [34, 211, 238]
INCLINACION = 52
GIRO = -12
ALTURA_MINIMA_M = 3000
ALTURA_MAXIMA_M = 70_000
RADIO_COLUMNA_M = 6_000
RADIO_HALO_M = 17_000
# Segundos que dura cada hora en la reproducción automática (ver panel/animacion.py)
PASO_REPRODUCCION_S = 1.2
# Al cambiar día u hora a mano, deck.gl anima el cambio de altura y color en este tiempo
TRANSICION_MS = 800
TOOLTIP = {"html": "<div style='font:600 10px JetBrains Mono,monospace;letter-spacing:.16em;"
                   "color:#67E8F9;text-transform:uppercase'>{provincia}</div>"
                   "<div style='font:600 14px Space Grotesk,Inter,sans-serif;margin:2px 0 6px'>"
                   "{nombre}</div><div style='font:600 13px JetBrains Mono,monospace'>"
                   "{etiqueta}</div>",
           "style": {"backgroundColor": "rgba(6,10,20,0.92)", "color": "#E2E8F0",
                     "border": "1px solid rgba(34,211,238,0.45)", "borderRadius": "12px",
                     "padding": "10px 12px", "fontFamily": "Inter, sans-serif",
                     "boxShadow": "0 14px 34px -10px rgba(0,0,0,.85), "
                                  "0 0 24px -8px rgba(34,211,238,.6)",
                     "backdropFilter": "blur(8px)"}}
# Rejilla de meridianos y paralelos cada grado (más marcada cada cinco)
GRATICULA = {"lat": (26, 45), "lon": (-20, 6)}


def encuadre(caja: tuple[float, float, float, float], pitch: float = 0, bearing: float = 0,
             ancho: int = 1100, alto: int = 620, alejar: float = 0.5) -> pdk.ViewState:
    """Vista que hace caber ``caja`` en un mapa de ``ancho`` x ``alto`` px, alejada ``alejar`` niveles.

    Web Mercator: a zoom 0 el mundo mide 512 px y cada nivel lo duplica.
    """
    lat_min, lon_min, lat_max, lon_max = caja

    def mercator(lat: float) -> float:
        return math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))

    alto_grados = math.degrees(mercator(lat_max) - mercator(lat_min))
    zoom = min(math.log2(ancho * 360 / (512 * (lon_max - lon_min))),
               math.log2(alto * 360 / (512 * alto_grados))) - alejar
    centro = math.degrees(2 * math.atan(math.exp((mercator(lat_min) + mercator(lat_max)) / 2))
                          - math.pi / 2)
    return pdk.ViewState(latitude=centro, longitude=(lon_min + lon_max) / 2, zoom=zoom,
                         pitch=pitch, bearing=bearing)


def vista_inclinada(caja: tuple[float, float, float, float], ancho: int = 900,
                    alto: int = 620, alejar: float = -0.1) -> pdk.ViewState:
    """Encuadre inclinado de una caja, algo girado para que se vean las columnas en
    perspectiva. Al inclinar, el norte se aleja: se baja el centro."""
    vista = encuadre(caja, pitch=INCLINACION, bearing=GIRO, ancho=ancho, alto=alto,
                     alejar=alejar)
    vista.latitude -= (caja[2] - caja[0]) * 0.2
    return vista


def muestras(red: RedEstaciones, valores: dict[str, float]) -> tuple:
    """``(lat, lon, valor)`` de las estaciones con valor, listo para la caché."""
    lista = tuple((e.lat, e.lon, float(valores[e.codigo])) for e in red
                  if e.codigo in valores and valores[e.codigo] == valores[e.codigo])
    if not lista:
        raise DatosNoValidos("No hay datos de ninguna estación para dibujar")
    return lista


def colores_matizados(variable: str, valores: np.ndarray) -> np.ndarray:
    """``escalas.rgb_matizado`` para muchos valores a la vez: una fila RGB por valor."""
    datos = escalas.escala(variable)
    cortes = np.array(datos["cortes"], dtype=float)
    clases = range(len(cortes) + 1)
    inferior, superior = np.array([escalas.limites_clase(variable, i) for i in clases]).T
    tonos = np.array([escalas.rgb(c) for c in datos["colores"]], dtype=float)
    fondo = np.array(escalas.FONDO, dtype=float)
    indice = np.searchsorted(cortes, valores, side="left")   # como bisect_left
    posicion = np.clip((valores - inferior[indice]) / (superior[indice] - inferior[indice]), 0, 1)
    intensidad = (0.45 + 0.55 * posicion)[:, None]
    return np.rint(fondo + (tonos[indice] - fondo) * intensidad).astype(np.uint8)


def _filas_mercator(norte: float, sur: float, paso: float, filas: int) -> np.ndarray:
    """Para cada fila de la imagen final (iguales en Mercator), la fila de celdas que le toca."""
    def mercator(lat):
        return np.log(np.tan(np.pi / 4 + np.radians(lat) / 2))
    salida = filas * 3                     # más filas para no perder detalle al remuestrear
    y = mercator(norte) - (np.arange(salida) + 0.5) * (mercator(norte) - mercator(sur)) / salida
    latitud = np.degrees(2 * np.arctan(np.exp(y)) - np.pi / 2)
    return np.clip(((norte - latitud) / paso).astype(int), 0, filas - 1)


@st.cache_data(max_entries=600)
def imagen_superficie(variable: str, muestras_: tuple, opacidad: int = 175) -> tuple[str, list]:
    """PNG de la superficie (un píxel por celda) en base64 y sus límites ``[oeste, sur, este, norte]``."""
    celdas = fuente.superficie(muestras_)
    paso = fuente.PASO_REJILLA
    oeste, norte = celdas["lon"].min(), celdas["lat"].max()
    columna = np.rint((celdas["lon"] - oeste) / paso).astype(int).to_numpy()
    fila = np.rint((norte - celdas["lat"]) / paso).astype(int).to_numpy()
    pixeles = np.zeros((fila.max() + 1, columna.max() + 1, 4), dtype=np.uint8)
    pixeles[fila, columna, :3] = colores_matizados(variable, celdas["valor"].to_numpy())
    pixeles[fila, columna, 3] = opacidad
    mitad = paso / 2
    sur = celdas["lat"].min() - mitad
    # deck.gl estira la imagen en Mercator, donde los grados de latitud no miden igual:
    # se rehacen las filas a intervalos iguales en Mercator para que cada celda caiga en su sitio
    pixeles = pixeles[_filas_mercator(norte + mitad, sur, paso, pixeles.shape[0])]
    salida = io.BytesIO()
    Image.fromarray(pixeles, "RGBA").save(salida, format="PNG")
    limites = [oeste - mitad, sur, celdas["lon"].max() + mitad, norte + mitad]
    return "data:image/png;base64," + base64.b64encode(salida.getvalue()).decode(), limites


def capa_superficie(red: RedEstaciones, variable: str, valores: dict[str, float],
                    opacidad: int = 175) -> pdk.Layer:
    """Superficie interpolada por IDW, plana, como imagen sobre el mapa."""
    imagen, limites = imagen_superficie(variable, muestras(red, valores), opacidad)
    # pdk.types.String: sin él, pydeck tomaría la imagen como una expresión de JavaScript
    return pdk.Layer("BitmapLayer", None, id="superficie", image=pdk.types.String(imagen),
                     bounds=limites)


def capa_graticula() -> pdk.Layer:
    """Meridianos y paralelos cada grado, muy tenues; los de cada 5° algo más marcados."""
    (lat_min, lat_max), (lon_min, lon_max) = GRATICULA["lat"], GRATICULA["lon"]
    lineas = [{"camino": [[lon, lat_min], [lon, lat_max]], "fuerte": lon % 5 == 0}
              for lon in range(lon_min, lon_max + 1)]
    lineas += [{"camino": [[lon_min, lat], [lon_max, lat]], "fuerte": lat % 5 == 0}
               for lat in range(lat_min, lat_max + 1)]
    tabla = pd.DataFrame(lineas)
    tabla["color"] = [[*CIAN, 55] if fuerte else [148, 163, 184, 22] for fuerte in tabla["fuerte"]]
    return pdk.Layer("PathLayer", tabla, id="graticula", get_path="camino", get_color="color",
                     get_width=1, width_min_pixels=1, width_max_pixels=1)


def capas_contorno() -> list[pdk.Layer]:
    """Costa y fronteras de España con brillo cian."""
    caminos = pd.DataFrame({"camino": [[*anillo, anillo[0]] for anillo in fuente.contorno()]})
    return [
        pdk.Layer("PathLayer", caminos, id="contorno_halo", get_path="camino",
                  get_color=[*CIAN, 18], width_min_pixels=18),
        pdk.Layer("PathLayer", caminos, id="contorno_brillo", get_path="camino",
                  get_color=[*CIAN, 60], width_min_pixels=6),
        pdk.Layer("PathLayer", caminos, id="contorno", get_path="camino",
                  get_color=[*CIAN, 235], width_min_pixels=1.5),
    ]


def tabla_estaciones(red: RedEstaciones, variable: str, valores: dict[str, float],
                     exageracion: float) -> pd.DataFrame:
    """Una fila por estación con valor, color oficial, altura de columna y textos."""
    tabla = pd.DataFrame([{"codigo": e.codigo, "nombre": e.nombre, "provincia": e.provincia,
                           "lat": e.lat, "lon": e.lon, "valor": valores[e.codigo]}
                          for e in red if e.codigo in valores])
    altura = [(ALTURA_MINIMA_M + escalas.proporcion(variable, v) * ALTURA_MAXIMA_M) * exageracion
              for v in tabla["valor"]]
    return tabla.assign(
        altura=altura,
        cima=[[lon, lat, z] for lon, lat, z in zip(tabla["lon"], tabla["lat"], altura)],
        color=[[*escalas.rgb(escalas.color(variable, v)), 255] for v in tabla["valor"]],
        halo=[[*escalas.rgb(escalas.color(variable, v)), 45] for v in tabla["valor"]],
        aro=[[*escalas.rgb(escalas.color(variable, v)), 170] for v in tabla["valor"]],
        texto=[f"{v:.0f}" for v in tabla["valor"]],
        etiqueta=[escalas.describir(variable, v) for v in tabla["valor"]],
    )


def capas_columnas(estaciones: pd.DataFrame, radio_m: float = RADIO_COLUMNA_M) -> list[pdk.Layer]:
    """Una columna fina por estación con el color oficial, un halo en su base y su valor
    en la punta."""
    return [
        pdk.Layer("ScatterplotLayer", estaciones, id="halos", get_position=["lon", "lat"],
                  get_radius=RADIO_HALO_M, get_fill_color="halo", get_line_color="aro",
                  stroked=True, filled=True, line_width_min_pixels=1.2,
                  transitions={"getFillColor": TRANSICION_MS, "getLineColor": TRANSICION_MS}),
        pdk.Layer("ColumnLayer", estaciones, id="columnas", get_position=["lon", "lat"],
                  get_elevation="altura", radius=radio_m, disk_resolution=24,
                  get_fill_color="color", extruded=True, pickable=True, auto_highlight=True,
                  highlight_color=[255, 255, 255, 90],
                  material={"ambient": 0.6, "diffuse": 0.55, "shininess": 48,
                            "specularColor": [120, 200, 255]},
                  transitions={"getElevation": TRANSICION_MS, "getFillColor": TRANSICION_MS}),
        pdk.Layer("TextLayer", estaciones, id="valores", get_position="cima", get_text="texto",
                  get_size=13, get_color=[248, 250, 252], get_pixel_offset=[0, -12],
                  billboard=True, font_family="Inter, sans-serif", font_weight=700,
                  outline_width=5, outline_color=[6, 10, 20], font_settings={"sdf": True},
                  transitions={"getPosition": TRANSICION_MS}),
    ]


def mapa(red: RedEstaciones, variable: str, valores: dict[str, float], zona: str,
         exageracion: float = 1.0, alto: int = 620, vista_inicial: pdk.ViewState | None = None,
         extra: list[pdk.Layer] = ()) -> pdk.Deck:
    """Superficie plana, contorno y una columna 3D por estación.

    ``vista_inicial`` sustituye al encuadre de la zona y ``extra`` añade capas encima.
    """
    estaciones = tabla_estaciones(red, variable, valores, exageracion)
    capas = [capa_graticula(), capa_superficie(red, variable, valores), *capas_contorno(),
             *capas_columnas(estaciones), *extra]
    vista = vista_inicial or vista_inclinada(ZONAS[zona], alto=alto)
    return pdk.Deck(layers=capas, initial_view_state=vista, map_style="dark", tooltip=TOOLTIP)
