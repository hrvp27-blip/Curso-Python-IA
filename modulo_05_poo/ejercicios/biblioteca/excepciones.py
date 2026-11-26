"""Excepciones propias de la biblioteca (Módulo 6, ampliación 3).

    ErrorDeBiblioteca (ValueError)    base común
    ├── MaterialNoEncontrado          el código no está en el catálogo
    ├── MaterialNoDisponible          está prestado o reservado para otro socio
    ├── SocioNoEncontrado             el número de socio no existe
    └── LimiteDePrestamos             el socio ya tiene el máximo de materiales

``ErrorDeBiblioteca`` hereda de ``ValueError`` y no directamente de
``Exception``: así el código que ya capturaba ``ValueError`` (y los tests de
la Práctica 5) sigue funcionando, y el código nuevo puede capturar solo los
errores de la biblioteca o uno concreto.
"""


class ErrorDeBiblioteca(ValueError):
    """Base de todos los errores de la biblioteca."""


class MaterialNoEncontrado(ErrorDeBiblioteca):
    """No hay ningún material con ese código en el catálogo."""

    def __init__(self, codigo: str):
        super().__init__(f"No existe el material {codigo}")
        self.codigo = codigo


class MaterialNoDisponible(ErrorDeBiblioteca):
    """El material no se puede prestar: ya está prestado o reservado para otro."""

    def __init__(self, codigo: str, motivo: str = "ya está prestado"):
        super().__init__(f"{codigo} {motivo}")
        self.codigo = codigo


class SocioNoEncontrado(ErrorDeBiblioteca):
    """No hay ningún socio con ese número."""

    def __init__(self, numero: int):
        super().__init__(f"No existe el socio {numero}")
        self.numero = numero


class LimiteDePrestamos(ErrorDeBiblioteca):
    """El socio ya tiene el máximo de materiales prestados."""

    def __init__(self, socio):
        super().__init__(f"{socio.nombre} ha alcanzado el máximo de préstamos")
        self.socio = socio
