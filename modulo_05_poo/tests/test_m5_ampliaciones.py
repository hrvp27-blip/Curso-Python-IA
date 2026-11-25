"""Tests de las ampliaciones del módulo 5: ejercicios y práctica."""

import dataclasses
import inspect
from datetime import date

import pytest

import m5_ej1_clases as ej1
import m5_ej2_metodos as ej2
import m5_ej4_polimorfismo as ej4
import m5_ej5_encapsulacion as ej5
import m5_practica_biblioteca as bib

HOY = date(2026, 11, 2)


# --------------------------------------------------------------- Ejercicios
def test_dinero_hash_como_clave():
    precios = {ej2.Dinero(5): "cinco", ej2.Dinero(5, "USD"): "five"}
    assert precios[ej2.Dinero(5)] == "cinco"
    assert precios[ej2.Dinero(5, "USD")] == "five"
    assert len({ej2.Dinero(1), ej2.Dinero(1), ej2.Dinero(2)}) == 2


def test_dinero_hash_coherente_con_eq():
    assert hash(ej2.Dinero(0.1) + ej2.Dinero(0.2)) == hash(ej2.Dinero(0.3))


def test_protocolo_exportador():
    from typing import Protocol

    assert Protocol in ej4.Exportador.__mro__
    assert "exportar" in vars(ej4.Exportador)
    assert inspect.signature(ej4.exportar_con).parameters["exportador"].annotation is ej4.Exportador
    assert inspect.signature(ej4.nombre_de_fichero).parameters["exportador"].annotation is ej4.Exportador
    # Los exportadores siguen sin heredar de nada
    assert ej4.ExportadorCsv.__bases__ == (object,)


def test_rectangulo_es_dataclass():
    assert dataclasses.is_dataclass(ej1.Rectangulo)
    assert [campo.name for campo in dataclasses.fields(ej1.Rectangulo)] == ["base", "altura"]
    assert "def __init__" not in inspect.getsource(ej1.Rectangulo), "El __init__ lo genera @dataclass"
    assert repr(ej1.Rectangulo(3, 4)) == "Rectangulo(base=3, altura=4)"
    assert ej1.Rectangulo(3, 4) == ej1.Rectangulo(3, 4)
    assert ej1.Rectangulo(3, 4).escalar(2) == ej1.Rectangulo(6, 8)


def test_cuenta_desde_movimientos():
    cuenta = ej5.CuentaBancaria.desde_movimientos("Ada", [100, -30, 50])
    assert cuenta.titular == "Ada"
    assert cuenta.saldo == 120
    assert cuenta.movimientos == (100, -30, 50)
    assert ej5.CuentaBancaria.desde_movimientos("Linus", []).saldo == 0
    assert isinstance(inspect.getattr_static(ej5.CuentaBancaria, "desde_movimientos"), classmethod)


def test_cuenta_desde_movimientos_valida():
    with pytest.raises(ValueError):
        ej5.CuentaBancaria.desde_movimientos("Ada", [50, -80])


# ------------------------------------------------------------------ Práctica
@pytest.fixture
def biblioteca():
    central = bib.Biblioteca("Central")
    central.anadir_material(bib.Libro("L001", "Clean Code", 2008, "Robert C. Martin"))
    central.anadir_material(bib.Dvd("D001", "Matrix", 1999, 136))
    central.anadir_material(bib.Audiolibro("A001", "Dune", 2021, "Scott Brick"))
    for nombre in ("Ada", "Linus", "Grace"):
        central.registrar_socio(nombre)
    return central


def test_audiolibro():
    dune = bib.Audiolibro("A001", "Dune", 2021, "Scott Brick")
    assert isinstance(dune, bib.Material)
    assert dune.dias_prestamo == 14
    assert dune.narrador == "Scott Brick"
    assert str(dune) == "[A001] Dune (2021), narrado por Scott Brick"
    assert repr(dune) == "Audiolibro('A001', 'Dune')"
    assert "super().__init__" in inspect.getsource(bib.Audiolibro.__init__)


def test_audiolibro_en_la_biblioteca(biblioteca):
    prestamo = biblioteca.prestar("A001", 1, HOY)
    assert prestamo.fecha_devolucion == date(2026, 11, 16)


@pytest.mark.parametrize(
    "hoy, multa",
    [(date(2026, 11, 23), 0), (date(2026, 11, 24), 0.2), (date(2026, 11, 30), 1.4)],
)
def test_multa(biblioteca, hoy, multa):
    biblioteca.prestar("L001", 1, HOY)
    assert biblioteca.multa("L001", hoy) == multa


def test_multa_sin_prestamo(biblioteca):
    with pytest.raises(ValueError) as error:
        biblioteca.multa("L001", HOY)
    assert str(error.value) == "No hay ningún préstamo de L001"


def test_reservar_y_cola(biblioteca):
    biblioteca.prestar("L001", 1, HOY)
    assert biblioteca.reservar("L001", 2) == 1
    assert biblioteca.reservar("L001", 3) == 2
    assert [s.nombre for s in biblioteca.reservas("L001")] == ["Linus", "Grace"]
    assert biblioteca.reservas("D001") == ()


@pytest.mark.parametrize(
    "codigo, socio, mensaje",
    [
        ("X999", 2, "No existe el material X999"),
        ("L001", 99, "No existe el socio 99"),
        ("D001", 2, "D001 está disponible: no hace falta reservarlo"),
        ("L001", 1, "Ada ya tiene L001"),
    ],
)
def test_reservar_errores(biblioteca, codigo, socio, mensaje):
    biblioteca.prestar("L001", 1, HOY)
    with pytest.raises(ValueError) as error:
        biblioteca.reservar(codigo, socio)
    assert str(error.value) == mensaje


def test_reservar_dos_veces(biblioteca):
    biblioteca.prestar("L001", 1, HOY)
    biblioteca.reservar("L001", 2)
    with pytest.raises(ValueError) as error:
        biblioteca.reservar("L001", 2)
    assert str(error.value) == "Linus ya ha reservado L001"
    assert len(biblioteca.reservas("L001")) == 1


def test_material_devuelto_queda_para_el_primero_de_la_cola(biblioteca):
    biblioteca.prestar("L001", 1, HOY)
    biblioteca.reservar("L001", 2)
    biblioteca.reservar("L001", 3)
    biblioteca.devolver("L001")
    with pytest.raises(ValueError) as error:
        biblioteca.prestar("L001", 3, HOY)
    assert str(error.value) == "L001 está reservado para Linus"
    assert biblioteca.buscar("L001").disponible is True
    with pytest.raises(ValueError):
        biblioteca.prestar("L001", 1, HOY)  # quien lo devolvió tampoco puede
    prestamo = biblioteca.prestar("L001", 2, HOY)
    assert prestamo.socio.nombre == "Linus"
    assert [s.nombre for s in biblioteca.reservas("L001")] == ["Grace"]


def test_se_puede_reservar_un_material_devuelto_con_cola(biblioteca):
    biblioteca.prestar("L001", 1, HOY)
    biblioteca.reservar("L001", 2)
    biblioteca.devolver("L001")
    assert biblioteca.reservar("L001", 3) == 2


def test_reserva_no_se_pierde_si_el_prestamo_falla(biblioteca):
    biblioteca.prestar("L001", 1, HOY)
    biblioteca.reservar("L001", 2)
    with pytest.raises(ValueError):
        biblioteca.prestar("L001", 2, HOY)  # aún no se ha devuelto
    assert [s.nombre for s in biblioteca.reservas("L001")] == ["Linus"]


def test_cancelar_reserva(biblioteca):
    biblioteca.prestar("L001", 1, HOY)
    biblioteca.reservar("L001", 2)
    biblioteca.cancelar_reserva("L001", 2)
    assert biblioteca.reservas("L001") == ()
    with pytest.raises(ValueError):
        biblioteca.cancelar_reserva("L001", 2)
    biblioteca.devolver("L001")
    biblioteca.prestar("L001", 3, HOY)  # sin cola, cualquiera puede


def test_paquete_biblioteca():
    from biblioteca import Biblioteca, Libro, modelos, servicios

    assert Libro is modelos.Libro is bib.Libro
    assert Biblioteca is servicios.Biblioteca is bib.Biblioteca
    assert bib.Material.__module__ == "biblioteca.modelos"
    assert bib.Biblioteca.__module__ == "biblioteca.servicios"
