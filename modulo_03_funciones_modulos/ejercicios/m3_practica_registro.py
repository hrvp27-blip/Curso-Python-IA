"""Módulo 3 - Práctica 3: alta de usuarios con el paquete m3_validacion.

Este programa es el cliente de la librería: no valida nada por sí mismo,
solo combina las funciones del paquete.
"""

from datetime import date

from m3_validacion import (
    es_dni,
    es_email,
    es_fecha,
    es_mayor_de_edad,
    esta_vacio,
    normalizar_nombre,
)

ERROR_NOMBRE = "El nombre es obligatorio."
ERROR_EMAIL = "El correo no es válido."
ERROR_DNI = "El DNI no es válido."
ERROR_FECHA = "La fecha de nacimiento no es válida."
ERROR_EDAD = "Hay que ser mayor de edad."

# Cada dato del alta, en el orden en que se pide, con su pregunta.
PREGUNTAS = {
    "nombre": "Nombre: ",
    "email": "Correo: ",
    "dni": "DNI: ",
    "fecha_nacimiento": "Fecha de nacimiento (AAAA-MM-DD): ",
}

# Qué dato hay que volver a pedir para cada error.
DATO_DEL_ERROR = {
    ERROR_NOMBRE: "nombre",
    ERROR_EMAIL: "email",
    ERROR_DNI: "dni",
    ERROR_FECHA: "fecha_nacimiento",
    ERROR_EDAD: "fecha_nacimiento",
}


def validar_registro(nombre: str, email: str, dni: str, fecha_nacimiento: str,
                     hoy: date | None = None) -> list[str]:
    """Valida los datos de un alta y devuelve la lista de errores encontrados.

    Los mensajes, en este orden, son:

    - "El nombre es obligatorio."
    - "El correo no es válido."
    - "El DNI no es válido."
    - "La fecha de nacimiento no es válida."
    - "Hay que ser mayor de edad."  (solo si la fecha es válida)

    Si todo es correcto devuelve una lista vacía.

    >>> validar_registro("Ada", "ada@ejemplo.com", "12345678Z", "1990-01-01")
    []
    """
    errores = []
    if esta_vacio(nombre):
        errores.append(ERROR_NOMBRE)
    if not es_email(email.strip()):
        errores.append(ERROR_EMAIL)
    if not es_dni(dni):
        errores.append(ERROR_DNI)
    if not es_fecha(fecha_nacimiento):
        errores.append(ERROR_FECHA)
    elif not es_mayor_de_edad(fecha_nacimiento, hoy):
        errores.append(ERROR_EDAD)
    return errores


def crear_ficha(nombre: str, email: str, dni: str, fecha_nacimiento: str) -> dict:
    """Devuelve un diccionario con los datos ya normalizados.

    El nombre se normaliza con ``normalizar_nombre``, el correo se pasa a
    minúsculas y el DNI a mayúsculas, todos sin espacios alrededor.

    >>> crear_ficha(" ada LOVELACE", "Ada@Ejemplo.com ", "12345678z", "1990-01-01")
    {'nombre': 'Ada Lovelace', 'email': 'ada@ejemplo.com', 'dni': '12345678Z', 'nacimiento': '1990-01-01'}
    """
    return {
        "nombre": normalizar_nombre(nombre),
        "email": email.lower().strip(),
        "dni": dni.upper().strip(),
        "nacimiento": fecha_nacimiento.strip(),
    }


def main(reintentar: bool = False):
    """Pide los datos por teclado y muestra la ficha o los errores.

    Pide, en este orden: nombre, correo, DNI y fecha de nacimiento. Si hay
    errores imprime "No se puede completar el alta:" y después cada error en
    una línea que empieza por " - ". Si no los hay imprime "Alta correcta:" y
    después cada dato de la ficha con el formato "clave: valor".

    Con ``reintentar=True``, en lugar de terminar vuelve a pedir solo los
    datos erróneos hasta que el alta es correcta.
    """
    datos = {}
    pendientes = list(PREGUNTAS)
    while True:
        for dato in pendientes:
            datos[dato] = input(PREGUNTAS[dato])

        errores = validar_registro(**datos)
        if not errores:
            break

        print("No se puede completar el alta:")
        for error in errores:
            print(f" - {error}")
        if not reintentar:
            return

        # Se vuelven a pedir, en el orden habitual, solo los datos con error.
        datos_erroneos = {DATO_DEL_ERROR[error] for error in errores}
        pendientes = [dato for dato in PREGUNTAS if dato in datos_erroneos]
        print("Corrige los datos erróneos:")

    print("Alta correcta:")
    ficha = crear_ficha(**datos)
    for clave, valor in ficha.items():
        print(f"{clave}: {valor}")


if __name__ == "__main__":
    main(reintentar=True)
