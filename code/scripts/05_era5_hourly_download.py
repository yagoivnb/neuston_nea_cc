# -*- coding: utf-8 -*-
"""
Module: 05_era5_hourly_download.py
Description: Download raw ERA5 hourly surface fields over the North Atlantic.
Retrieves monthly NetCDF files from 1940 to 2025 to act as the foundational 
dataset for subsequent daily and monthly temporal aggregations.
"""

import cdsapi
import numpy as np
from pathlib import Path

# --- DIRECTORY ARCHITECTURE ---
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RAW = REPO_ROOT / "data" / "raw"
DATA_RAW.mkdir(parents=True, exist_ok=True)

print("--- Initialising Copernicus CDS Client ---")
c = cdsapi.Client()

yo = 1940
ye = 2026

for y in np.arange(start=yo, stop=ye, step=1):
    yLst = [str(y)]
    
    for m in np.arange(start=1, stop=13, step=1):
        filename = f"ERA5_NAtlantic_Hourly_{y}{m:02d}.nc"
        output_path = DATA_RAW / filename
        
        print(f"Target: {output_path}")
        
        if output_path.exists():
            print("Already exists. Skipping download.")
        else:
            try:
                c.retrieve(
                    'reanalysis-era5-single-levels',
                    {
                        'product_type': ['reanalysis'],
                        'variable': [
                            '10m_u_component_of_wind', 
                            '10m_v_component_of_wind', 
                            'mean_sea_level_pressure', 
                        ],
                        'year': yLst,
                        'month': [f"{m:02d}"],
                        'day': [
                            "01", "02", "03", "04", "05", "06",
                            "07", "08", "09", "10", "11", "12",
                            "13", "14", "15", "16", "17", "18",
                            "19", "20", "21", "22", "23", "24",
                            "25", "26", "27", "28", "29", "30", "31"
                        ],
                        'time': [
                            '00:00', '01:00', '02:00', '03:00',
                            '04:00', '05:00', '06:00', '07:00',
                            '08:00', '09:00', '10:00', '11:00',
                            '12:00', '13:00', '14:00', '15:00',
                            '16:00', '17:00', '18:00', '19:00',
                            '20:00', '21:00', '22:00', '23:00',
                        ],
                        'data_format': 'netcdf',
                        'download_format': 'unarchived',
                        'area': [65, -50, 15, 5]
                    },
                    str(output_path)
                )
                print(f"Successfully downloaded: {filename}")
            except Exception as e:
                print(f"Error downloading {y}-{m:02d}: {e}")