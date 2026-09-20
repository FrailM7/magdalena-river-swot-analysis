#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analisis_swot_barrancabermeja.py
Análisis del nivel del agua SWOT - Río Magdalena cerca de Barrancabermeja

Este script:
  1. Lee el CSV generado por 'Descarga SWOT.py'
  2. Genera gráfica de variación del WSE (Water Surface Elevation)
     con episodios de El Niño sombreados
  3. Genera gráfica de variación mensual del WSE con El Niño sombreado
  4. Genera tabla de promedios mensuales por año
  5. (Opcional) Genera gráfica comparativa IDEAM vs SWOT
  6. Exporta resultados a CSV y Excel
"""

import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

# Fix encoding para Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# ---------- Ajuste de rutas ----------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)

# Agregar scripts/ al path
sys.path.insert(0, SCRIPT_DIR)

# ---------- Rutas de archivos ----------
RUTA_SWOT_CSV = os.path.join(PROJECT_DIR, "data", "raw", "SWOT_lvl_h2o_barrancabermeja.csv")
RUTA_IDEAM_CSV = os.path.join(PROJECT_DIR, "data", "raw", "descargaDhime.csv")
RUTA_FIGURAS = os.path.join(PROJECT_DIR, "data", "processed")

# Crear carpeta de salida si no existe
os.makedirs(RUTA_FIGURAS, exist_ok=True)


# ================================================================
# EPISODIOS DE EL NIÑO (fuente: NOAA CPC, eventos ONI >= +0.5 °C)
# ================================================================
EPISODIOS_NINO = [
    ("2023-05", "2024-04"),  # Último episodio, coincide con SWOT
]

# Lista completa para referencia (solo el relevante para SWOT)
EPISODIOS_NINO_COMPLETOS = [
    ("1951-07", "1952-01"),
    ("1953-03", "1953-11"),
    ("1957-04", "1958-06"),
    ("1963-06", "1964-01"),
    ("1965-05", "1966-03"),
    ("1968-08", "1970-01"),
    ("1972-05", "1973-03"),
    ("1976-09", "1977-02"),
    ("1977-08", "1978-01"),
    ("1979-09", "1980-02"),
    ("1982-04", "1983-06"),
    ("1986-09", "1988-01"),
    ("1991-05", "1992-06"),
    ("1994-08", "1995-03"),
    ("1997-04", "1998-05"),
    ("2002-05", "2003-03"),
    ("2004-07", "2005-02"),
    ("2006-09", "2007-01"),
    ("2009-07", "2010-04"),
    ("2014-10", "2016-04"),
    ("2018-09", "2019-06"),
    ("2023-05", "2024-04"),
]


def sombrear_episodios_nino(ax, fecha_min, fecha_max, episodios=None):
    """
    Sombrea en el eje 'ax' los episodios de El Niño que se solapen
    con el rango de datos [fecha_min, fecha_max].
    """
    if episodios is None:
        episodios = EPISODIOS_NINO

    etiqueta_agregada = False
    for inicio, fin in episodios:
        ini = pd.Timestamp(inicio)
        fin_ts = pd.Timestamp(fin) + pd.offsets.MonthEnd(0)

        if fin_ts < fecha_min or ini > fecha_max:
            continue

        ini_clip = max(ini, fecha_min)
        fin_clip = min(fin_ts, fecha_max)

        ax.axvspan(
            ini_clip, fin_clip,
            color="red", alpha=0.18, zorder=0,
            label="Fenómeno de El Niño" if not etiqueta_agregada else None
        )
        etiqueta_agregada = True

    if etiqueta_agregada:
        ax.legend(loc="best", fontsize=9)


def plot_swot_diario(data, guardar_en=None):
    """
    Genera gráfica de la variación del WSE (Water Surface Elevation)
    medido por SWOT, con episodios de El Niño sombreados.
    """
    fig, ax = plt.subplots(figsize=(16, 6))

    # Gráfica principal
    ax.scatter(data["Fecha"], data["lvl_h2o"],
               s=15, color="#1a73e8", alpha=0.7, zorder=3,
               label="WSE SWOT")
    ax.plot(data["Fecha"], data["lvl_h2o"],
            linewidth=0.8, color="#1a73e8", alpha=0.4, zorder=2)

    # Sombrear incertidumbre si está disponible
    if "wse_incertidumbre" in data.columns:
        wse_u = data["wse_incertidumbre"].fillna(0)
        ax.fill_between(data["Fecha"],
                        data["lvl_h2o"] - wse_u,
                        data["lvl_h2o"] + wse_u,
                        alpha=0.1, color="#1a73e8",
                        label="Incertidumbre WSE")

    # Sombrear El Niño
    fecha_min = data["Fecha"].min()
    fecha_max = data["Fecha"].max()
    sombrear_episodios_nino(ax, fecha_min, fecha_max)

    ax.set_xlabel("Fecha", fontsize=12)
    ax.set_ylabel("Elevación de la superficie del agua - WSE (m)", fontsize=12)
    ax.set_title("Variación del nivel del agua (SWOT)\n"
                 "Río Magdalena - Zona Barrancabermeja",
                 fontsize=14, fontweight="bold")
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.grid(True, linestyle="--", alpha=0.4)
    ax.legend(loc="best", fontsize=9)
    fig.autofmt_xdate()
    fig.tight_layout()

    if guardar_en:
        fig.savefig(guardar_en, dpi=300, bbox_inches="tight")
        print(f"Gráfica guardada en: {guardar_en}")

    return fig, ax


def plot_swot_mensual(data, guardar_en=None):
    """
    Genera gráfica de la variación mensual del WSE.
    """
    # Agrupar por período mensual
    data_temp = data.copy()
    data_temp["Periodo"] = data_temp["Fecha"].dt.to_period("M").dt.to_timestamp()

    mensual = data_temp.groupby("Periodo")["lvl_h2o"].agg(
        ["mean", "min", "max", "count", "std"]
    ).reset_index()

    fig, ax = plt.subplots(figsize=(16, 6))

    ax.plot(mensual["Periodo"], mensual["mean"],
            linewidth=2, color="#0d47a1", marker="o", markersize=6,
            label="Promedio mensual WSE", zorder=3)
    ax.fill_between(mensual["Periodo"], mensual["min"], mensual["max"],
                    alpha=0.2, color="#42a5f5", label="Rango (min-max)")

    # Anotar número de observaciones por mes
    for _, row in mensual.iterrows():
        ax.annotate(f"n={int(row['count'])}",
                    (row["Periodo"], row["max"]),
                    textcoords="offset points", xytext=(0, 8),
                    fontsize=7, ha="center", color="gray")

    # Sombrear El Niño
    fecha_min = mensual["Periodo"].min()
    fecha_max = mensual["Periodo"].max()
    sombrear_episodios_nino(ax, fecha_min, fecha_max)

    ax.set_xlabel("Fecha", fontsize=12)
    ax.set_ylabel("Elevación de la superficie del agua - WSE (m)", fontsize=12)
    ax.set_title("Nivel medio mensual del agua (SWOT)\n"
                 "Río Magdalena - Zona Barrancabermeja",
                 fontsize=14, fontweight="bold")
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.legend(loc="best", fontsize=9)
    ax.grid(True, linestyle="--", alpha=0.4)
    fig.autofmt_xdate()
    fig.tight_layout()

    if guardar_en:
        fig.savefig(guardar_en, dpi=300, bbox_inches="tight")
        print(f"Gráfica guardada en: {guardar_en}")

    return fig, ax


def plot_comparativa_ideam_swot(data_swot, guardar_en=None):
    """
    Genera gráfica comparativa del nivel del agua IDEAM vs SWOT.
    Ambas series se normalizan para poder compararlas visualmente
    (IDEAM en metros relativos, SWOT en metros sobre el geoide).
    """
    # Intentar cargar datos IDEAM
    if not os.path.exists(RUTA_IDEAM_CSV):
        print("⚠️ No se encontró el CSV del IDEAM. Saltando gráfica comparativa.")
        return None, None

    print("\n--- Cargando datos IDEAM para comparación ---")
    df_ideam = pd.read_csv(RUTA_IDEAM_CSV, encoding="utf-8",
                           na_values=["", "NaN", "null", "-"])
    df_ideam["Fecha"] = pd.to_datetime(df_ideam["Fecha"], format="%Y-%m-%d %H:%M")
    df_ideam["lvl_h2o_ideam"] = df_ideam["Valor"] / 100.0  # cm a metros

    # Filtrar IDEAM al período SWOT
    fecha_min_swot = data_swot["Fecha"].min()
    fecha_max_swot = data_swot["Fecha"].max()
    mascara = (df_ideam["Fecha"] >= fecha_min_swot) & (df_ideam["Fecha"] <= fecha_max_swot)
    df_ideam_filtrado = df_ideam.loc[mascara].copy()

    if len(df_ideam_filtrado) == 0:
        print("⚠️ No hay datos IDEAM en el período SWOT.")
        return None, None

    # --- Gráfica con doble eje Y ---
    fig, ax1 = plt.subplots(figsize=(16, 7))

    # Eje izquierdo: IDEAM
    color_ideam = "#1a73e8"
    ax1.plot(df_ideam_filtrado["Fecha"], df_ideam_filtrado["lvl_h2o_ideam"],
             linewidth=0.8, color=color_ideam, alpha=0.7,
             label="IDEAM - Nivel (m, relativo)")
    ax1.set_xlabel("Fecha", fontsize=12)
    ax1.set_ylabel("Nivel del agua IDEAM (m, relativo)", fontsize=12, color=color_ideam)
    ax1.tick_params(axis="y", labelcolor=color_ideam)

    # Eje derecho: SWOT
    ax2 = ax1.twinx()
    color_swot = "#e65100"
    ax2.scatter(data_swot["Fecha"], data_swot["lvl_h2o"],
                s=25, color=color_swot, alpha=0.8, zorder=5,
                label="SWOT - WSE (m, geoide)")
    ax2.plot(data_swot["Fecha"], data_swot["lvl_h2o"],
             linewidth=1, color=color_swot, alpha=0.4, zorder=4)
    ax2.set_ylabel("WSE SWOT (m sobre geoide WGS84)", fontsize=12, color=color_swot)
    ax2.tick_params(axis="y", labelcolor=color_swot)

    # Sombrear El Niño
    sombrear_episodios_nino(ax1, fecha_min_swot, fecha_max_swot)

    # Título
    ax1.set_title("Comparación del nivel del agua: IDEAM vs SWOT\n"
                  "Río Magdalena - Barrancabermeja [23157030]",
                  fontsize=14, fontweight="bold")

    # Leyenda combinada
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", fontsize=9)

    ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax1.grid(True, linestyle="--", alpha=0.3)
    fig.autofmt_xdate()
    fig.tight_layout()

    if guardar_en:
        fig.savefig(guardar_en, dpi=300, bbox_inches="tight")
        print(f"Gráfica comparativa guardada en: {guardar_en}")

    return fig, (ax1, ax2)


def tabla_promedios_mensuales_por_anio(data):
    """
    Genera tabla de promedios mensuales para cada año.
    """
    meses_nombre = {1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
                    7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"}

    prom = data.groupby(["Anio", "Mes"])["lvl_h2o"].mean().round(4)
    tabla = prom.unstack(level="Anio")
    tabla.index = tabla.index.map(meses_nombre)
    tabla.index.name = "Mes"
    tabla["Promedio_multianual"] = tabla.mean(axis=1).round(4)

    return tabla


def main():
    # ================================================================
    # 1. LECTURA DEL CSV SWOT
    # ================================================================
    print("=" * 60)
    print("ANÁLISIS DE DATOS SWOT - BARRANCABERMEJA")
    print("=" * 60)

    if not os.path.exists(RUTA_SWOT_CSV):
        print(f"\n❌ No se encontró el archivo: {RUTA_SWOT_CSV}")
        print("   Ejecuta primero: python \"Descarga SWOT.py\"")
        sys.exit(1)

    print(f"\nCargando datos desde: {RUTA_SWOT_CSV}")
    data = pd.read_csv(RUTA_SWOT_CSV, encoding="utf-8-sig",
                       na_values=["", "NaN", "null", "-"])

    print(f"Filas cargadas: {len(data)}")
    print(f"Columnas: {list(data.columns)}")

    # Parsear fechas
    data["Fecha"] = pd.to_datetime(data["Fecha"])
    data["Anio"] = data["Fecha"].dt.year
    data["Mes"] = data["Fecha"].dt.month

    # Eliminar valores NaN en lvl_h2o
    data = data.dropna(subset=["lvl_h2o"])

    print(f"\nRegistros válidos: {len(data)}")
    print(f"Rango de fechas: {data['Fecha'].min()} a {data['Fecha'].max()}")
    print(f"WSE (m): min={data['lvl_h2o'].min():.2f}, max={data['lvl_h2o'].max():.2f}, "
          f"mean={data['lvl_h2o'].mean():.2f}")
    print("\nPrimeras filas:")
    print(data.head(10))

    # ================================================================
    # 2. GRÁFICA DIARIA (SCATTER) DEL WSE
    # ================================================================
    print("\n" + "=" * 60)
    print("Generando gráfica de WSE SWOT...")
    print("=" * 60)

    plot_swot_diario(
        data,
        guardar_en=os.path.join(RUTA_FIGURAS, "swot_wse_diario_barrancabermeja.png")
    )

    # ================================================================
    # 3. GRÁFICA MENSUAL DEL WSE
    # ================================================================
    print("\nGenerando gráfica mensual de WSE SWOT...")

    plot_swot_mensual(
        data,
        guardar_en=os.path.join(RUTA_FIGURAS, "swot_wse_mensual_barrancabermeja.png")
    )

    # ================================================================
    # 4. GRÁFICA COMPARATIVA IDEAM vs SWOT
    # ================================================================
    print("\n" + "=" * 60)
    print("Generando gráfica comparativa IDEAM vs SWOT...")
    print("=" * 60)

    plot_comparativa_ideam_swot(
        data,
        guardar_en=os.path.join(RUTA_FIGURAS, "comparativa_ideam_vs_swot_barrancabermeja.png")
    )

    # ================================================================
    # 5. RESUMEN POR AÑO
    # ================================================================
    print("\n" + "=" * 60)
    print("Resumen del WSE SWOT por año:")
    print("=" * 60)

    resumen_anual = data.groupby("Anio")["lvl_h2o"].agg(
        ["count", "mean", "min", "max", "std"]
    ).round(4)
    resumen_anual.columns = ["Registros", "Promedio_m", "Min_m", "Max_m", "Desv_m"]
    print(resumen_anual)

    # ================================================================
    # 6. TABLA DE PROMEDIOS MENSUALES POR AÑO
    # ================================================================
    print("\n" + "=" * 60)
    print("Tabla de promedios mensuales WSE SWOT (m) por año:")
    print("=" * 60)

    tabla = tabla_promedios_mensuales_por_anio(data)
    print(tabla)

    # Exportar
    ruta_csv = os.path.join(RUTA_FIGURAS, "swot_promedios_mensuales_por_anio.csv")
    ruta_xlsx = os.path.join(RUTA_FIGURAS, "swot_promedios_mensuales_por_anio.xlsx")

    tabla.to_csv(ruta_csv, encoding="utf-8-sig")
    try:
        tabla.to_excel(ruta_xlsx)
        print(f"\n[OK] Tabla exportada a: {ruta_xlsx}")
    except Exception as e:
        print(f"\n[AVISO] No se pudo exportar a Excel: {e}")

    print(f"[OK] Tabla exportada a: {ruta_csv}")

    # ================================================================
    # 7. DETALLE AÑO POR AÑO
    # ================================================================
    print("\n" + "=" * 60)
    print("Detalle año por año (promedio mensual WSE SWOT, m):")
    print("=" * 60)

    meses_nombre = {1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
                    7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"}
    for anio in sorted(data["Anio"].unique()):
        sub = data[data["Anio"] == anio]
        prom_anio = sub.groupby("Mes")["lvl_h2o"].agg(["mean", "count"]).round(4)
        prom_anio.index = prom_anio.index.map(meses_nombre)
        prom_anio.columns = ["Promedio_WSE_m", "N_observaciones"]
        print(f"\n--- Año {anio} ---")
        print(prom_anio)

    # Mostrar gráficas
    plt.show()

    print("\n[OK] Análisis SWOT completado exitosamente.")
    return data


if __name__ == "__main__":
    df_resultado = main()
