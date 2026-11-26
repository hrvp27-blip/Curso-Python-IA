"""Módulo 6 - Ejercicio 2: CSV.

Todos los ficheros se abren con ``encoding="utf-8"`` y ``newline=""``.
"""

import csv
import json
from pathlib import Path


def leer_csv(ruta, delimitador: str = ",") -> list[dict]:
    """Devuelve las filas del CSV como lista de diccionarios.

    Las claves son los nombres de la cabecera y todos los valores son cadenas.
    """
    with open(ruta, encoding="utf-8", newline="") as fichero:
        return list(csv.DictReader(fichero, delimiter=delimitador))


def cabecera(ruta) -> list[str]:
    """Devuelve la lista de nombres de columna. Con el fichero vacío, lista vacía."""
    with open(ruta, encoding="utf-8", newline="") as fichero:
        return next(csv.reader(fichero), [])


def escribir_csv(ruta, registros: list[dict], campos: list[str]) -> None:
    """Escribe los registros en un CSV con la cabecera indicada en ``campos``.

    Las claves de los registros que no estén en ``campos`` se ignoran.
    """
    with open(ruta, "w", encoding="utf-8", newline="") as fichero:
        escritor = csv.DictWriter(fichero, fieldnames=campos, extrasaction="ignore")
        escritor.writeheader()
        escritor.writerows(registros)


def leer_ventas(ruta) -> list[dict]:
    """Lee un CSV de ventas y convierte ``unidades`` a ``int`` y ``precio`` a ``float``.

    El resto de los campos se dejan como cadenas.
    """
    return [
        {**fila, "unidades": int(fila["unidades"]), "precio": float(fila["precio"])}
        for fila in leer_csv(ruta)
    ]


def total_columna(ruta, columna: str) -> float:
    """Devuelve la suma de los valores de una columna numérica, con dos decimales."""
    return round(sum(float(fila[columna]) for fila in leer_csv(ruta)), 2)


def filtrar_csv(origen, destino, columna: str, valor: str) -> int:
    """Copia en ``destino`` las filas de ``origen`` en las que ``columna`` vale ``valor``.

    El fichero de destino conserva la cabecera y el orden de las columnas.
    Devuelve el número de filas copiadas.
    """
    filas = [fila for fila in leer_csv(origen) if fila[columna] == valor]
    escribir_csv(destino, filas, cabecera(origen))
    return len(filas)


def convertir_delimitador(origen, destino, de: str = ";", a: str = ",") -> None:
    """Reescribe un CSV cambiando el delimitador.

    Tiene que funcionar aunque algún campo contenga cualquiera de los dos
    delimitadores: usa ``csv.reader`` y ``csv.writer``, no ``replace``.
    """
    with (
        open(origen, encoding="utf-8", newline="") as entrada,
        open(destino, "w", encoding="utf-8", newline="") as salida,
    ):
        csv.writer(salida, delimiter=a).writerows(csv.reader(entrada, delimiter=de))


# ------------------------------------------------------- Ampliación 2: JSON
def guardar_json(ruta, datos) -> None:
    """Guarda ``datos`` en un fichero JSON legible, con sangría y sin escapar la ñ.

    Si la carpeta no existe, se crea.
    """
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as fichero:
        json.dump(datos, fichero, ensure_ascii=False, indent=2)
        fichero.write("\n")


def cargar_json(ruta):
    """Devuelve los datos guardados en un fichero JSON."""
    with open(ruta, encoding="utf-8") as fichero:
        return json.load(fichero)


def csv_a_json(origen, destino) -> int:
    """Convierte un CSV de ventas en JSON, con unidades y precio como números.

    Devuelve el número de ventas convertidas.

    Uso: python m6_ej2_csv.py   (convierte datos/ventas.csv en datos/ventas.json)
    """
    ventas = leer_ventas(origen)
    guardar_json(destino, ventas)
    return len(ventas)


if __name__ == "__main__":
    DATOS = Path(__file__).parent.parent / "datos"
    convertidas = csv_a_json(DATOS / "ventas.csv", DATOS / "ventas.json")
    print(f"{convertidas} ventas guardadas en {DATOS / 'ventas.json'}")
