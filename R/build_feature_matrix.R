#!/usr/bin/env Rscript
# Build labelled feature matrices for the SNI supervised-learning analysis.
#
# Reads the 18-protein labelled benchmark set from the supplementary repo
# (SolNRCH_foldome) and the helper/sensor ID lists, drops entries with no
# structural data (nrc0, slnrc0_sa -- matches the authors' REMOVE_FROM_TEST
# in R/NRC_heatmap_analysis.R), attaches a binary class label, and writes
# two feature matrices:
#
#   data/feature_matrix_labelled_11.{csv,rds}  -- ID, class, the 11 canonical
#                                                 SNI features defined in the
#                                                 manuscript (ALL_PARAMS)
#   data/feature_matrix_labelled_full.{csv,rds} -- ID, class, every numeric
#                                                 feature column from the
#                                                 summary table
#
# Run from the sni_ml/ directory:
#     Rscript R/build_feature_matrix.R
#
# Paths are resolved relative to sni_ml/ so the supplementary repo is
# expected at ../SolNRCH_foldome/.

suppressPackageStartupMessages({
  library(readxl)
})

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SUPP_TEST_DIR <- "../SolNRCH_foldome/R/test"
XLSX_PATH     <- file.path(SUPP_TEST_DIR, "resistosome_analysis_summary.xlsx")
HELPERS_PATH  <- file.path(SUPP_TEST_DIR, "helpers.txt")
SENSORS_PATH  <- file.path(SUPP_TEST_DIR, "sensors.txt")

OUT_DIR <- "data"

stopifnot(
  "Run this script from the sni_ml/ directory" =
    basename(normalizePath(getwd())) == "sni_ml",
  "Supplementary repo not found at ../SolNRCH_foldome" =
    dir.exists(SUPP_TEST_DIR),
  file.exists(XLSX_PATH),
  file.exists(HELPERS_PATH),
  file.exists(SENSORS_PATH)
)

# ---------------------------------------------------------------------------
# Canonical 11 SNI features, as defined in SolNRCH_foldome/R/NRC_heatmap_analysis.R
# ---------------------------------------------------------------------------
CANONICAL_11 <- c(
  "ipTM_LCB", "Sum_CONTACTS", "BSA_INT_PROTO",
  "SD_THETA_ROT", "S_PROTO", "D_APEX",
  "THETA_APEX_mean", "L_APEX_mean", "H_ABS_mean", "MU_H_mean",
  "D_MHD_P_mean"
)

REMOVE_IDS <- c("nrc0", "slnrc0_sa")   # no structural data in summary table

# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------
summary_tbl <- as.data.frame(read_excel(XLSX_PATH))
helpers_ids <- trimws(readLines(HELPERS_PATH))
sensors_ids <- trimws(readLines(SENSORS_PATH))
helpers_ids <- helpers_ids[nzchar(helpers_ids)]
sensors_ids <- sensors_ids[nzchar(sensors_ids)]

# Normalise IDs (lowercase, dots -> underscores) -- matches the authors' convention
norm_id <- function(x) tolower(gsub("\\.", "_", x))

summary_tbl$ID_norm <- norm_id(summary_tbl$ID)
helpers_norm <- norm_id(helpers_ids)
sensors_norm <- norm_id(sensors_ids)

# ---------------------------------------------------------------------------
# Attach class label and drop entries without data
# ---------------------------------------------------------------------------
summary_tbl$class <- NA_character_
summary_tbl$class[summary_tbl$ID_norm %in% helpers_norm] <- "helper"
summary_tbl$class[summary_tbl$ID_norm %in% sensors_norm] <- "sensor"

unlabelled <- summary_tbl$ID[is.na(summary_tbl$class)]
if (length(unlabelled) > 0) {
  warning(sprintf(
    "Dropping %d rows without a helper/sensor label: %s",
    length(unlabelled), paste(unlabelled, collapse = ", ")
  ))
}

labelled <- summary_tbl[!is.na(summary_tbl$class), , drop = FALSE]

before_remove <- nrow(labelled)
labelled <- labelled[!labelled$ID_norm %in% REMOVE_IDS, , drop = FALSE]
after_remove <- nrow(labelled)

# IDs listed in helpers.txt / sensors.txt but with no row in the summary table
helpers_missing <- setdiff(helpers_norm, summary_tbl$ID_norm)
sensors_missing <- setdiff(sensors_norm, summary_tbl$ID_norm)

# ---------------------------------------------------------------------------
# Feature selection
# ---------------------------------------------------------------------------
META_COLS <- c("ID", "ID_norm", "class", "N_replicates", "N_chains", "Seeds")
numeric_cols <- names(labelled)[
  vapply(labelled, is.numeric, logical(1)) & !(names(labelled) %in% META_COLS)
]

missing_canonical <- setdiff(CANONICAL_11, numeric_cols)
if (length(missing_canonical) > 0) {
  stop(sprintf(
    "Canonical features not found in summary table: %s",
    paste(missing_canonical, collapse = ", ")
  ))
}

build_matrix <- function(feature_cols) {
  out <- labelled[, c("ID", "class", feature_cols), drop = FALSE]
  out$class <- factor(out$class, levels = c("sensor", "helper"))  # helper = positive
  rownames(out) <- NULL
  out
}

mat_11   <- build_matrix(CANONICAL_11)
mat_full <- build_matrix(numeric_cols)

# ---------------------------------------------------------------------------
# Write outputs
# ---------------------------------------------------------------------------
dir.create(OUT_DIR, showWarnings = FALSE, recursive = TRUE)

write.csv(mat_11,   file.path(OUT_DIR, "feature_matrix_labelled_11.csv"),   row.names = FALSE)
write.csv(mat_full, file.path(OUT_DIR, "feature_matrix_labelled_full.csv"), row.names = FALSE)
saveRDS(mat_11,     file.path(OUT_DIR, "feature_matrix_labelled_11.rds"))
saveRDS(mat_full,   file.path(OUT_DIR, "feature_matrix_labelled_full.rds"))

# ---------------------------------------------------------------------------
# Provenance summary (stdout)
# ---------------------------------------------------------------------------
rule <- function() cat(strrep("-", 70), "\n", sep = "")

rule()
cat("Build feature matrix -- summary\n")
rule()
cat(sprintf("Source xlsx     : %s\n", normalizePath(XLSX_PATH)))
cat(sprintf("helpers.txt     : %d IDs\n", length(helpers_ids)))
cat(sprintf("sensors.txt     : %d IDs\n", length(sensors_ids)))
cat(sprintf("Rows in xlsx    : %d\n", nrow(summary_tbl)))
cat(sprintf("Labelled (pre-drop)  : %d\n", before_remove))
cat(sprintf("Dropped REMOVE_IDS   : %s\n",
            paste(intersect(REMOVE_IDS, norm_id(summary_tbl$ID)), collapse = ", ")))
cat(sprintf("Final labelled rows  : %d\n", after_remove))
cat(sprintf("  helper : %d\n", sum(mat_11$class == "helper")))
cat(sprintf("  sensor : %d\n", sum(mat_11$class == "sensor")))
if (length(helpers_missing) > 0)
  cat(sprintf("helpers.txt IDs absent from xlsx: %s\n",
              paste(helpers_missing, collapse = ", ")))
if (length(sensors_missing) > 0)
  cat(sprintf("sensors.txt IDs absent from xlsx: %s\n",
              paste(sensors_missing, collapse = ", ")))
rule()
cat(sprintf("Canonical 11-feature matrix : %d rows x %d cols\n",
            nrow(mat_11), ncol(mat_11) - 2))
cat(sprintf("Full feature matrix          : %d rows x %d cols\n",
            nrow(mat_full), ncol(mat_full) - 2))
rule()

cat("NA counts per feature (canonical 11):\n")
na_counts <- sapply(mat_11[, CANONICAL_11, drop = FALSE], function(x) sum(is.na(x)))
print(na_counts[order(-na_counts)])
cat("\n")

cat("NA counts per class x feature (canonical 11, sensors only):\n")
sensor_na <- sapply(mat_11[mat_11$class == "sensor", CANONICAL_11, drop = FALSE],
                    function(x) sum(is.na(x)))
print(sensor_na[order(-sensor_na)])
cat("\n")

cat("NA counts per class x feature (canonical 11, helpers only):\n")
helper_na <- sapply(mat_11[mat_11$class == "helper", CANONICAL_11, drop = FALSE],
                    function(x) sum(is.na(x)))
print(helper_na[order(-helper_na)])
cat("\n")

rule()
cat("Output files:\n")
for (f in c("feature_matrix_labelled_11.csv",
            "feature_matrix_labelled_11.rds",
            "feature_matrix_labelled_full.csv",
            "feature_matrix_labelled_full.rds"))
  cat(sprintf("  %s (%d bytes)\n",
              file.path(OUT_DIR, f),
              file.info(file.path(OUT_DIR, f))$size))
rule()