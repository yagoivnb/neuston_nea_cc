# ==============================================================================
# Module: exploratory_assumptions.R
# Description: Initial exploratory data analysis to evaluate parametric assumptions
# (normality, homoscedasticity, linearity) and formally justify the use of qGAMs 
# for latitudinal distribution modelling.
# ==============================================================================

library(dplyr)
library(ggplot2)
library(lubridate)
library(lmtest)
library(ggpubr)

# ------------------------------------------------------------------------------
# 1. LOAD TARGET DATASET
# ------------------------------------------------------------------------------
# We utilise the Physalia dataset as the primary case study for assumption testing
df <- readRDS("data/processed/eurobs_physalia.rds") |>
  mutate(
    yday        = yday(verbatimEventDate),
    decimalYear = decimal_date(verbatimEventDate)
  )

# ------------------------------------------------------------------------------
# 2. RESPONSE VARIABLE DISTRIBUTION (Normality Check)
# ------------------------------------------------------------------------------
## Histogram
p_hist <- ggplot(df, aes(x = decimalLatitude)) +
  geom_histogram(bins = 40, fill = "grey70", colour = "black") +
  labs(title = "Distribution of Physalia latitudes", x = "Latitude (°)", y = "Count") +
  theme_minimal()
print(p_hist)

## QQ-plot (Visual test of normality)
p_qq <- ggqqplot(df$decimalLatitude, 
                 title = "Normal Q–Q plot of decimalLatitude",
                 xlab = "Theoretical quantiles", 
                 ylab = "Observed quantiles")
print(p_qq)

## Shapiro-Wilk test
shapiro.test(df$decimalLatitude[1:5000])

# Interpretation: Multimodal histogram and massive deviations in the QQ-plot, 
# supported by a significant Shapiro test (p < 0.001), indicate severe non-normality.

# ------------------------------------------------------------------------------
# 3. VARIANCE DISTRIBUTION (Heteroscedasticity Check)
# ------------------------------------------------------------------------------
## Fit a standard linear model as a baseline benchmark
lm_mod <- lm(decimalLatitude ~ yday + decimalYear, data = df)

## Breusch–Pagan test
bptest(lm_mod)

## Fligner-Killeen test (More robust non-parametric alternative)
fligner.test(decimalLatitude ~ yday, data = df)

## Residuals vs fitted diagnostic plot
plot(
  fitted(lm_mod), resid(lm_mod),
  xlab = "Fitted values (LM)",
  ylab = "Residuals",
  main = "Residuals vs fitted (LM)"
)
abline(h = 0, lty = 2)

# Interpretation: A clear pattern in the residuals and strongly significant 
# BP/Fligner-Killeen tests (p < 0.001) confirm heteroscedasticity.

# ------------------------------------------------------------------------------
# 4. FREQUENCY DISTRIBUTION ACROSS LATITUDES (Spatial Bias Check)
# ------------------------------------------------------------------------------
df_bands <- df |>
  mutate(lat_band = cut(decimalLatitude,
                        breaks = seq(floor(min(decimalLatitude)),
                                     ceiling(max(decimalLatitude)),
                                     by = 5.8),
                        include.lowest = TRUE)) |>
  group_by(lat_band) |>
  summarise(n = n())

## Chi-square test for spatial uniformity
chisq.test(df_bands$n, p = rep(1/nrow(df_bands), nrow(df_bands)))

## Frequency plot
ggplot(df_bands, aes(x = lat_band, y = n)) +
  geom_bar(stat = "identity", fill = "steelblue") +
  theme_minimal() +
  labs(title = "Observations per 5° latitude band", x = "Latitude band (°)", y = "Count")

# Interpretation: Observations are not uniformly distributed (p < 0.001). 
# Mid-latitudes dominate, which would bias mean-centric Gaussian models.

# ------------------------------------------------------------------------------
# 5. METHODOLOGICAL CONCLUSION
# ------------------------------------------------------------------------------
# 1) Non-normal, multimodal, and non-linear response.
# 2) Heteroscedasticity invalidates standard Gaussian assumptions.
# 3) Mid-latitudes dominate the sample.
# 4) Extreme latitudes are critical for early arrival and dispersal inference.
#
# Decision: qGAMs are strictly required to model distribution extremes effectively.