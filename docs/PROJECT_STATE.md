# Project state and decision log

Single source of truth for the restart. Where this file disagrees with the archived handover
documents in `docs/archive/`, this file wins. Where this file disagrees with any document outside
`docs/` (including OneDrive `Claude outputs/`, current or `previous/`), this file wins too — see the
2026-09-27 update below for why that now needs saying explicitly. Last updated: 2026-09-27.

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
- RESOLVED (2026-09-27, D19): Tm/Tm-gap must come from an actual calculation, not the settings file's
  target values — see the 2026-09-27 update.
- MGB or LNA probes remain a fallback only if real-target design fails at 30-36 nt.
- Confirm the exact RefSeq complete genome count and the two nvCT plasmid accessions (handover lists NC_012630.1 and FM865439.1; verify).
- Follow up the single PRJEB2035 anomaly from D3.
- Exact Tm calculation conditions (Mg2+, dNTP, oligo concentrations) to match the intended wet-lab master mix — still a placeholder in `config/primer3_settings.txt`; every Tm/gap number in this project (Phase 1 and Phase 2 alike) will shift slightly once real values are supplied.
- RESOLVED (2026-09-27): BLAST validation of the 12 redesigned Phase 1 oligos (mutL/aroB/PSD2/group_306) —
  clean; see the addendum at the end of the 2026-09-27 update below.
- RESOLVED (2026-09-27, D22): which sets make up the final panel vs. which are backups — 4 genes / 7 sets
  locked in (mutL, aroB x3, PSD2 x2, group_306); group_159/140/181 and PSD2 Alt2 parked.
- **New (2026-09-27):** D13's quality-review-tier genome check (10 genomes, tested separately, not used for consensus) has not been run against any of the 13 designed sets (7 final-panel + 6 parked) yet. This is now the largest remaining gap before the panel can be called fully validated end to end.
- RESOLVED (2026-09-27): `docs/HANDOVER.md`, this file, and `docs/lessons_learned.md` were committed and pushed to `main` (commit `860c638`), via a git-enabled session run by the user in WSL after this cloud session found it had no push access of its own (see addendum). The oligo design deliverables themselves (Phase 1/2 design docs, FASTAs, combined ranking, BLAST validation writeups) are still OneDrive-only by choice — see Open Items in HANDOVER.md.
- **New (2026-09-27):** the plasmid target (nvCT-aware, multicopy) has not been started at all — every gene designed so far (11 sets) is chromosomal. Scope reminder from the top of this project: chromosomal + plasmid.

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
- 2026-09-24, QC rule: a chromosome more than 8 kb from the median (1,042,743 nt) or CheckM completeness below 97% is now flagged automatically by bin/02 (empirical tail of the 125 genomes). QH111L (-17 kb, 91.6%), B/TW-5/OT (-9.5 kb, 93.8%) and RC-J(s)/122 (+19 kb) moved to the quality-review tier: possible real deletions or assembly issues, so they are still tested for inclusivity but do not shape the consensus. Final tiers: 97 primary, 10 quality-review, 18 excluded.

## Update 2026-09-24: species check, ompA typing

**D14.** Serial and near-identical isolates are all kept in the primary set for consensus and inclusivity (more isolates = more chance to see variants; redundancy costs nothing). Variant frequencies are reported per near-identical cluster (bin/03 clusters) so that clonal copies are not read as independent observations.

**Findings.**
- bin/03 fastANI (125 genomes): all pairs >= 98.90% ANI, 0 flagged, so every genome is C. trachomatis. Primary set collapses to 58 clusters at ANI >= 99.99 (largest 7).
- bin/04 ompA typing: ompA extracted from 125/125; 14 serovar groups in the primary set (checkpoint >= 8: PASS). Label vs nearest neighbour: 100 exact, 1 same group, 3 disagree of 104 labelled.
- RC-J/971 (GCF_000441795.1): labelled J, ompA 100% L2/L2c, genome ANI to L2/434/Bu 99.71 (not identical). Kept primary; serovar label inconsistent with ompA. J is covered by 12 other genomes.
- D/13-96 (GCF_000590675.1): ompA nearest Da at 99.75; subtype variant, no action.
- LGV II 434 (GCF_036285905.1): already quality-review; ompA nearest L1 (100%) adds a second inconsistency.
- D/Ep6/S19-121 (GCF_059083935.1): ompA only 95.61% to any set member; normal size/CheckM/BioProject. Kept primary pending web BLAST of its ompA (user). If hits are poor -> quality-review.

## Update 2026-09-25: Panaroo pangenome, and two corrections

**D15.** Panaroo (bin/06) is run directly (subprocess call to the panaroo binary in panaroo_env), not through
Nextflow, even though Nextflow is installed. At this scale (single machine, ~100 genomes, one tool) a direct
call is simpler to run, debug and resume than a Nextflow pipeline, and matches bin/01-05.

**Correction.** HANDOVER.md previously said "100 primary / 7 quality-review / 18 excluded". The correct,
unchanged split (confirmed again by bin/06 reading provenance_audit.tsv directly) is 97 primary / 10
quality-review / 18 excluded, matching the original bin/02 findings log entry. bin/05's "107 genomes"
figure was always correct (97 + 10).

**Findings.**
- bin/06 Panaroo pangenome on the 97 primary genomes: 904 gene clusters total -> 874 core (>=99%), 6
  soft-core (95-99%), 21 shell (15-95%), 3 cloud (<15%). Very small accessory genome, as expected for
  C. trachomatis. core_genes.fasta (874 representative sequences) is the input for bin/07 exclusivity
  screening.

## Update 2026-09-25: exclusivity screening, panel reuse

**D16.** The exclusivity panel (10 genus-tier Chlamydia species / 31 genomes, 25 clinical-tier species / 92
genomes, 123 genomes total) was recovered from an earlier abandoned trial run
(~/projects/trial_C_trachomatis_inclusivity_exclusivity, not tracked in git) and reused as-is: its
composition and rationale (docs/exclusivity_panel_species.txt) were not affected by the reasons for the
restart (genome provenance, probe Tm gap). The already-built genomes and BLAST databases were copied over
and verified against the trial run's own checksums rather than re-downloaded.

**Findings.**
- bin/07 exclusivity screening: of 874 core genes, 30 have a gap of >=150bp with zero BLAST similarity to
  the genus-tier panel at any identity; 692 have such a gap when only counting hits >=85% identity (a more
  realistic threshold for actual PCR cross-reactivity). Against the more distant clinical-tier panel, 859
  and 873 of 874 genes are clean respectively. Full per-gene results: results/exclusivity/core_gene_exclusivity.tsv.
- Top exclusivity-clean genes by gap size include tarP (a candidate from the earlier project), several
  cardiolipin-synthase-related gene clusters, incG, and a number of unannotated ("hypothetical protein") genes.

## Update 2026-09-25: candidate region discovery and consensus building

**bin/08 candidate_regions.py.** For each of the 692 core genes with a >=150bp exclusivity-clean gap at 
>=85% identity (id85 threshold), the script loads Panaroo's per-gene alignment and walks the representative 
sequence through the exclusivity window, computing the fraction of genomes with the majority base at each 
position. A position is "conserved" if agreement is >=99%. The script finds the longest run of conserved 
positions inside the exclusivity window and reports it as the refined candidate region.

**Findings.**
- 588 of 692 genes (85.0%) with >=150bp id85 exclusivity gap also have >=100bp of >=99% conserved sequence 
  inside that window (--min-region 100 bp; configurable).
- Top candidates by region length and copy-number tier: ranked by region length (descending), 
  tie-broken by single-copy preference then gene name. See results/candidate_regions/candidate_regions.tsv 
  for the full table and results/candidate_regions/candidate_regions.fasta for the refined region sequences.
- The ranking is input to bin/09; the default (--top 30) takes the 30 longest conserved+exclusive regions.

**bin/09 build_consensus.py.** For the top N candidate regions (default N=30), the script builds a 
true majority-consensus sequence by computing the majority base at every alignment position across all 
genomes that carry the gene, rather than using one representative's sequence. This corrects for positions 
where the representative genome carries a minority base (still >=99% conserved overall by construction).

**Findings.**
- bin/09 completed successfully on the top 30 candidates. Output: results/consensus/consensus_regions.fasta 
  (majority-consensus sequence per region) and results/consensus/consensus_variability.tsv (per-position 
  report for positions with <100% invariance, i.e., variant alleles present in the alignment).
- Ready for bin/10+ (Primer3 design step): design a complete PCR/TaqMan assay against these 30 consensus sequences, 
  then post-filter and validate.

**Next immediate step:** User to web BLAST the top consensus candidates against NCBI nt to validate 
that the exclusivity analysis is sound (i.e., top candidates have few/no off-target hits to clinical 
species). This manual validation step was done in the earlier project and is recommended before 
committing effort to Primer3 design.

## Update 2026-09-27: reconciling an untracked side thread, Phase 2 backup design, methodology corrections

**Context.** Between the 2026-09-25 update above (pipeline paused after bin/09, before bin/10 Primer3
design) and this update, the actual Primer3 design and QC of four genes — mutL, aroB, PSD2, group_306 —
happened in a separate, untracked side session (Claude Haiku, 2026-09-24 to 26; deliverables live only in
OneDrive `Claude outputs/previous/`, e.g. `OLIGO_MASTER_TABLE_COMPLETE.md`, `01_LESSONS_LEARNT.md`,
`02_PROJECT_STATUS.md`), never entered into this decision log and never run through the repo's own
`bin/` scripts. A follow-on Claude Sonnet 5 session (2026-09-27) was hand-started from that side thread's
own handover note, treating those four genes as an already-finished "Phase 1" and adding backup/alternative
designs for group_159, group_140, group_181 ("Phase 2") plus two extra loci each for aroB and PSD2. This
update reconciles both threads into the single decision log and **supersedes several specific numbers**
the untracked thread had reported as final.

**D17.** The mutL/aroB/PSD2/group_306 gene choices and their bin/08 conserved-window coordinates
(`results/candidate_regions/candidate_regions.tsv`: aroB 257-953, PSD2 300-889, mutL 1-560, group_306
462-681, all 100% conserved across the 97 primary genomes, zero variable positions) are adopted into this
log and are correct. The specific oligo **sequences and QC numbers** the untracked thread reported for
them are not — see D19-D21 and the redesign below.

**D18.** Web BLAST validation of any oligo (≤~30 nt) uses Expect threshold=1000, word_size=7, low-complexity
filter OFF, against both a human-genome database (prefer the full assembly + transcripts, not only a
curated gene-loci subset) and `core_nt` with `NOT(txid813[ORGN])`. *Rationale:* the untracked thread's
BLAST pass used different (likely default/stricter) parameters; re-running all 44 of its oligos under
these settings surfaced real hits its own report had characterized as uniformly weak (see findings below).

**D19.** Tm and the Tm gap (D6) are computed by actually running `primer3-py`/`primer3_core` (or an
equivalent salt-corrected nearest-neighbor calculation, cross-checked against a second independent
implementation) on the real candidate sequence under `config/primer3_settings.txt` — never taken from the
settings file's own opt/min/max target values as a stand-in. *Rationale:* see findings below — the
untracked thread's master table recorded a flat, uncalculated Tm for all 44 oligos.

**D20.** An off-target BLAST hit is only actionable if a **partner primer or probe from the same designed
set** also hits within a plausible product distance (~400 bp), correctly oriented, on the same accession —
a single probe or primer matching an off-target sequence cannot by itself generate a false TaqMan signal.
Single-oligo "% identity to human/non-target" is retained as context in reports but is not itself a
pass/fail criterion. *Rationale:* the untracked thread's QC report initially stated a blanket "all oligos
pass" while its own table showed a 100%-identity, full-length hit for one probe; the pair-level check is
what actually determines cross-reactivity risk.

**D21.** Oligo-dimer QC for a TaqMan set checks all three pairwise heterodimer combinations (F-R, F-Probe,
R-Probe) plus each oligo's own hairpin and homodimer, via `primer3-py`'s `calc_hairpin`/`calc_homodimer`/
`calc_heterodimer`. Severity is classified by the structure's own melting Tm relative to reaction
temperature (NONE <0°C, LOW 0-40°C, MEDIUM 40-55°C, HIGH ≥55°C), not primer3's binary `structure_found`
flag, which fires on any ΔG<0 including thermodynamically irrelevant structures. *Rationale:* the untracked
thread used a custom, hand-written hairpin/dimer detector not cross-checked against a validated tool, and
never explicitly checked F-Probe/R-Probe heterodimers (only F-R).

**Findings — Phase 2 backup/alternative design (2026-09-27).**
- group_159 (window 19-247/732bp), group_140 (417-735/852bp), group_181 (1-183/591bp): each window
  reconfirmed 100% conserved across all 97 primary genomes (zero variable positions), and each gene
  reconfirmed **present, single-copy, in all 97** primary genomes directly from the Panaroo per-gene
  alignments (97/97 real non-empty sequences each), not merely inferred from conservation-where-present.
  Designed with `primer3-py` per the D7 settings. Recommended (Rank 1) sets: group_159 Tm gap 7.06°C,
  group_140 6.84°C (plus a second, more distal probe locus, gap 6.81°C), group_181 6.47°C (plus a second
  locus, gap 8.61°C — the best gap of the batch). All LOW structure severity; all 3' GC-stable except
  group_140's second-locus reverse primer (flagged, needs a 1-3 nt shift) and one MEDIUM-severity
  alternative rank each for group_159/group_181.
- aroB and PSD2 each got two additional, genomically independent conserved sub-regions inside their
  already-exclusivity-clean full-gene windows (aroB: 1-125 and 955-1078 of 1122bp; PSD2: two probe sites
  within 49-253 of 906bp) as true amplicon-level backups to the primary design. Gaps 6.44-8.71°C; PSD2 Alt
  2 has the best gap of the whole project (8.71°C) but a non-trivial forward-primer hairpin flagged for a
  re-pick before ordering.
- BLAST (D18) of all 7 Phase 2 sets, plus a full re-run of all 44 Phase 1 oligos, against human genome
  (RefSeqGene, then the broader full-assembly-plus-transcripts database) and core_nt: **zero plausible
  off-target amplicons anywhere** by the D20 pair-level check, and zero hits to *C. muridarum*/*C. suis*
  anywhere. Two individual-oligo hits are worth watching in a human-DNA no-template control:
  group140_R1 (19/20nt, E≈0.04, chr7) and group159_probe1 (20/23nt, E≈0.02, DNAJC5 locus) — neither has a
  partner nearby, so neither is a design blocker.

**Findings — Phase 1 Tm-gap failure and redesign (2026-09-27).** Applying D19 to the untracked thread's
44 mutL/aroB/PSD2/group_306 oligos found **all four genes fail D6's Tm-gap floor as actually calculated**:
PSD2 gap ≈0.2°C (probe 63.8°C vs. the 66°C floor), mutL ≈2.6-3.1°C (probe 65.2°C, borderline on the floor
depending on calculation method), group_306 ≈2.7°C (probe 63.3°C), aroB **negative** (probe 58.6°C, 7-9°C
below its own primers' Tm, and 7.4°C below the 66°C floor). Several primers also sit outside the 59-61°C
window (PSD2 forward over, aroB forward under, mutL forward mostly over). Cross-checked with an
independent nearest-neighbor calculation (Biopython `Tm_NN`); agreement within ~1°C. This does not indicate
a new specificity problem (D20's pair-level BLAST check still finds all 44 clean) — it means the untracked
thread's "Tm=60/66, ready for wet-lab" claim for these sequences was not correct.

Re-running `primer3-py` directly on the *same* already-established, 100%-conserved D17 window coordinates
(no new region search) returned fully compliant replacement sets for all four genes on the first pass:
mutL gap 8.07°C, aroB 7.75°C, PSD2 7.54°C, group_306 7.82°C — all LOW structure severity, all D21-clean,
and (for mutL/group_306 specifically) free of the self-dimer/F-F-dimer issues the untracked thread's
sequences had. Full sequences: `PHASE1_REDESIGNED_PROBES.md` (OneDrive `Claude outputs/`).

**Addendum, same day: Phase 1 redesign BLAST validation, and getting this session's work into git.**
The 12 redesigned oligos were BLAST-validated (D18 settings, both databases) the same day. Result: clean —
zero *C. muridarum* hits, zero plausible off-target amplicon in the human genome by the D20 pair-level
check. One finding worth recording rather than just clearing: `aroB_redesign_F` and `aroB_redesign_probe`
both have a full-length, 100%-identity hit to *C. suis* across essentially its whole genome collection in
`core_nt` (32 accessions, same ~71 bp F-to-probe spacing every time) — the aroB target region is genuinely
conserved between *C. trachomatis* and *C. suis* at those two sites. `aroB_redesign_R` has zero hits
anywhere in the *C. suis* genome, so D20 clears this (no completing primer pair, no plausible amplicon),
but it means this particular reverse primer is carrying all of the genus-level specificity for the aroB
set — worth keeping in mind if aroB is ever redesigned again. Full detail and the systematic pair-level
check for all 12 oligos: `PHASE1_REDESIGN_BLAST_VALIDATION.md` (OneDrive `Claude outputs/`).

Separately: this cloud session attempted to push `docs/HANDOVER.md`/`PROJECT_STATE.md`/`lessons_learned.md`
to GitHub directly and found it has read-only access to the repo (clone works because the repo is public;
a direct push attempt was refused by session policy, and no in-session mechanism exists to request write
access). The user ran the actual `git commit`/`git push` themselves in WSL instead, landing commit
`860c638` on `main`. The oligo design deliverables (FASTAs, per-gene docs, the combined ranking, the two
BLAST validation writeups) remain OneDrive-only for now — deliberately, since two components (item 3 in
HANDOVER's Open Items) still need a re-pick before the file set is final.

**Superseded:** the untracked thread's `OLIGO_MASTER_TABLE_COMPLETE.md` / `OLIGO_MASTER_TABLE_WITH_IDENTITY.md`
sequences and QC numbers for mutL/aroB/PSD2/group_306, and its "ready for wet-lab validation" status
determination, are superseded by the redesign above pending D18 BLAST confirmation. Its gene *choice*,
region *coordinates*, zero-non-target-Chlamydia finding, and the general absence-of-plausible-off-target-
amplicon conclusion all still hold.

**Current full candidate-set inventory (13 gene-level designs — 11 above plus group_140/group_181's second
loci, counted separately since they're genomically independent amplicons — 2026-09-27, updated same day
once the redesign's BLAST came back):** see `PHASE1_PHASE2_COMBINED_RANKING.md` for the complete ranked
table. Ten of the thirteen sets are fully D6/D18/D19/D20/D21-compliant end to end: Tm gap ≥5°C (most ≥7°C),
LOW structure, and clean BLAST. Three (group_140 locus 2, group_181 locus 2, PSD2 Alt 2) are compliant on
Tm/BLAST but each has one flagged structural component needing a re-pick.

**D22 (2026-09-27). Final chromosomal panel locked in: 4 genes, 7 sets — mutL; aroB (redesign, primary +
Alt1 + Alt2, three independent loci); PSD2 (redesign, primary + Alt1, two independent loci); group_306.**
*Rationale:* the user asked for "5-10 good oligo sets against 2-4 targets" and to stop optimizing once
that's met — a composite score (Tm-gap margin + structure severity + BLAST cleanliness) across all 13
candidate sets put the four original Phase 1 genes at the top once their redesign was BLAST-validated
(scores 87-94 of 100, vs. 61-87 for the nine Phase 2 sets), and between them they already supply 7 clean,
unflagged sets — squarely inside the requested range, with no further design work needed. `group_159`,
`group_140` (both loci), `group_181` (both loci), and `PSD2 Alt 2` are **parked, not deleted**: fully
designed and validated (aside from the two long-standing structural flags on group_140 locus 2 and PSD2
Alt 2, and one flagged-but-unexplained MEDIUM call on group_181 locus 2), kept in reserve in case a
final-panel gene underperforms at the bench, but no further design work is planned on them. Full per-oligo
detail for all 13 sets (39 oligos: sequence, length, Tm, GC%, structure, three-way dimer check, human and
whole-database BLAST divergence) is in `Oligo_QC_Reference.xlsx` (OneDrive `Claude outputs/`).

**Addendum: closing the D21 gap for the Phase 1 redesign.** `PHASE1_REDESIGNED_PROBES.md` had only
explicitly reported each redesigned oligo's own hairpin/homodimer plus F-R heterodimer, not the full D21
three-way check. Ran it directly with `primer3-py` on all 4 redesigned sets: F-Probe and R-Probe
heterodimers are NONE or LOW everywhere (aroB's R-Probe is the single highest at 8.2°C, still far below
reaction temperature) — no MEDIUM/HIGH anywhere. D21 is now fully closed for all 13 candidate sets project-wide.
