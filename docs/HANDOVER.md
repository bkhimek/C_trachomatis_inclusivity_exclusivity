# HANDOVER: read this first at the start of every session

Short, current-state file. Rewritten at the end of each session. Long-term decisions and findings live in
`docs/PROJECT_STATE.md` (decision log D1-D14 + findings). If this file and PROJECT_STATE disagree, ask the user.

Last updated: 2026-09-24 (end of session 1 of the restart)

## Project
In-silico design of a multiplex PCR/TaqMan assay for *Chlamydia trachomatis*: chromosomal targets + multicopy-plasmid
target (nvCT-aware). Goal: inclusivity across C. trachomatis genomes, exclusivity vs. related/clinical species,
then primer/probe design. Owner: Krzysztof Gizynski.

## Paths (do not guess others)
- WSL repo: `~/projects/C_trachomatis_inclusivity_exclusivity`  (NOT `..._RESTART`, despite what the old handover said)
- Prior trial run (reference only, not a working directory): `~/projects/trial_C_trachomatis_inclusivity_exclusivity`.
  Has a real, already-built exclusivity panel (genomes + BLAST DBs) that bin/07 reuses; may hold other salvageable
  reference material (e.g. an old case study .docx) not yet checked.
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

## Pipeline status
| Step | Script | Status |
|---|---|---|
| Primer3 smoke test / probe sweep | bin/00, 00b | done, results in docs/ |
| RefSeq inventory + download (125) | bin/01 | done |
| Provenance audit, tiers | bin/02 (+ config/provenance_*.tsv) | done: 97 primary / 10 quality-review / 18 excluded |
| Species check (fastANI) + redundancy | bin/03 | done: all >= 98.90% ANI; 58 clusters at >= 99.99 |
| ompA serovar typing | bin/04 | done: 14 serovar groups |
| Prokka annotation | bin/05 | done: 107 genomes (primary + quality-review), CDS median 897 |
| Excel/Word reports | bin/90 | done for inventory; oligo table to be added |
| Panaroo pangenome | bin/06 | done: 874 core / 6 soft-core / 21 shell / 3 cloud (904 families, 97 primary genomes) |
| Exclusivity screening | bin/07 | done: panel reused from the trial run (35 species, 10 genus-tier + 25 clinical-tier, 123 genomes); 30/874 core genes clean vs the genus panel at any-hit level, 692/874 clean at >=85% identity; see results/exclusivity/core_gene_exclusivity.tsv |
| Candidate region discovery, ranking | bin/08 | **NEXT** (input: results/exclusivity/core_gene_exclusivity.tsv) |
| Consensus, Primer3 design + post-filter, validation, plasmid, final report | bin/09+ | not started |

Genome tiers: primary = consensus + inclusivity claim; quality-review = natural isolates with suspicious metrics
(oligos are tested against them, reported separately); excluded = experimental/engineered/lab-selected or non-C. trachomatis.
Serial/near-identical isolates are all kept (D14); report variant frequency per cluster.

## Key technical rules (see PROJECT_STATE for the full list)
- Primer3 caps internal oligos at 36 nt; the plan is 20-28 nt probes (shorter = lower background fluorescence).
- Tm gap probe - primers: >= 5 C hard floor, 7+ preferred; Primer3 cannot enforce it, so post-filter (D12).
- Primer3 salt/oligo settings are PLACEHOLDERS until the user gives real master-mix conditions.

## Open items
1. User: web BLAST of the D/Ep6/S19-121 ompA (95.6% to nearest); if poor hits -> move to quality-review.
2. User: real master-mix Mg2+, dNTP, oligo nM (replace placeholders in `config/primer3_settings.txt`).
3. Confirm nvCT plasmid accessions (NC_012630.1, FM865439.1) before the plasmid steps.
4. Web BLAST validation package (same manual approach as the earlier project) once exclusivity fragments and oligo sets exist.
5. The two old handover .md files still need to go into `docs/archive/` (user to supply); write docs/lessons_learned.md.

## Starting a new session: say to the assistant
"Continue the C. trachomatis project. Read docs/HANDOVER.md and docs/PROJECT_STATE.md in the repo (or the OneDrive copy) first."
At the end of a session: ask the assistant to "update HANDOVER.md and PROJECT_STATE.md".
