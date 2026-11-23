"""Demo del módulo 3: qué pasa al importar un módulo."""

print("Cargando saludo")


def saludar(nombre):
    """Devuelve un saludo para ``nombre``."""
    return f"Hola, {nombre}"


print("__name__ vale:", __name__)

if __name__ == "__main__":
    print(saludar("mundo"))
