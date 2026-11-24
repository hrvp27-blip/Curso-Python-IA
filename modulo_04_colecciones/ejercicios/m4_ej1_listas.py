"""Módulo 4 - Ejercicio 1: listas."""


def extremos(lista: list) -> tuple:
    """Devuelve una tupla con el primer y el último elemento de la lista.

    Con la lista vacía devuelve ``(None, None)``.

    >>> extremos([4, 8, 15])
    (4, 15)
    >>> extremos([7])
    (7, 7)
    """
    return (lista[0], lista[-1]) if lista else (None, None)


def rotar(lista: list, posiciones: int = 1) -> list:
    """Devuelve una lista nueva con los elementos desplazados a la izquierda.

    Los que salen por el principio entran por el final. ``posiciones`` puede
    ser mayor que la longitud de la lista. No modifica la lista original.

    >>> rotar([1, 2, 3, 4, 5], 2)
    [3, 4, 5, 1, 2]
    >>> rotar([1, 2, 3], 4)
    [2, 3, 1]
    """
    return lista[posiciones % len(lista):] + lista[:posiciones % len(lista)] if lista else []


def segundo_mayor(numeros: list[float]) -> float | None:
    """Devuelve el segundo valor más alto, sin contar repetidos.

    Si no hay al menos dos valores distintos devuelve ``None``.

    >>> segundo_mayor([4, 42, 15, 42])
    15
    >>> segundo_mayor([5, 5]) is None
    True
    """
    return sorted(set(numeros))[-2] if len(set(numeros)) > 1 else None


def trocear(lista: list, tamano: int) -> list[list]:
    """Divide la lista en trozos de ``tamano`` elementos.

    El último trozo puede ser más corto.

    >>> trocear([1, 2, 3, 4, 5], 2)
    [[1, 2], [3, 4], [5]]
    """
    return [lista[i:i + tamano] for i in range(0, len(lista), tamano)]
    # Con comprensión: [lista[i:i + tamano] for i in range(0, len(lista), tamano)]


def sin_duplicados(lista: list) -> list:
    """Devuelve una lista nueva sin repetidos, conservando el orden de aparición.

    >>> sin_duplicados([3, 1, 3, 2, 1])
    [3, 1, 2]
    """
    return list(dict.fromkeys(lista))


def insertar_ordenado(ordenada: list[float], valor: float) -> list[float]:
    """Devuelve una lista nueva con ``valor`` insertado en su sitio.

    ``ordenada`` está en orden ascendente y no se modifica.

    >>> insertar_ordenado([1, 3, 5], 4)
    [1, 3, 4, 5]
    """
    return sorted(ordenada + [valor])
    # También vale sorted(ordenada + [valor]); la librería estándar tiene bisect.insort


def crear_tablero(filas: int, columnas: int, valor=0) -> list[list]:
    """Devuelve una matriz de ``filas`` x ``columnas`` rellena con ``valor``.

    Cada fila tiene que ser una lista independiente de las demás.

    >>> crear_tablero(2, 3)
    [[0, 0, 0], [0, 0, 0]]
    """
    return [[valor] * columnas for _ in range(filas)]
