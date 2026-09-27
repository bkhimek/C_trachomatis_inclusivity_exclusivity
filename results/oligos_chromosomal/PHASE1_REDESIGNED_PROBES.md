# Phase 1 Redesign: mutL, aroB, PSD2, group_306

**Date:** 2026-09-27
**Why:** `PHASE1_PHASE2_COMBINED_RANKING.md` found that the Phase 1 master
table's flat "Tm=60/66" values weren't the real calculated Tm of these
sequences — recomputed properly, all four probes fell short of the
project's 66°C floor and none of the four genes met the ≥5°C Tm-gap rule.
Re-running `primer3-py` directly on the *same already-established,
100%-conserved conserved windows* (not a new region — same
`results/candidate_regions/candidate_regions.tsv` coordinates used before)
returns fully compliant results for all four genes. This means the earlier
master table's sequences were very likely not the actual output of a
properly-configured primer3 run on this project's settings file — the same
"placeholder value substituted for a real calculation" pattern already
found once this session (the handover's incorrect probe-Tm claim) and once
more today (the Phase 1 BLAST E-values). The redesign below is a genuine
re-pick, not a re-labeling of the old sequences.

**Method:** identical to Phase 2 — `primer3-py` with
`config/primer3_settings.txt` settings (primer 59-61°C opt 60, probe
66-72°C opt 68, salts 50mM monovalent/3mM divalent/0.8mM dNTP/250nM oligo,
product size 80-250bp), run on the exact bin/08 conserved windows already
established and already exclusivity-clean vs. the genus panel:
mutL 1-560/1731bp, aroB 257-953/1122bp, PSD2 300-889/906bp, group_306
462-681/1521bp. Re-confirmed all four windows are **100% conserved across
all 97 primary genomes, zero variable positions** (same check used for
every other locus in this project).

## mutL

| Oligo | Sequence (5'→3') | Len | Tm | GC% | 3' GC |
|---|---|---|---|---|---|
| Forward | GTTGATTGAAAAAGGCGAGC | 20 | 60.04°C | 45.0% | pass |
| Reverse | CATCTGCGGAGATTTTTGGA | 20 | 60.04°C | 45.0% | pass |
| Probe | AGCAGGGAACGACTATTGCGGT | 22 | 68.11°C | 54.5% | — |

Product 127bp; **Tm gap 8.07°C** (preferred tier); structure LOW throughout
(no hairpin on F; low-severity hairpin/homodimer on R and probe, all well
below reaction temperature); F/R heterodimer NONE; probe 5' base A (passes
D12). This directly fixes the two structural problems flagged in the old
mutL design (HIGH-severity R-R self-dimer that was identical and
unavoidable across all 5 old ranks, and the probe's hairpin+homodimer
combination) — this reverse primer and probe are different sequences, not
re-ranked versions of the old ones.

**Ranked alternatives (same probe):**

| Rank | Forward | Reverse | Gap | Product | Secondary Structure |
|---|---|---|---|---|---|
| 2 | CGTTGATTGAAAAAGGCGAG | CATCTGCGGAGATTTTTGGA | 8.07°C | 128bp | LOW |
| 3 | GGGGTCTAAGACGTTGATTG | CATCTGCGGAGATTTTTGGA | 8.07°C | 139bp | LOW |

## aroB

| Oligo | Sequence (5'→3') | Len | Tm | GC% | 3' GC |
|---|---|---|---|---|---|
| Forward | GCCTTTCATTGCTATTCCCA | 20 | 60.04°C | 45.0% | pass |
| Reverse | AGTTTTCTAGGGCAGATCCA | 20 | 59.89°C | 45.0% | pass |
| Probe | TCGCATCGGCTCTTTTTATCTCCCT | 25 | 67.78°C | 48.0% | — |

Product 144bp; **Tm gap 7.75°C** (preferred tier); structure LOW throughout;
probe 5' base T (passes D12). This directly fixes the old aroB probe, whose
real Tm (58.6°C) was 7-9°C below the project floor and below its own
primers' Tm — the new probe sits correctly in the 66-72°C window.

**Ranked alternatives (same probe):**

| Rank | Forward | Reverse | Gap | Product | Secondary Structure |
|---|---|---|---|---|---|
| 2 | TGCCTTTCATTGCTATTCCC | AGTTTTCTAGGGCAGATCCA | 7.75°C | 145bp | LOW |
| 3 | GCCTTTCATTGCTATTCCCA | AGAGGTAGGATGGCAGAATC | 7.67°C | 231bp | LOW |

## PSD2

| Oligo | Sequence (5'→3') | Len | Tm | GC% | 3' GC |
|---|---|---|---|---|---|
| Forward | GCTTCCACTTTCCTATAGCG | 20 | 59.90°C | 50.0% | pass |
| Reverse | GGAGAAAACGTTTGGTGGAT | 20 | 60.18°C | 45.0% | pass |
| Probe | TGGTGAGGTTGCCTACGTGGAA | 22 | 67.73°C | 54.5% | — |

Product 214bp; **Tm gap 7.54°C** (preferred tier); structure LOW throughout
(mild low-severity probe hairpin/homodimer, F/R heterodimer LOW but far
below reaction temp); probe 5' base T (passes D12). Fixes the old PSD2
probe's 2.2°C Tm-floor shortfall (63.8°C → 67.73°C) and the forward
primer's Tm-ceiling overshoot (all 5 old ranks were 61.5-63.6°C vs. the
61.0°C max; this one is 59.90°C, inside the window).

**Ranked alternatives (same probe):**

| Rank | Forward | Reverse | Gap | Product | Secondary Structure |
|---|---|---|---|---|---|
| 2 | CGCTTCCACTTTCCTATAGC | GGAGAAAACGTTTGGTGGAT | 7.54°C | 215bp | LOW |
| 3 | GCTTCCACTTTCCTATAGCG | TAACTACCGGGAGAAAACGT | 7.54°C | 223bp | LOW |

## group_306

| Oligo | Sequence (5'→3') | Len | Tm | GC% | 3' GC |
|---|---|---|---|---|---|
| Forward | AAGAAGAAACCGTTGCACAA | 20 | 60.33°C | 40.0% | pass |
| Reverse | ACGAGTCTTGACTTTCTCCT | 20 | 59.82°C | 45.0% | pass |
| Probe | CTCCACCCCTCCTTCCAAAGCA | 22 | 68.15°C | 59.1% | — |

Product 90bp; **Tm gap 7.82°C** (preferred tier); structure LOW throughout
— notably **no hairpin found on any of the three oligos**, which directly
fixes the old design's unavoidable F-F dimer (present on every one of the
5 old forward-primer ranks, MED-to-HIGH severity). This is the cleanest
structural profile of any of the four Phase 1 redesigns, and the shortest
product (90bp) of the batch — this gene's conserved window is the shortest
of the four (220bp total), so there was less room to search, but primer3
still returned a fully compliant, clean set.

**Ranked alternatives:**

| Rank | Forward | Reverse | Gap | Product | Secondary Structure |
|---|---|---|---|---|---|
| 2 | AAAGAAGAAACCGTTGCACA | ACGAGTCTTGACTTTCTCCT | 7.82°C | 91bp | LOW |
| 3 | CCGCTGAAACTGAGTCTCTA | ACGAGTCTTGACTTTCTCCT | 7.53°C | 135bp | LOW |

## Summary

| Gene | Old Tm gap (as actually calculated) | New Tm gap | Old worst structure | New worst structure |
|---|---|---|---|---|
| mutL | ~3.1°C | **8.07°C** | HIGH (R-R dimer, unavoidable) | LOW |
| aroB | negative | **7.75°C** | LOW (but probe Tm 7-9°C off-spec) | LOW |
| PSD2 | ~2.2°C | **7.54°C** | LOW (but F primer Tm off-spec) | LOW |
| group_306 | ~2.7°C | **7.82°C** | MEDIUM (F-F dimer, unavoidable) | LOW |

All four redesigned sets are now in the same "preferred tier" (≥7°C gap,
LOW structure) as the strongest Phase 2 backups — this brings the whole
11-set combined ranking to a single clean tier, no more Tier 3.

## Still needed before these replace the old sequences

1. **BLAST specificity check** — these are 12 new sequences (not
   re-labelings of the old ones), so they haven't been checked yet against
   human genome / core_nt / the genus-tier Chlamydia panel the way every
   other oligo in this project has. `PHASE1_REDESIGN_FOR_BLAST.fasta` is
   ready for you to run through the same two NCBI web BLAST searches used
   throughout this project (Expect=1000, word_size=7, filter off — human
   genomic plus transcript, and core_nt with `NOT(txid813[ORGN])`). I'll do
   the same best-hit + pair-level check on the results once you send them
   back, same as every other batch this session.
2. These windows are the *same* exclusivity-clean regions already verified
   against the genus-tier Chlamydia panel (bin/07), so that check doesn't
   need re-running — only the human/core_nt specificity is new.
3. Real master-mix Mg²⁺/dNTP/oligo concentrations are still the project-wide
   placeholder (open item carried over from Phase 1/2).
