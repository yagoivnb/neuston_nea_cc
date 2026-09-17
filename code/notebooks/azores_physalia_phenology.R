# ==============================================================================
# Module: azores_physalia_phenology.R
# Description: Exploratory analysis of Physalia physalis monthly reporting 
# frequency in the Azores. Applies standard Darwin Core cleaning and observer 
# bias mitigation to pre-filtered regional raw data.
# ==============================================================================

# ------------------------------------------------------------------------------
# 0. SETUP AND DEPENDENCIES
# ------------------------------------------------------------------------------
library(bdc)
library(dplyr)
library(ggplot2)
library(readr)
library(lubridate)
library(here)

set.seed(1234)

# ------------------------------------------------------------------------------
# 1. DATA INGESTION
# ------------------------------------------------------------------------------
# Assuming raw file is named 'azores_phys.csv'
raw_path <- here("data", "raw", "azores_phys.csv")

if (!file.exists(raw_path)) {
  stop("Raw dataset not found. Ensure 'azores_phys.csv' is present in 'data/raw/'.")
}

df <- read_csv(raw_path, show_col_types = FALSE)
cat(sprintf("[INFO] Initial raw records loaded: %d\n", nrow(df)))

# ------------------------------------------------------------------------------
# 2. DARWIN CORE STANDARDISATION & TEMPORAL FORMATTING
# ------------------------------------------------------------------------------
df_std <- df |>
  rename(
    occurrenceID      = id,
    verbatimEventDate = observed_on,
    references        = url,
    associatedMedia   = image_url,
    county            = place_guess,
    decimalLatitude   = latitude,
    decimalLongitude  = longitude,
    country           = place_guess,
    scientificName    = scientific_name,
    vernacularName    = common_name,
    kingdom           = iconic_taxon_name,
    taxonID           = taxon_id
  ) |>
  mutate(
    verbatimEventDate = as.Date(verbatimEventDate, format = "%Y-%m-%d"), 
    year  = as.integer(format(verbatimEventDate, "%Y")),
    # Extract month as an ordered factor (Jan, Feb, Mar...)
    month = month(verbatimEventDate, label = TRUE, abbr = TRUE)
  ) |>
  filter(year <= 2025)

# ------------------------------------------------------------------------------
# 3. BIODIVERSITY QUALITY CONTROL (bdc)
# ------------------------------------------------------------------------------
# Geographic bounding box is omitted as the dataset is intrinsically regional.
# Basic QA/QC applied to eliminate structurally corrupt records.
df_qc <- df_std |>
  bdc_coordinates_empty() |>
  bdc_eventDate_empty(eventDate = "verbatimEventDate") |>
  bdc_scientificName_empty() |>
  bdc_coordinates_outOfRange() |>
  bdc_filter_out_flags()

# ------------------------------------------------------------------------------
# 4. OBSERVER BIAS MITIGATION
# ------------------------------------------------------------------------------
azores_final <- df_qc |>
  filter(!is.na(user_id) & user_id != "",
         !is.na(user_login) & user_login != "") |>
  arrange(user_id, verbatimEventDate, scientificName) |>
  distinct(user_id, verbatimEventDate, scientificName, .keep_all = TRUE) |>
  filter(quality_grade == "research", scientificName == "Physalia physalis")

cat(sprintf("[INFO] Final research-grade Physalia records: %d\n", nrow(azores_final)))

# ------------------------------------------------------------------------------
# 5. PHENOLOGY SUMMARY & VISUALISATION
# ------------------------------------------------------------------------------
# Count occurrences per month
monthly_counts <- azores_final |>
  filter(!is.na(month)) |>
  count(month, name = "frequency")

p_phenology <- ggplot(monthly_counts, aes(x = month, y = frequency)) +
  geom_col(fill = "#7570b3", color = "black", alpha = 0.8) +
  scale_y_continuous(expand = expansion(mult = c(0, 0.05))) +
  theme_minimal(base_size = 16) +
  labs(
    title = bquote("Frequency of" ~ italic("Physalia physalis") ~ "in the Azores"),
    x = "Month", 
    y = "Number of observations"
  ) +
  theme(
    axis.title = element_text(face = "bold"),
    axis.text = element_text(color = "black"),
    panel.grid.major.x = element_blank(),
    panel.grid.minor = element_blank(),
    axis.line = element_line(color = "black", linewidth = 0.5),
    axis.ticks = element_line(color = "black", linewidth = 0.5)
  )

print(p_phenology)

# ------------------------------------------------------------------------------
# 6. EXPORT
# ------------------------------------------------------------------------------
saveRDS(azores_final, here("data", "processed", "azores_phys_clean.rds"))
ggsave(here("figures", "exploratory", "fig_S5_azores_physalia_phenology.png"), 
       plot = p_phenology, width = 8, height = 6, dpi = 300, bg = "white")

cat("\n[SUCCESS] Pipeline executed. Processed data and SVG plot saved.\n")