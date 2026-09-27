# Lessons learned

New file (flagged as an open item in `docs/HANDOVER.md` since 2026-09-24, written 2026-09-27). Synthesizes
lessons from the whole project so far, including from two informal QC documents written during an
untracked side session on 2026-09-24/26 (`01_LESSONS_LEARNT.md`, `02_PROJECT_STATUS.md`, OneDrive
`Claude outputs/previous/`). Those two documents are treated here as source material, not as settled
conclusions — several of their specific claims did not survive independent re-checking this session (see
below), even though some of their organizational advice still holds. Where this file and either of them
disagree, this file is correct; see `docs/PROJECT_STATE.md`'s 2026-09-27 update for the full evidence.

## 1. The one lesson that matters most: verify, don't transcribe

Every serious problem found in this project so far has the same shape: a document stated a specific number
or a "checked, passes" verdict, and the number turned out to be a placeholder or the verdict turned out to
be incomplete, only caught because someone (the project owner, or a later session) went back to the actual
data and recalculated.

Four concrete instances, earliest to latest:

- **The original project handover** stated a TaqMan probe Tm target of "~60°C (standard for TaqMan)". The
  project's own settings file (`config/primer3_settings.txt`, D7) says 66-72°C. A 6-12°C error in a core
  design parameter, stated as if it were a known standard.
- **The 2026-09-26 oligo master table** (untracked side session) recorded Tm=60°C (primers) / 66°C
  (probes) for all 44 mutL/aroB/PSD2/group_306 oligos — suspiciously uniform for 44 different sequences of
  varying length and GC%. Recomputing directly with `primer3-py` (cross-checked with an independent
  nearest-neighbor calculation, agreement within ~1°C) found the real Tm gap failed the project's own ≥5°C
  floor for all four genes, and one gene's probe Tm was actually *below* its primers' — the opposite of
  what a TaqMan assay needs. Nobody had actually run the calculation; the target values from the settings
  file had apparently been copied into the "result" column.
- **The same table's BLAST section** stated "42 weak human DNA matches (all E > 1)" and, for one specific
  oligo, a note of "Weak human DNA E=7.05". Re-running the same 44 oligos through web BLAST with the
  correct short-sequence parameters (see §2) found several oligos with E<1, including one full-length,
  zero-mismatch 19/19 nt match to a human chromosome — not weak by any definition, and the earlier note's
  own E-value for that exact oligo doesn't reproduce.
- **A same-session draft of the Phase 2 specificity report** (this session) stated "all oligos pass"
  immediately above a table row showing a probe with a 100%-identity, full-length hit to a bacterium — an
  overclaim caught by the project owner reading the table, not by the model. That correction is what
  established the pair-level check (D20) used for everything afterward.

**The pattern:** overconfident, specific-sounding numbers are the most dangerous kind of error, because
they read as verified. A vague claim invites scrutiny; a precise one (an E-value, a Tm to two decimal
places, a percentage) tends not to. The fix that actually worked every time was the same: re-derive the
number from the primary data (the raw BLAST JSON, the actual sequence run through the actual Tm formula)
rather than trusting a summary table, and cross-check with a second, independent method when the finding
is consequential enough to act on. Do this by default for any number that will drive a go/no-go decision,
not only when something looks suspicious — the Tm error above looked perfectly normal (round numbers,
consistent across every row) until someone actually ran the calculation.

## 2. Specific methodological corrections (see PROJECT_STATE.md D18-D21 for the formal decisions)

- **BLAST parameters for short oligos:** Expect threshold=1000, word_size=7, low-complexity filter OFF.
  The stricter defaults many BLAST UIs start with (Expect≈0.001-10, filter on) are tuned for longer
  queries and will under-report or miss real short exact/near-exact matches. Always confirm the `params`
  block in the returned JSON shows what you intended — don't assume the UI defaults are fine for a ~20 nt
  query.
- **Human-genome database choice:** a curated gene-loci database (e.g. NCBI RefSeqGene, ~656 Mb) is good
  coverage of where a match would matter most, but it is not the full genome — a hit sitting in intergenic
  or otherwise non-curated sequence won't show up. Follow up with the full assembly (+transcripts) database
  before treating human specificity as closed. E-values are not comparable between databases of different
  sizes; if you need to check whether a hit is "the same" one seen in a smaller database, the two E-values
  should differ by roughly the ratio of database sizes — if they don't, it's probably a different hit,
  not a rescaled one.
- **Off-target hits are a pair-level question, not a single-oligo one.** A primer or probe matching an
  off-target sequence, by itself, cannot generate a false signal — TaqMan detection requires an actual PCR
  product first. Before accepting or rejecting a design on a BLAST hit, check whether a partner oligo from
  the *same designed set* also hits nearby (same accession, plausible product distance, workable
  orientation). This turns "should we worry about this hit" from a judgment call about organism plausibility
  into a mechanical, checkable question. It also means a single-oligo summary statistic ("% identity to
  human/non-target") is useful context but should never be the pass/fail criterion by itself.
- **Secondary-structure checks need to cover every pair in the tube.** A TaqMan reaction has three oligos
  (F, R, probe); checking only the F-R heterodimer (as the untracked side session's custom detector did)
  misses F-Probe and R-Probe. Use a validated library (`primer3-py`'s `calc_hairpin`/`calc_homodimer`/
  `calc_heterodimer`, which wraps the same thermodynamics engine as primer3 itself) rather than a
  hand-written detector, and classify severity by the structure's own melting Tm relative to reaction
  temperature — primer3's binary "structure found" flag fires on any negative ΔG, including structures
  that melt at -30°C and are irrelevant at any real annealing temperature.
- **A design constraint you didn't choose is worth re-testing, not just documenting.** The untracked side
  session described mutL's reverse-primer self-dimer and group_306's forward-primer self-dimer as
  unavoidable "design choices" / "genomic constraints" specific to those regions, present across every one
  of the 5 ranked alternatives primer3 had returned. Actually re-running primer3 on the same conserved
  window from scratch produced a completely different, dimer-free set for both genes on the first attempt.
  The original run's 5 "alternatives" were all minor shifts of the same underlying pick (typical of
  primer3's own ranking), which is why they all shared the same flaw — a real independent re-design,
  not just picking a different one of the 5 already-offered ranks, found the actual fix. Don't conclude a
  problem is structural to the target region until a fresh design attempt has actually failed to avoid it.

## 3. What worked and is worth keeping

- **Splitting deliverables by audience** (the untracked session's six-document structure — index,
  technical deep-dive, executive summary, BLAST detail, wet-lab plan) is a reasonable pattern for a project
  with several stakeholders, and this session followed a similar shape (one file per gene, one summary/
  ranking file, one BLAST-input FASTA). Keep a short index note when the file count grows past 4-5.
- **Stratifying BLAST results by gene and by oligo component** (forward/reverse/probe) surfaced real
  differences between genes that an aggregate count would have hidden, and this session's per-gene,
  per-oligo tables followed the same approach.
- **Treating structural/Tm issues and specificity issues as different categories with different fixes**
  is correct: a Tm-gap or dimer problem is fixable by redesign (as this session's Phase 1 redesign showed —
  what looked unfixable wasn't), while a genuine specificity problem (a real off-target amplicon) would
  usually mean the target region itself needs to change. Keep that distinction; just verify which bucket a
  given finding is actually in (§1) before deciding it can't be fixed.
- **Recording every real conserved-window/exclusivity number from the primary alignment data directly**,
  rather than from a summary, worked well in both Phase 1 (bin/07-09) and Phase 2 (this session's
  group_159/140/181 conservation and 97/97-genome-presence checks) and should stay the standard: read the
  `.aln.fas` files and recompute, don't trust a table's summary of them without spot-checking.

## 4. Recommendations for the next session or project lead

1. **Any number that will drive a decision gets recomputed from primary data before it's trusted**,
   especially Tm, Tm gap, and BLAST E-values/identity. If a report states a value without showing how it
   was derived, don't build on it — regenerate it.
2. **Cross-check consequential calculations two independent ways** (this project's pattern: `primer3-py`
   + Biopython for Tm; direct alignment inspection + a summary `.tsv` for gene presence/conservation).
   Agreement within ~1°C or an exact match is the bar; a bigger gap means something is wrong and needs
   investigating before proceeding, not averaging away.
3. **State exactly what was checked, not just the verdict.** "All oligos pass" needs a definition of pass;
   "checked against human genome" needs the database name and BLAST parameters. This session's specificity
   sections list the exact database, parameters, and the pair-level check performed on every notable hit —
   keep doing that even when (especially when) the answer is "no problem found."
4. **Don't let side-channel work sessions run without touching the decision log.** The four-gene design
   work happening entirely outside `docs/PROJECT_STATE.md` for two days is what let an unverified Tm value
   and an incomplete BLAST pass ship as "ready for wet-lab validation." Every session, whatever tool or
   environment it runs in, should end by adding to `docs/PROJECT_STATE.md` and rewriting `docs/HANDOVER.md`
   — this file's own creation, three days later than it should have been possible, is the example of what
   happens when that's deferred.
5. **A redesign attempt is cheap; don't skip straight to "it's a constraint."** When a project rule fails
   (Tm gap, a dimer, an exclusivity threshold) on the first design pass, try a genuinely fresh design
   before writing it up as an inherent limitation of the target region.
6. **Keep the pair-level specificity check and the three-way (F-R/F-Probe/R-Probe) dimer check as
   permanent parts of the QC pipeline** for every future gene, including the plasmid target once that work
   starts — they're now the project's standard (D20, D21), not one-off fixes for the genes that prompted
   them.
