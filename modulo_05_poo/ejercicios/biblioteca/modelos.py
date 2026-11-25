"""Modelos del dominio: los materiales, los socios y los préstamos.

    Material (abstracta)      lo que se puede prestar
    ├── Libro                 21 días
    ├── Revista                7 días
    ├── Dvd                    3 días
    └── Audiolibro            14 días (ampliación 1)
    Socio                     quien toma prestado
    Prestamo                  un material prestado a un socio en una fecha

Ninguna de estas clases sabe nada de la biblioteca: cada una solo protege
sus propias reglas.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, timedelta


class Material(ABC):
    """Clase base abstracta de todo lo que se puede prestar."""

    def __init__(self, codigo: str, titulo: str, anio: int):
        """Guarda ``codigo``, ``titulo`` y ``anio``. El material empieza disponible.

        La disponibilidad se guarda en el atributo interno ``_disponible``.
        """
        self.codigo = codigo
        self.titulo = titulo
        self.anio = anio
        self._disponible = True

    @property
    def disponible(self) -> bool:
        """Indica si el material se puede prestar. Solo lectura."""
        return self._disponible

    @property
    @abstractmethod
    def dias_prestamo(self) -> int:
        """Días que se puede tener prestado este tipo de material."""

    def prestar(self) -> None:
        """Marca el material como no disponible.

        Lanza ``ValueError`` si ya estaba prestado.
        """
        if not self._disponible:
            raise ValueError(f"{self.codigo} ya está prestado")
        self._disponible = False

    def devolver(self) -> None:
        """Marca el material como disponible.

        Lanza ``ValueError`` si no estaba prestado.
        """
        if self._disponible:
            raise ValueError(f"{self.codigo} no está prestado")
        self._disponible = True

    def __str__(self) -> str:
        """Devuelve "[codigo] titulo (anio)"."""
        return f"[{self.codigo}] {self.titulo} ({self.anio})"

    def __repr__(self) -> str:
        """Devuelve "Clase('codigo', 'titulo')" con el nombre de la clase real."""
        return f"{type(self).__name__}({self.codigo!r}, {self.titulo!r})"

    def __eq__(self, otro) -> bool:
        """Dos materiales son iguales si tienen el mismo código.

        Si ``otro`` no es un Material, devuelve ``NotImplemented``.
        """
        if not isinstance(otro, Material):
            return NotImplemented
        return self.codigo == otro.codigo

    def __hash__(self) -> int:
        return hash(self.codigo)


class Libro(Material):
    """Un libro. Se presta 21 días."""

    def __init__(self, codigo: str, titulo: str, anio: int, autor: str):
        """Inicializa la parte heredada y guarda ``autor``."""
        super().__init__(codigo, titulo, anio)
        self.autor = autor

    @property
    def dias_prestamo(self) -> int:
        return 21

    def __str__(self) -> str:
        """Añade el autor a la descripción heredada: "[codigo] titulo (anio), de autor"."""
        return f"{super().__str__()}, de {self.autor}"


class Revista(Material):
    """Una revista. Se presta 7 días."""

    def __init__(self, codigo: str, titulo: str, anio: int, numero: int):
        """Inicializa la parte heredada y guarda ``numero``."""
        super().__init__(codigo, titulo, anio)
        self.numero = numero

    @property
    def dias_prestamo(self) -> int:
        return 7

    def __str__(self) -> str:
        """Añade el número: "[codigo] titulo (anio), n.º numero"."""
        return f"{super().__str__()}, n.º {self.numero}"


class Dvd(Material):
    """Un DVD. Se presta 3 días. No redefine ``__str__``."""

    def __init__(self, codigo: str, titulo: str, anio: int, minutos: int):
        """Inicializa la parte heredada y guarda ``minutos``."""
        super().__init__(codigo, titulo, anio)
        self.minutos = minutos

    @property
    def dias_prestamo(self) -> int:
        return 3


class Audiolibro(Material):
    """Ampliación 1: un audiolibro. Se presta 14 días.

    Para añadirlo no hace falta tocar ``Biblioteca``: solo trabaja con la
    interfaz de ``Material`` (``codigo``, ``disponible``, ``dias_prestamo``...).
    """

    def __init__(self, codigo: str, titulo: str, anio: int, narrador: str):
        """Inicializa la parte heredada y guarda ``narrador``."""
        super().__init__(codigo, titulo, anio)
        self.narrador = narrador

    @property
    def dias_prestamo(self) -> int:
        return 14

    def __str__(self) -> str:
        """Añade el narrador: "[codigo] titulo (anio), narrado por narrador"."""
        return f"{super().__str__()}, narrado por {self.narrador}"


@dataclass
class Socio:
    """Una persona que puede tomar materiales en préstamo.

    Campos: ``numero`` (int), ``nombre`` (str) y ``prestados``, la lista de
    materiales que tiene en este momento, que empieza vacía y es propia de
    cada socio.
    """

    MAX_PRESTAMOS = 3

    numero: int
    nombre: str
    prestados: list[Material] = field(default_factory=list)

    def puede_tomar_prestado(self) -> bool:
        """Indica si el socio tiene menos de ``MAX_PRESTAMOS`` materiales."""
        return len(self.prestados) < self.MAX_PRESTAMOS


@dataclass
class Prestamo:
    """Un material prestado a un socio en una fecha.

    Campos: ``material`` (Material), ``socio`` (Socio) y ``fecha`` (date).
    """

    material: Material
    socio: Socio
    fecha: date

    @property
    def fecha_devolucion(self) -> date:
        """Fecha límite: la del préstamo más los días que permite el material."""
        return self.fecha + timedelta(days=self.material.dias_prestamo)

    def dias_de_retraso(self, hoy: date) -> int:
        """Días transcurridos desde la fecha límite. Si no ha vencido, 0."""
        return max((hoy - self.fecha_devolucion).days, 0)

    def esta_vencido(self, hoy: date) -> bool:
        """Indica si ``hoy`` es posterior a la fecha límite."""
        return hoy > self.fecha_devolucion
