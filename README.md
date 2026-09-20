# Proyecto de Tesis: Conectividad Hidraulica del Rio Magdalena

## Descripcion
Este proyecto analiza la conectividad hidraulica entre el Rio Magdalena y sus complejos cenagosos durante eventos de sequia extrema (El Nino), utilizando:
- Altimetria satelital SWOT
- Datos de estaciones IDEAM
- Fotogrametria con dron (UAV)

## Como usar este proyecto

### Requisitos
- Python 3.10+
- Librerias: pandas, numpy, matplotlib, geopandas

### Instalacion de librerias
```bash
pip install pandas numpy matplotlib geopandas
```

├── data/
│   ├── raw/                         # Datos crudos (descargaDhime.csv, SWOT_lvl_h2o_barrancabermeja.csv)
│   └── processed/                   # Datos procesados y figuras PNG
├── notebooks/
│   └── 01_exploracion_ideam.ipynb  # Notebook principal de exploracion
├── scripts/
│   ├── mi_tesis_utils.py            # Funciones reutilizables y metricas de conectividad
│   ├── analisis_nivel_barrancabermeja.py # Analisis historico in-situ IDEAM y El Niño
│   ├── descubrir_reach_id_swot.py   # Descubrimiento espacial de tramos SWORD
│   ├── Descarga SWOT.py             # Descarga de series WSE via API Hydrocron
│   └── analisis_swot_barrancabermeja.py # Comparativa IDEAM vs SWOT y correlacion ENSO
├── docs/
│   └── notas.md                     # Notas y documentacion
└── .env.example                     # Plantilla de variables de entorno
```

### Uso
1. Abre la carpeta `proyecto_tesis_magdalena` en Antigravity IDE (o VS Code).
2. Ve a la carpeta `notebooks/`.
3. Abre `01_exploracion_ideam.ipynb`.
4. Corre las celdas una por una con `Shift + Enter`.

### Fases del proyecto
1. **Fase 1 (Meses 1-3):** Acopio y limpieza de datos
2. **Fase 2 (Meses 4-5):** Campo con dron y fotogrametria
3. **Fase 3 (Meses 6-8):** Regresion IDEAM vs SWOT
4. **Fase 4 (Meses 9-12):** Dashboard y redaccion
