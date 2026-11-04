# Running nf-core pipelines

Check the pipeline's documentation page for the revision you pin; parameters change between
releases. Look up the latest release (`nf-core pipelines list` or the pipeline's releases page)
rather than reusing a version number from memory.

## Choosing a pipeline

| Data | Pipeline | Main decisions to confirm with the owner |
| --- | --- | --- |
| Bulk RNA-seq | `nf-core/rnaseq` | Genome and annotation, aligner/quantifier route (STAR + Salmon by default; HISAT2 for low memory; pseudo-alignment only for speed), strandedness |
| WGS / WES | `nf-core/sarek` | Germline vs somatic (tumour/normal pairs), callers in `--tools`, target BED for exomes, annotation tool |
| ATAC-seq | `nf-core/atacseq` | Genome, read length, narrow vs broad peaks, design for differential accessibility |
| Single-cell | `nf-core/scrnaseq` | Chemistry, aligner (STARsolo, simpleaf, Cell Ranger), whether to keep raw matrices for ambient correction |

Other data types usually have a pipeline too; search the nf-core list before writing one.

## Samplesheets

- Absolute paths, one row per FASTQ pair (lanes as extra rows with the same sample id; the
  pipeline merges them).
- rnaseq: `sample, fastq_1, fastq_2, strandedness` (`auto` lets the pipeline infer it).
- sarek: `patient, sample, lane, fastq_1, fastq_2` plus `status` (0 normal, 1 tumour) for somatic.
  These columns are identifiers: keep the file local and never echo its rows.
- atacseq: `sample, fastq_1, fastq_2, replicate`.
- Validate before the run; most pipelines fail early on a bad sheet, which is cheap.

## References

Use `--genome <key>` only for builds the pipeline's iGenomes config supports, and know that some
of those are dated. For current builds pass `--fasta` and `--gtf` (and prebuilt indices if you
have them, to save hours). Save built indices with the pipeline's `--save_reference` option for
reuse.

## Public data (GEO / SRA / ENA)

Optional, only when the owner asks for reanalysis:
1. Resolve the study accession to run accessions and a size estimate first; show the owner
   the sample groups and total size before downloading.
2. `nf-core/fetchngs` downloads runs and writes a samplesheet for the next pipeline; or use
   the SRA toolkit / ENA directly.
3. Never fetch controlled-access (dbGaP, EGA) data without the owner's approval and access.

## Checking a finished run

- `multiqc/multiqc_report.html`: alignment rate, duplication, insert size, strandedness agreement,
  per-pipeline metrics (for ATAC: fraction of reads in peaks, TSS enrichment, mitochondrial
  fraction; for variants: coverage and Ti/Tv).
- `pipeline_info/`: execution report, software versions, params used. Keep these with results.
- Report aggregated numbers (median alignment rate across samples, how many samples fall below a
  threshold), not a per-sample table with names.

## Common pipeline-specific failures

- Index build killed: the aligner index step needs the most memory; give it its own limit or
  supply a prebuilt index.
- Low alignment rate everywhere: wrong species or build, or heavy adapter content.
- Strandedness warnings: set it explicitly once the inferred value is confirmed.
- Somatic calls empty: tumour/normal pairing or `status` wrong in the sheet.
- Few peaks: low library complexity or over-digestion; check the fingerprint plot before
  loosening thresholds.
