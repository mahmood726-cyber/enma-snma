# E156 Protocol — `enma-snma`

This repository is the source code and dashboard backing an E156 micro-paper on the [E156 Student Board](https://mahmood726-cyber.github.io/e156/students.html).

---

## `[147]` Ensemble and Spectral Network Meta-Analysis: Novel Inconsistency-Robust Methods

**Type:** methods  |  ESTIMAND: Coverage improvement (percentage points)  
**Data:** 100 simulation replications x 5 topologies + 3 empirical NMA datasets (smoking, thrombolytics, Parki

### 156-word body

Can ensemble and spectral approaches improve inconsistency detection and robustness in network meta-analysis compared to standard methods? We developed two novel methods evaluated across 100 simulation replications per scenario using five network topologies with varying heterogeneity and inconsistency, plus three canonical empirical datasets. Ensemble NMA synthesises three complementary inconsistency diagnostics into an Inconsistency Confidence Score per edge and inflates variance adaptively, while Spectral NMA applies graph Laplacian eigen-decomposition to detect inconsistency via high-frequency energy in treatment effect signals. The median coverage improvement for Ensemble NMA was 1.8 percentage points (95% CI 1.5-2.2) across scenarios where inconsistency was present, without increasing RMSE over standard network meta-analysis. Spectral NMA runs in milliseconds versus minutes for MCMC-based diagnostics and correctly identified inconsistent edges in the thrombolytic therapy dataset. These methods offer computationally efficient, complementary tools for assessing and accommodating inconsistency in evidence networks. A limitation is that simulations used normal approximations rather than exact binomial or survival data-generating processes.

### Submission metadata

```
Corresponding author: Mahmood Ahmad <mahmood.ahmad2@nhs.net>
ORCID: 0000-0001-9107-3704
Affiliation: Tahir Heart Institute, Rabwah, Pakistan

Links:
  Code:      https://github.com/mahmood726-cyber/enma-snma
  Protocol:  https://github.com/mahmood726-cyber/enma-snma/blob/main/E156-PROTOCOL.md
  Dashboard: https://mahmood726-cyber.github.io/repo300-enma-snma/

References (topic pack: network meta-analysis):
  1. Rücker G. 2012. Network meta-analysis, electrical networks and graph theory. Res Synth Methods. 3(4):312-324. doi:10.1002/jrsm.1058
  2. Lu G, Ades AE. 2006. Assessing evidence inconsistency in mixed treatment comparisons. J Am Stat Assoc. 101(474):447-459. doi:10.1198/016214505000001302

Data availability: No patient-level data used. Analysis derived exclusively
  from publicly available aggregate records. All source identifiers are in
  the protocol document linked above.

Ethics: Not required. Study uses only publicly available aggregate data; no
  human participants; no patient-identifiable information; no individual-
  participant data. No institutional review board approval sought or required
  under standard research-ethics guidelines for secondary methodological
  research on published literature.

Funding: None.

Competing interests: MA serves on the editorial board of Synthēsis (the
  target journal); MA had no role in editorial decisions on this
  manuscript, which was handled by an independent editor of the journal.

Author contributions (CRediT):
  [STUDENT REWRITER, first author] — Writing – original draft, Writing –
    review & editing, Validation.
  [SUPERVISING FACULTY, last/senior author] — Supervision, Validation,
    Writing – review & editing.
  Mahmood Ahmad (middle author, NOT first or last) — Conceptualization,
    Methodology, Software, Data curation, Formal analysis, Resources.

AI disclosure: Computational tooling (including AI-assisted coding via
  Claude Code [Anthropic]) was used to develop analysis scripts and assist
  with data extraction. The final manuscript was human-written, reviewed,
  and approved by the author; the submitted text is not AI-generated. All
  quantitative claims were verified against source data; cross-validation
  was performed where applicable. The author retains full responsibility for
  the final content.

Preprint: Not preprinted.

Reporting checklist: PRISMA 2020 (methods-paper variant — reports on review corpus).

Target journal: ◆ Synthēsis (https://www.synthesis-medicine.org/index.php/journal)
  Section: Methods Note — submit the 156-word E156 body verbatim as the main text.
  The journal caps main text at ≤400 words; E156's 156-word, 7-sentence
  contract sits well inside that ceiling. Do NOT pad to 400 — the
  micro-paper length is the point of the format.

Manuscript license: CC-BY-4.0.
Code license: MIT.

SUBMITTED: [ ]
```


---

_Auto-generated from the workbook by `C:/E156/scripts/create_missing_protocols.py`. If something is wrong, edit `rewrite-workbook.txt` and re-run the script — it will overwrite this file via the GitHub API._