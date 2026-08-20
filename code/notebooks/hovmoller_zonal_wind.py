# -*- coding: utf-8 -*-
"""
Hovmöller Diagram Analysis (2014-2025)
Description: Generates a Latitude-Time (Hovmöller) diagram to illustrate 
the seasonal meridional migration of the Zonal Wind (U10).
"""

import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import warnings

warnings.filterwarnings("ignore")

# --- DIRECTORY ARCHITECTURE (ROBUST) ---
REPO_ROOT = Path(r"C:\Users\yagoi\repositories\neuston_nea_cc")
DATA_PROC = REPO_ROOT / "data" / "processed"
FIG_EXP = REPO_ROOT / "figures" / "exploratory"
FIG_EXP.mkdir(parents=True, exist_ok=True)

class HovmollerAnalyser:
    """
    Class dedicated to generating Latitude-Time (Hovmöller) diagrams to illustrate
    the seasonal meridional migration of atmospheric drivers (e.g., Zonal Wind).
    """
    @staticmethod
    def compute_climatological_hovmoller(ds, var_name='10m_u_component_of_wind', lon_band=(-25, -5), lat_band=(25, 60), years=None):
        print(f"--- Computing Hovmöller data for {var_name} (Lon: {lon_band}, Lat: {lat_band}) ---")
        
        # 1. Check variable name dynamically
        actual_var = 'u10' if 'u10' in ds.variables else var_name
        
        # 2. Temporal filtering by years
        if years is not None:
            ds = ds.sel(time=ds.time.dt.year.isin(years))
            
        # 3. Sort coordinates to allow correct slicing
        ds = ds.sortby('latitude')
        ds = ds.sortby('longitude')
        
        # 4. Spatial filtering
        ds_band = ds.sel(
            longitude=slice(lon_band[0], lon_band[1]),
            latitude=slice(lat_band[0], lat_band[1])
        )
        
        # 5. Zonal mean and monthly climatology
        zonal_mean = ds_band[actual_var].mean(dim='longitude')
        hov_data = zonal_mean.groupby('time.month').mean('time')
        return hov_data

    @staticmethod
    def plot_hovmoller(hov_data, title, cmap='RdBu_r', vmin=-6, vmax=6):
        fig, ax = plt.subplots(figsize=(8, 6), dpi=300)
        
        # --- CYCLIC WRAPPING FOR CONTOUR PLOTS ---
        # Append January's data to the end to close the annual cycle and render December fully.
        data_matrix = hov_data.T.values
        cyclic_data = np.hstack((data_matrix, data_matrix[:, 0:1])) 
        
        months_cyclic = np.arange(1, 14) # 1 to 13
        latitudes = hov_data.latitude.values
        
        # Plot using the cyclic data matrix
        cf = ax.contourf(months_cyclic, latitudes, cyclic_data, levels=np.linspace(vmin, vmax, 17), cmap=cmap, extend='both')
        cs = ax.contour(months_cyclic, latitudes, cyclic_data, levels=[0], colors='black', linewidths=1.5, linestyles='--')
        ax.clabel(cs, inline=True, fmt='0 m/s', fontsize=10, manual=[(2, 30)])
        
        # --- AXES CONFIGURATION (Centred labels + Boundary tick marks) ---
        ax.set_xlim(1, 13) # Ensure full rendering up to the end of December
        
        # 1. Major Ticks: Used exclusively for centred text labels
        ax.set_xticks(np.arange(1.5, 13.5)) 
        ax.set_xticklabels(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], fontsize=13)
        ax.tick_params(axis='x', which='major', length=5) # Hide major tick lines
        
        # 2. Minor Ticks: Used exclusively for physical boundary marks (1st of the month)
        ax.set_xticks(np.arange(1, 14), minor=True)
        ax.tick_params(axis='x', which='minor', length=0, width=1, color='black', direction='out')
        
        ax.set_ylabel('Latitude (°N)', fontweight='bold', fontsize=14)
        ax.tick_params(axis='y', labelsize=13)
        ax.set_title(title, fontweight='bold', pad=15)
        
        cbar = plt.colorbar(cf, ax=ax, orientation='vertical', pad=0.02)
        cbar.set_label('Zonal Wind Speed ($U_{10}$) [m/s]', fontweight='bold')
        
        # Align vertical grid lines with the minor ticks (start of the month)
        ax.grid(which='minor', axis='x', linestyle=':', alpha=0.6)
        ax.grid(which='major', axis='y', linestyle=':', alpha=0.6)
        
        plt.tight_layout()
        return fig

# --- EXECUTION OF BLOCK 3 ---
print("--- Loading Daily Consolidated Dataset ---")
file_path = DATA_PROC / "ERA5_NAtlantic_Daily_2014-2025.nc"

try:
    ds = xr.open_dataset(file_path)
    print("\nExecuting Block 3: Hovmöller Climatology (Period 2014-2025)...")
    
    hov_data = HovmollerAnalyser.compute_climatological_hovmoller(
        ds, 
        var_name='10m_u_component_of_wind', 
        lon_band=(-50, -10), 
        lat_band=(25, 55),
        years=range(2014, 2026) 
    )

    fig_hov = HovmollerAnalyser.plot_hovmoller(
        hov_data, 
        title=''
    )
    
    fig_path = FIG_EXP / 'HovmollerU10.png'
    fig_hov.savefig(fig_path, bbox_inches='tight')
    print(f"--- Figure saved to {fig_path} ---")
    
    plt.show()
    ds.close()

except FileNotFoundError:
    print(f"Cannot execute Block 3 because dataset is empty or undefined at {file_path}")