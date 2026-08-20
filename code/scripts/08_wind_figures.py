# -*- coding: utf-8 -*-
"""
Module: 08_wind_figrues.py
Description: Visualization engine for short-term atmospheric forcing (2014-2025).
Reads processed spatial means and 10-day regional databases to generate 
the spatial mosaics and statistical panels identically to the original design.
"""

import xarray as xr
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import seaborn as sns
from scipy import stats
from astropy.stats import kuiper_two
from matplotlib.lines import Line2D
from pathlib import Path
import warnings

warnings.filterwarnings("ignore")

# --- DIRECTORY ARCHITECTURE ---
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PROC = REPO_ROOT / "data" / "processed"
FIG_PUB = REPO_ROOT / "figures" / "publication"
FIG_EXP = REPO_ROOT / "figures" / "exploratory"

FIG_PUB.mkdir(parents=True, exist_ok=True)
FIG_EXP.mkdir(parents=True, exist_ok=True)

print("--- 1. Loading Processed Datasets ---")
ds_spatial = xr.open_dataset(DATA_PROC / "ERA5_Spatial_Means_Phases.nc")
df_10d = pd.read_parquet(DATA_PROC / "Wind_Phenology_10D.parquet")

# =============================================================================
# PART 1: SPATIAL MOSAICS (Cartopy) -> figures/publication
# =============================================================================
print("\n--- 2. Generating Spatial Mosaics ---")

season_names = ['MAM', 'JUN', 'JASO']
datos_mosaico = []

for s in season_names:
    p1_u, p1_v = ds_spatial[f'u_{s}_P1'].squeeze(), ds_spatial[f'v_{s}_P1'].squeeze()
    p2_u, p2_v = ds_spatial[f'u_{s}_P2'].squeeze(), ds_spatial[f'v_{s}_P2'].squeeze()
    p3_u, p3_v = ds_spatial[f'u_{s}_P3'].squeeze(), ds_spatial[f'v_{s}_P3'].squeeze()
    
    row_data = [
        (p1_u, p1_v),
        (p2_u, p2_v),
        (p3_u, p3_v),
        (p2_u - p1_u, p2_v - p1_v),
        (p3_u - p1_u, p3_v - p1_v)
    ]
    datos_mosaico.append(row_data)

lev_mean = np.linspace(-4, 4, 20)
lev_diff = np.linspace(-2, 2, 20)

config_filas = [
    {'ext': [-50, -5, 25, 65],   'scale': 100, 'skip': 10, 'x_step': 15, 'y_step': 10, 'label': 'Spring\n(MAM)'},
    {'ext': [-45, 0, 25, 65],    'scale': 100, 'skip': 10, 'x_step': 10, 'y_step': 10, 'label': 'Transition\n(JUN)'},
    {'ext': [-11.25, 0, 40, 50], 'scale': 60,  'skip': 4,  'x_step': 3,  'y_step': 3,  'label': 'Summer\n(JASO)'}
]

titulos_columnas = ["Low Incidence (Control)\n(2014-2018)", "Winter Strandings\n(2019-2022)", "Summer Mass Strandings\n(2023-2025)", 
                    "Zonal Anomaly\n(Winter vs Control)", "Zonal Anomaly\n(Summer vs Control)"]

col_filenames = ['Absence_1418', 'WinterStrand_1922', 'SummerStrand_2325', 'Anom_Winter_vs_Control', 'Anom_Summer_vs_Control']

def draw_panel(ax, u, v, extent, levels, scale, skip, show_left=False, show_right=False, show_bottom=False, is_diff=False, x_step=10, y_step=10, cmap='RdBu_r'):
    ax.set_extent(extent, crs=ccrs.PlateCarree())
    
    fill = ax.contourf(u.longitude, u.latitude, u, levels=levels, cmap=cmap, extend='both', transform=ccrs.PlateCarree(), zorder=1)
    ax.quiver(u.longitude[::skip], u.latitude[::skip], u[::skip, ::skip], v[::skip, ::skip],
              color='black', alpha=0.85 if not is_diff else 0.95, transform=ccrs.PlateCarree(), scale=scale, width=0.0035, zorder=2)
              
    ax.add_feature(cfeature.LAND, facecolor='lightgray', edgecolor='black', zorder=3)
    ax.add_feature(cfeature.COASTLINE, linewidth=0.8, zorder=4)
    ax.add_feature(cfeature.BORDERS, linestyle=':', alpha=0.5, zorder=4)
    
    gl = ax.gridlines(draw_labels=True, linewidth=0.4, color='gray', alpha=0.5, linestyle='--', zorder=5,
                      xlocs=np.arange(-180, 180, x_step), ylocs=np.arange(-90, 90, y_step))
    gl.xlabel_style = {'size': 12, 'color': 'black'}
    gl.ylabel_style = {'size': 12, 'color': 'black'}
    
    if hasattr(gl, 'bottom_labels'):
        gl.top_labels = False; gl.left_labels = show_left; gl.right_labels = show_right; gl.bottom_labels = show_bottom
    else:
        gl.xlabels_top = False; gl.ylabels_left = show_left; gl.ylabels_right = show_right; gl.xlabels_bottom = show_bottom
        
    return fill

fig = plt.figure(figsize=(24, 15), dpi=300)
gs = gridspec.GridSpec(4, 5, height_ratios=[1, 1, 1, 0.12], hspace=0.15, wspace=0.05)

for r in range(3): 
    cfg = config_filas[r]
    for c in range(5): 
        u, v = datos_mosaico[r][c]
        is_diff = (c >= 3)
        current_scale = cfg['scale'] if not is_diff else cfg['scale'] / 2 
        
        ax = fig.add_subplot(gs[r, c], projection=ccrs.PlateCarree())
        
        fill = draw_panel(ax, u, v, extent=cfg['ext'], 
                          levels=lev_diff if is_diff else lev_mean, 
                          scale=current_scale, skip=cfg['skip'], 
                          show_left=(c == 0), 
                          show_right=False, 
                          show_bottom=True, 
                          is_diff=is_diff, x_step=cfg['x_step'], y_step=cfg['y_step'], 
                          cmap='PuOr_r' if is_diff else 'RdBu_r')
                          
        if r == 0: ax.set_title(titulos_columnas[c], fontweight='bold', fontsize=18, pad=15)
        if c == 0: ax.annotate(cfg['label'], xy=(-0.35, 0.5), xycoords='axes fraction', 
                        va='center', ha='center', rotation=90, fontweight='bold', fontsize=18)
        
        if r == 0 and c == 0: fill_mean = fill
        if r == 0 and c == 3: fill_diff = fill

        fig_indiv = plt.figure(figsize=(8, 8), dpi=300)
        ax_indiv = plt.axes(projection=ccrs.PlateCarree())
        
        fill_indiv = draw_panel(ax_indiv, u, v, extent=cfg['ext'], 
                                levels=lev_diff if is_diff else lev_mean, 
                                scale=current_scale, skip=cfg['skip'], 
                                show_left=True, show_right=False, show_bottom=True, 
                                is_diff=is_diff, x_step=cfg['x_step'], y_step=cfg['y_step'], 
                                cmap='PuOr_r' if is_diff else 'RdBu_r')
        
        title_clean = titulos_columnas[c].replace('\n', ' ')
        label_clean = cfg['label'].replace('\n', ' ')
        ax_indiv.set_title(f"{label_clean} | {title_clean}", fontweight='bold', fontsize=14, pad=15)
        
        cbar_indiv = plt.colorbar(fill_indiv, ax=ax_indiv, orientation='horizontal', pad=0.08, shrink=0.8)
        cbar_label = 'Zonal Anomaly ($\Delta u_{10}$) [m/s]' if is_diff else 'Mean Zonal Wind ($u_{10}$) [m/s]'
        cbar_indiv.set_label(cbar_label, fontsize=12, fontweight='bold')
        
        file_name = f"Map_{season_names[r]}_{col_filenames[c]}.png"
        fig_indiv.savefig(FIG_EXP / file_name, bbox_inches='tight', facecolor='white')
        plt.close(fig_indiv)

print(f"--- 15 mapas individuales generados y guardados como PNG en {FIG_PUB.name} ---")

cax_mean = fig.add_subplot(gs[3, 0:3])
cbar_mean = plt.colorbar(fill_mean, cax=cax_mean, orientation='horizontal', ticks=np.arange(-4, 5, 1))
cbar_mean.ax.tick_params(labelsize=14)
cbar_mean.set_label('Mean Zonal Wind ($u_{10}$) [m/s]', fontsize=16, fontweight='bold')

cax_diff = fig.add_subplot(gs[3, 3:5])
cbar_diff = plt.colorbar(fill_diff, cax=cax_diff, orientation='horizontal', ticks=np.arange(-2, 3, 1))
cbar_diff.ax.tick_params(labelsize=14)
cbar_diff.set_label('Zonal Anomaly ($\Delta u_{10}$) [m/s]', fontsize=16, fontweight='bold')

plt.suptitle("", fontsize=24, fontweight='bold', y=0.96)

master_path = FIG_PUB / 'Mosaico_Global_ProgressiveForcing.svg'
plt.savefig(master_path, bbox_inches='tight', facecolor='white', format='svg')
print(f"--- Mosaico de Hipótesis guardado en formato vectorial (SVG) en: {master_path.name} ---")
plt.close(fig)

# =============================================================================
# PART 2: UNIFIED STATISTICAL PANEL -> figures/exploratory
# =============================================================================
print("\n--- 3. Generating Unified Statistical Panel ---")

titulos_col = ['Initial Push\n(Spring - MAM)', 'Transition Zone\n(June)', 'Coastal Barrier\n(Summer - JASO)']
phase_labels = ['Absence\n(14-18)', 'Winter Surge\n(19-22)', 'Summer Surge\n(23-25)']
colores = ['#1f77b4', '#ff7f0e', '#d62728'] 

fig_stat = plt.figure(figsize=(18, 16), dpi=300)
gs_stat = fig_stat.add_gridspec(3, 3, hspace=0.35, wspace=0.25)

for i, fase in enumerate(season_names):
    var_u = f'U10_{fase}'
    var_a = f'Ang_{fase}'
    
    df_sub = df_10d.dropna(subset=[var_u, 'Arribazón']).copy()
    df_sub['Arribazón'] = df_sub['Arribazón'].astype(int)
    
    g0_u = df_sub[df_sub['Arribazón'] == 0][var_u]
    g1_u = df_sub[df_sub['Arribazón'] == 1][var_u]
    g2_u = df_sub[df_sub['Arribazón'] == 2][var_u]
    
    ang0 = df_sub[df_sub['Arribazón'] == 0][var_a].dropna()
    ang1 = df_sub[df_sub['Arribazón'] == 1][var_a].dropna()
    ang2 = df_sub[df_sub['Arribazón'] == 2][var_a].dropna()

    # FILA 1: VIOLIN PLOTS
    ax_v = fig_stat.add_subplot(gs_stat[0, i])
    _, p_kw = stats.kruskal(g0_u, g1_u, g2_u)
    
    sns.violinplot(data=df_sub, x='Arribazón', y=var_u, ax=ax_v, 
                   hue='Arribazón', palette=colores, legend=False, inner='quartile')
    sns.stripplot(data=df_sub, x='Arribazón', y=var_u, ax=ax_v, 
                  color='black', alpha=0.3, size=3, jitter=True)
    
    ax_v.set_title(f"{titulos_col[i]}\n(Kruskal-Wallis p={p_kw:.3f})", fontweight='bold', fontsize=14)
    ax_v.set_xticks([0, 1, 2])
    ax_v.set_xticklabels(phase_labels)
    ax_v.set_xlabel('')
    ax_v.set_ylabel('Mean Zonal Wind [m/s]' if i == 0 else '')
    ax_v.grid(axis='y', linestyle='--', alpha=0.5)

    # FILA 2: ECDF 
    ax_cdf = fig_stat.add_subplot(gs_stat[1, i])
    _, p01 = stats.mannwhitneyu(g0_u, g1_u, alternative='two-sided')
    _, p02 = stats.mannwhitneyu(g0_u, g2_u, alternative='two-sided')
    _, p12 = stats.mannwhitneyu(g1_u, g2_u, alternative='two-sided')
    
    sns.ecdfplot(data=df_sub, x=var_u, hue='Arribazón', palette=colores, linewidth=2.5, ax=ax_cdf)
    
    ax_cdf.set_title(f"Pairwise M-W (p-vals):\n0vs1: {p01:.3f} | 0vs2: {p02:.3f} | 1vs2: {p12:.3f}", 
                     fontsize=11, style='italic')
    ax_cdf.set_xlabel('Mean Zonal Wind [m/s]')
    ax_cdf.grid(True, linestyle=':', alpha=0.7)
    
    if ax_cdf.get_legend() is not None:
        ax_cdf.get_legend().remove() 
        
    if i == 0:
        ax_cdf.set_ylabel('Cumulative Probability')
        leyenda_lineas = [Line2D([0], [0], color=colores[0], lw=2.5),
                          Line2D([0], [0], color=colores[1], lw=2.5),
                          Line2D([0], [0], color=colores[2], lw=2.5)]
        ax_cdf.legend(leyenda_lineas, ['Absence', 'Winter', 'Summer'], title='Phase', loc='lower right')
    else:
        ax_cdf.set_ylabel('')

    # FILA 3: ROSAS DE VIENTO
    ax_a = fig_stat.add_subplot(gs_stat[2, i], projection='polar')
    
    if len(ang0) > 2 and len(ang1) > 2 and len(ang2) > 2:
        _, pk01 = kuiper_two(np.radians(ang0) % (2*np.pi), np.radians(ang1) % (2*np.pi))
        _, pk02 = kuiper_two(np.radians(ang0) % (2*np.pi), np.radians(ang2) % (2*np.pi))
        _, pk12 = kuiper_two(np.radians(ang1) % (2*np.pi), np.radians(ang2) % (2*np.pi))
        
        sectores = 30
        bins = np.arange(0, 361, sectores)
        width = np.radians(sectores) / 3.5  
        theta = np.radians(bins[:-1] + (sectores / 2))
        
        h0, _ = np.histogram(ang0, bins=bins); freq0 = (h0/len(ang0))*100
        h1, _ = np.histogram(ang1, bins=bins); freq1 = (h1/len(ang1))*100
        h2, _ = np.histogram(ang2, bins=bins); freq2 = (h2/len(ang2))*100
        
        ax_a.bar(theta - width, freq0, width=width, color=colores[0], alpha=0.8, edgecolor='black', linewidth=0.5)
        ax_a.bar(theta,         freq1, width=width, color=colores[1], alpha=0.8, edgecolor='black', linewidth=0.5)
        ax_a.bar(theta + width, freq2, width=width, color=colores[2], alpha=0.8, edgecolor='black', linewidth=0.5)
        
        ax_a.set_title(f"Pairwise Kuiper (p-vals):\n0vs1: {pk01:.3f} | 0vs2: {pk02:.3f} | 1vs2: {pk12:.3f}", 
                       fontsize=11, style='italic', pad=15)
        
    ax_a.set_theta_zero_location('N'); ax_a.set_theta_direction(-1)
    ax_a.set_xticks(np.radians([0, 90, 180, 270]))
    ax_a.set_xticklabels(['N', 'E', 'S', 'W'], fontweight='bold')
    ax_a.set_yticks([])

plt.suptitle("Statistical Dynamics: The Progressive Forcing Hypothesis", fontweight='bold', fontsize=22, y=0.96)

fig_path = FIG_EXP / 'Panel_Estadistico_Unificado_3Fases.svg'
plt.savefig(fig_path, bbox_inches='tight', facecolor='white')
print(f"--- Mega-Panel Estadístico guardado en: {fig_path.name} ---")

ds_spatial.close()