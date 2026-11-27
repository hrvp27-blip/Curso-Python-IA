"""Tests de las ampliaciones del módulo 7: ejercicios y práctica."""

import os

os.environ.setdefault("MPLBACKEND", "Agg")

import json
import logging
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import pytest

import m4_datos_ventas
import m4_practica_ventas as p4
import m7_informe_pandas as inf
import m7_practica_analisis as pr

MODULO = Path(__file__).parent.parent
DATOS = MODULO / "datos"


@pytest.fixture(scope="module")
def ventas():
    return pr.preparar(pr.cargar(DATOS / "ventas_2026.csv"))


@pytest.fixture(scope="module")
def sucias_en_bruto():
    return pr.cargar(DATOS / "ventas_sucias.csv")


# ======================================================= Ejercicios
# ------------------------------------- informe de la Práctica 4 con pandas
def test_informe_pandas_igual_que_el_de_la_practica_4():
    ventas = m4_datos_ventas.VENTAS
    assert inf.generar_informe(inf.a_dataframe(ventas)) == p4.generar_informe(ventas)


def test_informe_pandas_con_un_filtro():
    sur = p4.filtrar_ventas(m4_datos_ventas.VENTAS, region="Sur", desde="2026-10-16")
    assert inf.generar_informe(inf.a_dataframe(sur)) == p4.generar_informe(sur)


def test_informe_pandas_con_las_ventas_del_anio():
    df = pd.read_csv(DATOS / "ventas_2026.csv")
    lista = df.to_dict("records")
    assert inf.generar_informe(inf.a_dataframe(lista)) == p4.generar_informe(lista)


def test_ranking_desempata_por_orden_alfabetico():
    df = pd.DataFrame({"vendedor": ["Linus", "Ada", "Grace"], "importe": [10.0, 10.0, 30.0]})
    assert inf.ranking(df, "vendedor").index.tolist() == ["Grace", "Ada", "Linus"]


# ----------------------------------------------- cuaderno resuelto
def test_cuaderno_resuelto_y_ejemplo_intacto():
    cuaderno = json.loads((MODULO / "ejercicios" / "m7_cuaderno_exploracion.ipynb").read_text(encoding="utf-8"))
    codigo = "\n".join("".join(c["source"]) for c in cuaderno["cells"] if c["cell_type"] == "code")
    assert "# Tu código aquí" not in codigo
    assert "day_of_week" in codigo and "%timeit" in codigo and "pd.concat([ventas] * 1000" in codigo
    ejemplo = (MODULO / "ejemplos" / "07_cuaderno_exploracion.ipynb").read_text(encoding="utf-8")
    assert "# Tu código aquí" in ejemplo, "El cuaderno de ejemplo no se toca"


# ======================================================= Práctica
# ------------------------------------------------- 1. indicadores ampliados
def test_indicadores_ampliados(ventas):
    resultado = pr.indicadores(ventas, ampliados=True)
    assert resultado["region_mayor_ticket"] == "Norte"
    assert resultado["dia_mas_ventas"] == "lunes"
    assert list(resultado)[:6] == list(pr.indicadores(ventas))


def test_indicadores_ampliados_coinciden_con_el_calculo_directo(ventas):
    resultado = pr.indicadores(ventas, ampliados=True)
    tickets = ventas.groupby("region")["importe"].mean()
    assert tickets[resultado["region_mayor_ticket"]] == tickets.max()
    dias = ventas["fecha"].dt.day_name().value_counts()
    assert dias.index[0] == "Monday"


# ---------------------------------------------------- 2. tercer gráfico
def test_grafico_categoria_region(ventas, tmp_path):
    abiertas = plt.get_fignums()
    ruta = pr.grafico_categoria_region(ventas, tmp_path / "graficos")
    assert ruta == tmp_path / "graficos" / "importe_por_categoria_y_region.png"
    assert ruta.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    assert plt.get_fignums() == abiertas, "Cierra la figura después de guardarla"


# ------------------------------------------------------------ 3. Excel
def test_exportar_excel(ventas, tmp_path):
    pytest.importorskip("openpyxl")
    objetivos = pd.read_csv(DATOS / "objetivos.csv")
    tablas = {"ranking": pr.ranking_vendedores(ventas, objetivos), "evolucion": pr.evolucion_mensual(ventas)}
    ruta = pr.exportar_excel(tablas, tmp_path / "salida" / "resultados.xlsx")
    hojas = pd.read_excel(ruta, sheet_name=None)
    assert list(hojas) == ["ranking", "evolucion"]
    assert hojas["ranking"]["vendedor"].tolist() == ["Ada", "Grace", "Margaret", "Alan", "Linus"]
    assert len(hojas["evolucion"]) == 10 and "Unnamed: 0" not in hojas["evolucion"].columns


# ---------------------------------------------- 4. motivos de descarte
def test_preparar_con_motivos(sucias_en_bruto):
    ventas, motivos = pr.preparar_con_motivos(sucias_en_bruto)
    assert motivos == {"fila repetida": 3, "fecha no válida": 2, "falta el vendedor": 1, "unidades no válidas": 3}
    assert len(ventas) + sum(motivos.values()) == len(sucias_en_bruto)
    pd.testing.assert_frame_equal(ventas, pr.preparar(sucias_en_bruto))


def test_preparar_con_motivos_un_motivo_por_fila():
    df = pd.DataFrame({
        "fecha": [None, "2026-01-02", "2026-01-03", "2026-01-04"],
        "vendedor": [None, "Ada", "Ada", "Ada"],
        "region": ["Sur"] * 4, "producto": ["Ratón"] * 4, "categoria": ["Periféricos"] * 4,
        "unidades": ["x", "1", "0", "2"],
        "precio": ["1", "-3", "1", "1,5"],
    })
    ventas, motivos = pr.preparar_con_motivos(df)
    assert motivos == {"fecha no válida": 1, "precio no válido": 1, "unidades no válidas": 1}
    assert ventas["importe"].tolist() == [3.0]


def test_fichero_limpio_sin_descartes(ventas):
    _, motivos = pr.preparar_con_motivos(pr.cargar(DATOS / "ventas_2026.csv"))
    assert motivos == {}


# ------------------------------------------ 5. conexión con la Práctica 6
def test_desde_importador_fichero_limpio(ventas):
    resultado, errores = pr.desde_importador(DATOS / "ventas_2026.csv")
    assert errores == []
    pd.testing.assert_frame_equal(resultado, ventas)


def test_desde_importador_fichero_sucio(caplog):
    with caplog.at_level(logging.WARNING):
        resultado, errores = pr.desde_importador(DATOS / "ventas_sucias.csv")
    assert len(resultado) == 52
    assert len(errores) == 11 and len(caplog.records) == 11
    assert "Línea 14: falta el campo region" in errores
    assert "Línea 17: unidades no válidas: tres" in errores
    assert "Sin región" not in set(resultado["region"]), "La Práctica 6 exige la región"
    assert resultado["vendedor"].str.strip().eq(resultado["vendedor"]).all()


def test_desde_importador_sin_coma_decimal():
    resultado, errores = pr.desde_importador(DATOS / "ventas_sucias.csv", coma_decimal=False)
    assert len(resultado) == 49
    assert "Línea 22: precio no válido: 480,0" in errores


def test_desde_importador_fichero_inexistente(tmp_path):
    from m6_practica_importador import FicheroNoValido

    with pytest.raises(FicheroNoValido):
        pr.desde_importador(tmp_path / "no_existe.csv")
