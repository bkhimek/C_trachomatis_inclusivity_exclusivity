# HANDOVER: read this first at the start of every session

Short, current-state file. Rewritten at the end of each session. Long-term decisions and findings live in
`docs/PROJECT_STATE.md` (decision log D1-D28 + findings). If this file and PROJECT_STATE disagree, ask the user.

Last updated: 2026-10-02 — **project fully closed out; the locked panels have not changed since 2026-09-27.** Updates since then are documentation, plus one optional check added on 2026-10-02 evening: `bin/18` tested the 10 quality-review genomes against the 7 locked chromosomal sets, clean — 69/70 exact, 1 OK (QH111L, PSD2_alt1 backup set, one internal probe mismatch), 0 at risk/fail, control 97/97 (D28). Final chromosomal panel locked in
(D22): 4 targets/7 sets. Plasmid target locked in (D25): 1 target/2 sets. 5 targets, 9 sets total, all
D6/D18/D19/D20/D21-clean. Remaining housekeeping (D13 chromosomal quality-review check, two flagged
backup-set primers, master-mix placeholders) closed as won't-fix/not-applicable (D26; the quality-review check was later run anyway, D28). The ompA web BLAST
follow-up and any wet-lab step are confirmed out of scope (D27) — this project's deliverable is the
in-silico design and its QC record. All oligo deliverables (chromosomal + plasmid) are committed to `main`
on GitHub. **Two closing documents, both revised 2026-10-01:** the case study —
*Case Study: C. trachomatis — Target Selection for Oligo Design*
(https://claude.ai/code/artifact/16f0002d-0b4f-4fd2-bb40-dddde4e93536) — had its genome-provenance
narrative reconciled against the real audit log and gained a genome-count-by-pipeline-stage table (see
PROJECT_STATE.md's 2026-10-01 update for the full story); the companion white paper —
*From Genome Selection to Assay Candidate*
(https://claude.ai/code/artifact/78ece28a-0591-4b7c-a8e3-ad58c7260a6e) — had its genome-verification
section (§2-3) brought into sync with the same narrative. Both are Claude Docs artifacts, not repo files;
current `.docx` exports were delivered to the user directly, not committed. **Technical note for whoever
exports either artifact to `.docx` next:** a large inline base64 `docx` export can decode to the right byte
count yet still be internally corrupted (bad ZIP CRC) — export as `markdown` and convert locally with
`pandoc` instead; see `docs/lessons_learned.md` §1 and PROJECT_STATE.md's 2026-10-01 update. **2026-10-02:** the white paper now documents how the 125 RefSeq genomes were verified (four checks), and a
case-study error was fixed (Panaroo ran on the 97 primary genomes, not 107; quality-review genomes were never
part of the pangenome) — see PROJECT_STATE.md's 2026-10-02 update. Only item 9
(archiving old superseded handover files) remains genuinely open — see Open Items.

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
| Panaroo pangenome | bin/06 | done: 904 gene clusters, 874 core (97 primary-tier genomes only; quality-review excluded) |
| Exclusivity screening | bin/07 | done: 588/692 genes id85-clean with a usable conserved block |
| Candidate region refinement + consensus | bin/08, bin/09 | done: `results/candidate_regions/candidate_regions.tsv` |
| Primer3 design + post-filter (bin/10+) | *not run as bin/10* | done manually (not through the numbered pipeline) for 8 genes total — see below |
| Web BLAST validation, final report | bin/11+ | oligo BLAST done manually for all 13 chromosomal sets (see below) |
| Plasmid contig extraction, consensus, design | bin/12-17 | done 2026-09-27, committed — see Plasmid target section below |
| Quality-review genomes vs 7 locked chromosomal sets | bin/18 + `config/final_chromosomal_oligos.tsv` | done 2026-10-02: 69/70 exact, 1 OK, 0 at risk/fail; control 97/97 (D28). Outputs in `results/qr_oligo_check/`; committed and pushed to `main` (commit `6b00884`) |

**Oligo design status (2026-09-27) — FINAL CHROMOSOMAL PANEL LOCKED IN (D22).** 4 targets, 7 sets, matching
the user's "5-10 sets against 2-4 targets, then stop" instruction. See PROJECT_STATE.md's 2026-09-27 update
for the scoring behind this and what it supersedes. Full per-oligo QC (sequence, Tm, GC%, structure,
three-way dimer check, human/whole-database BLAST divergence) for all 13 candidate sets (39 oligos): the
`Oligo_QC_Reference.xlsx` spreadsheet (OneDrive `Claude outputs/`).

**Plasmid target (2026-09-27) — LOCKED IN (D25).** 2 sets (Primary, Reserve), 6 oligos, same D6/D18/D19/
D20/D21 standard. See "Plasmid target" section below for the full trail. Combined with the chromosomal
panel above: 5 targets, 9 sets total for this assay design project.

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

## Plasmid target (investigated 2026-09-27, chromosomal panel above is unaffected)

A separate handover, `PLASMID_OLIGO_DESIGN_HANDOVER.md` (Claude Haiku, 2026-09-27), proposed a plasmid
design workflow and claimed (with ✅ checkmarks) that a 128-genome RefSeq plasmid curation, alignment,
consensus and validation already existed. **None of it does** — checked directly: `data/plasmid_inventory/`,
`data/plasmids_downloaded/`, `data/blast_databases/`, and `results/oligos_plasmid/` are all empty. Its Part 12
table naming chromosomal targets `group_122/28/24/83` is not this project's panel (D22: mutL/aroB/PSD2/
group_306) and was ignored per the user's instruction. Its "V1 Primary/Reserve" plasmid oligo sequences and
Tm values, and its nvCT deletion coordinates (2365-2560) / accessions (NC_012630.1, FM865439.1), are all
**unverified** — see PROJECT_STATE.md's 2026-09-27 plasmid update for exactly what was and wasn't checked
(NCBI eutils and PubMed/PMC are not reachable from this cloud session; the ~377bp nvCT deletion itself is
real and well-documented in the literature, but the specific numbers above are not independently confirmed).

**Real finding, not from the handover:** this project's own `data/genome_inventory/genome_files.tsv`
(written by bin/01) already flags 34 of the 125 downloaded genomes as carrying a second small replicon, and
for every one of those 34 its size is 7,415-7,510 bp — matching the known ~7.5kb C. trachomatis plasmid.
Those 34 genome files (in WSL `data/genomes_downloaded/`, not on OneDrive) are a real, ready plasmid-sequence
source — no fresh 128-genome curation needed to get started. Tier: 29 primary, 5 quality-review, 0 excluded.
None of the 34 look like the Swedish nvCT variant by strain name; a real nvCT reference would need to come
from elsewhere if the user wants nvCT-aware design now rather than later.

**Decision (D23, user-approved 2026-09-27):** proceed with a standard/consensus plasmid design from the 34
verified genomes now; nvCT-specific design is parked (not dropped) pending a real, independently-sourced
nvCT reference and confirmed deletion coordinates. Rationale in PROJECT_STATE.md — short version: the nvCT
numbers we'd need are exactly the ones we couldn't verify, the 4-gene chromosomal panel already detects
nvCT-positive samples regardless (nvCT differs only on the plasmid), and this matches the same
"good enough, stop optimizing" call already used for D22.

**bin/12 done (2026-09-27):** ran clean — 34/34 plasmid contigs extracted, zero missing, zero length flags
(7,415-7,510 bp range, as predicted). `data/plasmids_downloaded/plasmids_34_combined.fasta` (WSL only) is
ready for alignment.

**Finding, fixed and confirmed:** raw MAFFT alignment came out ~2x too long (13,075 bp vs. ~7,500 bp input) —
a circular-rotation/strand artifact (different RefSeq submissions start a circular plasmid's FASTA at
different points, some on the opposite strand), not real divergence. `bin/13_fix_plasmid_orientation.py`
fixed 31/34 (3 excluded as low-confidence — all 3 were already independently flagged `auto_verdict=REVIEW`
in the original chromosomal QC, a reassuring cross-check). Re-aligning the 31 gave **aln_len=7,606** — fix
confirmed working.

**bin/14 done:** consensus built from the 27 primary-tier genomes, clean — 7,500bp (106 minor-insertion
columns dropped, matching the raw plasmid length exactly), 98.3% 100%-conserved, 1.65% (124bp) real
cross-strain variation correctly N-masked. `results/plasmid/consensus/consensus_plasmid_standard.fasta`
(WSL, not yet on git).

**bin/15 done — three real findings:**
1. Consensus GC = **35.4%**, not the ~50% the plasmid handover claimed (and lower than the ~43%
   chromosomal figure it compared against, not higher). Its plasmid-specific primer3 Tm target (70°C
   instead of chromosomal 68°C) was based on that now-disproven claim, so it's **not being used** — plasmid
   design uses the same D6/D7 settings as the chromosomal panel.
2. All 31 genomes: 30 at 100% identity to consensus, 1 (GCF_001885175.1) at 99.95%. D13's held-out
   quality-review check passes cleanly.
3. No nvCT-like deletion anywhere in this dataset (longest gap run 85bp, nvCT's signature is ~377bp) —
   confirms rather than just infers that none of these 31 carry it.

**bin/16 done:** 120 N-free runs found; longest 418bp (position 4,860-5,277), second 298bp (1,315-1,612) —
plenty of clean sequence, no region-hunt needed. The handover's claimed nvCT window (2365-2560) actually
contains 6 N's out of 196bp here — not itself one of the clean windows, another independent strike against
trusting that specific claim.

**bin/17 done — plasmid Primary + Reserve designed, D6/D19/D21-clean:**

| Set | Window | Oligo | Sequence | Tm | GC% |
|---|---|---|---|---|---|
| Primary | 4,860-5,277 | F | CTACCATCCCATTTTGAGCC | 60.11 | 50.0% |
| Primary | | R | GCCACTTCATCAAAAGTCCT | 59.89 | 45.0% |
| Primary | | Probe (27nt) | TGACCAGGTCTTCTTCCAAACTTCTGA | 67.39 | 44.4% |
| Reserve | 1,315-1,612 | F | GATGAGTTCGACATTCCACA | 59.40 | 45.0% |
| Reserve | | R | AGAGTTTCAATCGATCCCCT | 59.96 | 45.0% |
| Reserve | | Probe (24nt) | TCTAGCGGCCAAAATATATGCGGA | 66.04 | 45.8% |

Primary Tm gap 7.28°C (preferred), Reserve 6.08°C (floor). **Both fully D21-clean (0 structural flags)** —
this only holds because a ranking bug was caught first: the initial Tm-gap/length-only ranking would have
picked a flagged candidate in both windows (D24, see PROJECT_STATE.md). Full writeup:
`PLASMID_PRIMARY_RESERVE_DESIGN.md` (OneDrive `Claude outputs/`).

**D18 BLAST done (2026-09-27) — both sets clean.** User ran the manual web BLAST (human genome +
transcript DB, and core_nt excl. txid813) on all 6 oligos. Human genome: all hits weak/partial, zero
completing pairs (D20) for either set — clean. core_nt: both sets match 7 published *C. trachomatis*
genetics-lab shuttle/cloning vectors (pBOMB4 series, pGFPBSDZ-SW2, pREF100) at 100% identity, full length,
correctly ordered/spaced — expected, not a specificity concern, since these vectors are built by cloning the
native plasmid backbone (confirmed via literature: Bauler & Hackstadt 2014; Wang et al. 2011) and would never
appear in a clinical sample. Primary Probe alone has a weak partial *C. muridarum* hit with no completing
partner (D20 clears it), matching the aroB/*C. suis* precedent from the chromosomal panel. Full writeup:
`PLASMID_BLAST_VALIDATION.md` (OneDrive `Claude outputs/`).

**D25 (2026-09-27, user-approved): plasmid target formally locked in.** Primary + Reserve — 2 sets, 6
oligos — on the same D6/D18/D19/D20/D21 standard the chromosomal panel met before D22. nvCT-specific design
stays parked per D23. The plasmid sub-project is now done, mirroring where the chromosomal panel landed
after D22.

## Key technical rules (see PROJECT_STATE for the full list, now D1-D28)
- Primer3 caps internal oligos at 36 nt; probes are 20-28 nt (opt 22) — shorter = lower background fluorescence.
- Tm gap probe - primers: >= 5 C hard floor, 7+ preferred (D6). **Compute it from an actual primer3/NN
  calculation on the real sequence (D19) — do not assume it from the settings file's target Tm values.**
- Web BLAST of oligos: Expect=1000, word_size=7, filter off (D18); check both a full human-genome-assembly
  database and core_nt (excl. txid813).
- An off-target hit only matters if a partner oligo from the same set also hits nearby on the same
  accession (D20) — check that before rejecting or accepting a design on BLAST grounds alone.
- Check all three oligo-pair heterodimers (F-R, F-Probe, R-Probe), not just F-R (D21).
- Primer3 salt/oligo settings (50mM Na+, 3.0mM Mg2+, 0.8mM dNTP, 250nM oligo) are the fixed basis for every
  Tm/gap number in the project (D26) — this is an in-silico design exercise, not a wet-lab protocol, so
  these are not placeholders pending real values; they are the project's permanent assumption.

## Open items
1. ~~Run BLAST (D18 settings) on the 12 redesigned Phase 1 oligos~~ — **done 2026-09-27**, clean. See
   `PHASE1_REDESIGN_BLAST_VALIDATION.md` (OneDrive `Claude outputs/`).
2. ~~Combine Phase 1 + Phase 2 into one scored ranking and pick a final panel~~ — **done 2026-09-27 (D22)**:
   4 targets / 7 sets locked in, see the table above. `group_159/140/181` and `PSD2 Alt 2` are parked, not
   deleted — no further design work planned on them unless a final-panel gene fails downstream.
3. ~~Quality-review-tier genome check (D13) for the chromosomal panel~~ — **closed 2026-09-27 as won't-fix (D26), then run anyway and passed, 2026-10-02 (D28).** `bin/18` tested the 10 quality-review genomes against the 7 locked sets: 69/70 exact, 1 OK (QH111L, PSD2_alt1), 0 at risk/fail; control 97/97.
4. ~~Two flagged structural components (PSD2 Alt 2 forward-primer hairpin; group_140 locus-2 reverse-primer
   3'-GC rule)~~ — **closed, won't-fix, 2026-09-27 (D26).** Both are on parked backup sets, not in the
   locked panel; user decision: leave as-is permanently rather than as an open item. Only worth revisiting if
   a final-panel gene is ever replaced by one of these specific backups.
5. ~~Real master-mix Mg2+, dNTP, oligo nM~~ — **not applicable, 2026-09-27 (D26).** Project scope is in-silico
   design only (no wet-lab phase); the placeholder concentrations above are the project's permanent, final
   values, not a pending input.
6. ~~Commit the oligo design files to git~~ — **done, 2026-09-27.** `docs/HANDOVER.md`,
   `docs/PROJECT_STATE.md`, and `docs/lessons_learned.md` were committed on `main` (commit `860c638`); the
   chromosomal + plasmid oligo deliverables (design docs, BLAST FASTAs/validation writeups, the combined
   ranking, both `Oligo_QC_Reference.xlsx` spreadsheets, `bin/12`-`17`) followed in commit `90d0d05`, and the
   FASTA files a blanket `.gitignore` rule had silently excluded were added back with targeted exceptions in
   commit `68930f5`. Nothing design-related remains OneDrive-only.
7. ~~Plasmid target — design + QC~~ — **done 2026-09-27 (D25):** Primary+Reserve locked in, same
   D6/D18/D19/D20/D21 standard as the chromosomal panel. See the "Plasmid target" section above.
   nvCT-specific design remains parked (D23), not blocking — no further action planned there unless a real,
   independently-sourced nvCT reference and confirmed deletion coordinates (NC_012630.1, FM865439.1, still
   unconfirmed) surface later.
8. ~~User: web BLAST of the D/Ep6/S19-121 ompA (95.6% to nearest); if poor hits -> move to
   quality-review.~~ — **closed, won't-run, 2026-09-27 (D27).** Confirmed out of scope: this project
   delivers the in-silico design and its QC record, not a fully re-verified genome tier list. D/Ep6/S19-121
   stays primary-tier as originally recorded.
9. The two old pre-restart handover .md files still need to go into `docs/archive/` (user to supply).
   Separately, the 2026-09-24/26 side session's own handover/status/lessons docs
   (`01_LESSONS_LEARNT.md`, `02_PROJECT_STATUS.md`, `03_DETAILED_HANDOVER.md` in OneDrive
   `Claude outputs/previous/`) are now superseded by `docs/lessons_learned.md` and this file — consider
   moving them into `docs/archive/` too rather than deleting them, since some of their non-oligo-specific
   process lessons still hold (see `docs/lessons_learned.md`).

## Starting a new session: say to the assistant
"Continue the C. trachomatis project. Read docs/HANDOVER.md and docs/PROJECT_STATE.md in the repo (or the OneDrive copy) first."
At the end of a session: ask the assistant to "update HANDOVER.md, PROJECT_STATE.md, and lessons_learned.md."
