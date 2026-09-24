# Neuston strandings reveal _Physalia physalis_ as a sentinel of wind-driven tropicalisation

[![Status: In Preparation](https://img.shields.io/badge/Status-In_Preparation-orange)](#)
[![Code License: MIT](https://img.shields.io/badge/Code_License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Data License: CC BY 4.0](https://img.shields.io/badge/Data_License-CC_BY_4.0-green.svg)](https://creativecommons.org/licenses/by/4.0/)
[![DOI: Pending](https://img.shields.io/badge/DOI-Pending_Zenodo-lightgrey)](#)

## 1. Overview
This repository contains the complete analytical pipeline and data for investigating the spatial and temporal dynamics of neustonic organisms in the Northeast Atlantic and the Bay of Biscay. 

**Abstract:** This study investigates the tropicalisation of temperate seas by tracking neustonic organisms as biological sentinels. Coupling citizen-science records with atmospheric reanalysis (2014–2025), we applied QGAMs and machine learning algorithms (CART, Random Forest) to model the spatio-temporal dynamics of nine surface-drifting species. Results show that the high-windage hydrozoan *Physalia physalis* decoupled from the baseline neustonic community, driving unprecedented mass strandings in the Bay of Biscay since 2019. Furthermore, a multi-decadal hindcast (1940–2025) confirms these incursions are triggered by the poleward expansion of the Azores High and intensifying local westerlies, demonstrating how synoptic atmospheric restructuring directly dictates upper-ocean biological shifts.

**Lead Author:** Yago Iván-Baragaño (University of Oviedo)

---

## 2. Repository Architecture
The repository is structured to guarantee exact computational reproducibility.

*   `code/`:
    *   `scripts/`: Core analytical scripts for statistical modelling (R) and machine learning/climatic extraction (Python).
    *   `notebooks/`: Supplementary R scripts and markdown notebooks for assumption testing, parameter tuning, and specific sub-analyses.
*   `data/raw/`: Contains the essential primary matrices required for execution (`coastalsp_25_raw.csv`, `azores_phys.csv`). 
*   `.Rprofile` & `renv/`: R-specific configuration files that automatically bootstrap the local package environment upon project initialization.
*   `renv.lock`: Deterministic lockfile tracking exact R package dependencies and versions.
*   `environment.yml`: Conda configuration file containing the precise Python environment dependencies.
*   `neuston_nea_cc.Rproj`: RStudio project configuration.
*   `.gitignore`: Controls version tracking, specifically excluding heavy outputs, binaries, and local library caches.

---

## 3. Data Dictionary
The `data/raw/` directory contains the foundational biological datasets extracted from iNaturalist. Both matrices share an identical schema.

### 3.1. Biological Matrices (`coastalsp_25_raw.csv` & `azores_phys.csv`)
`coastalsp_25_raw.csv` (118,019 observations) covers the broad Northeast Atlantic neuston community, while `azores_phys.csv` (491 observations) isolates the *Physalia physalis* oceanic control node within the Azores archipelago.

*   **`id` / `uuid`**: Unique permanent identifiers for the observation within the iNaturalist database. Essential for traceability.
*   **`observed_on`**: Local date of the observation (Format: YYYY-MM-DD). Core temporal variable for phenological modelling.
*   **`time_observed_at` & `time_zone`**: Exact timestamp and local time zone of the stranding event.
*   **`user_login` / `user_id`**: Anonymised identifiers for the citizen scientist who recorded the event.
*   **`quality_grade`**: Data validation flag. Observations flagged as "research" indicate community consensus on taxonomic identification and the presence of verifiable spatial-temporal metadata.
*   **`license`**: Intellectual property license associated with the record (e.g., CC-BY, CC-BY-NC).
*   **`url` / `image_url`**: Direct static URLs linking to the original observation portal and the primary photographic evidence.
*   **`latitude` / `longitude`**: Spatial coordinates of the stranding event (Decimal Degrees, WGS84 projection).
*   **`positional_accuracy`**: Estimated spatial uncertainty of the reported coordinates (in meters).
*   **`place_guess`**: Textual description or toponym of the location provided by the observer.
*   **`scientific_name`**: Accepted binomial nomenclature of the observed organism (e.g., *Physalia physalis*).
*   **`common_name`**: Vernacular name of the taxon (if recorded).
*   **`iconic_taxon_name`**: Broad taxonomic grouping (e.g., Animalia, Mollusca) used for high-level ecological categorization.
*   **`taxon_id`**: Unique taxonomic serial number from the iNaturalist taxonomic framework.

*(Note: Full gridded atmospheric matrices are excluded from version control due to file size constraints, but reproducibility is guaranteed via the Phase II pipeline).*

---

## 4. Analytical Pipeline
The workflow is strictly sequential for the core models, followed by supplementary diagnostic notebooks.

### Phase I: Biological Dynamics & Phenology (R)
*   `00_preprocess.R`: Cleans and structures raw observational datasets, standardizing temporal vectors and spatial coordinates.
*   `01_qgam_modelling.R`: Fits Quantile Generalised Additive Models (QGAM) to extract non-linear seasonal trends and identify temporal shifts in stranding peaks.
*   `02_qgam_figures.R`: Renders quantitative spatio-temporal distribution plots.
*   `03_regionaltrend_modelling.R`: Fits Generalised Linear Models to extract regional incidence trends for each species.
*   `04_regionaltrend_figures.R`: Renders regional trend visualisations.

### Phase II: Climatic Forcing & Hindcast Modelling (Python)
*   `05_era5_hourly_download.py`: API routines executing retrieval of Copernicus ERA5 single-level wind components ($U_{10}$, $V_{10}$).
*   `06_era5_temporal_aggregation.py`: Condenses hourly spatial matrices into daily and monthly climatic baselines.
*   `07_wind_anomalies.py`: Computes regional atmospheric transport vectors for key forcing windows.
*   `08_wind_figures.py`: Generates latitude-time diagrams tracking the meridional migration of the Azores High influence.
*   `09_machine_learning_analysis.py`: Trains CART and Random Forest classifiers on the modern baseline (2014-2024) to project continuous advection probabilities across historical periods.
*   `10_machine_learning_figures.py`: Renders deterministic tree topologies, Partial Dependence Plots (PDP), and the final multi-decadal hindcast timeline.

### Supplementary Phase: Notebooks & Diagnostics
This section contains independent scripts and notebooks utilized for assumption verification and specific visualizations:
*   `azores_physalia_phenology.R`: Phenological dynamics specifically isolated to the Azores control node.
*   `exploratory_assumptions.R`: Diagnostic checks verifying statistical assumptions (e.g., homoscedasticity, normality) for the fitted models.
*   `hovmoller_zonal_wind`: Notebook generating Hovmöller diagrams to visualize zonal wind anomalies.
*   `Species_list`: Notebook synthesizing the taxonomic summary and raw observational counts.
*   `temporal_autocorrelation`: Notebook executing ACF/PACF analysis to detect temporal autocorrelation in stranding events.
*   `tuning_k_parameters.R`: Optimization script for tuning the basis dimensions ($k$) of the splines used in the GAM/QGAM models.

---

## 5. Execution & Reproducibility Protocol
To replicate this study, clone the repository and initialize the exact computational environments.

**1. R Environment (Phase I & Supplementary):**
Open `neuston_nea_cc.Rproj` in RStudio. The `.Rprofile` will automatically detect the `renv` infrastructure. Execute the following command in the R console to synchronize the exact package dependencies:

    renv::restore()

**2. Python Environment (Phase II):**
Open a terminal in the repository root and build the isolated Conda environment using the provided configuration file:

    conda env create -f environment.yml
    conda activate neuston_env

*(Note: Replace `neuston_env` with the exact name specified inside your `environment.yml` file if it differs).*

**3. Execution Order:**
Scripts from Phase I and II must be executed in absolute numerical order (`00` to `10`). Supplementary notebooks can be run independently after `01_qgam_modelling.R`.

---

## 6. License & Citation
This repository operates under a dual-licensing model to ensure open-source code reproducibility while protecting dataset provenance:

*   **Source code:** All analytical scripts (R and Python) are distributed under the **MIT License**. You are free to use, modify, and distribute the code, provided that the original authorship is acknowledged.
*   **Data and assets:** The biological matrices (`.csv` files) housed in `data/raw/`, generated datasets, and output visualisations are distributed under a **Creative Commons Attribution 4.0 International (CC-BY 4.0)** license. Re-use of these datasets requires citing this repository and the associated publication.

If this code or dataset assists in your research, please cite the associated manuscript (citation to be updated upon publication).