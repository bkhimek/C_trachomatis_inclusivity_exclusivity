# Phase 1 Redesign — BLAST Validation (D18 settings)

**Date:** 2026-09-27
**Scope:** Web BLAST of the 12 redesigned Phase 1 oligos (mutL, aroB, PSD2, group_306 — F/R/probe each,
from `PHASE1_REDESIGNED_PROBES.md` / `PHASE1_REDESIGN_FOR_BLAST.fasta`) against both databases required by
D18: human genome (`GPIPE/9606/current/ref_top_level GPIPE/9606/current/rna`, i.e. Human genomic plus
transcript, full assembly) and `core_nt` with `NOT(txid813[ORGN])`. Parameters confirmed from the returned
JSON: `expect=1000`, `filter=F` (low-complexity filter off), correct on both files.
**Closes open item 1** in `docs/HANDOVER.md` ("Run BLAST on the 12 redesigned Phase 1 oligos").

## Best-hit summary (44 databases-worth of hits condensed to the top of each side)

| Oligo | Len | Best human hit | E | Best non-human/non-target hit | E |
|---|---|---|---|---|---|
| mutL_redesign_F | 20 | 16/16 chr9 | 2.42 | 20/20 *Candidatus Spongiihabitans* sp. | 1.79 |
| mutL_redesign_R | 20 | 16/16 chr2 | 2.42 | 19/19 *Bacteroidota bacterium* | 7.05 |
| mutL_redesign_probe | 22 | 14/14 chr1 | 63.1 | 20/20 *Humulus lupulus* (hop) | 1.79 |
| aroB_redesign_F | 20 | 17/17 chr1 | 0.61 | **20/20 (full-length) *Chlamydia suis*, 32 accessions** | 1.79 |
| aroB_redesign_R | 20 | 18/18 chr11 | 0.16 | 17/17 *Chlamydia abortus*, 14 accessions | 110 |
| aroB_redesign_probe | 25 | 18/18 chr3 | 0.36 | 21/21 *Verrucomicrobiia bacterium* | 0.90 |
| PSD2_redesign_F | 20 | 17/17 chr15 | 0.61 | 18/18 *Mus musculus* | 27.9 |
| PSD2_redesign_R | 20 | 17/17 chr1 | 0.61 | 20/20 *Tarenaya hassleriana* | 1.79 |
| PSD2_redesign_probe | 22 | 17/17 chr13 | 1.02 | 20/20 *Pseudobutyrivibrio xylanivorans* | 1.79 |
| group_306_redesign_F | 20 | 18/19 chr3 | 9.57 | 20/20 *Marmota marmota* | 1.79 |
| group_306_redesign_R | 20 | 18/18 chr10 | 0.16 | 19/19 *Phytophthora nicotianae* | 7.05 |
| group_306_redesign_probe | 22 | 18/18 chr14 | 0.26 | 21/21 *Crotalus tigris* (rattlesnake) | 0.45 |

As with every earlier round: "100%"/"N/N" is identity over the aligned stretch shown, not full-length
coverage of the oligo, except where stated otherwise.

## Zero non-target-Chlamydia amplicon risk, despite one real shared-homology hit

**Zero hits to *C. muridarum* anywhere** (either database, any oligo, any E-value — not even a weak one).

**One notable finding, checked and cleared:** `aroB_redesign_F` and `aroB_redesign_probe` both have a
full-length, 100%-identity hit to ***Chlamydia suis***, on the same 32 accessions (essentially the whole
*C. suis* genome collection in `core_nt`), at a fixed ~71 bp separation in every case — i.e. the aroB
target region itself is conserved between *C. trachomatis* and *C. suis* at both the forward-primer site
and the probe site. That is a real, biologically meaningful shared-homology result, not noise (E=1.79 and
E=14.1, but the 32-for-32 consistency of position and distance is what makes it worth reporting).

Applying D20: **`aroB_redesign_R` has zero hits anywhere in the *C. suis* genome** — checked against all 32
accessions F/probe hit, and against *C. suis* generally (no hit at all, at any E-value up to the weakest
BLAST reported, E≈590, across ~200 accessions returned). A TaqMan reaction needs the reverse primer to bind
and extension to occur before the probe signal means anything; with no reverse-primer site on *C. suis* at
all, F+probe both matching does not translate into a plausible amplicon or false signal. **Verdict: clean,
but worth knowing** — if this primer set is ever redesigned again, note that the aroB forward-primer/probe
region sits in Chlamydia-genus-conserved sequence, so the reverse primer is carrying the genus-specificity
for this particular set.

Separately, `aroB_redesign_R` has a weak (E=110, essentially background) 17/17 hit to 14 *C. abortus*
accessions; neither the forward primer nor the probe has a hit anywhere near those same accessions, so the
same D20 logic clears it — no partner, no plausible amplicon.

## Human genome: no plausible amplicon

Applying D20 systematically (every hit with E<2 on either database — a real short near-exact match, not
background — checked for a cross-role partner, i.e. F vs. R vs. probe, on the same accession within 500 bp,
at any E-value for the partner): **zero cross-role, same-chromosome, <500 bp pairs found for any of the 12
redesigned oligos.** The only same-accession, cross-role, close-together hits that exist anywhere in the
raw data are between hits with E>37 on *both* sides (i.e. two independent ~12-16 nt coincidental matches
within 1000 bp of each other by chance across a 3.2 Gb genome) — expected background at this hit density,
not a specificity finding, and excluded from the table above by the same E<2 anchor rule used throughout
this project.

## Conclusion

All 12 redesigned Phase 1 oligos (mutL, aroB, PSD2, group_306) pass D18/D20 BLAST validation: no plausible
off-target amplicon in the human genome, zero *C. muridarum* hits, and the one *C. suis* shared-homology
hit (aroB F + probe) does not complete into an amplicon because the reverse primer does not bind there.
Combined with the Tm-gap/structure results already in `PHASE1_REDESIGNED_PROBES.md` (gaps 7.5-8.1°C, LOW
structure, D21-clean), **all four redesigned Phase 1 gene sets are now fully validated to the same standard
as Phase 2** — the last gap in the 11-set candidate inventory referenced in `PROJECT_STATE.md`'s 2026-09-27
update is closed.
