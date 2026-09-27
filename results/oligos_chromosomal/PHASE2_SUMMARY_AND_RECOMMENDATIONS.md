# Phase 2 Summary and Recommendations

**Date:** 2026-09-27
**Scope:** Backup oligo sets for group_159, group_140, group_181; alternative
oligo sets for aroB and PSD2 (existing primary designs unchanged).
**Companion files:** `PHASE2_GROUP159_OLIGO_DESIGN.md`,
`PHASE2_GROUP140_OLIGO_DESIGN.md`, `PHASE2_GROUP181_OLIGO_DESIGN.md`,
`PHASE2_AROB_PSD2_ALTERNATIVES.md`, `PHASE2_OLIGOS_FOR_BLAST.fasta`

## What changed from the handover, and why

1. **Probe Tm target corrected.** The handover stated "~60°C (standard for
   TaqMan)" for probes. The project's actual rule (`config/primer3_settings.txt`,
   decisions D6/D7/D10-D12) is probe Tm 66-72°C (opt 68), primer Tm 59-61°C
   (opt 60), with a hard floor of a 5°C Tm gap (probe minus higher primer),
   7°C+ preferred. All designs below use the real target. The existing
   mutL/aroB/PSD2/group_306 designs already used 66°C probes correctly, so
   nothing there needs rework.
2. **Conserved-fragment mapping done from the real 97-genome Panaroo
   alignments**, not from a summary table, per-gene
   (`results/pangenome/aligned_gene_sequences/*.aln.fas`). This let me
   verify — rather than assume — where the true variable positions are.
3. **Finding that changes the design approach:** group_159, group_140 and
   group_181's exclusivity windows are each **100% conserved across all 97
   primary genomes, with zero intra-species variable positions.** The
   "map conserved blocks separated by variable gaps" strategy in the
   handover doesn't apply to these three — there's nothing to fragment
   around. Each window is one contiguous, safe design surface, and the
   "multiple targets per gene" goal is met instead by finding a second,
   well-separated probe site within the window where the window is long
   enough (group_140, group_181; not group_159, which is too short).

## Recommended oligo sets (ranked)

| Priority | Gene | Role | Product | Tm gap | Secondary Structure | Notes |
|---|---|---|---|---|---|---|
| 1 | group_140 | Backup | 169 bp | 6.84°C | LOW | Longest, cleanest window; genuine 2nd probe site available |
| 2 | group_181 | Backup | 155 bp | 6.47°C | LOW | 2nd probe site has best gap (8.61°C) of the whole batch |
| 3 | group_159 | Backup | 109 bp | 7.06°C | LOW | Shortest window; single-target only |
| 4 | aroB Alt 2 (955-1078) | Alternative | 82 bp | 7.00°C | LOW | Fully independent locus from primary aroB design |
| 5 | aroB Alt 1 (1-125) | Alternative | 101 bp | 6.44°C | LOW | Fully independent locus from primary aroB design |
| 6 | PSD2 Alt 1 (site A) | Alternative | 82 bp | 6.81°C | LOW | |
| 7 | PSD2 Alt 2 (site B) | Alternative | 147 bp | 8.71°C | MEDIUM | Best gap for PSD2, but forward primer has a non-trivial hairpin — re-pick before ordering if chosen |

All seven pass the D12 post-filter (Tm gap ≥5°C, probe 5' base not G) and
have clean 3' GC stability on both primers, except the group_140 second
probe locus (flagged separately, reverse primer needs a 1-3 nt shift) and
the PSD2 Alt 2 forward primer (MEDIUM hairpin, flagged above).

## Probe length, oligo-dimer, and gene-presence checks

Three follow-up checks, answered here for all nine Phase 2 oligo sets
(group_159, group_140 x2 loci, group_181 x2 loci, aroB Alt1/Alt2, PSD2
Alt1/Alt2):

**1. Probe length.** All nine probes are within the project's 20-28 nt
probe-length spec (opt 22):

| Set | Probe | Length |
|---|---|---|
| group_159 | ACCCACAGCTCACTCAGAATCCA | 23 nt |
| group_140 locus 1 | AGTCACAGGAAGAAATATCCCTCGCA | 26 nt |
| group_140 locus 2 | CCTCAAGAAAGCAAGCACGGGA | 22 nt |
| group_181 locus 1 | AGAAGCTGCTAGAACACTCTCTCTGT | 26 nt |
| group_181 locus 2 | TGGTACTAAAAACATGGGGTTACCGAGG | 28 nt |
| aroB Alt 1 | TCTCCTCACCCTATTCACCTAGTTGAT | 27 nt |
| aroB Alt 2 | AGAAGAGATCGGACTAGCAGCTTCT | 25 nt |
| PSD2 Alt 1 | TGTAAGAATAGCCTGTTTTCCCGTATCG | 28 nt |
| PSD2 Alt 2 | AGGCTGGTGTCAAAGACTGCGA | 22 nt |

Two (group_181 locus 2, PSD2 Alt 1) sit right at the 28 nt ceiling — still
compliant, just worth knowing if you want a smaller design margin.

**2. Oligo-dimer check.** Yes — but the original design pass only reported
each oligo's own homodimer/hairpin and the F-R heterodimer explicitly; it
didn't separately call out F-Probe and R-Probe heterodimers (all TaqMan
sets need all three cross-pairs checked, since the probe is in the same
tube as both primers). I've now run `calc_heterodimer` on all three pairwise
combinations (F-R, F-Probe, R-Probe) for all nine sets — **every single one
comes back LOW or NONE severity** (melting Tm well below the ~60°C
reaction/annealing temperature); nothing MEDIUM or HIGH. Per-set numbers
are now recorded in each gene's own design file
(`PHASE2_GROUP159/140/181_OLIGO_DESIGN.md`, `PHASE2_AROB_PSD2_ALTERNATIVES.md`).
The only structural flags in this whole batch remain the two already
called out above (group_140 locus 2's reverse-primer 3' GC issue, and
PSD2 Alt 2's forward-primer hairpin) — both are single-oligo
hairpin/3'-stability issues, not cross-oligo dimers.

**3. Gene presence across all 97 primary genomes.** Checked directly
against the Panaroo per-gene alignments, not just inferred from the
conservation call: `group_159.aln.fas`, `group_140.aln.fas`, and
`group_181.aln.fas` each contain exactly **97 sequences, one per primary
genome, all with real (non-empty) coding sequence** — group_159 at
720-732 bp (matches its 732 bp reference length, small length variation
consistent with the gene's own indel positions outside the 100%-conserved
design window), group_140 at exactly 852 bp in all 97, group_181 at exactly
591 bp in all 97. `results/candidate_regions/candidate_regions.tsv`
independently reports `avg_copies=1.00` and `n_genomes_aligned=97` for all
three, confirming single-copy presence in every one of the 97 primary
genomes — not just conservation *where present*. (aroB and PSD2's
alternative loci are sub-regions of the same full-gene alignments already
established as 97/97-present for the primary aroB/PSD2 design, so this
doesn't need re-checking for the alternatives.)

## BLAST validation results (2026-09-27, web BLAST, blastn, Expect=1000, word_size=7, filter off)

You ran three searches on all 28 oligo sequences in `PHASE2_OLIGOS_FOR_BLAST.fasta`:
human genome (NCBI `genomic/9606/RefSeqGene`, curated gene loci), whole
database (`core_nt`, with `NOT(txid813[ORGN])` to exclude C. trachomatis
itself, so every hit returned is a genuine non-target organism), and a
follow-up against the full human genome assembly (`Human genomic plus
transcript` / Human G+T — see the dedicated subsection below) to close the
RefSeqGene search's curated-loci-only scope.

**Verdict, precisely stated: no oligo *set* (primer pair + probe, checked
together) has a plausible off-target amplicon in either database.** That's
narrower than "every oligo has zero notable hits" — several individual
oligos do have 100%-identity matches to something (see table and the
pair-level check below); what was verified is that none of those matches
combine with a partner primer from the same design into a workable PCR
product, which is what would actually be needed to generate a false
signal. See "Pair-level check" below for exactly how this was confirmed —
an earlier draft of this section stated a blanket "all pass" without that
check; this version replaces it.

| Oligo | Len | Best human hit | Human E | Best non-target (excl. Ct) hit | E |
|---|---|---|---|---|---|
| group159_F1 | 20 | 15/20 (75%) | 129 | 19/20 (95%) uncultured Bacteroidota bacterium | 7.05 |
| group159_R1 | 20 | 17/20 (85%) | 8.24 | 20/20 (100%) Granulicella sp. | 1.78 |
| group159_probe1 | 23 | 20/23 (87%) | **0.00379** | 22/23 (96%) Saimiri boliviensis | 7.05 |
| group159_F2 | 20 | 16/20 (80%) | 32.6 | 19/20 (95%) Nocardia sp. | 435 |
| group159_R2 | 20 | 18/20 (90%) | 2.09 | 19/20 (95%) Filimonas lacunae | 7.05 |
| group140_F1 | 20 | 18/20 (90%) | 129 | 19/20 (95%) Winogradskyella sp. | 7.05 |
| group140_R1 | 20 | 18/20 (90%) | 2.09 | 19/20 (95%) Rutilus rutilus | 7.05 |
| group140_probe1 | 26 | 19/26 (73%) | 1.32 | 23/26 (88%) Pyrinomonadaceae bacterium — **+ 7 hits to C. muridarum at 19/26 (73%), E=17.6** | 4.46 |
| group140_R2_2ndlocus | 20 | 18/20 (90%) | 2.09 | 19/20 (95%) Pseudomonas sp. | 7.05 |
| group140_probe2_2ndlocus | 22 | 18/22 (82%) | 3.13 | 22/22 (100%) Bacteroidota bacterium | 0.114 |
| group181_F1 | 20 | 17/20 (85%) | 8.24 | 19/20 (95%) uncultured Leptospiraceae bacterium | 7.05 |
| group181_R1 | 20 | 17/20 (85%) | 8.24 | 19/20 (95%) Rhodospirillaceae bacterium | 7.05 |
| group181_probe1 | 26 | 18/26 (69%) | 0.0846 | 23/26 (88%) Porites lutea | 4.46 |
| group181_F2_2ndlocus | 20 | 18/20 (90%) | 2.09 | 19/20 (95%) Esox lucius | 7.05 |
| group181_R2_2ndlocus | 20 | 16/20 (80%) | 32.6 | 20/20 (100%) Thalassotalea sp. | 1.78 |
| group181_probe2_2ndlocus | 28 | 18/28 (64%) | 5.74 | 20/28 (71%) Phycodurus eques | 5.35 |
| aroB_alt1_F | 19 | 14/19 (74%) | 6.18 | 19/19 (100%) Myxococcota bacterium | 7.05 |
| aroB_alt1_R | 20 | 17/20 (85%) | 0.134 | 20/20 (100%) Vitis vinifera | 1.78 |
| aroB_alt1_probe | 27 | 18/27 (67%) | 5.22 | 22/27 (81%) Sphingobacterium daejeonense | 17.6 |
| aroB_alt2_F | 21 | 18/21 (86%) | **0.0423** | 19/21 (90%) uncultured Chryseotalea sp. | 7.05 |
| aroB_alt2_R | 20 | 17/20 (85%) | 8.24 | 20/20 (100%) Lingula anatina | 1.78 |
| aroB_alt2_probe | 25 | 19/25 (76%) | 73.3 | 21/25 (84%) Roseibium sp. | 55.7 |
| PSD2_alt1_F | 20 | 16/20 (80%) | 0.528 | 19/20 (95%) Acidobacteriaceae bacterium | 435 |
| PSD2_alt1_R | 19 | 16/19 (84%) | 0.396 | 19/19 (100%) Rosa chinensis | 7.05 |
| PSD2_alt1_probe | 28 | 20/28 (71%) | 22.7 | 24/28 (86%) Eucommia ulmoides | 83.6 |
| PSD2_alt2_F | 20 | 18/20 (90%) | 2.09 | 19/20 (95%) Ceratotherium simum simum | 435 |
| PSD2_alt2_R | 21 | 17/21 (81%) | 10.3 | 20/21 (95%) Varanus komodoensis | 1.78 |
| PSD2_alt2_probe | 22 | 17/22 (77%) | 12.4 | 21/22 (95%) Streptococcus pantholopis | 27.9 |

**How to read this:**
- **No 100%-identity, full-length human hit anywhere** — the closest any
  oligo gets is 90% (2 mismatches in a 20mer). That's the headline result:
  none of these 14 oligos have a real human binding site.
- **Two hits worth knowing about, not worth rejecting the oligo over:**
  group159_probe1 (87% identity to DNAJC5, E=0.00379) and aroB_alt2_F (86%
  identity to ERBB4, E=0.0423) are the only human hits with an E-value low
  enough to be more than chance for a sequence this short. Both still carry
  2-3 mismatches distributed across the oligo — TaqMan probes and primers
  generally need near-perfect complementarity to anneal/hybridize
  productively, so partial homology like this is very unlikely to cause
  a real false-positive signal, but they're the ones to watch first if
  anything unexpected shows up in a human-DNA no-template-control well.
- **group140_probe1 is the only oligo with any hit to a non-target
  Chlamydia species** — 7 hits to C. muridarum, all at 73.1% identity
  (19/26 nt, 7 mismatches), E=17.6. This is well below the ~90-95% identity
  TaqMan probes typically need to hybridize and generate signal, and it's
  consistent with bin/07's own exclusivity threshold (genes are called
  "exclusivity-clean" below 85% identity to the genus panel) — expected
  residual genus-level homology, not a cross-reactivity risk. No C. suis
  hits were found for this or any other oligo.
- **The "100% full-length" hits in the core_nt column** (Granulicella,
  Bacteroidota bacterium, Vitis vinifera/grape, Rosa chinensis/rose,
  Lingula anatina, Thalassotalea, Myxococcota bacterium, etc.) are real,
  exact matches — not something to wave away by species name alone. What
  makes them non-actionable is checked explicitly below, not assumed.

### Pair-level check on every 100%-identity hit

A probe alone matching 100% cannot generate a false TaqMan signal — the
probe only fluoresces if a PCR product already exists spanning its site,
which needs the forward AND reverse primer from the same design to also
bind and prime nearby, in the right orientation, on that same off-target
template. So every 100%-identity, full-length hit in the table above was
checked against every other oligo in its own designed set, on the exact
same accession:

| 100%-identity hit | Organism (accession) | E | Any partner oligo from the same set also hits that accession? |
|---|---|---|---|
| group159_R1 | Granulicella sp. (OZ533717) | 1.78 | No |
| group181_R2_2ndlocus | Thalassotalea sp. / Gilliamella apis | 1.78 | No |
| aroB_alt1_F | Myxococcota bacterium / CP200281 | 7.05 | No |
| aroB_alt1_R | Vitis vinifera (OZ252944) | 1.78 | No |
| aroB_alt2_R | Lingula anatina (3 accessions) | 1.78 | No |
| PSD2_alt1_R | Rosa chinensis / Fragaria vesca / others | 7.05 | No |
| **group140_probe2_2ndlocus** | **Bacteroidota bacterium (OZ524871)** | **0.114** | **group140_R1 hits the same accession (18/20, E=27.9), but at position 1,058,517-1,058,534 — overlapping the probe's own site (1,058,517-1,058,538), not flanking it. A primer and probe occupying the same physical bases can't function together in a real amplicon. No forward primer (group140_F1) hits this accession at all.** |

None of the seven produce a plausible off-target amplicon. The Bacteroidota
case (E=0.114) is the one that actually warranted this check — it's a
meaningfully lower E-value than the others and deserved more than a
by-species dismissal — and it still comes back clean on the mechanism that
matters. Separately, that accession (`MFD15205`) is from the Microflora
Danica soil-microbiome survey — an environmental isolate with no plausible
route into a genital swab specimen, which is a second, independent reason
it's not a real-world concern.

The same pair-level check was run on the two most significant human hits:
neither group159_F1/F2/R1/R2 (partners of group159_probe1) nor
aroB_alt2_R/probe (partners of aroB_alt2_F) hit the same human gene locus
as their flagged partner oligo. No plausible off-target human amplicon
either.

**Scope note (now closed, see below):** the search above used NCBI's
`RefSeqGene` database (curated representative gene loci, ~656 Mb across
6,843 sequences) rather than the full genome assembly. That's good coverage
of exactly the regions where an off-target match would matter most
(annotated genes), but it didn't rule out a match sitting in intergenic or
repetitive DNA outside those curated loci. That gap is now closed — see the
follow-up search immediately below.

### Follow-up: full human genome search (Human G+T database)

You re-ran all 28 oligos against NCBI's **"Human genomic plus transcript"**
database (`GPIPE/9606/current/ref_top_level` + `.../rna` — the full GRCh38.p14
primary assembly, all 24 chromosomes, plus RNA transcripts; 186,890
sequences, ~4.0 Gb total, vs. RefSeqGene's ~656 Mb), same short-sequence
parameters (Expect=1000, filter off). This is strictly broader than the
RefSeqGene search — every curated gene locus is a subset of the full
chromosome it sits on — so it closes the scope caveat above rather than
replacing the result.

**Important: E-values from this database are not comparable to the
RefSeqGene table above.** E-value scales with search-space size, and this
database is ~6x larger, so the same exact hit gets a proportionally higher
(worse-looking) E-value here purely from database size, not from any change
in match quality. Two hits confirm this arithmetic directly: group159_probe1
DNAJC5 (RefSeqGene E=0.00379 → Human G+T E=0.0199, ratio 5.2x) and
aroB_alt2_F ERBB4 (RefSeqGene E=0.0423 → Human G+T E=0.207, ratio 4.9x) —
both ≈6x, confirming these are the *same* two hits already known, not new
ones, just re-scaled for the bigger database.

**Result: still no 100%-identity, full-length human hit anywhere.** Every
hit in this database is a partial-length exact match (identity runs of
13-20 nt embedded in longer 19-28 nt oligos, at most 95% query coverage) —
consistent with, and slightly finer-grained than, the RefSeqGene result.

| Oligo | Best human hit (Human G+T) | Identity | Coverage | E | New vs. RefSeqGene table? |
|---|---|---|---|---|---|
| group159_probe1 | chr8 (DNAJC5 locus) | 20/20 (100%) | 87% | 0.0199 | Same hit, rescaled |
| group140_R1 | **chr7, 148,893,910-148,893,928** | 19/20 (100%) | **95%** | **0.0393** | **New — not in RefSeqGene table** |
| PSD2_alt2_F | chr5 | 18/20 (100%) | 90% | 0.155 | New (was 90%/E=2.09 in old table — same call, tighter E) |
| aroB_alt2_F | chr2 (ERBB4 locus) | 18/21 (100%) | 86% | 0.207 | Same hit, rescaled |
| group140_probe1 | chr7 | 18/26 (100%) | 69% | 0.414 | Similar tier to before |
| group181_probe1 | chr8 | 18/26 (100%) | 69% | 0.414 | Similar tier to before |
| all other 22 oligos | various chromosomes | ≤17/20 | ≤85% | ≥0.5 | Same tier as RefSeqGene table (chance-level) |

The one genuinely new, notable finding is **group140_R1's chr7 hit — 19/20
nt identical (only the 5'-most base differs), 95% coverage, E=0.039.** This
wasn't visible in the RefSeqGene search because it doesn't sit inside any of
NCBI's 6,843 curated gene loci — it's evidently intergenic or otherwise
non-curated. At 19/20 with a single mismatch this is the closest any oligo
in the whole Phase 2 batch comes to a human sequence, so it got the same
pair-level check as before: **group140_F1 and group140_probe1 — the two
oligos actually combined with R1 in the recommended group_140 amplicon —
have no hit anywhere near chr7:148,893,910-928** (nearest hit from either
is >100 kb away on that chromosome). No plausible amplicon, same conclusion
as every other flagged hit in this project. The weaker chr8 hit for the
same query also has no partner nearby.

The same check was repeated for every hit in the table above with E<1
(group159_probe1's chr8/chr9/chr15 hits, group140_probe1's chr7 hit,
group181's chr2/chr8/chr6 hits, aroB_alt1_R's chr7 hit, aroB_alt2_F's chr2/
chr3 hits, PSD2_alt1_probe's chr8/chr16 hits, PSD2_alt2_F's two chr5 hits) —
**zero have a partner oligo from their own designed set within a plausible
product distance on the same chromosome.** Full genome-wide human
specificity is now confirmed clean at the pair level, closing the earlier
scope caveat.

## Other open items before wet-lab / ordering

1. **Quality-review-tier genomes (10 genomes, D13) — not checked.** These
   designs were built only from the 97 primary genomes. D13 says every
   oligo should also be tested against the quality-review tier and reported
   separately. I can pull those 10 genomes' sequences at this locus and
   check in the next pass if you want that before finalizing.
2. **group_140 second-probe reverse primer** and **PSD2 Alt 2 forward
   primer** need a quick re-pick (shift a few nt) if either of those two
   specific sets is one you want to actually order — flagged earlier, not
   blocking the other 5 sets.
3. **Real master-mix Mg²⁺/dNTP/oligo concentrations** are still placeholders
   in `config/primer3_settings.txt` (open item #2, HANDOVER.md) — all Tm
   values above will shift slightly once real conditions are supplied.

## Docs reconciliation (deferred to end of session, per your earlier answer)

`docs/HANDOVER.md` and `docs/PROJECT_STATE.md` are still at their Sep
24-25 state (pipeline paused at "consensus built for top-30, awaiting BLAST
validation before Primer3 design"). They don't yet reflect: Phase 1
complete (mutL/aroB/PSD2/group_306 designed and BLAST-validated) or this
Phase 2 work. I'll write the update at the end of this session as agreed —
flagging it here so it isn't lost.
