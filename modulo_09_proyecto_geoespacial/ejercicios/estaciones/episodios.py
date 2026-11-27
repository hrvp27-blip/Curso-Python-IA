"""Episodios: tramos de horas seguidas en que una estación supera (o no llega a) un umbral."""

import pandas as pd

from .excepciones import DatosNoValidos
from .modelos import VARIABLES

COLUMNAS = ["codigo", "nombre", "provincia", "inicio", "fin", "horas", "pico", "media"]


def detectar(tabla: pd.DataFrame, variable: str, umbral: float, minimo_horas: int = 3,
             por_debajo: bool = False) -> pd.DataFrame:
    """Episodios de al menos ``minimo_horas`` horas seguidas por encima de ``umbral``.

    Con ``por_debajo=True`` busca horas por debajo (por ejemplo, heladas).
    Una hora sin dato corta el episodio. Devuelve un DataFrame con
    ``COLUMNAS`` ordenado por inicio; ``pico`` es el valor más extremo.
    """
    if variable not in VARIABLES:
        raise DatosNoValidos(f"Variable no válida: {variable}")
    ordenada = tabla.sort_values(["codigo", "fecha_hora"]).reset_index(drop=True)
    activo = ordenada[variable] < umbral if por_debajo else ordenada[variable] > umbral
    otra_estacion = ordenada["codigo"] != ordenada["codigo"].shift()
    salto = ordenada["fecha_hora"].diff() != pd.Timedelta(hours=1)
    tramo = ((activo != activo.shift()) | otra_estacion | salto).cumsum()
    dentro = ordenada[activo].assign(tramo=tramo[activo])
    if dentro.empty:
        return pd.DataFrame(columns=COLUMNAS)
    episodios = dentro.groupby("tramo").agg(
        codigo=("codigo", "first"), nombre=("nombre", "first"), provincia=("provincia", "first"),
        inicio=("fecha_hora", "min"), fin=("fecha_hora", "max"), horas=("fecha_hora", "size"),
        pico=(variable, "min" if por_debajo else "max"), media=(variable, "mean"),
    )
    episodios = episodios[episodios["horas"] >= minimo_horas]
    return episodios.round({"pico": 1, "media": 1}).sort_values("inicio").reset_index(drop=True)


def activos(episodios: pd.DataFrame, momento) -> pd.DataFrame:
    """Los episodios que están en marcha en ``momento``."""
    momento = pd.Timestamp(momento)
    return episodios[(episodios["inicio"] <= momento) & (episodios["fin"] >= momento)]


def por_estacion(episodios: pd.DataFrame) -> pd.DataFrame:
    """Número de episodios, horas totales y pico por estación, de más a menos horas."""
    resumen = episodios.groupby(["codigo", "nombre"]).agg(
        episodios=("inicio", "size"), horas=("horas", "sum"), pico=("pico", "max"))
    return resumen.sort_values("horas", ascending=False).reset_index()
