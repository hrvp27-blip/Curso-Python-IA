"""Tests de la red, el almacén, el análisis, las escalas, la predicción, los episodios y los informes."""

import io
import json
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
import pytest

from estaciones import almacen, analisis, episodios, escalas, geo, informes, mapa, prediccion
from estaciones.excepciones import DatosNoValidos, ErrorDeAlmacen, EstacionNoEncontrada
from estaciones.modelos import Estacion, Medicion
from estaciones.red import RedEstaciones

DATOS = Path(__file__).parent.parent / "datos"
MOMENTO = datetime(2026, 11, 10, 8)


@pytest.fixture(scope="module")
def red():
    return almacen.cargar_red(DATOS / "estaciones.csv", DATOS / "mediciones.csv")


@pytest.fixture(scope="module")
def tabla(red):
    return analisis.a_tabla(red.mediciones(), list(red))


def mini_red():
    """Tres estaciones en línea a lo largo del meridiano 0 y una medición de cada una."""
    red = RedEstaciones([Estacion("A", "Sur", "P", 39.0, 0.0), Estacion("B", "Centro", "P", 40.0, 0.0),
                         Estacion("C", "Norte", "P", 41.0, 0.0)])
    for codigo, valor in (("A", 10.0), ("B", 20.0), ("C", 30.0)):
        red.registrar(Medicion(codigo, MOMENTO, no2=valor))
    return red


# --- red ---------------------------------------------------------------------

def test_red_anadir_obtener_y_duplicado():
    red = mini_red()
    assert len(red) == 3
    assert red.obtener(" b ").nombre == "Centro"
    with pytest.raises(DatosNoValidos):
        red.anadir(Estacion("A", "Otra", "P", 0, 0))
    with pytest.raises(EstacionNoEncontrada):
        red.obtener("Z")


def test_red_registrar_medicion_de_estacion_desconocida():
    with pytest.raises(EstacionNoEncontrada):
        mini_red().registrar(Medicion("Z", MOMENTO))


def test_red_cercanas_ordenadas_y_mas_cercana():
    red = mini_red()
    cercanas = red.cercanas(40.2, 0.0, 130)
    assert [e.codigo for e, _ in cercanas] == ["B", "C"]
    assert cercanas[0][1] < cercanas[1][1]
    assert red.mas_cercana(38.0, 0.0)[0].codigo == "A"


def test_red_mas_cercana_red_vacia():
    with pytest.raises(DatosNoValidos):
        RedEstaciones().mas_cercana(40, 0)


def test_red_en_zona_y_por_provincia():
    red = mini_red()
    assert [e.codigo for e in red.en_zona((39.5, -1, 41.5, 1))] == ["B", "C"]
    assert red.por_provincia() == {"P": 3}


def test_red_estimar_en_una_estacion_y_entre_dos():
    red = mini_red()
    assert red.estimar(40.0, 0.0, "no2", MOMENTO) == 20.0
    assert 20 < red.estimar(40.5, 0.0, "no2", MOMENTO) < 30


def test_red_estimar_sin_datos_a_esa_hora():
    with pytest.raises(DatosNoValidos):
        mini_red().estimar(40, 0, "no2", MOMENTO + timedelta(hours=1))


# --- almacén -----------------------------------------------------------------

def test_almacen_guardar_y_cargar_estaciones(tmp_path):
    estaciones = list(mini_red())
    almacen.guardar_estaciones(estaciones, tmp_path / "e.csv")
    assert almacen.cargar_estaciones(tmp_path / "e.csv") == estaciones


def test_almacen_mediciones_inexistentes_es_lista_vacia(tmp_path):
    assert almacen.cargar_mediciones(tmp_path / "no.csv") == []


def test_almacen_estaciones_inexistentes_es_error(tmp_path):
    with pytest.raises(ErrorDeAlmacen):
        almacen.cargar_estaciones(tmp_path / "no.csv")


def test_almacen_fila_mala_indica_la_linea():
    flujo = io.StringIO("codigo,nombre,provincia,lat,lon,altitud\nA,x,y,40,0,1\nB,x,y,999,0,1\n")
    with pytest.raises(ErrorDeAlmacen, match="línea 3"):
        almacen.leer_estaciones(flujo)


def test_almacen_leer_desde_flujo_y_red_desde():
    estaciones = almacen.leer_estaciones(io.StringIO("codigo,nombre,provincia,lat,lon,altitud\n"
                                                     "A,Uno,P,40,0,10\n"))
    mediciones = almacen.leer_mediciones(io.StringIO(
        "codigo,fecha_hora,temperatura,humedad,pm25,no2\nA,2026-11-01T00:00,10,50,,20\n"))
    red = almacen.red_desde(estaciones, mediciones)
    assert red.mediciones()[0].pm25 is None


def test_almacen_geojson_lon_lat_y_valor():
    geojson = almacen.a_geojson(list(mini_red()), {"B": 20.0})
    punto = geojson["features"][1]
    assert punto["geometry"]["coordinates"] == [0.0, 40.0]
    assert punto["properties"]["valor"] == 20.0
    assert "valor" not in geojson["features"][0]["properties"]


def test_almacen_exportar_geojson(tmp_path):
    almacen.exportar_geojson(list(mini_red()), tmp_path / "r.geojson")
    contenido = json.loads((tmp_path / "r.geojson").read_text(encoding="utf-8"))
    assert contenido["type"] == "FeatureCollection"


# --- análisis ----------------------------------------------------------------

def test_analisis_tabla_tipos(tabla):
    assert len(tabla) == 60 * 91 * 24
    assert pd.api.types.is_datetime64_any_dtype(tabla["fecha_hora"])
    assert tabla["no2"].dtype == "float64"
    assert {"nombre", "lat", "lon"} <= set(tabla.columns)


def test_analisis_medias_diarias_forma(tabla):
    assert analisis.medias_diarias(tabla, "temperatura").shape == (91, 60)


def test_analisis_excedencias_incluye_todas_ordenadas(tabla):
    dias = analisis.excedencias(tabla, "no2")
    assert len(dias) == 60
    assert dias.is_monotonic_decreasing


def test_analisis_ciclo_diario_24_horas(tabla):
    assert list(analisis.ciclo_diario(tabla, "no2").index) == list(range(24))


def test_analisis_indicadores_tipos_python(tabla):
    cifras = analisis.indicadores(tabla, date(2026, 11, 10))
    assert isinstance(cifras["estaciones"], int)
    assert isinstance(cifras["temperatura_media"], float)
    assert cifras["mas_fria"] in {e.codigo for e in almacen.cargar_estaciones(DATOS / "estaciones.csv")}


def test_analisis_variable_no_valida(tabla):
    with pytest.raises(DatosNoValidos):
        analisis.ranking(tabla, "ozono")


# --- escalas -----------------------------------------------------------------

@pytest.mark.parametrize("variable, valor, clase", [
    ("no2", 30, "Buena"), ("no2", 100, "Regular"), ("pm25", 80, "Extremadamente desfavorable"),
    ("temperatura", 19, "16 a 20"), ("temperatura", -10, "≤ -4"), ("humedad", 95, "> 90 %"),
])
def test_escalas_clase(variable, valor, clase):
    assert escalas.clase(variable, valor) == clase


def test_escalas_misma_cantidad_de_colores_y_etiquetas():
    for variable, datos in escalas.ESCALAS.items():
        assert len(datos["colores"]) == len(datos["cortes"]) + 1 == len(escalas.etiquetas(variable))


def test_escalas_19_grados_no_es_rojo():
    assert escalas.color("temperatura", 19) not in ("#E53935", "#8E0000")


def test_escalas_proporcion_limitada():
    assert escalas.proporcion("no2", -5) == 0
    assert escalas.proporcion("no2", 500) == 1


# --- geo extra ---------------------------------------------------------------

@pytest.mark.parametrize("grados, latitud, texto", [
    (40.4215, True, "40° 25′ 17″ N"), (-3.6823, False, "3° 40′ 56″ O"),
    (-33.5, True, "33° 30′ 00″ S"), (2.0, False, "2° 00′ 00″ E"),
])
def test_geo_sexagesimal(grados, latitud, texto):
    assert geo.a_sexagesimal(grados, latitud) == texto


# --- predicción --------------------------------------------------------------

def test_prediccion_forma_y_banda(tabla):
    modelo = prediccion.ajustar(tabla, "no2", datetime(2026, 11, 20, 23))
    futuro = prediccion.predecir(modelo, 48)
    assert len(futuro) == 60 * 48
    assert futuro["paso"].min() == 1 and futuro["paso"].max() == 48
    assert (futuro["inferior"] <= futuro["prediccion"]).all()
    assert (futuro["prediccion"] <= futuro["superior"]).all()
    assert 0 <= modelo.phi < 1


def test_prediccion_banda_crece_con_el_horizonte(tabla):
    futuro = prediccion.predecir(prediccion.ajustar(tabla, "temperatura",
                                                    datetime(2026, 11, 20, 23)), 24)
    ancho = (futuro["superior"] - futuro["inferior"]).groupby(futuro["paso"]).mean()
    assert ancho.iloc[-1] > ancho.iloc[0]


def test_prediccion_respeta_rangos_fisicos(tabla):
    futuro = prediccion.predecir(prediccion.ajustar(tabla, "humedad",
                                                    datetime(2026, 11, 20, 23)), 24)
    assert futuro["superior"].max() <= 100 and futuro["inferior"].min() >= 0


def test_prediccion_sin_historia_suficiente(tabla):
    with pytest.raises(DatosNoValidos):
        prediccion.ajustar(tabla, "no2", datetime(2026, 9, 1, 5))


def test_prediccion_mejora_a_la_persistencia(tabla):
    resumen = prediccion.resumen_validacion(prediccion.validar(tabla, "temperatura"))
    assert resumen["modelo"] < resumen["persistencia"]
    assert resumen["mejora"] > 0


# --- episodios ---------------------------------------------------------------

def tabla_artificial(valores):
    inicio = datetime(2026, 11, 1)
    return pd.DataFrame({"codigo": "A", "nombre": "Uno", "provincia": "P",
                         "fecha_hora": [inicio + timedelta(hours=h) for h in range(len(valores))],
                         "no2": valores, "temperatura": valores})


def test_episodios_detecta_tramos_y_duracion_minima():
    tabla = tabla_artificial([10, 30, 30, 30, 10, 30, 10, 40, 40, 40, 40])
    encontrados = episodios.detectar(tabla, "no2", 25, minimo_horas=3)
    assert list(encontrados["horas"]) == [3, 4]
    assert list(encontrados["pico"]) == [30, 40]


def test_episodios_por_debajo():
    encontrados = episodios.detectar(tabla_artificial([5, -1, -2, -1, 3]), "temperatura", 0,
                                     minimo_horas=2, por_debajo=True)
    assert len(encontrados) == 1 and encontrados.iloc[0]["pico"] == -2


def test_episodios_hueco_sin_dato_corta():
    tabla = tabla_artificial([30, 30, None, 30, 30])
    assert len(episodios.detectar(tabla, "no2", 25, minimo_horas=3)) == 0


def test_episodios_activos_y_por_estacion():
    encontrados = episodios.detectar(tabla_artificial([30, 30, 30, 10]), "no2", 25)
    assert len(episodios.activos(encontrados, datetime(2026, 11, 1, 1))) == 1
    assert len(episodios.activos(encontrados, datetime(2026, 11, 1, 3))) == 0
    assert episodios.por_estacion(encontrados).iloc[0]["horas"] == 3


def test_episodios_sin_resultados_devuelve_tabla_vacia():
    assert episodios.detectar(tabla_artificial([1, 2, 3]), "no2", 25).empty


# --- informes y mapa ---------------------------------------------------------

def test_informes_de_un_dia(tabla):
    texto = informes.informe(tabla, date(2026, 11, 10))
    assert texto.startswith("# Informe de la red nacional de estaciones del 10/11/2026")
    assert "Categoría ICA" in texto and "### Temperatura" in texto


def test_informes_dia_sin_datos(tabla):
    with pytest.raises(DatosNoValidos):
        informes.informe(tabla, date(2027, 1, 1))


def test_mapa_html_con_todas_las_estaciones(red, tmp_path):
    html = mapa.crear_mapa(list(red), {"MAD01": 30.0}, "no2", "Prueba", tmp_path / "m.html")
    assert html.count("circle_marker") >= 25
    assert (tmp_path / "m.html").exists()
