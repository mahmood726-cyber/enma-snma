# ============================================================================
# NMA Methods Research: Data Audit & Fix Script (Step 1)
# ============================================================================
# Purpose: Audit all datasets, identify issues, and create fix recipes
# ============================================================================

# Set working directory -- relative to this script's location
setwd(file.path(dirname(sys.frame(1)$ofile %||% "."), ".."))

# Load required packages
suppressPackageStartupMessages({
  library(dplyr)
  library(tidyr)
  library(readr)
})

cat("\n")
cat("=================================================================\n")
cat("  NMA DATA AUDIT & FIX - Step 1\n")
cat("=================================================================\n")
cat("\n")

# ============================================================================
# SECTION 1: Audit all CSV files
# ============================================================================

cat("Section 1: Auditing CSV files...\n\n")

# Define directories
nmadatasets_dir <- "nmadatasets/inst/extdata"
netmeta_dir <- "netmetaDatasets/inst/extdata"

# Get all CSV files
nmadatasets_files <- list.files(nmadatasets_dir, pattern = "\\.csv$", full.names = TRUE)
netmeta_files <- list.files(netmeta_dir, pattern = "\\.csv$", full.names = TRUE)

all_files <- c(nmadatasets_files, netmeta_files)

cat(sprintf("Found %d CSV files to audit\n\n", length(all_files)))

# Audit function
audit_csv <- function(filepath) {
  result <- list(
    file = basename(filepath),
    path = filepath,
    status = "OK",
    n_rows = 0,
    n_cols = 0,
    columns = character(),
    issues = character(),
    sample_data = NULL
  )

  tryCatch({
    df <- read.csv(filepath, stringsAsFactors = FALSE, nmax = 100)

    result$n_rows <- nrow(df)
    result$n_cols <- ncol(df)
    result$columns <- names(df)

    # Check for issues
    # 1. Check for NA values
    for (col in names(df)) {
      na_count <- sum(is.na(df[[col]]))
      if (na_count > 0) {
        result$issues <- c(result$issues,
          sprintf("Column '%s': %d NA values (%.1f%%)",
            col, na_count, 100*na_count/nrow(df)))
      }
    }

    # 2. Check for empty treatment names
    if ("treatment" %in% names(df)) {
      empty_treatments <- df$treatment == "" | df$treatment == " " | is.na(df$treatment)
      if (any(empty_treatments)) {
        result$issues <- c(result$issues,
          sprintf("%d empty treatment labels", sum(empty_treatments)))
      }

      # Check for placeholder labels
      placeholder_pattern <- "^[0-9]+$|^[A-D]$"
      if (any(grepl(placeholder_pattern, df$treatment))) {
        result$issues <- c(result$issues,
          "Contains placeholder treatment labels (numbers or A-D)")
      }
    }

    # 3. Check for empty study names
    if ("study" %in% names(df)) {
      empty_studies <- df$study == "" | df$study == " " | is.na(df$study)
      if (any(empty_studies)) {
        result$issues <- c(result$issues,
          sprintf("%d empty study labels", sum(empty_studies)))
      }

      # Check for placeholder study IDs
      placeholder_pattern <- "^[0-9]+$"
      if (any(grepl(placeholder_pattern, df$study))) {
        result$issues <- c(result$issues,
          "Contains numeric/placeholder study IDs")
      }
    }

    # 4. Check for duplicates
    if (all(c("study", "treatment") %in% names(df))) {
      n_dups <- sum(duplicated(df[, c("study", "treatment")]))
      if (n_dups > 0) {
        result$issues <- c(result$issues,
          sprintf("%d duplicate (study, treatment) rows", n_dups))
      }
    }

    # 5. Check if file is empty
    if (nrow(df) == 0) {
      result$status <- "EMPTY"
      result$issues <- c(result$issues, "File is empty")
    } else if (length(result$issues) > 0) {
      result$status <- "ISSUES"
    }

    # Store sample data
    result$sample_data <- head(df, 3)

  }, error = function(e) {
    result$status <- "ERROR"
    result$issues <- as.character(e$message)
  })

  return(result)
}

# Run audit on all files
audit_results <- lapply(all_files, audit_csv)

# Summarize by status
status_summary <- table(sapply(audit_results, function(x) x$status))

cat("Audit Summary:\n")
print(status_summary)
cat("\n")

# Group by package
cat("Files by Package:\n")
by_package <- sapply(audit_results, function(x) {
  if (grepl("nmadatasets", x$path)) {
    if (grepl("bnma__", x$file)) "bnma"
    else if (grepl("BUGSnet__", x$file)) "BUGSnet"
    else if (grepl("gemtc__", x$file)) "gemtc"
    else if (grepl("MBNMAdose__", x$file)) "MBNMAdose"
    else if (grepl("multinma__", x$file)) "multinma"
    else if (grepl("nmaINLA__", x$file)) "nmaINLA"
    else if (grepl("pcnetmeta__", x$file)) "pcnetmeta"
    else if (grepl("netmeta__", x$file)) "netmeta"
    else "nmadatasets_other"
  } else {
    "netmetaDatasets"
  }
})

package_summary <- table(by_package)
print(package_summary)
cat("\n")

# ============================================================================
# SECTION 2: Identify Cross-Package Datasets
# ============================================================================

cat("\nSection 2: Identifying Cross-Package Datasets...\n\n")

# Map file to dataset name
get_dataset_name <- function(filename) {
  # Extract dataset ID from filename
  # e.g., "bnma__smoking_studies.csv" -> "smoking"
  # e.g., "gemtc__thrombolytic_nodes.csv" -> "thrombolytic"

  if (grepl("__smoking", filename)) return("smoking")
  if (grepl("__thrombolyt", filename)) return("thrombolytic")
  if (grepl("__parkinson", filename)) return("parkinson")
  if (grepl("__diabetes", filename)) return("diabetes")
  if (grepl("__depression", filename)) return("depression")
  if (grepl("__dietfat|__dietary", filename)) return("dietary_fat")
  if (grepl("__blocker", filename)) return("blocker")
  if (grepl("__statins", filename)) return("statins")

  return(gsub("__.*$", "", filename))
}

# Group by dataset name
dataset_names <- sapply(audit_results, function(x) get_dataset_name(x$file))
dataset_presence <- table(dataset_names)

cat("Datasets appearing multiple times (cross-package):\n")
multi_presence <- dataset_presence[dataset_presence > 2]
print(multi_presence)
cat("\n")

# ============================================================================
# SECTION 3: Detailed Issue Report
# ============================================================================

cat("\nSection 3: Detailed Issue Report\n")
cat("==================================\n\n")

# Get files with issues
problematic <- Filter(function(x) x$status %in% c("ISSUES", "ERROR", "EMPTY"), audit_results)

cat(sprintf("Found %d files with issues\n\n", length(problematic)))

# Group by issue type
for (i in seq_along(problematic)) {
  item <- problematic[[i]]
  cat(sprintf("[%d] %s\n", i, item$file))
  cat(sprintf("    Status: %s\n", item$status))
  cat(sprintf("    Size: %d rows x %d cols\n", item$n_rows, item$n_cols))
  cat("    Issues:\n")
  for (issue in item$issues) {
    cat(sprintf("      - %s\n", issue))
  }
  cat("\n")
}

# ============================================================================
# SECTION 4: Generate Fix Recipes
# ============================================================================

cat("\nSection 4: Generating Fix Recipes\n")
cat("================================\n\n")

fix_recipes <- list()

for (item in problematic) {

  recipe <- list(
    file = item$file,
    path = item$path,
    fixes = character()
  )

  for (issue in item$issues) {
    if (grepl("placeholder treatment", issue)) {
      recipe$fixes <- c(recipe$fixes,
        "FIX: Load from source package and extract treatment labels")
    } else if (grepl("numeric/placeholder study IDs", issue)) {
      recipe$fixes <- c(recipe$fixes,
        "FIX: Load from source package and extract study names")
    } else if (grepl("duplicate", issue)) {
      recipe$fixes <- c(recipe$fixes,
        "FIX: Remove duplicate (study, treatment) rows, keep first")
    } else if (grepl("NA values", issue)) {
      recipe$fixes <- c(recipe$fixes,
        "FIX: Impute or remove rows with NA values")
    } else if (grepl("File is empty", issue)) {
      recipe$fixes <- c(recipe$fixes,
        "FIX: Re-extract from source package")
    }
  }

  if (length(recipe$fixes) > 0) {
    fix_recipes[[length(fix_recipes) + 1]] <- recipe
  }
}

cat(sprintf("Generated %d fix recipes\n\n", length(fix_recipes)))

# ============================================================================
# SECTION 5: Save Results
# ============================================================================

cat("Section 5: Saving Results\n")
cat("=========================\n\n")

# Create results directory
results_dir <- "outputs"
if (!dir.exists(results_dir)) {
  dir.create(results_dir, recursive = TRUE)
}

# Save audit summary
audit_summary <- data.frame(
  file = sapply(audit_results, function(x) x$file),
  status = sapply(audit_results, function(x) x$status),
  n_rows = sapply(audit_results, function(x) x$n_rows),
  n_cols = sapply(audit_results, function(x) x$n_cols),
  n_issues = sapply(audit_results, function(x) length(x$issues)),
  issues = I(sapply(audit_results, function(x) paste(x$issues, collapse = "; ")))
)

write.csv(audit_summary, file.path(results_dir, "data_audit_summary.csv"), row.names = FALSE)
cat("Saved: data_audit_summary.csv\n")

# Save problematic files detail
if (length(problematic) > 0) {
  problematic_detail <- data.frame(
    file = sapply(problematic, function(x) x$file),
    status = sapply(problematic, function(x) x$status),
    issues = I(sapply(problematic, function(x) paste(x$issues, collapse = "; ")))
  )
  write.csv(problematic_detail, file.path(results_dir, "problematic_files_detail.csv"), row.names = FALSE)
  cat("Saved: problematic_files_detail.csv\n")
}

# Save fix recipes
if (length(fix_recipes) > 0) {
  fix_recipes_df <- data.frame(
    file = sapply(fix_recipes, function(x) x$file),
    fixes = I(sapply(fix_recipes, function(x) paste(x$fixes, collapse = "; ")))
  )
  write.csv(fix_recipes_df, file.path(results_dir, "fix_recipes.csv"), row.names = FALSE)
  cat("Saved: fix_recipes.csv\n")
}

# Save cross-package dataset mapping
cross_package_mapping <- data.frame(
  dataset = names(dataset_presence),
  n_files = as.integer(dataset_presence)
)
cross_package_mapping <- cross_package_mapping[order(cross_package_mapping$n_files, decreasing = TRUE), ]
write.csv(cross_package_mapping, file.path(results_dir, "cross_package_datasets.csv"), row.names = FALSE)
cat("Saved: cross_package_datasets.csv\n")

cat("\n")
cat("=================================================================\n")
cat("  AUDIT COMPLETE\n")
cat("=================================================================\n")
cat(sprintf("\nResults saved to: %s\n", results_dir))
cat("\n")

# Print summary
cat("SUMMARY:\n")
cat(sprintf("  Total files audited: %d\n", length(audit_results)))
cat(sprintf("  Files with issues: %d\n", length(problematic)))
cat(sprintf("  Cross-package datasets: %d\n", sum(dataset_presence > 2)))
cat("\nNext steps:\n")
cat("  1. Review problematic_files_detail.csv\n")
cat("  2. Apply fixes from fix_recipes.csv\n")
cat("  3. Run cross-package comparison on clean datasets\n")
cat("\n")
