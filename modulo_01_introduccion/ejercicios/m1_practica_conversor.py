"""Módulo 1 - Práctica 1: conversor de unidades.

Lee el enunciado en PRACTICA_1.md.
"""

KM_POR_MILLA = 1.609344
KG_POR_LIBRA = 0.45359237
M_POR_PIE = 0.3048

MENU = """Conversor de unidades
1. Celsius a Fahrenheit
2. Fahrenheit a Celsius
3. Kilómetros a millas
4. Millas a kilómetros
5. Kilogramos a libras
6. Libras a kilogramos
7. Metros a pies
0. Salir"""


def celsius_a_fahrenheit(grados):
    """Convierte grados Celsius a Fahrenheit."""
    return grados * 9 / 5 + 32


def fahrenheit_a_celsius(grados):
    """Convierte grados Fahrenheit a Celsius."""
    return (grados - 32) * 5 / 9


def km_a_millas(km):
    """Convierte kilómetros a millas."""
    return km / KM_POR_MILLA


def millas_a_km(millas):
    """Convierte millas a kilómetros."""
    return millas * KM_POR_MILLA


def kg_a_libras(kg):
    """Convierte kilogramos a libras."""
    return kg / KG_POR_LIBRA


def libras_a_kg(libras):
    """Convierte libras a kilogramos."""
    return libras * KG_POR_LIBRA


def metros_a_pies(metros):
    """Convierte metros a pies."""
    return metros / M_POR_PIE


# Cada opción del menú: (función de conversión, unidad de origen, unidad de destino)
CONVERSIONES = {
    "1": (celsius_a_fahrenheit, "°C", "°F"),
    "2": (fahrenheit_a_celsius, "°F", "°C"),
    "3": (km_a_millas, "km", "mi"),
    "4": (millas_a_km, "mi", "km"),
    "5": (kg_a_libras, "kg", "lb"),
    "6": (libras_a_kg, "lb", "kg"),
    "7": (metros_a_pies, "m", "ft"),
}


def formatear(valor, unidad_origen, resultado, unidad_destino):
    """Devuelve el texto de la conversión con dos decimales.

    >>> formatear(100, "°C", 212.0, "°F")
    '100.00 °C = 212.00 °F'
    """
    return f"{valor:.2f} {unidad_origen} = {resultado:.2f} {unidad_destino}"


def convertir_opcion(opcion):
    """Pide el valor e imprime la conversión correspondiente a ``opcion``."""
    convertir, unidad_origen, unidad_destino = CONVERSIONES[opcion]
    valor = float(input("Valor a convertir: "))
    resultado = convertir(valor)
    print(formatear(valor, unidad_origen, resultado, unidad_destino))


def main():
    """Muestra el menú, atiende una opción y dice si hay que seguir.

    Devuelve False si el usuario elige 0 para salir y True en otro caso.
    """
    print(MENU)
    opcion = input(f"Elige una opción (0-{len(CONVERSIONES)}): ").strip()
    if opcion == "0":
        print("Hasta luego.")
        return False
    if opcion in CONVERSIONES:
        convertir_opcion(opcion)
    else:
        print("Opción no válida")
    return True


if __name__ == "__main__":
    while main():
        print()
