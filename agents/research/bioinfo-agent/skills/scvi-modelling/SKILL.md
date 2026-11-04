---
name: scvi-modelling
description: Fits and checks scvi-tools models on single-cell data — picks the model (scVI, scANVI, totalVI, PeakVI, MultiVI, DestVI, query mapping, veloVI, sysVI), sets up AnnData with raw counts and covariates, trains with convergence checks, evaluates batch mixing against preserved biology, transfers labels, and runs and interprets model-based differential expression. Use when integrating batches or datasets, mapping a query onto a reference, modelling CITE-seq, ATAC or multiome data, or when asked whether a latent space or integration is any good.
triggers:
  - scvi
  - scanvi
  - totalvi
  - scvi-tools
  - batch correction
  - integration
  - latent space
  - label transfer
  - reference mapping
  - cite-seq
  - multiome
---

# scvi-tools modelling

These are probabilistic models of raw counts that learn a low-dimensional latent space with
chosen nuisance factors (batch, technology) accounted for. They are worth it when batches are
many or strongly different, when labels need transferring, or when several modalities are
measured. For one clean batch, PCA on log-normalised data is enough; say so.

Input should be QC'd data (skill `single-cell-qc`). Same data rule: aggregated numbers only, no
barcodes, sample or donor names in output, plots or file names.

## 1. Pick the model

| Data and goal | Model |
| --- | --- |
| scRNA-seq, integrate batches, no labels | scVI |
| scRNA-seq with some or all cells labelled; transfer or refine labels | scANVI, initialised from a trained scVI |
| RNA + surface protein (CITE-seq) | totalVI |
| scATAC-seq peaks | PeakVI (or poissonVI on fragment counts) |
| Paired or partly paired RNA + ATAC | MultiVI |
| Spatial spots + single-cell reference, cell-type proportions | DestVI (reference model first) |
| New query onto a trained reference without retraining it | Query mapping (scArches-style `load_query_data`) |
| Spliced/unspliced counts, velocity with uncertainty | veloVI |
| Very different systems (species, organoid vs tissue, single-cell vs single-nucleus) | sysVI |

Model-specific setup and pitfalls: [references/models.md](references/models.md).

## 2. Set up the data

1. **Raw integer counts** in a layer (`layers["counts"]`). Check: non-negative, integer-valued.
   If only normalised values exist, stop and find the counts; do not round normalised data.
2. **Genes**: 1,500–5,000 highly variable genes chosen on counts with the batch taken into
   account (`highly_variable_genes(..., flavor="seurat_v3", layer="counts", batch_key=...)`).
   Subset to them, except for models that need all features of a modality.
3. **Covariates**: `batch_key` = the main technical unit (sample, lane, or study). Extra technical
   factors go in `categorical_covariate_keys` / `continuous_covariate_keys`.
   **Never put the biological variable you want to study (condition, disease) in a covariate**;
   the model will remove it.
4. Check batch and condition are not confounded (every condition in one batch). If they are,
   integration cannot separate them; tell the owner before training.
5. `scvi.settings.seed = <n>` and record versions.

## 3. Train and check

- Defaults are sensible (`n_latent` 10–30, 1–2 layers). Smaller data (< ~10k cells) wants a
  smaller model; very large data needs fewer epochs.
- Use early stopping and keep a validation split. Plot `model.history` training and validation
  ELBO / reconstruction loss: both should flatten; validation rising while training falls is
  overfitting.
- NaN loss: cells or genes with all-zero counts, non-integer input, or extreme values. Fix the
  data before touching the learning rate.
- Save with `model.save(dir, save_anndata=False)` next to the `.h5ad`; record the setup
  arguments.

## 4. Evaluate the latent space

Two questions, and both must be answered:

- **Did batches mix?** UMAP of the latent space coloured by batch; within each known cell type,
  cells from all batches should overlap. Quantify with batch-mixing scores (e.g. iLISI, kBET,
  batch silhouette).
- **Did biology survive?** Known cell types and markers stay distinct; clusters are not merged
  across lineages; condition-specific populations still appear. Quantify with label-conservation
  scores (NMI/ARI against labels, cLISI, isolated-label scores) when labels exist.

`scib-metrics` computes both families when installed; compare against an unintegrated PCA
baseline. A perfect mixing score with collapsed cell types is over-correction. Report the scores
and the comparison, not just a UMAP.

## 5. Use it

- Clustering and UMAP on `obsm["X_scVI"]` (or the model's latent key), not on PCA.
- Denoised, batch-corrected expression (`get_normalized_expression`) is for visualisation and
  marker inspection, not for statistical tests.
- Label transfer: report prediction confidence; cells below a cut-off stay "unassigned"; check
  transferred labels against markers.

## 6. Differential expression

`model.differential_expression(groupby=..., group1=..., group2=...)` compares groups of cells in
the model's space; with `mode="change"` and a `delta` it tests for effects above a minimum size.
Rank by Bayes factor or `proba_de` and effect size (`lfc_mean`), and drop genes with tiny
expression in both groups.

It treats cells, not donors, as observations. For comparing **conditions across donors or
samples**, use pseudobulk: sum counts per sample × cell type, then DESeq2 / edgeR / limma with
samples as replicates. Use model DE for markers between clusters within the data.

## Report

Model and version, setup arguments (covariates, genes used), training curve summary, evaluation
scores vs baseline, what the latent space was used for, DE method and thresholds, paths to the
model and outputs. State any confounding or caveat.
