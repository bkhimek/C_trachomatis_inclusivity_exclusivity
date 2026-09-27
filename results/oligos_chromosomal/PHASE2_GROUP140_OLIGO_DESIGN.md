# Phase 2 Oligo Design: group_140 (backup candidate)

**Date:** 2026-09-27
**Gene:** group_140 (hypothetical protein, Panaroo cluster)
**Status:** Design complete, in-silico QC passed, awaiting BLAST validation

## Source data and method

Same method as group_159: recomputed conservation directly from the real
97-genome Panaroo alignment (`aligned_gene_sequences/group_140.aln.fas`)
within the established exclusivity window (417-735 of 852 bp gene, 319 bp,
clean at ≥85% identity vs. the genus panel).

**Finding: the entire 319 bp window is 100% conserved across all 97 primary
genomes — zero variable positions.** This is the largest of the three
backup windows, and the only one of the three with enough room for a
genuinely useful second probe binding site (see below).

## Recommended set (Rank 1)

| Oligo | Sequence (5'→3') | Len | Tm | GC% | 3' GC |
|---|---|---|---|---|---|
| Forward | AGCTTCCTCGTAATGGTGTA | 20 | 59.96°C | 45.0% | pass |
| Reverse | GTGCTTGCTTTCTTGAGGAA | 20 | 60.47°C | 45.0% | pass |
| Probe | AGTCACAGGAAGAAATATCCCTCGCA | 26 | 67.31°C | 46.2% | — |

- Product size: 169 bp
- Probe−primer Tm gap: **6.84°C** (floor tier, 5-7°C)
- Probe 5' base: A (passes D12); secondary structure severity: LOW
- Probe length: 26 nt (within the project's 20-28 nt probe-length spec)
- Oligo-dimer check, all three pairwise combinations: F-R heterodimer
  Tm=5.3°C (LOW), F-Probe heterodimer Tm=9.4°C (LOW), R-Probe heterodimer
  Tm=−3.8°C (NONE) — all far below reaction temperature. F-Probe/R-Probe
  weren't explicitly reported in the original design pass; confirmed clean
  now.

## Ranked alternatives (same probe locus)

| Rank | Forward | Reverse | Gap | Product | Secondary Structure |
|---|---|---|---|---|---|
| 2 | AGCTTCCTCGTAATGGTGTA | AACATGGTTGATTTGTCCCG | 6.77°C | 188 bp | LOW |
| 3 | AAACAGCTTCCTCGTAATGG | GCTTGCTTTCTTGAGGAAGA | 7.42°C | 171 bp | MEDIUM |

## Second, more distal probe locus (extended-product option)

group_140's window is long enough that a second TaqMan probe site exists,
~100 bp further into the conserved region, still using the same forward
primer:

| Oligo | Sequence (5'→3') | Len | Tm | GC% |
|---|---|---|---|---|
| Forward (same) | AGCTTCCTCGTAATGGTGTA | 20 | 59.96°C | 45.0% |
| Reverse (alt) | TTCCGCAGCATGAATGAATT | 20 | 60.33°C | 40.0% |
| Probe (alt) | CCTCAAGAAAGCAAGCACGGGA | 22 | 67.14°C | 54.5% |

- Product size: 230 bp; gap 6.81°C; secondary structure MEDIUM
- Probe length: 22 nt (within spec). Oligo-dimer check: F-R heterodimer
  Tm=−2.2°C (NONE), F-Probe Tm=−9.9°C (NONE), R-Probe Tm=10.9°C (LOW) — all
  clean.
- Note: this reverse primer's 3' end (last 5 nt) does **not** meet the
  >25% GC-ratio rule — usable as a fallback probe/amplicon option but the
  reverse primer should be re-picked (shift 1-3 nt) before ordering if this
  locus is wanted as a true second target. This is flagged, not resolved,
  in this pass.
- **This probe (`CCTCAAGAAAGCAAGCACGGGA`) has a 100%-identity, full-length
  (22/22 nt) hit to a Bacteroidota bacterium genome (accession OZ524871,
  E=0.114)** — see the pair-level check below. Flagging this up front since
  it's a genuine exact match, not a rounding artifact of the table.

## Specificity status

Clean vs. genus-tier Chlamydia panel (bin/07, already established). BLAST
checked vs. human RefSeqGene, core_nt, and (follow-up) the full human genome
assembly (Human G+T database, GRCh38.p14, all chromosomes — broader than
RefSeqGene's curated-gene-loci-only scope).

**group140_probe1** (Rank-1 recommended set): no 100%-identity full-length
human match (best is 90%, 2 mismatches, high E-value in RefSeqGene). It's
the only oligo in the whole Phase 2 batch with homology to a target-relevant
non-target species: 7 hits to Chlamydia muridarum at 73.1% identity (19/26
nt, E=17.6) — well under the ~90-95% identity a TaqMan probe needs to
actually hybridize, and consistent with this gene's own bin/07 exclusivity
call (clean below 85% identity to the genus panel). No C. suis hits.

**group140_R1** (Rank-1 recommended set, reverse primer): the full-genome
follow-up search found a closer human hit than RefSeqGene had shown —
**19/20 nt identical (95% coverage, single 5' mismatch) to chromosome 7,
position 148,893,910-148,893,928, E=0.039.** This region isn't inside any
of RefSeqGene's curated gene loci, which is why the earlier, narrower search
didn't surface it. Per the project's pair-level standard: a primer matching
alone can't generate signal without its partners also binding nearby. I
checked group140_F1 and group140_probe1 — the forward primer and probe
actually used with R1 in this recommended set — against the same
chromosome, and neither has any hit within 100 kb of that position (nearest
is >100,000 bp away). **No plausible off-target amplicon.** This is the
single closest human match found anywhere in the Phase 2 batch (see
`PHASE2_SUMMARY_AND_RECOMMENDATIONS.md` for the full comparison table), so
it's worth knowing about even though it doesn't change the recommendation —
it would be the first thing to check if a human-DNA no-template control
ever showed unexpected amplification on this channel.

**group140_probe2 (the second, more distal locus above)** has the
100%-identity Bacteroidota hit noted above. A probe match alone can't
generate a false signal without a primer pair also priming that same
off-target template, so I checked: group140_R1 (a different set's reverse
primer) does hit the same accession, but at position 1,058,517-1,058,534 —
directly overlapping the probe's own site (1,058,517-1,058,538) rather than
flanking it, which isn't a workable primer/probe arrangement. No forward
primer hits this accession at all. So this locus has no plausible
off-target amplicon either, but it's the only one of the seven backup/
alternative oligo sets across the whole Phase 2 batch where a partner
oligo showed up on the same genome at all — worth being aware of if this
second locus is the one you choose to actually use, and worth re-checking
if the reverse primer here is ever re-picked (see the 3' GC note above).

Full table and the complete pair-level check across all seven 100%-identity
hits: `PHASE2_SUMMARY_AND_RECOMMENDATIONS.md`. Quality-review-tier genome
check (D13) still outstanding.
