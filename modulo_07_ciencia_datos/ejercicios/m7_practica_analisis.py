"""Módulo 7 - Práctica 7: análisis de las ventas del año.

Un pequeño proceso de análisis completo: cargar, limpiar, calcular indicadores,
generar gráficos y exportar los resultados.

Uso:

    python m7_practica_analisis.py

Ampliaciones (las funciones del enunciado conservan su contrato, para que
sus tests sigan valiendo; lo nuevo va en parámetros opcionales o en
funciones aparte):

1. ``indicadores(df, ampliados=True)`` añade la región con mayor ticket medio
   y el día de la semana con más ventas.
2. ``grafico_categoria_region`` guarda un panel de dos ejes: importe por
   categoría y por región.
3. ``exportar_excel`` escribe varias tablas en un único Excel, una hoja por
   tabla. Necesita ``pip install openpyxl``.
4. ``preparar_con_motivos`` devuelve, además de las ventas, cuántas filas se
   han descartado por cada motivo, como el importador de la Práctica 6.
5. ``desde_importador`` valida el fichero con ``importar_ventas`` de la
   Práctica 6 y construye el DataFrame con las ventas que devuelve.
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Se reutiliza lo hecho en los ejercicios 3 y 5, que están en esta misma carpeta
from m7_ej3_limpieza import convertir_tipos, normalizar_texto, quitar_duplicados, rellenar_region
from m7_ej5_graficos import grafico_barras, grafico_lineas, guardar

# Ampliación 5: la Práctica 6 está en otra carpeta del curso. Con pytest ya
# está en el path gracias a conftest.py; así también funciona al ejecutar
# este fichero directamente.
CARPETA_PRACTICA_6 = Path(__file__).resolve().parents[2] / "modulo_06_archivos_excepciones" / "ejercicios"
if str(CARPETA_PRACTICA_6) not in sys.path:
    sys.path.append(str(CARPETA_PRACTICA_6))

from m6_practica_importador import CAMPOS, importar_ventas  # noqa: E402

DATOS = Path(__file__).resolve().parent.parent / "datos"
SALIDA = Path(__file__).resolve().parent / "salida_practica_7"
COLUMNAS_TEXTO = ["vendedor", "region", "producto", "categoria"]
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


def cargar(ruta: str | Path) -> pd.DataFrame:
    """Lee el CSV de ventas con todas las columnas como texto."""
    return pd.read_csv(ruta, encoding="utf-8", dtype=str)


def preparar(df: pd.DataFrame) -> pd.DataFrame:
    """Devuelve las ventas limpias y con las columnas calculadas.

    1. Texto sin espacios sobrantes y con la inicial en mayúscula.
    2. Sin filas duplicadas.
    3. ``fecha`` como fecha (formato "AAAA-MM-DD"), ``unidades`` y ``precio``
       como números. ``precio`` admite coma decimal.
    4. Las regiones ausentes pasan a ser "Sin región".
    5. Se descartan las filas sin fecha, vendedor, unidades o precio válidos, y
       las que tienen unidades o precio menores o iguales que cero.
    6. ``unidades`` queda como entero.
    7. Columnas nuevas: ``importe`` (unidades por precio) y ``mes`` ("AAAA-MM").
    8. Filas ordenadas por fecha, con el índice renumerado desde 0. A igual
       fecha se conserva el orden original.

    No modifica el DataFrame recibido.
    """
    ventas, _ = preparar_con_motivos(df)
    return ventas


def preparar_con_motivos(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, int]]:
    """Ampliación 4: hace lo mismo que ``preparar`` y cuenta las filas descartadas.

    Devuelve una tupla (ventas preparadas, motivos). ``motivos`` es un
    diccionario con cuántas filas se han descartado por cada motivo; solo
    aparecen los motivos que se han dado. Cada fila cuenta una sola vez, por
    el primer motivo de esta lista, en el mismo orden que comprueba
    ``validar_fila`` en la Práctica 6:

    - "fila repetida"
    - "fecha no válida"
    - "falta el vendedor"
    - "unidades no válidas"
    - "precio no válido"
    """
    # Pasos 1 a 4: la limpieza del Ejercicio 3, función a función para poder contar
    normalizado = normalizar_texto(df)
    sin_repetidas = quitar_duplicados(normalizado)
    datos = rellenar_region(convertir_tipos(sin_repetidas))

    # Paso 5: se decide el motivo de descarte de todas las filas a la vez
    condiciones = [
        datos["fecha"].isna(),
        datos["vendedor"].isna(),
        ~(datos["unidades"] > 0),   # ausente (NaN) también da False en "> 0"
        ~(datos["precio"] > 0),
    ]
    nombres = ["fecha no válida", "falta el vendedor", "unidades no válidas", "precio no válido"]
    motivo = pd.Series(np.select(condiciones, nombres, default=""), index=datos.index)

    motivos = {"fila repetida": len(normalizado) - len(sin_repetidas)}
    motivos.update(motivo[motivo != ""].value_counts().to_dict())
    motivos = {nombre: int(motivos[nombre]) for nombre in ["fila repetida"] + nombres
               if motivos.get(nombre)}

    # Pasos 6 a 8
    limpio = datos[motivo == ""].astype({"unidades": int})
    limpio["importe"] = limpio["unidades"] * limpio["precio"]
    limpio["mes"] = limpio["fecha"].dt.strftime("%Y-%m")
    # "stable" conserva el orden original entre ventas del mismo día
    return limpio.sort_values("fecha", kind="stable").reset_index(drop=True), motivos


def desde_importador(ruta: str | Path, coma_decimal: bool = True) -> tuple[pd.DataFrame, list[str]]:
    """Ampliación 5: valida el fichero con la Práctica 6 y prepara el DataFrame.

    ``importar_ventas`` descarta las filas no válidas y devuelve sus errores
    ("Línea N: motivo"). Con las ventas válidas se construye un DataFrame de
    texto, igual que el que devuelve ``cargar``, y se pasa por ``preparar``,
    que normaliza el texto, quita las repetidas que solo se distinguían por
    mayúsculas o espacios y calcula ``importe`` y ``mes``.

    Por defecto se acepta la coma decimal, como en ``preparar``. Las reglas
    de la Práctica 6 son más estrictas en un punto: una fila sin región se
    descarta en lugar de pasar a "Sin región". Con ``ventas_sucias.csv``
    quedan 52 ventas en lugar de 54: las dos que no tienen región.

    Lanza ``FicheroNoValido`` (de la Práctica 6) si el fichero no existe o le
    faltan columnas. Devuelve una tupla (ventas preparadas, errores).
    """
    ventas, errores = importar_ventas(ruta, coma_decimal=coma_decimal)
    texto = pd.DataFrame(ventas, columns=CAMPOS).astype(str)
    return preparar(texto), errores


def indicadores(df: pd.DataFrame, ampliados: bool = False) -> dict:
    """Devuelve los indicadores principales de unas ventas preparadas.

    Claves:

    - "ventas": número de ventas (int).
    - "importe_total": float con dos decimales.
    - "ticket_medio": importe medio por venta, float con dos decimales.
    - "mejor_vendedor": el de mayor importe total.
    - "mejor_mes": el mes "AAAA-MM" de mayor importe total.
    - "producto_mas_vendido": el de más unidades.

    Ampliación 1: con ``ampliados=True`` se añaden dos claves más:

    - "region_mayor_ticket": la región con mayor importe medio por venta.
    - "dia_mas_ventas": el día de la semana ("lunes", "martes"...) con más ventas.
    """
    resultado = {
        "ventas": len(df),
        "importe_total": round(float(df["importe"].sum()), 2),
        "ticket_medio": round(float(df["importe"].mean()), 2),
        "mejor_vendedor": str(df.groupby("vendedor")["importe"].sum().idxmax()),
        "mejor_mes": str(df.groupby("mes")["importe"].sum().idxmax()),
        "producto_mas_vendido": str(df.groupby("producto")["unidades"].sum().idxmax()),
    }
    if ampliados:
        dia = df["fecha"].dt.day_of_week.map(dict(enumerate(DIAS)))
        resultado["region_mayor_ticket"] = str(df.groupby("region")["importe"].mean().idxmax())
        resultado["dia_mas_ventas"] = str(dia.value_counts().idxmax())
    return resultado


def ranking_vendedores(df: pd.DataFrame, objetivos: pd.DataFrame) -> pd.DataFrame:
    """Devuelve una fila por vendedor, de mayor a menor importe.

    Columnas, en este orden: vendedor, ventas, importe, objetivo, cumplimiento
    y cumplido. ``importe`` va redondeado a dos decimales, ``cumplimiento`` es
    el porcentaje del objetivo alcanzado con un decimal y ``cumplido`` indica
    si el importe llega al objetivo. El índice va de 0 en adelante.

    ``objetivos`` tiene las columnas vendedor y objetivo.
    """
    ranking = (
        df.groupby("vendedor")
        .agg(ventas=("importe", "size"), importe=("importe", "sum"))
        .reset_index()
        .merge(objetivos[["vendedor", "objetivo"]], on="vendedor", how="left")
        .sort_values("importe", ascending=False)
        .reset_index(drop=True)
    )
    ranking["cumplimiento"] = (ranking["importe"] / ranking["objetivo"] * 100).round(1)
    ranking["cumplido"] = ranking["importe"] >= ranking["objetivo"]
    ranking["importe"] = ranking["importe"].round(2)
    return ranking


def evolucion_mensual(df: pd.DataFrame) -> pd.DataFrame:
    """Devuelve una fila por mes, en orden, con las columnas mes, importe y variacion.

    ``importe`` va redondeado a dos decimales. ``variacion`` es el cambio en
    porcentaje respecto al mes anterior, con un decimal; en el primer mes es
    un valor ausente. El índice va de 0 en adelante.
    """
    mensual = df.groupby("mes")["importe"].sum().sort_index()
    return pd.DataFrame({
        "mes": mensual.index,
        "importe": mensual.round(2).to_numpy(),
        "variacion": (mensual.pct_change() * 100).round(1).to_numpy(),
    })


def generar_graficos(df: pd.DataFrame, carpeta: str | Path) -> list[Path]:
    """Guarda dos gráficos en ``carpeta`` y devuelve sus rutas, en este orden.

    1. ``importe_por_vendedor.png``: barras, de mayor a menor importe.
    2. ``evolucion_mensual.png``: líneas con el importe de cada mes.

    Crea la carpeta si no existe. Cada gráfico lleva título y etiqueta en el
    eje Y. Las figuras se cierran después de guardarlas.
    """
    carpeta = Path(carpeta)
    por_vendedor = df.groupby("vendedor")["importe"].sum().sort_values(ascending=False)
    mensual = df.groupby("mes")["importe"].sum().sort_index()
    return [
        guardar(grafico_barras(por_vendedor, "Importe por vendedor"), carpeta / "importe_por_vendedor.png"),
        guardar(grafico_lineas(mensual, "Evolución mensual del importe"), carpeta / "evolucion_mensual.png"),
    ]


def grafico_categoria_region(df: pd.DataFrame, carpeta: str | Path) -> Path:
    """Ampliación 2: guarda ``importe_por_categoria_y_region.png`` y devuelve su ruta.

    Un panel con dos gráficos de barras, cada uno de mayor a menor importe: a
    la izquierda el importe por categoría y a la derecha por región.
    """
    figura, (izquierda, derecha) = plt.subplots(1, 2, figsize=(13, 5), sharey=True)
    for ejes, columna, titulo, color in [(izquierda, "categoria", "Por categoría", "steelblue"),
                                         (derecha, "region", "Por región", "darkorange")]:
        totales = df.groupby(columna)["importe"].sum().sort_values(ascending=False)
        ejes.bar(totales.index.astype(str), totales.to_numpy(), color=color)
        ejes.set_title(titulo)
        ejes.grid(True, axis="y", alpha=0.3)
    izquierda.set_ylabel("Importe (€)")
    figura.suptitle("Importe por categoría y por región")
    figura.tight_layout()
    return guardar(figura, Path(carpeta) / "importe_por_categoria_y_region.png")


def exportar(tabla: pd.DataFrame, ruta: str | Path) -> None:
    """Escribe la tabla en un CSV en UTF-8, sin la columna del índice.

    Crea la carpeta de destino si no existe.
    """
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    tabla.to_csv(ruta, index=False, encoding="utf-8")


def exportar_excel(tablas: dict[str, pd.DataFrame], ruta: str | Path) -> Path:
    """Ampliación 3: escribe las tablas en un único Excel, una hoja por tabla.

    Las claves del diccionario son los nombres de las hojas. Sin la columna
    del índice. Crea la carpeta de destino si no existe y devuelve la ruta.
    Necesita ``openpyxl`` (``pip install openpyxl``).
    """
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(ruta, engine="openpyxl") as libro:
        for hoja, tabla in tablas.items():
            tabla.to_excel(libro, sheet_name=hoja, index=False)
    return ruta


def main() -> None:
    """Ejecuta el análisis completo con los datos del módulo."""
    ventas = preparar(cargar(DATOS / "ventas_2026.csv"))
    objetivos = pd.read_csv(DATOS / "objetivos.csv")

    print("INDICADORES")
    for nombre, valor in indicadores(ventas).items():
        print(f"  {nombre:<22}{valor}")
    print()
    print("RANKING DE VENDEDORES")
    ranking = ranking_vendedores(ventas, objetivos)
    print(ranking.to_string(index=False))
    print()
    print("EVOLUCIÓN MENSUAL")
    print(evolucion_mensual(ventas).to_string(index=False))

    exportar(ranking, SALIDA / "ranking_vendedores.csv")
    exportar(evolucion_mensual(ventas), SALIDA / "evolucion_mensual.csv")
    for ruta in generar_graficos(ventas, SALIDA):
        print(f"Gráfico guardado en {ruta}")

    # ------------------------------------------------------------ ampliaciones
    print()
    print("AMPLIACIONES")
    ampliados = indicadores(ventas, ampliados=True)
    print(f"  {'region_mayor_ticket':<22}{ampliados['region_mayor_ticket']}")
    print(f"  {'dia_mas_ventas':<22}{ampliados['dia_mas_ventas']}")
    _, motivos = preparar_con_motivos(cargar(DATOS / "ventas_sucias.csv"))
    print(f"  Descartes en ventas_sucias.csv: {motivos}")
    print(f"Gráfico guardado en {grafico_categoria_region(ventas, SALIDA)}")
    try:
        libro = exportar_excel({"ranking": ranking, "evolucion": evolucion_mensual(ventas)},
                               SALIDA / "resultados.xlsx")
    except ImportError:
        print("Para exportar a Excel hace falta instalar openpyxl: pip install openpyxl")
    else:
        print(f"Excel guardado en {libro}")


if __name__ == "__main__":
    main()
