# HANDOVER: read this first at the start of every session

Short, current-state file. Rewritten at the end of each session. Long-term decisions and findings live in
`docs/PROJECT_STATE.md` (decision log D1-D22 + findings). If this file and PROJECT_STATE disagree, ask the user.

Last updated: 2026-09-27 (Phase 2 design + Phase 1 correction/redesign/BLAST session; final chromosomal panel locked in; docs committed to git this session)

## Project
In-silico design of a multiplex PCR/TaqMan assay for *Chlamydia trachomatis*: chromosomal targets + multicopy-plasmid
target (nvCT-aware). Goal: inclusivity across C. trachomatis genomes, exclusivity vs. related/clinical species,
then primer/probe design. Owner: Krzysztof Gizynski.

## Read this before trusting anything dated before 2026-09-27
Between the 2026-09-25 pipeline-status update and now, the actual primer/probe design and QC for
mutL/aroB/PSD2/group_306 happened in a side session that never went through this file or PROJECT_STATE.md
(deliverables in OneDrive `Claude outputs/previous/`, dated 2026-09-24 to 26). That side session's Tm
values and several of its QC conclusions did not survive independent re-checking — see PROJECT_STATE.md's
2026-09-27 update for the full story, and `docs/lessons_learned.md` for why this happened and how to avoid
it again. **Anything from that side thread (OLIGO_MASTER_TABLE_COMPLETE.md, 01/02/03_*.md, etc.) should be
treated as superseded, not as ground truth**, for the four genes it covers.

## Paths (do not guess others)
- WSL repo: `~/projects/C_trachomatis_inclusivity_exclusivity`  (NOT `..._RESTART`, despite what the old handover said)
- OneDrive (Windows): `C:\Users\krist\OneDrive\Documents\Projects\C_trachomatis_inclusivity_exclusivity`
- OneDrive (from WSL): `/mnt/c/Users/krist/OneDrive/Documents/Projects/C_trachomatis_inclusivity_exclusivity`
- GitHub: https://github.com/bkhimek/C_trachomatis_inclusivity_exclusivity
- Working branch: `feature/125-refseq-restart` (main holds only the scaffold; a rename dropping "restart" is optional and undecided)

## How we work (the user's preferences)
- The user runs commands in WSL and **pastes the output back**. Keep pasted commands SHORT.
- Long scripts: the assistant writes them to OneDrive `_incoming/<repo-relative path>`; the user runs `./pull_incoming.sh`
  in the repo (moves them into place and archives them in `_incoming/_done/`). Long heredoc pastes are unreliable.
- Readable outputs (tables, .docx, .xlsx, .txt) go to `reports/` (gitignored) and reach OneDrive via `./sync_onedrive.sh`.
  Run `./sync_onedrive.sh` after every commit/push. OneDrive should hold files a human can open, e.g. an oligo-set table
  (sequence, length, Tm, GC%, Tm gap).
- Commit messages: plain, **never** prefixed with "[RESTART]". Never commit genome FASTA (gitignored).
- Environment: WSL2 Ubuntu, conda base. **Do not create new conda envs**; pip-install into base.
  Prokka lives in env `prokka_env` (1.14.6), Panaroo in `panaroo_env` (1.5.2); scripts locate these themselves.
  Base has fastANI 1.34, blast+ 2.17, mafft 7.525, datasets 18.29.1, primer3 2.6.1, biopython, pandas, openpyxl, python-docx.
- Nothing is committed before the user has seen the results.
- **Note on this and the 2026-09-24/26 sessions:** neither ran in the WSL environment above. Both worked
  directly against the OneDrive folder (this one through a desktop-app device bridge, with `primer3-py`/
  `biopython` in its own cloud sandbox, not the WSL conda base described above). Deliverables landed in
  OneDrive `Claude outputs/`, not `reports/`, and nothing from either session has been committed to git.
  If a future session runs in WSL again, treat the OneDrive copies of `docs/HANDOVER.md`/`PROJECT_STATE.md`
  as the current ones and pull them (plus the result files listed below) into the repo working tree before
  trusting `git log`/`git status` to reflect the project's real state.

## Pipeline status
| Step | Script | Status |
|---|---|---|
| Primer3 smoke test / probe sweep | bin/00, 00b | done, results in docs/ |
| RefSeq inventory + download (125) | bin/01 | done |
| Provenance audit, tiers | bin/02 (+ config/provenance_*.tsv) | done: 97 primary / 10 quality-review / 18 excluded |
| Species check (fastANI) + redundancy | bin/03 | done: all >= 98.90% ANI; 58 clusters at >= 99.99 |
| ompA serovar typing | bin/04 | done: 14 serovar groups |
| Prokka annotation | bin/05 | done: 107 genomes (primary + quality-review), CDS median 897 |
| Panaroo pangenome | bin/06 | done: 904 gene clusters, 874 core |
| Exclusivity screening | bin/07 | done: 588/692 genes id85-clean with a usable conserved block |
| Candidate region refinement + consensus | bin/08, bin/09 | done: `results/candidate_regions/candidate_regions.tsv` |
| Primer3 design + post-filter (bin/10+) | *not run as bin/10* | done manually (not through the numbered pipeline) for 8 genes total — see below |
| Web BLAST validation, plasmid, final report | bin/11+ | oligo BLAST done manually for all 11 current sets (see below); plasmid not started |

**Oligo design status (2026-09-27) — FINAL PANEL LOCKED IN (D22).** 4 targets, 7 sets, matching the
user's "5-10 sets against 2-4 targets, then stop" instruction. See PROJECT_STATE.md's 2026-09-27 update
for the scoring behind this and what it supersedes. Full per-oligo QC (sequence, Tm, GC%, structure,
three-way dimer check, human/whole-database BLAST divergence) for all 13 candidate sets (39 oligos): the
`Oligo_QC_Reference.xlsx` spreadsheet (OneDrive `Claude outputs/`).

### Final panel (4 genes, 7 sets)

| Gene | Set | Tm gap | Structure | BLAST | Status |
|---|---|---|---|---|---|
| mutL | primary (only locus in this window) | 8.07°C | LOW | clean (pair-level) | **final panel** |
| aroB | redesign (primary) | 7.75°C | LOW | clean (pair-level)* | **final panel** |
| aroB | Alt 1 (backup locus) | 6.44°C | LOW | clean | **final panel** |
| aroB | Alt 2 (backup locus) | 7.00°C | LOW | clean | **final panel** |
| PSD2 | redesign (primary) | 7.54°C | LOW | clean (pair-level) | **final panel** |
| PSD2 | Alt 1 (backup locus) | 6.81°C | LOW | clean | **final panel** |
| group_306 | primary (only locus in this window) | 7.82°C | LOW | clean (pair-level) | **final panel** |

\* aroB's forward primer and probe both have a full-length hit to *C. suis* (a genus-conserved region at
that exact locus), but the reverse primer has zero hits anywhere in the *C. suis* genome — no completing
pair, so no plausible off-target amplicon. See `PHASE1_REDESIGN_BLAST_VALIDATION.md` (OneDrive
`Claude outputs/`) for the full writeup.

### Parked backups (fully designed and validated, not part of the panel — no further work planned)

| Gene | Set | Tm gap | Structure | BLAST | Why parked |
|---|---|---|---|---|---|
| group_159 | backup gene | 7.06°C | LOW | clean | not needed once the 4 primary genes redesigned clean |
| group_140 | locus 1 | 6.84°C | LOW | clean | not needed; see above |
| group_140 | locus 2 | 6.81°C | MEDIUM (R primer 3' GC rule) | clean | flagged AND not needed |
| group_181 | locus 1 | 6.47°C | LOW | clean | not needed; see above |
| group_181 | locus 2 | 8.61°C | MEDIUM (cause not isolated) | clean | flagged AND not needed |
| PSD2 | Alt 2 | 8.71°C | MEDIUM (fwd hairpin) | clean | flagged; PSD2 already has 2 clean sets in the panel |

Genome tiers: primary = consensus + inclusivity claim; quality-review = natural isolates with suspicious metrics
(oligos are tested against them, reported separately — **not yet done for any of the 13 designed sets, panel or parked**); excluded = experimental/engineered/lab-selected or non-C. trachomatis.
Serial/near-identical isolates are all kept (D14); report variant frequency per cluster.

## Key technical rules (see PROJECT_STATE for the full list, now D1-D22)
- Primer3 caps internal oligos at 36 nt; probes are 20-28 nt (opt 22) — shorter = lower background fluorescence.
- Tm gap probe - primers: >= 5 C hard floor, 7+ preferred (D6). **Compute it from an actual primer3/NN
  calculation on the real sequence (D19) — do not assume it from the settings file's target Tm values.**
- Web BLAST of oligos: Expect=1000, word_size=7, filter off (D18); check both a full human-genome-assembly
  database and core_nt (excl. txid813).
- An off-target hit only matters if a partner oligo from the same set also hits nearby on the same
  accession (D20) — check that before rejecting or accepting a design on BLAST grounds alone.
- Check all three oligo-pair heterodimers (F-R, F-Probe, R-Probe), not just F-R (D21).
- Primer3 salt/oligo settings are PLACEHOLDERS until the user gives real master-mix conditions.

## Open items
1. ~~Run BLAST (D18 settings) on the 12 redesigned Phase 1 oligos~~ — **done 2026-09-27**, clean. See
   `PHASE1_REDESIGN_BLAST_VALIDATION.md` (OneDrive `Claude outputs/`).
2. ~~Combine Phase 1 + Phase 2 into one scored ranking and pick a final panel~~ — **done 2026-09-27 (D22)**:
   4 targets / 7 sets locked in, see the table above. `group_159/140/181` and `PSD2 Alt 2` are parked, not
   deleted — no further design work planned on them unless a final-panel gene fails downstream.
3. **Quality-review-tier genome check (D13)** — 10 genomes, not yet tested against any of the 13 designed
   sets (7 final-panel + 6 parked). Now the single largest remaining gap before the panel can be called
   fully validated end to end.
4. Two flagged components remain unresolved, but **no longer block anything** since they're parked, not in
   the panel: PSD2 Alt 2's forward primer (hairpin) and group_140's second-locus reverse primer (3'
   GC-stability rule). Only worth fixing if a final-panel gene needs replacing later.
5. Real master-mix Mg2+, dNTP, oligo nM (replace placeholders in `config/primer3_settings.txt`) — every
   Tm/gap number in the project will shift slightly once these are real.
6. **Commit the oligo design files to git** — `docs/HANDOVER.md`, `docs/PROJECT_STATE.md`, and
   `docs/lessons_learned.md` were committed to `main` on 2026-09-27 (commit `860c638`); the oligo
   deliverables themselves (Phase 1/2 design docs, BLAST FASTAs/validation writeups, the combined ranking,
   `Oligo_QC_Reference.xlsx`) are still OneDrive-only — worth committing now that the panel is locked, into
   the repo's existing empty `results/oligos_chromosomal/`, `results/specificity_validation/`, etc.
   placeholders.
7. Confirm nvCT plasmid accessions (NC_012630.1, FM865439.1) before the plasmid steps. **The plasmid target
   itself has not been started at all** — the panel above is chromosomal only.
8. User: web BLAST of the D/Ep6/S19-121 ompA (95.6% to nearest); if poor hits -> move to quality-review.
   (Carried over, unresolved since 2026-09-24.)
9. The two old pre-restart handover .md files still need to go into `docs/archive/` (user to supply).
   Separately, the 2026-09-24/26 side session's own handover/status/lessons docs
   (`01_LESSONS_LEARNT.md`, `02_PROJECT_STATUS.md`, `03_DETAILED_HANDOVER.md` in OneDrive
   `Claude outputs/previous/`) are now superseded by `docs/lessons_learned.md` and this file — consider
   moving them into `docs/archive/` too rather than deleting them, since some of their non-oligo-specific
   process lessons still hold (see `docs/lessons_learned.md`).

## Starting a new session: say to the assistant
"Continue the C. trachomatis project. Read docs/HANDOVER.md and docs/PROJECT_STATE.md in the repo (or the OneDrive copy) first."
At the end of a session: ask the assistant to "update HANDOVER.md, PROJECT_STATE.md, and lessons_learned.md."
