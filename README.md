# Drifting sentinels: neuston strandings reveal the tropicalisation of Northeast Atlantic

[![Status: In Preparation](https://img.shields.io/badge/Status-In_Preparation-orange)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Data: Pending](https://img.shields.io/badge/Data_Availability-Pending_Repository-lightgrey)](#)

## Overview
This repository contains the complete analytical pipeline for investigating the spatial and temporal dynamics of neustonic organisms (*Physalia physalis* and *Velella velella*) in the Northeast Atlantic and the Bay of Biscay. 

**Abstract Placeholder:** Mass stranding events of pelagic hydrozoans are increasingly reported along the European Atlantic coastlines. This study couples citizen science biological datasets with decadal atmospheric reanalysis to demonstrate how wind-driven advection regimes act as biological proxies for the progressive tropicalisation of the basin.

**Lead Author:** Yago Iván-Baragaño (University of Oviedo)

---

## Repository Architecture & Pipeline
The workflow is strictly sequential, progressing from biological data processing (R) to atmospheric forcing extraction and multi-decadal hindcasting (Python).

### Phase I: Biological Dynamics & Phenology (R)
*   `00_data_preprocessing.R`: Cleaning and structuring of raw observational datasets (e.g., iNaturalist coordinates, standardising dates).
*   `01_exploratory_analysis.R`: Initial spatial aggregations and basic phenological distributions.
*   `02_qgam_modelling.R`: Fitting Quantile Generalised Additive Models (QGAM) to extract non-linear seasonal trends and shifts in stranding peaks.
*   `03_biological_figures.R`: Rendering of spatial distribution maps and phenological density plots.
*   `04_archival_integration.R`: Structuring historical newspaper stranding reports (1940-2012) across Aquitaine and northern Spain.

### Phase II: Climatic Forcing & Hindcast Modelling (Python)
*   `05_era5_extraction.py`: API routines to download Copernicus ERA5 single-level wind ($U_{10}$, $V_{10}$) components.
*   `06_temporal_aggregation.py`: Condensing hourly spatial matrices into daily and monthly climatic baselines.
*   `07_spatial_mosaics.py`: Generating regional atmospheric transport vectors for key forcing windows.
*   `08_hovmoller_climatology.py`: Latitude-time diagrams to track the meridional migration of the Azores High influence.
*   `09_machine_learning_analysis.py`: Training CART and Random Forest classifiers on the modern baseline (2014-2024) and projecting continuous advection probabilities across the historical matrix.
*   `10_machine_learning_visualization.py`: Rendering deterministic tree topologies, Partial Dependence Plots (PDP), and the multi-decadal hindcast timeline.

---

## Data Availability
The heavy raw datasets and binary matrices (NetCDF, Parquet, RData) required to execute this pipeline are excluded from this repository to ensure lightweight version control. Upon publication, all primary datasets, including the cleaned historical archival matrices and atmospheric extractions, will be permanently hosted on a certified scientific repository (e.g., Zenodo) under a persistent DOI.

---

## Dependencies
The analytical core relies on two distinct computational environments.

**R Stack (Phase I):**
*   `qgam`, `mgcv` (Non-linear quantile modelling)
*   `tidyverse`, `dplyr` (Data manipulation)
*   `sf` (Geospatial operations)
*   `ggplot2` (Data visualisation)

**Python Stack (Phase II):**
*   `xarray`, `pandas`, `numpy` (Multidimensional arrays and NetCDF parsing)
*   `scikit-learn` (Machine learning algorithms and validation)
*   `matplotlib`, `seaborn` (Statistical rendering)
*   `pathlib` (Robust directory architecture)

## Execution Protocol
Clone the repository and ensure the target directory structure (`data/raw/`, `data/processed/`, `figures/`) is instantiated. Scripts must be executed in absolute numerical order (00 to 10). Ensure the raw datasets downloaded from the data repository are placed in `data/raw/` prior to initialising Phase I.