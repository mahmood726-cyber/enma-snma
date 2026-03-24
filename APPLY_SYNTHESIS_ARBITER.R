# NOTE: This script requires the FATIHA_Project synthesis.R module.
# Adjust the source path below to your local installation.
# source("path/to/FATIHA_Project/R/synthesis.R")

cat("=== SYNTHESIS ARBITER: Resolving NMA Bake-Off Disagreements ===\n\n")

# Load the actual bake-off outputs if they exist, otherwise use the demonstration set
output_file <- file.path("outputs", "synthesis_arbiter_input.csv")
if (file.exists(output_file)) {
    bakeoff_results <- read.csv(output_file)
} else {
    bakeoff_results <- data.frame(
        Package = c("netmeta", "gemtc", "multinma", "bnma", "nmaINLA"),
        Estimate = c(0.45, 0.52, 0.48, 0.65, 0.47),
        SE = c(0.05, 0.08, 0.06, 0.15, 0.055)
    )
}
package_quality <- c(0.9, 0.95, 0.95, 0.5, 0.85)

# Uncomment when synthesis.R is available:
# arbiter_res <- synthesis_arbiter(bakeoff_results$Estimate, bakeoff_results$SE,
#                                   source_quality = package_quality)
# cat("SYNTHESIS Arbitrated Consensus:\n")
# print(arbiter_res)
# write.csv(synthesis_table(arbiter_res),
#           file.path("outputs", "SYNTHESIS_ARBITRATED_RESULTS.csv"),
#           row.names = FALSE)
# cat("\nFinal arbitration report saved to outputs/SYNTHESIS_ARBITRATED_RESULTS.csv\n")

cat("Bake-off results (demo data):\n")
print(bakeoff_results)
