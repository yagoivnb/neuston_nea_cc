# -*- coding: utf-8 -*-
"""
# @file:    07_wind_short_term_analysis.py
# @author:  Yago Iván-Baragaño (ivanyago@uniovi.es)
# @funding: Severo Ochoa Ph.D. program (Principado de Asturias, NAC-AT-PUB-ASV-2025 BP24-109)
# @cite:    
# @brief:   Spatiotemporal analysis of atmospheric forcing
Exports clean datasets for visualisation pipeline
"""

import xarray as xr
import pandas as pd
import numpy as np
from scipy import stats
from pathlib import Path
import warnings

warnings.filterwarnings("ignore")

# --- DIRECTORY ARCHITECTURE ---
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PROC = REPO_ROOT / "data" / "processed"

print("--- 1. Loading Daily Consolidated Dataset ---")
ds = xr.open_dataset(DATA_PROC / "ERA5_NAtlantic_Daily_2014-2025.nc")

u_var = 'u10' if 'u10' in ds.variables else '10m_u_component_of_wind'
v_var = 'v10' if 'v10' in ds.variables else '10m_v_component_of_wind'

# =============================================================================
# PART 1: SPATIAL AGGREGATION FOR MOSAICS (EXPORT TO NETCDF)
# =============================================================================
print("\n--- 2. Calculating Spatial Means for Mosaics (3 Seasons x 3 Phases) ---")
ds_mam = ds.sel(time=ds.time.dt.month.isin([3, 4, 5]))
ds_jun = ds.sel(time=ds.time.dt.month == 6)
ds_jaso = ds.sel(time=ds.time.dt.month.isin([7, 8, 9, 10]))

def calc_phases(d_sub):
    p1 = d_sub.sel(time=slice('2014', '2018')).mean('time').compute()
    p2 = d_sub.sel(time=slice('2019', '2022')).mean('time').compute()
    p3 = d_sub.sel(time=slice('2023', '2025')).mean('time').compute()
    return p1, p2, p3

p1_m, p2_m, p3_m = calc_phases(ds_mam)
p1_j, p2_j, p3_j = calc_phases(ds_jun)
p1_s, p2_s, p3_s = calc_phases(ds_jaso)

ds_spatial = xr.Dataset({
    'u_MAM_P1': p1_m[u_var], 'v_MAM_P1': p1_m[v_var],
    'u_MAM_P2': p2_m[u_var], 'v_MAM_P2': p2_m[v_var],
    'u_MAM_P3': p3_m[u_var], 'v_MAM_P3': p3_m[v_var],
    'u_JUN_P1': p1_j[u_var], 'v_JUN_P1': p1_j[v_var],
    'u_JUN_P2': p2_j[u_var], 'v_JUN_P2': p2_j[v_var],
    'u_JUN_P3': p3_j[u_var], 'v_JUN_P3': p3_j[v_var],
    'u_JASO_P1': p1_s[u_var], 'v_JASO_P1': p1_s[v_var],
    'u_JASO_P2': p2_s[u_var], 'v_JASO_P2': p2_s[v_var],
    'u_JASO_P3': p3_s[u_var], 'v_JASO_P3': p3_s[v_var],
})

spatial_out = DATA_PROC / "ERA5_Spatial_Means_Phases.nc"
ds_spatial.to_netcdf(spatial_out)
print(f"Spatial phases successfully serialized to: {spatial_out.name}")

# =============================================================================
# PART 2: REGIONAL 10-DAY AGGREGATION & DATABASE CREATION
# =============================================================================
print("\n--- 3. Extracting Regional Time-Series & 10-Day Downsampling ---")
ds_sorted = ds.sortby('latitude').sortby('longitude')

cajas = {
    'MAM':   {'lon': slice(-50, -25), 'lat': slice(35, 45)},
    'JUN':   {'lon': slice(-25, -10), 'lat': slice(43.2, 55)},
    'JASO':  {'lon': slice(-10, -1), 'lat': slice(43.2, 48.5)}
}

ts = {}
for fase, lims in cajas.items():
    ts[f'u_{fase}'] = ds_sorted[u_var].sel(longitude=lims['lon'], latitude=lims['lat']).mean(dim=['latitude', 'longitude']).compute()
    ts[f'v_{fase}'] = ds_sorted[v_var].sel(longitude=lims['lon'], latitude=lims['lat']).mean(dim=['latitude', 'longitude']).compute()

def calc_angle(u, v): 
    return (90 - np.degrees(np.arctan2(v, u))) % 360

def circmean_safe(x): 
    return np.nan if len(x.dropna()) == 0 else stats.circmean(x.dropna(), high=360, low=0)

df_diario = pd.DataFrame({'Fecha': ds_sorted.time.values, 'Año': ds_sorted.time.dt.year.values, 'Mes': ds_sorted.time.dt.month.values})
for f in cajas:
    df_diario[f'U10_{f}_B'] = ts[f'u_{f}'].values
    df_diario[f'Ang_{f}_B'] = calc_angle(ts[f'u_{f}'], ts[f'v_{f}']).values

df_diario['Arribazón'] = np.select(
    [(df_diario['Año'] <= 2018), (df_diario['Año'] >= 2019) & (df_diario['Año'] <= 2022), (df_diario['Año'] >= 2023)], 
    [0, 1, 2], default=np.nan
)

mask_map = {'MAM': [3, 4, 5], 'JUN': [6], 'JASO': [7, 8, 9, 10]}
for f, meses in mask_map.items():
    df_diario[f'U10_{f}'] = np.where(df_diario['Mes'].isin(meses), df_diario[f'U10_{f}_B'], np.nan)
    df_diario[f'Ang_{f}'] = np.where(df_diario['Mes'].isin(meses), df_diario[f'Ang_{f}_B'], np.nan)

df_10d = df_diario.set_index('Fecha').resample('10D').agg({
    **{f'U10_{f}': 'mean' for f in cajas}, 
    **{f'Ang_{f}': circmean_safe for f in cajas}, 
    'Arribazón': lambda x: x.mode()[0] if not x.mode().empty else np.nan
}).reset_index()

# Exportación en formato Parquet (el equivalente directo y optimizado del .rds en Python)
db_out = DATA_PROC / "Wind_Phenology_10D.parquet"
df_10d.to_parquet(db_out, index=False)
print(f"10-Day database successfully exported to: {db_out.name}")

print("\n✅ Script 07 completed. Analytical backend is ready for visualization.")