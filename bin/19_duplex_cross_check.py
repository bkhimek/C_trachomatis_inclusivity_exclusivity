#!/usr/bin/env python3
"""bin/19: cross-interactions between a chromosomal set and a plasmid set in the proposed duplex (D29).

Why: D21 checks the three oligos of ONE set (F-R, F-Probe, R-Probe plus each oligo's own hairpin and
homodimer). The proposed final assay (case study, white paper) is a duplex: one chromosomal set run together
with one plasmid set, six oligos in one reaction. Nothing in bin/00-18 compared oligos from different sets,
so the six-oligo case had not been assessed. This script closes that gap computationally.

Input : config/final_chromosomal_oligos.tsv                          21 oligos = the 7 chromosomal sets (D22)
        results/oligos_plasmid/plasmid_primary_reserve_oligos.fasta   6 oligos = Plasmid Primary + Reserve (D25)
Output: results/duplex_check/cross_dimer_all_pairs.tsv   one row per cross pair (14 combinations x 9 pairs)
        results/duplex_check/cross_dimer_by_combo.tsv    one row per chromosomal-set x plasmid-set combination
        results/duplex_check/summary.txt                 verdict per combination and the strongest interactions

Method (same structure and severity scale as D21 / bin/17):
  - every oligo of the chromosomal set is paired with every oligo of the plasmid set (3 x 3 = 9 cross
    heterodimers per combination; the within-set pairs were already covered by D21)
  - structure Tm from primer3-py calc_heterodimer, classified by the structure's own melting Tm:
    NONE <0 C, LOW 0-40 C, MEDIUM 40-55 C, HIGH >=55 C
  - the Tm is computed twice: (a) with primer3-py's default conditions, which is what bin/17 used for the
    D21 checks, so the numbers are directly comparable with the within-set results; (b) with the project's
    reaction conditions from config/primer3_settings.txt (50 mM Na+, 3.0 mM Mg2+, 0.8 mM dNTP, 250 nM oligo)
    as a sensitivity check. A combination passes only if no pair is MEDIUM or HIGH under either.
  - for primer-primer pairs (F or R of one set against F or R of the other) the 3'-end stability of the better
    of the two directions is also reported (calc_end_stability, kcal/mol). Informational only: the project has
    no pass/fail threshold for it, and none is introduced here.
  - positive control: an oligo against its own reverse complement must come out HIGH, otherwise the method
    would be reporting "no interaction" for the wrong reason; the script stops if it does not.

Not covered: BLAST cross-hits between the two targets' oligos and the other target's sequence, dye/quencher and
detection-channel assignment, and real multiplex behaviour (amplification efficiency, competition, LoD). Those
are laboratory questions. A clean result here means no predicted strong oligo-oligo interaction, not a
demonstrated working duplex.

Usage: bin/19_duplex_cross_check.py [--root PATH]
Needs primer3-py (the same package bin/17 uses). Runs in a few seconds.
"""
import argparse
import csv
import itertools
import sys
from pathlib import Path

import primer3

DEFAULT_ROOT = Path(__file__).resolve().parent.parent
CHROM_FILE = "config/final_chromosomal_oligos.tsv"
PLASMID_FILE = "results/oligos_plasmid/plasmid_primary_reserve_oligos.fasta"
OUT_DIR = "results/duplex_check"

# reaction conditions of config/primer3_settings.txt (D6/D7/D19)
PROJECT_CONDITIONS = dict(mv_conc=50.0, dv_conc=3.0, dntp_conc=0.8, dna_conc=250.0)

EXPECTED_CHROM_SETS = 7
EXPECTED_PLASMID_SETS = 2


def classify(tm):
    """Severity from the structure's own melting Tm, as in D21 / bin/17."""
    if tm < 0:
        return "NONE"
    if tm < 40:
        return "LOW"
    if tm < 55:
        return "MEDIUM"
    return "HIGH"


def structure_tm(seq_a, seq_b, **conditions):
    res = primer3.calc_heterodimer(seq_a, seq_b, **conditions)
    return res.tm if res.structure_found else -273.0


def revcomp(seq):
    return seq.translate(str.maketrans("ACGT", "TGCA"))[::-1]


def read_chromosomal(path):
    sets = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            role = {"F": "F", "R": "R", "probe": "P"}[row["role"]]
            sets.setdefault(row["set_id"], {})[role] = (row["name"], row["sequence"].upper())
    return sets


def read_plasmid(path):
    sets = {}
    name = None
    for line in open(path):
        line = line.strip()
        if line.startswith(">"):
            name = line[1:].split()[0]
        elif line and name:
            set_id, role = name.rsplit("_", 1)          # Plasmid_Primary_F -> Plasmid_Primary, F
            role = {"F": "F", "R": "R", "Probe": "P"}[role]
            sets.setdefault(set_id, {})[role] = (name, line.upper())
            name = None
    return sets


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    args = ap.parse_args()
    root = args.root

    chrom = read_chromosomal(root / CHROM_FILE)
    plasmid = read_plasmid(root / PLASMID_FILE)
    for label, sets, n in (("chromosomal", chrom, EXPECTED_CHROM_SETS), ("plasmid", plasmid, EXPECTED_PLASMID_SETS)):
        if len(sets) != n or any(set(s) != {"F", "R", "P"} for s in sets.values()):
            sys.exit(f"ERROR: expected {n} {label} sets with F, R and probe each, found {sorted(sets)}")

    # positive control: a perfect duplex must be reported as a strong interaction
    ctl_seq = chrom[next(iter(chrom))]["F"][1]
    ctl_tm = structure_tm(ctl_seq, revcomp(ctl_seq))
    print(f"positive control (oligo vs its reverse complement): Tm {ctl_tm:.1f} C -> {classify(ctl_tm)}")
    if classify(ctl_tm) != "HIGH":
        sys.exit("ERROR: positive control not HIGH; the method is not detecting interactions, stopping.")

    out_dir = root / OUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    pair_rows, combo_rows = [], []
    for (c_id, c_oligos), (p_id, p_oligos) in itertools.product(chrom.items(), plasmid.items()):
        worst_default = worst_project = None
        flags = 0
        for c_role, p_role in itertools.product("FRP", "FRP"):
            c_name, c_seq = c_oligos[c_role]
            p_name, p_seq = p_oligos[p_role]
            tm_d = structure_tm(c_seq, p_seq)
            tm_p = structure_tm(c_seq, p_seq, **PROJECT_CONDITIONS)
            end_dg = ""
            if c_role != "P" and p_role != "P":
                dg = min(primer3.calc_end_stability(c_seq, p_seq).dg, primer3.calc_end_stability(p_seq, c_seq).dg)
                end_dg = f"{dg / 1000:.2f}"
            row = dict(chromosomal_set=c_id, plasmid_set=p_id, oligo_a=c_name, oligo_b=p_name,
                       roles=f"{c_role}-{p_role}", tm_default_c=f"{tm_d:.1f}", class_default=classify(tm_d),
                       tm_project_c=f"{tm_p:.1f}", class_project=classify(tm_p),
                       primer_end_dg_kcal_mol=end_dg)
            pair_rows.append(row)
            if classify(tm_d) in ("MEDIUM", "HIGH") or classify(tm_p) in ("MEDIUM", "HIGH"):
                flags += 1
            if worst_default is None or tm_d > worst_default[0]:
                worst_default = (tm_d, f"{c_name} / {p_name}")
            if worst_project is None or tm_p > worst_project[0]:
                worst_project = (tm_p, f"{c_name} / {p_name}")
        combo_rows.append(dict(
            chromosomal_set=c_id, plasmid_set=p_id,
            worst_pair_default=worst_default[1], worst_tm_default_c=f"{worst_default[0]:.1f}",
            worst_class_default=classify(worst_default[0]),
            worst_pair_project=worst_project[1], worst_tm_project_c=f"{worst_project[0]:.1f}",
            worst_class_project=classify(worst_project[0]),
            medium_or_high_pairs=flags, verdict="PASS" if flags == 0 else "FLAG"))

    for name, rows in (("cross_dimer_all_pairs.tsv", pair_rows), ("cross_dimer_by_combo.tsv", combo_rows)):
        with open(out_dir / name, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter="\t")
            w.writeheader()
            w.writerows(rows)

    n_pass = sum(r["verdict"] == "PASS" for r in combo_rows)
    max_d = max(float(r["worst_tm_default_c"]) for r in combo_rows)
    max_p = max(float(r["worst_tm_project_c"]) for r in combo_rows)
    ends = [float(r["primer_end_dg_kcal_mol"]) for r in pair_rows if r["primer_end_dg_kcal_mol"]]
    lines = [
        "bin/19 duplex cross-interaction check (D29)",
        f"primer3-py {primer3.__version__}; conditions (b) = {PROJECT_CONDITIONS}",
        f"positive control: {ctl_tm:.1f} C -> {classify(ctl_tm)}",
        "",
        f"{len(combo_rows)} chromosomal x plasmid combinations, {len(pair_rows)} cross pairs "
        f"({len(chrom)} chromosomal sets x {len(plasmid)} plasmid sets x 9 pairs)",
        f"combinations with no MEDIUM/HIGH cross-dimer under either condition: {n_pass} of {len(combo_rows)}",
        f"strongest cross-dimer structure Tm: {max_d:.1f} C (default conditions), {max_p:.1f} C (project conditions)",
        f"weakest (most negative) primer-primer 3'-end dG: {min(ends):.2f} kcal/mol (informational, no threshold)",
        "",
        f"{'chromosomal set':<14} {'plasmid set':<17} {'worst Tm default':>16} {'worst Tm project':>16}  verdict",
    ]
    for r in combo_rows:
        lines.append(f"{r['chromosomal_set']:<14} {r['plasmid_set']:<17} "
                     f"{r['worst_tm_default_c'] + ' C ' + r['worst_class_default']:>16} "
                     f"{r['worst_tm_project_c'] + ' C ' + r['worst_class_project']:>16}  {r['verdict']}")
    lines += ["", "Scope: oligo-oligo thermodynamics only. Not covered: BLAST cross-hits between targets, dye and "
              "channel assignment, real multiplex behaviour (laboratory evaluation)."]
    (out_dir / "summary.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
