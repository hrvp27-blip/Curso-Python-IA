# Módulo 9. Proyecto geoespacial: red nacional de estaciones

Proyecto propio que aplica lo del curso a un caso de geoinformación: una red de
estaciones de calidad del aire y meteorología repartidas por toda España
(península, Baleares y Canarias), con un dashboard de "sala de control".

## Qué hace

- **Centro de control:** la hora elegida como **columnas 3D** (una por
  estación, la altura es su valor) sobre la superficie interpolada por IDW,
  plana y recortada al contorno de España. Incluye indicadores, alertas
  activas, un ranking y la reproducción del periodo hora a hora.
- **Predicción** a 24, 48 o 72 h con un modelo propio (ciclo diario +
  persistencia AR(1)), banda de incertidumbre del 80 %, mapa previsto y
  validación frente a dos referencias.
- **Estaciones:**
  - **Ficha:** coordenadas en grados, minutos y segundos, vecinas con
    distancia y rumbo, reparto por clases, ciclo diario y huella horaria.
  - **Comparador:** de dos a cuatro estaciones.
- **Datos:** carga de CSV propios y exportación a GeoJSON (QGIS), CSV,
  informe en Markdown y mapa HTML independiente (folium).
- **Ampliaciones:** ideas para seguir con el proyecto, con lo que aportaría
  cada una, lo que haría falta y el esfuerzo.

## Diseño

Tema oscuro de "sala de control" definido en `ejercicios/.streamlit/config.toml` y
`ejercicios/panel/estilo.py`:

- Fondo con auroras suaves y una rejilla de coordenadas; paneles de cristal con un filo
  de luz y entrada animada.
- Cabecera lateral con borde de degradado giratorio y reloj luminoso.
- Tarjetas KPI con brillo del color de su clase y minigráficos de área.
- Mapas con meridianos y paralelos, halo en la base de cada columna, contorno con
  resplandor y marco de visor con línea de barrido.
- Alertas con icono, cifra y barra de intensidad; ranking numerado con barras luminosas.
- `estilo.grafico()` da a todos los gráficos de ECharts el mismo aspecto (tooltip de
  cristal, ejes discretos, líneas con brillo y áreas con degradado).
- Respeta `prefers-reduced-motion`: sin animaciones si el sistema lo pide.

## Escalas oficiales

- **NO₂ y PM2.5:** las seis categorías y colores del Índice Nacional de
  Calidad del Aire (ICA) del MITECO, de *Buena* a *Extremadamente
  desfavorable*, y la guía de la OMS de 2021.
- **Temperatura y humedad:** clases de 4 °C y de 10 % con colores al estilo
  de los mapas de AEMET.

## Datos

| Fichero | Contenido |
| --- | --- |
| `datos/estaciones.csv` | 60 estaciones (todas las capitales de provincia y otras ciudades grandes) con coordenadas reales WGS84 (EPSG:4326) y altitud en metros |
| `datos/mediciones.csv` | 131 040 mediciones horarias de septiembre a noviembre de 2026: temperatura (°C), humedad (%), PM2.5 y NO₂ (µg/m³) |
| `datos/generar_datos.py` | Genera las mediciones sintéticas con semilla fija |
| `datos/espana_contorno.geojson` | Contorno simplificado a mano de la península, Baleares y Canarias (precisión de 10-20 km) |

Las mediciones son sintéticas pero siguen reglas reales:
- La temperatura baja con la latitud y la altitud.
- La humedad es mayor en la costa.
- El NO₂ tiene picos en las horas punta.
- En Canarias hay episodios de calima.
- El otoño avanza: de septiembre a noviembre baja la temperatura y suben
  la humedad y el NO₂.
- Cada día se parece al anterior, como las situaciones meteorológicas reales.

## Arquitectura

```
ejercicios/
├── m9_dashboard.py         Punto de entrada: estilo, variable global y navegación
├── app_pages/              Una página del dashboard por fichero
├── panel/                  Piezas del dashboard: datos en caché, estilo y capas pydeck
└── estaciones/             Lógica, sin Streamlit ni print
    ├── excepciones.py      Jerarquía de errores propia
    ├── geo.py              A mano: haversine, rumbo, sexagesimal, punto en polígono, rejilla, IDW
    ├── modelos.py          Estacion y Medicion (dataclasses siempre válidas) e ICA
    ├── escalas.py          Escalas de color oficiales
    ├── red.py              RedEstaciones: consultas espaciales
    ├── almacen.py          CSV (disco o subidos), GeoJSON
    ├── analisis.py         pandas sin bucles sobre filas
    ├── prediccion.py       Modelo propio y validación de origen móvil
    ├── episodios.py        Detección de episodios con pandas (para el informe)
    ├── informes.py         Informe en Markdown
    └── mapa.py             Mapa HTML con folium
```

## Ejecutar

```bash
pip install -r modulo_09_proyecto_geoespacial/requirements.txt
streamlit run modulo_09_proyecto_geoespacial/ejercicios/m9_dashboard.py
pytest modulo_09_proyecto_geoespacial                       # 146 tests
pytest --doctest-modules modulo_09_proyecto_geoespacial/ejercicios/estaciones
python modulo_09_proyecto_geoespacial/datos/generar_datos.py   # regenerar mediciones
```
