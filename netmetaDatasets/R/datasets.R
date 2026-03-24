#' List available network meta-analysis datasets
#'
#' Returns a tibble enumerating the datasets shipped with the
#' package along with metadata such as clinical area, outcome, and
#' licensing information. Remote entries sourced from external
#' repositories are included so researchers can discover them even if
#' the data are not bundled locally.
#'
#' @param include_remote Logical indicating whether to include datasets
#'   that require downloading or loading from external packages.
#'   Defaults to TRUE.
#' @return A tibble with one row per dataset entry.
#' @examples
#' list_nma_datasets()
#' @export
list_nma_datasets <- function(include_remote = TRUE) {
  metadata_path <- system.file("extdata", "datasets.csv", package = "netmetaDatasets")
  if (!file.exists(metadata_path)) {
    stop("Dataset registry is missing; please reinstall the package.")
  }

  registry <- readr::read_csv(metadata_path, show_col_types = FALSE) |>
    dplyr::mutate(
      dataset_id = stringr::str_trim(dataset_id),
      available_locally = data_access_type == "local_csv" &
        file.exists(system.file("extdata", access_details, package = "netmetaDatasets"))
    ) |>
    dplyr::arrange(dataset_id)

  if (!include_remote) {
    registry <- dplyr::filter(registry, available_locally)
  }

  registry
}

rename_with_synonyms <- function(data, mapping) {
  normalized <- stringr::str_to_lower(names(data))
  for (target in names(mapping)) {
    if (target %in% names(data)) {
      next
    }
    synonyms <- stringr::str_to_lower(mapping[[target]])
    match_idx <- which(normalized %in% synonyms)
    if (length(match_idx) == 0) {
      next
    }
    names(data)[match_idx[1]] <- target
    normalized[match_idx[1]] <- stringr::str_to_lower(target)
  }
  data
}

standardize_column_names <- function(data) {
  if (!tibble::is_tibble(data)) {
    data <- dplyr::as_tibble(data)
  }

  general_map <- list(
    study_id = c("study_id", "studlab", "study", "trial", "studyid"),
    treatment = c("treatment", "treat", "treat1", "trt", "tx", "arm", "treatment1"),
    comparator = c("comparator", "treat2", "treatment2", "trt2", "tx2"),
    responders = c("responders", "events", "event", "r", "responders_arm", "responders1"),
    non_responders = c("nonresponders", "non_responders", "failures", "nr"),
    sample_size = c("sample_size", "samplesize", "n", "total", "ntotal", "sample", "number"),
    mean_change = c("mean_change", "mean", "ybar", "mean_arm", "mean1", "y"),
    sd_change = c("sd_change", "sd", "sd_arm", "sd1", "sdiff"),
    events = c("events", "cases", "responders"),
    person_time = c("person_time", "personyears", "person_years", "exposure", "followup", "time"),
    arm = c("arm", "arm_id"),
    contrast = c("contrast", "comparison")
  )

  rename_with_synonyms(data, general_map)
}

numeric_columns <- c(
  "responders", "non_responders", "sample_size", "mean_change", "sd_change",
  "se_mean_change", "events", "person_time", "log_hazard_ratio",
  "se_log_hazard_ratio", "log_odds_ratio", "se_log_odds_ratio", "effect_size",
  "se_effect_size"
)

coerce_numeric <- function(data, columns) {
  present <- intersect(columns, names(data))
  for (column in present) {
    data[[column]] <- suppressWarnings(as.numeric(data[[column]]))
  }
  data
}

standardize_dataset_structure <- function(data, record) {
  standardized <- standardize_column_names(data)
  standardized <- coerce_numeric(standardized, numeric_columns)

  dataset_id <- record$dataset_id[[1]]
  design <- record$design[[1]]

  require_columns <- function(required, optional = character()) {
    missing_cols <- setdiff(required, names(standardized))
    if (length(missing_cols) > 0) {
      stop(
        "Dataset '", dataset_id, "' is missing required columns: ",
        paste(missing_cols, collapse = ", "),
        call. = FALSE
      )
    }
    keep <- unique(c("study_id", "treatment", required, optional))
    dplyr::select(standardized, dplyr::any_of(keep))
  }

  if (design == "arm_binary") {
    require_columns(c("responders", "sample_size"), optional = c("non_responders"))
  } else if (design == "arm_continuous") {
    standardized <- rename_with_synonyms(standardized, list(
      se_mean_change = c("se_mean_change", "se_mean", "sem", "se_diff")
    ))
    require_columns(c("mean_change", "sd_change", "sample_size"), optional = "se_mean_change")
  } else if (design == "arm_rate") {
    require_columns(c("events", "person_time"))
  } else if (design == "arm_hr") {
    standardized <- rename_with_synonyms(standardized, list(
      log_hazard_ratio = c("log_hazard_ratio", "log_hr", "loghazardratio", "loghr", "loghazard"),
      se_log_hazard_ratio = c("se_log_hazard_ratio", "se_log_hr", "seloghr", "seloghazardratio")
    ))
    require_columns(c("comparator", "log_hazard_ratio", "se_log_hazard_ratio"))
  } else if (design == "arm_smd") {
    standardized <- rename_with_synonyms(standardized, list(
      effect_size = c("effect_size", "smd", "effect", "te"),
      se_effect_size = c("se_effect_size", "se_effect", "se_smd", "sete")
    ))
    require_columns(c("comparator", "effect_size", "se_effect_size"))
  } else if (design == "arm_mixed") {
    standardized <- rename_with_synonyms(standardized, list(
      log_hazard_ratio = c("log_hazard_ratio", "log_hr", "loghazardratio", "loghr"),
      se_log_hazard_ratio = c("se_log_hazard_ratio", "se_log_hr", "seloghr", "seloghazardratio"),
      log_odds_ratio = c("log_odds_ratio", "log_or", "logor", "te", "effect", "logrr"),
      se_log_odds_ratio = c("se_log_odds_ratio", "se_log_or", "selogor", "sete", "se_te"),
      effect_size = c("effect_size", "smd", "effect"),
      se_effect_size = c("se_effect_size", "se_effect", "se_smd")
    ))
    measures <- intersect(
      c(
        "responders", "sample_size", "mean_change", "sd_change", "events",
        "person_time", "log_hazard_ratio", "se_log_hazard_ratio", "effect_size",
        "se_effect_size", "log_odds_ratio", "se_log_odds_ratio"
      ),
      names(standardized)
    )
    if (length(measures) == 0) {
      stop(
        "Dataset '", dataset_id, "' could not be standardized because no known outcome columns were detected.",
        call. = FALSE
      )
    }
    require_columns(measures)
  } else {
    stop(
      "Dataset '", dataset_id, "' uses unsupported design '", design, "'.",
      call. = FALSE
    )
  }
}

#' Load a network meta-analysis dataset
#'
#' @param dataset_id A character identifier matching the `dataset_id`
#'   column in [list_nma_datasets()].
#' @param install_if_missing Logical; if TRUE, the function will attempt
#'   to install required CRAN packages when a dataset is sourced
#'   externally. Defaults to FALSE.
#' @return A tibble containing the harmonized dataset. Binary arm-based
#'   datasets include `study_id`, `treatment`, `responders`, and
#'   `sample_size`. Continuous outcomes include `mean_change`,
#'   `sd_change`, and `sample_size` columns.
#' @examples
#' smoking <- load_nma_dataset("smoking_cessation_2013")
#' @export
load_nma_dataset <- function(dataset_id, install_if_missing = FALSE) {
  datasets <- list_nma_datasets()
  id <- stringr::str_to_lower(dataset_id)
  record <- dplyr::filter(datasets, stringr::str_to_lower(dataset_id) == id)

  if (nrow(record) == 0) {
    stop("Dataset not found. Run list_nma_datasets() for options.")
  }

  access_type <- record$data_access_type[[1]]
  access_details <- record$access_details[[1]]

  raw_data <- NULL
  if (access_type == "local_csv") {
    data_path <- system.file("extdata", access_details, package = "netmetaDatasets")
    if (!file.exists(data_path)) {
      stop("Data file is missing for dataset ", dataset_id)
    }

    raw_data <- readr::read_csv(data_path, show_col_types = FALSE)
  } else if (access_type == "cran_package") {
    parts <- stringr::str_split(access_details, "::", n = 2)[[1]]
    if (length(parts) != 2) {
      stop("Invalid access details for dataset ", dataset_id)
    }

    package_name <- parts[[1]]
    object_name <- parts[[2]]

    if (!requireNamespace(package_name, quietly = TRUE)) {
      if (!install_if_missing) {
        stop(
          "Package '", package_name, "' is required for dataset '", dataset_id,
          "'. Install it manually or set install_if_missing = TRUE."
        )
      }
      utils::install.packages(package_name)
      if (!requireNamespace(package_name, quietly = TRUE)) {
        stop("Failed to install package '", package_name, "' for dataset '", dataset_id, "'.")
      }
    }

    data_env <- new.env(parent = emptyenv())
    utils::data(list = object_name, package = package_name, envir = data_env)
    if (!exists(object_name, envir = data_env, inherits = FALSE)) {
      stop("Dataset '", object_name, "' not found in package '", package_name, "'.")
    }

    obj <- get(object_name, envir = data_env, inherits = FALSE)
    raw_data <- dplyr::as_tibble(obj)
  } else {
    stop(
      "Unsupported data access type '", access_type, "' for dataset '", dataset_id,
      "'."
    )
  }

  standardize_dataset_structure(raw_data, record)
}

#' Summarize an NMA dataset
#'
#' Provides quick descriptive statistics for a dataset loaded with
#' [load_nma_dataset()]. For binary outcomes the summary includes
#' responder totals. For continuous outcomes the summary reports mean
#' change distributions.
#'
#' @param data A tibble returned by [load_nma_dataset()].
#' @return A list containing summary tables tailored to the outcome
#'   type.
#' @examples
#' smoking <- load_nma_dataset("smoking_cessation_2013")
#' nma_dataset_overview(smoking)
#' @export
nma_dataset_overview <- function(data) {
  cols <- names(data)
  if (all(c("responders", "sample_size") %in% cols)) {
    summary <- data |>
      dplyr::group_by(treatment) |>
      dplyr::summarise(
        studies = dplyr::n_distinct(study_id),
        total_sample = sum(sample_size, na.rm = TRUE),
        total_responders = sum(responders, na.rm = TRUE),
        response_rate = total_responders / total_sample,
        .groups = "drop"
      ) |>
      dplyr::arrange(dplyr::desc(response_rate))

    list(type = "binary", summary = summary)
  } else if (all(c("mean_change", "sd_change", "sample_size") %in% cols)) {
    summary <- data |>
      dplyr::group_by(treatment) |>
      dplyr::summarise(
        studies = dplyr::n_distinct(study_id),
        pooled_mean = stats::weighted.mean(mean_change, sample_size, na.rm = TRUE),
        pooled_sd = sqrt(stats::weighted.mean(sd_change^2, sample_size, na.rm = TRUE)),
        total_sample = sum(sample_size, na.rm = TRUE),
        .groups = "drop"
      ) |>
      dplyr::arrange(pooled_mean)

    list(type = "continuous", summary = summary)
  } else {
    stop("Data structure not recognized. Ensure the dataset uses the standard schema.")
  }
}

#' Audit dataset accessibility and schema conformance
#'
#' Iterates over the dataset registry and attempts to load each entry
#' using [load_nma_dataset()]. The function captures any errors and
#' returns a tibble summarizing which datasets are immediately
#' accessible under the current R session configuration.
#'
#' @param include_remote Logical; include datasets that rely on external
#'   CRAN packages. Defaults to `TRUE`.
#' @param install_if_missing Logical; passed to [load_nma_dataset()].
#'   When `TRUE` the function will attempt to install any required
#'   packages for remote datasets.
#' @return A tibble with one row per dataset entry including status
#'   information and any associated error messages.
#' @examples
#' audit <- audit_nma_datasets(include_remote = FALSE)
#' audit$status
#' @export
audit_nma_datasets <- function(include_remote = TRUE, install_if_missing = FALSE) {
  registry <- list_nma_datasets(include_remote = include_remote)
  if (nrow(registry) == 0) {
    return(tibble::tibble())
  }

  results <- vector("list", nrow(registry))

  for (idx in seq_len(nrow(registry))) {
    record <- registry[idx, ]
    dataset_id <- record$dataset_id[[1]]

    outcome <- tryCatch(
      {
        data <- load_nma_dataset(dataset_id, install_if_missing = install_if_missing)
        tibble::tibble(
          status = "ok",
          message = NA_character_,
          rows = nrow(data),
          columns = ncol(data)
        )
      },
      error = function(err) {
        tibble::tibble(
          status = "error",
          message = conditionMessage(err),
          rows = NA_integer_,
          columns = NA_integer_
        )
      }
    )

    record_info <- dplyr::select(
      record,
      dataset_id,
      title,
      design,
      data_access_type,
      available_locally
    )

    results[[idx]] <- dplyr::bind_cols(record_info, outcome)
  }

  dplyr::bind_rows(results)
}
