#!/usr/bin/env python3
"""
bin/14_build_plasmid_consensus.py

Build a majority-rule consensus of the C. trachomatis plasmid from the
rotation-corrected 31-genome alignment (bin/13 output), using ONLY primary-tier
genomes (D13: primary genomes build the consensus and carry the inclusivity
claim; quality-review genomes are tested against the finished consensus
afterward, never used to build it). This mirrors the methodology bin/09 used
for the chromosomal consensus regions: majority base per column, masked 'N'
below a 99% conservation threshold.

Of the 31 rotation-corrected genomes (bin/13), 27 are primary tier. (Of the
original 29 primary genomes, bin/13 excluded GCF_001655455.1 and
GCF_001655575.1 as low-confidence rotations -- both already independently
flagged auto_verdict=REVIEW in the original chromosomal QC. The 34th, a third
bin/13 exclusion, GCF_001183825.1, was quality-review tier and was never going
into the consensus anyway.) The 4 remaining quality-review genomes are held out
here and should be tested against the finished consensus in the next step, not
used to build it.

Column rule: a column where a MAJORITY of the 27 primary sequences carry a gap
is dropped entirely from the consensus -- it's an insertion carried by a
minority of genomes, not part of the conserved plasmid backbone. For every
remaining column, the majority base among the primary sequences that are NOT
gapped there is kept if it reaches >=99% agreement; otherwise the position is
masked 'N' and logged to the variability report.

Input:  results/plasmid/alignments/plasmids_34_rotated_aligned.fasta (31 seqs, bin/13 output)
        data/genome_inventory/genome_inventory_final.tsv (tier lookup)
Output: results/plasmid/consensus/consensus_plasmid_standard.fasta
        results/plasmid/consensus/consensus_plasmid_variability.tsv (one row per masked/variable position)
        printed summary

Run from the repo root:
    python bin/14_build_plasmid_consensus.py
"""
import csv
from collections import Counter
from pathlib import Path

from Bio import AlignIO

REPO = Path(__file__).resolve().parents[1]
ALIGNMENT = REPO / "results" / "plasmid" / "alignments" / "plasmids_34_rotated_aligned.fasta"
FINAL_TSV = REPO / "data" / "genome_inventory" / "genome_inventory_final.tsv"
OUT_DIR = REPO / "results" / "plasmid" / "consensus"

CONSERVATION_THRESHOLD = 0.99
GAP_MAJORITY_THRESHOLD = 0.5


def load_tier():
    tier = {}
    with open(FINAL_TSV) as f:
        for row in csv.DictReader(f, delimiter="\t"):
            tier[row["accession"]] = row.get("tier", "")
    return tier


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tier = load_tier()

    aln = AlignIO.read(ALIGNMENT, "fasta")
    primary_records = []
    for rec in aln:
        acc = rec.id.replace("_plasmid", "")
        if tier.get(acc) == "primary":
            primary_records.append((acc, str(rec.seq).upper()))

    n_primary = len(primary_records)
    aln_len = aln.get_alignment_length()
    print(f"Alignment: {len(aln)} sequences total, {aln_len} columns")
    print(f"Primary-tier sequences used for consensus: {n_primary}")
    if n_primary == 0:
        raise SystemExit("No primary-tier sequences found in the alignment -- check tier lookup / accession match")

    consensus_bases = []
    variability_rows = []
    dropped_gap_majority = 0
    n_masked = 0
    n_conserved_100 = 0
    n_conserved_99 = 0

    for col_idx in range(aln_len):
        col = [seq[col_idx] for _, seq in primary_records]
        gap_count = col.count("-")
        if gap_count / n_primary > GAP_MAJORITY_THRESHOLD:
            dropped_gap_majority += 1
            continue

        non_gap = [b for b in col if b != "-"]
        counts = Counter(non_gap)
        majority_base, majority_count = counts.most_common(1)[0]
        fraction = majority_count / len(non_gap) if non_gap else 0

        if fraction >= 1.0:
            n_conserved_100 += 1
            consensus_bases.append(majority_base)
        elif fraction >= CONSERVATION_THRESHOLD:
            n_conserved_99 += 1
            consensus_bases.append(majority_base)
        else:
            n_masked += 1
            consensus_bases.append("N")
            variant_accs = [acc for (acc, _), b in zip(primary_records, col) if b != majority_base]
            variability_rows.append(
                {
                    "alignment_column": col_idx,
                    "consensus_position": len(consensus_bases),
                    "majority_base": majority_base,
                    "majority_fraction": round(fraction, 4),
                    "n_non_gap": len(non_gap),
                    "n_gap": gap_count,
                    "variant_accessions": ";".join(variant_accs),
                }
            )

    consensus_seq = "".join(consensus_bases)

    with open(OUT_DIR / "consensus_plasmid_standard.fasta", "w") as f:
        f.write(f">consensus_plasmid_standard {n_primary}_primary_genomes_{len(consensus_seq)}bp\n")
        for i in range(0, len(consensus_seq), 70):
            f.write(consensus_seq[i:i + 70] + "\n")

    with open(OUT_DIR / "consensus_plasmid_variability.tsv", "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "alignment_column", "consensus_position", "majority_base",
                "majority_fraction", "n_non_gap", "n_gap", "variant_accessions",
            ],
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(variability_rows)

    print(f"\nColumns dropped (majority-gap, insertion carried by <50% of genomes): {dropped_gap_majority}")
    print(f"Columns kept: {aln_len - dropped_gap_majority}")
    print(f"  100% conserved: {n_conserved_100}")
    print(f"  >=99% conserved (majority kept): {n_conserved_99}")
    print(f"  <99% conserved (masked N): {n_masked}")
    print(f"\nConsensus length: {len(consensus_seq)}bp, N count: {consensus_seq.count('N')}")
    print(f"Written -> {OUT_DIR / 'consensus_plasmid_standard.fasta'}")
    print(f"Variability report ({len(variability_rows)} rows) -> {OUT_DIR / 'consensus_plasmid_variability.tsv'}")


if __name__ == "__main__":
    main()
