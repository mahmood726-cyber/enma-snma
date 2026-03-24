## Antidepressants for major depressive disorder (Cipriani 2018)
## Source: Cipriani A, et al. Lancet. 2018;391:1357-1366. Appendix tables pp. 51-60.

library(dplyr)
library(readr)
library(stringr)

# Manual extraction: Appendix tables provide responders and sample sizes by study.
# Enter values into `raw/antidepressants_responses.csv` with columns:
# study_id, treatment, responders, sample_size.

raw <- readr::read_csv("raw/antidepressants_responses.csv", show_col_types = FALSE)

clean <- raw |>
  mutate(treatment = stringr::str_replace_all(treatment, " ", ""))

readr::write_csv(clean, file.path("inst", "extdata", "antidepressants_2018.csv"))
