# ==============================================================================
# Module: 04_regionaltrend_figures.R
# Description: Visualisation module for regional latitudinal band trends.
# Ingests pre-computed beta-binomial predictive grids to generate 
# publication-grade multipanel plots.
# ==============================================================================

library(ggplot2)
library(scales)
library(ggh4x)
library(stringr)
library(dplyr)
library(here)

# ------------------------------------------------------------------------------
# 1. MASTER CONTROL & DATA INGESTION
# ------------------------------------------------------------------------------
# Ensures aesthetic labels match the targeted species and region dynamically
TARGET_SPECIES <- "Physalia physalis"
FOCAL_REGION   <- "Bay of Biscay"
START_YEAR     <- 2014

# Ingest static mathematical outputs
bands_mod <- readRDS(here("data", "processed", "regionaltrend_bands_mod.rds"))
pred_grid <- readRDS(here("data", "processed", "regionaltrend_pred_grid.rds"))

# ------------------------------------------------------------------------------
# 2. AESTHETIC CONFIGURATIONS & PLOTTING
# ------------------------------------------------------------------------------
common_y_panels <- c("Atlantic Iberian Coast", "Bay of Biscay", "Celtic Seas")

p_fit_pub <- ggplot() +
  geom_ribbon(data = pred_grid, aes(x = year, ymin = lower, ymax = upper, fill = highlight), alpha = 0.25) +
  geom_line(data = pred_grid, aes(x = year, y = fit, colour = highlight), linewidth = 1.1) +
  geom_point(data = bands_mod, aes(x = year, y = n_target / n_total, colour = highlight, size = sqrt(n_total)), alpha = 0.7) +
  
  scale_size_continuous(range = c(1.5, 4), guide = "none") +
  scale_colour_manual(values = setNames(c("black", "grey40"), c(FOCAL_REGION, "Other")), guide = "none") +
  scale_fill_manual(values = setNames(c("black", "grey80"), c(FOCAL_REGION, "Other")), guide = "none") +
  
  facet_wrap2(~ lat_band_regional, scales = "free_y", ncol = 2, axes = "all", remove_labels = "x") +
  
  scale_x_continuous(limits = c(START_YEAR, 2025), breaks = seq(START_YEAR, 2024, by = 2), expand = expansion(mult = c(0, 0.01))) +
  scale_y_continuous(limits = c(0, 0.40), breaks = seq(0.08, 0.32, by = 0.08), labels = label_percent(accuracy = 1), expand = expansion(mult = c(0.02, 0.02))) +
  
  facetted_pos_scales(
    y = list(
      lat_band_regional %in% common_y_panels ~ scale_y_continuous(
        limits = c(0, 0.15), breaks = seq(0.03, 0.12, by = 0.03), 
        labels = label_percent(accuracy = 1), expand = expansion(mult = c(0, 0))
      )
    )
  ) +
  
  labs(
    x = NULL,
    y = bquote("Reporting rate of " * italic(.(TARGET_SPECIES)))
  ) +
  theme_minimal(base_size = 26) +
  theme(
    axis.line           = element_line(linewidth = 0.5),
    axis.ticks          = element_line(linewidth = 0.5),
    axis.ticks.length   = unit(1.5, "mm"),
    panel.grid.minor    = element_blank(),
    strip.text          = element_text(face = "bold", size = 26),
    panel.spacing       = unit(1, "lines"),
    axis.title.y        = element_text(face = "bold"),
    axis.text.x         = element_text(angle = 0, hjust = 0.5, vjust = 1, size = 20), 
    axis.text.y         = element_text(size = 22), 
    axis.text.x.top     = element_blank(),
    plot.title.position = "plot"
  )

# ------------------------------------------------------------------------------
# 3. EXPORT
# ------------------------------------------------------------------------------
export_name <- sprintf("fig_03_regional_%s.png", str_replace_all(tolower(TARGET_SPECIES), " ", "_"))
ggsave(here("figures", "publication", export_name), plot = p_fit_pub, width = 16, height = 10, dpi = 300, bg = "white")

cat(sprintf("\n[SUCCESS] Figure exported to: figures/publication/%s\n", export_name))

