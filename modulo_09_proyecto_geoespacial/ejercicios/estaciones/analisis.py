"""Análisis de las mediciones con pandas (hito 4). Sin bucles sobre filas."""

from dataclasses import asdict
from datetime import date, datetime

import pandas as pd

from .excepciones import DatosNoValidos
from .modelos import CONTAMINANTES, UMBRALES_OMS, VARIABLES, Estacion, Medicion


def _comprobar(variable: str, validas: tuple[str, ...] = VARIABLES) -> None:
    """Lanza ``DatosNoValidos`` si ``variable`` no está entre las ``validas``."""
    if variable not in validas:
        raise DatosNoValidos(f"Variable no válida: {variable}")


def a_tabla(mediciones: list[Medicion], estaciones: list[Estacion]) -> pd.DataFrame:
    """DataFrame con una fila por medición, ``fecha_hora`` como fecha, las variables como
    ``float`` (ausente = NaN) y las columnas de la estación unidas por código."""
    medidas = pd.DataFrame([asdict(m) for m in mediciones],
                           columns=["codigo", "fecha_hora", *VARIABLES])
    medidas["fecha_hora"] = pd.to_datetime(medidas["fecha_hora"])
    medidas = medidas.astype({variable: "float64" for variable in VARIABLES})
    puntos = pd.DataFrame([asdict(e) for e in estaciones])
    return medidas.merge(puntos, on="codigo", how="left")


def en_momento(tabla: pd.DataFrame, momento: datetime) -> pd.DataFrame:
    """Las filas de la hora ``momento``: una por estación."""
    return tabla[tabla["fecha_hora"] == pd.Timestamp(momento)]


def medias_diarias(tabla: pd.DataFrame, variable: str) -> pd.DataFrame:
    """Media diaria de ``variable``: una fila por día y una columna por estación."""
    _comprobar(variable)
    return tabla.pivot_table(index=tabla["fecha_hora"].dt.normalize().rename("dia"),
                             columns="codigo", values=variable, aggfunc="mean")


def media_nacional_diaria(tabla: pd.DataFrame, variable: str) -> pd.Series:
    """Media de todas las estaciones para cada día."""
    return medias_diarias(tabla, variable).mean(axis="columns")


def excedencias(tabla: pd.DataFrame, contaminante: str) -> pd.Series:
    """Días en que la media diaria del contaminante supera el umbral de la OMS, por estación,
    de más a menos. Las estaciones sin excedencias valen 0."""
    _comprobar(contaminante, CONTAMINANTES)
    diarias = medias_diarias(tabla, contaminante)
    superan = (diarias > UMBRALES_OMS[contaminante]).sum().astype(int)
    return superan.sort_values(ascending=False, kind="stable").rename("dias")


def ranking(tabla: pd.DataFrame, variable: str) -> pd.DataFrame:
    """Media, mínimo y máximo de ``variable`` por estación, ordenado de mayor a menor media."""
    _comprobar(variable)
    resumen = tabla.groupby(["codigo", "nombre"])[variable].agg(
        media="mean", minimo="min", maximo="max")
    return resumen.round(1).sort_values("media", ascending=False).reset_index()


def ciclo_diario(tabla: pd.DataFrame, variable: str) -> pd.Series:
    """Media de ``variable`` para cada hora del día (0 a 23), con todas las estaciones."""
    _comprobar(variable)
    return tabla.groupby(tabla["fecha_hora"].dt.hour.rename("hora"))[variable].mean().round(2)


def indicadores(tabla: pd.DataFrame, dia: date) -> dict:
    """Cifras principales de un día, con tipos de Python (no de NumPy).

    Claves: ``estaciones`` con dato, ``temperatura_media``,
    ``mas_calida`` y ``mas_fria`` (código de la estación por media diaria) y
    ``superan_pm25`` / ``superan_no2`` (estaciones cuya media diaria supera
    el umbral de la OMS).
    """
    del_dia = tabla[tabla["fecha_hora"].dt.date == dia]
    if del_dia.empty:
        raise DatosNoValidos(f"No hay mediciones del {dia:%d/%m/%Y}")
    medias = del_dia.groupby("codigo")[list(VARIABLES)].mean()
    return {
        "estaciones": int(medias["temperatura"].notna().sum()),
        "temperatura_media": round(float(medias["temperatura"].mean()), 1),
        "mas_calida": str(medias["temperatura"].idxmax()),
        "mas_fria": str(medias["temperatura"].idxmin()),
        **{f"superan_{c}": int((medias[c] > UMBRALES_OMS[c]).sum()) for c in CONTAMINANTES},
    }
