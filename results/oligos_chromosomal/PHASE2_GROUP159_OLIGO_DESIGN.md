# Phase 2 Oligo Design: group_159 (backup candidate)

**Date:** 2026-09-27
**Gene:** group_159 (hypothetical protein, Panaroo cluster)
**Status:** Design complete, in-silico QC passed, awaiting BLAST validation

## Source data and method

Designed from the real Panaroo per-gene alignment across all 97 primary
C. trachomatis genomes (`results/pangenome/aligned_gene_sequences/group_159.aln.fas`),
not a summary table. Per-position conservation was recomputed directly from
this alignment inside the exclusivity-clean window already established by
bin/07/08 (`results/candidate_regions/candidate_regions.tsv`: window 19-247,
732 bp gene, exclusivity gap 229 bp, clean at ≥85% identity vs. the genus-tier
panel).

**Finding: the entire 229 bp exclusivity window is 100% conserved across all
97 primary genomes — zero variable positions.** No fragmentation into
sub-blocks separated by polymorphic gaps was needed or possible; the whole
window is one contiguous, invariant design surface.

```
Reference (GCF_000008725.1), gene coords 19-247 of 732 bp:
TGTTATCCCGGATACAACAATATTCCCGCATACAGTAACAGTTACTTCTACTGTACACTGTGTGATGGCGTTGTATCACC
TACCAACGTGGATATTGCTATTGTTGTACCTAACAAACCCACAGCTCACTCAGAATCCAAACTGTCTGTTTTACGCTGTA
AAAACCATCCTGTTAAAGGTCTGCACTCTGGTGGTCCAATTACTTCTTTAAGAGGTCTGATCCCCTTTT
[ 19 ─────────────────────────── 100% conserved, n=97/97 ─────────────────────────── 247 ]
```

## Design settings

Per `config/primer3_settings.txt` (D6/D7/D10-D12): primers 18-25 nt, Tm
59-61°C (opt 60); probe 20-28 nt, Tm 66-72°C (opt 68); hard floor probe Tm −
max(primer Tm) ≥ 5°C, ≥7°C preferred. Computed with primer3-py (bundled
libprimer3), Tm formula SantaLucia 1998 + salt correction, salts/dNTP/oligo
conc. matching the settings file (still placeholders pending real master-mix
values — open item #2 in HANDOVER.md). Cross-checked against an independent
nearest-neighbor Tm calculation (Biopython) — agreement within 0.5-0.7°C.

## Recommended set (Rank 1)

| Oligo | Sequence (5'→3') | Len | Tm | GC% | 3' GC (last 5nt) |
|---|---|---|---|---|---|
| Forward | GATGGCGTTGTATCACCTAC | 20 | 59.90°C | 50.0% | 2/5 (pass) |
| Reverse | CAGGATGGTTTTTACAGCGT | 20 | 60.26°C | 45.0% | 2/5 (pass) |
| Probe | ACCCACAGCTCACTCAGAATCCA | 23 | 67.32°C | 52.2% | — |

- Product size: 109 bp
- Probe−primer Tm gap: **7.06°C** (preferred tier, ≥7°C)
- Probe 5' base: A (not G — passes D12)
- Secondary structure: LOW severity only (all hairpin/homodimer/heterodimer
  melting temperatures are far below reaction temperature; the primer3
  "structure found" flag is oversensitive — see Methods note below)
- No poly-T at 3' end on either primer
- Probe length: 23 nt (within the project's 20-28 nt / opt-22 probe-length
  spec)
- Oligo-dimer check, all three pairwise combinations: F-R heterodimer
  Tm=14.4°C (LOW), F-Probe heterodimer Tm=−50.2°C (NONE), R-Probe
  heterodimer Tm=−15.7°C (NONE) — all far below the ~60°C reaction/probe
  annealing temperature. The original design pass only reported F-R
  heterodimer explicitly; F-Probe and R-Probe are now confirmed clean too.

## Ranked alternatives

| Rank | Forward | Reverse | Probe | Gap | Product | Secondary Structure |
|---|---|---|---|---|---|---|
| 2 | CGTTGTATCACCTACCAACG | CAGGATGGTTTTTACAGCGT | ACCCACAGCTCACTCAGAATCCA (same) | 7.06°C | 104 bp | LOW |
| 3 | TGATGGCGTTGTATCACCTA | CAGGATGGTTTTTACAGCGT | ACCCACAGCTCACTCAGAATCCA (same) | 6.99°C | 110 bp | LOW |
| 4 | GATGGCGTTGTATCACCTAC | ACAGGATGGTTTTTACAGCG | ACCCACAGCTCACTCAGAATCCA (same) | 7.06°C | 110 bp | MEDIUM |

All alternatives reuse one of two probe sites within the window (position
~116 or ~142 of the 229 bp region); with only 229 bp available there is not
enough room for a second, fully independent amplicon — these are ranked
primer-boundary variants around the same conserved core, matching the style
used for the four primary genes (mutL/aroB/PSD2/group_306).

## Note on secondary-structure scoring

primer3's `structure_found=True` flag fires on any predicted ΔG < 0, which
includes trivially weak structures with melting temperatures of −20 to
−35°C — physically irrelevant at any real reaction temperature. This report
classifies severity by the structure's own Tm (NONE <0°C, LOW 0-40°C, MEDIUM
40-55°C, HIGH ≥55°C, i.e. competitive with primer/probe annealing) rather
than the raw boolean, which is what the earlier oligo-QC work for the four
primary genes also effectively did (reporting bp-count/severity rather than
a bare found/not-found flag).

## Specificity status

- Vs. genus-tier Chlamydia panel: clean at ≥85% identity over this window
  (bin/07 exclusivity screen, already established for all 588 candidate
  genes including this one).
- Vs. human genome (NCBI RefSeqGene, curated gene loci) and vs. core_nt (all
  non-C. trachomatis organisms): **checked, all pass.** No 100%-identity
  full-length match to human anywhere. Best human hit is group159_probe1 at
  87% (20/23 nt, E=0.00379, DNAJC5 gene) — 3 mismatches, unlikely to support
  real probe hybridization but worth watching in a human-DNA no-template
  control. Forward/reverse primers all sit at 75-90% human identity with
  high E-values (indistinguishable from chance). No hits to C. muridarum or
  C. suis for any group_159 oligo.
- **Follow-up vs. the full human genome assembly (Human G+T database,
  GRCh38.p14, all chromosomes)**, closing RefSeqGene's curated-loci-only
  scope: same group159_probe1/DNAJC5 hit reconfirmed (E rescales to 0.0199
  in the ~6x larger database — same hit, not a new one), plus two additional
  weak partial matches on chr9 and chr15 (18/18 and 18/19 nt, E≈0.31, no
  gene annotation). Pair-level check: none of group159_F1/F2/R1/R2 hit
  those same chromosomes anywhere near those positions. No plausible
  off-target amplicon. Full results and how to read them:
  `PHASE2_SUMMARY_AND_RECOMMENDATIONS.md`.
- Vs. quality-review tier genomes (10 genomes, not used for consensus per
  D13): not yet checked. These oligos were designed only from the 97
  primary genomes; recommend a quick BLAST/alignment check against the 10
  quality-review genomes before finalizing, per D13's "tested against them,
  reported separately" rule.
