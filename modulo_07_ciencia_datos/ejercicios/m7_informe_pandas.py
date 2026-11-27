"""Módulo 7 - Ampliación de los ejercicios: el informe de la Práctica 4 con pandas.

``generar_informe`` de la Práctica 4 recorre una lista de diccionarios con
bucles y diccionarios acumuladores. Aquí se calcula lo mismo sobre un
DataFrame con ``groupby`` y se escribe con el mismo formato, de modo que las
dos versiones dan exactamente el mismo texto (lo comprueban los tests).

Uso:

    python m7_informe_pandas.py
"""

from pathlib import Path

import pandas as pd

ANCHO = 44
DATOS = Path(__file__).resolve().parent.parent / "datos"


def a_dataframe(ventas: list[dict]) -> pd.DataFrame:
    """Convierte la lista de ventas del Módulo 4 en un DataFrame con la columna ``importe``.

    Como en la Práctica 4, el importe de cada venta se redondea a dos decimales.
    """
    df = pd.DataFrame(ventas)
    return df.assign(importe=(df["unidades"] * df["precio"]).round(2))


def ranking(df: pd.DataFrame, campo: str) -> pd.Series:
    """Importe total por ``campo``, de mayor a menor y, a igual importe, por orden alfabético."""
    totales = df.groupby(campo)["importe"].sum().round(2).rename_axis("clave").reset_index()
    ordenado = totales.sort_values(["importe", "clave"], ascending=[False, True])
    return ordenado.set_index("clave")["importe"]


def producto_mas_vendido(df: pd.DataFrame) -> str:
    """Producto con más unidades; a igualdad, el primero por orden alfabético. Sin ventas, "-"."""
    if df.empty:
        return "-"
    unidades = df.groupby("producto")["unidades"].sum()
    # groupby ordena el índice, e idxmax devuelve el primero de los empatados
    return str(unidades.idxmax())


def generar_informe(df: pd.DataFrame) -> str:
    """Devuelve el informe con el mismo formato que ``generar_informe`` de la Práctica 4."""
    doble, simple = "=" * ANCHO, "-" * ANCHO
    total = round(float(df["importe"].sum()), 2) if not df.empty else 0.0
    ticket = round(total / len(df), 2) if len(df) else 0.0
    lineas = [
        doble,
        "INFORME DE VENTAS".center(ANCHO).rstrip(),
        doble,
        f"{'Ventas registradas':<30}{len(df):>14}",
        f"{'Importe total':<30}{f'{total:,.2f}':>14}",
        f"{'Ticket medio':<30}{f'{ticket:,.2f}':>14}",
        f"{'Producto más vendido':<30}{producto_mas_vendido(df):>14}",
    ]
    for campo, titulo in [("region", "Por región"), ("categoria", "Por categoría"),
                          ("vendedor", "Por vendedor")]:
        lineas += [simple, titulo]
        lineas += [f"  {clave:<28}{importe:>14,.2f}" for clave, importe in ranking(df, campo).items()]
    lineas.append(doble)
    return "\n".join(lineas)


def main() -> None:
    ventas = pd.read_csv(DATOS / "ventas_2026.csv", encoding="utf-8")
    ventas["importe"] = (ventas["unidades"] * ventas["precio"]).round(2)
    print(generar_informe(ventas))


if __name__ == "__main__":
    main()
