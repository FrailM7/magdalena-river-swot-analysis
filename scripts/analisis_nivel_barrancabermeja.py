#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analisis_nivel_barrancabermeja.py
Análisis del nivel del agua - Estación BARRANCABERMEJA [23157030]

Este script:
  1. Lee el CSV separado por comas desde data/raw/
  2. Parsea la columna 'Fecha' con pd.to_datetime()
  3. Convierte los valores de cm a m y crea la columna 'lvl_h2o'
  4. Genera gráfica de variación diaria del nivel del agua (con El Niño sombreado)
  5. Genera gráfica de variación mensual del nivel del agua (con El Niño sombreado)
  6. Genera TABLA DE PROMEDIOS MENSUALES POR AÑO (pivote meses x años)
     y la exporta a Excel y CSV en data/processed/
"""

import os
import sys
import pandas as pd
import matplotlib.pyplot as plt

# ---------- Ajuste de rutas ----------
# Carpeta raíz del proyecto (un nivel arriba de scripts/)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)

# Agregar scripts/ al path para importar magdalena_utils
sys.path.insert(0, SCRIPT_DIR)
from magdalena_utils import cm_a_metros, plot_nivel_diario, plot_nivel_mensual

# ---------- Rutas de archivos ----------
RUTA_CSV = os.path.join(PROJECT_DIR, "data", "raw", "descargaDhime.csv")
RUTA_FIGURAS = os.path.join(PROJECT_DIR, "data", "processed")

# Crear carpeta de salida si no existe
os.makedirs(RUTA_FIGURAS, exist_ok=True)


# ================================================================
# EPISODIOS DE EL NIÑO (fuente: NOAA CPC, eventos ONI >= +0.5 °C)
# Formato: (fecha_inicio, fecha_fin)
# Puedes agregar o quitar episodios según el rango de tus datos.
# ================================================================
EPISODIOS_NINO = [
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


def sombrear_episodios_nino(ax, fecha_min, fecha_max):
    """
    Sombrea en el eje 'ax' los episodios de El Niño que se solapen
    con el rango de datos [fecha_min, fecha_max].

    Parámetros
    ----------
    ax : matplotlib.axes.Axes
        Eje de la gráfica (el eje x debe estar en fechas).
    fecha_min, fecha_max : pd.Timestamp
        Rango temporal de los datos graficados.
    """
    etiqueta_agregada = False
    for inicio, fin in EPISODIOS_NINO:
        ini = pd.Timestamp(inicio)
        # El fin del episodio se extiende hasta el final de ese mes
        fin_ts = pd.Timestamp(fin) + pd.offsets.MonthEnd(0)

        # Solo sombrear si el episodio se solapa con los datos
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


def tabla_promedios_mensuales_por_anio(data):
    """
    Genera la tabla de promedios MENSUALES para CADA AÑO:
    una tabla pivote con los meses como filas y los años como columnas.

    Retorna el DataFrame pivote (valores en metros, lvl_h2o).
    """
    meses_nombre = {1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
                    7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"}

    # Promedio de la lámina de agua agrupando por año Y mes
    prom = data.groupby(["Anio", "Mes"])["lvl_h2o"].mean().round(4)

    # Pivote: filas = meses, columnas = años
    tabla = prom.unstack(level="Anio")
    tabla.index = tabla.index.map(meses_nombre)
    tabla.index.name = "Mes"

    # Columna adicional con el promedio multianual de cada mes
    tabla["Promedio_multianual"] = tabla.mean(axis=1).round(4)

    return tabla


def main():
    # ================================================================
    # 1. LECTURA DEL ARCHIVO CSV (separado por comas)
    # ================================================================
    print("=" * 60)
    print("Cargando datos desde:", RUTA_CSV)
    print("=" * 60)

    data = pd.read_csv(
        RUTA_CSV,
        sep=",",
        encoding="utf-8",
        na_values=["", "NaN", "null", "-"]
    )

    print(f"\nFilas cargadas: {len(data)}")
    print(f"Columnas: {list(data.columns)}")
    print("\nPrimeras filas (original):")
    print(data.head())

    # ================================================================
    # 2. PARSEO DE FECHAS con pd.to_datetime()
    # ================================================================
    # El formato en el CSV es 'YYYY-MM-DD HH:MM'
    # (en Excel se visualiza como d/mm/yyyy h:mm)
    data["Fecha"] = pd.to_datetime(data["Fecha"], format="%Y-%m-%d %H:%M")

    # Agregar columnas de año y mes para agrupaciones posteriores
    data["Anio"] = data["Fecha"].dt.year
    data["Mes"] = data["Fecha"].dt.month

    print("\n--- Fechas parseadas correctamente ---")
    print(f"Rango de fechas: {data['Fecha'].min()} a {data['Fecha'].max()}")
    print(f"Años disponibles: {sorted(data['Anio'].unique())}")

    # ================================================================
    # 3. CONVERSIÓN DE cm A m -> columna 'lvl_h2o'
    # ================================================================
    data = cm_a_metros(data, columna_valor="Valor")

    print("\n--- Conversión cm -> m completada ---")
    print(f"Valor original (cm): min={data['Valor'].min():.2f}, max={data['Valor'].max():.2f}")
    print(f"lvl_h2o (m):         min={data['lvl_h2o'].min():.4f}, max={data['lvl_h2o'].max():.4f}")
    print("\nPrimeras filas con 'lvl_h2o':")
    print(data[["Fecha", "Valor", "lvl_h2o", "Anio", "Mes"]].head(10))

    fecha_min = data["Fecha"].min()
    fecha_max = data["Fecha"].max()

    # ================================================================
    # 4. GRÁFICA DE VARIACIÓN DIARIA DEL NIVEL DEL AGUA
    #    (con episodios de El Niño sombreados)
    # ================================================================
    print("\n" + "=" * 60)
    print("Generando gráfica de nivel diario...")
    print("=" * 60)

    fig_diario, ax_diario = plot_nivel_diario(
        data,
        columna_fecha="Fecha",
        columna_nivel="lvl_h2o",
        titulo="Variación diaria del nivel del agua\nEstación Barrancabermeja [23157030]",
        guardar_en=os.path.join(RUTA_FIGURAS, "nivel_diario_barrancabermeja.png")
    )

    # Sombrear episodios de El Niño y volver a guardar la figura
    sombrear_episodios_nino(ax_diario, fecha_min, fecha_max)
    fig_diario.savefig(
        os.path.join(RUTA_FIGURAS, "nivel_diario_barrancabermeja.png"),
        dpi=300, bbox_inches="tight"
    )

    # ================================================================
    # 5. GRÁFICA DE VARIACIÓN MENSUAL DEL NIVEL DEL AGUA
    #    (con episodios de El Niño sombreados)
    # ================================================================
    print("\nGenerando gráfica de nivel mensual...")

    fig_mensual, ax_mensual = plot_nivel_mensual(
        data,
        columna_fecha="Fecha",
        columna_nivel="lvl_h2o",
        titulo="Nivel medio mensual del agua\nEstación Barrancabermeja [23157030]",
        guardar_en=os.path.join(RUTA_FIGURAS, "nivel_mensual_barrancabermeja.png")
    )

    # NOTA: el sombreado usa fechas en el eje x. Si en tu función
    # plot_nivel_mensual el eje x es categórico (nombres de meses
    # agregados de todos los años), el sombreado por episodios no
    # aplica allí y se omitirá con un aviso.
    try:
        sombrear_episodios_nino(ax_mensual, fecha_min, fecha_max)
        fig_mensual.savefig(
            os.path.join(RUTA_FIGURAS, "nivel_mensual_barrancabermeja.png"),
            dpi=300, bbox_inches="tight"
        )
    except Exception as e:
        print(f"[AVISO] No se pudo sombrear El Niño en la gráfica mensual: {e}")

    # ================================================================
    # 6. RESUMEN POR AÑO
    # ================================================================
    print("\n" + "=" * 60)
    print("Resumen del nivel del agua por año:")
    print("=" * 60)

    resumen_anual = data.groupby("Anio")["lvl_h2o"].agg(
        ["count", "mean", "min", "max", "std"]
    ).round(4)
    resumen_anual.columns = ["Registros", "Promedio_m", "Min_m", "Max_m", "Desv_m"]
    print(resumen_anual)

    # ================================================================
    # 7. TABLA DE PROMEDIOS MENSUALES POR AÑO (lámina de agua, m)
    #    Filas = meses, Columnas = años
    # ================================================================
    print("\n" + "=" * 60)
    print("Tabla de promedios mensuales de lámina de agua (m) por año:")
    print("=" * 60)

    tabla_mensual_anual = tabla_promedios_mensuales_por_anio(data)
    print(tabla_mensual_anual)

    # ---- Exportar la tabla a CSV y Excel ----
    ruta_tabla_csv = os.path.join(RUTA_FIGURAS, "promedios_mensuales_por_anio.csv")
    ruta_tabla_xlsx = os.path.join(RUTA_FIGURAS, "promedios_mensuales_por_anio.xlsx")

    tabla_mensual_anual.to_csv(ruta_tabla_csv, encoding="utf-8-sig")
    tabla_mensual_anual.to_excel(ruta_tabla_xlsx)

    print(f"\n[OK] Tabla exportada a: {ruta_tabla_csv}")
    print(f"[OK] Tabla exportada a: {ruta_tabla_xlsx}")

    # ---- También imprimir una tabla individual por cada año ----
    print("\n" + "=" * 60)
    print("Detalle año por año (promedio mensual de lámina de agua, m):")
    print("=" * 60)

    meses_nombre = {1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
                    7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"}
    for anio in sorted(data["Anio"].unique()):
        sub = data[data["Anio"] == anio]
        prom_anio = sub.groupby("Mes")["lvl_h2o"].mean().round(4)
        prom_anio.index = prom_anio.index.map(meses_nombre)
        print(f"\n--- Año {anio} ---")
        print(prom_anio.to_frame("Promedio_m"))

    # Mostrar las gráficas
    plt.show()

    print("\n[OK] Analisis completado exitosamente.")
    return data


if __name__ == "__main__":
    df_resultado = main()
    print("\nPrimeras filas del DataFrame resultante:")
    print(df_resultado.head())
