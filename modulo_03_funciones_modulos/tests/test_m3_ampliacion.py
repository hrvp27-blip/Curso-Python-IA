"""Tests de las ampliaciones de la práctica 3: teléfono, IBAN y reintento en main()."""

import pytest

import m3_practica_registro as registro
import m3_validacion
from m3_validacion import texto


# --------------------------------------------------------------- es_telefono
@pytest.mark.parametrize(
    "telefono",
    [
        "612345678",
        "712345678",
        "812345678",
        "912345678",
        "612 345 678",
        "612 34 56 78",
        " 612345678 ",
    ],
)
def test_es_telefono_valido(telefono):
    assert texto.es_telefono(telefono) is True


@pytest.mark.parametrize(
    "telefono",
    [
        "",
        "   ",
        "512345678",        # empieza por 5
        "012345678",        # empieza por 0
        "61234567",         # le falta un dígito
        "6123456789",       # le sobra un dígito
        "61234567a",        # una letra
        "+34612345678",     # con prefijo internacional
        "612-345-678",      # guiones en lugar de espacios
    ],
)
def test_es_telefono_no_valido(telefono):
    assert texto.es_telefono(telefono) is False


# ------------------------------------------------------------------- es_iban
@pytest.mark.parametrize(
    "iban",
    ["ES9121000418450200051332", "ES91 2100 0418 4502 0005 1332", "es9121000418450200051332"],
)
def test_es_iban_valido(iban):
    assert texto.es_iban(iban) is True


@pytest.mark.parametrize(
    "iban",
    [
        "",
        "ES9221000418450200051332",      # dígitos de control incorrectos
        "ES9121000418450200051333",      # un dígito de la cuenta cambiado
        "FR9121000418450200051332",      # otro país
        "ES912100041845020005133",       # le falta un dígito
        "ES91210004184502000513322",     # le sobra un dígito
        "ES91210004184502000513A2",      # una letra entre los dígitos
    ],
)
def test_es_iban_no_valido(iban):
    assert texto.es_iban(iban) is False


def test_ampliaciones_exportadas_en_el_paquete():
    assert m3_validacion.es_telefono is texto.es_telefono
    assert m3_validacion.es_iban is texto.es_iban


# ------------------------------------------------------- main(reintentar=True)
def _ejecutar_main(monkeypatch, capsys, respuestas, **opciones):
    entradas = iter(respuestas)
    preguntas = []

    def responder(pregunta=""):
        preguntas.append(pregunta)
        return next(entradas)

    monkeypatch.setattr("builtins.input", responder)
    registro.main(**opciones)
    return preguntas, capsys.readouterr().out


def test_main_reintenta_solo_los_datos_erroneos(monkeypatch, capsys):
    respuestas = [
        "", "ada@ejemplo", "12345678Z", "1990-01-01",    # nombre y correo erróneos
        "Ada", "ada@ejemplo.com",                        # solo se vuelven a pedir esos dos
    ]
    preguntas, salida = _ejecutar_main(monkeypatch, capsys, respuestas, reintentar=True)
    assert preguntas[4:] == ["Nombre: ", "Correo: "]
    assert "No se puede completar el alta:" in salida
    assert "Alta correcta:" in salida
    assert "nombre: Ada" in salida


def test_main_reintenta_la_fecha_si_es_menor_de_edad(monkeypatch, capsys):
    respuestas = ["Ada", "ada@ejemplo.com", "12345678Z", "2020-01-01", "1990-01-01"]
    preguntas, salida = _ejecutar_main(monkeypatch, capsys, respuestas, reintentar=True)
    assert preguntas[4:] == ["Fecha de nacimiento (AAAA-MM-DD): "]
    assert " - Hay que ser mayor de edad." in salida
    assert "nacimiento: 1990-01-01" in salida


def test_main_sin_reintentar_termina_al_primer_error(monkeypatch, capsys):
    preguntas, salida = _ejecutar_main(
        monkeypatch, capsys, ["", "ada@ejemplo.com", "12345678Z", "1990-01-01"]
    )
    assert len(preguntas) == 4
    assert "Alta correcta" not in salida
