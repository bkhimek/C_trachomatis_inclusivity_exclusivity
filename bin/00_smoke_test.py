#!/usr/bin/env python3
"""bin/00: tool and Primer3 smoke test.

1. Records tool versions to docs/tool_versions.txt.
2. Runs Primer3 on a synthetic 43% GC template with three probe-length ranges to find out
   which probe lengths the installed Primer3 accepts, and what Tm gap (probe Tm minus the
   higher primer Tm) it actually delivers. Nothing here is real target data.
Exit code 1 only if the baseline (24-36 nt) test fails.
"""
import datetime
import random
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SETTINGS = ROOT / "config" / "primer3_settings.txt"
VERSIONS = ROOT / "docs" / "tool_versions.txt"


def load_settings(path):
    d = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            k, v = line.split("=", 1)
            d[k.strip()] = v.strip()
    return d


def make_template(n=1000, seed=42):
    rng = random.Random(seed)
    return "".join(rng.choices("ATGC", weights=[0.285, 0.285, 0.215, 0.215], k=n))


def run_primer3(settings, template):
    rec = dict(settings)
    rec["SEQUENCE_ID"] = "smoke"
    rec["SEQUENCE_TEMPLATE"] = template
    text = "".join(f"{k}={v}\n" for k, v in rec.items()) + "=\n"
    p = subprocess.run(["primer3_core"], input=text, capture_output=True, text=True, timeout=120)
    out = {}
    for line in p.stdout.splitlines():
        if "=" in line and line != "=":
            k, v = line.split("=", 1)
            out[k] = v
    return out, p.stderr.strip()


def summarise(name, out, err):
    print(f"\n== {name}")
    if err:
        print("  stderr:", err[:300])
    for k in ("PRIMER_ERROR", "PRIMER_WARNING"):
        if k in out:
            print(f"  {k}: {out[k]}")
    print("  internal explain:", out.get("PRIMER_INTERNAL_EXPLAIN", "-"))
    n = int(out.get("PRIMER_PAIR_NUM_RETURNED", 0))
    rows = []
    for i in range(n):
        try:
            left = float(out[f"PRIMER_LEFT_{i}_TM"])
            right = float(out[f"PRIMER_RIGHT_{i}_TM"])
            probe_tm = float(out[f"PRIMER_INTERNAL_{i}_TM"])
            seq = out[f"PRIMER_INTERNAL_{i}_SEQUENCE"]
        except KeyError:
            continue
        gap = probe_tm - max(left, right)
        rows.append((len(seq), probe_tm, max(left, right), gap))
        print(f"  set {i}: probe {len(seq)} nt  Tm {probe_tm:.1f}  max primer Tm {max(left, right):.1f}  gap {gap:.1f}")
    if rows:
        lens = [r[0] for r in rows]
        gaps = [r[3] for r in rows]
        print(f"  -> {len(rows)} sets | probe length {min(lens)}-{max(lens)} nt | "
              f"gap >=5: {sum(g >= 5 for g in gaps)} | gap >=7: {sum(g >= 7 for g in gaps)}")
    else:
        print("  -> NO sets with a probe returned")
    return bool(rows)


def ver(cmd, contains=None):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        lines = [l.strip() for l in (r.stdout + r.stderr).splitlines() if l.strip()]
        if contains:
            lines = [l for l in lines if contains in l.lower()]
        return lines[0] if lines else "no output"
    except Exception as e:
        return f"unavailable ({e.__class__.__name__})"


def write_versions():
    tools = [
        ("primer3_core", ["primer3_core", "-about"], None),
        ("blastn", ["blastn", "-version"], None),
        ("makeblastdb", ["makeblastdb", "-version"], None),
        ("mafft", ["mafft", "--version"], None),
        ("fastANI", ["fastANI", "--version"], None),
        ("ncbi-datasets", ["datasets", "--version"], None),
        ("nextflow", ["nextflow", "-version"], "version"),
        ("prokka (prokka_env)", ["conda", "run", "-n", "prokka_env", "prokka", "--version"], None),
        ("panaroo (panaroo_env)", ["conda", "run", "-n", "panaroo_env", "panaroo", "--version"], None),
    ]
    lines = [f"# Tool versions, recorded {datetime.date.today()} by bin/00_smoke_test.py",
             f"python {sys.version.split()[0]}"]
    try:
        import Bio
        import pandas
        lines.append(f"biopython {Bio.__version__}")
        lines.append(f"pandas {pandas.__version__}")
    except ImportError as e:
        lines.append(f"python packages: {e}")
    for name, cmd, contains in tools:
        lines.append(f"{name}: {ver(cmd, contains)}")
    VERSIONS.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def main():
    print("== Tool versions")
    write_versions()
    base = load_settings(SETTINGS)
    template = make_template()
    tests = [
        ("A: probe 35-42 nt (original handover plan)",
         {"PRIMER_INTERNAL_MIN_SIZE": "35", "PRIMER_INTERNAL_OPT_SIZE": "38", "PRIMER_INTERNAL_MAX_SIZE": "42"}),
        ("B: probe 30-36 nt",
         {"PRIMER_INTERNAL_MIN_SIZE": "30", "PRIMER_INTERNAL_OPT_SIZE": "33", "PRIMER_INTERNAL_MAX_SIZE": "36"}),
        ("C: probe 24-36 nt (baseline)",
         {"PRIMER_INTERNAL_MIN_SIZE": "24", "PRIMER_INTERNAL_OPT_SIZE": "30", "PRIMER_INTERNAL_MAX_SIZE": "36"}),
    ]
    baseline_ok = False
    for name, override in tests:
        s = dict(base)
        s.update(override)
        out, err = run_primer3(s, template)
        ok = summarise(name, out, err)
        if name.startswith("C"):
            baseline_ok = ok
    return 0 if baseline_ok else 1


if __name__ == "__main__":
    sys.exit(main())
