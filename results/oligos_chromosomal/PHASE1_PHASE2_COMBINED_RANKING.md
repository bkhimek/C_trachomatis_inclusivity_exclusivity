# Combined Scored Ranking: Phase 1 (redesigned) + Phase 2, and Final Panel Recommendation

**Date:** 2026-09-27 (supersedes the earlier version of this file, which was written before the Phase 1
redesign's BLAST results were back — see `PHASE1_REDESIGN_BLAST_VALIDATION.md`)

## Status check: dimer/secondary-structure QC on the redesigned Phase 1 oligos

Before scoring anything, closing a real gap: `PHASE1_REDESIGNED_PROBES.md` reported "structure LOW
throughout" for the 4 redesigned genes, but only explicitly showed each oligo's own hairpin/homodimer plus
the F-R heterodimer — not the full D21 three-way check (F-Probe, R-Probe) the way every Phase 2 document
does. Re-ran it directly with `primer3-py` (`calc_hairpin`/`calc_homodimer`/`calc_heterodimer`, same salts
as `config/primer3_settings.txt`) on all four Rank-1 sets:

| Gene | F hairpin/homodimer | R hairpin/homodimer | Probe hairpin/homodimer | F-R | F-Probe | R-Probe |
|---|---|---|---|---|---|---|
| mutL | 0.0/-30.5 (NONE) | 38.4/23.6 (LOW) | 37.6/-22.3 (LOW/NONE) | -14.2 (NONE) | -20.1 (NONE) | -3.4 (NONE) |
| aroB | 0.0/-27.3 (NONE) | 36.9/-15.8 (LOW/NONE) | 38.8/-29.0 (LOW/NONE) | -15.3 (NONE) | -19.1 (NONE) | 8.2 (LOW) |
| PSD2 | 0.0/-4.2 (NONE) | 0.0/21.3 (LOW) | 39.1/4.3 (LOW) | 1.7 (LOW) | 9.3 (LOW) | -16.8 (NONE) |
| group_306 | 0.0/-32.4 (NONE) | 0.0/9.7 (LOW) | 0.0/-26.2 (NONE) | -7.6 (NONE) | -11.7 (NONE) | -31.0 (NONE) |

(All Tm in °C; severity NONE <0°C, LOW 0-40°C, MEDIUM 40-55°C, HIGH ≥55°C — D21.) **Confirmed: no MEDIUM or
HIGH structure anywhere, including F-Probe and R-Probe, for any of the 4 redesigned Phase 1 sets.** The
D21 gap is now closed for these too — full three-way dimer QC is complete for all 13 candidate sets in the
project (4 redesigned Phase 1 + 9 Phase 2).

## Composite score, all 13 candidate sets

Score = Tm-gap component (0-25, scaled from the 5°C floor to 9°C+) + structure component (0-35: LOW=35,
MEDIUM=15, HIGH=0) + BLAST component (0-40: 40 if clean with no standout single-oligo hit, 35 if clean but
with a notable hit worth a human/non-target watch-note — always cleared at the pair level, D20, in every
case in this project). This is a design-margin score, not a specificity risk score — everything below has
already passed the pair-level BLAST check; the score just orders how much *cushion* each set has.

| Rank | Gene / Set | Tm gap | Structure | BLAST note | Score |
|---|---|---|---|---|---|
| 1 | **mutL** (Phase 1 redesign) | 8.07°C | LOW | clean, unremarkable | **94.2** |
| 2 | **group_306** (Phase 1 redesign) | 7.82°C | LOW | clean, unremarkable | **92.6** |
| 3 | **PSD2** (Phase 1 redesign) | 7.54°C | LOW | clean, unremarkable | **90.9** |
| 4 | **aroB** (Phase 1 redesign) | 7.75°C | LOW | clean; F+probe share a *C. suis*-conserved locus, cleared (no R hit there) | **87.2** |
| 5 | **PSD2 Alt 1** (Phase 2) | 6.81°C | LOW | clean, unremarkable | **86.3** |
| 6 | group_181 locus 1 (Phase 2) | 6.47°C | LOW | clean, unremarkable | 84.2 |
| 7 | **aroB Alt 1** (Phase 2) | 6.44°C | LOW | clean, unremarkable | **84.0** |
| 8 | group_159 (Phase 2) | 7.06°C | LOW | clean; probe has a tight human hit (E≈0.02), cleared | 82.9 |
| 9 | **aroB Alt 2** (Phase 2) | 7.00°C | LOW | clean; F has a tight human hit (E≈0.04, ERBB4), cleared | **82.5** |
| 10 | group_140 locus 1 (Phase 2) | 6.84°C | LOW | clean; R1 has the tightest human hit in the project (E≈0.04, chr7), cleared | 81.5 |
| 11 | PSD2 Alt 2 (Phase 2) | 8.71°C (best raw gap) | **MEDIUM — fwd-primer hairpin, flagged** | clean | 78.2 |
| 12 | group_181 locus 2 (Phase 2) | 8.61°C | **MEDIUM — flagged, cause TBD** | clean | 77.6 |
| 13 | group_140 locus 2 (Phase 2) | 6.81°C | **MEDIUM — reverse primer fails the 3' GC-stability rule, flagged** | clean; shares the notable region | 61.3 |

**Bold** = the four original Phase 1 genes, redesigned. Every set above the line at rank 10 is fully clean
(no flags); ranks 11-13 are the three components already identified as needing a re-pick before ordering.

## Recommendation: you now have more than enough — here's the natural 2-4 target panel

You said 5-10 good sets against 2-4 targets is enough and we should stop optimizing past that point. The
scoring above makes the answer straightforward: **the four original Phase 1 genes — mutL, aroB, PSD2,
group_306 — are also, now that the redesign is BLAST-validated, the four highest-scoring, cleanest targets
in the whole project**, and between them they already provide 7 fully-validated sets with zero open flags:

- **mutL** — 1 set (no independent backup locus exists in this gene's conserved window; it's short)
- **aroB** — 3 independent sets (the redesign at 257-953bp, Alt 1 at 1-125bp, Alt 2 at 955-1078bp — three
  genomically separate loci within the same gene, so a real primary + 2 backups)
- **PSD2** — 2 clean sets (the redesign at 300-889bp, Alt 1 within 49-253bp) + PSD2 Alt 2 available as a
  3rd backup once its forward-primer hairpin is re-picked, if you ever want it
- **group_306** — 1 set

That's **7 validated sets across 4 targets**, right in the middle of the 5-10/2-4 range you asked for, and
every one of the 7 scores ≥82.5 — no flags, no re-picks needed, nothing pending except the D13
quality-review-tier genome check (not yet done for any of the 11 sets, including these 7) and the
project-wide master-mix-concentration placeholder.

**My recommendation: adopt these 7 sets across mutL/aroB/PSD2/group_306 as the final chromosomal panel, and
park group_159/group_140/group_181 as documented-but-unused backups** (already fully designed and
validated in `PHASE2_*` docs, in case any of the primary 4 genes fails wet-lab testing later) rather than
spending more time on them or on the two flagged Phase 2 components (PSD2 Alt 2, group_140 locus 2) — they
don't add anything the current 7 don't already cover, and fixing them isn't necessary to hit your target.
This also has the advantage of being the simplest story for a handover document: 4 genes, not 7.

If you'd rather use group_159/181 in place of, say, mutL/group_306 (both single-set genes with no backup),
that's a reasonable alternative reading of "good enough" too — happy to swap the recommendation if you'd
prefer backup depth over sticking with the four original targets. Otherwise, the oligo-design phase of this
project is substantively done pending the D13 check.
