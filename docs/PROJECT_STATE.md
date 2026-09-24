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
| D6 | Tm rule: probe Tm minus max(primer Tm) must be at least 5 C (hard floor, enforced by a post-filter because Primer3 cannot enforce it); sets with a gap of 7 C or more rank higher | Earlier design had only 2-4 C gap. A 5 C gap has worked in practice and 7+ C is hard to reach on an AT-rich genome |
| D7 | Primer3 settings (config/primer3_settings.txt): primers Tm 59/60/61, size 18/20/25; probe Tm 66/68/72, size 30/33/36 | Tested in bin/00 on a synthetic template; re-verify on real targets |
| D8 | Script numbering follows the layout in README.md (00-24). The handover numbering (01-23) and LESSONS_LEARNED numbering (bin/24-25, bin/31) are superseded | Old files disagreed with each other |
| D9 | Plasmid design must be nvCT-aware: avoid the 377 bp deletion; separate standard and nvCT sets if needed | Known clinical failure mode of earlier commercial assays |
| D10 | The 35-42 nt probe plan is dropped: Primer3 2.6.1 rejects PRIMER_INTERNAL_MAX_SIZE above 36 (built-in limit). With identical explicit salt settings for primers and probe (placeholders: 50 mM Na, 3.0 mM Mg, 0.8 mM dNTP, 250 nM), 30-36 nt probes gave Tm 66-68 C and a gap of 6-8 C in the bin/00 smoke test (synthetic 43% GC template, not real data; see docs/bin00_smoke_test_results.txt) | Long probes were never possible. The earlier 2-4 C gap may partly reflect inconsistent Tm settings (hypothesis, unverified) |

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
