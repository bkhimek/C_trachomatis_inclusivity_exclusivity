# Project state and decision log

Single source of truth for the restart. Where this file disagrees with the archived handover
documents in `docs/archive/`, this file wins. Last updated: 2026-09-24.

## Decisions
| ID | Decision | Rationale |
|----|----------|-----------|
| D1 | Reference set is RefSeq complete C. trachomatis genomes only (125 verified against NCBI on 2026-09-24 by bin/01) | Simpler, cleaner set with documented curation |
| D2 | Excluded from the earlier 317-genome inventory: 149 GenBank-only genomes from PRJNA558398 (lab-engineered recombinants) | All 8 earlier inclusivity "misses" fell in this tier |
| D3 | Excluded 11 of 12 "target absent" draft assemblies traced to PRJEB35640 (MAG artifacts). The remaining one (PRJEB2035, legitimate clinical project) is flagged for independent follow-up | Provenance-verified |
| D4 | The 43 chromosome-level assemblies are out of the primary set. This is a scope simplification, not a quality judgement | They were natural isolates; may be re-added as secondary validation |
| D5 | Provenance audit (bin/02) runs BEFORE any analysis and is applied to the RefSeq genomes too | RefSeq status alone does not guarantee natural isolate |
| D6 | Tm rule: probe Tm minus max(primer Tm) must be at least 5 C (hard floor, enforced by a post-filter because Primer3 cannot enforce it); sets with a gap of 7 C or more rank higher | Earlier design had only 2-4 C gap. A 5 C gap has worked in practice and 7+ C is hard to reach on an AT-rich genome |
| D7 | Primer3 settings (config/primer3_settings.txt): primers Tm 59/60/61, size 18/20/25; probe Tm 66/68/72, size 20/22/28 with PRIMER_INTERNAL_WT_SIZE_GT=1.0 (longer probes penalised) | Chosen from bin/00b (synthetic templates: 22 nt probes at Tm>=66 are plentiful); re-verify on real targets |
| D8 | Script numbering follows the layout in README.md (00-24). The handover numbering (01-23) and LESSONS_LEARNED numbering (bin/24-25, bin/31) are superseded | Old files disagreed with each other |
| D9 | Plasmid design must be nvCT-aware: avoid the 377 bp deletion; separate standard and nvCT sets if needed | Known clinical failure mode of earlier commercial assays |
| D10 | The 35-42 nt probe plan is dropped: Primer3 2.6.1 rejects PRIMER_INTERNAL_MAX_SIZE above 36 (built-in limit). With identical explicit salt settings for primers and probe (placeholders: 50 mM Na, 3.0 mM Mg, 0.8 mM dNTP, 250 nM), 30-36 nt probes gave Tm 66-68 C and a gap of 6-8 C in the bin/00 smoke test (synthetic 43% GC template, not real data; see docs/bin00_smoke_test_results.txt) | Long probes were never possible. The earlier 2-4 C gap may partly reflect inconsistent Tm settings (hypothesis, unverified) |
| D11 | Shorter probes are preferred: longer probes give higher background fluorescence (observed in earlier wet-lab work), which matters in some PCR systems. Design goal is the shortest probe that keeps Tm at least 5 C above the higher primer Tm; final ranking prefers shorter probes among sets that pass the gap filter. Range set in D7 from bin/00b (docs/probe_length_sweep_results.txt) | Replaces the earlier 30-36 nt range |
| D12 | Post-filter on Primer3 output (bin/12): hard reject if probe Tm minus higher primer Tm is below 5 C; hard reject if the probe has G at the 5' end (commonly recommended for TaqMan; confirm for the chosen dye); rank survivors by shorter probe first, then larger gap | Primer3 cannot express these rules itself |
| D13 | Genome tiers: (1) primary = used for consensus building and the inclusivity claim; (2) quality-review = natural isolates with suspicious quality metrics (e.g. CheckM contamination, ANI flags), NOT used for consensus, but every oligo is tested against them and results are reported separately; (3) excluded = experimental, engineered or laboratory-selected strains, plus anything shown not to be C. trachomatis. Each decision is recorded per genome with a reason in config/provenance_overrides.tsv | Keeps natural diversity in the evidence without letting doubtful assemblies shape the consensus |

## Open questions
- RESOLVED (D10): Primer3 2.6.1 rejects probes longer than 36 nt.
- MGB or LNA probes remain a fallback only if real-target design fails at 30-36 nt.
- Confirm the exact RefSeq complete genome count and the two nvCT plasmid accessions (handover lists NC_012630.1 and FM865439.1; verify).
- Follow up the single PRJEB2035 anomaly from D3.
- Exact Tm calculation conditions (Mg2+, dNTP, oligo concentrations) to match the intended wet-lab master mix.

## Known inconsistencies in the original handover files (all resolved by the decisions above)
- Script numbering differed between the two documents (D8).
- The Tm gap was stated as 7-10 C and as 8-12 C, and the numbers did not guarantee either (D6, D7).
- The handover says "clone the repo", but the working directory is already this project folder, not a `_RESTART` copy.
- Older numbers (168 genomes, 5 finalist regions) are historical and not part of the restart.

## Environment state (checked 2026-09-24)
Found: python 3.12.2, mafft 7.525, fastANI 1.34, NCBI datasets 18.29.1, git 2.43.0, gh 2.97.0.
Tool versions are recorded in docs/tool_versions.txt (written by bin/00).
Prokka and Panaroo are in their own conda envs (not on the base PATH).

## Findings log
- 2026-09-24, bin/01: 125 RefSeq complete records, all 125 downloaded; md5 and sequence-length checks passed. Only 34 of 125 assemblies contain a plasmid sequence (91 are chromosome-only), so the plasmid inventory must come from separate plasmid records (bin/16).
- 2026-09-24, bin/02 first pass: 111 INCLUDE, 14 REVIEW (5 transposon mutants PRJNA386688; 3 chxR mutants PRJNA315548; 3 tet-selected derivatives; A/HAR-13 ANI flag; 2 RC-F(s) genomes with CheckM contamination 7.15). Neither PRJNA558398 nor PRJEB35640 is among the 125.
- Audit gap found: name-based keyword rules missed BioProjects whose titles describe experiments (e.g. laboratory adaptation, gene-function studies, re-sequencing). BioProject-title rules added; PRJNA1066129 has a title naming Bordetella pertussis for a genome labelled C. trachomatis (held for review).
- 2026-09-24, provenance review: PRJNA1102004 (7 genomes) come from experimentally infected pig-tailed macaques (host Macaca nemestrina) and are excluded as experimental. Quality-review tier: PRJNA234355 (laboratory-adaptation study, 4 Portuguese clinical isolates), RC-F(s)/852 and RC-F(s)/342 (CheckM contamination 7.15 and about 1.084 Mb, roughly 40 kb above typical), and LGV II 434 (Vircell; BioProject title names Bordetella pertussis). Primary: A/HAR-13 (the ANI flag is on the species type-strain assembly itself; confirm with fastANI in bin/03) and PRJNA316787 (Jena patient samples, 1990).
- Redundancy: PRJNA338746 is 14 serial isolates from one patient (1986-1998), and several reference strains (L2/434, D/UW-3, E/Bour) are sequenced more than once. Open question for the consensus step (bin/10): collapse near-identical genomes by SNP distance or weight them, so one lineage does not dominate the 99% conservation rule.
