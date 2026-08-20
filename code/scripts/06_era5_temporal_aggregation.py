# -*- coding: utf-8 -*-
"""
Module: 06_era5_temporal_aggregation.py
Description: Ingests raw hourly ERA5 NetCDF files from data/raw/ and applies 
temporal downsampling. Generates two specific datasets in data/processed/:
  1. Monthly mean (1940-2025) for historical climatology.
  2. Daily mean (2014-2025) for short-term forcing dynamics.
"""

import xarray as xr
from pathlib import Path
import time

# --- DIRECTORY ARCHITECTURE ---
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RAW = REPO_ROOT / "data" / "raw"
DATA_PROC = REPO_ROOT / "data" / "processed"
DATA_PROC.mkdir(parents=True, exist_ok=True)

def process_aggregations():
    start_time = time.time()
    
    # Patrón de búsqueda para todos los archivos horarios crudos
    search_pattern = str(DATA_RAW / "ERA5_NAtlantic_Hourly_*.nc")
    
    print("--- 1. Ingesta Virtual de Datos (Dask Lazy Loading) ---")
    try:
        # parallel=True utiliza Dask para no saturar la RAM
        ds_hourly = xr.open_mfdataset(search_pattern, combine='by_coords', parallel=True)
    except Exception as e:
        print(f"Error crítico al cargar los datos crudos: {e}")
        return

    # -------------------------------------------------------------------------
    # PIPELINE 1: PROMEDIO MENSUAL (1940-2025)
    # -------------------------------------------------------------------------
    print("\n--- 2. Generando Promedio Mensual (1940-2025) ---")
    # Corte estricto para asegurar que termina en 2025
    ds_hist = ds_hourly.sel(time=slice('1940-01-01', '2025-12-31'))
    
    # Remuestreo a inicio de mes (1MS)
    ds_monthly = ds_hist.resample(time='1MS').mean(dim='time', keep_attrs=True)
    ds_monthly.attrs['processing_history'] = "Aggregated to monthly mean from hourly ERA5"
    
    out_monthly = DATA_PROC / "ERA5_NAtlantic_Monthly_1940-2025.nc"
    print(f"Exportando a disco: {out_monthly.name} ...")
    ds_monthly.to_netcdf(out_monthly)
    
    # -------------------------------------------------------------------------
    # PIPELINE 2: PROMEDIO DIARIO (2014-2025)
    # -------------------------------------------------------------------------
    print("\n--- 3. Generando Promedio Diario (2014-2025) ---")
    # Corte estricto para la ventana de dinámica a corto plazo
    ds_recent = ds_hourly.sel(time=slice('2014-01-01', '2025-12-31'))
    
    # Remuestreo a intervalo de 24 horas (1D)
    ds_daily = ds_recent.resample(time='1D').mean(dim='time', keep_attrs=True)
    ds_daily.attrs['processing_history'] = "Aggregated to daily mean from hourly ERA5"
    
    out_daily = DATA_PROC / "ERA5_NAtlantic_Daily_2014-2025.nc"
    print(f"Exportando a disco: {out_daily.name} ...")
    ds_daily.to_netcdf(out_daily)

    # Limpieza de memoria
    ds_hourly.close()
    ds_monthly.close()
    ds_daily.close()
    
    elapsed = (time.time() - start_time) / 60
    print(f"\n✅ Operación completada con éxito en {elapsed:.2f} minutos.")

if __name__ == "__main__":
    process_aggregations()