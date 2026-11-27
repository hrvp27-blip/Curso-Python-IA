"""Lectura y escritura de ficheros: CSV y GeoJSON (hito 3)."""

import csv
import json
from pathlib import Path
from typing import TextIO

from .excepciones import DatosNoValidos, ErrorDeAlmacen
from .modelos import CAMPOS_ESTACION, CAMPOS_MEDICION, Estacion, Medicion
from .red import RedEstaciones


def _leer_flujo(flujo: TextIO, clase, nombre: str) -> list:
    """Convierte cada fila de un CSV abierto con ``clase.desde_fila``, indicando la línea si una falla."""
    objetos = []
    for linea, fila in enumerate(csv.DictReader(flujo), start=2):
        try:
            objetos.append(clase.desde_fila(fila))
        except DatosNoValidos as error:
            raise ErrorDeAlmacen(f"{nombre}, línea {linea}: {error}") from error
    return objetos


def _leer(ruta: Path, clase) -> list:
    """Lee un CSV del disco con ``_leer_flujo``."""
    with open(ruta, encoding="utf-8", newline="") as fichero:
        return _leer_flujo(fichero, clase, ruta.name)


def leer_estaciones(flujo: TextIO, nombre: str = "estaciones") -> list[Estacion]:
    """Estaciones de un CSV ya abierto (por ejemplo, uno subido desde el dashboard)."""
    return _leer_flujo(flujo, Estacion, nombre)


def leer_mediciones(flujo: TextIO, nombre: str = "mediciones") -> list[Medicion]:
    """Mediciones de un CSV ya abierto (por ejemplo, uno subido desde el dashboard)."""
    return _leer_flujo(flujo, Medicion, nombre)


def red_desde(estaciones: list[Estacion], mediciones: list[Medicion]) -> RedEstaciones:
    """Crea una red con las estaciones y registra todas las mediciones.

    Lanza ``EstacionNoEncontrada`` si una medición es de una estación que no está.
    """
    red = RedEstaciones(estaciones)
    for medicion in mediciones:
        red.registrar(medicion)
    return red


def _escribir(objetos: list, campos: list[str], ruta: Path) -> None:
    """Escribe en un CSV la ``a_fila()`` de cada objeto."""
    with open(ruta, "w", encoding="utf-8", newline="") as fichero:
        escritor = csv.DictWriter(fichero, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(objeto.a_fila() for objeto in objetos)


def cargar_estaciones(ruta: str | Path) -> list[Estacion]:
    """Lee el CSV de estaciones.

    Lanza ``ErrorDeAlmacen`` si el fichero no existe, porque sin estaciones
    no hay red, o si una fila no vale, indicando la línea.
    """
    ruta = Path(ruta)
    if not ruta.exists():
        raise ErrorDeAlmacen(f"No existe el fichero de estaciones {ruta}")
    return _leer(ruta, Estacion)


def guardar_estaciones(estaciones: list[Estacion], ruta: str | Path) -> None:
    """Escribe las estaciones en un CSV con las columnas de ``CAMPOS_ESTACION``."""
    _escribir(estaciones, CAMPOS_ESTACION, Path(ruta))


def cargar_mediciones(ruta: str | Path) -> list[Medicion]:
    """Lee el CSV de mediciones. Si no existe devuelve una lista vacía.

    Una fila que no vale lanza ``ErrorDeAlmacen`` indicando la línea.
    """
    ruta = Path(ruta)
    return _leer(ruta, Medicion) if ruta.exists() else []


def guardar_mediciones(mediciones: list[Medicion], ruta: str | Path) -> None:
    """Escribe las mediciones en un CSV con las columnas de ``CAMPOS_MEDICION``."""
    _escribir(mediciones, CAMPOS_MEDICION, Path(ruta))


def cargar_red(ruta_estaciones: str | Path, ruta_mediciones: str | Path) -> RedEstaciones:
    """Crea una red con las estaciones y registra en ella todas las mediciones."""
    return red_desde(cargar_estaciones(ruta_estaciones), cargar_mediciones(ruta_mediciones))


def cargar_contorno(ruta: str | Path) -> list[list[tuple[float, float]]]:
    """Lee los polígonos (``Polygon`` o ``MultiPolygon``) de un GeoJSON.

    Devuelve el anillo exterior de cada polígono como lista de ``(lon, lat)``;
    los huecos no se usan. Lanza ``ErrorDeAlmacen`` si el fichero no existe o
    no es un GeoJSON de polígonos.
    """
    ruta = Path(ruta)
    try:
        with open(ruta, encoding="utf-8") as fichero:
            geometrias = [feature["geometry"] for feature in json.load(fichero)["features"]]
    except FileNotFoundError as error:
        raise ErrorDeAlmacen(f"No existe el fichero {ruta}") from error
    except (json.JSONDecodeError, KeyError, TypeError) as error:
        raise ErrorDeAlmacen(f"{ruta.name} no es un GeoJSON válido") from error
    poligonos = [g["coordinates"] for g in geometrias if g["type"] == "Polygon"]
    poligonos += [p for g in geometrias if g["type"] == "MultiPolygon" for p in g["coordinates"]]
    if not poligonos:
        raise ErrorDeAlmacen(f"{ruta.name} no contiene polígonos")
    return [[(lon, lat) for lon, lat, *_ in poligono[0]] for poligono in poligonos]


def a_geojson(estaciones: list[Estacion], valores: dict[str, float] | None = None) -> dict:
    """Las estaciones como FeatureCollection GeoJSON (RFC 7946).

    Cada estación es un ``Point`` con coordenadas ``[lon, lat]`` (en ese
    orden, como pide el estándar) y sus datos en ``properties``. Si se pasa
    ``valores``, cada estación lleva además la propiedad ``valor``.
    """
    valores = valores or {}
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [estacion.lon, estacion.lat]},
                "properties": {"codigo": estacion.codigo, "nombre": estacion.nombre,
                               "provincia": estacion.provincia, "altitud": estacion.altitud,
                               **({"valor": valores[estacion.codigo]}
                                  if estacion.codigo in valores else {})},
            }
            for estacion in estaciones
        ],
    }


def exportar_geojson(estaciones: list[Estacion], ruta: str | Path,
                     valores: dict[str, float] | None = None) -> None:
    """Escribe ``a_geojson(estaciones, valores)`` en ``ruta``; se abre directamente en QGIS."""
    with open(ruta, "w", encoding="utf-8") as fichero:
        json.dump(a_geojson(estaciones, valores), fichero, ensure_ascii=False, indent=2)
