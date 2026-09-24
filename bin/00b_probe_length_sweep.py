#!/usr/bin/env python3
"""bin/00b: how short can the probe be while keeping Tm and the primer-probe gap?

Synthetic templates only (not real target data). Uses Primer3 with identical primer/probe
salt settings from config/primer3_settings.txt. Shorter probes are preferred (lower background
fluorescence), so probe size optimum is set low and longer probes are penalised.
"""
import importlib.util
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("smoke", ROOT / "bin" / "00_smoke_test.py")
smoke = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smoke)


def template(gc, n=1000, seed=42):
    rng = random.Random(seed)
    at = (1 - gc) / 2
    g = gc / 2
    return "".join(rng.choices("ATGC", weights=[at, at, g, g], k=n))


def rows(out):
    res = []
    for i in range(int(out.get("PRIMER_PAIR_NUM_RETURNED", 0))):
        try:
            pt = float(out[f"PRIMER_INTERNAL_{i}_TM"])
            mp = max(float(out[f"PRIMER_LEFT_{i}_TM"]), float(out[f"PRIMER_RIGHT_{i}_TM"]))
            res.append((len(out[f"PRIMER_INTERNAL_{i}_SEQUENCE"]), pt, pt - mp))
        except KeyError:
            pass
    return res


def case(base, tpl, cap, tm_min, mg=None):
    s = dict(base)
    s.update({
        "PRIMER_INTERNAL_MIN_SIZE": "18",
        "PRIMER_INTERNAL_OPT_SIZE": str(min(22, cap)),
        "PRIMER_INTERNAL_MAX_SIZE": str(cap),
        "PRIMER_INTERNAL_WT_SIZE_GT": "1.0",
        "PRIMER_INTERNAL_MIN_TM": str(tm_min),
        "PRIMER_INTERNAL_OPT_TM": str(tm_min + 2),
        "PRIMER_INTERNAL_MAX_TM": "72.0",
    })
    if mg is not None:
        s["PRIMER_SALT_DIVALENT"] = s["PRIMER_INTERNAL_SALT_DIVALENT"] = str(mg)
    out, _ = smoke.run_primer3(s, tpl)
    m = re.search(r"\bok (\d+)", out.get("PRIMER_INTERNAL_EXPLAIN", ""))
    ok = int(m.group(1)) if m else 0
    r = rows(out)
    if not r:
        return f"acceptable probes {ok:>5} | no sets returned"
    lens = [x[0] for x in r]
    tms = [x[1] for x in r]
    g5 = sum(x[2] >= 5 for x in r)
    return (f"acceptable probes {ok:>5} | sets {len(r):>2} | len {min(lens)}-{max(lens)} nt | "
            f"probe Tm {min(tms):.1f}-{max(tms):.1f} | gap>=5: {g5}/{len(r)}")


def main():
    base = smoke.load_settings(ROOT / "config" / "primer3_settings.txt")
    t43 = template(0.43)
    print("== 1. Length cap x probe Tm floor (43% GC, Mg 3.0 mM)")
    for tm_min in (66, 65, 64):
        for cap in (22, 24, 26, 28, 30, 32, 36):
            print(f"  Tm>={tm_min} cap {cap:>2} | {case(base, t43, cap, tm_min)}")
    print("\n== 2. Template GC sensitivity (Tm>=66, Mg 3.0 mM)")
    for gc in (0.38, 0.43, 0.48):
        for cap in (24, 26, 28, 30):
            print(f"  GC {gc:.2f} cap {cap:>2} | {case(base, template(gc), cap, 66)}")
    print("\n== 3. Mg2+ sensitivity (Tm>=66, 43% GC)")
    for mg in (1.5, 3.0, 5.0):
        for cap in (26, 28, 30):
            print(f"  Mg {mg:.1f} mM cap {cap:>2} | {case(base, t43, cap, 66, mg)}")


if __name__ == "__main__":
    sys.exit(main())
