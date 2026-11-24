"""Tests de las ampliaciones del módulo 4: ejercicios y práctica."""

import copy

import pytest

import m4_ej2_diccionarios as ej2
import m4_ej6_datos as ej6
import m4_practica_ventas as practica
from m4_datos_ventas import VENTAS

EMPLEADOS = [
    {"id": 1, "nombre": "Ada", "departamento": "IT", "salario": 52000},
    {"id": 2, "nombre": "Linus", "departamento": "IT", "salario": 48000},
    {"id": 3, "nombre": "Grace", "departamento": "Ventas", "salario": 45000},
    {"id": 4, "nombre": "Alan", "departamento": "Ventas", "salario": 39000},
    {"id": 5, "nombre": "Guido", "departamento": "IT", "salario": 48000},
    {"id": 6, "nombre": "Barbara", "departamento": "Legal", "salario": 61000},
]


@pytest.fixture
def ventas():
    return copy.deepcopy(VENTAS)


@pytest.fixture
def empleados():
    return copy.deepcopy(EMPLEADOS)


@pytest.fixture(autouse=True)
def _los_datos_no_cambian(ventas, empleados):
    yield
    assert ventas == VENTAS, "La función ha modificado la lista de ventas"
    assert empleados == EMPLEADOS, "La función ha modificado los empleados"


# --------------------------------------------------------------- Ejercicios
def test_contar_palabras_con_counter_devuelve_dict_en_orden():
    resultado = ej2.contar_palabras("uno dos uno tres dos uno")
    assert type(resultado) is dict
    assert list(resultado.items()) == [("uno", 3), ("dos", 2), ("tres", 1)]


def test_agrupar_por_con_defaultdict_devuelve_dict(empleados):
    grupos = ej6.agrupar_por(empleados, "departamento")
    assert type(grupos) is dict
    assert grupos.get("Marketing") is None


def test_ordenar_por_varios(empleados):
    resultado = ej6.ordenar_por_varios(empleados, ["departamento", "salario", "nombre"])
    assert ej6.nombres(resultado) == ["Guido", "Linus", "Ada", "Barbara", "Alan", "Grace"]
    assert resultado is not empleados


def test_ordenar_por_varios_descendente_y_un_campo(empleados):
    resultado = ej6.ordenar_por_varios(empleados, ["salario", "nombre"], descendente=True)
    assert ej6.nombres(resultado)[:4] == ["Barbara", "Ada", "Linus", "Guido"]
    assert ej6.ordenar_por_varios(empleados, ["nombre"]) == ej6.ordenar_por(empleados, "nombre")
    assert ej6.ordenar_por_varios([], ["nombre"]) == []


# ----------------------------------------------------------------- Práctica
def test_semana():
    assert practica.semana({"fecha": "2026-10-01"}) == "2026-S40"
    assert practica.semana({"fecha": "2026-10-05"}) == "2026-S41"
    assert practica.semana({"fecha": "2026-01-01"}) == "2026-S01"


def test_importe_por_semana(ventas):
    semanas = practica.importe_por_semana(ventas)
    assert semanas == {
        "2026-S40": 2891.0,
        "2026-S41": 5908.0,
        "2026-S42": 3891.3,
        "2026-S43": 2889.0,
        "2026-S44": 6107.5,
    }
    assert list(semanas) == sorted(semanas)
    assert round(sum(semanas.values()), 2) == practica.total_ventas(ventas)
    assert practica.importe_por_semana([]) == {}
    assert "semana" not in ventas[0]


def test_informe_por_semana(ventas):
    lineas = [linea.rstrip() for linea in practica.generar_informe(ventas, por_semana=True).split("\n")]
    assert lineas[-8:] == [
        "-" * 44,
        "Por semana",
        "  2026-S40                          2,891.00",
        "  2026-S41                          5,908.00",
        "  2026-S42                          3,891.30",
        "  2026-S43                          2,889.00",
        "  2026-S44                          6,107.50",
        "=" * 44,
    ]
    assert "Por semana" not in practica.generar_informe(ventas)


def test_comparar_periodos(ventas):
    assert practica.comparar_periodos(ventas, "2026-10-16") == -25.83
    assert practica.comparar_periodos(ventas, "2026-11-01") == -100.0
    assert practica.comparar_periodos(ventas, "2026-10-01") is None
    assert practica.comparar_periodos([], "2026-10-16") is None


def test_ranking_por_unidades(ventas):
    assert practica.ranking(ventas, "producto", medida="unidades") == [
        ("Antivirus", 70),
        ("Licencia ofimática", 30),
        ("Teclado", 23),
    ]
    assert practica.ranking(ventas, "vendedor", medida="importe") == practica.ranking(ventas, "vendedor")


def test_ranking_medida_no_valida(ventas):
    with pytest.raises(ValueError):
        practica.ranking(ventas, "producto", medida="beneficio")


def test_mejor_vendedor_por_region(ventas):
    assert practica.mejor_vendedor_por_region(ventas) == {
        "Norte": "Ada",
        "Sur": "Alan",
        "Centro": "Grace",
    }
    assert practica.mejor_vendedor_por_region([]) == {}
