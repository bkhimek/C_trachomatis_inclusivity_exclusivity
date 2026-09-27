# Plasmid target — Primary and Reserve oligo design (2026-09-27)

**Status: primer3-designed and QC'd (D6/D19/D21 all clean). Not yet BLAST-validated (D18) — that's the next step, same manual web-BLAST process as every chromosomal set.**

## Where these came from

Real 27-primary-tier-genome consensus (`results/plasmid/consensus/consensus_plasmid_standard.fasta`, bin/14), built from actually-downloaded RefSeq plasmid contigs — not from the plasmid handover's unverified V1 sequences, and not from its claimed-but-nonexistent 128-genome curation. Two independent, fully N-free windows were used (bin/16): the two longest conserved stretches in the consensus, named Primary and Reserve to match this project's existing naming convention (not the same sequences as the handover's V1 Primary/Reserve, which remain unverified).

Primer3 design used the **same settings as the chromosomal panel** (`config/primer3_settings.txt`, D6/D7) — not the plasmid handover's proposed higher-Tm probe target, whose stated justification (plasmid supposedly ~50% GC vs ~43% chromosomal) was checked against the real consensus (bin/15) and found false: actual plasmid GC is 35.4%, *lower* than chromosomal, not higher.

## A ranking bug caught and fixed before locking these in

The first design pass ranked candidates by Tm-gap and probe length only (matching the original chromosomal D12 rule), and only computed the full D21 dimer check on the resulting top pick — same order of operations used for the chromosomal panel. Doing that here would have picked a candidate with a flagged MEDIUM-severity primer hairpin over an equally-viable, fully clean alternative one row down in primer3's own output, in both windows. The script was corrected to compute D21 for every D6/D12 survivor and rank on structural cleanliness first, then probe length, then Tm-gap — the picks below reflect that corrected ranking, verified against the actual candidate data.

## Primary set (consensus position 4,860–5,277 window)

| Oligo | Sequence (5'→3') | Length | Tm | GC% |
|---|---|---|---|---|
| Forward primer | CTACCATCCCATTTTGAGCC | 20 nt | 60.11°C | 50.0% |
| Reverse primer | GCCACTTCATCAAAAGTCCT | 20 nt | 59.89°C | 45.0% |
| Probe | TGACCAGGTCTTCTTCCAAACTTCTGA | 27 nt | 67.39°C | 44.4% |

Tm gap (probe − higher primer Tm): **7.28°C** (preferred, ≥7°C — D6). Product size within the 418bp window.

D21 three-way dimer check — **fully clean, 0 flags**:
- F: hairpin 0.0°C (NONE), homodimer −54.9°C (NONE)
- R: hairpin 37.4°C (LOW), homodimer −52.9°C (NONE)
- Probe: hairpin 33.1°C (LOW), homodimer 20.8°C (LOW)
- F–R heterodimer: −2.9°C (NONE)
- F–Probe heterodimer: −36.3°C (NONE)
- R–Probe heterodimer: −32.1°C (NONE)

## Reserve set (consensus position 1,315–1,612 window — independent locus)

| Oligo | Sequence (5'→3') | Length | Tm | GC% |
|---|---|---|---|---|
| Forward primer | GATGAGTTCGACATTCCACA | 20 nt | 59.40°C | 45.0% |
| Reverse primer | AGAGTTTCAATCGATCCCCT | 20 nt | 59.96°C | 45.0% |
| Probe | TCTAGCGGCCAAAATATATGCGGA | 24 nt | 66.04°C | 45.8% |

Tm gap (probe − higher primer Tm): **6.08°C** (meets the 5°C floor; below the 7°C preferred, but with zero structural flags — see below). Product size within the 298bp window.

D21 three-way dimer check — **fully clean, 0 flags**:
- F: hairpin 0.0°C (NONE), homodimer −42.8°C (NONE)
- R: hairpin 0.0°C (NONE), homodimer −5.7°C (NONE)
- Probe: hairpin 0.0°C (NONE), homodimer 2.2°C (LOW)
- F–R heterodimer: −35.6°C (NONE)
- F–Probe heterodimer: −40.8°C (NONE)
- R–Probe heterodimer: −40.8°C (NONE)

## What's still open

1. **D18 web BLAST** (Expect=1000, word_size=7, filter off, human genome + core_nt excl. txid813) — not yet run on these 6 oligos. Needs the user's manual web BLAST, same process as every chromosomal set.
2. **nvCT-specific design** — parked per D23 (user-approved 2026-09-27): the chromosomal panel already detects nvCT-positive samples regardless of the plasmid target, and the nvCT-specific numbers in the plasmid handover (deletion coordinates, accessions) were not independently verifiable in this session.
3. Real master-mix Mg²⁺/dNTP/oligo concentrations are still placeholders (same open item as the chromosomal panel) — every Tm/gap number here will shift slightly once real values are supplied.
4. The 3 genomes bin/13 excluded from the alignment (rotation/orientation low-confidence) were not used anywhere in this design and were not tested for inclusivity against it; not blocking, but worth a note if the panel is later audited for completeness.
