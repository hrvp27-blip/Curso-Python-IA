"""Informes de situación en Markdown, listos para descargar o pegar en un documento."""

from datetime import date

import pandas as pd

from . import episodios
from .escalas import describir, escala
from .excepciones import DatosNoValidos
from .modelos import CATEGORIAS_ICA, LIMITES_ICA, UMBRALES_OMS, VARIABLES, categoria_ica


def _periodo(tabla: pd.DataFrame, dia: date | None) -> tuple[pd.DataFrame, str]:
    """Las filas del día pedido (o todas) y el texto que describe el periodo."""
    if dia is None:
        inicio, fin = tabla["fecha_hora"].min(), tabla["fecha_hora"].max()
        return tabla, f"del {inicio:%d/%m/%Y} al {fin:%d/%m/%Y}"
    filas = tabla[tabla["fecha_hora"].dt.date == dia]
    if filas.empty:
        raise DatosNoValidos(f"No hay mediciones del {dia:%d/%m/%Y}")
    return filas, f"del {dia:%d/%m/%Y}"


def _seccion_variable(filas: pd.DataFrame, variable: str) -> list[str]:
    """Líneas del informe de una variable."""
    datos = escala(variable)
    validas = filas.dropna(subset=[variable])
    maxima = validas.loc[validas[variable].idxmax()]
    minima = validas.loc[validas[variable].idxmin()]
    medias = validas.groupby("nombre")[variable].mean().sort_values(ascending=False)
    lineas = [
        f"### {datos['nombre']} ({datos['unidad']})",
        "",
        f"- Media de la red: **{validas[variable].mean():.1f} {datos['unidad']}**",
        f"- Máximo: {describir(variable, maxima[variable])} en {maxima['nombre']}, "
        f"{maxima['fecha_hora']:%d/%m %H:00}",
        f"- Mínimo: {describir(variable, minima[variable])} en {minima['nombre']}, "
        f"{minima['fecha_hora']:%d/%m %H:00}",
        f"- Media más alta: {medias.index[0]} ({medias.iloc[0]:.1f}); "
        f"más baja: {medias.index[-1]} ({medias.iloc[-1]:.1f})",
    ]
    if variable in LIMITES_ICA:
        categorias = validas[variable].map(lambda valor: categoria_ica(variable, valor))
        reparto = categorias.value_counts(normalize=True).reindex(CATEGORIAS_ICA, fill_value=0)
        lineas += ["", "| Categoría ICA | % de las horas |", "| --- | ---: |"]
        lineas += [f"| {nombre} | {100 * parte:.1f} |" for nombre, parte in reparto.items()]
    if variable in UMBRALES_OMS:
        umbral = UMBRALES_OMS[variable]
        diarias = validas.groupby(["codigo", validas["fecha_hora"].dt.date])[variable].mean()
        lineas += ["", f"- Días-estación con la media diaria sobre la guía OMS ({umbral}): "
                       f"**{int((diarias > umbral).sum())}**"]
        encontrados = episodios.detectar(validas, variable, umbral)
        lineas.append(f"- Episodios de 3 h o más sobre la guía: **{len(encontrados)}**")
    return [*lineas, ""]


def informe(tabla: pd.DataFrame, dia: date | None = None,
            variables: tuple[str, ...] = VARIABLES) -> str:
    """Informe en Markdown de un día (o de todo el periodo si ``dia`` es None)."""
    filas, periodo = _periodo(tabla, dia)
    lineas = [
        f"# Informe de la red nacional de estaciones {periodo}",
        "",
        f"- Estaciones: **{filas['codigo'].nunique()}**",
        f"- Mediciones horarias: **{len(filas):,}**".replace(",", "."),
        f"- Datos ausentes: **{100 * filas[list(variables)].isna().mean().mean():.1f} %**",
        "",
        "## Resumen por variable",
        "",
    ]
    for variable in variables:
        lineas += _seccion_variable(filas, variable)
    lineas += ["---", "Calidad del aire según el Índice Nacional de Calidad del Aire (MITECO) "
                      "y la guía de la OMS de 2021 para medias de 24 horas."]
    return "\n".join(lineas)
