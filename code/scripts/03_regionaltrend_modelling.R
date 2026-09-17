# ==============================================================================
# @file:    03_regionaltrend_modelling.r
# @author:  Yago Iván-Baragaño (ivanyago@uniovi.es)
# @funding: Severo Ochoa Ph.D. program (Principado de Asturias, NAC-AT-PUB-ASV-2025 BP24-109)
# @cite:    
# @brief:   Core modelling pipeline fitting beta-binomial GLMMs
# Temporal changes in occurrence proportions across latitudinal bands
# Outputs are saved as static binary objects for visualisation.
# ==============================================================================

# ------------------------------------------------------------------------------
# 0. SETUP AND DEPENDENCIES
# ------------------------------------------------------------------------------
library(glmmTMB)
library(DHARMa)
library(emmeans)
library(dplyr)
library(lubridate)
library(here)

# ------------------------------------------------------------------------------
# 1. MASTER CONTROL BLOCK
# ------------------------------------------------------------------------------
TARGET_SPECIES <- c("Physalia physalis")
FOCAL_REGION   <- "Bay of Biscay"

START_YEAR <- 2014
LAT_MIN    <- 26
LAT_MAX    <- 56

BAND_BREAKS <- c(26, 36, 43.2, 48.5, 56)
BAND_LABELS <- c(
  "Canaries and Madeira",
  "Atlantic Iberian Coast",
  "Bay of Biscay",
  "Celtic Seas"
)

# ------------------------------------------------------------------------------
# 2. DATA INGESTION & BINOMIAL PREPARATION
# ------------------------------------------------------------------------------
df <- readRDS(here("data", "processed", "eurobs_coastalsp_master.rds"))

df_prep <- df |>
  mutate(
    year      = year(verbatimEventDate),
    lat       = as.numeric(decimalLatitude),
    is_target = (scientificName == TARGET_SPECIES),
    lat_band_regional = cut(lat, breaks = BAND_BREAKS, right = TRUE, 
                            include.lowest = TRUE, labels = BAND_LABELS)
  ) |>
  filter(!is.na(lat), lat >= LAT_MIN, lat <= LAT_MAX) |>
  filter(!is.na(year), year >= START_YEAR)

bands_mod <- df_prep |>
  filter(!is.na(lat_band_regional)) |>
  group_by(year, lat_band_regional) |>
  summarise(
    n_total   = n(),
    n_target  = sum(is_target, na.rm = TRUE),
    .groups   = "drop"
  ) |>
  mutate(
    year_centered     = year - mean(year, na.rm = TRUE),
    lat_band_regional = factor(lat_band_regional, levels = BAND_LABELS),
    highlight         = ifelse(lat_band_regional == FOCAL_REGION, FOCAL_REGION, "Other")
  ) |>
  arrange(lat_band_regional, year)

cat(sprintf("\n[INFO] Executing statistical pipeline for: %s\n", TARGET_SPECIES))

# ------------------------------------------------------------------------------
# 3. BETA-BINOMIAL GLMM FITTING
# ------------------------------------------------------------------------------
m_betabinom <- glmmTMB(
  cbind(n_target, n_total - n_target) ~ year_centered * lat_band_regional,
  family = betabinomial(link = "logit"),
  data   = bands_mod
)

# ------------------------------------------------------------------------------
# 4. POST-HOC TESTING & DIAGNOSTICS
# ------------------------------------------------------------------------------
band_trends <- emtrends(m_betabinom, specs = ~ lat_band_regional, var = "year_centered")

cat("\n[DIAGNOSTIC] Simulating DHARMa residuals for dispersion validation...\n")
sim_res_betabinom <- simulateResiduals(m_betabinom, plot = FALSE)
testDispersion(sim_res_betabinom)

# ------------------------------------------------------------------------------
# 5. STATISTICAL EXTRACTION & EXPORT
# ------------------------------------------------------------------------------
# 5.1 Extract Fixed Effects (Global Base Model)
fixed_eff <- as.data.frame(summary(m_betabinom)$coefficients$cond) |>
  tibble::rownames_to_column("Parameter") |>
  rename(Estimate = Estimate, Std_Error = `Std. Error`, Z_ratio = `z value`, P_value = `Pr(>|z|)`) |>
  mutate(Component = "Fixed Effects (Logit)") |>
  select(Component, Parameter, Estimate, Std_Error, Z_ratio, P_value)

# 5.2 Extract Regional Slopes (Marginal Trends)
slopes_df <- as.data.frame(test(band_trends)) |>
  rename(Parameter = lat_band_regional, Estimate = year_centered.trend, 
         Std_Error = SE, Z_ratio = z.ratio, P_value = p.value) |>
  mutate(Component = "Regional Slopes (emtrends)") |>
  select(Component, Parameter, Estimate, Std_Error, Z_ratio, P_value)

# 5.3 Extract Contrasts against Focal Region
contrasts_df <- as.data.frame(contrast(band_trends, method = "trt.vs.ctrl", ref = FOCAL_REGION, adjust = "Holm")) |>
  rename(Parameter = contrast, Estimate = estimate, 
         Std_Error = SE, Z_ratio = z.ratio, P_value = p.value) |>
  mutate(Component = sprintf("Contrasts vs %s (Holm-adj)", FOCAL_REGION)) |>
  select(Component, Parameter, Estimate, Std_Error, Z_ratio, P_value)

# Assemble Master Table
master_stats <- bind_rows(fixed_eff, slopes_df, contrasts_df) |>
  mutate(across(where(is.numeric), ~ round(.x, 4)))

if (!dir.exists(here("tables"))) dir.create(here("tables"))
write.csv(master_stats, here("tables", "03_regionaltrend_statistics.csv"), row.names = FALSE)

# ------------------------------------------------------------------------------
# 6. PREDICTIVE GRIDDING & BINARY EXPORT
# ------------------------------------------------------------------------------
pred_grid <- bands_mod |>
  distinct(lat_band_regional, year, year_centered, highlight) |>
  arrange(lat_band_regional, year)

preds <- predict(m_betabinom, newdata = pred_grid, type = "link", se.fit = TRUE)

pred_grid <- pred_grid |>
  mutate(
    fit   = plogis(preds$fit),
    lower = plogis(preds$fit - 1.96 * preds$se.fit),
    upper = plogis(preds$fit + 1.96 * preds$se.fit)
  )

saveRDS(bands_mod, here("data", "processed", "regionaltrend_bands_mod.rds"))
saveRDS(pred_grid, here("data", "processed", "regionaltrend_pred_grid.rds"))
saveRDS(m_betabinom, here("data", "processed", "regionaltrend_model.rds"))

cat(sprintf("\n[SUCCESS] %s modelling complete. Matrices and tabular stats exported.\n", TARGET_SPECIES))
