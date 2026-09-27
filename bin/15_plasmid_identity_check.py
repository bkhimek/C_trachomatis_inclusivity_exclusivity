#!/usr/bin/env python3
"""
bin/15_plasmid_identity_check.py

QC gate (D13): test every non-primary genome in the bin/13 alignment (currently
the 4 quality-review genomes) against the consensus bin/14 just built, reporting
percent identity over the comparable positions. Also reports the consensus GC%
(checking it against the plasmid handover's claim of "~50% vs 43% chromosomal" --
untested until now), and, as a free side-check using data already in hand, the
longest run of consecutive gaps each genome carries at positions the consensus
keeps. A real deletion in a genome would show up as a long gap run there --
C. trachomatis's own documented plasmid deletion, nvCT, is reported as ~377bp,
but nvCT design is parked per D23, so this is reported only as a side
observation, not chased further here.

Reuses the exact same column-selection logic as bin/14 (majority-gap columns
dropped, primary-tier consensus with a 99% conservation threshold) and asserts
its output matches the actual consensus file byte-for-byte in length, so this
never silently reports against a stale consensus.

Input:  results/plasmid/alignments/plasmids_34_rotated_aligned.fasta (31 seqs, bin/13)
        results/plasmid/consensus/consensus_plasmid_standard.fasta (bin/14 output)
        data/genome_inventory/genome_inventory_final.tsv (tier)
Output: printed summary only (no files) -- consensus GC%/length, then a table of
        every genome in the alignment (primary genomes as a self-check, plus the
        quality-review genomes that matter for D13): tier, positions compared,
        percent identity to consensus, longest gap run.

Run from the repo root:
    python bin/15_plasmid_identity_check.py
"""
import csv
from collections import Counter
from pathlib import Path

from Bio import AlignIO, SeqIO

REPO = Path(__file__).resolve().parents[1]
ALIGNMENT = REPO / "results" / "plasmid" / "alignments" / "plasmids_34_rotated_aligned.fasta"
CONSENSUS = REPO / "results" / "plasmid" / "consensus" / "consensus_plasmid_standard.fasta"
FINAL_TSV = REPO / "data" / "genome_inventory" / "genome_inventory_final.tsv"

CONSERVATION_THRESHOLD = 0.99
GAP_MAJORITY_THRESHOLD = 0.5
GAP_RUN_FLAG = 200  # bp; nvCT's documented deletion is ~377bp -- flag well below that


def load_tier():
    tier = {}
    with open(FINAL_TSV) as f:
        for row in csv.DictReader(f, delimiter="\t"):
            tier[row["accession"]] = row.get("tier", "")
    return tier


def main():
    tier = load_tier()
    aln = AlignIO.read(ALIGNMENT, "fasta")
    aln_len = aln.get_alignment_length()

    primary_seqs, all_seqs = {}, {}
    for rec in aln:
        acc = rec.id.replace("_plasmid", "")
        s = str(rec.seq).upper()
        all_seqs[acc] = s
        if tier.get(acc) == "primary":
            primary_seqs[acc] = s
    n_primary = len(primary_seqs)

    kept_columns = []  # (col_idx, consensus_base_or_N), same rule as bin/14
    for col_idx in range(aln_len):
        col = [s[col_idx] for s in primary_seqs.values()]
        gap_count = col.count("-")
        if gap_count / n_primary > GAP_MAJORITY_THRESHOLD:
            continue
        non_gap = [b for b in col if b != "-"]
        counts = Counter(non_gap)
        majority_base, majority_count = counts.most_common(1)[0]
        fraction = majority_count / len(non_gap) if non_gap else 0
        cbase = majority_base if fraction >= CONSERVATION_THRESHOLD else "N"
        kept_columns.append((col_idx, cbase))

    consensus_seq = str(next(SeqIO.parse(CONSENSUS, "fasta")).seq).upper()
    assert len(consensus_seq) == len(kept_columns), (
        "consensus length mismatch vs. recomputed columns -- bin/14 output may be stale relative to "
        "the alignment file; rebuild it (python bin/14_build_plasmid_consensus.py) before trusting this"
    )
    gc = sum(consensus_seq.count(b) for b in "GC") / len(consensus_seq) * 100
    print(f"Consensus: {len(consensus_seq)}bp, GC={gc:.1f}%, N={consensus_seq.count('N')}\n")

    print(f"{'accession':<18}{'tier':<16}{'n_compared':<12}{'pct_identity':<14}{'longest_gap_run'}")
    for acc, seq in all_seqs.items():
        t = tier.get(acc, "?")
        matches = compared = gap_run = max_gap_run = 0
        for col_idx, cbase in kept_columns:
            b = seq[col_idx]
            if b == "-":
                gap_run += 1
                max_gap_run = max(max_gap_run, gap_run)
                continue
            gap_run = 0
            if cbase == "N":
                continue
            compared += 1
            if b == cbase:
                matches += 1
        pct = (matches / compared * 100) if compared else 0.0
        flag = "  <-- FLAG (>=200bp gap run)" if max_gap_run >= GAP_RUN_FLAG else ""
        print(f"{acc:<18}{t:<16}{compared:<12}{pct:<14.2f}{max_gap_run}{flag}")


if __name__ == "__main__":
    main()
