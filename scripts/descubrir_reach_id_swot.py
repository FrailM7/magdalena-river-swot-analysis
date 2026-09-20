#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
descubrir_reach_id_swot.py
Descubre los reach_id y node_id del SWORD database para el Río Magdalena
en la zona de Barrancabermeja.

Método: Descarga UN solo gránulo SWOT RiverSP Reach de la zona,
lo descomprime, lee el shapefile y filtra por proximidad a
las coordenadas de la estación IDEAM Barrancabermeja.

Requisito: pip install earthaccess geopandas shapely
           Tener cuenta Earthdata (https://urs.earthdata.nasa.gov)
"""

import os
import sys
import requests

# Fix encoding para Windows (cp1252 no soporta emojis/Unicode)
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
import zipfile
import geopandas as gpd
from shapely.geometry import Point

# ---------- Configuración ----------
# Coordenadas de la estación IDEAM Barrancabermeja [23157030]
LAT_ESTACION = 7.065
LON_ESTACION = -73.855

# Radio de búsqueda en grados (~0.5° ≈ 55 km)
RADIO_BUSQUEDA = 0.5

# Credenciales Earthdata (configurar via variables de entorno o archivo .env)
USER = os.environ.get("EARTHDATA_USERNAME", "")
PASSWORD = os.environ.get("EARTHDATA_PASSWORD", "")

# Collection IDs SWOT RiverSP (Version D - más reciente)
COLLECTION_REACH_D = "C3233942283-POCLOUD"  # Reach only, Version D
COLLECTION_NODE_D = "C3233942282-POCLOUD"   # Node only, Version D

# Alternativas Version C
COLLECTION_REACH_C = "C2799438303-POCLOUD"  # Reach only, Version C
COLLECTION_NODE_C = "C2799438301-POCLOUD"   # Node only, Version C

CMR_URL = "https://cmr.earthdata.nasa.gov/search/granules.json"

# Carpeta de trabajo
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
WORK_DIR = os.path.join(PROJECT_DIR, "swot_data", "discovery")
os.makedirs(WORK_DIR, exist_ok=True)


def buscar_granulo(collection_id, tipo="Reach"):
    """
    Busca un gránulo SWOT RiverSP que cubra la zona de Barrancabermeja.
    """
    # Bounding box alrededor de Barrancabermeja
    bbox = f"{LON_ESTACION - 1},{LAT_ESTACION - 1},{LON_ESTACION + 1},{LAT_ESTACION + 1}"

    params = {
        "collection_concept_id": collection_id,
        "temporal": "2024-01-01T00:00:00Z,2024-03-31T23:59:59Z",
        "bounding_box": bbox,
        "page_size": 5,
        "sort_key": "-start_date"
    }

    print(f"\n🔍 Buscando gránulos SWOT {tipo} en CMR...")
    r = requests.get(CMR_URL, params=params)
    r.raise_for_status()
    entries = r.json()["feed"]["entry"]

    if not entries:
        print(f"   ⚠️ No se encontraron gránulos {tipo} para la zona.")
        return None

    print(f"   ✅ Encontrados {len(entries)} gránulos")

    # Buscar el enlace al ZIP del shapefile
    for granule in entries:
        for link in granule.get("links", []):
            href = link.get("href", "")
            if href.endswith(".zip") and "RiverSP" in href:
                print(f"   📦 Gránulo: {granule['title']}")
                return href

    # Si no hay .zip, buscar enlace de datos directo
    for granule in entries:
        for link in granule.get("links", []):
            href = link.get("href", "")
            if "podaac-swot-ops-cumulus-protected" in href and href.endswith(".zip"):
                print(f"   📦 Gránulo: {granule['title']}")
                return href

    print("   ⚠️ No se encontró enlace de descarga ZIP")
    return None


def descargar_granulo(url):
    """Descarga un gránulo usando credenciales Earthdata."""
    fname = os.path.join(WORK_DIR, os.path.basename(url))
    if os.path.exists(fname):
        print(f"   ℹ️ Ya descargado: {fname}")
        return fname

    print(f"   ⬇️ Descargando {os.path.basename(url)}...")

    session = requests.Session()
    session.auth = (USER, PASSWORD)

    # Earthdata usa redirects con autenticación
    resp = session.get(url, allow_redirects=True)

    if resp.status_code == 401:
        print("   ❌ Error de autenticación. Verifica tus credenciales Earthdata.")
        print("      Alternativa: Configura un archivo .netrc con tus credenciales.")
        return None

    resp.raise_for_status()

    with open(fname, "wb") as f:
        f.write(resp.content)

    print(f"   ✅ Descargado: {fname} ({len(resp.content) / 1024 / 1024:.1f} MB)")
    return fname


def extraer_y_leer_shapefile(zip_path):
    """Extrae el ZIP y lee el shapefile contenido."""
    extract_dir = zip_path.replace(".zip", "")
    os.makedirs(extract_dir, exist_ok=True)

    if not zipfile.is_zipfile(zip_path):
        print(f"   ❌ {zip_path} no es un archivo ZIP válido")
        return None

    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(extract_dir)

    import glob
    shp_files = glob.glob(os.path.join(extract_dir, "**", "*.shp"), recursive=True)

    if not shp_files:
        print(f"   ❌ No se encontró shapefile en {zip_path}")
        return None

    print(f"   📄 Leyendo shapefile: {os.path.basename(shp_files[0])}")
    gdf = gpd.read_file(shp_files[0])
    return gdf


def filtrar_por_proximidad(gdf, lat, lon, radio_grados):
    """
    Filtra features del GeoDataFrame que estén dentro del radio
    de las coordenadas dadas.
    """
    punto_estacion = Point(lon, lat)

    # Calcular distancia (en grados) de cada feature al punto
    if gdf.geometry.geom_type.iloc[0] in ["LineString", "MultiLineString"]:
        # Para reaches (líneas), usar el centroide
        distancias = gdf.geometry.centroid.distance(punto_estacion)
    else:
        # Para nodes (puntos), usar directamente
        distancias = gdf.geometry.distance(punto_estacion)

    gdf_filtrado = gdf[distancias <= radio_grados].copy()
    gdf_filtrado["distancia_grados"] = distancias[distancias <= radio_grados]

    return gdf_filtrado.sort_values("distancia_grados")


def main():
    print("=" * 70)
    print("DESCUBRIMIENTO DE REACH_ID / NODE_ID SWOT")
    print(f"Estación IDEAM Barrancabermeja: {LAT_ESTACION}°N, {LON_ESTACION}°W")
    print(f"Radio de búsqueda: {RADIO_BUSQUEDA}°")
    print("=" * 70)

    # --- Intentar con Reaches ---
    print("\n" + "=" * 70)
    print("BUSCANDO REACHES (tramos ~10 km)")
    print("=" * 70)

    # Intentar Version D primero, luego C
    for version, coll_id in [("D", COLLECTION_REACH_D), ("C", COLLECTION_REACH_C)]:
        print(f"\n--- Intentando Versión {version} ---")
        url = buscar_granulo(coll_id, f"Reach v{version}")
        if url:
            zip_path = descargar_granulo(url)
            if zip_path:
                gdf = extraer_y_leer_shapefile(zip_path)
                if gdf is not None:
                    print(f"\n   Columnas disponibles: {list(gdf.columns)}")
                    print(f"   Total features en gránulo: {len(gdf)}")

                    # Filtrar por proximidad
                    cerca = filtrar_por_proximidad(gdf, LAT_ESTACION, LON_ESTACION, RADIO_BUSQUEDA)

                    if len(cerca) > 0:
                        print(f"\n   🎯 REACHES ENCONTRADOS CERCA DE BARRANCABERMEJA ({len(cerca)}):")
                        print("   " + "-" * 60)

                        # Buscar la columna del reach_id
                        id_col = None
                        for col in ["reach_id", "REACH_ID", "reach_i", "rch_id_dn"]:
                            if col in gdf.columns:
                                id_col = col
                                break

                        wse_col = None
                        for col in ["wse", "WSE", "wse_mean"]:
                            if col in gdf.columns:
                                wse_col = col
                                break

                        if id_col:
                            for _, row in cerca.head(10).iterrows():
                                info = f"   reach_id: {row[id_col]}"
                                if wse_col and row.get(wse_col):
                                    info += f" | WSE: {row[wse_col]:.2f} m"
                                info += f" | dist: {row['distancia_grados']:.4f}°"
                                print(info)

                            print("\n   👉 REACH_IDs para usar en Hydrocron API:")
                            for rid in cerca[id_col].unique()[:5]:
                                print(f"      {rid}")
                        else:
                            print(f"   Columnas: {list(gdf.columns[:15])}")
                            print("   ⚠️ No se encontró columna reach_id")
                    else:
                        print(f"\n   ⚠️ No se encontraron reaches dentro de {RADIO_BUSQUEDA}° de la estación")

                    break  # Éxito, no intentar otra versión

    print("\n" + "=" * 70)
    print("NOTA: Copia el reach_id de arriba y úsalo en 'Descarga SWOT.py'")
    print("=" * 70)


if __name__ == "__main__":
    main()
