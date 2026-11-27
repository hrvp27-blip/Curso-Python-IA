"""Tests del territorio: punto en polígono, contorno de España, rejilla e ICA."""

import json
from pathlib import Path

import pytest

from estaciones import almacen, geo
from estaciones.excepciones import DatosNoValidos, ErrorDeAlmacen
from estaciones.modelos import CATEGORIAS_ICA, categoria_ica

DATOS = Path(__file__).parent.parent / "datos"
CUADRADO = [(0, 0), (2, 0), (2, 2), (0, 2)]
# Polígono en forma de U: el hueco central (lat 1.5, lon 1.5) queda fuera
U = [(0, 0), (3, 0), (3, 3), (2, 3), (2, 1), (1, 1), (1, 3), (0, 3)]


@pytest.fixture(scope="module")
def contorno():
    return almacen.cargar_contorno(DATOS / "espana_contorno.geojson")


# --- punto en polígono -------------------------------------------------------

@pytest.mark.parametrize("lat, lon, dentro", [(1, 1, True), (0.5, 1.9, True), (3, 1, False),
                                              (1, -0.1, False), (-1, -1, False)])
def test_territorio_punto_en_cuadrado(lat, lon, dentro):
    assert geo.punto_en_poligono(lat, lon, CUADRADO) is dentro


@pytest.mark.parametrize("lat, lon, dentro", [(0.5, 1.5, True), (2.5, 0.5, True),
                                              (2.5, 2.5, True), (2, 1.5, False)])
def test_territorio_punto_en_poligono_concavo(lat, lon, dentro):
    assert geo.punto_en_poligono(lat, lon, U) is dentro


def test_territorio_caja_de_un_poligono():
    assert geo.caja_de(U) == (0, 0, 3, 3)


def test_territorio_en_tierra_con_varios_poligonos():
    lejos = [(10, 10), (11, 10), (11, 11), (10, 11)]
    assert geo.en_tierra(1, 1, [lejos, CUADRADO])
    assert not geo.en_tierra(5, 5, [lejos, CUADRADO])


# --- rejilla -----------------------------------------------------------------

def test_territorio_rejilla_regular():
    puntos = geo.rejilla((0, 0, 1, 2), 0.5)
    assert len(puntos) == 3 * 5
    assert puntos[0] == (0, 0) and puntos[-1] == (1, 2)


def test_territorio_rejilla_en_tierra_solo_dentro():
    puntos = geo.rejilla_en_tierra([CUADRADO], 0.5)
    assert puntos
    assert all(geo.punto_en_poligono(lat, lon, CUADRADO) for lat, lon in puntos)


def test_territorio_rejilla_idw_conserva_los_puntos():
    muestras = [(0, 0, 10.0), (0, 2, 20.0)]
    resultado = geo.rejilla_idw(muestras, [(0, 0), (0, 1)])
    assert resultado[0] == (0, 0, 10.0)
    assert resultado[1][2] == pytest.approx(15.0)


# --- contorno de España ------------------------------------------------------

def test_territorio_contorno_tiene_peninsula_baleares_y_canarias(contorno):
    assert len(contorno) == 11
    assert all(anillo[0] == anillo[-1] for anillo in contorno)


def test_territorio_todas_las_estaciones_estan_en_tierra(contorno):
    estaciones = almacen.cargar_estaciones(DATOS / "estaciones.csv")
    assert all(geo.en_tierra(e.lat, e.lon, contorno) for e in estaciones)


@pytest.mark.parametrize("lugar, lat, lon", [("Lisboa", 38.72, -9.14), ("Oporto", 41.15, -8.61),
                                             ("Marruecos", 34.0, -5.0), ("Francia", 44.5, 0.5),
                                             ("Mediterráneo", 38.5, 5.0),
                                             ("Atlántico", 31.0, -15.0)])
def test_territorio_fuera_de_espana(contorno, lugar, lat, lon):
    assert not geo.en_tierra(lat, lon, contorno), lugar


def test_territorio_contorno_fichero_inexistente(tmp_path):
    with pytest.raises(ErrorDeAlmacen):
        almacen.cargar_contorno(tmp_path / "no_existe.geojson")


def test_territorio_contorno_json_roto(tmp_path):
    ruta = tmp_path / "roto.geojson"
    ruta.write_text("{esto no es json", encoding="utf-8")
    with pytest.raises(ErrorDeAlmacen) as info:
        almacen.cargar_contorno(ruta)
    assert info.value.__cause__ is not None


def test_territorio_contorno_sin_poligonos(tmp_path):
    ruta = tmp_path / "puntos.geojson"
    punto = {"type": "Feature", "properties": {},
             "geometry": {"type": "Point", "coordinates": [-3.7, 40.4]}}
    ruta.write_text(json.dumps({"type": "FeatureCollection", "features": [punto]}),
                    encoding="utf-8")
    with pytest.raises(ErrorDeAlmacen):
        almacen.cargar_contorno(ruta)


# --- ICA ---------------------------------------------------------------------

@pytest.mark.parametrize("contaminante, valor, categoria", [
    ("no2", 0, "Buena"), ("no2", 40, "Buena"), ("no2", 40.1, "Razonablemente buena"),
    ("no2", 120, "Regular"), ("no2", 230, "Desfavorable"), ("no2", 340, "Muy desfavorable"),
    ("no2", 341, "Extremadamente desfavorable"), ("pm25", 10, "Buena"),
    ("pm25", 22, "Regular"), ("pm25", 60, "Muy desfavorable"),
])
def test_territorio_categoria_ica(contaminante, valor, categoria):
    assert categoria_ica(contaminante, valor) == categoria


def test_territorio_ica_tiene_seis_categorias():
    assert len(CATEGORIAS_ICA) == 6


def test_territorio_ica_contaminante_no_valido():
    with pytest.raises(DatosNoValidos):
        categoria_ica("ozono", 50)


def test_superficie_numpy_igual_que_la_hecha_a_mano():
    """La superficie rápida del panel (NumPy) da lo mismo que geo.rejilla_idw."""
    from panel import datos
    muestras = ((40.42, -3.68, 30.0), (41.39, 2.15, 45.0), (37.40, -6.00, 12.0),
                (28.12, -15.44, 8.0))
    rapida = datos.superficie(muestras)
    puntos = list(zip(rapida["lat"], rapida["lon"]))[:400]
    a_mano = [valor for _, _, valor in geo.rejilla_idw(list(muestras), puntos)]
    assert rapida["valor"].iloc[:400].tolist() == pytest.approx(a_mano, rel=1e-9)
