"""Tests del hito 1: excepciones, cálculos geográficos y modelos."""

import csv
from datetime import datetime
from pathlib import Path

import pytest

from estaciones import geo
from estaciones.excepciones import (
    CoordenadaNoValida,
    DatosNoValidos,
    ErrorDeAlmacen,
    ErrorDeEstaciones,
    EstacionNoEncontrada,
)
from estaciones.modelos import CAMPOS_ESTACION, CAMPOS_MEDICION, Estacion, Medicion

DATOS = Path(__file__).parent.parent / "datos"
MADRID = (40.4168, -3.7038)
BARCELONA = (41.3874, 2.1686)


def estacion(**cambios):
    datos = {"codigo": "mad01", "nombre": " Madrid - Centro ", "provincia": "Madrid",
             "lat": 40.4215, "lon": -3.6823, "altitud": 672.0}
    return Estacion(**{**datos, **cambios})


def medicion(**cambios):
    datos = {"codigo": "MAD01", "fecha_hora": datetime(2026, 11, 1, 8),
             "temperatura": 9.5, "humedad": 70.0, "pm25": 12.0, "no2": 40.0}
    return Medicion(**{**datos, **cambios})


# --- excepciones -------------------------------------------------------------

@pytest.mark.parametrize("clase", [DatosNoValidos, EstacionNoEncontrada, ErrorDeAlmacen,
                                   CoordenadaNoValida])
def test_excepciones_heredan_de_la_base(clase):
    assert issubclass(clase, ErrorDeEstaciones)


def test_excepciones_coordenada_es_un_dato_no_valido():
    assert issubclass(CoordenadaNoValida, DatosNoValidos)


def test_excepciones_coordenada_guarda_lat_lon_y_mensaje():
    error = CoordenadaNoValida(95, 10)
    assert (error.lat, error.lon) == (95, 10)
    assert str(error) == "Coordenada fuera de rango: lat=95, lon=10"


def test_excepciones_estacion_no_encontrada():
    error = EstacionNoEncontrada("XXX01")
    assert error.codigo == "XXX01"
    assert str(error) == "No existe la estación XXX01"


# --- geo ---------------------------------------------------------------------

@pytest.mark.parametrize("lat, lon", [(0, 0), (90, 180), (-90, -180), (28.1, -15.4)])
def test_geo_coordenadas_validas(lat, lon):
    geo.validar_coordenada(lat, lon)


@pytest.mark.parametrize("lat, lon", [(90.1, 0), (-91, 0), (0, 180.5), (0, -181)])
def test_geo_coordenadas_no_validas(lat, lon):
    with pytest.raises(CoordenadaNoValida):
        geo.validar_coordenada(lat, lon)


def test_geo_haversine_un_grado_en_el_ecuador():
    assert geo.haversine(0, 0, 0, 1) == pytest.approx(111.19, abs=0.01)


def test_geo_haversine_madrid_barcelona():
    assert geo.haversine(*MADRID, *BARCELONA) == pytest.approx(505, abs=3)


def test_geo_haversine_mismo_punto_y_simetria():
    assert geo.haversine(*MADRID, *MADRID) == 0
    assert geo.haversine(*MADRID, *BARCELONA) == pytest.approx(geo.haversine(*BARCELONA, *MADRID))


@pytest.mark.parametrize("destino, esperado", [((1, 0), 0), ((0, 1), 90), ((-1, 0), 180),
                                               ((0, -1), 270)])
def test_geo_rumbo_puntos_cardinales(destino, esperado):
    assert geo.rumbo(0, 0, *destino) == pytest.approx(esperado)


def test_geo_rumbo_madrid_barcelona_es_casi_este():
    grados = geo.rumbo(*MADRID, *BARCELONA)
    assert 70 < grados < 80
    assert geo.punto_cardinal(grados) == "E"


@pytest.mark.parametrize("grados, esperado", [(0, "N"), (22.4, "N"), (22.5, "NE"), (135, "SE"),
                                              (225, "SO"), (300, "NO"), (359, "N")])
def test_geo_punto_cardinal(grados, esperado):
    assert geo.punto_cardinal(grados) == esperado


def test_geo_centroide():
    assert geo.centroide([(40, -4), (42, -2)]) == pytest.approx((41, -3))


def test_geo_centroide_vacio():
    with pytest.raises(DatosNoValidos):
        geo.centroide([])


@pytest.mark.parametrize("punto, dentro", [((40, -3), True), ((36, -3), True), ((44, -3), False),
                                           ((40, 4), False)])
def test_geo_en_caja(punto, dentro):
    peninsula = (36, -9.5, 43.8, 3.4)
    assert geo.en_caja(*punto, peninsula) is dentro


def test_geo_idw_punto_coincidente_devuelve_su_valor():
    assert geo.idw(40, -3, [(40, -3, 12.0), (41, -3, 20.0)]) == 12.0


def test_geo_idw_punto_medio_es_la_media():
    assert geo.idw(40, 0, [(39, 0, 10.0), (41, 0, 20.0)]) == pytest.approx(15.0, abs=0.01)


def test_geo_idw_pesa_mas_lo_cercano():
    valor = geo.idw(40.2, 0, [(40, 0, 10.0), (41, 0, 20.0)])
    assert 10 < valor < 15


def test_geo_idw_sin_muestras():
    with pytest.raises(DatosNoValidos):
        geo.idw(40, -3, [])


# --- Estacion ----------------------------------------------------------------

def test_estacion_limpia_textos_y_codigo_en_mayusculas():
    e = estacion()
    assert e.codigo == "MAD01"
    assert e.nombre == "Madrid - Centro"


@pytest.mark.parametrize("campo", ["codigo", "nombre", "provincia"])
def test_estacion_campos_obligatorios(campo):
    with pytest.raises(DatosNoValidos, match=campo):
        estacion(**{campo: "   "})


def test_estacion_coordenada_fuera_de_rango():
    with pytest.raises(CoordenadaNoValida):
        estacion(lat=100)


def test_estacion_coordenadas_y_distancia():
    e = estacion()
    assert e.coordenadas == (40.4215, -3.6823)
    assert e.distancia_a(*BARCELONA) == pytest.approx(geo.haversine(*e.coordenadas, *BARCELONA))


def test_estacion_a_fila_y_desde_fila_son_inversas():
    e = estacion()
    fila = e.a_fila()
    assert list(fila) == CAMPOS_ESTACION
    assert all(isinstance(valor, str) for valor in fila.values())
    assert Estacion.desde_fila(fila) == e


def test_estacion_desde_fila_falta_campo():
    fila = estacion().a_fila()
    del fila["lat"]
    with pytest.raises(DatosNoValidos) as info:
        Estacion.desde_fila(fila)
    assert isinstance(info.value.__cause__, KeyError)


def test_estacion_desde_fila_numero_no_valido():
    fila = {**estacion().a_fila(), "lon": "oeste"}
    with pytest.raises(DatosNoValidos) as info:
        Estacion.desde_fila(fila)
    assert isinstance(info.value.__cause__, ValueError)


def test_estacion_todas_las_del_csv_son_validas():
    with open(DATOS / "estaciones.csv", encoding="utf-8", newline="") as fichero:
        estaciones = [Estacion.desde_fila(fila) for fila in csv.DictReader(fichero)]
    assert len(estaciones) == 60
    assert len({e.codigo for e in estaciones}) == 60


# --- Medicion ----------------------------------------------------------------

def test_medicion_valida_y_codigo_en_mayusculas():
    assert medicion(codigo=" mad01 ").codigo == "MAD01"


def test_medicion_admite_valores_ausentes():
    m = medicion(pm25=None, no2=None)
    assert m.pm25 is None


@pytest.mark.parametrize("variable, valor", [("temperatura", 70), ("humedad", 101),
                                             ("pm25", -1), ("no2", 2000)])
def test_medicion_fuera_de_rango(variable, valor):
    with pytest.raises(DatosNoValidos, match=f"{variable} fuera de rango"):
        medicion(**{variable: valor})


def test_medicion_codigo_obligatorio():
    with pytest.raises(DatosNoValidos):
        medicion(codigo="")


def test_medicion_supera_umbral():
    m = medicion(pm25=12.0, no2=40.0)
    assert m.supera_umbral("no2") is True
    assert m.supera_umbral("pm25") is False
    assert medicion(no2=None).supera_umbral("no2") is False


def test_medicion_supera_umbral_contaminante_no_valido():
    with pytest.raises(DatosNoValidos):
        medicion().supera_umbral("ozono")


def test_medicion_a_fila_y_desde_fila_son_inversas():
    m = medicion(pm25=None)
    fila = m.a_fila()
    assert list(fila) == CAMPOS_MEDICION
    assert fila["fecha_hora"] == "2026-11-01T08:00"
    assert fila["pm25"] == ""
    assert Medicion.desde_fila(fila) == m


def test_medicion_desde_fila_fecha_no_valida():
    fila = {**medicion().a_fila(), "fecha_hora": "1 de noviembre"}
    with pytest.raises(DatosNoValidos) as info:
        Medicion.desde_fila(fila)
    assert isinstance(info.value.__cause__, ValueError)


def test_medicion_las_del_csv_son_validas():
    with open(DATOS / "mediciones.csv", encoding="utf-8", newline="") as fichero:
        mediciones = [Medicion.desde_fila(fila) for fila in csv.DictReader(fichero)]
    assert len(mediciones) == 60 * 91 * 24   # 60 estaciones, septiembre-noviembre
