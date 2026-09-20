# 🌊 Análisis Hidrológico y Teledetección Satelital: Río Magdalena (Barrancabermeja)
### *Monitoreo del nivel del agua, conectividad ecohidrológica e impacto de El Niño mediante IDEAM y la misión SWOT (NASA/CNES)*

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![NASA SWOT](https://img.shields.io/badge/NASA-SWOT%20Mission-red.svg?logo=nasa&logoColor=white)](https://swot.jpl.nasa.gov/)
[![IDEAM](https://img.shields.io/badge/IDEAM-DHIME%20Colombia-green.svg)](http://dhime.ideam.gov.co/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 📌 Descripción del Proyecto

Este repositorio contiene un pipeline completo en Python diseñado para **integrar, procesar y comparar datos hidrológicos in-situ con altimetría satelital de última generación**. 

El caso de estudio se centra en el **Río Magdalena** en la estación limnigráfica de **Barrancabermeja [23157030]** (Santander, Colombia), evaluando la respuesta hidrológica del río y su conectividad con caños y humedales ante eventos climáticos extremos como el fenómeno de **El Niño (2023–2024)**.

### 🎯 Objetivos Principales
1. **Línea base histórica in-situ:** Procesar más de una década (2014–2024) de registros diarios oficiales del IDEAM (DHIME).
2. **Adquisición satelital optimizada:** Descargar series temporales de elevación de la lámina de agua (**WSE**), ancho y pendiente fluvial del satélite **SWOT (Surface Water and Ocean Topography)** mediante la **API Hydrocron** de PO.DAAC / NASA Earthdata Cloud.
3. **Harmonización de datums:** Contrastar mediciones referidas al cero de la mira local con cotas absolutas respecto al geoide EGM2008 / elipsoide WGS84.
4. **Conectividad ecohidrológica:** Evaluar la relación hidráulica entre el cauce principal y los complejos cenagosos adyacentes según umbrales de cota de fondo (`z_fondo`).
5. **Replicabilidad global:** Servir de plantilla modular para que investigadores y profesionales apliquen este mismo análisis a **cualquier cuenca hidrográfica del mundo**.

---

## 🏗️ Estructura del Repositorio

```text
proyecto_tesis_magdalena/
├── data/
│   ├── raw/                                     # Datos brutos (fuentes oficiales)
│   │   ├── descargaDhime.csv                    # Serie diaria IDEAM (2014-2024, cm)
│   │   └── SWOT_lvl_h2o_barrancabermeja.csv     # Serie temporal SWOT (WSE, m)
│   └── processed/                               # Salidas: figuras PNG y tablas exportadas
│       ├── comparativa_ideam_vs_swot_barrancabermeja.png
│       ├── nivel_diario_barrancabermeja.png
│       ├── nivel_mensual_barrancabermeja.png
│       ├── swot_wse_diario_barrancabermeja.png
│       ├── swot_wse_mensual_barrancabermeja.png
│       ├── promedios_mensuales_por_anio.xlsx
│       └── swot_promedios_mensuales_por_anio.xlsx
├── scripts/                                     # Módulos y scripts ejecutables
│   ├── mi_tesis_utils.py                        # Funciones comunes (ETL, calidad, conectividad)
│   ├── analisis_nivel_barrancabermeja.py        # Análisis de series históricas IDEAM
│   ├── descubrir_reach_id_swot.py               # Descubrimiento espacial de tramos SWORD
│   ├── Descarga SWOT.py                         # Descarga automatizada vía API Hydrocron
│   └── analisis_swot_barrancabermeja.py         # Comparativa IDEAM vs SWOT y correlación ENSO
├── notebooks/
│   └── 01_exploracion_ideam.ipynb               # Cuaderno interactivo de exploración
├── docs/
│   └── notas.md                                 # Apuntes metodológicos y notas de campo
├── .env.example                                 # Plantilla para credenciales seguras
├── .gitignore                                   # Configuración de exclusión de Git
└── README.md                                    # Documentación principal
```

---

## ⚙️ Requisitos e Instalación

### 1. Clonar el repositorio
```bash
git clone https://github.com/FrailM7/Tesis-Barrancabermeja-.git
cd Tesis-Barrancabermeja-
```

### 2. Crear un entorno virtual (recomendado)
```bash
python -m venv env
# En Windows:
env\Scripts\activate
# En Linux/macOS:
source env/bin/activate
```

### 3. Instalar librerías necesarias
```bash
pip install pandas numpy matplotlib openpyxl requests geopandas shapely
```

### 4. Configurar variables de entorno (Opcional)
Para la búsqueda espacial de tramos mediante la API CMR de NASA Earthdata, copia el archivo de plantilla:
```bash
copy .env.example .env   # En Windows
cp .env.example .env     # En Linux/macOS
```
Edita `.env` con tus credenciales de [NASA Earthdata](https://urs.earthdata.nasa.gov/). *(Nota: La descarga vía Hydrocron no requiere credenciales para endpoints públicos).*

---

## 🚀 Flujo de Trabajo y Uso de los Scripts

### Paso 1: Análisis de Datos In-Situ del IDEAM
```bash
python scripts/analisis_nivel_barrancabermeja.py
```
- Lee `data/raw/descargaDhime.csv`.
- Convierte lecturas de cm a metros (`lvl_h2o`).
- Genera gráficas de niveles diarios y mensuales con sombreado automático de los episodios de **El Niño** según el índice ONI de la NOAA.
- Exporta tablas pivote multianuales a CSV y Excel en `data/processed/`.

### Paso 2: Descubrimiento Espacial de Tramos SWOT (`reach_id`)
```bash
python scripts/descubrir_reach_id_swot.py
```
- Conecta a la API CMR de NASA Earthdata.
- Filtra tramos de la base **SWORD** (*SWOT River Database*) por proximidad geográfica a las coordenadas de la estación (7.065°N, -73.855°W).
- Retorna los `reach_id` más cercanos (ej. `61209100051`, `61209100031`).

### Paso 3: Descarga Automatizada de Datos SWOT (Hydrocron API)
```bash
python "scripts/Descarga SWOT.py"
```
- Consulta la **API REST Hydrocron** de PO.DAAC para los tramos definidos.
- Extrae variables hidrológicas:
  - `wse`: Elevación de la superficie del agua (Water Surface Elevation, m).
  - `wse_u`: Incertidumbre de medición de WSE (m).
  - `width`: Ancho del espejo de agua (m).
  - `slope`: Pendiente de la lámina de agua.
- Guarda la serie resultante en `data/raw/SWOT_lvl_h2o_barrancabermeja.csv`.

### Paso 4: Comparativa IDEAM vs SWOT y Análisis Climático
```bash
python scripts/analisis_swot_barrancabermeja.py
```
- Sincroniza temporalmente ambas fuentes de información.
- Genera la gráfica comparativa con **doble eje Y**:
  - **Eje izquierdo:** Nivel relativo de la estación en tierra (m).
  - **Eje derecho:** Cota absoluta del satélite SWOT (m sobre geoide WGS84).
- Resalta la anomalía y estiaje severo ocasionado por el episodio **El Niño 2023–2024**.

---

## 🧩 Módulo de Utilidades (`scripts/mi_tesis_utils.py`)

El módulo `mi_tesis_utils.py` contiene funciones modulares reutilizables:

| Función | Descripción |
| :--- | :--- |
| `cargar_ideam(ruta_csv, ...)` | Carga datasets del IDEAM/DHIME gestionando codificaciones y delimitadores. |
| `limpiar_nivel(df, ...)` | Filtra registros nulos y aplica filtros de control de calidad (`Calidad <= 2`). |
| `filtrar_periodo(df, inicio, fin)` | Filtra ventanas de tiempo específicas. |
| `calcular_conectividad(df, z_fondo)` | Clasifica el estado hidráulico en **CONECTADO** o **DESCONECTADO** según la cota de desborde/fondo de caños laterales. |
| `resumen_anual(df, ...)` | Calcula estadísticas anuales de días y porcentaje de desconexión biológica. |
| `cm_a_metros(df, ...)` | Normaliza unidades de medición. |
| `plot_nivel_diario(...)` / `plot_nivel_mensual(...)` | Funciones estandarizadas de visualización con Matplotlib. |

---

## 🌍 ¿Cómo Replicar este Análisis en Otra Cuenca del Mundo?

El diseño del algoritmo es **100% modular y agnóstico a la ubicación**:

1. **Obtén tus datos in-situ:** Coloca el archivo CSV de tu estación limnimétrica/limnigráfica local (ej. USGS, ANA, GRDC, etc.) en `data/raw/`.
2. **Ajusta las coordenadas:** En `scripts/descubrir_reach_id_swot.py` y `scripts/Descarga SWOT.py`, actualiza `LAT_ESTACION` y `LON_ESTACION` con la ubicación de tu estación o zona de interés.
3. **Descubre tu `reach_id`:** Ejecuta el descubridor o consulta [SWORD Explorer](https://www.swordexplorer.com/) para obtener los identificadores de tramo de tu río.
4. **Ejecuta la descarga y comparativa:** Corre `Descarga SWOT.py` y genera las gráficas comparativas.

---

## 📊 Resultados Visuales

El repositorio genera automáticamente visualizaciones listas para publicación:
- **`comparativa_ideam_vs_swot_barrancabermeja.png`:** Validación visual del satélite SWOT frente a los sensores en tierra.
- **`nivel_diario_barrancabermeja.png` / `swot_wse_diario_barrancabermeja.png`:** Series temporales completas con bandas de incertidumbre y fases de El Niño sombreadas.
- **`swot_promedios_mensuales_por_anio.xlsx`:** Matrices multianuales para modelación y calibración hidrodinámica.

---

## 🤝 Contribuciones y Contacto

Las contribuciones, sugerencias y mejoras son bienvenidas. Si encuentras algún problema o deseas proponer una nueva funcionalidad, no dudes en abrir un *Issue* o enviar un *Pull Request*.

- **Autor:** Nicolás (@FrailM7)
- **Proyecto:** Tesis de Grado - Conectividad Hidráulica del Río Magdalena y Teledetección Satelital.
- **Repositorio:** [https://github.com/FrailM7/Tesis-Barrancabermeja-](https://github.com/FrailM7/Tesis-Barrancabermeja-)
