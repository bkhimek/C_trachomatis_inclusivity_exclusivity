# C. trachomatis inclusivity / exclusivity: multiplex PCR/TaqMan assay design

In-silico design and validation of a multiplex PCR/TaqMan assay for *Chlamydia trachomatis*
with chromosomal and multicopy-plasmid targets, ready for wet-lab testing.

**Status:** restart in progress. Nothing here has been run yet, and no results are claimed.
The current plan and every decision made so far are in [`docs/PROJECT_STATE.md`](docs/PROJECT_STATE.md).

## Requirements
- **Inclusivity:** targets present in all natural *C. trachomatis* isolate genomes in the reference set.
- **Exclusivity:** targets absent from other *Chlamydia* species and clinically relevant co-pathogens.
- **Plasmid target:** must detect the Swedish new-variant (nvCT) 377 bp deletion plasmids as well as standard plasmids.
- **Oligo design:** TaqMan probe Tm at least 7 C above the highest primer Tm.

## Design principles
1. **Provenance first.** A "complete genome" label does not mean a natural isolate. Every genome is traced to its
   BioProject before use (see `docs/lessons_learned.md`).
2. **One source of truth.** Decisions live in `docs/PROJECT_STATE.md`. Scripts read parameters from `config/`.
3. **Reproducible.** Numbered scripts in `bin/`, pinned tool versions in `docs/tool_versions.txt`.

## Planned pipeline (script names may change; see PROJECT_STATE.md)
| Phase | Scripts | Purpose |
|-------|---------|---------|
| 0. Setup | `bin/00` | Tool and parameter smoke test |
| 1. Inventory | `bin/01-04` | RefSeq genome download, provenance audit, species check, ompA typing |
| 2. Discovery | `bin/05-11` | Annotation, pangenome, exclusivity screen, candidate regions, consensus |
| 3. Design | `bin/12-15` | Primer3 design, validation, inclusivity BLAST, ranking |
| 4. Plasmid | `bin/16-18` | Plasmid alignment, nvCT-aware design, exclusivity |
| 5. Final | `bin/19-24` | Specificity checks, selection, final specification, report |

## Layout
`bin/` scripts, `config/` parameters, `data/` inventories (large downloads are gitignored),
`results/` outputs, `docs/` documentation and result tables.

## Environment
WSL2 Ubuntu. BLAST+, Primer3, MAFFT, fastANI and NCBI Datasets in `base`; Prokka in `prokka_env`;
Panaroo in `panaroo_env`. Genome FASTA files are never committed.
