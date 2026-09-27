#!/usr/bin/env python3
"""
bin/16_find_conserved_windows.py

Find candidate windows for plasmid primer3 design: maximal N-free runs in the
bin/14 consensus (results/plasmid/consensus/consensus_plasmid_standard.fasta),
ranked by length. With only 124 N's out of 7,500bp (1.65%, see bin/14/bin/15),
there should be several long clean stretches -- this finds and ranks them
rather than assuming.

Also reports, for context only (nvCT design is parked per D23, not being
designed for right now): whether the plasmid handover's claimed nvCT-deletion
window (2365-2560, unverified -- see PROJECT_STATE.md) is itself N-masked in
this consensus.

Input:  results/plasmid/consensus/consensus_plasmid_standard.fasta (bin/14 output)
Output: printed ranked list of N-free windows (start, end, length), 1-based
        inclusive coordinates on the consensus.

Run from the repo root:
    python bin/16_find_conserved_windows.py
"""
import re
from pathlib import Path

from Bio import SeqIO

REPO = Path(__file__).resolve().parents[1]
CONSENSUS = REPO / "results" / "plasmid" / "consensus" / "consensus_plasmid_standard.fasta"

MIN_WINDOW_LEN = 150  # need roughly primer + probe + primer, plus margin
HANDOVER_CLAIMED_WINDOW = (2365, 2560)  # unverified, context only -- see PROJECT_STATE.md


def find_runs(seq):
    """Maximal runs with no 'N', as 0-based [start, end) half-open tuples."""
    return [(m.start(), m.end()) for m in re.finditer(r"[^N]+", seq)]


def main():
    rec = next(SeqIO.parse(CONSENSUS, "fasta"))
    seq = str(rec.seq).upper()
    print(f"Consensus: {len(seq)}bp, N count: {seq.count('N')}\n")

    runs = find_runs(seq)
    runs_sorted = sorted(runs, key=lambda r: r[1] - r[0], reverse=True)
    n_at_or_above = sum(1 for r in runs if r[1] - r[0] >= MIN_WINDOW_LEN)

    print(f"{len(runs)} N-free runs total; {n_at_or_above} at or above {MIN_WINDOW_LEN}bp\n")
    print(f"{'rank':<6}{'start(1-based)':<16}{'end(1-based)':<14}{'length'}")
    for i, (s, e) in enumerate(runs_sorted[:15], start=1):
        print(f"{i:<6}{s + 1:<16}{e:<14}{e - s}")

    lo, hi = HANDOVER_CLAIMED_WINDOW
    lo0, hi0 = lo - 1, hi
    window_slice = seq[lo0:hi0]
    n_in_window = window_slice.count("N")
    print(
        f"\nContext only (nvCT design parked, D23): the handover's claimed nvCT-deletion window "
        f"{lo}-{hi} (unverified coordinates) contains {n_in_window} N-masked base(s) in this consensus "
        f"out of {len(window_slice)}bp."
    )


if __name__ == "__main__":
    main()
