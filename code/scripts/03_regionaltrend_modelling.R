# ==============================================================================
# Module: 03_regionaltrend_modelling.R
# Description: Statistical pipeline to analyse temporal changes in occurrence 
# proportions across latitudinal bands. Implements beta-binomial GLMM modelling 
# to handle overdispersion, post-hoc statistical testing, and predictive gridding.
# Outputs are saved as static binary objects for visualisation.
# ==============================================================================

library(glmmTMB)
library(DHARMa)
library(emmeans)
library(dplyr)
library(lubridate)
library(here)

# ------------------------------------------------------------------------------
# 1. MASTER CONTROL BLOCK
# ------------------------------------------------------------------------------
TARGET_SPECIES <- "Physalia physalis"
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
# here() dynamically locates the project root regardless of the working directory
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

cat("\n[MODEL] Beta-Binomial GLMM Summary:\n")
print(summary(m_betabinom))

# ------------------------------------------------------------------------------
# 4. POST-HOC TESTING & DIAGNOSTICS
# ------------------------------------------------------------------------------
band_trends <- emtrends(m_betabinom, specs = ~ lat_band_regional, var = "year_centered")

cat("\n[POST-HOC] Pairwise comparisons of temporal slopes (Tukey-adjusted):\n")
print(contrast(band_trends, method = "pairwise", adjust = "Tukey"))

cat(sprintf("\n[POST-HOC] Directed comparisons vs %s (Holm-adjusted):\n", FOCAL_REGION))
print(contrast(band_trends, method = "trt.vs.ctrl", ref = FOCAL_REGION, adjust = "Holm"))

cat("\n[DIAGNOSTIC] Simulating DHARMa residuals for dispersion validation...\n")
sim_res_betabinom <- simulateResiduals(m_betabinom, plot = FALSE)
testDispersion(sim_res_betabinom)

# ------------------------------------------------------------------------------
# 5. PREDICTIVE GRIDDING & EXPORT
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

# Save static objects for the figure generation script
saveRDS(bands_mod, here("data", "processed", "regionaltrend_bands_mod.rds"))
saveRDS(pred_grid, here("data", "processed", "regionaltrend_pred_grid.rds"))
saveRDS(m_betabinom, here("data", "processed", "regionaltrend_model.rds"))

cat("\n[SUCCESS] Modelling complete. Matrices exported to data/processed/.\n")
