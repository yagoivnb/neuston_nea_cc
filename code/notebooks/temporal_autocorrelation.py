# -*- coding: utf-8 -*-
"""
Module: temporal_autocorrelation.py
Description: Evaluates synoptic wind persistence (memory) to determine 
the optimal temporal binning threshold for phenological studies.
"""

import xarray as xr
import matplotlib.pyplot as plt
from statsmodels.tsa.stattools import acf
from pathlib import Path
import warnings

warnings.filterwarnings("ignore")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PROC = REPO_ROOT / "data" / "processed"
FIG_EXP = REPO_ROOT / "figures" / "exploratory"
FIG_EXP.mkdir(parents=True, exist_ok=True)

ds = xr.open_dataset(DATA_PROC / "ERA5_NAtlantic_Daily_2014-2025.nc")
u_var = 'u10' if 'u10' in ds.variables else '10m_u_component_of_wind'

ds_basin = ds[u_var].sel(longitude=slice(-50, -5), latitude=slice(65, 25)).mean(dim=['latitude', 'longitude']).compute()
u_series = ds_basin.to_dataframe().dropna()[u_var]

lags = 30
acf_values, confint = acf(u_series, nlags=lags, alpha=0.05)

fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
ax.bar(range(lags+1), acf_values, color='#1f77b4', alpha=0.7, edgecolor='black')
ax.axhline(y=0, color='black', linewidth=1)
ax.axvline(x=10, color='darkorange', linestyle='-', linewidth=2.5, label='10-Day Threshold')

ax.set_title("Autocorrelation of Zonal Wind ($u_{10}$)", fontweight='bold')
ax.set_xlabel("Lag (Days)")
ax.set_ylabel("Autocorrelation Coefficient")
ax.legend()
ax.grid(True, linestyle=':', alpha=0.6)

acf_path = FIG_EXP / 'Autocorrelation_10D.png'
fig.savefig(acf_path, bbox_inches='tight')
plt.close(fig)
ds.close()

print(f"Autocorrelation analysis exported to {acf_path}")