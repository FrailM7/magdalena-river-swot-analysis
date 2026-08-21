import requests
import os
from datetime import datetime, timedelta
import geopandas as gpd
import pandas as pd
import glob

# Credenciales Earthdata (puedes usar .netrc, pero aquí van directas)
USER = "FrailN"
PASSWORD = "SIG2024grupo2*"

# Collection ID de RiverSP (nivel 2 vector)
COLLECTION_ID = "C3233944997-POCLOUD"
BASE_URL = "https://cmr.earthdata.nasa.gov/search/granules.json"

# Carpeta destino
os.makedirs("swot_data", exist_ok=True)

def download_month(year, month):
    start = datetime(year, month, 1)
    end = (start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    params = {
        "collection_concept_id": COLLECTION_ID,
        "temporal": f"{start.strftime('%Y-%m-%dT00:00:00Z')},{end.strftime('%Y-%m-%dT23:59:59Z')}",
        "page_size": 200
    }

    r = requests.get(BASE_URL, params=params)  # sin auth
    r.raise_for_status()
    results = r.json()["feed"]["entry"]

    for granule in results:
        for link in granule["links"]:
            href = link["href"]
            if href.endswith(".zip") and "_REACH" in href:
                fname = os.path.join("swot_data", os.path.basename(href))
                if not os.path.exists(fname):
                    print(f"Descargando {fname}...")
                    resp = requests.get(href)  # sin auth
                    resp.raise_for_status()
                    with open(fname, "wb") as f:
                        f.write(resp.content)

# Descargar todos los meses de 2023 a 2025
for year in range(2023, 2026):
    for m in range(1, 13):
        download_month(year, m)

import zipfile

# Procesar shapefiles y organizar tabla
import zipfile

files = glob.glob("swot_data/*.zip")
data = []

for f in files:
    try:
        # Solo procesar si el nombre contiene "_REACH"
        if "_REACH" not in os.path.basename(f):
            continue

        # Verificar si realmente es un zip válido
        if not zipfile.is_zipfile(f):
            print(f"Saltando {f}, no es un zip válido")
            continue

        # Crear carpeta temporal para cada zip
        extract_dir = os.path.join("swot_data", os.path.splitext(os.path.basename(f))[0])
        os.makedirs(extract_dir, exist_ok=True)

        # Extraer contenido del zip
        with zipfile.ZipFile(f, "r") as z:
            z.extractall(extract_dir)

        # Buscar shapefile dentro del zip
        shp_files = glob.glob(os.path.join(extract_dir, "*.shp"))
        if not shp_files:
            print(f"No se encontró shapefile en {f}")
            continue

        # Leer shapefile
        gdf = gpd.read_file(shp_files[0])

        # Extraer fecha del nombre del archivo (ejemplo: 20240101T004012)
        fecha_str = os.path.basename(f).split("_")[6]
        fecha = pd.to_datetime(fecha_str[:8])  # YYYYMMDD

        # Calcular promedio WSE
        promedio = gdf["WSE"].mean()

        data.append({
            "Fecha": fecha.strftime("%Y-%m-%d"),
            "lvl_h2o": promedio,
            "Anio": fecha.year,
            "Mes": fecha.month
        })
    except Exception as e:
        print(f"Error procesando {f}: {e}")

# Crear DataFrame final
df = pd.DataFrame(data)
df.to_csv("SWOT_lvl_h2o_2023_2025.csv", index=False)

print("✅ Archivo SWOT_lvl_h2o_2023_2025.csv generado con columnas: Fecha, lvl_h2o, Anio, Mes")

print(df.head())