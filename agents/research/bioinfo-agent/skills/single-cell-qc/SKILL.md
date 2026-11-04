---
name: single-cell-qc
description: Runs quality control on single-cell RNA-seq count data (AnnData .h5ad, 10x .h5 or matrix folders) — per-cell metrics, thresholds derived from each sample's own distributions, doublet detection, ambient RNA checks, gene filtering and normalisation — and reports what was removed and why using aggregated numbers only. Use before clustering, integration or modelling, when cells look low quality, or when asked to filter, clean or QC a single-cell dataset.
triggers:
  - single-cell qc
  - scrna-seq qc
  - filter cells
  - mitochondrial
  - doublets
  - ambient rna
  - h5ad
  - scanpy
  - normalise counts
---

# Single-cell RNA-seq QC

Goal: remove empty droplets, dying cells and multiplets while keeping real but unusual cells,
and leave a written record of every cut. Default to permissive; it is easy to filter more later
and impossible to recover a lost rare population.

## Data rule

Never print `obs` rows, barcodes, sample or donor names, or any clinical column. Report totals,
medians and percentages, per batch only under neutral labels (`batch_1`, `batch_2`, kept in a
local mapping file the owner controls). Plot titles and output file names carry no identifiers.

## 1. Load and inspect

- Know what you have: raw (all barcodes) or filtered (called cells) matrix, counts or already
  normalised values (`adata.X` should hold non-negative integers; check a sample of values),
  genes as symbols or IDs, how many samples and which `obs` column identifies them.
- If values are not integers, find the counts (`adata.layers["counts"]`, `adata.raw`) before
  doing anything else. QC and most models need raw counts.
- Keep the raw matrix if there is one: ambient correction needs empty droplets.

## 2. Compute per-cell metrics

`sc.pp.calculate_qc_metrics(adata, qc_vars=[...], log1p=True, percent_top=None)` with boolean
gene flags for mitochondrial, ribosomal and haemoglobin genes. Prefixes differ by species
(human `MT-`, `RPS`/`RPL`, `HB*` excluding `HBP1`; mouse `mt-`, `Rps`/`Rpl`, `Hb*` excluding
`Hbp1`). Confirm the flags caught a plausible number of genes (about 13 mitochondrial protein
genes for human and mouse) before trusting the percentages. Details per metric:
[references/metrics.md](references/metrics.md).

## 3. Look at distributions, per sample

Plot, for each sample separately: histograms of log total counts and log genes detected, the
mitochondrial fraction, and counts vs genes coloured by mitochondrial fraction. Look for a
low-count shoulder (empty or broken cells), a high-mito tail, and samples that differ from the
rest. Write down what you see before choosing cut-offs.

## 4. Choose thresholds from the data

- Per sample, flag outliers on log total counts and log genes as more than about 5 median
  absolute deviations from that sample's median, and on mitochondrial fraction above median +
  3 MADs. Thresholds come from each sample because depth and quality differ between them.
- Add a hard mitochondrial ceiling only with a reason: tissue matters (cardiomyocytes, hepatocytes,
  kidney and some neurons run high; blood runs low). Single-nucleus data should have almost no
  mitochondrial reads; a high value there means cytoplasmic contamination.
- Check what the cut removes: if one cell type or one cluster loses most of its cells, the
  threshold is cutting biology. Loosen it or set it per cell type.
- A sample that fails on every metric is a sample problem, not a threshold problem. Flag it to
  the owner instead of filtering it into shape.

## 5. Doublets

Run per sample, on counts, before merging samples (scDblFinder, scrublet or similar). Expected
rate grows with cells loaded, roughly 0.8% per 1,000 recovered cells on common droplet
platforms. Compare the called rate with the expected one, and check doublet scores by cluster:
a small cluster expressing markers of two lineages is suspect. With cell hashing or genotype
demultiplexing, use those calls first. Record the method and rate.

## 6. Ambient RNA

Signs: markers of the most abundant cell type detected at low level in every cluster, haemoglobin
genes in non-blood tissue, a high count floor in empty droplets. If present and raw matrices
exist, estimate and remove it (SoupX, CellBender, DecontX) before downstream analysis, and keep
the uncorrected counts too. If no raw matrix exists, say ambient correction was not possible.

## 7. Genes and normalisation

- Drop genes detected in very few cells (a handful to ~20 depending on dataset size; lower when
  rare populations matter).
- Store counts first: `adata.layers["counts"] = adata.X.copy()`.
- Default: total-count scaling then `log1p`. Alternatives when they fit: pooling-based size
  factors (scran) for heterogeneous depth, analytic Pearson residuals for variable-gene selection.
  scvi-tools models take the counts layer, not normalised values.

## 8. Report

Write a short QC note next to the outputs:

| Item | Content |
| --- | --- |
| Input | Path, matrix type, cells × genes before QC, number of samples |
| Metrics | Medians (and MAD) per metric, per batch label |
| Thresholds | Each cut, its value per batch, and why |
| Removed | Cells removed by each filter and in total (count and %), overall and per batch label |
| Doublets / ambient | Method, expected vs called rate, what was corrected |
| Output | Paths of the filtered `.h5ad`, the annotated pre-filter `.h5ad`, plots; package versions |

Never filter silently: keep flags in `obs` (`qc_fail_counts`, `qc_fail_mito`, `doublet`) on the
annotated copy so the decision can be revisited.
