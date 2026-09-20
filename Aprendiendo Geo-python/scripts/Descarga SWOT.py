#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Descarga SWOT.py
Descarga datos de nivel de agua (WSE) del satélite SWOT para el
Río Magdalena en Barrancabermeja usando la API Hydrocron de NASA.

Este script:
  1. Consulta la API Hydrocron para obtener series de tiempo de WSE
     (Water Surface Elevation) para los reaches del Río Magdalena
     cercanos a Barrancabermeja.
  2. Genera un CSV con columnas: Fecha, lvl_h2o, Anio, Mes
     compatible con analisis_swot_barrancabermeja.py

Hydrocron API Docs: https://podaac.github.io/hydrocron/
SWOT Data: https://podaac.jpl.nasa.gov/swot

NOTA: Si no conoces el reach_id, ejecuta primero:
      python descubrir_reach_id_swot.py
"""

import os
import sys
import requests
import pandas as pd
from io import StringIO
from datetime import datetime

# Fix encoding para Windows (cp1252 no soporta emojis/Unicode)
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# ---------- Ajuste de rutas ----------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)

# ---------- Configuración SWOT ----------
# API Hydrocron endpoint
HYDROCRON_URL = "https://soto.podaac.earthdatacloud.nasa.gov/hydrocron/v1/timeseries"

# ==============================================================
# REACH_IDs del Río Magdalena cerca de Barrancabermeja
# INSTRUCCIÓN: Reemplaza estos IDs con los que obtengas de
# Si no conoces los IDs, el script intentará descubrirlos
# automáticamente usando la CMR API.
# ==============================================================
# Reach IDs del Río Magdalena cerca de Barrancabermeja (SWORD v17b)
# Descubiertos desde shapefile SWOT_L2_HR_RiverSP_Reach_008_507_SA
# Los más cercanos a la estación IDEAM (7.065°N, -73.855°W):
REACH_IDS = [
    "61209100051",   # lat 6.984, lon -73.877 (más cercano, ~9 km al sur)
    "61209100031",   # lat 6.956, lon -73.945 (~15 km al suroeste)
    "61207000171",   # lat 7.517, lon -73.890 (~50 km al norte, con datos)
    "61207000161",   # lat 7.599, lon -73.837 (aguas abajo)
]

# Coordenadas de la estación IDEAM Barrancabermeja [23157030]
LAT_ESTACION = 7.065
LON_ESTACION = -73.855

# Período de datos SWOT disponibles
# SWOT entró en órbita científica en agosto 2023
FECHA_INICIO = "2023-08-01T00:00:00Z"
FECHA_FIN = "2025-12-31T23:59:59Z"

# Versiones de colección a intentar (más reciente primero)
COLLECTION_NAMES = ["SWOT_L2_HR_RiverSP_D", "SWOT_L2_HR_RiverSP_2.0"]

# Campos a descargar
FIELDS = "reach_id,time_str,wse,wse_u,width,slope,d_x_area"

# Carpeta de salida
OUTPUT_DIR = os.path.join(PROJECT_DIR, "data", "raw")
os.makedirs(OUTPUT_DIR, exist_ok=True)
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "SWOT_lvl_h2o_barrancabermeja.csv")


# ================================================================
# DESCUBRIMIENTO AUTOMÁTICO DE REACH_IDs
# ================================================================
def descubrir_reach_ids_cmr():
    """
    Descubre los reach_ids del Río Magdalena cerca de Barrancabermeja
    descargando un gránulo SWOT y filtrando por proximidad.
    
    Requiere: geopandas, shapely, zipfile
    """
    print("\n" + "=" * 60)
    print("🔍 Descubrimiento automático de REACH_IDs...")
    print("=" * 60)
    
    try:
        import geopandas as gpd
        from shapely.geometry import Point
        import zipfile
        import glob
    except ImportError:
        print("❌ Necesitas geopandas y shapely: pip install geopandas shapely")
        print("   Alternativa: Busca el reach_id en swordexplorer.com")
        return []
    
    CMR_URL = "https://cmr.earthdata.nasa.gov/search/granules.json"
    
    # Collection IDs para Reach
    collection_ids = [
        ("C3233942283-POCLOUD", "Version D"),
        ("C2799438303-POCLOUD", "Version C"),
    ]
    
    bbox = f"{LON_ESTACION - 1},{LAT_ESTACION - 1},{LON_ESTACION + 1},{LAT_ESTACION + 1}"
    
    for coll_id, version in collection_ids:
        params = {
            "collection_concept_id": coll_id,
            "temporal": "2024-01-01T00:00:00Z,2024-03-31T23:59:59Z",
            "bounding_box": bbox,
            "page_size": 3,
        }
        
        print(f"\n   Buscando gránulos {version}...")
        r = requests.get(CMR_URL, params=params)
        if r.status_code != 200:
            continue
            
        entries = r.json()["feed"]["entry"]
        if not entries:
            continue
        
        # Buscar enlace ZIP
        zip_url = None
        for granule in entries:
            for link in granule.get("links", []):
                href = link.get("href", "")
                if href.endswith(".zip") and "RiverSP" in href and "Reach" in href:
                    zip_url = href
                    break
            if zip_url:
                break
        
        if not zip_url:
            continue
        
        # Descargar
        work_dir = os.path.join(PROJECT_DIR, "swot_data", "discovery")
        os.makedirs(work_dir, exist_ok=True)
        fname = os.path.join(work_dir, os.path.basename(zip_url))
        
        if not os.path.exists(fname):
            print(f"   ⬇️ Descargando gránulo de muestra...")
            session = requests.Session()
            session.auth = ("FrailN", "SIG2024grupo2*")
            resp = session.get(zip_url, allow_redirects=True)
            if resp.status_code != 200:
                print(f"   ⚠️ Error {resp.status_code} descargando. Necesitas credenciales Earthdata.")
                continue
            with open(fname, "wb") as f:
                f.write(resp.content)
        
        if not zipfile.is_zipfile(fname):
            continue
        
        extract_dir = fname.replace(".zip", "")
        os.makedirs(extract_dir, exist_ok=True)
        with zipfile.ZipFile(fname, "r") as z:
            z.extractall(extract_dir)
        
        shp_files = glob.glob(os.path.join(extract_dir, "**", "*.shp"), recursive=True)
        if not shp_files:
            continue
        
        gdf = gpd.read_file(shp_files[0])
        punto = Point(LON_ESTACION, LAT_ESTACION)
        
        # Calcular distancia
        if gdf.geometry.geom_type.iloc[0] in ["LineString", "MultiLineString"]:
            dist = gdf.geometry.centroid.distance(punto)
        else:
            dist = gdf.geometry.distance(punto)
        
        cerca = gdf[dist <= 0.5].copy()
        cerca["dist"] = dist[dist <= 0.5]
        cerca = cerca.sort_values("dist")
        
        # Buscar columna reach_id
        id_col = None
        for col in ["reach_id", "REACH_ID", "reach_i", "rch_id_dn"]:
            if col in gdf.columns:
                id_col = col
                break
        
        if id_col and len(cerca) > 0:
            reach_ids = list(cerca[id_col].unique()[:5])
            print(f"\n   🎯 REACH_IDs encontrados cerca de Barrancabermeja:")
            for rid in reach_ids:
                print(f"      {rid}")
            return [str(rid) for rid in reach_ids]
    
    print("   ⚠️ No se pudieron descubrir reach_ids automáticamente")
    print("   👉 Busca manualmente en https://www.swordexplorer.com/")
    return []


# ================================================================
# DESCARGA VÍA HYDROCRON API
# ================================================================
def descargar_hydrocron(reach_id, collection_name, start_time, end_time, fields):
    """
    Consulta la API Hydrocron para un reach_id específico.
    Retorna un DataFrame con los datos o None si falla.
    
    NOTA: La API Hydrocron retorna JSON con la clave 'results.csv'
    que contiene el CSV como string, no CSV directo.
    """
    params = {
        "feature": "Reach",
        "feature_id": str(reach_id),
        "start_time": start_time,
        "end_time": end_time,
        "output": "csv",
        "collection_name": collection_name,
        "fields": fields,
    }
    
    try:
        resp = requests.get(HYDROCRON_URL, params=params, timeout=60)
        
        if resp.status_code == 200:
            # La respuesta es JSON: {"status":"200 OK","hits":N,"results":{"csv":"..."}}
            data = resp.json()
            hits = data.get("hits", 0)
            
            if hits > 0:
                csv_text = data.get("results", {}).get("csv", "")
                if csv_text and len(csv_text.strip().split("\n")) > 1:
                    df = pd.read_csv(StringIO(csv_text))
                    return df
            return None
        elif resp.status_code == 400:
            # Puede ser reach_id inválido o collection_name incorrecta
            return None
        else:
            print(f"      [AVISO] HTTP {resp.status_code}: {resp.text[:200]}")
            return None
    except requests.exceptions.Timeout:
        print(f"      [TIMEOUT] para reach_id {reach_id}")
        return None
    except Exception as e:
        print(f"      [ERROR] {e}")
        return None
    
    return None


def descargar_todos_los_reaches():
    """
    Descarga datos WSE para todos los reach_ids configurados,
    probando diferentes versiones de colección.
    """
    global REACH_IDS
    
    if not REACH_IDS:
        print("\n⚠️ No hay REACH_IDs configurados.")
        print("   Intentando descubrimiento automático...\n")
        REACH_IDS = descubrir_reach_ids_cmr()
        
        if not REACH_IDS:
            print("\n❌ No se pudieron obtener reach_ids.")
            print("   Opciones:")
            print("   1. Ejecuta: python descubrir_reach_id_swot.py")
            print("   2. Busca en: https://www.swordexplorer.com/")
            print("   3. Agrega manualmente REACH_IDS en este script")
            return None
    
    print("\n" + "=" * 60)
    print("📡 DESCARGANDO DATOS SWOT VÍA HYDROCRON API")
    print("=" * 60)
    print(f"Reach IDs: {REACH_IDS}")
    print(f"Período: {FECHA_INICIO} a {FECHA_FIN}")
    print(f"Campos: {FIELDS}")
    
    all_data = []
    
    for reach_id in REACH_IDS:
        print(f"\n--- Reach ID: {reach_id} ---")
        
        for collection_name in COLLECTION_NAMES:
            print(f"   Probando colección: {collection_name}...")
            
            df = descargar_hydrocron(
                reach_id=reach_id,
                collection_name=collection_name,
                start_time=FECHA_INICIO,
                end_time=FECHA_FIN,
                fields=FIELDS,
            )
            
            if df is not None and len(df) > 0:
                print(f"   ✅ {len(df)} registros obtenidos")
                df["reach_id_usado"] = reach_id
                df["collection"] = collection_name
                all_data.append(df)
                break  # Éxito con esta colección
            else:
                print(f"   ⚠️ Sin datos con {collection_name}")
    
    if not all_data:
        print("\n❌ No se obtuvieron datos de ningún reach.")
        return None
    
    # Combinar todos los DataFrames
    df_combined = pd.concat(all_data, ignore_index=True)
    return df_combined


def procesar_datos_swot(df_raw):
    """
    Procesa los datos crudos de Hydrocron para generar el CSV final
    con formato compatible con el análisis IDEAM.
    """
    print("\n" + "=" * 60)
    print("🔧 PROCESANDO DATOS SWOT")
    print("=" * 60)
    
    # La columna 'time_str' contiene la fecha/hora en formato ISO
    # Ejemplo: "2024-01-03T09:10:01Z"
    df = df_raw.copy()
    
    # Parsear fecha
    if "time_str" in df.columns:
        df["Fecha"] = pd.to_datetime(df["time_str"], errors="coerce")
    elif "time" in df.columns:
        df["Fecha"] = pd.to_datetime(df["time"], errors="coerce")
    else:
        print("❌ No se encontró columna de tiempo")
        return None
    
    # Eliminar filas sin fecha válida
    df = df.dropna(subset=["Fecha"])
    
    # WSE (Water Surface Elevation) en metros
    if "wse" in df.columns:
        df["lvl_h2o"] = pd.to_numeric(df["wse"], errors="coerce")
    elif "WSE" in df.columns:
        df["lvl_h2o"] = pd.to_numeric(df["WSE"], errors="coerce")
    else:
        print("❌ No se encontró columna WSE")
        return None
    
    # Filtrar valores inválidos de SWOT
    # Los fill values de SWOT son típicamente -999999999999 o similares
    df = df[df["lvl_h2o"] > -1e10]
    df = df[df["lvl_h2o"] < 1e10]
    
    # Agregar columnas de año y mes
    df["Anio"] = df["Fecha"].dt.year
    df["Mes"] = df["Fecha"].dt.month
    
    # Agregar incertidumbre si está disponible
    if "wse_u" in df.columns:
        df["wse_incertidumbre"] = pd.to_numeric(df["wse_u"], errors="coerce")
    
    # Agregar ancho si está disponible
    if "width" in df.columns:
        df["ancho_m"] = pd.to_numeric(df["width"], errors="coerce")
    
    # Ordenar por fecha
    df = df.sort_values("Fecha").reset_index(drop=True)
    
    # Eliminar duplicados (mismo reach, misma fecha)
    df = df.drop_duplicates(subset=["Fecha", "lvl_h2o"])
    
    print(f"\nRegistros válidos: {len(df)}")
    print(f"Rango de fechas: {df['Fecha'].min()} a {df['Fecha'].max()}")
    print(f"WSE (m): min={df['lvl_h2o'].min():.2f}, max={df['lvl_h2o'].max():.2f}, "
          f"mean={df['lvl_h2o'].mean():.2f}")
    
    return df


def guardar_csv(df):
    """Guarda el DataFrame procesado como CSV."""
    # Seleccionar columnas para el CSV de salida
    cols_salida = ["Fecha", "lvl_h2o", "Anio", "Mes"]
    
    # Agregar columnas extra si existen
    for col in ["wse_incertidumbre", "ancho_m", "reach_id_usado"]:
        if col in df.columns:
            cols_salida.append(col)
    
    df_salida = df[cols_salida].copy()
    df_salida["Fecha"] = df_salida["Fecha"].dt.strftime("%Y-%m-%d")
    
    df_salida.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    print(f"\n✅ CSV guardado en: {OUTPUT_CSV}")
    print(f"   Filas: {len(df_salida)}")
    print(f"   Columnas: {list(df_salida.columns)}")
    
    # También guardar en la raíz del proyecto para compatibilidad
    output_raiz = os.path.join(PROJECT_DIR, "SWOT_lvl_h2o_2023_2025.csv")
    df_salida.to_csv(output_raiz, index=False, encoding="utf-8-sig")
    print(f"   (copia en: {output_raiz})")
    
    return df_salida


# ================================================================
# MAIN
# ================================================================
def main():
    print("=" * 60)
    print("DESCARGA DE DATOS SWOT - RÍO MAGDALENA (BARRANCABERMEJA)")
    print("Fuente: NASA SWOT via Hydrocron API")
    print("=" * 60)
    
    # Paso 1: Descargar datos de Hydrocron
    df_raw = descargar_todos_los_reaches()
    
    if df_raw is None or len(df_raw) == 0:
        print("\n❌ No se obtuvieron datos. Revisa los REACH_IDs.")
        sys.exit(1)
    
    print(f"\nDatos crudos descargados: {len(df_raw)} registros")
    print(f"Columnas: {list(df_raw.columns)}")
    print("\nPrimeras filas:")
    print(df_raw.head())
    
    # Paso 2: Procesar datos
    df_procesado = procesar_datos_swot(df_raw)
    
    if df_procesado is None or len(df_procesado) == 0:
        print("\n❌ No se pudieron procesar los datos.")
        sys.exit(1)
    
    # Paso 3: Guardar CSV
    df_final = guardar_csv(df_procesado)
    
    print("\n" + "=" * 60)
    print("✅ DESCARGA COMPLETADA")
    print("=" * 60)
    print(f"\nAhora ejecuta: python analisis_swot_barrancabermeja.py")
    
    return df_final


if __name__ == "__main__":
    df = main()