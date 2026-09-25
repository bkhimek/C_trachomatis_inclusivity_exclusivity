# Lessons Learned: C. trachomatis Inclusivity/Exclusivity Multiplex Oligo Design

**Document Date:** September 2026  
**Status:** Restart Phase - Integrated Approach  
**Related Document:** [COMPREHENSIVE_HANDOVER_RESTART.md](./COMPREHENSIVE_HANDOVER_RESTART.md)

---

## Executive Summary

During initial development of this multiplex PCR/TaqMan assay design project, a critical data quality issue emerged that led to unexpected project complexity and redesign cycles. This document captures the key lessons learned, particularly around **genome provenance auditing**, and explains how these lessons are being integrated into the restart phase.

**Key Takeaway:** "Complete genome" designation in GenBank/NCBI does not guarantee that an isolate is a natural environmental sample. Systematic provenance auditing at the BioProject level is essential for accurate assay design targeting natural population diversity.

---

## The Core Discovery: Genome Provenance Audit

### What Happened

The initial genome inventory consisted of **317 isolates**:
- 125 RefSeq complete genomes (NCBI curated, high-confidence)
- 149 GenBank-only complete genomes (submitted by authors)
- 43 chromosome-level assemblies (partial, not RefSeq)

**The Problem:** During oligo inclusivity validation, the assay showed 8 unexpected "misses"—genomic regions that were predicted to amplify but did not in certain isolates. These 8 misses clustered entirely within a single inventory tier: the 149 GenBank-only complete genomes.

### Investigation and Discovery

Detailed BioProject-level tracing revealed:
- **ALL 149 GenBank-only complete genomes traced to a single BioProject: PRJNA558398**
- Project title: *"Chromosomal recombination targets in Chlamydia interspecies lateral gene transfer"*
- Strain nomenclature pattern: `::Tn(x/c)L2/tetR-` (characteristic of lab-engineered constructs with selectable markers)
- These were **deliberately engineered laboratory strains**, not natural environmental isolates

### Why This Matters

1. **Design Goal Violation:** The project aims to design assays for detecting natural *C. trachomatis* in clinical samples. Including engineered lab strains in the reference set skews the definition of "natural diversity."

2. **False N-Masking:** When these non-natural strains differ systematically from natural isolates (due to engineered deletions, insertions, or antibiotic resistance markers), the consensus sequence algorithm incorrectly masks conserved positions as "variable," reducing oligo specificity.

3. **Inclusivity Artifacts:** The "misses" were not real probe design failures—they were real biological differences in engineered strains that should not have been in the reference set.

4. **Downstream Validation:** Later phases (plasmid targeting, exclusivity against related species) rely on accurate inclusivity baseline. Contaminated reference sets compromise downstream decisions.

---

## Secondary Issues: Draft Assemblies and MAG Artifacts

During the same audit, 11 of 12 supplementary draft assemblies were traced to **PRJEB35640** (MAG/metagenome-assembled genome database artifacts), not high-confidence isolate genomes. These were also excluded.

**Lesson:** Even "additional" or "supplementary" genomes require provenance verification.

---

## Technical Implications for Oligo Design

### Issue 1: Consensus Sequence Bias
When lab-engineered strains with engineered deletions are included:
- Positions unique to natural isolates appear "variable"
- Consensus algorithm marks these as 'N' (ambiguous)
- Resulting probes have lower specificity

**Solution:** Use only RefSeq complete genomes (125 isolates) for consensus building. This provides excellent natural diversity without lab-engineering artifacts.

### Issue 2: Probe Tm Gap Insufficiency
During initial design, probes were optimized for Tm 62-64°C while primers targeted ~60°C. This 2-4°C gap is insufficient for multiplex TaqMan assays (need 7-10°C gap).

**Root Cause:** The AT-rich C. trachomatis genome (43% GC) naturally limits achievable Tm values. Attempts to compensate by using short probes (24-31 bp) failed.

**Solution:** Extend probes to 35-40 bp, accepting longer synthesis times and higher costs, to achieve 68-72°C Tm (7-10°C gap from 60°C primers).

---

## Restart Approach: Lessons Integrated from Day 1

Based on these discoveries, the restart phase implements several key changes:

### 1. Explicit Provenance Tracking (bin/01)
- Curate only 125 RefSeq complete genomes (all with documented RefSeq status)
- For each accession, record:
  - Assembly source (RefSeq vs GenBank)
  - Assembly category (complete genome)
  - BioProject accession
  - Collection date and location (where available)
- This becomes the reference standard for all downstream work

### 2. Corrected Primer3 Parameters (bin/28, incorporated from restart)
**Old parameters (problematic):**
```
PRIMER_INTERNAL_OPT_TM = 66
PRIMER_INTERNAL_MIN_TM = 62
PRIMER_INTERNAL_MAX_TM = 70
PRIMER_INTERNAL_OPT_SIZE = 30    # ← Too short
PRIMER_INTERNAL_MIN_SIZE = 24
PRIMER_INTERNAL_MAX_SIZE = 36
```

**New parameters (corrected):**
```
PRIMER_INTERNAL_OPT_TM = 68      # ← Shifted up slightly
PRIMER_INTERNAL_MIN_TM = 66      # ← Tighter control
PRIMER_INTERNAL_MAX_TM = 72
PRIMER_INTERNAL_OPT_SIZE = 38    # ← Extended
PRIMER_INTERNAL_MIN_SIZE = 35    # ← Extended
PRIMER_INTERNAL_MAX_SIZE = 42    # ← Extended
```

Expected result: Probes 35-40 bp at 68-72°C (7-10°C gap from primers)

### 3. Broader Target Exploration (bin/31)
Rather than stopping at 5 candidate regions, the restart will identify ALL genomic regions with 100% presence in the 125 RefSeq genomes. This likely yields 20-30+ candidates, providing options for:
- Multiplex assays with more than 5 targets
- Redundant detection if one target fails
- Serovar-specific vs pan-species coverage

### 4. Fresh Plasmid Optimization (bin/24-25)
Curate 128 plasmid records with explicit consideration for Swedish new variant (nvCT) deletion carriers. Design separate oligo sets for:
- Standard CT plasmids (majority of isolates)
- nvCT-specific variant (emerging Swedish lineage with 377 bp deletion)

---

## Recommendations for Ongoing Data Integrity

### For This Project

1. **Every genome used must have documented RefSeq status or equivalent curation.** Do not mix RefSeq with GenBank-only submissions.
2. **BioProject tracing should be part of the initial setup (bin/01), not a retrospective audit.** This prevents contamination at the source.
3. **Strain nomenclature should be reviewed.** Lab-engineered constructs (marked with antibiotic markers or transposon tags) should be flagged and excluded.
4. **When inclusivity misses occur, investigate root causes at the genome level**, not just the oligo level.

### For Similar Projects

1. **"Complete genome" is a technical classification, not a sample-type guarantee.** Always verify:
   - Is this a RefSeq or GenBank entry?
   - What is the source (clinical isolate vs lab construct)?
   - Are there documented antimicrobial resistance or engineering markers?

2. **Provenance tracing should be automated.** A simple script checking NCBI metadata (BioProject, strain name patterns, assembly source) can flag suspicious entries before they enter the reference set.

3. **Reference genome sets should be version-controlled.** Document:
   - Accession numbers and versions
   - Curation date
   - Exclusion rationale for any removed genomes
   - This makes future updates and audits reproducible.

4. **Consensus algorithms are sensitive to contamination.** If using N-masking at 99% conservation:
   - Verify that N-masked positions match known variable sites
   - If unexpected N-masking occurs, investigate at the isolate level
   - Consider stratified analysis (RefSeq vs other sources) to isolate problems

---

## Timeline: How This Delayed the Project

**Initial Discovery Phase (Week 1-2):**
- Designed oligos with full 317-genome inventory
- Ran BLAST inclusivity validation: discovered 8 misses
- Initial hypothesis: oligo design problem (too short, low Tm)

**Investigation Phase (Week 3-4):**
- Analyzed failed genomes: all from same inventory tier
- Traced to PRJNA558398: lab-engineered recombinants
- Realized fundamental reference set contamination

**Redesign Phase (Week 5):**
- Extended probes from 30bp → 38bp (addressing Tm gap)
- Excluded non-RefSeq genomes from consensus
- Re-ran design and validation

**Current Phase (Week 6):**
- Documented lessons learned
- Planning systematic restart with integrated provenance tracking
- Estimated 20-32 hours for full restart with corrected approach

**Total delay:** ~2 weeks of rework that could have been avoided with upfront provenance auditing.

---

## Key Files in This Repository

| File | Purpose |
|------|---------|
| **COMPREHENSIVE_HANDOVER_RESTART.md** | Detailed technical handover with directory structure, parameter specifications, and step-by-step instructions for restart phase |
| **bin/01_genome_curation.py** | (To be created) Curate 125 RefSeq complete genomes with provenance tracking |
| **bin/02_plasmid_curation.py** | (To be created) Curate 128 plasmid records with nvCT variant flagging |
| **results/genome_provenance.tsv** | (To be created) Complete provenance audit for all genomes: accession, RefSeq status, BioProject, strain nomenclature |
| **results/plasmid_provenance.tsv** | (To be created) Complete provenance audit for all plasmids: accession, size, nvCT status, coverage |

---

## Conclusion

The genome provenance audit was a valuable discovery that redirected the project toward a more robust approach. Rather than viewing it as a setback, treating it as an integrated design principle from the restart ensures:

- **Data Integrity:** Only rigorously curated genomes form the reference set
- **Design Quality:** Consensus sequences and parameter optimization work from valid inputs
- **Reproducibility:** Every genome is documented, auditable, and traceable to its source
- **Scalability:** The provenance-first approach can be applied to plasmid databases, related species, and future projects

The restart phase incorporates all these lessons systematically, with the expectation of faster, cleaner execution and higher confidence in final assay designs.

---

**Prepared by:** Claude Haiku 4.5  
**For:** GitHub repository documentation and project continuity  
**Related:** https://github.com/bkhimek/C_trachomatis_inclusivity_exclusivity
