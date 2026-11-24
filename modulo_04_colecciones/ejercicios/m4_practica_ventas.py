"""Módulo 4 - Práctica 4: análisis de ventas en memoria.

Cada venta es un diccionario con las claves "fecha", "vendedor", "region",
"producto", "categoria", "unidades" y "precio". Ninguna función modifica la
lista de ventas que recibe.
"""

from datetime import date

from m4_datos_ventas import VENTAS

ANCHO = 44
MEDIDAS = ("importe", "unidades")


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


def unidades_por(ventas: list[dict], campo: str) -> dict[str, int]:
    """Agrupa las ventas por ``campo`` y devuelve las unidades totales de cada grupo.

    >>> unidades_por([{"region": "Norte", "unidades": 2}, {"region": "Norte", "unidades": 3}], "region")
    {'Norte': 5}
    """
    return _sumar_por(ventas, campo, lambda venta: venta["unidades"])


def unidades_por_producto(ventas: list[dict]) -> dict[str, int]:
    """Devuelve las unidades totales vendidas de cada producto."""
    return unidades_por(ventas, "producto")


def _sumar_por(ventas: list[dict], campo: str, valor) -> dict:
    """Agrupa las ventas por ``campo`` y suma ``valor(venta)`` en cada grupo."""
    totales = {}
    for venta in ventas:
        clave = venta[campo]
        totales[clave] = totales.get(clave, 0) + valor(venta)
    return totales


def ranking(ventas: list[dict], campo: str, cantidad: int = 3, *,
            medida: str = "importe") -> list[tuple[str, float]]:
    """Devuelve los ``cantidad`` grupos con mayor importe, como tuplas (clave, importe).

    De mayor a menor importe. A igual importe, por orden alfabético de la clave.
    Con ``medida="unidades"`` ordena por unidades vendidas en lugar de por importe.

    >>> ventas = [{"region": "Norte", "unidades": 1, "precio": 100.0},
    ...           {"region": "Sur", "unidades": 5, "precio": 10.0}]
    >>> ranking(ventas, "region")
    [('Norte', 100.0), ('Sur', 50.0)]
    >>> ranking(ventas, "region", medida="unidades")
    [('Sur', 5), ('Norte', 1)]
    """
    if medida not in MEDIDAS:
        raise ValueError(f"medida debe ser una de {MEDIDAS}, no {medida!r}")
    totales = importe_por(ventas, campo) if medida == "importe" else unidades_por(ventas, campo)
    return sorted(totales.items(), key=lambda par: (-par[1], par[0]))[:cantidad]


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


def semana(venta: dict) -> str:
    """Devuelve la semana ISO de la venta con el formato ``AAAA-Snn``.

    >>> semana({"fecha": "2026-10-01"})
    '2026-S40'
    """
    anio, numero, _ = date.fromisoformat(venta["fecha"]).isocalendar()
    return f"{anio}-S{numero:02d}"


def importe_por_semana(ventas: list[dict]) -> dict[str, float]:
    """Devuelve el importe total de cada semana ISO, en orden cronológico."""
    # Copia de cada venta con el campo "semana" añadido: no se tocan los originales
    con_semana = [{**venta, "semana": semana(venta)} for venta in ventas]
    return dict(sorted(importe_por(con_semana, "semana").items()))


def comparar_periodos(ventas: list[dict], corte: str) -> float | None:
    """Devuelve la variación en porcentaje del importe entre dos periodos.

    El primer periodo son las ventas anteriores a ``corte`` y el segundo, las
    de ``corte`` en adelante. Redondea a dos decimales. Si el primer periodo
    no tiene importe devuelve ``None``, porque no se puede dividir entre cero.

    >>> ventas = [{"fecha": "2026-10-01", "unidades": 1, "precio": 100.0},
    ...           {"fecha": "2026-10-20", "unidades": 1, "precio": 150.0}]
    >>> comparar_periodos(ventas, "2026-10-16")
    50.0
    """
    anterior = total_ventas([venta for venta in ventas if venta["fecha"] < corte])
    posterior = total_ventas(filtrar_ventas(ventas, desde=corte))
    if not anterior:
        return None
    return round((posterior - anterior) / anterior * 100, 2)


def mejor_vendedor_por_region(ventas: list[dict]) -> dict[str, str]:
    """Devuelve el vendedor con mayor importe de cada región.

    A igual importe, el primero por orden alfabético, igual que en ``ranking``.
    """
    return {
        region: ranking(filtrar_ventas(ventas, region=region), "vendedor", 1)[0][0]
        for region in importe_por(ventas, "region")
    }


def _linea_resumen(etiqueta: str, valor) -> str:
    """Línea del resumen: etiqueta a la izquierda en 30 y valor a la derecha en 14."""
    return f"{etiqueta:<30}{valor:>14}"


def _lineas_grupos(titulo: str, grupos) -> list[str]:
    """Título y una línea por cada par (clave, importe)."""
    return [titulo] + [f"  {clave:<28}{total:>14,.2f}" for clave, total in grupos]


def _desglose(ventas: list[dict], campo: str, titulo: str) -> list[str]:
    """Título y una línea por grupo, de mayor a menor importe."""
    return _lineas_grupos(titulo, ranking(ventas, campo, len(ventas)))


def generar_informe(ventas: list[dict], *, por_semana: bool = False) -> str:
    """Devuelve el informe de ventas como texto, con el formato del enunciado.

    Con ``por_semana=True`` añade al final un desglose «Por semana», en orden
    cronológico.
    """
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
    if por_semana:
        lineas.append(simple)
        lineas.extend(_lineas_grupos("Por semana", importe_por_semana(ventas).items()))
    lineas.append(doble)
    return "\n".join(lineas)


def main():
    print(generar_informe(VENTAS))
    print()
    print("Solo la región Sur, segunda quincena:")
    print(generar_informe(filtrar_ventas(VENTAS, region="Sur", desde="2026-10-16")))


if __name__ == "__main__":
    main()
