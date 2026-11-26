"""Módulo 6 - Ejercicio 4: programa de ``ejemplos/06_para_depurar.py`` corregido.

El original se deja intacto en ``ejemplos/``. La salida correcta es:

    Ventas leídas: 20
    Importe total: 21686.80
    Mejor vendedor: Ada (7435.30)

Errores encontrados (las líneas son las del fichero original)
------------------------------------------------------------

1. Línea 31, ``importe``: ``TypeError: can't multiply sequence by non-int
   of type 'str'``.
   Cómo: es el que detiene el programa. La traza apunta a la línea 31; con un
   punto de ruptura ahí, el panel de variables muestra que ``venta`` tiene
   ``'unidades': '2'`` y ``'precio': '950.0'``: ``csv.DictReader`` entrega
   todos los valores como cadenas.
   Cambio: convertir antes de multiplicar, ``int(...)`` y ``float(...)``.

2. Línea 36, ``total``: el bucle recorre ``ventas[1:]`` y se salta la primera
   venta, así que el total sale 1900 € más bajo (19786.80).
   Cómo: punto de ruptura dentro del bucle y F10: la primera ``venta`` que
   aparece es la del 1 de octubre de Linus, no la de Ada. El ``[1:]`` sobra
   porque ``DictReader`` ya consume la cabecera.
   Cambio: ``for venta in ventas:``.

3. Línea 44, ``mejor_vendedor``: ``por_vendedor[...] = importe(venta)``
   sustituye el importe en cada venta en lugar de acumularlo, y el
   diccionario acaba con el importe de la última venta de cada vendedor.
   Cómo: punto de ruptura en el ``max`` y revisar ``por_vendedor`` en el
   panel de variables: los importes son de una sola venta, no la suma.
   Cambio: ``por_vendedor.get(vendedor, 0) + importe(venta)``.
"""

import csv
from pathlib import Path

RUTA = Path(__file__).parent.parent / "datos" / "ventas.csv"


def leer_ventas(ruta):
    with open(ruta, encoding="utf-8", newline="") as fichero:
        return list(csv.DictReader(fichero))


def importe(venta):
    # Error 1: los valores del CSV son cadenas
    return int(venta["unidades"]) * float(venta["precio"])


def total(ventas):
    suma = 0
    for venta in ventas:  # Error 2: antes era ventas[1:]
        suma += importe(venta)
    return suma


def mejor_vendedor(ventas):
    por_vendedor = {}
    for venta in ventas:
        vendedor = venta["vendedor"]
        # Error 3: hay que acumular, no sustituir
        por_vendedor[vendedor] = por_vendedor.get(vendedor, 0) + importe(venta)
    nombre = max(por_vendedor, key=por_vendedor.get)
    return nombre, por_vendedor[nombre]


def main():
    ventas = leer_ventas(RUTA)
    print(f"Ventas leídas: {len(ventas)}")
    print(f"Importe total: {total(ventas):.2f}")
    nombre, vendido = mejor_vendedor(ventas)
    print(f"Mejor vendedor: {nombre} ({vendido:.2f})")


if __name__ == "__main__":
    main()
