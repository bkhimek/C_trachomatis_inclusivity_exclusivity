#!/usr/bin/env python3
"""
bin/17_design_plasmid_primers.py

Primer3 design for the plasmid target, on the two longest N-free windows found
by bin/16 (rank 1 = "Primary", rank 2 = "Reserve" -- independent loci, same
naming convention as the plasmid handover's V1 sets, but these are freshly
designed from the real consensus, not the handover's unverified V1 sequences).

Deliberately uses the SAME primer3 settings already established for the
chromosomal panel (config/primer3_settings.txt, D6/D7), not the plasmid
handover's proposed plasmid-specific parameter set -- its stated reason for a
higher probe Tm target (plasmid supposedly ~50% GC vs ~43% chromosomal) was
checked against the real consensus in bin/15 and found false (actual GC:
35.4%, lower than chromosomal, not higher), so there is no basis to deviate.

Applies the project's standing QC rules directly on primer3's own computed
values (never on the settings file's target values, D19):
  - D6: reject if PRIMER_INTERNAL_TM - max(PRIMER_LEFT_TM, PRIMER_RIGHT_TM) < 5C
        (hard floor); prefer >=7C.
  - D12: reject if the probe's 5' base is G.
  - D21: for EVERY D6/D12 survivor (not just a provisionally Tm-ranked one --
    an earlier version of this script ranked on Tm-gap/probe-length alone and
    only computed D21 for the resulting top pick, which on the real data
    turned out to silently prefer a candidate with a flagged MEDIUM hairpin
    over an equally-good, fully-clean alternative one row down; see
    PROJECT_STATE.md), compute each oligo's own hairpin/homodimer plus all
    three heterodimers (F-R, F-Probe, R-Probe) via primer3-py's
    calc_hairpin/calc_homodimer/calc_heterodimer, classified by the
    structure's own Tm (NONE <0C, LOW 0-40C, MEDIUM 40-55C, HIGH >=55C).
  - Rank survivors by: fewest MEDIUM/HIGH structural flags first, then shorter
    probe, then larger Tm gap. Structure is checked before the Tm-gap/length
    tiebreak, not after, so a clean set with a smaller (but floor-passing) gap
    or a slightly longer probe still outranks a flagged one.

This design step does NOT include D18 web BLAST validation -- that still needs
the user's manual web BLAST (same as every chromosomal set), reported back the
same way.

Input:  results/plasmid/consensus/consensus_plasmid_standard.fasta (bin/14 output)
        config/primer3_settings.txt (existing project settings; falls back to
        the documented D6/D7/D10 defaults for any key not found in that file,
        and says so)
Output: printed report per window: every returned candidate's Tm/GC/gap, which
        passed/failed the D6/D12 filter, the top pick, and its full D21 dimer
        table. No files written -- this is a design/QC report, not yet a
        locked set (that's a decision for after D18 BLAST, same as the
        chromosomal panel).

Run from the repo root:
    python bin/17_design_plasmid_primers.py
"""
import re
from pathlib import Path

import primer3
from Bio import SeqIO

REPO = Path(__file__).resolve().parents[1]
CONSENSUS = REPO / "results" / "plasmid" / "consensus" / "consensus_plasmid_standard.fasta"
SETTINGS_FILE = REPO / "config" / "primer3_settings.txt"

# (label, 1-based inclusive start, end) -- rank 1 and rank 2 from bin/16's output
TARGET_WINDOWS = [
    ("Primary", 4860, 5277),
    ("Reserve", 1315, 1612),
]

TM_GAP_FLOOR = 5.0
TM_GAP_PREFERRED = 7.0
PRIMER_NUM_RETURN = 5

# D6/D7/D10-documented defaults, used only for any key SETTINGS_FILE doesn't provide
DEFAULT_GLOBALS = {
    "PRIMER_OPT_SIZE": 20,
    "PRIMER_MIN_SIZE": 18,
    "PRIMER_MAX_SIZE": 25,
    "PRIMER_OPT_TM": 60.0,
    "PRIMER_MIN_TM": 59.0,
    "PRIMER_MAX_TM": 61.0,
    "PRIMER_INTERNAL_OPT_SIZE": 22,
    "PRIMER_INTERNAL_MIN_SIZE": 20,
    "PRIMER_INTERNAL_MAX_SIZE": 36,  # primer3 2.6.1 hard cap, D10
    "PRIMER_INTERNAL_OPT_TM": 68.0,
    "PRIMER_INTERNAL_MIN_TM": 66.0,
    "PRIMER_INTERNAL_MAX_TM": 72.0,
    "PRIMER_INTERNAL_WT_SIZE_GT": 1.0,
    "PRIMER_PICK_INTERNAL_OLIGO": 1,
    "PRIMER_NUM_RETURN": PRIMER_NUM_RETURN,
}


def load_settings():
    """Parse config/primer3_settings.txt (KEY=VALUE per line). Returns
    (settings dict, list of keys that came from DEFAULT_GLOBALS instead)."""
    settings = dict(DEFAULT_GLOBALS)
    used_default = set(DEFAULT_GLOBALS.keys())
    if SETTINGS_FILE.exists():
        with open(SETTINGS_FILE) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key, val = key.strip(), val.strip()
                if key in used_default:
                    used_default.discard(key)
                for cast in (int, float):
                    try:
                        val = cast(val)
                        break
                    except ValueError:
                        continue
                settings[key] = val
    else:
        print(f"NOTE: {SETTINGS_FILE} not found -- using documented D6/D7/D10 defaults for everything.\n")
    return settings, used_default


def classify(tm):
    if tm < 0:
        return "NONE"
    if tm < 40:
        return "LOW"
    if tm < 55:
        return "MEDIUM"
    return "HIGH"


def run_design(seq_window, args, n_return):
    args = dict(args)
    args["PRIMER_NUM_RETURN"] = n_return
    seq_args = {"SEQUENCE_ID": "plasmid_window", "SEQUENCE_TEMPLATE": seq_window}
    return primer3.bindings.design_primers(seq_args, args)


def evaluate_candidates(result, n_returned):
    """Returns (printed_lines, survivors) -- survivors is a list of tuples."""
    lines, survivors = [], []
    for i in range(n_returned):
        try:
            l_seq = result[f"PRIMER_LEFT_{i}_SEQUENCE"]
            r_seq = result[f"PRIMER_RIGHT_{i}_SEQUENCE"]
            p_seq = result[f"PRIMER_INTERNAL_{i}_SEQUENCE"]
            l_tm = result[f"PRIMER_LEFT_{i}_TM"]
            r_tm = result[f"PRIMER_RIGHT_{i}_TM"]
            p_tm = result[f"PRIMER_INTERNAL_{i}_TM"]
        except KeyError:
            continue
        gap = p_tm - max(l_tm, r_tm)
        reject_reasons = []
        if gap < TM_GAP_FLOOR:
            reject_reasons.append(f"Tm gap {gap:.2f}C < {TM_GAP_FLOOR}C floor (D6)")
        if p_seq[0].upper() == "G":
            reject_reasons.append("probe 5' base is G (D12)")
        status = "REJECT: " + "; ".join(reject_reasons) if reject_reasons else "pass"
        lines.append(
            f"  candidate {i}: F={l_seq} (Tm {l_tm:.2f}) R={r_seq} (Tm {r_tm:.2f}) "
            f"Probe={p_seq} (Tm {p_tm:.2f}, {len(p_seq)}nt) gap={gap:.2f}C -> {status}"
        )
        if not reject_reasons:
            survivors.append((i, l_seq, r_seq, p_seq, l_tm, r_tm, p_tm, gap, len(p_seq)))
    return lines, survivors


def d21_check(l_seq, r_seq, p_seq):
    """Full three-way D21 check. Returns (flag_count, lines) -- flag_count is
    how many of the 6 structures (3 own + 3 heterodimer) are MEDIUM or HIGH."""
    lines = []
    flag_count = 0
    for name, s in (("F", l_seq), ("R", r_seq), ("Probe", p_seq)):
        hp = primer3.calc_hairpin(s).tm
        hd = primer3.calc_homodimer(s).tm
        for tm in (hp, hd):
            if classify(tm) in ("MEDIUM", "HIGH"):
                flag_count += 1
        lines.append(f"      {name} own hairpin={hp:.1f}C ({classify(hp)})  homodimer={hd:.1f}C ({classify(hd)})")
    for name_a, seq_a, name_b, seq_b in (
        ("F", l_seq, "R", r_seq),
        ("F", l_seq, "Probe", p_seq),
        ("R", r_seq, "Probe", p_seq),
    ):
        het = primer3.calc_heterodimer(seq_a, seq_b).tm
        if classify(het) in ("MEDIUM", "HIGH"):
            flag_count += 1
        lines.append(f"      {name_a}-{name_b} heterodimer={het:.1f}C ({classify(het)})")
    return flag_count, lines


def design_window(label, start1, end1, seq, global_args):
    seq_window = seq[start1 - 1 : end1]
    window_len = len(seq_window)
    max_product = max(100, window_len - 10)
    args = dict(global_args)
    args["PRIMER_PRODUCT_SIZE_RANGE"] = [[min(100, max_product), max_product]]

    result = run_design(seq_window, args, PRIMER_NUM_RETURN)
    n_returned = result.get("PRIMER_PAIR_NUM_RETURNED", 0)
    print(f"=== {label}: consensus {start1}-{end1} ({window_len}bp), {n_returned} candidate(s) returned ===")
    lines, survivors = evaluate_candidates(result, n_returned)
    for line in lines:
        print(line)

    if not survivors and n_returned >= PRIMER_NUM_RETURN:
        retry_n = 30
        print(f"  0 survivors out of {n_returned} -- retrying with PRIMER_NUM_RETURN={retry_n} before giving up.")
        result = run_design(seq_window, args, retry_n)
        n_returned = result.get("PRIMER_PAIR_NUM_RETURNED", 0)
        lines, survivors = evaluate_candidates(result, n_returned)
        print(f"  Retry: {n_returned} candidate(s) returned, {len(survivors)} survived.")

    if not survivors:
        print("  No candidates survived the D6/D12 filter for this window even after retry.\n")
        return

    # D21 for every survivor -- dedupe identical (F,R,Probe) triples first, primer3
    # often returns the same oligo combo multiple times with different rankings.
    seen = {}
    for s in survivors:
        idx, l_seq, r_seq, p_seq, l_tm, r_tm, p_tm, gap, plen = s
        key = (l_seq, r_seq, p_seq)
        if key not in seen:
            seen[key] = s
    unique_survivors = list(seen.values())

    print(f"  D21 three-way dimer check, all {len(unique_survivors)} unique surviving combination(s):")
    scored = []
    for s in unique_survivors:
        idx, l_seq, r_seq, p_seq, l_tm, r_tm, p_tm, gap, plen = s
        flag_count, d21_lines = d21_check(l_seq, r_seq, p_seq)
        print(f"    candidate {idx}: gap={gap:.2f}C probe={plen}nt flags={flag_count}")
        for line in d21_lines:
            print(line)
        scored.append((flag_count, plen, -gap, s))

    scored.sort(key=lambda t: (t[0], t[1], t[2]))
    flag_count, plen, neg_gap, pick = scored[0]
    idx, l_seq, r_seq, p_seq, l_tm, r_tm, p_tm, gap, plen = pick
    pref = "preferred (>=7C)" if gap >= TM_GAP_PREFERRED else "meets 5C floor only"
    print(
        f"\n  TOP PICK (candidate {idx}): {flag_count} structural flag(s), gap {gap:.2f}C ({pref}), "
        f"probe {plen}nt"
    )
    print(f"    F:     {l_seq}  Tm={l_tm:.2f}  len={len(l_seq)}")
    print(f"    R:     {r_seq}  Tm={r_tm:.2f}  len={len(r_seq)}")
    print(f"    Probe: {p_seq}  Tm={p_tm:.2f}  len={plen}")
    if len(scored) > 1:
        runner = scored[1]
        print(
            f"  (next-best: candidate {runner[3][0]}, {runner[0]} structural flag(s), "
            f"gap {-runner[2]:.2f}C, probe {runner[1]}nt -- see the D21 lines above for why it ranked lower.)"
        )
    print()


def main():
    rec = next(SeqIO.parse(CONSENSUS, "fasta"))
    seq = str(rec.seq).upper()

    settings, used_default = load_settings()
    if used_default:
        print(f"Using documented defaults (not found in {SETTINGS_FILE}) for: {sorted(used_default)}\n")

    for label, start1, end1 in TARGET_WINDOWS:
        design_window(label, start1, end1, seq, settings)


if __name__ == "__main__":
    main()
