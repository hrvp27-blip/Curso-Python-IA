"""Módulo 6 - Práctica 6: importador de ventas en CSV.

Lee un CSV de ventas, valida cada fila, registra las que no valen y exporta
un resumen por región.

Ampliaciones:

1. Acepta el delimitador punto y coma y la coma decimal (``29,5``).
2. Descarta las filas repetidas con el motivo "fila repetida".
3. ``main()`` admite ``--log fichero`` para enviar el registro a un fichero.
4. Después de importar, genera el informe de la Práctica 4 en ``informe.txt``.
"""

import csv
import logging
import sys
from datetime import date
from pathlib import Path

# Ampliación 4: la Práctica 4 está en otra carpeta del curso. Se añade al
# final de sys.path para poder ejecutar este fichero directamente; con
# pytest ya está en el path gracias a conftest.py.
CARPETA_PRACTICA_4 = Path(__file__).resolve().parents[2] / "modulo_04_colecciones" / "ejercicios"
if str(CARPETA_PRACTICA_4) not in sys.path:
    sys.path.append(str(CARPETA_PRACTICA_4))

from m4_practica_ventas import generar_informe  # noqa: E402

logger = logging.getLogger(__name__)

CAMPOS = ["fecha", "vendedor", "region", "producto", "categoria", "unidades", "precio"]
CAMPOS_RESUMEN = ["region", "ventas", "unidades", "importe"]


class ErrorDeImportacion(Exception):
    """Base de los errores del importador."""


class FicheroNoValido(ErrorDeImportacion):
    """El fichero no existe o le faltan columnas. No es recuperable."""


class FilaNoValida(ErrorDeImportacion):
    """Una fila tiene un dato incorrecto. Se anota y se sigue con la siguiente."""


def validar_fila(fila: dict, coma_decimal: bool = False) -> dict:
    """Devuelve la venta de una fila con los tipos convertidos.

    Recibe un diccionario de cadenas y devuelve uno NUEVO con los mismos
    campos sin espacios alrededor, ``unidades`` como ``int`` y ``precio``
    como ``float``. Lanza ``FilaNoValida`` con uno de estos mensajes,
    comprobados en este orden:

    - "falta el campo <nombre>" si algún campo de ``CAMPOS`` está vacío
    - "fecha no válida: <valor>" si la fecha no es una fecha ISO
    - "unidades no válidas: <valor>" si no es un entero mayor que cero
    - "precio no válido: <valor>" si no es un número mayor que cero

    Ampliación 1: con ``coma_decimal=True`` el precio puede llevar coma
    decimal (``29,5``). Solo se cambia la coma por un punto: un precio con
    separador de miles como ``1.234,5`` sigue siendo no válido, para no
    adivinar qué quería decir quien lo tecleó.
    """
    venta = {}
    for campo in CAMPOS:
        valor = (fila.get(campo) or "").strip()  # el campo puede faltar o ser None
        if not valor:
            raise FilaNoValida(f"falta el campo {campo}")
        venta[campo] = valor

    try:
        date.fromisoformat(venta["fecha"])
    except ValueError:
        raise FilaNoValida(f"fecha no válida: {venta['fecha']}") from None

    venta["unidades"] = _positivo(int, venta["unidades"], "unidades no válidas")
    a_precio = _float_con_coma if coma_decimal else float
    venta["precio"] = _positivo(a_precio, venta["precio"], "precio no válido")
    return venta


def _float_con_coma(texto: str) -> float:
    """Convierte a float aceptando la coma como separador decimal."""
    return float(texto.replace(",", "."))


def _positivo(convertir, texto: str, motivo: str):
    """Convierte el texto con ``convertir`` y comprueba que es mayor que cero.

    Si no se puede, lanza ``FilaNoValida`` con el mensaje "<motivo>: <texto>".
    """
    try:
        numero = convertir(texto)
    except ValueError:
        raise FilaNoValida(f"{motivo}: {texto}") from None
    if numero <= 0:
        raise FilaNoValida(f"{motivo}: {texto}")
    return numero


def importar_ventas(
    ruta, delimitador: str | None = None, coma_decimal: bool | None = None
) -> tuple[list[dict], list[str]]:
    """Lee el CSV y devuelve una tupla (ventas válidas, errores).

    Cada error es un texto "Línea N: motivo", donde N es el número de línea
    en el fichero (la cabecera es la línea 1) y el motivo es el mensaje de
    ``FilaNoValida``. Por cada fila descartada se registra además un aviso
    con ``logger.warning``.

    Lanza ``FicheroNoValido``:

    - "No existe el fichero <ruta>" si no se encuentra, encadenada con el
      ``FileNotFoundError`` original
    - "Faltan columnas: <nombres separados por coma y espacio>" si a la
      cabecera le falta alguna de ``CAMPOS``, en el orden de ``CAMPOS``

    Ampliación 1: si no se indica ``delimitador``, se deduce de la cabecera
    (coma o punto y coma). Si no se indica ``coma_decimal``, se activa con el
    punto y coma, que es como exporta Excel en español.

    Ampliación 2: una fila igual a otra ya importada (con los datos ya
    limpios y convertidos) se descarta con el motivo "fila repetida".
    """
    # Este try solo protege la apertura: es el error no recuperable
    try:
        fichero = open(ruta, encoding="utf-8", newline="")
    except FileNotFoundError as error:
        raise FicheroNoValido(f"No existe el fichero {ruta}") from error

    ventas, errores = [], []
    vistas = set()
    with fichero:
        if delimitador is None:
            delimitador = _detectar_delimitador(fichero)
        if coma_decimal is None:
            coma_decimal = delimitador == ";"
        lector = csv.DictReader(fichero, delimiter=delimitador)
        _comprobar_columnas(lector.fieldnames or [])
        for fila in lector:
            # Este try protege una sola fila: el error es recuperable
            try:
                venta = validar_fila(fila, coma_decimal)
                clave = tuple(venta.values())
                if clave in vistas:
                    raise FilaNoValida("fila repetida")
            except FilaNoValida as error:
                errores.append(f"Línea {lector.line_num}: {error}")
                logger.warning("Línea %d descartada: %s", lector.line_num, error)
            else:
                vistas.add(clave)
                ventas.append(venta)
    return ventas, errores


def _detectar_delimitador(fichero) -> str:
    """Mira la cabecera y devuelve ";" si tiene más puntos y comas que comas.

    Deja el fichero otra vez al principio para que lo lea ``csv.DictReader``.
    """
    cabecera = fichero.readline()
    fichero.seek(0)
    return ";" if cabecera.count(";") > cabecera.count(",") else ","


def _comprobar_columnas(cabecera: list[str]) -> None:
    """Lanza ``FicheroNoValido`` si a la cabecera le falta alguna de ``CAMPOS``."""
    faltan = [campo for campo in CAMPOS if campo not in cabecera]
    if faltan:
        raise FicheroNoValido(f"Faltan columnas: {', '.join(faltan)}")


def resumen_por_region(ventas: list[dict]) -> list[dict]:
    """Agrupa las ventas por región.

    Devuelve una lista de diccionarios con las claves de ``CAMPOS_RESUMEN``:
    la región, el número de ventas, las unidades totales y el importe total
    con dos decimales. Ordenada de mayor a menor importe.
    """
    regiones = {}
    for venta in ventas:
        grupo = regiones.setdefault(
            venta["region"], {"region": venta["region"], "ventas": 0, "unidades": 0, "importe": 0}
        )
        grupo["ventas"] += 1
        grupo["unidades"] += venta["unidades"]
        grupo["importe"] += venta["unidades"] * venta["precio"]
    for grupo in regiones.values():
        grupo["importe"] = round(grupo["importe"], 2)
    return sorted(regiones.values(), key=lambda grupo: grupo["importe"], reverse=True)


def exportar_resumen(ruta, ventas: list[dict]) -> None:
    """Escribe en un CSV el resumen por región, con la cabecera ``CAMPOS_RESUMEN``."""
    with open(ruta, "w", encoding="utf-8", newline="") as fichero:
        escritor = csv.DictWriter(fichero, fieldnames=CAMPOS_RESUMEN)
        escritor.writeheader()
        escritor.writerows(resumen_por_region(ventas))


def escribir_errores(ruta, errores: list[str]) -> None:
    """Escribe los errores en un fichero de texto, uno por línea."""
    with open(ruta, "w", encoding="utf-8") as fichero:
        for error in errores:
            fichero.write(error + "\n")


def escribir_informe(ruta, ventas: list[dict]) -> None:
    """Ampliación 4: escribe el informe de la Práctica 4 en un fichero de texto."""
    with open(ruta, "w", encoding="utf-8") as fichero:
        fichero.write(generar_informe(ventas) + "\n")


def procesar(entrada, carpeta_salida) -> dict:
    """Importa el fichero y deja los resultados en la carpeta de salida.

    Crea la carpeta si no existe y escribe en ella ``resumen.csv`` y
    ``errores.txt``. Registra con ``logger.info`` un mensaje final con las
    cantidades. Devuelve un diccionario con las claves "leidas", "validas"
    y "descartadas".

    Si el fichero de entrada no vale, ``FicheroNoValido`` sube sin capturar
    y no se escribe nada.

    Ampliación 4: escribe además ``informe.txt`` con el informe de la
    Práctica 4, generado con ``generar_informe`` a partir de las ventas
    válidas.
    """
    ventas, errores = importar_ventas(entrada)  # FicheroNoValido sube hasta main()
    carpeta = Path(carpeta_salida)
    carpeta.mkdir(parents=True, exist_ok=True)
    exportar_resumen(carpeta / "resumen.csv", ventas)
    escribir_errores(carpeta / "errores.txt", errores)
    escribir_informe(carpeta / "informe.txt", ventas)
    logger.info("Importación terminada: %d válidas y %d descartadas", len(ventas), len(errores))
    return {
        "leidas": len(ventas) + len(errores),
        "validas": len(ventas),
        "descartadas": len(errores),
    }


def main(argumentos: list[str] | None = None) -> int:
    """Punto de entrada. Se entrega hecho: es el único sitio donde se capturan
    los errores del importador y donde se configura el logging.

    Uso: python m6_practica_importador.py [entrada.csv] [carpeta_salida] [--log fichero]

    Ampliación 3: con ``--log fichero`` los mensajes del registro se envían a
    ese fichero en lugar de a la pantalla, con la fecha y la hora delante.
    """
    import argparse

    datos = Path(__file__).parent.parent / "datos"
    analizador = argparse.ArgumentParser(description="Importador de ventas en CSV.")
    analizador.add_argument("entrada", nargs="?", default=datos / "ventas_con_errores.csv")
    analizador.add_argument("salida", nargs="?", default=Path("salida_practica_6"))
    analizador.add_argument("--log", metavar="fichero", help="envía el registro a este fichero")
    opciones = analizador.parse_args(argumentos)

    manejador = _manejador_de_registro(opciones.log)
    raiz = logging.getLogger()
    nivel_anterior = raiz.level
    raiz.addHandler(manejador)
    raiz.setLevel(logging.INFO)
    try:
        cantidades = procesar(opciones.entrada, opciones.salida)
    except ErrorDeImportacion as error:
        logger.error("No se ha podido importar: %s", error)
        return 1
    finally:
        # Se deja el logging como estaba, y el fichero de registro cerrado
        raiz.removeHandler(manejador)
        raiz.setLevel(nivel_anterior)
        manejador.close()
    print(f"Leídas {cantidades['leidas']} filas: {cantidades['validas']} válidas "
          f"y {cantidades['descartadas']} descartadas. Resultados en {opciones.salida}")
    return 0


def _manejador_de_registro(ruta_log: str | None) -> logging.Handler:
    """Devuelve un manejador hacia el fichero ``ruta_log`` o, sin él, hacia la pantalla."""
    if ruta_log is None:
        manejador = logging.StreamHandler()
        manejador.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    else:
        Path(ruta_log).parent.mkdir(parents=True, exist_ok=True)
        manejador = logging.FileHandler(ruta_log, encoding="utf-8")
        manejador.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    return manejador


if __name__ == "__main__":
    raise SystemExit(main())
