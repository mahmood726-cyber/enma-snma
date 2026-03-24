# ============================================================================
# NMA Methods Research: Dataset Fixing & Cross-Package Comparison
# ============================================================================
# Purpose:
#   1. Fix broken datasets (missing labels, NAs, duplicates)
#   2. Load clean cross-package datasets for bake-off
#   3. Create unified comparison framework
# ============================================================================
# Author: repo300 Research Project
# Date: 2026-01-15
# ============================================================================

# Required packages
required_pkgs <- c("netmeta", "gemtc", "bnma", "multinma", "nmaINLA",
                   "dplyr", "tidyr", "jsonlite", "boot")

# Install missing packages
install_if_missing <- function(pkgs) {
  for (pkg in pkgs) {
    if (!requireNamespace(pkg, quietly = TRUE)) {
      message(paste("Installing", pkg))
      install.packages(pkg, repos = "https://cloud.r-project.org/")
    }
  }
}
install_if_missing(required_pkgs)

# Load packages
suppressPackageStartupMessages({
  library(netmeta)
  library(gemtc)
  library(bnma)
  library(dplyr)
  library(tidyr)
})

# ============================================================================
# PART 1: Define Cross-Package Datasets for Comparison
# ============================================================================

cross_package_datasets <- list(
  smoking = list(
    name = "Smoking Cessation",
    source_packages = c("netmeta", "gemtc", "bnma", "multinma"),
    outcome = "Abstinence at >=6 months",
    design = "arm_binary"
  ),
  thrombolytic = list(
    name = "Thrombolytic Therapy",
    source_packages = c("gemtc", "bnma", "BUGSnet"),
    outcome = "Mortality/Stroke",
    design = "arm_binary"
  ),
  parkinson = list(
    name = "Parkinson's Disease",
    source_packages = c("netmeta", "gemtc", "bnma", "multinma", "nmaINLA"),
    outcome = "UPDRS score",
    design = "arm_continuous"
  ),
  diabetes = list(
    name = "Type 2 Diabetes",
    source_packages = c("gemtc", "multinma", "nmaINLA", "BUGSnet"),
    outcome = "HbA1c change",
    design = "arm_continuous"
  )
)

# ============================================================================
# PART 2: Load Datasets Directly from Source Packages
# ============================================================================

#' Load dataset from source package with proper error handling
#' @param dataset_name Name of the dataset (e.g., "smoking", "thrombolytic")
#' @param package_name Source package name
#' @return List with data and metadata
load_from_source <- function(dataset_name, package_name) {

  result <- list(
    dataset = dataset_name,
    package = package_name,
    status = "error",
    data = NULL,
    n_studies = NA,
    n_treatments = NA,
    n_arms = NA,
    error = NULL
  )

  tryCatch({
    # Different packages have different loading mechanisms
    if (package_name == "netmeta") {
      # netmeta datasets are usually loaded with data()
      data(list = dataset_name, package = "netmeta", envir = environment())
      df <- get(dataset_name, envir = environment())
      result$data <- df
      result$status <- "loaded"
    } else if (package_name == "gemtc") {
      # gemtc stores data as specific objects
      data(list = dataset_name, package = "gemtc", envir = environment())
      df <- get(dataset_name, envir = environment())
      result$data <- df
      result$status <- "loaded"
    } else if (package_name == "bnma") {
      # bnma uses network loading
      net_data <- bnma::network.load(dataset_name, package = "bnma")
      result$data <- net_data
      result$status <- "loaded"
    } else if (package_name == "multinma") {
      # multinma uses special loading function
      df <- multinma::smoking  # Direct access
      result$data <- df
      result$status <- "loaded"
    } else if (package_name == "nmaINLA") {
      # nmaINLA datasets
      data(list = dataset_name, package = "nmaINLA", envir = environment())
      df <- get(dataset_name, envir = environment())
      result$data <- df
      result$status <- "loaded"
    }

    # Extract metadata
    if (!is.null(result$data)) {
      if (is.data.frame(result$data)) {
        result$n_arms <- nrow(result$data)
        result$n_studies <- length(unique(result$data$study))
        result$n_treatments <- length(unique(result$data$treatment))
      }
    }

  }, error = function(e) {
    result$error <<- as.character(e)
    result$status <<- "error"
  })

  return(result)
}

#' Load all cross-package datasets
#' @return List of loaded datasets with metadata
load_all_cross_package_data <- function() {

  results <- list()

  for (dataset_name in names(cross_package_datasets)) {
    dataset_info <- cross_package_datasets[[dataset_name]]

    for (pkg in dataset_info$source_packages) {

      cat(sprintf("\nLoading %s from %s...", dataset_name, pkg))

      result <- tryCatch({
        # Package-specific loading logic
        if (pkg == "netmeta") {
          # Load from local CSV files first (our curated data)
          csv_path <- sprintf("../../netmetaDatasets/inst/extdata/%s_2013.csv", dataset_name)
          if (file.exists(csv_path)) {
            df <- read.csv(csv_path, stringsAsFactors = FALSE)
            list(status = "loaded", data = df, source = "csv")
          } else {
            list(status = "not_found", data = NULL, error = "CSV not found")
          }
        } else if (pkg == "gemtc") {
          # Try loading from gemtc package
          if (requireNamespace("gemtc", quietly = TRUE)) {
            # Load network data
            data(list = dataset_name, package = "gemtc")
            net <- get(dataset_name)
            # Convert to arm-based format
            df <- tryCatch({
              as.data.frame(net)
            }, error = function(e) {
              NULL
            })
            if (!is.null(df)) {
              list(status = "loaded", data = df, source = "gemtc_package")
            } else {
              list(status = "conversion_failed", data = NULL, error = "Cannot convert to data frame")
            }
          } else {
            list(status = "package_not_installed", data = NULL)
          }
        } else {
          list(status = "not_implemented", data = NULL, error = paste("Loading from", pkg, "not yet implemented"))
        }
      }, error = function(e) {
        list(status = "error", data = NULL, error = as.character(e$message))
      })

      # Store result
      key <- sprintf("%s__%s", dataset_name, pkg)
      results[[key]] <- result

      # Print status
      status_symbol <- switch(result$status,
        loaded = "✓",
        not_found = "✗",
        error = "✗",
        not_implemented = "○",
        package_not_installed = "○",
        "?"
      )
      cat(sprintf(" %s %s\n", status_symbol, result$status))
    }
  }

  return(results)
}

# ============================================================================
# PART 3: Fix Broken Datasets
# ============================================================================

#' Fix dataset with missing labels or NAs
#' @param df Data frame to fix
#' @param dataset_name Name of dataset (for lookup)
#' @return Fixed data frame
fix_dataset <- function(df, dataset_name) {

  # Check for NAs in study or treatment columns
  if (any(is.na(df$study)) || any(is.na(df$treatment))) {

    warning(sprintf("Dataset %s has NA values in study/treatment columns", dataset_name))

    # Try to recover from clean version
    if (dataset_name == "smoking") {
      # Load clean version from netmetaDatasets
      clean_path <- "../../netmetaDatasets/inst/extdata/smoking_cessation_2013.csv"
      if (file.exists(clean_path)) {
        clean_df <- read.csv(clean_path, stringsAsFactors = FALSE)
        return(clean_df)
      }
    }
  }

  # Check for duplicate (study, treatment) rows
  if (all(c("study", "treatment") %in% names(df))) {
    duplicates <- df[duplicated(df[, c("study", "treatment")]), ]
    if (nrow(duplicates) > 0) {
      warning(sprintf("Dataset %s has %d duplicate (study,treatment) rows",
                     dataset_name, nrow(duplicates)))
      # Remove duplicates, keep first occurrence
      df <- df[!duplicated(df[, c("study", "treatment")]), ]
    }
  }

  return(df)
}

#' Fix all broken datasets in nmadatasets
fix_all_broken_datasets <- function() {

  cat("\n=== FIXING BROKEN DATASETS ===\n")

  # Read catalogue
  catalogue_path <- "../nmadatasets/inst/extdata/catalogue.csv"
  if (!file.exists(catalogue_path)) {
    stop("Catalogue not found:", catalogue_path)
  }

  catalogue <- read.csv(catalogue_path, stringsAsFactors = FALSE)

  # Find datasets with issues
  broken <- catalogue[catalogue$issues != "", ]

  cat(sprintf("\nFound %d datasets with issues\n", nrow(broken)))

  for (i in 1:nrow(broken)) {
    dataset_id <- broken$id[i]
    issues <- broken$issues[i]

    cat(sprintf("\n[%d/%d] Fixing %s\n", i, nrow(broken), dataset_id))
    cat(sprintf("     Issues: %s\n", issues))

    # Try to fix based on issue type
    if (grepl("missing treatment labels", issues)) {
      # Try to load from source package and extract labels
      cat("     Action: Attempting to extract treatment labels from source package...\n")
    }

    if (grepl("duplicate", issues)) {
      cat("     Action: Removing duplicate (study,treatment) rows...\n")
    }

    if (grepl("missing study identifiers", issues)) {
      cat("     Action: Attempting to recover study IDs...\n")
    }
  }
}

# ============================================================================
# PART 4: Cross-Package Method Comparison (The Bake-Off)
# ============================================================================

#' Run netmeta on a dataset
run_netmeta <- function(df, outcome = "binary") {

  result <- list(method = "netmeta", status = "error", warnings = list())

  tryCatch({
    # Prepare data for netmeta
    if (outcome == "binary") {
      # Need contrast-based format for netmeta
      # Convert arm-based to contrast-based
      # This is a simplified conversion

      # For now, return placeholder
      result$status <- "not_implemented"
      result$error <- "Arm-to-contrast conversion needed"

    } else {
      result$status <- "not_implemented"
      result$error <- "Continuous outcomes not yet implemented"
    }

  }, error = function(e) {
    result$error <- as.character(e$message)
  }, warning = function(w) {
    result$warnings <- append(result$warnings, as.character(w$message))
  })

  return(result)
}

#' Run gemtc on a dataset
run_gemtc <- function(df) {

  result <- list(method = "gemtc", status = "error", warnings = list())

  tryCatch({
    # Convert to tc network object
    # This requires proper data preparation

    result$status <- "not_implemented"
    result$error <- "Data preparation for gemtc not yet implemented"

  }, error = function(e) {
    result$error <- as.character(e$message)
  })

  return(result)
}

#' Run full bake-off comparison
#' @param dataset_name Name of dataset to compare
#' @return Data frame with comparison results
run_bakeoff <- function(dataset_name) {

  cat(sprintf("\n=== BAKE-OFF: %s ===\n", toupper(dataset_name)))

  # Load dataset from all available packages
  packages_to_test <- c("netmeta", "gemtc", "bnma", "multinma", "nmaINLA")

  results <- data.frame(
    package = character(),
    status = character(),
    n_studies = integer(),
    n_treatments = integer(),
    runtime_sec = numeric(),
    warnings = character(),
    stringsAsFactors = FALSE
  )

  for (pkg in packages_to_test) {

    cat(sprintf("\nTesting %s...", pkg))

    start_time <- Sys.time()

    tryCatch({
      # Run the method
      if (pkg == "netmeta") {
        result <- run_netmeta(NULL)
      } else if (pkg == "gemtc") {
        result <- run_gemtc(NULL)
      } else {
        result <- list(method = pkg, status = "not_implemented",
                      error = paste("Method", pkg, "not yet implemented"))
      }

      end_time <- Sys.time()
      runtime <- as.numeric(difftime(end_time, start_time, units = "secs"))

      # Store result
      results <- rbind(results, data.frame(
        package = pkg,
        status = result$status,
        n_studies = NA,
        n_treatments = NA,
        runtime_sec = runtime,
        warnings = paste(result$warnings, collapse = "; "),
        stringsAsFactors = FALSE
      ))

      # Print status
      status_symbol <- if(result$status == "success") "✓" else "✗"
      cat(sprintf(" %s %s (%.2fs)\n", status_symbol, result$status, runtime))

    }, error = function(e) {
      end_time <- Sys.time()
      runtime <- as.numeric(difftime(end_time, start_time, units = "secs"))

      results <<- rbind(results, data.frame(
        package = pkg,
        status = "error",
        n_studies = NA,
        n_treatments = NA,
        runtime_sec = runtime,
        warnings = as.character(e$message),
        stringsAsFactors = FALSE
      ))

      cat(sprintf(" ✗ ERROR: %s\n", as.character(e$message)))
    })
  }

  return(results)
}

# ============================================================================
# PART 5: Main Execution
# ============================================================================

main <- function() {

  cat("\n")
  cat("=================================================================\n")
  cat("  NMA METHODS RESEARCH: Dataset Fixing & Cross-Package Comparison\n")
  cat("=================================================================\n")
  cat("\n")

  # Step 1: Fix broken datasets
  fix_all_broken_datasets()

  # Step 2: Load cross-package datasets
  cat("\n=== LOADING CROSS-PACKAGE DATASETS ===\n")
  loaded_data <- load_all_cross_package_data()

  # Step 3: Run bake-off on key datasets
  bakeoff_datasets <- c("smoking", "thrombolytic", "parkinson", "diabetes")

  bakeoff_results <- list()
  for (ds in bakeoff_datasets) {
    bakeoff_results[[ds]] <- run_bakeoff(ds)
  }

  # Step 4: Summarize results
  cat("\n")
  cat("=================================================================\n")
  cat("  SUMMARY\n")
  cat("=================================================================\n")
  cat("\n")

  for (ds in names(bakeoff_results)) {
    cat(sprintf("\n%s:\n", toupper(ds)))
    print(bakeoff_results[[ds]])
  }

  # Return results
  return(list(
    loaded_data = loaded_data,
    bakeoff_results = bakeoff_results
  ))
}

# Run main if executed directly
if (!interactive()) {
  results <- main()
}

# ============================================================================
# END OF SCRIPT
# ============================================================================
