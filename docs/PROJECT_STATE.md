# Project state and decision log

Single source of truth for the restart. Where this file disagrees with the archived handover
documents in `docs/archive/`, this file wins. Last updated: 2026-09-24.

## Decisions
| ID | Decision | Rationale |
|----|----------|-----------|
| D1 | Reference set is RefSeq complete C. trachomatis genomes only (target 125; count must be re-verified against NCBI in bin/01) | Simpler, cleaner set with documented curation |
| D2 | Excluded from the earlier 317-genome inventory: 149 GenBank-only genomes from PRJNA558398 (lab-engineered recombinants) | All 8 earlier inclusivity "misses" fell in this tier |
| D3 | Excluded 11 of 12 "target absent" draft assemblies traced to PRJEB35640 (MAG artifacts). The remaining one (PRJEB2035, legitimate clinical project) is flagged for independent follow-up | Provenance-verified |
| D4 | The 43 chromosome-level assemblies are out of the primary set. This is a scope simplification, not a quality judgement | They were natural isolates; may be re-added as secondary validation |
| D5 | Provenance audit (bin/02) runs BEFORE any analysis and is applied to the RefSeq genomes too | RefSeq status alone does not guarantee natural isolate |
| D6 | Tm rule: probe Tm minus max(primer Tm) must be at least 7 C, enforced by a post-filter because Primer3 cannot enforce it | Earlier design had only 2-4 C gap |
| D7 | Initial Primer3 settings: primers Tm 59/60/61, size 18/20/25; probe Tm 68/69/72 (min/opt/max), size 35/38/42. Probe size limits are provisional until bin/00 confirms what the installed Primer3 accepts | Pending verification |
| D8 | Script numbering follows the layout in README.md (00-24). The handover numbering (01-23) and LESSONS_LEARNED numbering (bin/24-25, bin/31) are superseded | Old files disagreed with each other |
| D9 | Plasmid design must be nvCT-aware: avoid the 377 bp deletion; separate standard and nvCT sets if needed | Known clinical failure mode of earlier commercial assays |

## Open questions
- Does the installed Primer3 accept probe lengths above about 36 nt? (bin/00)
- If long probes fail or quench poorly, switch to MGB or LNA probes at roughly 18-25 bp?
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
blastn, makeblastdb, primer3_core, nextflow present (versions to record in bin/00).
Prokka and Panaroo are in their own conda envs (not on the base PATH).
