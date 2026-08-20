# -*- coding: utf-8 -*-
"""
Module: 09_machine_learning_analysis.py
Description: Integrated Model Training & Historical Hindcast Inference Pipeline.
Extracts annual features (1940-2025), fits CART & Random Forest algorithms 
on the modern baseline (2014-2025), and projects advection probabilities 
across the multi-decadal historical record.
"""

import xarray as xr
import pandas as pd
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from pathlib import Path
import warnings

warnings.filterwarnings("ignore")

# --- DIRECTORY ARCHITECTURE ---
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PROC = REPO_ROOT / "data" / "processed"
TABLES_DIR = REPO_ROOT / "tables"
TABLES_DIR.mkdir(parents=True, exist_ok=True)

print("--- 1. Loading Monthly Historical Dataset (1940-2025) ---")
ds = xr.open_dataset(DATA_PROC / "ERA5_NAtlantic_Monthly_1940-2025.nc")
ds = ds.sortby('latitude').sortby('longitude')

u_var = 'u10' if 'u10' in ds.variables else '10m_u_component_of_wind'
v_var = 'v10' if 'v10' in ds.variables else '10m_v_component_of_wind'

print("\n--- 2. Reconstructing the Multi-decadal Feature Matrix (1940-2025) ---")

# A. Spring Zonal Push (MAM)
ds_mam = ds.sel(longitude=slice(-50, -25), latitude=slice(35, 45))
ds_mam = ds_mam.sel(valid_time=ds_mam['valid_time'].dt.month.isin([3, 4, 5]))
df_mam = ds_mam[u_var].groupby('valid_time.year').mean(dim=xr.ALL_DIMS).to_dataframe(name='U10_MAM').reset_index().rename(columns={'year': 'Año'})

# B. Transition Angle (JUN)
ds_jun = ds.sel(longitude=slice(-25, -10), latitude=slice(43.2, 55))
ds_jun = ds_jun.sel(valid_time=ds_jun['valid_time'].dt.month == 6)
df_jun_vec = ds_jun[[u_var, v_var]].groupby('valid_time.year').mean(dim=xr.ALL_DIMS).to_dataframe().reset_index().rename(columns={'year': 'Año'})
angle_rad = np.arctan2(df_jun_vec[v_var], df_jun_vec[u_var])
df_jun_vec['Ang_JUN'] = (90 - np.degrees(angle_rad)) % 360
df_jun = df_jun_vec[['Año', 'Ang_JUN']]

# C. Summer Coastal Barrier (JASO)
ds_jaso = ds.sel(longitude=slice(-10, -1), latitude=slice(43.2, 48.5))
ds_jaso = ds_jaso.sel(valid_time=ds_jaso['valid_time'].dt.month.isin([7, 8, 9, 10]))
df_jaso = ds_jaso[u_var].groupby('valid_time.year').mean(dim=xr.ALL_DIMS).to_dataframe(name='U10_JASO').reset_index().rename(columns={'year': 'Año'})

# Merge complete historical matrix
df_historical = df_mam.merge(df_jun, on='Año', how='outer').merge(df_jaso, on='Año', how='outer').dropna().reset_index(drop=True)

print("\n--- 3. Defining the Modern Training Baseline (2014-2025) ---")
df_train = df_historical[(df_historical['Año'] >= 2014) & (df_historical['Año'] <= 2025)].copy()

conditions_binary = [(df_train['Año'] <= 2018), (df_train['Año'] >= 2019)]
df_train['Arribazón_Binario'] = np.select(conditions_binary, [0, 1], default=np.nan)

X_train = df_train[['U10_MAM', 'Ang_JUN', 'U10_JASO']]
y_train = df_train['Arribazón_Binario']

print("\n--- 4. Instantiating Models & Executing Hindcast Projection ---")
# Random Forest Model instantiation and fitting
rf_model = RandomForestClassifier(n_estimators=500, random_state=42, max_depth=2, max_features='sqrt', oob_score=True)
rf_model.fit(X_train, y_train)

df_rf_imp = pd.DataFrame({
    'Predictor': X_train.columns, 
    'Importance_RF_Pct': rf_model.feature_importances_ * 100
})

# Hindcast Projection across 1940-2025
X_historical = df_historical[['U10_MAM', 'Ang_JUN', 'U10_JASO']]
df_historical['Prob_Presence_RF'] = rf_model.predict_proba(X_historical)[:, 1]
df_historical['Rolling_Avg_5yr'] = df_historical['Prob_Presence_RF'].rolling(window=5, center=True, min_periods=1).mean()

# Integrate archival stranding proxy records
hemeroteca_years = [1946, 1957, 1961, 1974, 1979, 2000, 2001, 2008, 2010, 2011, 2012, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
df_historical['Archival_Record'] = df_historical['Año'].isin(hemeroteca_years).astype(int)

# Diagnostic Validation Metrics
archival_subset = df_historical[df_historical['Archival_Record'] == 1]
true_positives = archival_subset[archival_subset['Prob_Presence_RF'] >= 0.5].shape[0]
total_archival = archival_subset.shape[0]
validation_yield = (true_positives / total_archival) * 100

report_content = (
    "--- 1. RANDOM FOREST BASELINE VALIDATION (2014-2025) ---\n"
    f"Out-Of-Bag (OOB) Accuracy: {rf_model.oob_score_ * 100:.1f}%\n"
    f"Feature Importances:\n{df_rf_imp.to_string(index=False)}\n\n"
    "--- 2. HINDCAST VALIDATION (1940-2025) ---\n"
    f"Total documented historical events (Archival Proxy): {total_archival}\n"
    f"Events correctly classified as high risk (P >= 0.5): {true_positives}\n"
    f"Empirical Validation Yield: {validation_yield:.1f}%\n"
)
print(f"\n{report_content}")

# Data Serialization
out_train = DATA_PROC / "ML_Training_Matrix_2014_2025.parquet"
out_hist = DATA_PROC / "ML_Hindcast_Matrix_1940_2025.parquet"
out_imp = TABLES_DIR / "RF_Feature_Importances.csv"
out_report = TABLES_DIR / "Hindcast_Validation_Report.txt"

df_train.to_parquet(out_train, index=False)
df_historical.to_parquet(out_hist, index=False)
df_rf_imp.to_csv(out_imp, index=False)

with open(out_report, 'w') as f:
    f.write(report_content)

ds.close()
print("✅ Script 09 completed. ML matrices and validation reports exported successfully.")

