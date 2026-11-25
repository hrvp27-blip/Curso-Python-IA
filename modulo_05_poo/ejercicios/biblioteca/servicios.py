"""Servicios: la biblioteca, que coordina los modelos por composición."""

from collections import deque
from datetime import date

from .modelos import Material, Prestamo, Socio


class Biblioteca:
    """El catálogo, los socios, los préstamos en curso y las reservas.

    Usa composición: contiene un diccionario de materiales por código, un
    diccionario de socios por número, una lista de préstamos y un diccionario
    de colas de reserva por código. Ninguno es accesible directamente desde
    fuera.
    """

    MULTA_POR_DIA = 0.20

    def __init__(self, nombre: str):
        """Guarda el nombre y crea ``_materiales``, ``_socios``, ``_prestamos``
        y ``_reservas`` vacíos."""
        self.nombre = nombre
        self._materiales = {}
        self._socios = {}
        self._prestamos = []
        self._reservas = {}  # código -> deque de socios en espera

    # ------------------------------------------------------------- catálogo
    def anadir_material(self, material: Material) -> None:
        """Añade un material al catálogo.

        Lanza ``ValueError`` si ya hay un material con ese código.
        """
        if material.codigo in self._materiales:
            raise ValueError(f"Ya existe el material {material.codigo}")
        self._materiales[material.codigo] = material

    def buscar(self, codigo: str) -> Material | None:
        """Devuelve el material con ese código, o ``None`` si no existe."""
        return self._materiales.get(codigo)

    def buscar_por_titulo(self, texto: str) -> list[Material]:
        """Devuelve los materiales cuyo título contiene el texto.

        No distingue mayúsculas de minúsculas. El resultado va ordenado por título.
        """
        texto = texto.lower()
        encontrados = [m for m in self._materiales.values() if texto in m.titulo.lower()]
        return sorted(encontrados, key=lambda material: material.titulo)

    def disponibles(self) -> list[Material]:
        """Devuelve los materiales disponibles, ordenados por código."""
        disponibles = [m for m in self._materiales.values() if m.disponible]
        return sorted(disponibles, key=lambda material: material.codigo)

    def __len__(self) -> int:
        """Devuelve el número de materiales del catálogo."""
        return len(self._materiales)

    def __contains__(self, codigo: str) -> bool:
        """Indica si hay un material con ese código."""
        return codigo in self._materiales

    def __iter__(self):
        """Recorre los materiales del catálogo en el orden en que se añadieron."""
        return iter(self._materiales.values())

    # --------------------------------------------------------------- socios
    def registrar_socio(self, nombre: str) -> Socio:
        """Crea un socio con el siguiente número libre, lo guarda y lo devuelve.

        Los números empiezan en 1 y son consecutivos.
        """
        socio = Socio(len(self._socios) + 1, nombre)
        self._socios[socio.numero] = socio
        return socio

    def socio(self, numero: int) -> Socio | None:
        """Devuelve el socio con ese número, o ``None`` si no existe."""
        return self._socios.get(numero)

    # ------------------------------------------------------------ préstamos
    def prestar(self, codigo: str, numero_socio: int, fecha: date) -> Prestamo:
        """Presta un material a un socio y devuelve el préstamo creado.

        Lanza ``ValueError`` con uno de estos mensajes, comprobados en este orden:

        - "No existe el material <codigo>"
        - "No existe el socio <numero>"
        - "<nombre> ha alcanzado el máximo de préstamos"
        - "<codigo> está reservado para <nombre>" si hay una cola de reservas
          y el socio no es el primero (ampliación 3)
        - el de ``Material.prestar`` si el material ya está prestado

        Si todo es correcto: marca el material como prestado, lo añade a la
        lista del socio y guarda el préstamo. Si el socio era el primero de la
        cola de reservas, sale de ella.
        """
        material = self._material_existente(codigo)
        socio = self._socio_existente(numero_socio)
        if not socio.puede_tomar_prestado():
            raise ValueError(f"{socio.nombre} ha alcanzado el máximo de préstamos")
        cola = self._reservas.get(codigo)
        if cola and cola[0] is not socio:
            raise ValueError(f"{codigo} está reservado para {cola[0].nombre}")
        material.prestar()  # el material protege su propio estado
        if cola:
            self._atender_reserva(codigo)
        socio.prestados.append(material)
        prestamo = Prestamo(material, socio, fecha)
        self._prestamos.append(prestamo)
        return prestamo

    def devolver(self, codigo: str) -> Prestamo:
        """Registra la devolución de un material y devuelve el préstamo cerrado.

        Lanza ``ValueError`` con el mensaje "No hay ningún préstamo de <codigo>"
        si ese material no está prestado. Si lo está: lo marca como
        disponible, lo quita de la lista del socio y elimina el préstamo.
        """
        prestamo = self._prestamo_en_curso(codigo)
        prestamo.material.devolver()
        prestamo.socio.prestados.remove(prestamo.material)
        self._prestamos.remove(prestamo)
        return prestamo

    @property
    def prestamos(self) -> tuple:
        """Tupla con los préstamos en curso, en el orden en que se hicieron."""
        return tuple(self._prestamos)

    def prestamos_vencidos(self, hoy: date) -> list[Prestamo]:
        """Devuelve los préstamos vencidos, del que lleva más retraso al que menos."""
        vencidos = [p for p in self._prestamos if p.esta_vencido(hoy)]
        return sorted(vencidos, key=lambda prestamo: prestamo.dias_de_retraso(hoy), reverse=True)

    def multa(self, codigo: str, hoy: date) -> float:
        """Ampliación 2: multa del préstamo en curso de ese material.

        ``MULTA_POR_DIA`` euros por cada día de retraso, con dos decimales.
        Lanza ``ValueError`` si el material no está prestado.
        """
        prestamo = self._prestamo_en_curso(codigo)
        return round(prestamo.dias_de_retraso(hoy) * self.MULTA_POR_DIA, 2)

    # ------------------------------------------------------------- reservas
    def reservar(self, codigo: str, numero_socio: int) -> int:
        """Ampliación 3: pone al socio en la cola de espera de un material prestado.

        Devuelve la posición del socio en la cola, empezando en 1. Lanza
        ``ValueError`` con uno de estos mensajes, comprobados en este orden:

        - "No existe el material <codigo>"
        - "No existe el socio <numero>"
        - "<codigo> está disponible: no hace falta reservarlo"
        - "<nombre> ya tiene <codigo>"
        - "<nombre> ya ha reservado <codigo>"
        """
        material = self._material_existente(codigo)
        socio = self._socio_existente(numero_socio)
        if material.disponible and not self._reservas.get(codigo):
            raise ValueError(f"{codigo} está disponible: no hace falta reservarlo")
        if material in socio.prestados:
            raise ValueError(f"{socio.nombre} ya tiene {codigo}")
        cola = self._reservas.setdefault(codigo, deque())
        if socio in cola:
            raise ValueError(f"{socio.nombre} ya ha reservado {codigo}")
        cola.append(socio)
        return len(cola)

    def reservas(self, codigo: str) -> tuple[Socio, ...]:
        """Tupla con los socios en espera de ese material, por orden de llegada."""
        return tuple(self._reservas.get(codigo, ()))

    def cancelar_reserva(self, codigo: str, numero_socio: int) -> None:
        """Quita al socio de la cola de ese material.

        Lanza ``ValueError`` si el socio no estaba en la cola.
        """
        socio = self._socio_existente(numero_socio)
        cola = self._reservas.get(codigo)
        if not cola or socio not in cola:
            raise ValueError(f"{socio.nombre} no ha reservado {codigo}")
        cola.remove(socio)
        if not cola:
            del self._reservas[codigo]

    # -------------------------------------------------------------- resumen
    def resumen(self) -> str:
        """Devuelve "nombre: N materiales, D disponibles, S socios"."""
        return (
            f"{self.nombre}: {len(self)} materiales, "
            f"{len(self.disponibles())} disponibles, {len(self._socios)} socios"
        )

    # ------------------------------------------------------------- internos
    def _material_existente(self, codigo: str) -> Material:
        material = self.buscar(codigo)
        if material is None:
            raise ValueError(f"No existe el material {codigo}")
        return material

    def _socio_existente(self, numero: int) -> Socio:
        socio = self.socio(numero)
        if socio is None:
            raise ValueError(f"No existe el socio {numero}")
        return socio

    def _prestamo_en_curso(self, codigo: str) -> Prestamo:
        for prestamo in self._prestamos:
            if prestamo.material.codigo == codigo:
                return prestamo
        raise ValueError(f"No hay ningún préstamo de {codigo}")

    def _atender_reserva(self, codigo: str) -> None:
        """Saca de la cola al primer socio, que acaba de recibir el material."""
        cola = self._reservas[codigo]
        cola.popleft()
        if not cola:
            del self._reservas[codigo]
