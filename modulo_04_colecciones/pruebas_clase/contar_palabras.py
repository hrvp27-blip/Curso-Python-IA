"""Demo 5: contar cuántas veces aparece cada palabra, de tres formas."""

from collections import Counter

TEXTO = "el gato y el perro y el raton"


def contar_con_if(palabras):
    """Cuenta comprobando si la clave ya está en el diccionario."""
    cuenta = {}
    for palabra in palabras:
        if palabra in cuenta:
            cuenta[palabra] += 1
        else:
            cuenta[palabra] = 1
    return cuenta


def contar_con_get(palabras):
    """Cuenta con get(clave, 0) + 1: si no existe, empieza en 0."""
    cuenta = {}
    for palabra in palabras:
        cuenta[palabra] = cuenta.get(palabra, 0) + 1
    return cuenta


def contar_con_counter(palabras):
    """Cuenta con Counter, que hace todo el trabajo en una línea."""
    return Counter(palabras)


if __name__ == "__main__":
    palabras = TEXTO.split()
    print("Con if clave in d:", contar_con_if(palabras))
    print("Con get(clave, 0) + 1:", contar_con_get(palabras))
    print("Con Counter:", contar_con_counter(palabras))
    print("Las 2 más repetidas:", contar_con_counter(palabras).most_common(2))
