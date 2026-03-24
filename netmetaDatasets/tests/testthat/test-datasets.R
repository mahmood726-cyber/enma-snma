test_that("list_nma_datasets returns metadata", {
  meta <- list_nma_datasets()
  expect_s3_class(meta, "tbl_df")
  expect_gte(nrow(meta), 100)
  expect_true(all(c("dataset_id", "title", "license", "available_locally") %in% names(meta)))

  local_only <- list_nma_datasets(include_remote = FALSE)
  expect_lt(nrow(local_only), nrow(meta))
  expect_true(all(local_only$available_locally))
})

test_that("load_nma_dataset fetches csv", {
  smoking <- load_nma_dataset("smoking_cessation_2013")
  expect_s3_class(smoking, "tbl_df")
  expect_true(all(c("study_id", "treatment") %in% names(smoking)))

  diabetes <- load_nma_dataset("diabetes_glucose_2016")
  expect_true(all(c("mean_change", "sd_change", "sample_size") %in% names(diabetes)))
})

test_that("standardization harmonizes synonymous columns", {
  record <- tibble::tibble(dataset_id = "synthetic", design = "arm_binary")
  raw <- tibble::tibble(
    studlab = c("S1", "S1"),
    treat = c("A", "B"),
    r = c("3", "5"),
    n = c("10", "12")
  )

  harmonized <- netmetaDatasets:::standardize_dataset_structure(raw, record)
  expect_true(all(c("study_id", "treatment", "responders", "sample_size") %in% names(harmonized)))
  expect_equal(harmonized$responders, c(3, 5))
  expect_equal(harmonized$sample_size, c(10, 12))
})

test_that("load_nma_dataset warns for external requirements", {
  expect_error(
    load_nma_dataset("ra_biologics_2013"),
    "Package 'BUGSnet' is required",
    fixed = TRUE
  )
})

test_that("nma_dataset_overview identifies outcome type", {
  smoking <- load_nma_dataset("smoking_cessation_2013")
  smoking_summary <- nma_dataset_overview(smoking)
  expect_equal(smoking_summary$type, "binary")
  expect_true("response_rate" %in% names(smoking_summary$summary))

  diabetes <- load_nma_dataset("diabetes_glucose_2016")
  diabetes_summary <- nma_dataset_overview(diabetes)
  expect_equal(diabetes_summary$type, "continuous")
  expect_true("pooled_mean" %in% names(diabetes_summary$summary))
})

test_that("audit_nma_datasets reports local availability", {
  audit <- audit_nma_datasets(include_remote = FALSE)
  expect_s3_class(audit, "tbl_df")
  expect_true(all(audit$status == "ok"))
  expect_true(all(audit$rows > 0))
  expect_true(all(audit$columns >= 4))
})

test_that("audit_nma_datasets captures missing packages", {
  skip_if(requireNamespace("BUGSnet", quietly = TRUE), "BUGSnet is available")
  audit <- audit_nma_datasets()
  target <- dplyr::filter(audit, dataset_id == "ra_biologics_2013")
  expect_equal(nrow(target), 1)
  expect_equal(target$status, "error")
  expect_match(target$message, "Package 'BUGSnet' is required", fixed = TRUE)
})
