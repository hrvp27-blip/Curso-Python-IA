"""Predicción a corto plazo con un modelo propio: ciclo diario + persistencia de la anomalía.

Idea del modelo, para cada estación:

1. **Ciclo diario**: el valor medio de cada hora del día en los últimos
   ``dias`` días. Es lo que se espera "un día normal" a esa hora.
2. **Anomalía**: cuánto se aleja lo observado de ese ciclo.
3. **Persistencia AR(1)**: la anomalía de ahora se va olvidando poco a poco.
   Dentro de ``k`` horas queda multiplicada por ``phi ** k``, donde ``phi``
   es la autocorrelación horaria de las anomalías.

    predicción(t + k) = ciclo[hora de t + k] + anomalía(t) · phi^k

La incertidumbre crece con el horizonte como la de un proceso AR(1):
``sigma · sqrt(1 - phi^(2k))``. La banda devuelta es de ±1,28 sigmas (80 %).

Se valida con la técnica de origen móvil: se predice desde varios momentos
pasados y se compara con lo que ocurrió de verdad, frente a dos referencias,
la persistencia (mañana igual que ahora) y la climatología (solo el ciclo).
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .excepciones import DatosNoValidos
from .modelos import RANGOS, VARIABLES

Z_80 = 1.2816


@dataclass
class Modelo:
    """Un modelo ajustado para una variable hasta el instante ``desde``."""

    variable: str
    desde: pd.Timestamp
    ciclo: pd.DataFrame
    anomalia: pd.Series
    ultimo: pd.Series
    phi: float
    sigma: float


def _con_anomalias(historia: pd.DataFrame, ciclo: pd.DataFrame, variable: str) -> pd.DataFrame:
    """Añade a la historia el valor esperado por el ciclo diario y la anomalía."""
    esperado = ciclo.stack().rename("esperado")
    historia = historia.assign(hora=historia["fecha_hora"].dt.hour)
    historia = historia.join(esperado, on=["codigo", "hora"])
    return historia.assign(anomalia=historia[variable] - historia["esperado"])


def ajustar(tabla: pd.DataFrame, variable: str, desde, dias: int = 14) -> Modelo:
    """Ajusta el modelo con las mediciones de los ``dias`` días anteriores a ``desde`` (incluido).

    Lanza ``DatosNoValidos`` si la variable no existe o no hay historia suficiente.
    """
    if variable not in VARIABLES:
        raise DatosNoValidos(f"Variable no válida: {variable}")
    desde = pd.Timestamp(desde)
    inicio = desde - pd.Timedelta(days=dias)
    historia = tabla[(tabla["fecha_hora"] > inicio) & (tabla["fecha_hora"] <= desde)]
    historia = historia.dropna(subset=[variable]).sort_values(["codigo", "fecha_hora"])
    if historia["fecha_hora"].dt.normalize().nunique() < 2:
        raise DatosNoValidos(f"Hacen falta al menos dos días de datos antes del {desde:%d/%m/%Y}")

    ciclo = historia.pivot_table(index="codigo", columns=historia["fecha_hora"].dt.hour,
                                 values=variable, aggfunc="mean")
    historia = _con_anomalias(historia, ciclo, variable)
    previa = historia.groupby("codigo")["anomalia"].shift()
    correlacion = historia["anomalia"].corr(previa)
    phi = 0.0 if pd.isna(correlacion) else float(np.clip(correlacion, 0, 0.99))
    ultimas = historia.groupby("codigo").last()
    return Modelo(variable=variable, desde=desde, ciclo=ciclo,
                  anomalia=ultimas["anomalia"].fillna(0), ultimo=ultimas[variable],
                  phi=phi, sigma=float(historia["anomalia"].std()))


def predecir(modelo: Modelo, horas: int = 24, persistencia: bool = True) -> pd.DataFrame:
    """Predicción de las ``horas`` siguientes a ``modelo.desde`` para cada estación.

    Columnas: ``codigo``, ``fecha_hora``, ``paso`` (horas por delante),
    ``prediccion``, ``inferior`` y ``superior`` (banda del 80 %). Con
    ``persistencia=False`` solo se usa el ciclo diario (climatología).
    """
    momentos = modelo.desde + pd.to_timedelta(np.arange(1, horas + 1), unit="h")
    futuro = pd.MultiIndex.from_product([modelo.ciclo.index, momentos],
                                        names=["codigo", "fecha_hora"]).to_frame(index=False)
    futuro["paso"] = (futuro["fecha_hora"] - modelo.desde) // pd.Timedelta(hours=1)
    futuro["hora"] = futuro["fecha_hora"].dt.hour
    futuro = futuro.join(modelo.ciclo.stack().rename("esperado"), on=["codigo", "hora"])
    memoria = modelo.phi ** futuro["paso"] if persistencia else 0
    futuro["prediccion"] = futuro["esperado"] + futuro["codigo"].map(modelo.anomalia) * memoria
    if persistencia:
        dispersion = modelo.sigma * np.sqrt(1 - modelo.phi ** (2 * futuro["paso"]))
    else:
        dispersion = pd.Series(modelo.sigma, index=futuro.index)
    minimo, maximo = RANGOS[modelo.variable]
    futuro["prediccion"] = futuro["prediccion"].clip(minimo, maximo)
    futuro["inferior"] = (futuro["prediccion"] - Z_80 * dispersion).clip(minimo, maximo)
    futuro["superior"] = (futuro["prediccion"] + Z_80 * dispersion).clip(minimo, maximo)
    return futuro[["codigo", "fecha_hora", "paso", "prediccion", "inferior", "superior"]]


def validar(tabla: pd.DataFrame, variable: str, origenes: int = 7,
            horizonte: int = 24) -> pd.DataFrame:
    """Error absoluto medio por horizonte del modelo, la persistencia y la climatología.

    Se predice desde las 23:00 de cada uno de los ``origenes`` días previos
    al último día completo de datos y se compara con lo medido. Devuelve un
    DataFrame indexado por ``paso`` con las columnas ``modelo``,
    ``persistencia`` y ``climatologia``.
    """
    final = tabla["fecha_hora"].max() - pd.Timedelta(hours=horizonte)
    ultimo_origen = final.normalize() - pd.Timedelta(hours=1)
    reales = tabla.set_index(["codigo", "fecha_hora"])[variable].rename("real")
    errores = []
    for dias_atras in range(origenes):
        origen = ultimo_origen - pd.Timedelta(days=dias_atras)
        modelo = ajustar(tabla, variable, origen)
        prevision = predecir(modelo, horizonte).join(reales, on=["codigo", "fecha_hora"])
        prevision["clima"] = predecir(modelo, horizonte, persistencia=False)["prediccion"]
        prevision["persistencia"] = prevision["codigo"].map(modelo.ultimo)
        errores.append(prevision.assign(
            modelo=(prevision["prediccion"] - prevision["real"]).abs(),
            persistencia=(prevision["persistencia"] - prevision["real"]).abs(),
            climatologia=(prevision["clima"] - prevision["real"]).abs(),
        ))
    todos = pd.concat(errores)
    return todos.groupby("paso")[["modelo", "persistencia", "climatologia"]].mean().round(2)


def resumen_validacion(errores: pd.DataFrame) -> dict:
    """Error medio de cada método y mejora del modelo frente a la persistencia, en %."""
    medias = errores.mean()
    return {
        "modelo": round(float(medias["modelo"]), 2),
        "persistencia": round(float(medias["persistencia"]), 2),
        "climatologia": round(float(medias["climatologia"]), 2),
        "mejora": round(float(100 * (1 - medias["modelo"] / medias["persistencia"])), 1),
    }
