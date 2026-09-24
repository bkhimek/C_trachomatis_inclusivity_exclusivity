#!/usr/bin/env python3
"""bin/03: species check and redundancy map with fastANI (all genomes vs all genomes).

Input : data/genomes_downloaded/<accession>.fna for every genome in genome_metadata.tsv (from bin/01)
        data/genome_inventory/provenance_audit.tsv (tiers, from bin/02)
Output: results/genome_qc/fastani_all_vs_all.tsv     raw fastANI output (all pairs above fastANI's 80% floor)
        results/genome_qc/fastani_summary.tsv        per genome: nearest neighbour, min/median ANI, fragment fractions, flags
        results/genome_qc/near_identical_clusters.tsv clusters of near-identical genomes at several ANI thresholds

Why: (1) confirms every genome is C. trachomatis (species boundary is about 95% ANI; genomes of one
species here should sit at 98-100%), independently of NCBI's own ANI check; (2) maps redundancy
(serial same-patient isolates, re-sequenced reference strains) so the consensus step can
de-replicate or weight near-identical genomes.

Usage: bin/03_species_check_fastani.py [--threads 4] [--rerun]
"""
import argparse
import collections
import csv
import statistics
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INV = ROOT / "data" / "genome_inventory"
DL = ROOT / "data" / "genomes_downloaded"
OUT = ROOT / "results" / "genome_qc"

SPECIES_MIN = 95.0    # below this a genome is not the same species: hard flag
SUSPECT_MIN = 98.5    # below this against its nearest neighbour is unusual for C. trachomatis: review
LOW_FRACTION = 0.90   # median fraction of fragments mapped below this: review
CLUSTER_THRESHOLDS = (99.999, 99.99, 99.9, 99.5)
TIER = {"INCLUDE": "primary", "QUALITY_REVIEW": "quality-review", "REVIEW": "unresolved", "EXCLUDE": "excluded"}


def read_tsv(path):
    return list(csv.DictReader(open(path), delimiter="\t"))


def run_fastani(paths, threads, rerun):
    OUT.mkdir(parents=True, exist_ok=True)
    listing, raw = OUT / "genome_list.txt", OUT / "fastani_all_vs_all.tsv"
    listing.write_text("\n".join(str(p) for p in paths) + "\n")
    if raw.exists() and not rerun:
        print(f"  reusing {raw.relative_to(ROOT)} (use --rerun to recompute)")
        return raw
    cmd = ["fastANI", "--ql", str(listing), "--rl", str(listing), "-o", str(raw), "-t", str(threads)]
    print("  running:", " ".join(cmd))
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0 or not raw.exists():
        sys.exit(f"fastANI failed:\n{p.stderr[-800:]}")
    return raw


def parse(raw, acc_of):
    ani = {}
    for line in open(raw):
        q, r, a, m, t = line.rstrip("\n").split("\t")
        qa, ra = acc_of.get(Path(q).name), acc_of.get(Path(r).name)
        if not qa or not ra or qa == ra:
            continue
        ani[(qa, ra)] = (float(a), int(m) / int(t))
    return ani


def sym(ani, a, b):
    """Mean ANI and mean fragment fraction over both directions (None if the pair has no result)."""
    vals = [ani[k] for k in ((a, b), (b, a)) if k in ani]
    if not vals:
        return None
    return sum(v[0] for v in vals) / len(vals), sum(v[1] for v in vals) / len(vals)


def clusters(accs, ani, threshold):
    parent = {a: a for a in accs}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i, a in enumerate(accs):
        for b in accs[i + 1:]:
            s = sym(ani, a, b)
            if s and s[0] >= threshold:
                parent[find(a)] = find(b)
    groups = collections.defaultdict(list)
    for a in accs:
        groups[find(a)].append(a)
    return sorted(groups.values(), key=lambda g: (-len(g), g[0]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--rerun", action="store_true")
    args = ap.parse_args()

    meta = {r["accession"]: r for r in read_tsv(INV / "genome_metadata.tsv")}
    audit = {r["accession"]: r for r in read_tsv(INV / "provenance_audit.tsv")}
    accs = sorted(meta)
    missing = [a for a in accs if not (DL / f"{a}.fna").exists()]
    if missing:
        sys.exit(f"{len(missing)} genome files missing in data/genomes_downloaded/ (run bin/01): {missing[:3]}...")
    tier = {a: TIER[audit[a]["final_verdict"]] for a in accs}
    print(f"== fastANI all-vs-all on {len(accs)} genomes")
    raw = run_fastani([DL / f"{a}.fna" for a in accs], args.threads, args.rerun)
    ani = parse(raw, {f"{a}.fna": a for a in accs})

    rows = []
    for a in accs:
        partners = []
        for b in accs:
            if b != a:
                s = sym(ani, a, b)
                if s:
                    partners.append((s[0], s[1], b))
        if not partners:
            rows.append({"accession": a, "strain": meta[a]["strain"], "tier": tier[a], "n_partners": 0, "nearest": "",
                         "nearest_ani": "", "min_ani": "", "median_ani": "", "median_fraction": "",
                         "flag": "NO_ANI_RESULT (below fastANI 80% floor with every genome)"})
            continue
        partners.sort(reverse=True)
        anis = [p[0] for p in partners]
        med_frac = statistics.median(p[1] for p in partners)
        flags = []
        if anis[0] < SPECIES_MIN:
            flags.append(f"NOT_SAME_SPECIES (best ANI {anis[0]:.2f})")
        elif anis[0] < SUSPECT_MIN:
            flags.append(f"LOW_NEAREST_ANI ({anis[0]:.2f})")
        if med_frac < LOW_FRACTION:
            flags.append(f"LOW_FRAGMENT_FRACTION ({med_frac:.2f})")
        rows.append({
            "accession": a, "strain": meta[a]["strain"], "tier": tier[a], "n_partners": len(partners),
            "nearest": partners[0][2], "nearest_ani": f"{anis[0]:.4f}", "min_ani": f"{min(anis):.4f}",
            "median_ani": f"{statistics.median(anis):.4f}", "median_fraction": f"{med_frac:.3f}",
            "flag": "; ".join(flags),
        })
    with open(OUT / "fastani_summary.tsv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter="\t")
        w.writeheader()
        w.writerows(rows)

    print("\n== Per-tier ANI (each genome vs all others)")
    for t in ("primary", "quality-review", "excluded", "unresolved"):
        sel = [r for r in rows if r["tier"] == t and r["min_ani"] != ""]
        if sel:
            print(f"  {t:<15} n={len(sel):<3} lowest min-ANI {min(float(r['min_ani']) for r in sel):.2f} | "
                  f"lowest median-ANI {min(float(r['median_ani']) for r in sel):.2f} | "
                  f"lowest nearest-neighbour ANI {min(float(r['nearest_ani']) for r in sel):.2f}")
    flagged = [r for r in rows if r["flag"]]
    print(f"\n== Flagged genomes: {len(flagged)}")
    for r in flagged:
        print(f"  {r['accession']} {r['strain'][:22]:<22} {r['tier']:<14} nearest {r['nearest_ani'] or '-':>8} "
              f"median {r['median_ani'] or '-':>8}  {r['flag']}")

    prim = [a for a in accs if tier[a] in ("primary",)]
    print(f"\n== Redundancy among the {len(prim)} primary genomes (clusters of near-identical genomes)")
    cl_rows = []
    for th in CLUSTER_THRESHOLDS:
        groups = clusters(prim, ani, th)
        multi = [g for g in groups if len(g) > 1]
        print(f"  ANI >= {th}: {len(groups)} clusters ({len(multi)} with 2+ genomes; largest {len(groups[0])})")
        for i, g in enumerate(groups, 1):
            cl_rows.append({"threshold": th, "cluster": i, "size": len(g),
                            "members": "; ".join(f"{a}:{meta[a]['strain']}" for a in g),
                            "bioprojects": ";".join(sorted({meta[a]["bioproject"] for a in g}))})
    with open(OUT / "near_identical_clusters.tsv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(cl_rows[0].keys()), delimiter="\t")
        w.writeheader()
        w.writerows(cl_rows)
    print("  largest clusters at ANI >= 99.99:")
    for g in [g for g in clusters(prim, ani, 99.99) if len(g) > 1][:8]:
        print(f"    {len(g)}: " + ", ".join(meta[a]["strain"] for a in g[:8]) + (" ..." if len(g) > 8 else ""))
    print(f"\nwrote {OUT.relative_to(ROOT)}/ (fastani_summary.tsv, near_identical_clusters.tsv)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
