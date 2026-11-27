"""Datos: cargar CSV propios y exportar GeoJSON, CSV, informe y mapa HTML."""

import json

import streamlit as st

from estaciones import almacen, escalas, informes, mapa
from estaciones.excepciones import ErrorDeEstaciones
from estaciones.modelos import CAMPOS_ESTACION, CAMPOS_MEDICION
from panel import datos, estilo

actuales = datos.actuales()
variable = st.session_state["variable"]
escala = escalas.escala(variable)
momento = datos.momento()

estilo.cabecera("Datos", "Carga tus propios ficheros o exporta lo que ves", None,
                [estilo.chip("FUENTE", actuales.nombre),
                 estilo.chip("ESTACIONES", str(len(actuales.red))),
                 estilo.chip("MEDICIONES", f"{len(actuales.tabla):,}".replace(",", "."))],
                etiqueta="GESTIÓN DE DATOS")

izquierda, derecha = st.columns(2, gap="medium")
with izquierda, st.container(key="panel-cargar", height="stretch"):
    estilo.seccion("Cargar datos propios")
    fichero_estaciones = st.file_uploader("CSV de estaciones", type="csv", key="subida_est")
    fichero_mediciones = st.file_uploader("CSV de mediciones", type="csv", key="subida_med")
    with st.container(horizontal=True):
        if st.button("Usar estos datos", icon=":material/upload:", type="primary",
                     disabled=not (fichero_estaciones and fichero_mediciones)):
            try:
                nuevos = datos.usar_ficheros(fichero_estaciones.getvalue(),
                                             fichero_mediciones.getvalue(),
                                             f"{fichero_estaciones.name} + "
                                             f"{fichero_mediciones.name}")
            except (ErrorDeEstaciones, UnicodeDecodeError) as error:
                st.error(f"No se han podido cargar: {error}", icon=":material/error:")
            else:
                st.toast(f"Cargadas {len(nuevos.red)} estaciones y {len(nuevos.tabla)} "
                         "mediciones", icon=":material/check_circle:")
                st.rerun()
        if st.button("Volver a los datos de ejemplo", icon=":material/restart_alt:",
                     disabled="fuente" not in st.session_state):
            datos.usar_ejemplo()
            st.rerun()

with derecha, st.container(key="panel-formato", height="stretch"):
    estilo.seccion("Formato de los ficheros")
    st.markdown(
        f"**Estaciones**: `{', '.join(CAMPOS_ESTACION)}`. Coordenadas WGS84 en grados "
        "decimales, altitud en metros.\n\n"
        f"**Mediciones**: `{', '.join(CAMPOS_MEDICION)}`. Fecha ISO (`2026-11-01T08:00`), "
        "una fila por estación y hora. Un valor vacío es un dato ausente.\n\n"
        "Codificación UTF-8 y separador coma. Si una fila no vale, se indica la línea.")
    with st.container(horizontal=True):
        st.download_button("Plantilla de estaciones", icon=":material/download:",
                           data=(datos.CARPETA_DATOS / "estaciones.csv").read_text(encoding="utf-8"),
                           file_name="plantilla_estaciones.csv", mime="text/csv",
                           on_click="ignore")
        muestra = (datos.CARPETA_DATOS / "mediciones.csv").read_text(encoding="utf-8")
        st.download_button("Plantilla de mediciones", icon=":material/download:",
                           data="\n".join(muestra.splitlines()[:49]) + "\n",
                           file_name="plantilla_mediciones.csv", mime="text/csv",
                           on_click="ignore")

estilo.seccion(f"Exportar · {escala['nombre']} el {momento:%d/%m/%Y a las %H:00}",
               "La hora es la elegida en el centro de control; la variable, la del panel lateral.")
valores = datos.valores(actuales, variable, momento)
estaciones = list(actuales.red)

with st.container(key="exportar"):
    columnas = st.columns(4, gap="medium")
    with columnas[0], st.container(key="panel-exportar-0", height="stretch"):
        estilo.cabecera_exportar("public", "GeoJSON", "Puntos con su valor, para QGIS.")
        st.download_button("Descargar GeoJSON", icon=":material/download:", width="stretch",
                           data=json.dumps(almacen.a_geojson(estaciones, valores),
                                           ensure_ascii=False, indent=2),
                           file_name=f"estaciones_{variable}_{momento:%Y%m%d_%H}.geojson",
                           mime="application/geo+json", on_click="ignore")
    with columnas[1], st.container(key="panel-exportar-1", height="stretch"):
        estilo.cabecera_exportar("table", "CSV", "Mediciones del periodo elegido.",
                                 estilo.VIOLETA)
        desde, hasta = st.slider("Periodo", actuales.primer_dia, actuales.ultimo_dia,
                                 (actuales.primer_dia, actuales.ultimo_dia), format="DD/MM",
                                 key="exp_periodo", label_visibility="collapsed")
        fechas = actuales.tabla["fecha_hora"].dt.date
        filas = actuales.tabla[(fechas >= desde) & (fechas <= hasta)]
        st.download_button("Descargar CSV", icon=":material/download:", width="stretch",
                           data=filas[["codigo", "nombre", "provincia", "lat", "lon",
                                       "fecha_hora", "temperatura", "humedad", "pm25", "no2"]]
                           .to_csv(index=False),
                           file_name=f"mediciones_{desde:%Y%m%d}_{hasta:%Y%m%d}.csv",
                           mime="text/csv", on_click="ignore")
    with columnas[2], st.container(key="panel-exportar-2", height="stretch"):
        estilo.cabecera_exportar("description", "Informe", "Resumen en Markdown.", estilo.VERDE)
        alcance = st.segmented_control("Alcance", ["Día elegido", "Todo el periodo"],
                                       default="Día elegido", required=True, key="exp_alcance",
                                       label_visibility="collapsed")
        texto = informes.informe(actuales.tabla,
                                 momento.date() if alcance == "Día elegido" else None)
        st.download_button("Descargar informe", icon=":material/download:", width="stretch",
                           data=texto, file_name="informe_red_estaciones.md",
                           mime="text/markdown", on_click="ignore")
    with columnas[3], st.container(key="panel-exportar-3", height="stretch"):
        estilo.cabecera_exportar("map", "Mapa HTML", "Mapa interactivo independiente.",
                                 estilo.AMBAR)
        html = mapa.crear_mapa(estaciones, valores, variable,
                               f"{escala['nombre']} · {momento:%d/%m/%Y %H:00}")
        st.download_button("Descargar mapa", icon=":material/download:", width="stretch",
                           data=html, file_name=f"mapa_{variable}_{momento:%Y%m%d_%H}.html",
                           mime="text/html", on_click="ignore")

with st.container(key="panel-vista-informe", height=460):
    estilo.seccion("Vista previa del informe")
    st.markdown(texto)
