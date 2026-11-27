"""Estaciones: ficha detallada de una estación y comparador de varias."""

import pandas as pd
import pydeck as pdk
import streamlit as st

from estaciones import analisis, escalas, geo
from estaciones.modelos import UMBRALES_OMS
from panel import capas, datos, estilo

actuales = datos.actuales()
variable = st.session_state["variable"]
escala = escalas.escala(variable)
unidad = escala["unidad"]
tabla = actuales.tabla
nombres = {e.codigo: e.nombre for e in actuales.red}
piezas = estilo.piezas_echarts(variable)

modo_pagina = st.segmented_control(
    "Vista", ["Ficha", "Comparar"], default="Ficha", required=True, key="est_vista",
    persist_state="session", label_visibility="collapsed",
    format_func={"Ficha": ":material/badge: Ficha de estación",
                 "Comparar": ":material/compare_arrows: Comparar estaciones"}.get)


def ficha() -> None:
    """Todo sobre una estación: situación, vecinas, reparto por clases, ciclo y calendario."""
    codigo = st.selectbox("Estación", list(nombres), format_func=nombres.get,
                          key="ficha_estacion", persist_state="session")
    estacion = actuales.red.obtener(codigo)
    propias = tabla[tabla["codigo"] == codigo].dropna(subset=[variable])
    vecinas = actuales.red.cercanas(estacion.lat, estacion.lon, 20_000)[1:6]
    vecina, distancia = vecinas[0]
    rumbo = geo.rumbo(*estacion.coordenadas, *vecina.coordenadas)

    estilo.cabecera(estacion.nombre, f"{estacion.provincia} · código {codigo}", None,
                    [estilo.chip("LAT", geo.a_sexagesimal(estacion.lat, True)),
                     estilo.chip("LON", geo.a_sexagesimal(estacion.lon, False))],
                    etiqueta="FICHA DE ESTACIÓN")
    with st.container(key="panel-ficha"):
        estilo.ficha({
            "Coordenadas": f"{estacion.lat:.4f}, {estacion.lon:.4f}",
            "Sistema": "WGS84 · EPSG:4326",
            "Altitud": f"{estacion.altitud:.0f} m",
            "Vecina más cercana": vecina.nombre,
            "Distancia y rumbo": f"{distancia:.1f} km al {geo.punto_cardinal(rumbo)} ({rumbo:.0f}°)",
            "Mediciones válidas": f"{len(propias)} h",
        })

    maxima = propias.loc[propias[variable].idxmax()]
    minima = propias.loc[propias[variable].idxmin()]
    diarias = propias.groupby(propias["fecha_hora"].dt.date)[variable].mean()
    tarjetas = [
        {"titulo": "Media del periodo", "valor": f"{propias[variable].mean():.1f}",
         "unidad": unidad, "sub": escalas.clase(variable, propias[variable].mean()),
         "color": escalas.color(variable, propias[variable].mean()), "serie": diarias.tolist()},
        {"titulo": "Máximo", "valor": f"{maxima[variable]:.1f}", "unidad": unidad,
         "sub": f"{maxima['fecha_hora']:%d/%m %H:00}",
         "color": escalas.color(variable, maxima[variable]),
         "serie": propias.groupby(propias["fecha_hora"].dt.date)[variable].max().tolist()},
        {"titulo": "Mínimo", "valor": f"{minima[variable]:.1f}", "unidad": unidad,
         "sub": f"{minima['fecha_hora']:%d/%m %H:00}",
         "color": escalas.color(variable, minima[variable]),
         "serie": propias.groupby(propias["fecha_hora"].dt.date)[variable].min().tolist()},
    ]
    if variable in UMBRALES_OMS:
        umbral = UMBRALES_OMS[variable]
        tarjetas.append({"titulo": "Días sobre guía OMS", "valor": str(int((diarias > umbral).sum())),
                         "unidad": f"de {len(diarias)}", "sub": f"Media diaria > {umbral} {unidad}",
                         "color": estilo.ROJO})
    else:
        tarjetas.append({"titulo": "Variabilidad", "valor": f"{propias[variable].std():.1f}",
                         "unidad": unidad, "sub": "Desviación típica horaria",
                         "color": estilo.VIOLETA})
    estilo.tarjetas(tarjetas, nota="Las líneas de las tarjetas recorren el periodo día a día.")

    izquierda, derecha = st.columns([1.5, 1], gap="medium")
    with izquierda, st.container(key="panel-mini-mapa"):
        momento = datos.momento()
        estilo.seccion(f"Situación y vecinas · {escala['nombre']} el {momento:%d/%m %H:00}",
                       "La estación elegida va resaltada en cian; los arcos la unen con sus "
                       "cinco vecinas más cercanas.")
        valores = datos.valores(actuales, variable, momento)
        arcos = pd.DataFrame([{"origen": [estacion.lon, estacion.lat], "destino": [v.lon, v.lat],
                               "nombre": v.nombre, "provincia": v.provincia,
                               "etiqueta": f"{d:.0f} km"} for v, d in vecinas])
        extra = [pdk.Layer("ArcLayer", arcos, id="vecinas", get_source_position="origen",
                           get_target_position="destino", get_source_color=capas.CIAN,
                           get_target_color=[167, 139, 250], get_width=3, pickable=True)]
        if codigo in valores:
            # Funda cian translúcida alrededor de la columna de la estación elegida
            propia = capas.tabla_estaciones(actuales.red, variable, {codigo: valores[codigo]}, 1)
            extra.append(pdk.Layer(
                "ColumnLayer", propia.assign(altura=propia["altura"] + 6000,
                                             etiqueta="Estación elegida"),
                id="eleccion", get_position=["lon", "lat"], get_elevation="altura",
                radius=10_000, disk_resolution=24, get_fill_color=[*capas.CIAN, 70],
                extruded=True, pickable=False))
        lejana = max(d for _, d in vecinas)
        grados = lejana / 111 + 0.3
        vista = capas.vista_inclinada((estacion.lat - grados, estacion.lon - grados * 1.3,
                                       estacion.lat + grados, estacion.lon + grados * 1.3),
                                      ancho=700, alto=420, alejar=0.3)
        st.pydeck_chart(capas.mapa(actuales.red, variable, valores, "",
                                   vista_inicial=vista, extra=extra),
                        height=420, key=f"mapa-ficha-{codigo}",
                        alt=f"Situación de {estacion.nombre} y sus cinco vecinas")
    with derecha, st.container(key="panel-reparto-ajustado"):
        estilo.seccion("Horas en cada clase de la escala",
                       "Cuánto tiempo del periodo ha pasado la estación en cada clase oficial. "
                       "La barra es la parte del total.")
        clases = propias[variable].map(lambda valor: escalas.clase(variable, valor))
        reparto = clases.value_counts().reindex(escalas.etiquetas(variable), fill_value=0)
        total = int(reparto.sum()) or 1

        def porcentaje(horas: int) -> str:
            """Porcentaje redondeado, sin dar 0 % ni 100 % a una parte que no lo es."""
            parte = 100 * horas / total
            if 0 < parte < 1:
                return "<1 %"
            if 99 < parte < 100:
                return ">99 %"
            return f"{parte:.0f} %"

        estilo.barras([(nombre, int(horas), tono, f"{horas:.0f} h · {porcentaje(horas)}")
                       for (nombre, horas), tono in zip(reparto.items(), escala["colores"])],
                      maximo=total, posiciones=False)

    izquierda, derecha = st.columns(2, gap="medium")
    with izquierda, st.container(key="panel-ciclo-estacion"):
        estilo.seccion("Ciclo diario: estación frente a la red",
                       "Valor medio a cada hora del día. Si la línea continua va por encima de "
                       "la discontinua, la estación supera a la media de la red a esa hora.")
        ciclo = pd.DataFrame({
            "hora": [f"{h:02d}:00" for h in range(24)],
            "estacion": analisis.ciclo_diario(propias, variable).reindex(range(24)).to_numpy(),
            "red": analisis.ciclo_diario(tabla, variable).reindex(range(24)).to_numpy(),
        })
        estilo.grafico({
            "tooltip": {"trigger": "axis", "valueFormatter": "%.1f"},
            "legend": {"textStyle": {"color": "#CBD5E1"}},
            "dataset": {"source": ciclo},
            "xAxis": {"type": "category"}, "yAxis": {"type": "value", "scale": True},
            "series": [
                {"name": estacion.nombre, "type": "line", "smooth": True, "symbolSize": 6,
                 "encode": {"x": "hora", "y": "estacion"}, "lineStyle": {"width": 3},
                 "areaStyle": {"opacity": 0.15}},
                {"name": "Media de la red", "type": "line", "smooth": True, "showSymbol": False,
                 "encode": {"x": "hora", "y": "red"}, "lineStyle": {"type": "dashed"}},
            ],
        }, height=340, alt=f"Ciclo diario de {estacion.nombre} frente a la red")
    with derecha, st.container(key="panel-huella"):
        estilo.seccion("Huella horaria: día × hora",
                       "Cada fila es un día y cada columna una hora, con el color de la clase "
                       "oficial. Las bandas verticales son patrones que se repiten cada día.")
        huella = propias.assign(dia=propias["fecha_hora"].dt.strftime("%d/%m"),
                                hora=propias["fecha_hora"].dt.strftime("%H"))
        estilo.grafico({
            "tooltip": {"position": "top"},
            "dataset": {"source": huella[["hora", "dia", variable]].round(1)},
            "grid": {"left": 50, "right": 10, "top": 10, "bottom": 30},
            "xAxis": {"type": "category"}, "yAxis": {"type": "category"},
            "visualMap": {"show": False, "type": "piecewise", "dimension": 2, "pieces": piezas},
            "series": [{"type": "heatmap", "encode": {"x": "hora", "y": "dia"},
                        "itemStyle": {"borderColor": "#0B1120", "borderWidth": 1}}],
        }, height=340, alt=f"{escala['nombre']} de {estacion.nombre} por día y hora")


def comparar() -> None:
    """Varias estaciones a la vez: series, ciclo diario, medias diarias y estadísticas."""
    preferidas = [c for c in ("MAD01", "BCN01", "SEV01") if c in nombres] or list(nombres)[:3]
    elegidas = st.multiselect("Estaciones (de 2 a 4)", list(nombres), default=preferidas,
                              format_func=nombres.get, max_selections=4, key="comp_estaciones",
                              persist_state="session")
    if len(elegidas) < 2:
        st.info("Elige al menos dos estaciones para comparar.", icon=":material/info:")
        return
    filas = tabla[tabla["codigo"].isin(elegidas)]
    ancha = filas.pivot_table(index="fecha_hora", columns="codigo", values=variable)
    ancha = ancha.rename(columns=nombres).round(1).reset_index()
    ancha["fecha_hora"] = ancha["fecha_hora"].dt.strftime("%Y-%m-%d %H:%M")
    estilo.cabecera("Comparador de estaciones", " · ".join(nombres[c] for c in elegidas), None,
                    [estilo.chip("VARIABLE", escala["nombre"]),
                     estilo.chip("ESTACIONES", str(len(elegidas)))], etiqueta="COMPARADOR")

    resumen = analisis.ranking(filas, variable)
    estilo.tarjetas([{"titulo": fila.nombre, "valor": f"{fila.media:.1f}", "unidad": unidad,
                      "sub": f"Mín. {fila.minimo:.1f} · Máx. {fila.maximo:.1f}",
                      "color": escalas.color(variable, fila.media),
                      "serie": filas[filas["codigo"] == fila.codigo]
                      .groupby(filas["fecha_hora"].dt.date)[variable].mean().tolist()}
                     for fila in resumen.itertuples()],
                    nota="Media del periodo; la línea de cada tarjeta es su media día a día.")

    with st.container(key="panel-series"):
        estilo.seccion("Serie horaria completa",
                       "Arrastra sobre el gráfico o usa la barra inferior para acercar un tramo.")
        estilo.grafico({
            "tooltip": {"trigger": "axis", "valueFormatter": "%.1f"},
            "legend": {"textStyle": {"color": "#CBD5E1"}},
            "dataset": {"source": ancha},
            "grid": {"left": 50, "right": 20, "top": 40, "bottom": 70},
            "xAxis": {"type": "time"}, "yAxis": {"type": "value", "scale": True, "name": unidad},
            "dataZoom": [{"type": "inside"}, {"type": "slider", "height": 18}],
            "series": [{"name": nombres[c], "type": "line", "showSymbol": False,
                        "sampling": "lttb", "encode": {"x": "fecha_hora", "y": nombres[c]}}
                       for c in elegidas],
        }, height=400, alt=f"{escala['nombre']} hora a hora en las estaciones elegidas")

    izquierda, derecha = st.columns(2, gap="medium")
    with izquierda, st.container(key="panel-ciclos"):
        estilo.seccion("Ciclo diario", "Valor medio de cada estación a cada hora del día.")
        ciclos = filas.pivot_table(index=filas["fecha_hora"].dt.hour, columns="codigo",
                                   values=variable).rename(columns=nombres).round(1)
        ciclos.index = [f"{h:02d}:00" for h in ciclos.index]
        ciclos = ciclos.rename_axis("hora").reset_index()
        estilo.grafico({
            "tooltip": {"trigger": "axis", "valueFormatter": "%.1f"},
            "legend": {"textStyle": {"color": "#CBD5E1"}},
            "dataset": {"source": ciclos},
            "xAxis": {"type": "category"}, "yAxis": {"type": "value", "scale": True},
            "series": [{"name": nombres[c], "type": "line", "smooth": True, "showSymbol": False,
                        "lineStyle": {"width": 3}, "encode": {"x": "hora", "y": nombres[c]}}
                       for c in elegidas],
        }, height=340, alt="Ciclo diario medio de cada estación elegida")
    with derecha, st.container(key="panel-diarias"):
        estilo.seccion("Media diaria", "Media de cada día, estación a estación.")
        diarias = filas.pivot_table(index=filas["fecha_hora"].dt.strftime("%d/%m"),
                                    columns="codigo", values=variable)
        diarias = diarias.rename(columns=nombres).round(1).rename_axis("dia").reset_index()
        estilo.grafico({
            "tooltip": {"trigger": "axis", "valueFormatter": "%.1f"},
            "legend": {"textStyle": {"color": "#CBD5E1"}},
            "dataset": {"source": diarias},
            "xAxis": {"type": "category"}, "yAxis": {"type": "value", "scale": True},
            "series": [{"name": nombres[c], "type": "bar", "encode": {"x": "dia", "y": nombres[c]},
                        "itemStyle": {"borderRadius": [3, 3, 0, 0]}} for c in elegidas],
        }, height=340, alt="Media diaria de cada estación elegida")


if modo_pagina == "Ficha":
    ficha()
else:
    comparar()
