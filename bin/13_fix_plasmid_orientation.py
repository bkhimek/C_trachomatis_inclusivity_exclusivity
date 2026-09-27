#!/usr/bin/env python3
"""
bin/13_fix_plasmid_orientation.py

Diagnose and fix circular-rotation / strand-orientation mismatches among the 34
extracted plasmid contigs (bin/12 output) before building a consensus.

Why this is needed: the 34 raw plasmid contigs are tightly length-matched
(7,415-7,510 bp -- see PROJECT_STATE.md, 2026-09-27). A `mafft --auto` alignment
of them should therefore come out close to that length too. Instead it came out
at 13,075 bp -- nearly double. For a molecule this conserved within one species,
that kind of blowup is the signature of a circular-sequence artifact, not real
biological divergence: RefSeq records a circular plasmid linearly starting at an
arbitrary position, so different submissions can start at different points around
the circle (rotation) and/or be deposited on opposite strands (reverse-complement)
relative to each other. MAFFT has no concept of circularity and will insert one
huge gap block to paper over a rotation offset instead of recognizing the two
sequences are the same molecule read from a different start point.

Method: pick a reference genome, extract several short anchor probes spaced
through it, and for every other genome search for each probe on both strands.
A consistent hit (same offset from most/all probes) on the forward strand at
position p>0 means "same strand, rotated by p bp" -- fix: rotate so that offset
becomes 0. A consistent hit on the reverse-complement strand means "opposite
strand" -- fix: reverse-complement first, then rotate.

Input:  data/plasmids_downloaded/<accession>_plasmid.fna  (the 34 files from bin/12)
Output: data/plasmids_downloaded/plasmids_34_rotated/<accession>_plasmid_rotated.fna
        data/plasmids_downloaded/plasmids_34_rotated_combined.fasta
        Printed summary: accession, action taken, confidence (probes agreeing / probes tried)

Run from the repo root:
    python bin/13_fix_plasmid_orientation.py
Then re-run the MAFFT alignment on plasmids_34_rotated_combined.fasta (same command
as before, new input file) and confirm the alignment length drops back down near
the raw sequence length (~7,400-7,600 bp). If it doesn't, or if any accession is
printed as FLAG or with low confidence (fewer than half the probes agreeing),
stop and report back rather than trusting the rotation -- a wrong rotation would
silently corrupt every downstream position, including the consensus and any oligo
window picked from it.
"""
from collections import Counter
from pathlib import Path

from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

REPO = Path(__file__).resolve().parents[1]
IN_DIR = REPO / "data" / "plasmids_downloaded"
OUT_DIR = IN_DIR / "plasmids_34_rotated"

PROBE_LEN = 40
N_PROBES = 6
REFERENCE_ACCESSION = "GCF_000012125.1"  # A/HAR-13, the C. trachomatis type strain
MIN_CONFIDENCE_FRACTION = 0.5  # flag (don't silently trust) below this


def load_records():
    records = {}
    for fpath in sorted(IN_DIR.glob("*_plasmid.fna")):
        rec = next(SeqIO.parse(fpath, "fasta"))
        acc = fpath.name.replace("_plasmid.fna", "")
        records[acc] = rec
    return records


def make_probes(ref_seq, n=N_PROBES, probe_len=PROBE_LEN):
    length = len(ref_seq)
    step = length // (n + 1)
    return [(i * step, str(ref_seq[i * step : i * step + probe_len])) for i in range(1, n + 1)]


def find_probe(seq_str, probe):
    """Position of probe in seq_str, handling wraparound near the end of a
    circular sequence stored linearly. -1 if not found."""
    doubled = seq_str + seq_str[: len(probe)]
    pos = doubled.find(probe)
    if pos == -1 or pos >= len(seq_str):
        return -1
    return pos


def consensus_offset(offsets):
    if not offsets:
        return None, 0
    best_offset, count = Counter(offsets).most_common(1)[0]
    return best_offset, count


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    records = load_records()
    if REFERENCE_ACCESSION not in records:
        raise SystemExit(f"Reference {REFERENCE_ACCESSION} not found among extracted plasmids in {IN_DIR}")

    ref_seq = str(records[REFERENCE_ACCESSION].seq).upper()
    probes = make_probes(ref_seq)

    print(f"Reference: {REFERENCE_ACCESSION} ({len(ref_seq)}bp), {len(probes)} anchor probes ({PROBE_LEN}bp each)\n")
    print(f"{'accession':<18}{'action':<40}{'confidence'}")

    combined = []
    flagged = []
    for acc, rec in records.items():
        seq_str = str(rec.seq).upper()
        rc_str = str(rec.seq.reverse_complement()).upper()

        fwd_offsets = [
            (find_probe(seq_str, probe) - ref_pos) % len(seq_str)
            for ref_pos, probe in probes
            if find_probe(seq_str, probe) != -1
        ]
        rc_offsets = [
            (find_probe(rc_str, probe) - ref_pos) % len(rc_str)
            for ref_pos, probe in probes
            if find_probe(rc_str, probe) != -1
        ]

        fwd_offset, fwd_conf = consensus_offset(fwd_offsets)
        rc_offset, rc_conf = consensus_offset(rc_offsets)

        if fwd_conf >= rc_conf and fwd_offset is not None:
            use_str, offset, strand, conf = seq_str, fwd_offset, "fwd", fwd_conf
        elif rc_offset is not None:
            use_str, offset, strand, conf = rc_str, rc_offset, "revcomp", rc_conf
        else:
            print(f"{acc:<18}{'FLAG: no probe matched either strand':<40}0/{len(probes)}")
            flagged.append(acc)
            continue

        conf_str = f"{conf}/{len(probes)}"
        if conf < len(probes) * MIN_CONFIDENCE_FRACTION:
            print(f"{acc:<18}{'FLAG: low-confidence ' + strand + f', offset {offset}bp':<40}{conf_str}")
            flagged.append(acc)
            continue

        rotated = use_str[offset:] + use_str[:offset]
        action = "none (already matches reference)" if (strand == "fwd" and offset == 0) else f"{strand}, rotated {offset}bp"
        print(f"{acc:<18}{action:<40}{conf_str}")

        new_rec = SeqRecord(
            Seq(rotated),
            id=f"{acc}_plasmid",
            description=f"{acc} plasmid, {strand}, rotated {offset}bp to match {REFERENCE_ACCESSION} start (confidence {conf_str})",
        )
        SeqIO.write(new_rec, OUT_DIR / f"{acc}_plasmid_rotated.fna", "fasta")
        combined.append(new_rec)

    if combined:
        SeqIO.write(combined, IN_DIR / "plasmids_34_rotated_combined.fasta", "fasta")

    print(f"\nWrote {len(combined)}/{len(records)} rotated/oriented sequences -> {IN_DIR / 'plasmids_34_rotated_combined.fasta'}")
    if flagged:
        print(f"\n{len(flagged)} accession(s) FLAGGED, not included in the combined output -- inspect manually:")
        for acc in flagged:
            print(f"  {acc}")


if __name__ == "__main__":
    main()
