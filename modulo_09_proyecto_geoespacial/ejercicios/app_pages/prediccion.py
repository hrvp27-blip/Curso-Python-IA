"""Predicción: el futuro de cada estación con su incertidumbre, el mapa previsto y la validación."""

from datetime import datetime, time, timedelta

import pandas as pd
import streamlit as st

from estaciones import escalas, prediccion
from estaciones.excepciones import ErrorDeEstaciones
from estaciones.modelos import UMBRALES_OMS
from panel import capas, datos, estilo

actuales = datos.actuales()
variable = st.session_state["variable"]
escala = escalas.escala(variable)
unidad = escala["unidad"]
nombres = {e.codigo: e.nombre for e in actuales.red}

with st.container(horizontal=True, vertical_alignment="bottom"):
    origen = st.segmented_control(
        "Predecir desde", ["Final de los datos", "Un momento pasado"], default="Final de los datos",
        required=True, key="pred_origen", persist_state="session",
        help="Desde un momento pasado se puede comparar la predicción con lo que pasó de verdad.")
    horizonte = st.segmented_control("Horizonte", [24, 48, 72], default=48, required=True,
                                     key="pred_horizonte", format_func="{} h".format,
                                     persist_state="session")
    codigo = st.selectbox("Estación", list(nombres), format_func=nombres.get, key="pred_estacion",
                          persist_state="session")
    if origen == "Un momento pasado":
        dia = st.date_input("Día", actuales.ultimo_dia - timedelta(days=3),
                            min_value=actuales.primer_dia + timedelta(days=2),
                            max_value=actuales.ultimo_dia - timedelta(days=1), key="pred_dia",
                            format="DD/MM/YYYY")
        hora = st.slider("Hora", 0, 23, 23, key="pred_hora", format="%d:00")
        desde = datetime.combine(dia, time(hora))
    else:
        desde = actuales.ultimo_momento

try:
    prevision = datos.prevision(actuales.clave, variable, desde, horizonte, actuales.tabla)
    errores = datos.validacion(actuales.clave, variable, actuales.tabla)
except ErrorDeEstaciones as error:
    st.error(str(error), icon=":material/error:")
    st.stop()

resumen = prediccion.resumen_validacion(errores)
propia = prevision[prevision["codigo"] == codigo]
pico = propia.loc[propia["prediccion"].idxmax()]
picos = prevision.loc[prevision.groupby("codigo")["prediccion"].idxmax()]
picos = picos.sort_values("prediccion", ascending=False)
red_pico = picos.iloc[0]

estilo.cabecera(
    f"Predicción de {escala['nombre']}",
    "Lo que se espera en las próximas horas y su margen de error",
    desde,
    [estilo.chip("DESDE", f"{desde:%d/%m %H:00}"), estilo.chip("HORIZONTE", f"{horizonte} h")],
    etiqueta="PREDICCIÓN")

reales = actuales.tabla[actuales.tabla["codigo"] == codigo].set_index("fecha_hora")[variable]
futuro_real = reales.reindex(propia["fecha_hora"]).dropna()
tarjetas = [
    {"titulo": "Pico previsto", "valor": f"{pico['prediccion']:.1f}", "unidad": unidad,
     "sub": f"{pico['fecha_hora']:%d/%m %H:00} · {escalas.clase(variable, pico['prediccion'])}",
     "color": escalas.color(variable, pico["prediccion"]),
     "serie": propia["prediccion"].tolist()},
    {"titulo": "Media prevista", "valor": f"{propia['prediccion'].mean():.1f}", "unidad": unidad,
     "sub": nombres[codigo], "color": estilo.CIAN},
    {"titulo": "Pico de la red", "valor": f"{red_pico['prediccion']:.1f}", "unidad": unidad,
     "sub": f"{nombres[red_pico['codigo']]} · {red_pico['fecha_hora']:%d/%m %H:00}",
     "color": escalas.color(variable, red_pico["prediccion"]),
     "serie": prevision.groupby("paso")["prediccion"].max().tolist()},
    {"titulo": "Error habitual del modelo", "valor": f"{resumen['modelo']:.2f}", "unidad": unidad,
     "sub": f"{resumen['mejora']} % menos que repetir el último valor",
     "color": estilo.VIOLETA},
]
if not futuro_real.empty:
    acierto = (propia.set_index("fecha_hora")["prediccion"] - futuro_real).abs().mean()
    tarjetas.append({"titulo": "Error de esta predicción", "valor": f"{acierto:.2f}",
                     "unidad": unidad, "sub": f"Comparada con {len(futuro_real)} h medidas",
                     "color": estilo.VERDE, "serie": futuro_real.tolist()})
estilo.tarjetas(tarjetas, nota="Las líneas de las tarjetas recorren las horas previstas.")

# --- Gráfico de la estación: pasado, predicción, banda y realidad -----------------
pasado = reales[(reales.index > desde - timedelta(hours=72)) & (reales.index <= desde)]
serie = pd.concat([
    pd.DataFrame({"fecha_hora": pasado.index, "observado": pasado.to_numpy()}),
    propia.assign(banda=propia["superior"] - propia["inferior"])
          [["fecha_hora", "prediccion", "inferior", "banda"]],
], ignore_index=True)
serie["real"] = serie["fecha_hora"].map(futuro_real)
serie["fecha_hora"] = serie["fecha_hora"].dt.strftime("%Y-%m-%d %H:%M")
serie = serie.round(2)

with st.container(key="panel-grafico"):
    estilo.seccion(f"{nombres[codigo]} · últimas 72 h y próximas {horizonte} h",
                   "Blanco: lo medido. Cian discontinuo: la predicción; la franja es donde "
                   "caerá el valor 8 de cada 10 veces. Amarillo punteado: lo que pasó de "
                   "verdad (solo al predecir desde un momento pasado).")
    linea_ahora = {"symbol": "none", "label": {"formatter": "Ahora", "color": "#E2E8F0"},
                   "lineStyle": {"color": "#E2E8F0", "type": "solid", "opacity": 0.5},
                   "data": [{"xAxis": f"{desde:%Y-%m-%d %H:%M}"}]}
    if variable in UMBRALES_OMS:
        linea_ahora["data"].append({"yAxis": UMBRALES_OMS[variable],
                                    "lineStyle": {"color": estilo.ROJO, "type": "dashed"},
                                    "label": {"formatter": "Guía OMS", "color": estilo.ROJO}})
    estilo.grafico({
        "tooltip": {"trigger": "axis", "valueFormatter": "%.1f"},
        "legend": {"data": ["Medido", "Predicción", "Banda 80 %", "Lo que pasó"],
                   "textStyle": {"color": "#CBD5E1"}},
        "dataset": {"source": serie},
        "grid": {"left": 50, "right": 30, "top": 40, "bottom": 70},
        "xAxis": {"type": "time"},
        "yAxis": {"type": "value", "scale": True, "name": unidad},
        "dataZoom": [{"type": "inside"}, {"type": "slider", "height": 18}],
        "series": [
            {"name": "Medido", "type": "line", "showSymbol": False,
             "encode": {"x": "fecha_hora", "y": "observado"},
             "lineStyle": {"width": 2.5, "color": "#E2E8F0"}, "itemStyle": {"color": "#E2E8F0"},
             "markLine": linea_ahora},
            {"name": "Inferior", "type": "line", "stack": "banda", "showSymbol": False,
             "encode": {"x": "fecha_hora", "y": "inferior"}, "lineStyle": {"opacity": 0},
             "tooltip": {"show": False}},
            {"name": "Banda 80 %", "type": "line", "stack": "banda", "showSymbol": False,
             "encode": {"x": "fecha_hora", "y": "banda"}, "lineStyle": {"opacity": 0},
             "areaStyle": {"color": "rgba(34,211,238,0.16)"},
             "itemStyle": {"color": "rgba(34,211,238,0.4)"}},
            {"name": "Predicción", "type": "line", "showSymbol": False, "smooth": True,
             "encode": {"x": "fecha_hora", "y": "prediccion"},
             "lineStyle": {"width": 3, "type": "dashed", "color": estilo.CIAN},
             "itemStyle": {"color": estilo.CIAN}},
            {"name": "Lo que pasó", "type": "line", "showSymbol": False,
             "encode": {"x": "fecha_hora", "y": "real"},
             "lineStyle": {"width": 2, "type": "dotted", "color": estilo.AMBAR},
             "itemStyle": {"color": estilo.AMBAR}},
        ],
    }, height=420, alt=f"{escala['nombre']} medido y previsto en {nombres[codigo]}")


# --- Mapa previsto ----------------------------------------------------------------
with st.container(horizontal=True, vertical_alignment="bottom"):
    reproducir = st.toggle(":material/play_circle: Reproducir la previsión", key="pred_play")
    zona = st.selectbox("Zona", list(capas.ZONAS), key="pred_zona", persist_state="session")


def mapa_previsto() -> None:
    """Mapa de la red dentro de ``paso`` horas, con el ranking de picos al lado."""
    if reproducir:
        st.session_state["pred_paso"] = st.session_state.get("pred_paso", 0) % horizonte + 1
    elif st.session_state.get("pred_paso", 1) > horizonte:
        st.session_state["pred_paso"] = horizonte
    paso = st.slider("Horas por delante", 1, horizonte, key="pred_paso")
    instante = prevision[prevision["paso"] == paso]
    cuando = instante["fecha_hora"].iloc[0]
    izquierda, derecha = st.columns([3.3, 1.2], gap="medium")
    with izquierda, st.container(key="panel-mapa-prevision"):
        estilo.seccion(f"Mapa previsto · {cuando:%d/%m/%Y %H:00} (+{paso} h)",
                       "Las columnas son la predicción de cada estación para esa hora. Mueve "
                       "«Horas por delante» o pulsa Reproducir para ver cómo evoluciona.")
        valores = dict(zip(instante["codigo"], instante["prediccion"]))
        st.pydeck_chart(capas.mapa(actuales.red, variable, valores, zona, alto=600),
                        height=600, key=f"mapa-prevision-{zona}",
                        alt=f"{escala['nombre']} previsto para {cuando:%d/%m %H:00}")
        estilo.leyenda(variable)
    with derecha, st.container(key="panel-picos-ajustado"):
        estilo.seccion(f"Picos previstos · {horizonte} h",
                       "El valor más alto que se espera en cada estación.")
        estilo.barras([(nombres[fila.codigo], fila.prediccion,
                        escalas.color(variable, fila.prediccion),
                        f"{fila.prediccion:.1f}") for fila in picos.head(14).itertuples()],
                      maximo=float(picos["prediccion"].max()))


st.fragment(mapa_previsto, run_every=capas.PASO_REPRODUCCION_S if reproducir else None)()

# --- Validación ---------------------------------------------------------------------
izquierda, derecha = st.columns([1.6, 1], gap="medium")
with izquierda, st.container(key="panel-validacion"):
    estilo.seccion("¿Acierta el modelo?",
                   "Error medio al predecir desde 7 momentos pasados ya conocidos, según "
                   "cuántas horas por delante. Más bajo es mejor: el modelo (cian) debe "
                   "quedar por debajo de las dos referencias sencillas.")
    tabla_errores = errores.reset_index()
    estilo.grafico({
        "tooltip": {"trigger": "axis", "valueFormatter": "%.2f"},
        "legend": {"textStyle": {"color": "#CBD5E1"}},
        "dataset": {"source": tabla_errores},
        "grid": {"left": 50, "right": 20, "top": 40, "bottom": 40},
        "xAxis": {"type": "category", "name": "h"},
        "yAxis": {"type": "value", "name": f"error ({unidad})", "scale": True},
        "series": [
            {"name": "Modelo", "type": "line", "smooth": True, "symbolSize": 6,
             "encode": {"x": "paso", "y": "modelo"},
             "lineStyle": {"width": 3, "color": estilo.CIAN}, "itemStyle": {"color": estilo.CIAN},
             "areaStyle": {"opacity": 0.2}},
            {"name": "Persistencia", "type": "line", "smooth": True, "showSymbol": False,
             "encode": {"x": "paso", "y": "persistencia"},
             "lineStyle": {"color": estilo.ROJO}, "itemStyle": {"color": estilo.ROJO}},
            {"name": "Solo ciclo diario", "type": "line", "smooth": True, "showSymbol": False,
             "encode": {"x": "paso", "y": "climatologia"},
             "lineStyle": {"color": estilo.VIOLETA}, "itemStyle": {"color": estilo.VIOLETA}},
        ],
    }, height=330, alt="Error medio del modelo frente a la persistencia y el ciclo diario")
with derecha, st.container(key="panel-explicacion", height="stretch"):
    estilo.seccion("Cómo funciona")
    st.markdown(
        "Para cada estación y cada hora futura:\n\n"
        "$$\\hat{x}_{t+k} = \\text{ciclo}(h_{t+k}) + a_t\\,\\varphi^{k}$$\n\n"
        "- **Ciclo diario**: media de cada hora en los últimos 14 días.\n"
        "- **Anomalía** $a_t$: cuánto se aleja ahora el valor de su ciclo.\n"
        f"- **Persistencia** $\\varphi$: autocorrelación horaria de la anomalía; "
        "se olvida poco a poco.\n"
        "- **Banda del 80 %**: $\\pm 1{,}28\\,\\sigma\\sqrt{1-\\varphi^{2k}}$.\n\n"
        f"Validado prediciendo desde 7 momentos pasados: error medio de "
        f"**{resumen['modelo']} {unidad}**, un **{resumen['mejora']} %** menos que repetir el "
        "último valor (persistencia).")
