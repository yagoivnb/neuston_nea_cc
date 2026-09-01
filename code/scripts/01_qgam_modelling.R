# ==============================================================================
# @file:    01_qgam_modelling.r
# @author:  Yago Iván-Baragaño (ivanyago@uniovi.es)
# @funding: Severo Ochoa Ph.D. program (Principado de Asturias, NAC-AT-PUB-ASV-2025 BP24-109)
# @cite:    
# @brief:   Core modelling pipeline fitting qGAMs
# Temporal and seasonal latitudinal shifts of neustonic organisms
# Fits are saved as binary objects for subsequent visualisation 
# ==============================================================================

library(dplyr)
library(lubridate)
library(mgcv)
library(qgam)
library(gratia)

set.seed(1234)

# ------------------------------------------------------------------------------
# 1. GLOBAL SETTINGS & HYPERPARAMETERS
# ------------------------------------------------------------------------------
YEAR_MIN <- 2014
TAU_MED  <- 0.5
K_YDAY_GRID <- 4:15
K_YEAR_GRID <- 4:10
TOL <- 0.005

# Manual basis dimensions (k) established post grid-search optimisation
k_manual <- tibble::tribble(
  ~species,            ~ky, ~kt,
  "Physalia",          8,   9,
  "Velella",           6,   4,
  "Neutral Neuston",   5,   4
)

# ------------------------------------------------------------------------------
# 2. CORE FUNCTIONS
# ------------------------------------------------------------------------------
prep_data <- function(df, year_min = YEAR_MIN) {
  df |>
    mutate(
      yday        = yday(verbatimEventDate),
      decimalYear = decimal_date(verbatimEventDate)
    ) |>
    filter(year >= year_min)
}

fit_mqgam_median_fixedk <- function(data, ky, kt) {
  mqgam(
    decimalLatitude ~ s(yday, bs = "cc", k = ky) + s(decimalYear, bs = "tp", k = kt),
    qu   = c(TAU_MED),
    data = data
  )
}

extract_mq_smooth <- function(fit, tau, smooth_var){
  m_tau <- qdo(fit, qu = tau)
  intercept   <- coef(m_tau)[1]
  smooth_name <- paste0("s(", smooth_var, ")")
  
  smooth_estimates(m_tau, smooth = smooth_name) |>
    mutate(
      latitud_real  = .estimate + intercept,
      latitud_upper = .estimate + intercept + 1.96 * .se,
      latitud_lower = .estimate + intercept - 1.96 * .se,
      cuantil       = paste0("q", tau),
      variable      = smooth_var
    )
}

extract_qgam_stats <- function(fit, tau, species_label) {
  m_tau <- qdo(fit, qu = tau)
  sum_m <- summary(m_tau)
  s_table <- as.data.frame(sum_m$s.table)
  
  tibble(
    Species            = species_label,
    Quantile           = tau,
    N_obs              = sum_m$n,
    Deviance_Explained = round(sum_m$dev.expl * 100, 2),
    Adj_R_squared      = round(sum_m$r.sq, 3),
    EDF_yday           = round(s_table["s(yday)", "edf"], 2),
    P_val_yday         = s_table["s(yday)", "p-value"],
    EDF_year           = round(s_table["s(decimalYear)", "edf"], 2),
    P_val_year         = s_table["s(decimalYear)", "p-value"]
  )
}

run_species <- function(raw_df, species_label, ky_fixed, kt_fixed, year_min = YEAR_MIN) {
  df <- prep_data(raw_df, year_min = year_min)
  mq_fit <- fit_mqgam_median_fixedk(df, ky = ky_fixed, kt = kt_fixed)
  
  effects_mq_all <- bind_rows(
    extract_mq_smooth(mq_fit, TAU_MED, "yday"),
    extract_mq_smooth(mq_fit, TAU_MED, "decimalYear")
  ) |>
    mutate(species = species_label)
  
  list(
    data          = df,
    mq_fit        = mq_fit,
    effects_yday  = effects_mq_all |> filter(variable == "yday"),
    effects_dyear = effects_mq_all |> filter(variable == "decimalYear")
  )
}

# ------------------------------------------------------------------------------
# 3. EXECUTION AND DATA EXPORT
# ------------------------------------------------------------------------------
eurobs_physalia       <- readRDS("data/processed/eurobs_physalia.rds")
eurobs_velella        <- readRDS("data/processed/eurobs_velella.rds")
eurobs_neutralNeuston <- readRDS("data/processed/eurobs_neutralNeuston.rds")

message("Data loaded successfully. Commencing model fitting...")

# Execute models dynamically linking to k_manual parameters
res_physalia <- run_species(eurobs_physalia, "Physalia", k_manual$ky[1], k_manual$kt[1])
res_velella  <- run_species(eurobs_velella, "Velella", k_manual$ky[2], k_manual$kt[2])
res_neutral  <- run_species(eurobs_neutralNeuston, "Neutral Neuston", k_manual$ky[3], k_manual$kt[3])

# Consolidate spatial and temporal effects
df_all <- bind_rows(
  res_physalia$data |> mutate(species = "Physalia"),
  res_velella$data  |> mutate(species = "Velella"),
  res_neutral$data  |> mutate(species = "Neutral Neuston")
)

effects_yday_all <- bind_rows(res_physalia$effects_yday, res_velella$effects_yday, res_neutral$effects_yday)
effects_year_all <- bind_rows(res_physalia$effects_dyear, res_velella$effects_dyear, res_neutral$effects_dyear)

# Consolidate and export summary statistics table
stats_table <- bind_rows(
  extract_qgam_stats(res_physalia$mq_fit, TAU_MED, "Physalia"),
  extract_qgam_stats(res_velella$mq_fit, TAU_MED, "Velella"),
  extract_qgam_stats(res_neutral$mq_fit, TAU_MED, "Neutral Neuston")
)

# Create tables directory if it doesn't exist and write CSV
if (!dir.exists("tables")) dir.create("tables")
write.csv(stats_table, "tables/01_qgam_summary_statistics.csv", row.names = FALSE)

# Export standard binary data
saveRDS(df_all, "data/processed/modelling_df_all.rds")
saveRDS(effects_yday_all, "data/processed/modelling_effects_yday.rds")
saveRDS(effects_year_all, "data/processed/modelling_effects_year.rds")
saveRDS(list(res_physalia, res_velella, res_neutral), "data/processed/mqgam_models.rds")

message("Modelling complete. Statistical table saved to 'tables/' and binaries to 'data/processed/'.")