# -*- coding: utf-8 -*-
"""
Module: 10_machine_learning_visualization.py
Description: Generates high-resolution plots for phenomenological regime modelling.
Produces the CART topology and feature importances panel, and the multi-decadal 
Random Forest hindcast advection timeline (1940-2025). 
Outputs are saved to the exploratory folder for manual vector editing.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.tree import DecisionTreeClassifier, plot_tree
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from pathlib import Path
import warnings

warnings.filterwarnings("ignore")

# --- DIRECTORY ARCHITECTURE ---
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_PROC = REPO_ROOT / "data" / "processed"
FIG_EXP = REPO_ROOT / "figures" / "exploratory"
FIG_EXP.mkdir(parents=True, exist_ok=True)

print("--- 1. Loading Preprocessed ML Matrices ---")
df_train = pd.read_parquet(DATA_PROC / "ML_Training_Matrix_2014_2025.parquet")
df_historical = pd.read_parquet(DATA_PROC / "ML_Hindcast_Matrix_1940_2025.parquet")

X_train = df_train[['U10_MAM', 'Ang_JUN', 'U10_JASO']]
y_train = df_train['Arribazón_Binario']

# ==============================================================================
# PART 1: CART & RF TOPOLOGY & FEATURE IMPORTANCE
# ==============================================================================
print("\n--- 2. Generating Machine Learning Diagnostic Panel ---")
clf_cart = DecisionTreeClassifier(random_state=42, max_depth=2)
clf_cart.fit(X_train, y_train)

importancias_cart = clf_cart.feature_importances_ * 100
df_rf_imp = pd.read_csv(REPO_ROOT / "tables" / "RF_Feature_Importances.csv")
importancias_rf = df_rf_imp['Importance_RF_Pct'].values
predictores = ['Spring Zonal Wind (MAM)', 'Transition Angle (JUN)', 'Summer Zonal Wind (JASO)']

# Ampliamos a 3 paneles
fig_ml, axes = plt.subplots(1, 3, figsize=(24, 6), dpi=300)

# Panel A: CART Feature Importance
sns.barplot(x=importancias_cart, y=predictores, palette='viridis', ax=axes[0])
axes[0].set_title("Feature Importance (Single CART)", fontweight='bold', pad=10)
axes[0].set_xlabel("Mean Decrease in Gini Impurity (%)")
axes[0].set_xlim(0, 100)
for index, value in enumerate(importancias_cart):
    if value > 0: axes[0].text(value + 1.5, index, f'{value:.1f}%', va='center', fontweight='bold')

# Panel B: Random Forest Feature Importance
sns.barplot(x=importancias_rf, y=predictores, palette='magma', ax=axes[1])
axes[1].set_title("Feature Importance (Random Forest Ensemble)", fontweight='bold', pad=10)
axes[1].set_xlabel("Mean Decrease in Gini Impurity (%)")
axes[1].set_xlim(0, 100)
axes[1].set_yticklabels([]) # Limpiamos el eje Y para evitar redundancia visual
for index, value in enumerate(importancias_rf):
    if value > 0: axes[1].text(value + 1.5, index, f'{value:.1f}%', va='center', fontweight='bold')

# Panel C: Binary Decision Tree Topology (CART)
phenological_classes = ['Absence (14-18)', 'Presence (19-25)']
plot_tree(clf_cart, feature_names=X_train.columns, class_names=phenological_classes, 
          filled=True, rounded=True, proportion=False, fontsize=10, ax=axes[2])
axes[2].set_title("Climatic Decision Tree Topology (max_depth=2)", fontweight='bold', pad=10)

plt.tight_layout()

cart_path_svg = FIG_EXP / 'fig_09_ML_Diagnostics.svg'
cart_path_png = FIG_EXP / 'fig_09_ML_Diagnostics.png'
plt.savefig(cart_path_svg, format='svg', bbox_inches='tight', facecolor='white')
plt.savefig(cart_path_png, format='png', bbox_inches='tight', facecolor='white')
plt.close(fig_ml)
print(f"ML diagnostics panel exported to exploratory folder.")

# ==============================================================================
# PART 2: RANDOM FOREST HISTORICAL HINDCAST PROJECTION (1940-2025)
# ==============================================================================
print("\n--- 3. Generating Historical Hindcast Projection Plot ---")

sns.set_theme(style="ticks", context="paper")
plt.rcParams['font.family'] = 'sans-serif'
fig_rf, ax = plt.subplots(figsize=(15, 8), dpi=400)

# Fill Critical Advection Envelope 
ax.fill_between(df_historical['Año'], 0.5, df_historical['Prob_Presence_RF'], 
                where=(df_historical['Prob_Presence_RF'] >= 0.5), 
                color='#FF9C32', alpha=0.25, interpolate=True, zorder=1)

# Plot Low-Frequency Climatic Trend
ax.plot(df_historical['Año'], df_historical['Rolling_Avg_5yr'], 
        color='#3440AD', linewidth=1.8, linestyle='-.', alpha=0.85, zorder=3,
        label='5-Year Climatic Trend')

# Plot Main Advection Suitability 
ax.plot(df_historical['Año'], df_historical['Prob_Presence_RF'], 
        color='#000000', linewidth=2.2, zorder=4, alpha=0.95,
        label='Advection Suitability ($P_{Presence}$)')

# Critical Hydrodynamic Threshold
ax.axhline(y=0.5, color='#710000', linestyle='--', linewidth=1.5, alpha=1, zorder=2,
           label='Critical Threshold ($P=0.5$)')

# Overlay Archival Proxy Records
archival_subset = df_historical[df_historical['Archival_Record'] == 1]
ax.scatter(archival_subset['Año'], archival_subset['Prob_Presence_RF'], 
           color='#d73027', edgecolor='white', linewidth=1.2, 
           marker='v', s=100, zorder=5, 
           label='Documented Stranding (Archival Proxy)')

# Modern Baseline Training Period Shading
ax.axvspan(2013.5, 2025.5, color='grey', alpha=0.1, hatch='//', edgecolor='none', zorder=0)

# Formatting, Typography, and Accessibility
ax.set_title("", fontweight='bold', fontsize=20, pad=15)
ax.set_xlabel("", fontweight='bold', fontsize=12)
ax.set_ylabel("Probability of BoB strandings ($P_{Presence}$)", fontweight='bold', fontsize=20)

ax.tick_params(axis='both', which='major', labelsize=16)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# Strict view limits
ax.set_xlim(1940, 2025)
ax.set_ylim(-0.15, 1.19) 

# Minimalist grid strictly for the y-axis
ax.grid(axis='y', linestyle=':', color='lightgray', alpha=0.7, zorder=0)

# Custom Legend Construction
legend_elements = [
    Line2D([0], [0], color='#000000', lw=2.2, label='Advection Suitability ($P_{Presence}$)'),
    Line2D([0], [0], color='#3440AD', lw=1.8, linestyle='-.', label='5-Year Climatic Trend'),
    Line2D([0], [0], color='#710000', lw=1.5, linestyle='--', label='Critical Threshold ($P=0.5$)'),
    Line2D([0], [0], marker='v', color='w', markerfacecolor='#d73027', markeredgecolor='white', 
           markersize=10, markeredgewidth=1.2, label='Archival Stranding Event'),
    Patch(facecolor='grey', alpha=0.1, hatch='//', label='Modern Calibration Baseline (2014–2025)')
]

ax.legend(handles=legend_elements, loc='upper left', frameon=True, 
          framealpha=0.95, edgecolor='black', fontsize=14, borderpad=0.8)

plt.tight_layout()

# Exportación dual (SVG y PNG)
rf_path_svg = FIG_EXP / 'fig_10_Historical_Hindcast.svg'
rf_path_png = FIG_EXP / 'fig_10_Historical_Hindcast.png'
plt.savefig(rf_path_svg, format='svg', bbox_inches='tight', facecolor='white')
plt.savefig(rf_path_png, format='png', bbox_inches='tight', facecolor='white')
plt.close(fig_rf)

print(f"Historical hindcast plot exported to exploratory folder (SVG and PNG).")
print("\n✅ Script 10 completed successfully.")