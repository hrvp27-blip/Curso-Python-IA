"""Módulo 5 - Práctica 5: modelo de dominio de una biblioteca.

Clases del modelo:

    Material (abstracta)      lo que se puede prestar
    ├── Libro
    ├── Revista
    ├── Dvd
    └── Audiolibro            (ampliación 1)
    Socio                     quien toma prestado
    Prestamo                  un material prestado a un socio en una fecha
    Biblioteca                el catálogo, los socios y los préstamos (composición)

Ampliación 4: el código está en el paquete ``biblioteca/``, separado en
``modelos.py`` (materiales, socios y préstamos) y ``servicios.py``
(Biblioteca). Este fichero solo lo reexporta, para que el resto del curso y
los tests sigan importando ``m5_practica_biblioteca`` como antes.
"""

# =============================================================================
#  EL CÓDIGO DE LA PRÁCTICA NO ESTÁ EN ESTE FICHERO.
#  Se ha movido al paquete biblioteca/ (ampliación 4):
#
#    biblioteca/modelos.py     Material, Libro, Revista, Dvd, Audiolibro,
#                              Socio y Prestamo
#    biblioteca/servicios.py   Biblioteca (préstamos, multas y reservas)
#    biblioteca/__init__.py    reexporta todas las clases
#
#  Aquí solo se importan para que los tests sigan funcionando con
#  "import m5_practica_biblioteca", igual que en la Práctica 3.
# =============================================================================

from biblioteca import (
    Audiolibro,
    Biblioteca,
    Dvd,
    Libro,
    Material,
    Prestamo,
    Revista,
    Socio,
)

__all__ = [
    "Audiolibro",
    "Biblioteca",
    "Dvd",
    "Libro",
    "Material",
    "Prestamo",
    "Revista",
    "Socio",
]
