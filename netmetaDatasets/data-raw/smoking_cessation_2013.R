## Smoke cessation pharmacotherapies (Cahill 2013)
## Source: Cahill K, et al. BMJ 2013;346:f1435 and supplementary appendix table 3

library(dplyr)
library(readr)
library(tidyr)

# Manual step: download the supplementary spreadsheet from
# https://www.bmj.com/content/bmj/suppl/2013/04/04/bmj.f1435.DC1/cahk031172.ww1_default.pdf
# Extract the abstinence counts for each arm at ≥6 months and save as CSV `raw/smoking_abstinence.csv`.

raw <- readr::read_csv("raw/smoking_abstinence.csv", show_col_types = FALSE)

clean <- raw |>
  janitor::clean_names() |>
  transmute(
    study_id = study,
    treatment = gsub(" ", "", treatment),
    responders = abstinent,
    sample_size = total
  )

readr::write_csv(clean, file.path("inst", "extdata", "smoking_cessation_2013.csv"))
