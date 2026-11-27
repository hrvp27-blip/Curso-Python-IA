"""Ampliaciones: ideas para seguir desarrollando el proyecto, con lo que aportan y lo que costarían."""

import streamlit as st

from panel import estilo

# Color de cada bloque de ideas
COLORES = [estilo.CIAN, estilo.VIOLETA, estilo.VERDE]

# Cada bloque: (título, ayuda, ideas). Cada idea: título, icono, qué aporta, qué haría falta, esfuerzo
BLOQUES = [
    ("Datos", "Pasar de datos de ejemplo a datos reales y más completos.", [
        ("Datos reales de calidad del aire", "cloud_download",
         "Ver la situación real de España en lugar de datos sintéticos.",
         "Descargar las mediciones horarias de la Agencia Europea de Medio Ambiente o de las "
         "redes autonómicas y adaptarlas al formato de `mediciones.csv`.", "Medio"),
        ("Límites oficiales del IGN", "map",
         "Costa y fronteras precisas, y poder resumir por comunidad, provincia o municipio.",
         "Usar los límites administrativos del Centro de Descargas del CNIG en lugar del "
         "contorno dibujado a mano.", "Bajo"),
        ("Base de datos espacial", "database",
         "Guardar años de mediciones y hacer consultas espaciales rápidas.",
         "Pasar de CSV a PostgreSQL con PostGIS y leer desde el panel con consultas SQL.",
         "Alto"),
    ]),
    ("Análisis espacial", "Mejorar cómo se estima el valor entre estaciones y qué se predice.", [
        ("Kriging en lugar de IDW", "blur_on",
         "Una superficie más realista y, además, el error de la estimación en cada punto.",
         "Ajustar un variograma con los datos y comparar ambos métodos con validación cruzada "
         "(quitar una estación y estimarla con las demás).", "Medio"),
        ("Predicción con meteorología", "air",
         "Predecir mejor los episodios: el viento y la lluvia limpian el aire, la calma lo empeora.",
         "Añadir viento y precipitación (por ejemplo, de AEMET OpenData) como variables del "
         "modelo y validarlo igual que el actual.", "Alto"),
        ("Población expuesta", "groups",
         "Pasar de «dónde está mal el aire» a «a cuántas personas afecta».",
         "Cruzar la superficie interpolada con la rejilla de población del INE y sumar la "
         "población de las celdas que superan la guía de la OMS.", "Medio"),
    ]),
    ("Producto", "Que el panel lo pueda usar más gente y avise sin tener que mirarlo.", [
        ("Avisos automáticos", "notifications_active",
         "Enterarse de un episodio sin tener el panel abierto.",
         "Un proceso que revise los datos cada hora y mande un correo o un mensaje cuando una "
         "estación supere su umbral.", "Medio"),
        ("Publicarlo en internet", "public",
         "Enseñar el proyecto con un enlace, sin instalar nada.",
         "Subir el repositorio a Streamlit Community Cloud con su `requirements.txt`.", "Bajo"),
    ]),
]

total = sum(len(ideas) for _, _, ideas in BLOQUES)
estilo.cabecera("Posibles ampliaciones", "Ideas para seguir desarrollando el proyecto", None,
                [estilo.chip("IDEAS", str(total)), estilo.chip("BLOQUES", str(len(BLOQUES)))],
                etiqueta="HOJA DE RUTA")

estilo.intro("rocket_launch", f"<b>{total} ideas</b> para llevar el proyecto más lejos. Cada "
             "una dice <b>qué aportaría</b>, <b>qué haría falta</b> y cuánto esfuerzo supone "
             "(una, dos o tres marcas).")

for bloque, (titulo_bloque, ayuda, ideas) in enumerate(BLOQUES):
    estilo.seccion(titulo_bloque, ayuda)
    columnas = st.columns(3, gap="medium")
    for numero, (titulo, icono, aporta, falta, esfuerzo) in enumerate(ideas):
        with columnas[numero % 3], st.container(key=f"panel-idea-{bloque}-{numero}",
                                                height="stretch"):
            estilo.cabecera_idea(icono, titulo, esfuerzo, COLORES[bloque % len(COLORES)])
            st.markdown(f"**Qué aporta.** {aporta}\n\n**Qué haría falta.** {falta}")
