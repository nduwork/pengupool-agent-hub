# QC metrics and how to read them

## Per-cell metrics

| Metric (`obs` column from scanpy) | Low value suggests | High value suggests | Notes |
| --- | --- | --- | --- |
| `total_counts` (UMIs per cell) | Empty droplet, debris, broken cell | Doublet, or a large, transcriptionally busy cell | Right-skewed: judge on the log scale |
| `n_genes_by_counts` | Same as low counts | Doublet | Tracks counts closely; cells far off the counts–genes trend are suspicious |
| `pct_counts_mt` | — | Stressed, dying or lysed cell (cytoplasm leaked, mitochondria stayed) | Tissue-dependent baseline; near zero expected for nuclei |
| `pct_counts_ribo` | — | Cell state (growth, activation) or contamination | Usually not a filter on its own |
| `pct_counts_hb` | — | Red-cell or blood contamination | Mostly relevant outside blood |

## Reading plots

- **Counts vs genes**: a tight curved band is normal. Cells under the band (many counts, few
  genes) are often dominated by a few genes (mitochondrial or ambient). Cells far above at the
  top are doublet candidates.
- **Counts vs mito fraction**: dying cells sit at low counts and high mito. High counts with
  high mito can be a real metabolically active type; check which cluster they belong to before
  removing.
- **Two peaks in log counts**: either a mix of cell sizes (fine) or a population of empty or
  broken barcodes (filter). Decide by where the low peak sits on the mito axis and whether it
  clusters with real cell types.
- **One sample shifted from the rest**: a batch or sample problem; report it.

## Median absolute deviation thresholds

MAD = median(|x − median(x)|). A cut at k MADs adapts to each sample's depth and spread and is
not pulled by the outliers it is meant to find, unlike mean ± SD. Rules of thumb:

- k ≈ 5 on log counts and log genes: removes only clear outliers.
- k ≈ 3 on mitochondrial fraction (upper side only).
- Lower k when many poor cells are visible or clusters form around quality metrics; raise it when
  rare populations matter or the data are already clean.
- Always compute per sample; a pooled median hides a bad sample and punishes a deep one.

## Signs QC left something behind

After clustering: a cluster defined mainly by low counts or high mito, no clear markers, or
markers of two unrelated lineages. Go back and adjust thresholds or doublet calls rather than
annotating it as a cell type.

## Species gene flags

Use the reference annotation's gene names. Human: `MT-` for mitochondrial genes, `RPS`/`RPL`
for ribosomal proteins, `HBA*`/`HBB*`-style haemoglobin genes excluding `HBP1`. Mouse: same
genes in lower-case-after-first-letter form (`mt-`, `Rps`/`Rpl`, `Hb*` excluding `Hbp1`). For
other species or Ensembl IDs, flag by gene biotype or chromosome (`MT`) from the annotation.

## What not to do

- Fixed cut-offs copied from another dataset ("200 genes, 10% mito") without looking.
- Filtering after merging samples or after normalisation.
- Removing a cluster as "low quality" without checking its markers.
- Regressing out mitochondrial fraction as a substitute for filtering dying cells.
