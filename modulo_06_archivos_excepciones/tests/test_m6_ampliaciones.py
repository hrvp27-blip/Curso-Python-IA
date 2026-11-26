"""Tests de las ampliaciones del módulo 6: ejercicios y práctica."""

import logging
from pathlib import Path

import pytest

import m5_practica_biblioteca as bib
import m6_ej2_csv as ej2
import m6_ej3_excepciones as ej3
import m6_practica_importador as imp

DATOS = Path(__file__).parent.parent / "datos"
CABECERA = "fecha,vendedor,region,producto,categoria,unidades,precio\n"


def _csv(tmp_path, contenido, nombre="entrada.csv"):
    ruta = tmp_path / nombre
    ruta.write_text(contenido, encoding="utf-8")
    return ruta


# ======================================================= Ejercicios
# ------------------------------------------- 1. logging en convertir_todos
def test_convertir_todos_registra_un_aviso_por_rechazo(caplog):
    with caplog.at_level(logging.WARNING, logger=ej3.__name__):
        assert ej3.convertir_todos(["1", "x", "2", "y"]) == ([1.0, 2.0], ["x", "y"])
    avisos = [r.getMessage() for r in caplog.records if r.levelno == logging.WARNING]
    assert len(avisos) == 2
    assert "'x'" in avisos[0] and "'y'" in avisos[1]


def test_convertir_todos_sin_avisos_si_todo_vale(caplog):
    with caplog.at_level(logging.WARNING, logger=ej3.__name__):
        ej3.convertir_todos(["1", "2.5"])
    assert caplog.records == []


def test_ej3_main(capsys):
    assert ej3.main(["1.5", "x", "--nivel", "ERROR"]) == 0
    salida = capsys.readouterr().out
    assert "Números: [1.5]" in salida
    assert "Rechazados: ['x']" in salida


# ------------------------------------------------------------- 2. JSON
def test_guardar_y_cargar_json(tmp_path):
    datos = [{"nombre": "Íñigo", "unidades": 3, "precio": 19.9, "activo": True}]
    ruta = tmp_path / "sub" / "datos.json"
    ej2.guardar_json(ruta, datos)
    assert ej2.cargar_json(ruta) == datos
    texto = ruta.read_text(encoding="utf-8")
    assert "Íñigo" in texto, "ensure_ascii=False: la ñ se guarda tal cual"
    assert texto.startswith("[\n  {"), "Con sangría para que se pueda leer"


def test_csv_a_json(tmp_path):
    destino = tmp_path / "ventas.json"
    assert ej2.csv_a_json(DATOS / "ventas.csv", destino) == 20
    ventas = ej2.cargar_json(destino)
    assert ventas == ej2.leer_ventas(DATOS / "ventas.csv")
    assert isinstance(ventas[0]["unidades"], int)


def test_ventas_json_del_curso_coincide_con_el_csv():
    assert ej2.cargar_json(DATOS / "ventas.json") == ej2.leer_ventas(DATOS / "ventas.csv")


# ------------------------------- 3. excepciones propias en la Práctica 5
@pytest.fixture
def biblioteca():
    central = bib.Biblioteca("Central")
    central.anadir_material(bib.Libro("L001", "Clean Code", 2008, "Robert C. Martin"))
    central.registrar_socio("Ada")
    central.registrar_socio("Linus")
    return central


def test_jerarquia_errores_biblioteca():
    for clase in (bib.MaterialNoEncontrado, bib.MaterialNoDisponible,
                  bib.SocioNoEncontrado, bib.LimiteDePrestamos):
        assert issubclass(clase, bib.ErrorDeBiblioteca)
    # Hereda de ValueError para no romper el código que ya lo capturaba
    assert issubclass(bib.ErrorDeBiblioteca, ValueError)


def test_material_no_encontrado(biblioteca):
    with pytest.raises(bib.MaterialNoEncontrado) as error:
        biblioteca.prestar("X999", 1, None)
    assert error.value.codigo == "X999"
    assert str(error.value) == "No existe el material X999"


def test_socio_no_encontrado(biblioteca):
    with pytest.raises(bib.SocioNoEncontrado) as error:
        biblioteca.prestar("L001", 99, None)
    assert error.value.numero == 99
    assert str(error.value) == "No existe el socio 99"


def test_material_no_disponible(biblioteca):
    from datetime import date

    biblioteca.prestar("L001", 1, date(2026, 11, 2))
    with pytest.raises(bib.MaterialNoDisponible) as error:
        biblioteca.prestar("L001", 2, date(2026, 11, 2))
    assert error.value.codigo == "L001"
    with pytest.raises(bib.MaterialNoDisponible):
        biblioteca.buscar("L001").prestar()


def test_material_reservado_para_otro(biblioteca):
    from datetime import date

    biblioteca.prestar("L001", 1, date(2026, 11, 2))
    biblioteca.reservar("L001", 2)
    biblioteca.devolver("L001")
    with pytest.raises(bib.MaterialNoDisponible) as error:
        biblioteca.prestar("L001", 1, date(2026, 11, 3))
    assert str(error.value) == "L001 está reservado para Linus"


def test_limite_de_prestamos(biblioteca):
    from datetime import date

    for codigo in ("L002", "L003", "L004"):
        biblioteca.anadir_material(bib.Libro(codigo, "x", 2000, "y"))
        biblioteca.prestar(codigo, 1, date(2026, 11, 2))
    with pytest.raises(bib.LimiteDePrestamos) as error:
        biblioteca.prestar("L001", 1, date(2026, 11, 2))
    assert error.value.socio.nombre == "Ada"
    assert str(error.value) == "Ada ha alcanzado el máximo de préstamos"


def test_otros_errores_usan_la_base(biblioteca):
    with pytest.raises(bib.ErrorDeBiblioteca):
        biblioteca.devolver("L001")
    with pytest.raises(bib.ErrorDeBiblioteca):
        biblioteca.anadir_material(bib.Libro("L001", "Repetido", 2000, "x"))


# ======================================================= Práctica
# --------------------------------- 1. punto y coma y coma decimal
def test_validar_fila_con_coma_decimal():
    fila = dict(zip(imp.CAMPOS, ["2026-10-01", "Ada", "Norte", "Ratón", "Periféricos", "2", "29,5"]))
    assert imp.validar_fila(fila, coma_decimal=True)["precio"] == 29.5
    with pytest.raises(imp.FilaNoValida):
        imp.validar_fila(fila)  # por defecto, la coma no vale
    with pytest.raises(imp.FilaNoValida) as error:
        imp.validar_fila({**fila, "precio": "1.234,5"}, coma_decimal=True)
    assert str(error.value) == "precio no válido: 1.234,5"


def test_importar_con_punto_y_coma(tmp_path):
    ruta = _csv(
        tmp_path,
        CABECERA.replace(",", ";")
        + "2026-10-01;Ada;Norte;Ratón;Periféricos;2;29,5\n"
        + "2026-10-02;Linus;Sur;Monitor;Periféricos;1;189\n"
        + "2026-10-03;Grace;Centro;Teclado;Periféricos;1;gratis\n",
    )
    ventas, errores = imp.importar_ventas(ruta)
    assert [venta["precio"] for venta in ventas] == [29.5, 189.0]
    assert errores == ["Línea 4: precio no válido: gratis"]


def test_importar_delimitador_explicito(tmp_path):
    ruta = _csv(tmp_path, CABECERA.replace(",", "|") + "2026-10-01|Ada|Norte|Ratón|P|2|10\n")
    ventas, errores = imp.importar_ventas(ruta, delimitador="|")
    assert len(ventas) == 1 and errores == []


def test_la_coma_sigue_sin_coma_decimal():
    _, errores = imp.importar_ventas(DATOS / "ventas_con_errores.csv")
    assert "Línea 13: precio no válido: 29,5" in errores


# ----------------------------------------------------- 2. filas repetidas
def test_importar_descarta_filas_repetidas(tmp_path, caplog):
    fila = "2026-10-01,Ada,Norte,Ratón,Periféricos,2,10\n"
    ruta = _csv(
        tmp_path,
        CABECERA + fila + "2026-10-02,Ada,Norte,Ratón,Periféricos,2,10\n" + fila
        + " 2026-10-01 , Ada ,Norte,Ratón,Periféricos, 2 ,10.0\n",
    )
    with caplog.at_level(logging.WARNING, logger=imp.__name__):
        ventas, errores = imp.importar_ventas(ruta)
    assert len(ventas) == 2
    assert errores == ["Línea 4: fila repetida", "Línea 5: fila repetida"]
    assert len(caplog.records) == 2


def test_una_fila_no_valida_repetida_da_su_propio_motivo(tmp_path):
    mala = "2026-10-01,Ada,Norte,Ratón,Periféricos,x,10\n"
    _, errores = imp.importar_ventas(_csv(tmp_path, CABECERA + mala + mala))
    assert errores == ["Línea 2: unidades no válidas: x", "Línea 3: unidades no válidas: x"]


# ------------------------------------------------------------ 3. --log
def test_main_con_log(tmp_path, capsys):
    registro = tmp_path / "logs" / "importacion.log"
    resultado = imp.main([
        str(DATOS / "ventas_con_errores.csv"), str(tmp_path / "salida"), "--log", str(registro),
    ])
    assert resultado == 0
    assert "12 válidas y 6 descartadas" in capsys.readouterr().out
    lineas = registro.read_text(encoding="utf-8").splitlines()
    assert len(lineas) == 7
    assert "WARNING Línea 3 descartada: unidades no válidas: tres" in lineas[0]
    assert "INFO Importación terminada" in lineas[-1]


def test_main_con_log_y_error(tmp_path):
    registro = tmp_path / "importacion.log"
    assert imp.main([str(tmp_path / "no_existe.csv"), "--log", str(registro)]) == 1
    assert "ERROR No se ha podido importar: No existe el fichero" in registro.read_text(encoding="utf-8")


def test_main_deja_el_logging_como_estaba(tmp_path):
    raiz = logging.getLogger()
    antes = (list(raiz.handlers), raiz.level)
    imp.main([str(DATOS / "ventas.csv"), str(tmp_path), "--log", str(tmp_path / "r.log")])
    assert (list(raiz.handlers), raiz.level) == antes


# ------------------------------------------------- 4. informe de la Práctica 4
def test_procesar_escribe_el_informe(tmp_path):
    imp.procesar(DATOS / "ventas_con_errores.csv", tmp_path)
    informe = (tmp_path / "informe.txt").read_text(encoding="utf-8")
    assert "INFORME DE VENTAS" in informe
    assert "12,690.30" in informe  # importe total de las 12 ventas válidas


def test_informe_coincide_con_generar_informe(tmp_path):
    from m4_practica_ventas import generar_informe

    imp.procesar(DATOS / "ventas.csv", tmp_path)
    ventas, _ = imp.importar_ventas(DATOS / "ventas.csv")
    assert (tmp_path / "informe.txt").read_text(encoding="utf-8") == generar_informe(ventas) + "\n"
