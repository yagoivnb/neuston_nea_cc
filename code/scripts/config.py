# -*- coding: utf-8 -*-
"""
# @file:    config.py
# @author:  Yago Iván-Baragaño (ivanyago@uniovi.es)
# @funding: Severo Ochoa Ph.D. program (Principado de Asturias, NAC-AT-PUB-ASV-2025 BP24-109)
# @cite:    
# @brief:   Global configuration module
This script defines absolute paths to manage data and code locally
The secondary hierarchy strictly follows: data, code, and figures
Heavy files stored in the data directories will be ignored by Git
"""

from pathlib import Path

# =============================================================================
# 1. REPOSITORY ROOT PATH
# =============================================================================
# Absolute path to the local Git repository
REPO_DIR = Path(__file__).resolve().parent.parent.parent

# =============================================================================
# 2. INTERNAL DIRECTORY STRUCTURE (Secondary & Tertiary levels)
# =============================================================================

# --- DATA (Contents blocked by .gitignore) ---
DATA_DIR = REPO_DIR / "data"
RAW_DATA = DATA_DIR / "raw"             # Immutable original data (NetCDF, Excel)
PROCESSED_DATA = DATA_DIR / "processed" # Cleaned datasets ready for analysis

# --- CODE (Tracked by Git) ---
CODE_DIR = REPO_DIR / "code"
SCRIPTS_DIR = CODE_DIR / "scripts"      # Formal, sequentially numbered pipeline
NOTEBOOKS_DIR = CODE_DIR / "notebooks"  # Exploratory or draft Python scripts

# --- FIGURES (Contents blocked by .gitignore, except allowed final panels) ---
FIGURES_DIR = REPO_DIR / "figures"
EXPLORATORY_FIGS = FIGURES_DIR / "exploratory" # Drafts and quick diagnostic plots
PUBLICATION_FIGS = FIGURES_DIR / "publication" # High-resolution final panels

# =============================================================================
# 3. DIRECTORY INITIALISATION
# =============================================================================
# List of all tertiary directories to create
DIRECTORIES_TO_CREATE = [
    RAW_DATA, 
    PROCESSED_DATA, 
    SCRIPTS_DIR, 
    NOTEBOOKS_DIR, 
    EXPLORATORY_FIGS, 
    PUBLICATION_FIGS
]

# Ensure required directories exist to prevent runtime errors.
for folder in DIRECTORIES_TO_CREATE:
    folder.mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    print("Universal hierarchy initialised successfully. Folders have been created.")