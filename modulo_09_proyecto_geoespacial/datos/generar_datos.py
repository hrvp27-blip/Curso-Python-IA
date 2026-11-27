"""Genera ``mediciones.csv``: datos horarios sintéticos pero realistas de septiembre a noviembre de 2026.

Las coordenadas de ``estaciones.csv`` son reales; las mediciones no. Siguen
estas reglas para que el análisis tenga sentido:

- Temperatura: baja con la latitud y con la altitud (6,5 °C por km) y tiene
  ciclo diario, más marcado en el interior que en la costa. Del 1 de
  septiembre al 30 de noviembre baja unos 7 °C (el otoño avanza).
- Humedad: más alta en la costa y por la noche, cuando baja la temperatura;
  sube a medida que avanza el otoño.
- NO₂: depende del tamaño de la ciudad y tiene picos en las horas punta de
  tráfico (8 h y 20 h). Empeora algo con el frío (más inversiones térmicas
  y calefacciones).
- PM2.5: nivel de fondo con días buenos y malos; en Canarias hay episodios
  de calima con valores muy altos.
- El tiempo y la calidad del aire de cada día dependen del anterior (proceso
  AR(1)), como las situaciones meteorológicas reales que duran varios días.
- Alrededor del 1 % de las lecturas de contaminantes faltan (sensor caído).

Con la misma semilla se obtienen siempre los mismos datos.
"""

import csv
import math
import random
from datetime import datetime, timedelta
from pathlib import Path

CARPETA = Path(__file__).parent
SEMILLA = 2026
INICIO = datetime(2026, 9, 1)
DIAS = 91
CAMPOS = ["codigo", "fecha_hora", "temperatura", "humedad", "pm25", "no2"]

# Ciudades con más tráfico: multiplican el NO₂ y algo las partículas
FACTOR_CIUDAD = {"MAD01": 1.8, "MAD02": 1.1, "BCN01": 1.7, "VAL01": 1.3, "SEV01": 1.3,
                 "BIL01": 1.2, "ZAR01": 1.2, "MAL01": 1.2, "MUR01": 1.1, "ALG01": 1.2,
                 "VIG01": 1.1, "GIJ01": 1.1, "CBA01": 1.1, "TAR01": 1.1, "CAR01": 1.1}
CANARIAS = {"LPA01", "TFN01", "LZT01"}


def otono(dia):
    """Avance del otoño: 0 el 1 de septiembre y 1 el último día."""
    return dia / (DIAS - 1)


def campana(hora, centro, anchura):
    """Curva en forma de campana para modelar los picos de tráfico."""
    return math.exp(-((hora - centro) / anchura) ** 2)


def series_de_estacion(estacion, generador):
    """Devuelve las filas horarias de una estación para todo el periodo."""
    codigo = estacion["codigo"]
    lat, altitud = float(estacion["lat"]), float(estacion["altitud"])
    costera = altitud < 50
    factor = FACTOR_CIUDAD.get(codigo, 0.9)
    temperatura_base = 22 - 0.55 * (lat - 28) - 0.0065 * altitud
    amplitud = 3 if costera else 5 + altitud / 400
    # Unos 3 días de calima al mes en Canarias
    dias_calima = set(generador.sample(range(DIAS), 9)) if codigo in CANARIAS else set()
    filas = []
    tiempo_del_dia, log_calidad = 0.0, 0.0
    for dia in range(DIAS):
        # Las situaciones meteorológicas duran varios días: cada día se parece al anterior
        tiempo_del_dia = 0.75 * tiempo_del_dia + generador.gauss(0, 1.3)
        log_calidad = 0.75 * log_calidad + generador.gauss(0, 0.23)
        calidad_del_dia = math.exp(log_calidad)
        estacional = 5 - 7 * otono(dia)           # °C sobre la media: +5 en septiembre, -2 al final
        for hora in range(24):
            momento = INICIO + timedelta(days=dia, hours=hora)
            ciclo = math.sin(2 * math.pi * (hora - 9) / 24)
            temperatura = (temperatura_base + estacional + tiempo_del_dia + amplitud * ciclo
                           + generador.gauss(0, 0.5))
            humedad = ((78 if costera else 68) + 8 * otono(dia) - 4 * amplitud * ciclo
                       + generador.gauss(0, 4))
            trafico = 0.5 + 0.8 * campana(hora, 8, 2) + 0.6 * campana(hora, 20, 2.5)
            no2 = (18 * factor * trafico * calidad_del_dia * (0.85 + 0.3 * otono(dia))
                   + generador.gauss(0, 2))
            pm25 = 7 * (0.6 + 0.4 * factor) * calidad_del_dia * (0.8 + 0.3 * trafico) + generador.gauss(0, 1)
            if dia in dias_calima:
                pm25 *= 5
            filas.append({
                "codigo": codigo,
                "fecha_hora": momento.isoformat(timespec="minutes"),
                "temperatura": round(temperatura, 1),
                "humedad": round(min(100, max(10, humedad)), 1),
                "pm25": "" if generador.random() < 0.01 else round(max(0.5, pm25), 1),
                "no2": "" if generador.random() < 0.01 else round(max(1, no2), 1),
            })
    return filas


def main():
    """Lee las estaciones y escribe ``mediciones.csv`` junto a este script."""
    generador = random.Random(SEMILLA)
    with open(CARPETA / "estaciones.csv", encoding="utf-8", newline="") as fichero:
        estaciones = list(csv.DictReader(fichero))
    with open(CARPETA / "mediciones.csv", "w", encoding="utf-8", newline="") as fichero:
        escritor = csv.DictWriter(fichero, fieldnames=CAMPOS)
        escritor.writeheader()
        for estacion in estaciones:
            escritor.writerows(series_de_estacion(estacion, generador))
    print(f"Generadas {len(estaciones) * DIAS * 24} mediciones de {len(estaciones)} estaciones.")


if __name__ == "__main__":
    main()
