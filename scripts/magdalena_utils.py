#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
magdalena_utils.py
Funciones reutilizables para el análisis hidrológico, conectividad
ecohidrológica y procesamiento de datos del Río Magdalena.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def cargar_ideam(ruta_csv, sep=";", encoding="latin-1", columna_fecha="Fecha"):
    """
    Carga un CSV del IDEAM y parsea las fechas.

    Parametros:
        ruta_csv: str, ruta al archivo CSV
        sep: str, separador (; o ,)
        encoding: str, codificacion del archivo
        columna_fecha: str, nombre de la columna de fechas

    Retorna:
        DataFrame de pandas con la columna de fechas en formato datetime
    """
    df = pd.read_csv(
        ruta_csv,
        sep=sep,
        encoding=encoding,
        parse_dates=[columna_fecha],
        na_values=["", "NaN", "null", "-"]
    )
    return df


def limpiar_nivel(df, columna_nivel="Nivel_msnm", columna_calidad="Calidad"):
    """
    Limpia un DataFrame de niveles: elimina NaN, filtra calidad, ordena por fecha.

    Parametros:
        df: DataFrame con columnas de nivel y calidad
        columna_nivel: str, nombre de la columna de nivel
        columna_calidad: str, nombre de la columna de calidad

    Retorna:
        DataFrame limpio y ordenado
    """
    df_limpio = df.dropna(subset=[columna_nivel]).copy()
    df_limpio = df_limpio[df_limpio[columna_calidad] <= 2].copy()
    df_limpio = df_limpio.sort_values(df_limpio.columns[0]).reset_index(drop=True)
    return df_limpio


def filtrar_periodo(df, fecha_inicio, fecha_fin, columna_fecha="Fecha"):
    """
    Filtra un DataFrame por rango de fechas.

    Parametros:
        df: DataFrame con columna de fechas
        fecha_inicio: str, "YYYY-MM-DD"
        fecha_fin: str, "YYYY-MM-DD"
        columna_fecha: str, nombre de la columna de fechas

    Retorna:
        DataFrame filtrado
    """
    mascara = (df[columna_fecha] >= fecha_inicio) & (df[columna_fecha] <= fecha_fin)
    return df.loc[mascara].copy()


def calcular_conectividad(df, z_fondo, columna_nivel="Nivel_msnm"):
    """
    Clasifica cada registro como CONECTADO o DESCONECTADO segun el umbral Z_fondo.

    Parametros:
        df: DataFrame con columna de nivel
        z_fondo: float, cota del fondo del caño en msnm
        columna_nivel: str, nombre de la columna de nivel

    Retorna:
        DataFrame con columna nueva "Estado"
    """
    df = df.copy()
    df["Estado"] = np.where(df[columna_nivel] > z_fondo, "CONECTADO", "DESCONECTADO")
    return df


def resumen_anual(df, columna_estado="Estado", columna_nivel="Nivel_msnm", columna_anio="Año"):
    """
    Genera un resumen anual de dias conectados/desconectados.

    Parametros:
        df: DataFrame con columnas Estado, Nivel y Año

    Retorna:
        DataFrame de resumen
    """
    resumen = df.groupby(columna_anio).agg(
        dias_totales=(columna_estado, "size"),
        dias_desconectados=(columna_estado, lambda x: (x == "DESCONECTADO").sum()),
        nivel_minimo=(columna_nivel, "min"),
        nivel_promedio=(columna_nivel, "mean")
    ).reset_index()

    resumen["porcentaje_desconectado"] = (
        resumen["dias_desconectados"] / resumen["dias_totales"] * 100
    ).round(1)

    return resumen


def cm_a_metros(df, columna_valor="Valor"):
    """
    Transforma los datos de centimetros a metros y agrega la columna 'lvl_h2o'.

    Parametros:
        df: DataFrame con la columna de valores en cm
        columna_valor: str, nombre de la columna con valores en cm

    Retorna:
        DataFrame con la nueva columna 'lvl_h2o' en metros
    """
    df = df.copy()
    df["lvl_h2o"] = df[columna_valor] / 100.0
    return df


def plot_nivel_diario(df, columna_fecha="Fecha", columna_nivel="lvl_h2o",
                      titulo="Nivel del agua diario - Barrancabermeja",
                      guardar_en=None):
    """
    Genera una grafica de la variacion del nivel del agua por dia.

    Parametros:
        df: DataFrame con columnas de fecha y nivel
        columna_fecha: str, nombre de la columna de fechas
        columna_nivel: str, nombre de la columna de nivel en metros
        titulo: str, titulo de la grafica
        guardar_en: str o None, ruta para guardar la imagen

    Retorna:
        fig, ax: objetos de matplotlib
    """
    fig, ax = plt.subplots(figsize=(16, 5))

    ax.plot(df[columna_fecha], df[columna_nivel],
            linewidth=0.8, color="#1a73e8", alpha=0.85)
    ax.fill_between(df[columna_fecha], df[columna_nivel],
                    alpha=0.15, color="#1a73e8")

    ax.set_xlabel("Fecha", fontsize=12)
    ax.set_ylabel("Nivel del agua (m)", fontsize=12)
    ax.set_title(titulo, fontsize=14, fontweight="bold")
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.grid(True, linestyle="--", alpha=0.4)
    fig.autofmt_xdate()
    fig.tight_layout()

    if guardar_en:
        fig.savefig(guardar_en, dpi=150, bbox_inches="tight")
        print(f"Grafica guardada en: {guardar_en}")

    return fig, ax


def plot_nivel_mensual(df, columna_fecha="Fecha", columna_nivel="lvl_h2o",
                       titulo="Nivel medio mensual del agua - Barrancabermeja",
                       guardar_en=None):
    """
    Genera una grafica de la variacion del nivel del agua promedio por mes.

    Parametros:
        df: DataFrame con columnas de fecha y nivel
        columna_fecha: str, nombre de la columna de fechas
        columna_nivel: str, nombre de la columna de nivel en metros
        titulo: str, titulo de la grafica
        guardar_en: str o None, ruta para guardar la imagen

    Retorna:
        fig, ax: objetos de matplotlib
    """
    # Agrupar por año y mes
    df_temp = df.copy()
    df_temp["Anio"] = df_temp[columna_fecha].dt.year
    df_temp["Mes"] = df_temp[columna_fecha].dt.month
    df_temp["Periodo"] = df_temp[columna_fecha].dt.to_period("M").dt.to_timestamp()

    mensual = df_temp.groupby("Periodo")[columna_nivel].agg(
        ["mean", "min", "max"]
    ).reset_index()

    fig, ax = plt.subplots(figsize=(16, 5))

    ax.plot(mensual["Periodo"], mensual["mean"],
            linewidth=1.5, color="#0d47a1", marker="o", markersize=3,
            label="Promedio mensual")
    ax.fill_between(mensual["Periodo"], mensual["min"], mensual["max"],
                    alpha=0.2, color="#42a5f5", label="Rango (min-max)")

    ax.set_xlabel("Fecha", fontsize=12)
    ax.set_ylabel("Nivel del agua (m)", fontsize=12)
    ax.set_title(titulo, fontsize=14, fontweight="bold")
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.legend(loc="upper right")
    ax.grid(True, linestyle="--", alpha=0.4)
    fig.autofmt_xdate()
    fig.tight_layout()

    if guardar_en:
        fig.savefig(guardar_en, dpi=150, bbox_inches="tight")
        print(f"Grafica guardada en: {guardar_en}")

    return fig, ax
