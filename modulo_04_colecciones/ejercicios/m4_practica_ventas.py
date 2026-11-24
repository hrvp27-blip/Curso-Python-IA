"""Módulo 4 - Práctica 4: análisis de ventas en memoria.

Cada venta es un diccionario con las claves "fecha", "vendedor", "region",
"producto", "categoria", "unidades" y "precio". Ninguna función modifica la
lista de ventas que recibe.
"""

from m4_datos_ventas import VENTAS

ANCHO = 44


def importe(venta: dict) -> float:
    """Devuelve el importe de una venta: unidades por precio, con dos decimales.

    >>> importe({"unidades": 3, "precio": 19.9})
    59.7
    """
    return round(venta["unidades"] * venta["precio"], 2)


def total_ventas(ventas: list[dict]) -> float:
    """Devuelve la suma de los importes de todas las ventas, con dos decimales."""
    return round(sum(importe(venta) for venta in ventas), 2)


def filtrar_ventas(ventas: list[dict], *, region: str | None = None,
                   categoria: str | None = None, vendedor: str | None = None,
                   desde: str | None = None, hasta: str | None = None) -> list[dict]:
    """Devuelve las ventas que cumplen todos los criterios indicados.

    Un criterio que vale ``None`` no se aplica. ``desde`` y ``hasta`` son
    fechas ISO y las dos están incluidas en el intervalo.
    """
    # Las fechas ISO se pueden comparar como texto: su orden alfabético
    # coincide con el cronológico.
    return [venta for venta in ventas
            if (region is None or venta["region"] == region)
            and (categoria is None or venta["categoria"] == categoria)
            and (vendedor is None or venta["vendedor"] == vendedor)
            and (desde is None or venta["fecha"] >= desde)
            and (hasta is None or venta["fecha"] <= hasta)]


def importe_por(ventas: list[dict], campo: str) -> dict[str, float]:
    """Agrupa las ventas por ``campo`` y devuelve el importe total de cada grupo.

    Los importes van redondeados a dos decimales.

    >>> importe_por([{"region": "Norte", "unidades": 2, "precio": 10.0}], "region")
    {'Norte': 20.0}
    """
    totales = _sumar_por(ventas, campo, importe)
    return {clave: round(total, 2) for clave, total in totales.items()}


def unidades_por_producto(ventas: list[dict]) -> dict[str, int]:
    """Devuelve las unidades totales vendidas de cada producto."""
    return _sumar_por(ventas, "producto", lambda venta: venta["unidades"])


def _sumar_por(ventas: list[dict], campo: str, valor) -> dict:
    """Agrupa las ventas por ``campo`` y suma ``valor(venta)`` en cada grupo."""
    totales = {}
    for venta in ventas:
        clave = venta[campo]
        totales[clave] = totales.get(clave, 0) + valor(venta)
    return totales


def ranking(ventas: list[dict], campo: str, cantidad: int = 3) -> list[tuple[str, float]]:
    """Devuelve los ``cantidad`` grupos con mayor importe, como tuplas (clave, importe).

    De mayor a menor importe. A igual importe, por orden alfabético de la clave.
    """
    return sorted(importe_por(ventas, campo).items(), key=lambda par: (-par[1], par[0]))[:cantidad]


def producto_mas_vendido(ventas: list[dict]) -> str | None:
    """Devuelve el producto con más unidades vendidas, o ``None`` si no hay ventas.

    En caso de empate, el primero por orden alfabético.
    """
    unidades = unidades_por_producto(ventas)
    # min con (-unidades, nombre): más unidades primero y, a igualdad, orden alfabético
    return min(unidades, key=lambda producto: (-unidades[producto], producto), default=None)


def ticket_medio(ventas: list[dict]) -> float:
    """Devuelve el importe medio por venta, con dos decimales. Sin ventas, 0.0."""
    if not ventas:
        return 0.0
    return round(total_ventas(ventas) / len(ventas), 2)


def _linea_resumen(etiqueta: str, valor) -> str:
    """Línea del resumen: etiqueta a la izquierda en 30 y valor a la derecha en 14."""
    return f"{etiqueta:<30}{valor:>14}"


def _desglose(ventas: list[dict], campo: str, titulo: str) -> list[str]:
    """Título y una línea por grupo, de mayor a menor importe."""
    grupos = ranking(ventas, campo, len(ventas))
    return [titulo] + [f"  {clave:<28}{total:>14,.2f}" for clave, total in grupos]


def generar_informe(ventas: list[dict]) -> str:
    """Devuelve el informe de ventas como texto, con el formato del enunciado."""
    doble = "=" * ANCHO
    simple = "-" * ANCHO
    lineas = [
        doble,
        "INFORME DE VENTAS".center(ANCHO).rstrip(),
        doble,
        _linea_resumen("Ventas registradas", len(ventas)),
        _linea_resumen("Importe total", f"{total_ventas(ventas):,.2f}"),
        _linea_resumen("Ticket medio", f"{ticket_medio(ventas):,.2f}"),
        _linea_resumen("Producto más vendido", producto_mas_vendido(ventas) or "-"),
    ]
    for campo, titulo in [("region", "Por región"), ("categoria", "Por categoría"),
                          ("vendedor", "Por vendedor")]:
        lineas.append(simple)
        lineas.extend(_desglose(ventas, campo, titulo))
    lineas.append(doble)
    return "\n".join(lineas)


def main():
    print(generar_informe(VENTAS))
    print()
    print("Solo la región Sur, segunda quincena:")
    print(generar_informe(filtrar_ventas(VENTAS, region="Sur", desde="2026-10-16")))


if __name__ == "__main__":
    main()
