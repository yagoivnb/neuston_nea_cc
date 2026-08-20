# ==============================================================================
# Module: 00_preprocess.R
# Description: Data preparation and standardisation of coastal neuston records.
#   This script cleans raw iNaturalist observations from 'coastalsp_25_raw.csv'
#   according to Darwin Core standards, applies spatial bounding boxes for the 
#   North East Atlantic, mitigates observer bias, and implements quality control.
#   Outputs are saved as compressed .rds files for subsequent modelling.
# ==============================================================================

# ------------------------------------------------------------------------------
# 0. SETUP AND DEPENDENCIES
# ------------------------------------------------------------------------------
required_packages <- c(
  "bdc", "dplyr", "ggplot2", 
  "rnaturalearth", "rnaturalearthdata", "readr"
)

for (pkg in required_packages) {
  if (!requireNamespace(pkg, quietly = TRUE)) install.packages(pkg)
}

library(bdc)
library(dplyr)
library(ggplot2)
library(rnaturalearth)
library(rnaturalearthdata)
library(readr)

set.seed(1234)

# ------------------------------------------------------------------------------
# 1. LOAD RAW DATASET
# ------------------------------------------------------------------------------
# The raw CSV must be placed in the data/raw/ directory before execution.
raw_path <- "data/raw/coastalsp_25_raw.csv"

if (!file.exists(raw_path)) {
  stop("Raw data file not found. Ensure 'coastalsp_25_raw.csv' is in 'data/raw/'.")
}

# Direct ingestion of the raw dataset
df <- read_csv(raw_path, show_col_types = FALSE)
message("Initial raw records loaded: ", nrow(df))

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
    year = as.integer(format(verbatimEventDate, "%Y"))
  ) |>
  filter(year <= 2025)

# ------------------------------------------------------------------------------
# 3. SPATIAL FILTERING (ATLANTIC EUROPE BOUNDING BOXES)
# ------------------------------------------------------------------------------
# Select primary Atlantic European coastal region limits
df_spatial <- df_std |>
  filter(decimalLatitude >= 26 & decimalLatitude <= 56,
         decimalLongitude >= -19 & decimalLongitude <= 1)

# Exclude Mediterranean, Northern, and African regions
exclude_box <- function(data, box) {
  data[!(data$decimalLatitude >= box$min_lat & data$decimalLatitude <= box$max_lat &
           data$decimalLongitude >= box$min_lon & data$decimalLongitude <= box$max_lon), ]
}

boxes_to_exclude <- list(
  med1 = list(min_lat = 34, max_lat = 42, min_lon = -5.583, max_lon = 11),
  med2 = list(min_lat = 38, max_lat = 45, min_lon = 2, max_lon = 11),
  nor1 = list(min_lat = 51, max_lat = 56, min_lon = -2, max_lon = 2),
  nor2 = list(min_lat = 55.5, max_lat = 56.5, min_lon = -4, max_lon = 2),
  afr  = list(min_lat = 26.6, max_lat = 35.9, min_lon = -13.2, max_lon = -5.2)
)

for (box in boxes_to_exclude) {
  df_spatial <- exclude_box(df_spatial, box)
}

# ------------------------------------------------------------------------------
# 4. BIODIVERSITY DATA QUALITY CONTROL (bdc)
# ------------------------------------------------------------------------------
df_qc <- df_spatial |>
  bdc_coordinates_empty() |>
  bdc_eventDate_empty(eventDate = "verbatimEventDate") |>
  bdc_scientificName_empty() |>
  bdc_coordinates_outOfRange() |>
  bdc_filter_out_flags()

# ------------------------------------------------------------------------------
# 5. MITIGATION OF OBSERVER BIAS & DATA GRADE
# ------------------------------------------------------------------------------
df_final <- df_qc |>
  filter(!is.na(user_id) & user_id != "",
         !is.na(user_login) & user_login != "") |>
  # Retain a single record per user, date, and species to prevent overreporting
  arrange(user_id, verbatimEventDate, scientificName) |>
  distinct(user_id, verbatimEventDate, scientificName, .keep_all = TRUE) |>
  # Restrict strictly to Research Grade observations
  filter(quality_grade == "research")

message("Final records after spatial, QC, and observer bias filtering: ", nrow(df_final))

# ------------------------------------------------------------------------------
# 6. VISUAL DIAGNOSTICS (Optional verification)
# ------------------------------------------------------------------------------
world <- ne_countries(scale = "medium", returnclass = "sf")

diagnostic_plot <- ggplot() +
  geom_sf(data = world, fill = "gray90", color = "gray75", linewidth = 0.2) +
  geom_point(data = df_final, aes(x = decimalLongitude, y = decimalLatitude),
             color = "blue", alpha = 0.5, size = 1) +
  coord_sf(xlim = c(-20, 5), ylim = c(25, 60), expand = FALSE) +
  theme_minimal() +
  labs(title = "Filtered Coastal Species Observations - NEA",
       x = "Longitude", y = "Latitude")

# Save diagnostic map to exploratory figures directory
ggsave("figures/exploratory/map_filtered_observations.png", plot = diagnostic_plot, 
       width = 8, height = 8, dpi = 300, bg = "white")

# ------------------------------------------------------------------------------
# 7. TAXONOMIC SUBSETTING & EXPORT TO PROCESSED DIRECTORY
# ------------------------------------------------------------------------------
# Target species
eurobs_physalia <- df_final |> filter(scientificName == "Physalia physalis")
eurobs_velella  <- df_final |> filter(scientificName == "Velella velella")

# Neutral neuston group
neutral_taxa <- c(
  "Lepas anatifera", "Lepas anserifera", "Lepas pectinata",
  "Dosima fascicularis", "Glaucus atlanticus", 
  "Janthina janthina", "Porpita porpita"
)
eurobs_neutralNeuston <- df_final |> filter(scientificName %in% neutral_taxa)

# Export as .rds to preserve object structure and dates for downstream modelling
saveRDS(df_final, "data/processed/eurobs_coastalsp_master.rds")
saveRDS(eurobs_physalia, "data/processed/eurobs_physalia.rds")
saveRDS(eurobs_velella, "data/processed/eurobs_velella.rds")
saveRDS(eurobs_neutralNeuston, "data/processed/eurobs_neutralNeuston.rds")

message("Processing complete. Datasets successfully saved to 'data/processed/'.")
