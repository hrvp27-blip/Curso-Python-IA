"""Módulo 2 - Práctica 2, parte A: adivina el número."""

import random

MINIMO = 1
MAXIMO = 100
MAX_INTENTOS = 7

# Respuestas del usuario cuando adivina el ordenador, traducidas a las pistas
# que usa evaluar_intento.
RESPUESTAS_USUARIO = {"+": "mayor", "-": "menor", "=": "acierto"}


def evaluar_intento(secreto: int, intento: int) -> str:
    """Compara el intento con el número secreto.

    Devuelve "acierto", "mayor" si el secreto es mayor que el intento o
    "menor" si el secreto es menor.

    >>> evaluar_intento(50, 30)
    'mayor'
    """
    if intento == secreto:
        return "acierto"
    return "mayor" if secreto > intento else "menor"


def es_intento_valido(texto: str) -> bool:
    """Indica si ``texto`` es un entero entre MINIMO y MAXIMO.

    >>> es_intento_valido("50"), es_intento_valido("abc"), es_intento_valido("101")
    (True, False, False)
    """
    limpio = texto.strip()
    # isdigit() descarta vacíos, signos y decimales; isascii() descarta "²".
    return limpio.isdigit() and limpio.isascii() and MINIMO <= int(limpio) <= MAXIMO


def jugar(secreto: int, max_intentos: int = MAX_INTENTOS) -> bool:
    """Juega una partida y devuelve True si el jugador acierta.

    En cada turno pide un número con input(). Una entrada no válida no
    consume intento. Tras cada intento fallido imprime una pista.
    """
    intento_actual = 1
    while intento_actual <= max_intentos:
        texto = input(f"Intento {intento_actual} de {max_intentos}: ")
        if not es_intento_valido(texto):
            print(f"Escribe un número entre {MINIMO} y {MAXIMO}.")
            continue

        resultado = evaluar_intento(secreto, int(texto))
        if resultado == "acierto":
            print(f"¡Correcto! Lo has adivinado en {intento_actual} intentos.")
            return True
        print(f"El número secreto es {resultado}.")
        intento_actual += 1

    print(f"Has agotado los intentos. El número era {secreto}.")
    return False


def main() -> None:
    """Genera un número secreto al azar y lanza una partida."""
    jugar(random.randint(MINIMO, MAXIMO))


def proponer(minimo: int, maximo: int) -> int:
    """Devuelve el punto medio del intervalo: la propuesta de la búsqueda binaria.

    >>> proponer(1, 100), proponer(51, 100)
    (50, 75)
    """
    return (minimo + maximo) // 2


def acotar(minimo: int, maximo: int, propuesta: int, pista: str) -> tuple[int, int]:
    """Reduce el intervalo de búsqueda a la mitad según la pista.

    "mayor" significa que el número buscado es mayor que la propuesta.

    >>> acotar(1, 100, 50, "mayor"), acotar(1, 100, 50, "menor")
    ((51, 100), (1, 49))
    """
    if pista == "mayor":
        return propuesta + 1, maximo
    return minimo, propuesta - 1


def adivina_el_ordenador(max_intentos: int = MAX_INTENTOS) -> bool:
    """El ordenador adivina un número que piensa el usuario con búsqueda binaria.

    Devuelve True si lo adivina. Una respuesta no válida no consume intento.
    """
    print(f"Piensa un número entre {MINIMO} y {MAXIMO} y yo intentaré adivinarlo.")
    print("Responde + si tu número es mayor, - si es menor o = si he acertado.")
    minimo, maximo = MINIMO, MAXIMO
    intento_actual = 1
    while intento_actual <= max_intentos:
        if minimo > maximo:
            print("Tus respuestas se contradicen: ningún número las cumple.")
            return False

        propuesta = proponer(minimo, maximo)
        respuesta = input(f"Intento {intento_actual} de {max_intentos}. ¿Es {propuesta}? ")
        pista = RESPUESTAS_USUARIO.get(respuesta.strip())
        if pista is None:
            print("Responde +, - o =.")
            continue

        if pista == "acierto":
            print(f"¡Lo he adivinado en {intento_actual} intentos!")
            return True
        minimo, maximo = acotar(minimo, maximo, propuesta, pista)
        intento_actual += 1

    print("No lo he adivinado. ¿Seguro que tus respuestas eran correctas?")
    return False


def quiere_jugar_otra_vez() -> bool:
    """Pregunta si se quiere jugar otra partida."""
    respuesta = input("¿Quieres jugar otra vez? (s/n): ")
    return respuesta.strip().lower() in ("s", "si", "sí")


def programa() -> None:
    """Elige quién adivina y permite jugar varias partidas seguidas."""
    while True:
        print("¿Quién adivina?")
        print("1. Tú adivinas el número del ordenador")
        print("2. El ordenador adivina tu número")
        modo = input("Elige 1 o 2: ").strip()
        if modo == "1":
            main()
        elif modo == "2":
            adivina_el_ordenador()
        else:
            print("Opción no válida.")
            continue

        if not quiere_jugar_otra_vez():
            print("¡Hasta la próxima!")
            return
        print()


if __name__ == "__main__":
    programa()
