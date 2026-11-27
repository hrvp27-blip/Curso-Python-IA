"""Mapa HTML independiente con folium, para abrir en cualquier navegador (única capa con folium)."""

from html import escape
from pathlib import Path

import folium

from . import geo
from .escalas import color, describir, escala, etiquetas
from .modelos import Estacion

TESELAS = "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
ATRIBUCION = "© OpenStreetMap contributors © CARTO"


def _leyenda(variable: str) -> str:
    """HTML de la leyenda fija en la esquina del mapa."""
    datos = escala(variable)
    filas = "".join(
        f'<div><span style="display:inline-block;width:12px;height:12px;'
        f'background:{tono};margin-right:6px;border-radius:2px"></span>{escape(nombre)}</div>'
        for tono, nombre in zip(datos["colores"], etiquetas(variable)))
    return (f'<div style="position:fixed;bottom:24px;left:24px;z-index:9999;'
            f'background:#0B1120;color:#E2E8F0;padding:10px 14px;border-radius:8px;'
            f'font:12px Inter,sans-serif;border:1px solid #22D3EE">'
            f'<b>{escape(datos["nombre"])} ({escape(datos["unidad"])})</b>{filas}</div>')


def crear_mapa(estaciones: list[Estacion], valores: dict[str, float], variable: str,
               titulo: str, ruta: str | Path | None = None) -> str:
    """Mapa con un círculo por estación coloreado con la escala oficial.

    Devuelve el HTML completo y, si se indica ``ruta``, lo guarda también ahí.
    Las estaciones sin valor salen en gris.
    """
    centro = geo.centroide([e.coordenadas for e in estaciones])
    mapa = folium.Map(location=centro, zoom_start=5, tiles=TESELAS, attr=ATRIBUCION)
    for estacion in estaciones:
        valor = valores.get(estacion.codigo)
        texto = describir(variable, valor) if valor is not None else "sin dato"
        folium.CircleMarker(
            location=estacion.coordenadas, radius=11, weight=2,
            color="#E2E8F0", fill=True, fill_opacity=0.9,
            fill_color=color(variable, valor) if valor is not None else "#64748B",
            tooltip=f"{escape(estacion.nombre)}: {escape(texto)}",
            popup=folium.Popup(f"<b>{escape(estacion.nombre)}</b><br>"
                               f"{escape(estacion.provincia)}<br>{escape(texto)}", max_width=260),
        ).add_to(mapa)
    mapa.get_root().html.add_child(folium.Element(
        f'<h3 style="position:fixed;top:12px;left:60px;z-index:9999;color:#E2E8F0;'
        f'font:600 18px Inter,sans-serif;background:#0B1120cc;padding:6px 12px;'
        f'border-radius:8px">{escape(titulo)}</h3>'))
    mapa.get_root().html.add_child(folium.Element(_leyenda(variable)))
    html = mapa.get_root().render()
    if ruta is not None:
        Path(ruta).write_text(html, encoding="utf-8")
    return html
