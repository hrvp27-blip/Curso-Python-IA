"""Validación y normalización de textos."""

LETRAS_DNI = "TRWAGMYFPDXBNJZSQVHLCKE"
INICIOS_TELEFONO = "6789"
LONGITUD_IBAN_ES = 24


def esta_vacio(texto: str | None) -> bool:
    """Indica si el texto es ``None``, está vacío o solo contiene espacios.

    >>> esta_vacio("   ")
    True
    >>> esta_vacio(" a ")
    False
    """
    return texto is None or texto.strip() == ""


def normalizar_nombre(nombre: str) -> str:
    """Quita los espacios sobrantes y pone en mayúscula la inicial de cada palabra.

    >>> normalizar_nombre("  ada   LOVELACE ")
    'Ada Lovelace'
    """
    # split() sin argumentos separa por cualquier cantidad de espacios.
    return " ".join(nombre.split()).title()


def es_email(texto: str) -> bool:
    """Comprueba de forma sencilla que el texto tiene forma de correo.

    Reglas: no contiene espacios, tiene exactamente una arroba, hay texto
    antes de la arroba, y el dominio contiene al menos un punto que no está
    ni al principio ni al final.

    >>> es_email("ada@ejemplo.com")
    True
    >>> es_email("ada@ejemplo")
    False
    """
    if esta_vacio(texto):
        return False
    if " " in texto:
        return False
    if texto.count("@") != 1:
        return False
    local, domain = texto.split("@")
    if not local:
        return False
    if not domain or domain[0] == "." or domain[-1] == ".":
        return False
    if domain.count(".") < 1:
        return False
    return True


def es_dni(texto: str) -> bool:
    """Comprueba que el texto es un DNI válido: ocho dígitos y la letra correcta.

    La letra se obtiene tomando el resto de dividir el número entre 23 y
    usándolo como posición en ``LETRAS_DNI``. Admite la letra en minúscula y
    espacios alrededor.

    >>> es_dni("12345678Z")
    True
    >>> es_dni("12345678A")
    False
    """
    if esta_vacio(texto):
        return False
    texto = texto.strip()
    if len(texto) != 9:
        return False
    if not texto[:8].isdigit():
        return False
    if texto[8].upper() != LETRAS_DNI[int(texto[:8]) % 23]:
        return False
    return True


def es_telefono(texto: str) -> bool:
    """Comprueba que el texto es un teléfono español.

    Nueve dígitos que empiezan por 6, 7, 8 o 9. Admite espacios entre grupos
    y alrededor.

    >>> es_telefono("612 345 678"), es_telefono("512345678"), es_telefono("61234567")
    (True, False, False)
    """
    cifras = texto.replace(" ", "")
    return (
        len(cifras) == 9
        and cifras.isdigit()
        and cifras.isascii()
        and cifras[0] in INICIOS_TELEFONO
    )


def es_iban(texto: str) -> bool:
    """Comprueba que el texto es un IBAN español con los dígitos de control correctos.

    Formato: "ES" y 22 dígitos. Admite espacios entre grupos y minúsculas.
    Se pasan los 4 primeros caracteres al final, cada letra se sustituye por
    su número (A = 10, B = 11... Z = 35) y el resultado módulo 97 debe ser 1.

    >>> es_iban("ES91 2100 0418 4502 0005 1332"), es_iban("ES92 2100 0418 4502 0005 1332")
    (True, False)
    """
    iban = texto.replace(" ", "").upper()
    cifras = iban[2:]
    if len(iban) != LONGITUD_IBAN_ES or not iban.startswith("ES"):
        return False
    if not (cifras.isdigit() and cifras.isascii()):
        return False
    reordenado = iban[4:] + iban[:4]
    # int(caracter, 36) convierte "0"-"9" en 0-9 y las letras en 10-35.
    numero = "".join(str(int(caracter, 36)) for caracter in reordenado)
    return int(numero) % 97 == 1
