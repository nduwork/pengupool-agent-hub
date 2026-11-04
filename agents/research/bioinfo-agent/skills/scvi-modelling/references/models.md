# Model notes

Check the installed scvi-tools version and its API docs before writing code; arguments move
between releases. Optional GPU: training runs on CPU, only slower. Install PyTorch with the CUDA
build that matches the driver if a GPU is wanted.

## scVI

- Likelihood: negative binomial is the usual choice; zero-inflated NB rarely helps with UMI data.
- Many batches with few cells each: consider a coarser `batch_key` (e.g. study) plus sample as a
  categorical covariate.
- Integrating studies with different gene panels: use the intersection, or genes present in most
  studies, and check how many HVGs survive.

## scANVI

- Initialise from a trained scVI (`SCANVI.from_scvi_model(..., labels_key, unlabeled_category)`)
  and train briefly; faster and usually better than from scratch.
- Unlabelled cells get the `unlabeled_category`. Labels must be consistent across batches (same
  names for the same type); harmonise first.
- `predict(soft=True)` gives probabilities; keep the max as a confidence score.
- Labels pull the latent space toward them: good for conserving known types, but it can hide
  novel populations. Compare with the scVI space.

## totalVI (CITE-seq)

- Protein counts must be raw antibody counts in `obsm` (a DataFrame with protein names), not
  centred-log-ratio values exported from another tool.
- Keep isotype controls to judge background; drop failed antibodies (no signal anywhere).
- Gives denoised protein values (background removed) and joint RNA+protein DE.
- Batches with different antibody panels: missing proteins are handled, but say which.

## PeakVI / poissonVI (ATAC)

- Input is a cells × peaks matrix (binary or counts). Filter peaks seen in very few cells; keep
  thousands to tens of thousands of peaks.
- Use a consensus peak set across samples; per-sample peak calls do not line up.

## MultiVI (RNA + ATAC)

- Works with paired cells and with RNA-only or ATAC-only cells together; record the modality of
  each cell. How the modalities are combined depends on the version (one AnnData with genes then
  peaks in older releases, MuData in newer ones); follow the installed version's docs.

## DestVI (spatial deconvolution)

- Train the single-cell reference model (CondSCVI) on labelled single-cell data, then fit the
  spatial model on spots. Use genes shared by both.
- Proportions are only as good as the reference: a cell type missing from the reference gets
  absorbed into others. Report which types the reference covers.

## Query mapping onto a reference

- The query must use the reference genes in the reference order; missing genes are zero-filled
  by `prepare_query_anndata`. Report the fraction of reference genes present; a low fraction
  makes mapping unreliable.
- The reference model must have been trained to allow it (scVI defaults are fine; very old
  models may not be).
- Fine-tune on the query briefly; the reference weights stay fixed.
- Check mapped cells against markers, and flag query cells far from any reference cell as
  possibly novel rather than forcing a label.

## veloVI

- Needs spliced and unspliced layers (velocyto, STARsolo velocity, alevin-fry). Preprocess as the
  current docs describe; velocity results are sensitive to gene selection.
- Use its uncertainty estimates; do not over-read arrows on a UMAP.

## sysVI

- For strong system-level differences where scVI either fails to mix or over-mixes. Evaluate
  both mixing and conservation as for scVI; these settings trade one against the other.

## Common problems

| Problem | Likely cause | First thing to try |
| --- | --- | --- |
| Batches stay apart | Few shared genes, wrong `batch_key`, real biology differs | Check gene overlap and composition per batch; more HVGs; longer training |
| Cell types merged | Over-correction, biology in a covariate, too small latent space | Remove biological variables from covariates; scANVI with labels; larger `n_latent` |
| "Data not integer" error | Normalised values in the layer | Find the counts; never round |
| Out of GPU memory | Batch size or gene count too large | Smaller `batch_size`, fewer genes, or CPU |
| Validation loss rises | Overfitting | Early stopping; fewer epochs; more dropout |
| Results change run to run | No seed, small data | Set the seed; compare a few seeds before trusting fine structure |
