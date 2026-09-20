# Notas Técnicas del Proyecto

## Información General
- **Proyecto:** Monitoreo del Nivel de Agua, Conectividad Ecohidrológica y Validación SWOT en el Río Magdalena
- **Zona de Estudio:** Barrancabermeja, Santander, Colombia (Lat 7.065°N, Lon -73.855°W)
- **Estación de Referencia:** BARRANCABERMEJA - AUT [23157030] (IDEAM)

## Estructura de Datos y Procesamiento
- `data/raw/` → Series temporales oficiales del IDEAM (DHIME) y descargas SWOT vía Hydrocron API.
- `data/processed/` → Figuras de alta resolución (PNG) y tablas exportadas (Excel/CSV).
- `notebooks/` → Cuadernos interactivos de Jupyter para análisis exploratorio.
- `scripts/` → Módulos y scripts reutilizables en Python (`magdalena_utils.py`, `Descarga SWOT.py`, etc.).
- `docs/` → Documentación técnica, notas metodológicas y referencias.

## Hitos Completados
- [x] Adquisición y limpieza de 11 años de datos in-situ del IDEAM (2014–2024).
- [x] Descubrimiento espacial de tramos SWORD (`reach_id`) cercanos a Barrancabermeja mediante la API CMR de NASA Earthdata.
- [x] Descarga automatizada de series de WSE, ancho y pendiente vía API Hydrocron de NASA PO.DAAC.
- [x] Armonización de datums: contraste entre cota de mira relativa (IDEAM) y WSE sobre el geoide WGS84 (SWOT).
- [x] Análisis del impacto de anomalías climáticas (evento El Niño 2023–2024 con índice ONI de la NOAA).
- [x] Implementación de métricas de conectividad ecohidrológica río-ciénaga con umbral `z_fondo`.

## Eventos Climáticos de Referencia (ENSO)
- **2015–2016:** Episodio de El Niño Fuerte.
- **2023–2024:** Episodio de El Niño Moderado-Fuerte (analizado y contrastado con datos satelitales SWOT).

## Recursos y APIs
- **IDEAM (DHIME):** http://dhime.ideam.gov.co/
- **NASA PO.DAAC Hydrocron API:** https://podaac.github.io/hydrocron/
- **SWOT Mission (JPL/NASA):** https://swot.jpl.nasa.gov/
- **SWORD Explorer:** https://www.swordexplorer.com/
