# C. trachomatis inclusivity / exclusivity: multiplex qPCR/TaqMan assay design

In-silico design and quality control of a multiplex qPCR/TaqMan assay for *Chlamydia trachomatis*, with
chromosomal targets and a multicopy-plasmid target. The project selects targets from a curated set of
complete genomes, screens them against related and clinically relevant species, designs primers and probes
to an explicit standard, and records every decision and its evidence.

**Status.** Complete as an in-silico design (closed 2026-09-27; two further checks added: quality-review genomes on
2026-10-02 and duplex cross-interactions on 2026-10-20). Wet-lab validation is out of scope, so every result here is a computational screen, not a
measured assay performance.

## Results at a glance

- **Reference set.** 125 complete RefSeq genomes, tiered 97 primary / 10 quality-review / 18 excluded.
  149 GenBank-only genomes from a single study of engineered laboratory strains (PRJNA558398) were rejected
  before the reference set was built.
- **Pangenome** (Panaroo, 97 primary genomes): 904 gene clusters, 874 core genes.
- **Exclusivity screen** against 123 non-target genomes (35 species): 692 of 874 core genes contain a stretch
  of at least 150 bp that is below 85% identical to every genome in the panel; 588 of those also hold at
  least 100 bp that is at least 99% conserved across the primary genomes.
- **Final panel:** 5 targets, 9 oligo sets, 27 oligos.

| Target | Compartment | Oligo sets | Probe-to-primer Tm gap |
|---|---|---|---|
| mutL | chromosome | 1 | 8.07 °C |
| aroB | chromosome | 3 (primary + 2 backup loci) | 7.75 / 6.44 / 7.00 °C |
| PSD2 | chromosome | 2 (primary + 1 backup locus) | 7.54 / 6.81 °C |
| group_306 | chromosome | 1 | 7.82 °C |
| plasmid | multicopy plasmid | 2 (Primary + Reserve) | 7.28 / 6.08 °C |

- **Standard met by every set.** Probe Tm at least 5 °C above the highest primer Tm (6.08-8.07 °C across all
  sets); Tm computed from the real sequence; no structural flags in any of the three oligo pairs (F-R,
  F-probe, R-probe); BLAST against the human genome and core_nt with a pair-level rule for off-target hits.
- **Quality-review genomes tested against the finished design (`bin/18`).** For the seven chromosomal sets,
  69 of 70 set-by-genome cases bind exactly and one binds within tolerance (a single internal probe
  mismatch); none is at risk or fails. The 97 primary genomes run as a control bind 97 of 97.
- **Proposed duplex (`bin/19`).** The intended final assay pairs one chromosomal set with one plasmid set. Cross-dimers
  between the two sets were computed for all 14 combinations (126 oligo pairs): none is MEDIUM or HIGH on the same severity
  scale as the within-set checks (strongest structure Tm 21.5 °C, or 27.0 °C under the project reaction conditions).
  This is oligo-oligo thermodynamics only; dye assignment and real multiplex behaviour are laboratory questions.

The oligo sequences are in `config/final_chromosomal_oligos.tsv` (21 chromosomal oligos) and
`results/oligos_plasmid/PLASMID_PRIMARY_RESERVE_DESIGN.md` (6 plasmid oligos, with Tm and structure QC).

## Limitations

- Results are in-silico. No wet-lab verification against reference strains or near-neighbour DNA was done.
- Conclusions describe the curated collection (125 RefSeq genomes), not the whole species; a lineage absent
  from RefSeq complete genomes is not covered.
- The plasmid design is a standard consensus design. An nvCT-specific design (the Swedish new variant with a
  377 bp plasmid deletion) was not performed: its published coordinates and accessions could not be
  independently confirmed, so that work is parked (decision D23), and detection of nvCT by the plasmid sets
  is not claimed.
- Chromosomal primer design and the web BLAST of the finished oligos were run manually, outside the numbered
  scripts; their records are in `docs/PROJECT_STATE.md` and `results/oligos_chromosomal/`.

## Pipeline

| Script | Purpose |
|---|---|
| `bin/00`, `bin/00b` | Tool and Primer3 smoke test; probe-length sweep on synthetic templates |
| `bin/01` | RefSeq inventory and download (125 genomes) |
| `bin/02` | Provenance audit and genome tiering (`config/provenance_*.tsv`) |
| `bin/03` | Species check and redundancy map (fastANI) |
| `bin/04` | ompA serovar typing |
| `bin/05` | Annotation (Prokka) |
| `bin/06` | Pangenome (Panaroo), primary tier only |
| `bin/07` | Exclusivity screen of core genes against the non-target panel |
| `bin/08` | Candidate regions: exclusivity-clean and at least 99% conserved |
| `bin/09` | Population consensus for the 30 top candidate regions |
| manual | Chromosomal Primer3 design, structure QC and web BLAST (recorded in `docs/PROJECT_STATE.md`) |
| `bin/12`-`17` | Plasmid: contig extraction, orientation fix, consensus, identity check, conserved windows, primer design |
| `bin/18` | Quality-review genomes against the seven locked chromosomal sets |
| `bin/19` | Cross-dimer check between each chromosomal set and each plasmid set (the proposed duplex) |
| `bin/90` | Export of human-readable reports |

Numbers 10 and 11 are intentionally unused. The decision log refers to some earlier script numbers; where it
differs from this table, the table reflects the scripts in `bin/`.

## Design principles

1. **Provenance first.** A "complete genome" label does not mean a natural isolate. Every genome is traced to
   its BioProject and tiered before use (see `docs/lessons_learned.md`).
2. **Explicit thresholds.** Conserved means at least 99% agreement per position; an exclusivity gap is a
   stretch of at least 150 bp below 85% identity to every non-target genome; a probe must have a Tm at least
   5 °C above the highest primer Tm. None of these are software defaults.
3. **One source of truth.** Decisions D1-D29 and dated findings live in `docs/PROJECT_STATE.md`; scripts read
   parameters from `config/`.
4. **Recompute, do not transcribe.** Any number that drives a decision is recomputed from primary data
   (`docs/lessons_learned.md`).

## Repository layout

| Path | Contents |
|---|---|
| `bin/` | Numbered pipeline scripts |
| `config/` | Primer3 settings, provenance rules, final chromosomal oligo table |
| `data/` | Inventories and metadata (genome downloads and BLAST databases are gitignored) |
| `results/` | Per-step outputs, final oligo tables and validation reports |
| `docs/` | Decision log, handover, lessons learned, tool versions, exclusivity panel lists |

## Environment

WSL2 Ubuntu. Python 3.12, Biopython, pandas, Primer3 2.6.1 (used through primer3-py), BLAST+ 2.17, MAFFT
7.525, fastANI 1.34 and NCBI Datasets 18.29.1 in the base environment; Prokka 1.14.6 in `prokka_env`;
Panaroo 1.5.2 in `panaroo_env`. Exact versions are recorded in `docs/tool_versions.txt`. Genome FASTA files are never
committed. The exclusivity panel genomes and BLAST databases are not committed either; their accessions and
species are listed in `docs/exclusivity_panel_accessions.tsv` and `docs/exclusivity_panel_species.txt`.

## Documentation

- `docs/PROJECT_STATE.md`: decision log (D1-D29) and dated findings; the authoritative record.
- `docs/lessons_learned.md`: what went wrong, how it was caught, and what to do differently.
- [Case study (PDF)](docs/Case_Study_C_trachomatis_Oligonucleotide_Screening.pdf): a short narrative of the project, its verification checkpoints and its limitations.

## Author

Krzysztof Gizynski
