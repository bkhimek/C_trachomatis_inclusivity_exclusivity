# Plasmid Primary + Reserve — D18 BLAST validation (2026-09-27)

Web BLAST of the 6 plasmid oligos (Primary F/R/Probe, Reserve F/R/Probe), D18 settings confirmed from the
returned JSON params (Expect=1000, filter off, `entrez_query: "all [filter] NOT(txid813 [ORGN])"` on the
whole-database run). Two databases: human genome + transcript (GPIPE/9606 ref_top_level + rna), and core_nt
excluding *C. trachomatis* itself.

## Human genome + transcript database

Best hit per oligo, all weak and partial (none full-length):

| Oligo | Best hit | E-value | Identity |
|---|---|---|---|
| Primary F | NC_000003 (chr3) | 0.61 | 17/17 (100%, partial — 17 of 20nt) |
| Primary R | NC_000005 (chr5) | 0.61 | 17/17 (100%, partial) |
| Primary Probe | NC_000005 (chr5) | 0.12 | 19/19 (100%, partial — 19 of 27nt) |
| Reserve F | NC_000012 (chr12) | 2.4 | 16/16 (100%, partial) |
| Reserve R | NC_000003 (chr3) | 9.6 | 15/15 (100%, partial) |
| Reserve Probe | NC_000014 (chr14) | 19.1 | 18/19 (94.7%, partial) |

**Pair-level check (D20):** anchored on hits with E<2 per oligo (Primary Probe alone has 80 such hits,
scattered across nearly every chromosome at 17-19/27nt partial length; Primary F/R have 1-2 each; Reserve
oligos have none below E=2 at all). Checked every same-accession pair between different roles of the same
set within 500bp — **none found for either set.** No primer pair on the human genome can complete an
amplicon. Clean.

## core_nt (excl. *C. trachomatis*)

**Finding: both sets match several published Chlamydia-genetics laboratory shuttle/cloning vectors at
100% identity, full length, in the correct F→Probe→R order and spacing** — this is expected and not a
specificity concern, explained below, not glossed over.

| Vector accession | Vector name | Sets matching (full-length, 100% identity) |
|---|---|---|
| KF790907 | Cloning vector pBOMB4-MCI | Primary + Reserve |
| KF790906 | Cloning vector pBOMB4 | Primary + Reserve |
| KF790908 | Cloning vector pBOMB4R | Primary + Reserve |
| KF790909 | Cloning vector pBOMB4R-MCI | Primary + Reserve |
| KF790910 | Cloning vector pBOMB4-Tet-mCherry | Primary + Reserve |
| KF724860 | Transformation vector pGFPBSDZ-SW2 | Primary + Reserve |
| MT241513 | Cloning vector pREF100 | Primary + Reserve |

Example (Primary set on KF790907): F at 4938-4957 (Plus), Probe at 4982-5008 (Plus), R at 5023-5042 (Minus)
— a clean, correctly-ordered, correctly-spaced 105bp amplicon. Reserve set on the same accession: F at
1409-1428, Probe at 1471-1494, R at 1500-1519 — a clean 111bp amplicon.

**Why this isn't a red flag:** the "pBOMB" vector series and pGFPBSDZ-SW2 are real, published *C.
trachomatis* genetic-transformation tools (Bauler & Hackstadt 2014, *J Bacteriology*, "Expression and
Targeting of Secreted Proteins from *Chlamydia trachomatis*"; Wang et al. 2011, *PLOS Pathogens*,
"Development of a Transformation System for *Chlamydia trachomatis*") — shuttle plasmids built by cloning a
large fragment of the *native C. trachomatis cryptic plasmid* into a vector backbone, specifically so the
construct can replicate inside *Chlamydia*. A full-length match here means our consensus-derived design
windows sit on genuine native plasmid sequence that these labs independently cloned — if anything, a
reassuring cross-check on the consensus, not a specificity problem. None of these vectors would ever be
present in a clinical sample, so this creates no diagnostic risk. (The `NOT(txid813[ORGN])` filter didn't
exclude them because a lab construct is catalogued under a synthetic/vector taxonomy, not under *C.
trachomatis*'s own taxid — worth knowing for future BLAST runs on this target, but not something to design
around.)

**Other organisms:** *C. muridarum* — the Primary probe alone has a weak partial hit (X78726 / AE002162,
E=17.6, 25/27nt, 92.6% identity); Primary F and R have **zero** hits to *C. muridarum* anywhere in the
returned results, so no completing pair exists (D20 clears this, same logic as the aroB/*C. suis* finding
in the chromosomal redesign). No other species anywhere in either hit list shows a full-length or
near-full-length match — the remaining ~600 distinct organism names across both hit lists are the expected
background noise of an Expect=1000 search against the entire nucleotide database.

## Conclusion

Both plasmid sets pass D18/D20 cleanly. Combined with the D6 Tm gap, D19 real-computed Tm, and D21
zero-structural-flag results already reported (`PLASMID_PRIMARY_RESERVE_DESIGN.md`), **Primary and Reserve
are ready to lock in as the plasmid target**, on the same end-to-end standard as the chromosomal panel.

Sources:
- [Expression and Targeting of Secreted Proteins from Chlamydia trachomatis (PMC3993338)](https://pmc.ncbi.nlm.nih.gov/articles/PMC3993338/)
- [Development of a Transformation System for Chlamydia trachomatis (PLOS Pathogens)](https://journals.plos.org/plospathogens/article?id=10.1371%2Fjournal.ppat.1002258)
