# Data preparation scripts

Each R script in this directory reconstructs a published network meta-analysis dataset from publicly available supplementary material or open repositories. Running a script produces a harmonized CSV file saved to `inst/extdata/`.

All scripts follow the same pattern:

1. Download the raw supplementary table (manual download locations documented inline when automated retrieval is not possible).
2. Standardize column names and encodings.
3. Write the cleaned dataset to `inst/extdata/<dataset_id>.csv`.
4. Update `inst/extdata/datasets.csv` with any new metadata fields.

Ensure that datasets respect licensing requirements before committing.
