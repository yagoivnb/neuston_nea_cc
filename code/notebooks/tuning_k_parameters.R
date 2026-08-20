# ==============================================================================
# Module: tuning_k_parameters.R
# Description: Hyperparameter tuning for qGAM basis dimensions (k).
# Performs a grid-search to identify optimal k parameters for temporal and 
# seasonal smooths based on UBRE/GCV scores.
# ==============================================================================

library(dplyr)
library(lubridate)
library(mgcv)
library(qgam)

# Load subset of processed data for testing
df_physalia <- readRDS("data/processed/eurobs_physalia.rds") |>
  mutate(yday = yday(verbatimEventDate), decimalYear = decimal_date(verbatimEventDate))

# Grid parameters
K_YDAY_GRID <- 4:15
K_YEAR_GRID <- 4:10
TAU_MED <- 0.5
TOL <- 0.005

# ------------------------------------------------------------------------------
# 1. GRID SEARCH ALGORITHM
# ------------------------------------------------------------------------------
select_best_k_median <- function(data, k_yday_grid = K_YDAY_GRID, k_year_grid = K_YEAR_GRID, tol = TOL) {
  results <- list()
  
  for (ky in k_yday_grid) {
    for (kt in k_year_grid) {
      cat(sprintf("Testing ky=%d, kt=%d...\n", ky, kt))
      
      m <- try(
        qgam(
          decimalLatitude ~ s(yday, bs = "cc", k = ky) + s(decimalYear, bs = "tp", k = kt),
          data = data,
          qu   = TAU_MED
        ),
        silent = TRUE
      )
      
      if (inherits(m, "try-error")) next
      
      results[[length(results) + 1]] <- list(model = m, ky = ky, kt = kt, score = m$gcv.ubre)
    }
  }
  
  df_res <- do.call(rbind, lapply(results, function(x) data.frame(ky = x$ky, kt = x$kt, score = x$score)))
  best_score <- min(df_res$score)
  
  candidatos <- df_res |>
    filter(score <= best_score * (1 + tol)) |>
    arrange(ky + kt, ky, kt)
  
  print("--- Best Hyperparameters identified ---")
  print(candidatos[1, ])
  return(candidatos[1, ])
}

# Run the tuning (Warning: This may take significant time)
optimal_k_physalia <- select_best_k_median(df_physalia)

