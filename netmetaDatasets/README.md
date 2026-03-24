# netmetaDatasets

<!-- badges: start -->
[![R-CMD-check](https://github.com/OWNER/REPO/actions/workflows/R-CMD-check.yaml/badge.svg)](https://github.com/OWNER/REPO/actions/workflows/R-CMD-check.yaml)
<!-- badges: end -->

`netmetaDatasets` is a devtools-friendly R package that curates published
network meta-analysis (NMA) case studies alongside metadata and
reproducible processing scripts. The package aims to become the largest
openly licensed repository of NMA datasets for methodological research,
teaching, and software benchmarking.

## Features

- Real-world NMA datasets sourced from peer-reviewed systematic reviews
  and leading R packages focused on network evidence synthesis.
- Transparent provenance, including citations, access instructions, and
  extraction notes for each dataset.
- Tidy loaders that return standardized arm-based or contrast-based
  tables, regardless of whether the data ship with this package or live
  in an upstream dependency.
- Lightweight unit tests verifying loader behavior and schema
  consistency.
- Expandable architecture allowing contributors to add new case studies
  safely with full provenance tracking.

## Repository scale (v0.0.0.9000)

The registry currently indexes 100 real-world network meta-analysis
case studies spanning psychiatry, oncology, rheumatology, infectious
disease, endocrinology, dermatology, and more. Three datasets are
bundled directly as CSV files for immediate use. The remaining 97
entries reference datasets hosted in well-established R packages such as
`BUGSnet`, `gemtc`, `netmeta`, `pcnetmeta`, and `nmadata`, ensuring the
community can leverage a much broader catalogue without duplicating
storage.

A quick glance at the locally bundled examples:

| Dataset ID | Clinical area | Outcome | Design | Source |
|------------|---------------|---------|--------|--------|
| `smoking_cessation_2013` | Smoking cessation | Abstinence at ≥6 months | Arm-based binary | Cahill et al. (2013) Lancet |
| `antidepressants_2018` | Major depressive disorder | Response rate | Arm-based binary | Cipriani et al. (2018) Lancet |
| `diabetes_glucose_2016` | Type 2 diabetes | Change in HbA1c | Arm-based continuous | Palmer et al. (2016) Lancet |

Use `list_nma_datasets(include_remote = TRUE)` to explore the full
catalogue with provenance, access modality, and licensing metadata. Set
`include_remote = FALSE` to focus only on the CSV assets shipped with
this package.

## Getting started

```r
# install.packages("devtools")
devtools::install_github("example/netmetaDatasets")

library(netmetaDatasets)
list_nma_datasets()
smoking <- load_nma_dataset("smoking_cessation_2013")
nma_dataset_overview(smoking)
```

For datasets that live in external CRAN packages, call
`load_nma_dataset("<dataset_id>", install_if_missing = TRUE)` to fetch
the relevant dependency on demand.

### Auditing accessibility

Researchers can confirm which datasets are immediately usable within
their current R installation by running `audit_nma_datasets()`. The
audit attempts to load every registry entry, reports successful loads,
and captures error messages for datasets that require additional
packages or manual intervention.

```r
audit <- audit_nma_datasets()
subset(audit, status != "ok")
```

Pass `include_remote = FALSE` to focus only on the CSV assets bundled in
this repository, or `install_if_missing = TRUE` to let the function
install required CRAN packages on the fly when network access is
available.

### Standardized schema

All loaders funnel raw objects through a harmonization layer so that
columns use consistent names regardless of the original source. Arm
binary studies always expose `study_id`, `treatment`, `responders`, and
`sample_size`, while continuous outcomes return `mean_change`,
`sd_change`, and `sample_size`. Contrast-level summaries for hazard
ratios, odds ratios, or standardized mean differences similarly surface
canonical column names (`log_hazard_ratio`, `se_log_hazard_ratio`, etc.)
which means downstream code can rely on a single schema even when data
originate from different R packages.

### Current limitations

- Only the three CSV files listed above ship with this repository. Every
  other entry in `inst/extdata/datasets.csv` points to a dataset that is
  expected to live in an external CRAN package; if those package/dataset
  combinations do not exist or have been renamed upstream,
  `load_nma_dataset()` and `audit_nma_datasets()` will return errors.
- The registry has not been de-duplicated or independently validated. It
  is possible (and likely) that multiple rows reference the same evidence
  set or cite placeholder metadata copied from package indices rather than
  the original publications.
- The installation snippet in this README uses the placeholder GitHub
  path `example/netmetaDatasets`. Replace it with the actual repository
  slug before calling `devtools::install_github()`.
- The status badge above assumes the repository lives at
  `OWNER/REPO`. Update the badge URL once you push to your GitHub
  account so it reflects the actual workflow results.
- Automated checks such as `devtools::check()` or the testthat suite have
  not been executed in this development environment because R is not
  available in the container. Run those checks locally before relying on
  the package in production work. The new GitHub Actions workflow will
  execute `R CMD check` once the repository is published with a valid
  slug.

## Contributing datasets

1. Fork the repository and create a new branch.
2. Add raw extraction scripts in `data-raw/` with reproducible code for
   obtaining the dataset.
3. Place harmonized CSV files inside `inst/extdata/` following the naming
   convention `<dataset_id>.csv`. For datasets sourced from other
   packages, document the `package::dataset` reference in the registry.
4. Update the registry in `inst/extdata/datasets.csv` with metadata,
   citation, access modality, and license details.
5. Run `devtools::check()` to validate the package before submitting a
   pull request.

## Licensing

All code is MIT licensed. Dataset licensing varies; see
`inst/extdata/datasets.csv` for dataset-specific licensing terms and
links to upstream sources.
