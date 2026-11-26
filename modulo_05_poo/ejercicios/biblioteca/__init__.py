"""Módulo 5 - Práctica 5 (ampliación 4): paquete del modelo de una biblioteca.

El paquete separa el código en dos módulos, como en la Práctica 3:

- ``modelos``: Material y sus subclases, Socio y Prestamo.
- ``servicios``: Biblioteca, que coordina los modelos por composición.
- ``excepciones``: los errores propios de la biblioteca (Módulo 6, ampliación 3).

Este fichero reexporta las clases para poder escribir
``from biblioteca import Biblioteca, Libro``.
"""

from .excepciones import (
    ErrorDeBiblioteca,
    LimiteDePrestamos,
    MaterialNoDisponible,
    MaterialNoEncontrado,
    SocioNoEncontrado,
)
from .modelos import Audiolibro, Dvd, Libro, Material, Prestamo, Revista, Socio
from .servicios import Biblioteca

__all__ = [
    "Audiolibro",
    "Biblioteca",
    "Dvd",
    "ErrorDeBiblioteca",
    "Libro",
    "LimiteDePrestamos",
    "Material",
    "MaterialNoDisponible",
    "MaterialNoEncontrado",
    "Prestamo",
    "Revista",
    "Socio",
    "SocioNoEncontrado",
]
