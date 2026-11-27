"""Centro de control: el mapa de la hora elegida con indicadores, alertas y ranking."""

import streamlit as st

from estaciones import analisis, escalas
from estaciones.excepciones import ErrorDeEstaciones
from estaciones.modelos import UMBRALES_OMS, categoria_ica
from panel import animacion, capas, datos, estilo

actuales = datos.actuales()
variable = st.session_state["variable"]
escala = escalas.escala(variable)

# Barra de controles en una sola fila. Día y hora se dibujan desde el fragmento en sus huecos
with st.container(key="panel-controles"):
    hueco_play, hueco_dia, hueco_hora, hueco_zona, hueco_altura = st.columns(
        [1.5, 2.1, 1.9, 1.6, 1.5], gap="medium", vertical_alignment="bottom")
with hueco_play:
    reproducir = st.toggle(":material/play_circle: Reproducción", key="reproducir",
                           help="Avanza sola hora a hora por todo el periodo. "
                                "Desactívala para elegir día y hora a mano.")
with hueco_zona:
    zona = st.selectbox("Zona", list(capas.ZONAS), key="zona", persist_state="session")
with hueco_altura:
    exageracion = st.slider("Altura de columnas", 0.5, 3.0, 1.0, 0.25, key="exageracion",
                            format="×%.2f", persist_state="session")


AYUDA_ALERTAS = {
    "no2": f"Estaciones por encima de la guía de la OMS ({UMBRALES_OMS['no2']} µg/m³).",
    "pm25": f"Estaciones por encima de la guía de la OMS ({UMBRALES_OMS['pm25']} µg/m³).",
    "temperatura": "Heladas (0 °C o menos) y calor intenso (30 °C o más).",
    "humedad": "Aire saturado (97 % o más, posible niebla) o muy seco (30 % o menos).",
}


def alertas_de(filas, variable: str) -> list[dict]:
    """Alertas de la hora: superaciones OMS en contaminantes y extremos en meteorología."""
    if variable in UMBRALES_OMS:
        umbral = UMBRALES_OMS[variable]
        sobre = filas[filas[variable] > umbral].sort_values(variable, ascending=False)
        return [{"titulo": fila.nombre,
                 "detalle": f"{getattr(fila, variable) / umbral:.1f}× la guía OMS · "
                            f"{categoria_ica(variable, getattr(fila, variable))}",
                 "cifra": f"{getattr(fila, variable):.1f}", "unidad": escala["unidad"],
                 "nivel": getattr(fila, variable) / (umbral * 4), "icono": "warning",
                 "color": escalas.color(variable, getattr(fila, variable))
                 if categoria_ica(variable, getattr(fila, variable)) != "Buena" else estilo.AMBAR}
                for fila in sobre.itertuples()]
    if variable == "temperatura":
        extremos = filas[(filas[variable] <= 0) | (filas[variable] >= 30)]
        return [{"titulo": fila.nombre,
                 "detalle": "Helada" if fila.temperatura <= 0 else "Calor intenso",
                 "cifra": f"{fila.temperatura:.1f}", "unidad": "°C",
                 "icono": "ac_unit" if fila.temperatura <= 0 else "local_fire_department",
                 "color": escalas.color(variable, fila.temperatura)}
                for fila in extremos.itertuples()]
    extremos = filas[(filas[variable] >= 97) | (filas[variable] <= 30)]
    return [{"titulo": fila.nombre,
             "detalle": "Saturación: posible niebla" if fila.humedad >= 97 else "Aire muy seco",
             "cifra": f"{fila.humedad:.0f}", "unidad": "%",
             "icono": "foggy" if fila.humedad >= 97 else "water_drop",
             "color": escalas.color(variable, fila.humedad)}
            for fila in extremos.itertuples()]


def tarjetas_de(filas, del_dia, variable: str) -> list[dict]:
    """Las cinco tarjetas de indicadores de la hora."""
    unidad = escala["unidad"]
    por_hora = del_dia.groupby(del_dia["fecha_hora"].dt.hour)[variable]
    maxima = filas.loc[filas[variable].idxmax()]
    minima = filas.loc[filas[variable].idxmin()]
    media = filas[variable].mean()
    tarjetas = [
        {"titulo": "Media nacional", "valor": f"{media:.1f}", "unidad": unidad,
         "sub": escalas.clase(variable, media), "color": escalas.color(variable, media),
         "serie": por_hora.mean().tolist()},
        {"titulo": "Máximo", "valor": f"{maxima[variable]:.1f}", "unidad": unidad,
         "sub": maxima["nombre"], "color": escalas.color(variable, maxima[variable]),
         "serie": por_hora.max().tolist()},
        {"titulo": "Mínimo", "valor": f"{minima[variable]:.1f}", "unidad": unidad,
         "sub": minima["nombre"], "color": escalas.color(variable, minima[variable]),
         "serie": por_hora.min().tolist()},
    ]
    if variable in UMBRALES_OMS:
        umbral = UMBRALES_OMS[variable]
        sobre = (del_dia[variable] > umbral).groupby(del_dia["fecha_hora"].dt.hour).sum()
        peor = max(filas[variable])
        tarjetas += [
            {"titulo": "Sobre guía OMS", "valor": str(int((filas[variable] > umbral).sum())),
             "unidad": f"de {len(filas)}", "sub": f"Guía: {umbral} {unidad} (media 24 h)",
             "color": estilo.ROJO, "serie": sobre.tolist()},
            {"titulo": "Peor categoría ICA", "valor": categoria_ica(variable, peor),
             "sub": "Escala ICA del MITECO", "color": escalas.color(variable, peor)},
        ]
    else:
        tarjetas += [
            {"titulo": "Contraste", "valor": f"{maxima[variable] - minima[variable]:.1f}",
             "unidad": unidad, "sub": "Diferencia entre máximo y mínimo",
             "color": estilo.VIOLETA,
             "serie": (por_hora.max() - por_hora.min()).tolist()},
            {"titulo": "Estaciones con dato", "valor": str(len(filas)),
             "unidad": f"de {len(actuales.red)}", "sub": "Red operativa",
             "color": estilo.VERDE, "serie": por_hora.count().tolist()},
        ]
    return tarjetas


def panel() -> None:
    """La parte que se refresca: reloj, indicadores, título, mapa fijo, alertas y ranking.

    Escribe en los huecos reservados fuera del fragmento. En reproducción, el mapa
    animado no está aquí: se dibuja una sola vez fuera y el navegador lo anima.
    """
    if reproducir:
        animacion.sincronizar(actuales)
    with hueco_dia:
        st.slider("Día", actuales.primer_dia, actuales.ultimo_dia, key="dia",
                  format="DD/MM/YYYY", persist_state="session")
    with hueco_hora:
        st.slider("Hora", 0, 23, key="hora", format="%d:00", persist_state="session")
    momento = datos.momento()
    filas = analisis.en_momento(actuales.tabla, momento).dropna(subset=[variable])
    if filas.empty:
        with hueco_tarjetas:
            st.warning(f"No hay datos de {escala['nombre']} el {momento:%d/%m/%Y a las %H:00}.")
        return
    chips = [estilo.chip("ESTACIONES", f"{len(filas)}/{len(actuales.red)}"),
             estilo.chip("ZONA", zona)]
    estilo.cabecera("Red nacional de estaciones", "Lo que miden todas las estaciones a esta hora",
                    momento, chips, etiqueta="REPRODUCIENDO" if reproducir else "HORA ELEGIDA",
                    destino=hueco_cabecera, activo=reproducir)

    with hueco_tarjetas:
        del_dia = actuales.tabla[actuales.tabla["fecha_hora"].dt.date == momento.date()]
        estilo.tarjetas(tarjetas_de(filas, del_dia, variable),
                        nota="Las líneas de las tarjetas muestran el día completo, de 0:00 a 23:00.")
    with hueco_titulo:
        estilo.seccion(f"{escala['nombre']} a las {momento:%H:00}",
                       "Cada columna es una estación: la altura es el valor medido y el color, "
                       "su clase en la escala oficial. El suelo coloreado es la estimación "
                       "entre estaciones.")
    if not reproducir:
        with hueco_mapa:
            valores = dict(zip(filas["codigo"], filas[variable]))
            try:
                deck = capas.mapa(actuales.red, variable, valores, zona, exageracion, alto=620)
            except ErrorDeEstaciones as error:
                st.warning(str(error))
            else:
                st.pydeck_chart(deck, height=620, key=f"mapa-control-{zona}",
                                alt=f"{escala['nombre']} en {zona} el {momento:%d/%m %H:00}")
    with panel_lateral:
        # Pestañas: cambiar entre alertas y ranking no recarga la página ni obliga a bajar
        pestana_alertas, pestana_ranking = st.tabs(
            [":material/notifications: Alertas", ":material/leaderboard: Ranking"],
            key="lateral")
        with pestana_alertas:
            lista = alertas_de(filas, variable)
            estilo.ayuda(f"{AYUDA_ALERTAS[variable]} Ahora: {len(lista)}.")
            estilo.alertas(lista)
        with pestana_ranking:
            estilo.ayuda("Las 12 estaciones con el valor más alto a esta hora.")
            orden = filas.sort_values(variable, ascending=False).head(12)
            estilo.barras([(fila.nombre, getattr(fila, variable),
                            escalas.color(variable, getattr(fila, variable)),
                            f"{getattr(fila, variable):.1f}")
                           for fila in orden.itertuples()],
                          maximo=float(orden[variable].max()))


# Huecos reservados fuera del fragmento; el fragmento los rellena en cada refresco
hueco_cabecera = st.sidebar.container()
hueco_tarjetas = st.container()
izquierda, derecha = st.columns([3.3, 1.2], gap="medium")
with izquierda, st.container(key="panel-mapa"):
    hueco_titulo = st.container()
    hueco_mapa = st.container()
    estilo.leyenda(variable)
with derecha:
    panel_lateral = st.container(key="panel-lateral-ajustado")

if reproducir:
    # El mapa animado se dibuja una sola vez: los refrescos del fragmento no lo tocan
    animacion.sincronizar(actuales)
    with hueco_mapa:
        animacion.mapa(actuales, variable, zona, exageracion, alto=620)
else:
    animacion.parar()

st.fragment(panel, run_every=capas.PASO_REPRODUCCION_S if reproducir else None)()
