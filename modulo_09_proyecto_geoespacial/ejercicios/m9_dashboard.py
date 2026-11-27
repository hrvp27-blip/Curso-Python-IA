"""Dashboard de la red nacional de estaciones: punto de entrada y navegación.

Capa de presentación: toda la lógica está en el paquete ``estaciones``; las
piezas comunes del dashboard, en ``panel``, y cada página en ``app_pages``.
Desde la carpeta ``Curso-Python-IA``, con el entorno virtual activado:

    streamlit run modulo_09_proyecto_geoespacial/ejercicios/m9_dashboard.py

Cada página dibuja su cabecera arriba de la barra lateral; por eso los
controles comunes de la barra se dibujan después de la página.
"""

from pathlib import Path

import streamlit as st

from estaciones import escalas
from estaciones.excepciones import ErrorDeEstaciones
from panel import datos, estilo

RECURSOS = Path(__file__).parent / "recursos"

st.set_page_config(page_title="Red nacional de estaciones",
                   page_icon=str(RECURSOS / "icono.svg"), layout="wide")
# Logo arriba a la izquierda; con la barra lateral plegada queda solo el icono
st.logo(str(RECURSOS / "logo.svg"), icon_image=str(RECURSOS / "icono.svg"), size="large")
estilo.aplicar()

try:
    actuales = datos.actuales()
except ErrorDeEstaciones as error:
    st.error(f"Los datos subidos ya no se pueden cargar: {error}", icon=":material/error:")
    datos.usar_ejemplo()
    actuales = datos.actuales()
datos.colocar_momento(actuales)
st.session_state.setdefault("variable", "no2")

pagina = st.navigation([
    st.Page("app_pages/control.py", title="Centro de control", icon=":material/radar:",
            default=True,
            help="Mapa de columnas 3D de la hora elegida, con indicadores, "
                 "alertas activas y ranking. Se puede reproducir el mes hora a hora."),
    st.Page("app_pages/prediccion.py", title="Predicción", icon=":material/online_prediction:",
            help="Predicción a 24-72 h con un modelo propio (ciclo diario + persistencia), "
                 "su banda de incertidumbre, el mapa previsto y la validación del modelo."),
    st.Page("app_pages/estaciones.py", title="Estaciones", icon=":material/sensors:",
            help="Ficha detallada de cada estación y comparador de dos a cuatro estaciones."),
    st.Page("app_pages/datos.py", title="Datos", icon=":material/folder_open:",
            help="Cargar CSV propios de estaciones y mediciones, y exportar GeoJSON, CSV, "
                 "informe y mapa HTML."),
    st.Page("app_pages/ampliaciones.py", title="Ampliaciones", icon=":material/rocket_launch:",
            help="Ideas para seguir desarrollando el proyecto: qué aportaría cada una, "
                 "qué haría falta y cuánto esfuerzo supone."),
], position="top")
pagina.run()

with st.sidebar:
    st.segmented_control("Variable", list(escalas.ESCALAS), required=True, key="variable",
                         persist_state="session", width="stretch",
                         format_func=lambda clave: escalas.ESCALAS[clave]["nombre"])
    st.divider()
    estilo.pie_lateral(actuales.nombre, len(actuales.red), len(actuales.tabla),
                       f"{actuales.primer_dia:%d/%m/%Y} – {actuales.ultimo_dia:%d/%m/%Y}")
