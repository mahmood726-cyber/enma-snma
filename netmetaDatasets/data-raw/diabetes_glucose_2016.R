## Type 2 diabetes glucose control (Palmer 2016)
## Source: Palmer SC, et al. Lancet. 2016;389:733-743. Supplementary table S5.

library(dplyr)
library(readr)

# Manual preparation: Table S5 reports mean change and SD by study arm.
# Enter data into `raw/diabetes_hba1c.csv` with columns
# study_id, treatment, mean_change, sd_change, sample_size.

raw <- readr::read_csv("raw/diabetes_hba1c.csv", show_col_types = FALSE)

clean <- raw |>
  mutate(treatment = gsub(" ", "", treatment))

readr::write_csv(clean, file.path("inst", "extdata", "diabetes_glucose_2016.csv"))
