# Phase 2: Alternative Oligo Sets for aroB and PSD2

**Date:** 2026-09-27
**Status:** Design complete, in-silico QC passed, awaiting BLAST validation
**Note:** these are additional, independent candidates. The existing
primary designs for aroB and PSD2 (in the earlier oligo master table) are
unchanged and remain the primary picks — nothing here replaces them.

## Method

The existing primary designs use one exclusivity-clean, fully conserved
sub-region per gene (aroB: 257-953 of 1122 bp; PSD2: 300-889 of 906 bp —
both were already the longest invariant run bin/08 found inside each
gene's exclusivity window). To find truly independent alternative loci —
different genomic real estate, not just different primer boundaries around
the same target — the full per-gene alignment (all 97 primary genomes) was
re-scanned for *every* other ≥99%-conserved block inside each gene's
exclusivity window (which, for both aroB and PSD2, spans the entire gene —
both are clean at ≥85% identity across their full length, per
`candidate_regions.tsv`: `excl_gap_len` = full gene length for both).

## aroB — conservation map (full 1122 bp gene, all exclusivity-clean)

```
1-125 (125bp, 100% conserved) | 126-127 variable | 128-184 (57bp) | 185 variable |
186-255 (70bp) | 256 variable | 257-953 (697bp, PRIMARY DESIGN, 100% conserved) |
954 variable | 955-1078 (124bp, 100% conserved) | 1079 variable | 1080-1122 (43bp)
```

Only 6 positions in the entire gene show any intra-species variation across
the 97 primary genomes (126, 127, 185, 256, 954, 1079 — allele frequencies
53-99%). Two blocks outside the primary region are long enough for a full
primer+probe+primer design (≥80 bp): **1-125** and **955-1078**. (128-184
and 186-255 are exclusivity-clean but too short on their own for a full
TaqMan set at the project's 80-250 bp product-size range; 186-255 returned
zero Primer3 candidates.)

### aroB Alternative 1 (block 1-125)

| Oligo | Sequence (5'→3') | Len | Tm | GC% |
|---|---|---|---|---|
| Forward | GATCGAACTCGTTACCGAC | 19 | 59.49°C | 52.6% |
| Reverse | AAATGAGAGGGAAGTCGGTA | 20 | 59.59°C | 45.0% |
| Probe | TCTCCTCACCCTATTCACCTAGTTGAT | 27 | 66.04°C | 44.4% |

Product 101 bp; gap 6.44°C (floor tier); secondary structure LOW; 3' GC
passes on both primers; probe 5' base T (passes D12). Probe length 27 nt
(within spec). Oligo-dimer check: F-R heterodimer Tm=15.6°C (LOW), F-Probe
Tm=−31.9°C (NONE), R-Probe Tm=8.1°C (LOW) — all far below reaction
temperature.

### aroB Alternative 2 (block 955-1078)

| Oligo | Sequence (5'→3') | Len | Tm | GC% |
|---|---|---|---|---|
| Forward | CAAAATACTCCCTTACCACCA | 21 | 59.10°C | 42.9% |
| Reverse | TAGTTTGGCAAAATCGTCCA | 20 | 59.53°C | 40.0% |
| Probe | AGAAGAGATCGGACTAGCAGCTTCT | 25 | 66.53°C | 48.0% |

Product 82 bp; gap **7.00°C** (preferred tier); secondary structure LOW;
3' GC passes on both primers; probe 5' base A (passes D12). Probe length
25 nt (within spec). Oligo-dimer check: F-R heterodimer Tm=−45.3°C (NONE),
F-Probe Tm=−21.8°C (NONE), R-Probe Tm=−1.4°C (NONE) — all clean.

**These two loci are genomically independent of each other and of the
existing primary design (257-953)** — a real amplicon-level fallback, not
just a re-picked primer boundary, useful if the primary aroB amplicon
underperforms or if a third multiplex channel on aroB is ever wanted.

## PSD2 — conservation map (full 906 bp gene, all exclusivity-clean)

```
1-47 (47bp) | 48 variable | 49-253 (205bp, 100% conserved) | 254 variable |
255-298 (44bp) | 299 variable | 300-889 (590bp, PRIMARY DESIGN, 100% conserved) |
890 variable | 891-892 (2bp) | 893 variable | 894-906 (13bp)
```

Only 5 variable positions in the entire gene (48, 254, 299, 890, 893). One
block outside the primary region is long enough for a full design: **49-253**
(205 bp). The flanking 1-47/255-298 blocks and the 3' tail (891-906) are too
short individually. Within the 205 bp block there is room for two distinct
probe binding sites, ~30 bp apart — not fully independent amplicons, but
genuinely different probe sequences, useful as backups to each other.

### PSD2 Alternative 1 (block 49-253, probe site A)

| Oligo | Sequence (5'→3') | Len | Tm | GC% |
|---|---|---|---|---|
| Forward | AAACGAGAATAGGGAGAGCT | 20 | 59.67°C | 45.0% |
| Reverse | AGTCTTTGACACCAGCCTA | 19 | 59.67°C | 47.4% |
| Probe | TGTAAGAATAGCCTGTTTTCCCGTATCG | 28 | 66.48°C | 42.9% |

Product 82 bp; gap 6.81°C (floor tier); secondary structure LOW; 3' GC
passes on both primers; probe 5' base T (passes D12). Probe length 28 nt
(top of, but within, the project's 20-28 nt spec). Oligo-dimer check: F-R
heterodimer Tm=−20.0°C (NONE), F-Probe Tm=4.7°C (LOW), R-Probe
Tm=−35.2°C (NONE) — all clean.

### PSD2 Alternative 2 (block 49-253, probe site B — higher Tm gap, watch structure)

| Oligo | Sequence (5'→3') | Len | Tm | GC% |
|---|---|---|---|---|
| Forward | GAGAATAGGGAGAGCTCTGT | 20 | 59.45°C | 50.0% |
| Reverse | GAAGCACTCTCTTCTATGCAA | 21 | 59.53°C | 42.9% |
| Probe | AGGCTGGTGTCAAAGACTGCGA | 22 | 68.25°C | 54.5% |

Product 147 bp; gap **8.71°C** (best gap of the two, preferred tier);
secondary structure MEDIUM (forward primer hairpin, non-trivial — worth
re-checking by eye or re-picking a 1-2 nt shifted forward primer before
ordering); probe 5' base A (passes D12). Probe length 22 nt (within spec).
Oligo-dimer check: F-R heterodimer Tm=8.0°C (LOW), F-Probe Tm=−26.2°C
(NONE), R-Probe Tm=−27.3°C (NONE) — the forward primer's own hairpin (not
a cross-oligo dimer) is the flagged issue here, not F-R/F-Probe/R-Probe
interaction, which are all clean.

## Specificity status

Both genes' exclusivity windows (whole-gene, both) are already established
clean vs. the genus-tier Chlamydia panel at ≥85% identity (bin/07). BLAST
checked vs. human RefSeqGene and core_nt: **all 12 aroB/PSD2 alternative
oligos pass.** No 100%-identity full-length human match anywhere — the
closest is aroB_alt2_F at 86% (18/21 nt, E=0.0423, ERBB4 gene), the second
most notable human hit in the entire Phase 2 batch after group159_probe1,
but still 3 mismatches from a real match. No hits to C. muridarum or
C. suis for any aroB/PSD2 alternative oligo. Full table and how to read it:
`PHASE2_SUMMARY_AND_RECOMMENDATIONS.md`. Quality-review-tier genome check
(D13) still outstanding.
