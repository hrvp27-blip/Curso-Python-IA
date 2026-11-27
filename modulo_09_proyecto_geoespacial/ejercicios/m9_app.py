"""Menú de consola de la red de estaciones (hito 5).

Único sitio del proyecto con ``input``, ``print`` y captura de errores.
"""

from pathlib import Path

DATOS = Path(__file__).parent.parent / "datos"

MENU = """
RED NACIONAL DE ESTACIONES
1. Listar estaciones
2. Estaciones cercanas a un punto
3. Estación más cercana a un punto
4. Estaciones dentro de una zona
5. Estimar un valor en un punto (IDW)
6. Informe de calidad del aire
7. Exportar a GeoJSON
8. Generar mapa HTML
0. Salir"""


def main(ruta_estaciones=DATOS / "estaciones.csv", ruta_mediciones=DATOS / "mediciones.csv"):
    """Carga la red y muestra el menú hasta que se elige 0."""
    raise NotImplementedError


if __name__ == "__main__":
    main()
