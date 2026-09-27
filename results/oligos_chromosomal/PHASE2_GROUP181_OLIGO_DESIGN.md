# Phase 2 Oligo Design: group_181 (backup candidate)

**Date:** 2026-09-27
**Gene:** group_181 (hypothetical protein, Panaroo cluster)
**Status:** Design complete, in-silico QC passed, awaiting BLAST validation

## Source data and method

Same method as group_159/140: recomputed conservation directly from the
real 97-genome Panaroo alignment (`aligned_gene_sequences/group_181.aln.fas`)
within the established exclusivity window (1-183 of 591 bp gene, 183 bp,
clean at ≥85% identity vs. the genus panel — this window is the entire 5'
portion of the gene).

**Finding: the entire 183 bp window is 100% conserved across all 97
primary genomes — zero variable positions.** This is the shortest of the
three backup windows; still enough room for one strong probe target plus a
second, more marginal option.

## Recommended set (Rank 1)

| Oligo | Sequence (5'→3') | Len | Tm | GC% | 3' GC |
|---|---|---|---|---|---|
| Forward | CTTATTTTTGCTGATCCGGC | 20 | 59.26°C | 45.0% | pass |
| Reverse | AATGCTTGAACAACTCCTCG | 20 | 60.26°C | 45.0% | pass |
| Probe | AGAAGCTGCTAGAACACTCTCTCTGT | 26 | 66.72°C | 46.2% | — |

- Product size: 155 bp
- Probe−primer Tm gap: **6.47°C** (floor tier)
- Probe 5' base: A (passes D12); secondary structure severity: LOW
- Probe length: 26 nt (within the project's 20-28 nt probe-length spec)
- Oligo-dimer check, all three pairwise combinations: F-R heterodimer
  Tm=−27.3°C (NONE), F-Probe heterodimer Tm=−14.1°C (NONE), R-Probe
  heterodimer Tm=−7.2°C (NONE) — all clean.

## Ranked alternatives (same probe locus)

| Rank | Forward | Reverse | Gap | Product | Secondary Structure |
|---|---|---|---|---|---|
| 2 | AAGCTGCTAGAACACTCTCT | GGGGCTTAATGCTTGAACA | 6.13°C | 140 bp | MEDIUM |
| 3 | AGAAGCTGCTAGAACACTCT | GGGGCTTAATGCTTGAACA | 6.13°C | 142 bp | MEDIUM |

## Second probe locus (further into the window, redundant target)

| Oligo | Sequence (5'→3') | Len | Tm | GC% |
|---|---|---|---|---|
| Forward | TGCTAGAACACTCTCTCTGT | 20 | 59.23°C | 45.0% |
| Reverse | GGGCTTAATGCTTGAACAAC | 20 | 59.40°C | 45.0% |
| Probe | TGGTACTAAAAACATGGGGTTACCGAGG | 28 | 68.01°C | 46.4% |

- Product size: 135 bp; gap **8.61°C** (preferred tier — the best Tm gap of
  any set designed in this batch); secondary structure MEDIUM
- Probe length: 28 nt (at the top of, but within, the project's 20-28 nt
  probe-length spec). Oligo-dimer check: F-R heterodimer Tm=−27.3°C (NONE),
  F-Probe Tm=−18.4°C (NONE), R-Probe Tm=−38.6°C (NONE) — all clean.
- This probe binds ~90 bp downstream of the Rank-1 probe (position ~127 vs.
  ~39 in the 183 bp window), giving a genuinely different TaqMan target
  within the same conserved block — good candidate for a true second
  detection channel if multiplex redundancy on group_181 specifically is
  wanted.

## Specificity status

Clean vs. genus-tier Chlamydia panel (bin/07, already established). BLAST
checked vs. human RefSeqGene and core_nt: **passes.** No 100%-identity
full-length human match anywhere — best is 90% (2 mismatches, high
E-value). No hits to C. muridarum or C. suis for any group_181 oligo. Full
table: `PHASE2_SUMMARY_AND_RECOMMENDATIONS.md`. Quality-review-tier genome
check (D13) still outstanding.
