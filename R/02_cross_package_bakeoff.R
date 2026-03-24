# ============================================================================
# NMA Methods Research: Cross-Package Bake-Off Script (Step 2)
# ============================================================================
# Purpose: Run multiple NMA methods on identical datasets and compare results
# Datasets: Smoking, Thrombolytic, Parkinson, Diabetes
# Methods: netmeta, gemtc, multinma, bnma, nmaINLA
# ============================================================================

# Set working directory -- relative to this script's location
setwd(file.path(dirname(sys.frame(1)$ofile %||% "."), ".."))

# ============================================================================
# SETUP
# ============================================================================

cat("\n")
cat("=================================================================\n")
cat("  NMA METHODS RESEARCH: Cross-Package Bake-Off\n")
cat("=================================================================\n")
cat("\n")

# Create output directories
dir.create("outputs/bakeoff", showWarnings = FALSE, recursive = TRUE)
dir.create("outputs/comparisons", showWarnings = FALSE, recursive = TRUE)
dir.create("outputs/figures", showWarnings = FALSE, recursive = TRUE)

# Check and install required packages
required_pkgs <- c(
  "netmeta",      # Frequentist NMA
  "gemtc",        # Bayesian NMA (JAGS)
  "multinma",     # Bayesian NMA (Stan)
  "bnma",         # Bayesian NMA (JAGS)
  "nmaINLA",      # Bayesian NMA (INLA)
  "dplyr",        # Data manipulation
  "tidyr",        # Data tidying
  "ggplot2",      # Visualization
  "cowplot"       # Plot combining
)

install_if_missing <- function(pkg) {
  if (!requireNamespace(pkg, quietly = TRUE)) {
    message(paste("Installing", pkg, "..."))
    install.packages(pkg, repos = "https://cloud.r-project.org/")
  }
}

invisible(sapply(required_pkgs, install_if_missing))

# Load packages
suppressPackageStartupMessages({
  library(dplyr)
  library(tidyr)
  library(ggplot2)
})

cat("All required packages loaded successfully.\n\n")

# ============================================================================
# DATA LOADING FUNCTIONS
# ============================================================================

#' Load Smoking dataset from a specific package
#' @param package_name Package to load from
#' @return List with arm-based data and metadata
load_smoking_dataset <- function(package_name) {

  result <- list(
    package = package_name,
    status = NA,
    data = NULL,
    n_studies = NA,
    n_treatments = NA,
    n_arms = NA,
    error = NULL
  )

  tryCatch({

    if (package_name == "netmeta") {
      # Load from netmetaDatasets curated CSV
      df <- read.csv("netmetaDatasets/inst/extdata/smoking_cessation_2013.csv",
                     stringsAsFactors = FALSE)
      result$data <- df
      result$status <- "loaded"

    } else if (package_name == "gemtc") {
      # Load from gemtc package
      if (requireNamespace("gemtc", quietly = TRUE)) {
        # gemtc uses network objects
        # Try to load the smoking dataset
        data(list = "smoking", package = "gemtc", envir = environment())
        net <- get("smoking", envir = environment())

        # Convert to arm-based format
        # This requires extracting data from the network object
        df <- tryCatch({
          as.data.frame(net)
        }, error = function(e) {
          # Manually construct if conversion fails
          NULL
        })

        if (!is.null(df)) {
          result$data <- df
          result$status <- "loaded"
        } else {
          result$status <- "conversion_failed"
          result$error <- "Cannot convert gemtc network to data frame"
        }
      } else {
        result$status <- "package_not_available"
      }

    } else if (package_name == "bnma") {
      # Load from bnma package
      if (requireNamespace("bnma", quietly = TRUE)) {
        net <- bnma::network.load("smoking")
        result$data <- net
        result$status <- "loaded"
      } else {
        result$status <- "package_not_available"
      }

    } else if (package_name == "multinma") {
      # multinma has smoking data built-in
      if (requireNamespace("multinma", quietly = TRUE)) {
        df <- multinma::smoking
        result$data <- df
        result$status <- "loaded"
      } else {
        result$status <- "package_not_available"
      }

    } else if (package_name == "nmaINLA") {
      # nmaINLA smoking dataset
      if (requireNamespace("nmaINLA", quietly = TRUE)) {
        data(list = "Smokdat", package = "nmaINLA", envir = environment())
        df <- get("Smokdat", envir = environment())
        result$data <- df
        result$status <- "loaded"
      } else {
        result$status <- "package_not_available"
      }
    }

    # Extract metadata
    if (!is.null(result$data) && is.data.frame(result$data)) {
      result$n_arms <- nrow(result$data)
      if ("study" %in% names(result$data)) {
        result$n_studies <- length(unique(result$data$study))
      }
      if ("treatment" %in% names(result$data)) {
        result$n_treatments <- length(unique(result$data$treatment))
      }
    }

  }, error = function(e) {
    result$error <<- as.character(e$message)
    result$status <<- "error"
  })

  return(result)
}

#' Load Thrombolytic dataset from a specific package
load_thrombolytic_dataset <- function(package_name) {
  # Similar structure to load_smoking_dataset
  # Implementation details omitted for brevity
  result <- list(
    package = package_name,
    status = "not_implemented",
    data = NULL
  )
  return(result)
}

# ============================================================================
# METHOD RUNNING FUNCTIONS
# ============================================================================

#' Run netmeta analysis
#' @param data Arm-based data frame
#' @param outcome_type "binary" or "continuous"
#' @return List with results
run_netmeta <- function(data, outcome_type = "binary") {

  start_time <- Sys.time()

  result <- list(
    method = "netmeta",
    framework = "frequentist",
    status = NA,
    runtime = NA,
    rankings = NULL,
    treatment_effects = NULL,
    inconsistency = NULL,
    heterogeneity = NULL,
    warnings = character(),
    error = NULL
  )

  tryCatch({

    if (!requireNamespace("netmeta", quietly = TRUE)) {
      result$status <- "package_not_available"
      result$error <- "netmeta package not installed"
      return(result)
    }

    # Prepare data for netmeta (needs contrast-based format)
    # For binary outcomes, calculate log odds ratios
    # This is a simplified implementation

    # TODO: Convert arm-based to contrast-based format
    # TODO: Run netmeta::netmeta()
    # TODO: Extract rankings, effects, inconsistency

    result$status <- "not_implemented"
    result$error <- "Arm-to-contrast conversion not yet implemented"

  }, error = function(e) {
    result$error <- as.character(e$message)
    result$status <- "error"
  }, warning = function(w) {
    result$warnings <- append(result$warnings, as.character(w$message))
  })

  end_time <- Sys.time()
  result$runtime <- as.numeric(difftime(end_time, start_time, units = "secs"))

  return(result)
}

#' Run gemtc analysis
run_gemtc <- function(data) {

  start_time <- Sys.time()

  result <- list(
    method = "gemtc",
    framework = "bayesian_jags",
    status = NA,
    runtime = NA,
    rankings = NULL,
    treatment_effects = NULL,
    inconsistency = NULL,
    convergence = list(rhat = NA, ess = NA),
    warnings = character(),
    error = NULL
  )

  tryCatch({

    if (!requireNamespace("gemtc", quietly = TRUE)) {
      result$status <- "package_not_available"
      result$error <- "gemtc package not installed"
      return(result)
    }

    # TODO: Convert data to mtc.network object
    # TODO: Run mtc.model() with MCMC
    # TODO: Check convergence (R-hat, effective sample size)
    # TODO: Extract rankings (SUCRA), effects

    result$status <- "not_implemented"
    result$error <- "Data preparation for gemtc not yet implemented"

  }, error = function(e) {
    result$error <- as.character(e$message)
    result$status <- "error"
  }, warning = function(w) {
    result$warnings <- append(result$warnings, as.character(w$message))
  })

  end_time <- Sys.time()
  result$runtime <- as.numeric(difftime(end_time, start_time, units = "secs"))

  return(result)
}

#' Run multinma analysis
run_multinma <- function(data) {

  start_time <- Sys.time()

  result <- list(
    method = "multinma",
    framework = "bayesian_stan",
    status = NA,
    runtime = NA,
    rankings = NULL,
    treatment_effects = NULL,
    inconsistency = NULL,
    convergence = list(rhat = NA, ess = NA),
    warnings = character(),
    error = NULL
  )

  tryCatch({

    if (!requireNamespace("multinma", quietly = TRUE)) {
      result$status <- "package_not_available"
      result$error <- "multinma package not installed"
      return(result)
    }

    # TODO: Prepare data for multinma
    # TODO: Run nma() with Stan
    # TODO: Check convergence diagnostics
    # TODO: Extract rankings and effects

    result$status <- "not_implemented"
    result$error <- "Data preparation for multinma not yet implemented"

  }, error = function(e) {
    result$error <- as.character(e$message)
    result$status <- "error"
  }, warning = function(w) {
    result$warnings <- append(result$warnings, as.character(w$message))
  })

  end_time <- Sys.time()
  result$runtime <- as.numeric(difftime(end_time, start_time, units = "secs"))

  return(result)
}

#' Run bnma analysis
run_bnma <- function(data) {

  start_time <- Sys.time()

  result <- list(
    method = "bnma",
    framework = "bayesian_jags",
    status = NA,
    runtime = NA,
    rankings = NULL,
    treatment_effects = NULL,
    convergence = list(rhat = NA, ess = NA),
    warnings = character(),
    error = NULL
  )

  tryCatch({

    if (!requireNamespace("bnma", quietly = TRUE)) {
      result$status <- "package_not_available"
      result$error <- "bnma package not installed"
      return(result)
    }

    result$status <- "not_implemented"
    result$error <- "bnma implementation not yet complete"

  }, error = function(e) {
    result$error <- as.character(e$message)
    result$status <- "error"
  }, warning = function(w) {
    result$warnings <- append(result$warnings, as.character(w$message))
  })

  end_time <- Sys.time()
  result$runtime <- as.numeric(difftime(end_time, start_time, units = "secs"))

  return(result)
}

#' Run nmaINLA analysis
run_nmainla <- function(data) {

  start_time <- Sys.time()

  result <- list(
    method = "nmaINLA",
    framework = "bayesian_inla",
    status = NA,
    runtime = NA,
    rankings = NULL,
    treatment_effects = NULL,
    warnings = character(),
    error = NULL
  )

  tryCatch({

    if (!requireNamespace("nmaINLA", quietly = TRUE)) {
      result$status <- "package_not_available"
      result$error <- "nmaINLA package not installed"
      return(result)
    }

    result$status <- "not_implemented"
    result$error <- "nmaINLA implementation not yet complete"

  }, error = function(e) {
    result$error <- as.character(e$message)
    result$status <- "error"
  }, warning = function(w) {
    result$warnings <- append(result$warnings, as.character(w$message))
  })

  end_time <- Sys.time()
  result$runtime <- as.numeric(difftime(end_time, start_time, units = "secs"))

  return(result)
}

# ============================================================================
# BAKE-OFF FUNCTION
# ============================================================================

#' Run full bake-off comparison on a dataset
#' @param dataset_name Name of dataset ("smoking", "thrombolytic", etc.)
#' @return Comparison results
run_bakeoff <- function(dataset_name) {

  cat(sprintf("\n=== BAKE-OFF: %s ===\n", toupper(dataset_name)))

  # Define methods to test
  methods <- c("netmeta", "gemtc", "multinma", "bnma", "nmaINLA")

  # Load data for each method
  cat("\nLoading data...\n")
  loaded_data <- list()
  for (method in methods) {
    cat(sprintf("  %s: ", method))

    if (dataset_name == "smoking") {
      load_result <- load_smoking_dataset(method)
    } else if (dataset_name == "thrombolytic") {
      load_result <- load_thrombolytic_dataset(method)
    } else {
      load_result <- list(status = "not_implemented", error = "Dataset not yet implemented")
    }

    if (load_result$status == "loaded") {
      cat(sprintf("OK (%d studies, %d treatments)\n",
                  load_result$n_studies, load_result$n_treatments))
      loaded_data[[method]] <- load_result
    } else {
      cat(sprintf("FAILED: %s\n", load_result$error %||% load_result$status))
      loaded_data[[method]] <- load_result
    }
  }

  # Run each method
  cat("\nRunning methods...\n")
  results <- list()

  for (method in methods) {

    cat(sprintf("  %s: ", method))
    start_time <- Sys.time()

    if (is.null(loaded_data[[method]]) || loaded_data[[method]]$status != "loaded") {
      cat("SKIP (data not available)\n")
      next
    }

    data <- loaded_data[[method]]$data

    # Run the appropriate method
    result <- switch(method,
      "netmeta" = run_netmeta(data),
      "gemtc" = run_gemtc(data),
      "multinma" = run_multinma(data),
      "bnma" = run_bnma(data),
      "nmaINLA" = run_nmainla(data)
    )

    end_time <- Sys.time()
    runtime <- as.numeric(difftime(end_time, start_time, units = "secs"))

    # Print result
    if (result$status == "success") {
      cat(sprintf("OK (%.2fs)\n", runtime))
    } else if (result$status == "not_implemented") {
      cat("NOT IMPLEMENTED\n")
    } else {
      cat(sprintf("FAILED: %s\n", result$error %||% result$status))
    }

    results[[method]] <- result
  }

  # Create comparison summary
  comparison <- data.frame(
    method = methods,
    status = sapply(results, function(x) x$status %||% "no_result"),
    runtime = sapply(results, function(x) x$runtime %||% NA),
    n_warnings = sapply(results, function(x) length(x$warnings) %||% 0),
    stringsAsFactors = FALSE
  )

  cat("\nComparison Summary:\n")
  print(comparison)

  return(list(
    dataset = dataset_name,
    loaded_data = loaded_data,
    results = results,
    comparison = comparison
  ))
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

main <- function() {

  # Define datasets to test
  datasets_to_test <- c("smoking", "thrombolytic", "parkinson", "diabetes")

  all_results <- list()

  for (dataset in datasets_to_test) {
    result <- run_bakeoff(dataset)
    all_results[[dataset]] <- result

    # Save results
    saveRDS(result, file.path("outputs/bakeoff", paste0(dataset, "_results.rds")))
  }

  # Create overall summary
  overall_summary <- do.call(rbind, lapply(all_results, function(x) x$comparison))
  overall_summary$dataset <- rep(datasets_to_test, each = 5)

  cat("\n")
  cat("=================================================================\n")
  cat("  OVERALL SUMMARY\n")
  cat("=================================================================\n")
  cat("\n")
  print(overall_summary)

  # Save overall summary
  write.csv(overall_summary,
            file.path("outputs/comparisons", "overall_summary.csv"),
            row.names = FALSE)

  cat("\nResults saved to outputs/bakeoff/ and outputs/comparisons/\n")

  return(all_results)
}

# ============================================================================
# SCRIPT ENTRY POINT
# ============================================================================

cat("\nStarting NMA Cross-Package Bake-Off...\n")
cat("This script will compare multiple NMA methods on identical datasets.\n")
cat("Expected runtime: Variable (depends on MCMC convergence)\n\n")

# Run main analysis
all_results <- main()

cat("\nBake-off complete!\n")
cat("Next steps:\n")
cat("  1. Review results in outputs/bakeoff/\n")
cat("  2. Examine comparisons in outputs/comparisons/\n")
cat("  3. Investigate method disagreements\n")
cat("  4. Proceed to simulation studies\n")

# ============================================================================
# END OF SCRIPT
# ============================================================================
