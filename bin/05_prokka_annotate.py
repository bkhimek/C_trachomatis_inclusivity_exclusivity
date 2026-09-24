#!/usr/bin/env python3
"""bin/05: annotate the genomes with Prokka (one consistent annotation for the pangenome step, bin/06).

Input : data/genomes_downloaded/<accession>.fna
        data/genome_inventory/provenance_audit.tsv   (tiers, from bin/02)
Output: results/annotation/<accession>/<accession>.{gff,gbk,faa,ffn,txt,...}   (gitignored, large)
        results/annotation/annotation_summary.tsv    (committed: CDS/rRNA/tRNA counts, outlier flags)
        results/annotation/logs/<accession>.log      (gitignored)

Which genomes: primary and quality-review tiers (the excluded tier is not annotated). Prokka is run
with the same settings on all of them so that gene calls are comparable; RefSeq's own annotation is
not used because it was produced by different pipelines/versions.

Prokka lives in the conda env "prokka_env" (not on the base PATH). This script finds that env and
puts its bin/ first on PATH for the Prokka processes. Override with --prokka /path/to/prokka.

Resumable: a genome whose <accession>.gff already exists is skipped (use --rerun to redo).

Usage: bin/05_prokka_annotate.py [--jobs 3] [--cpus 2] [--tiers primary,quality-review] [--limit N] [--rerun]
"""
import argparse
import concurrent.futures
import csv
import os
import shutil
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INV = ROOT / "data" / "genome_inventory"
DL = ROOT / "data" / "genomes_downloaded"
OUT = ROOT / "results" / "annotation"
TIER = {"INCLUDE": "primary", "QUALITY_REVIEW": "quality-review", "REVIEW": "unresolved", "EXCLUDE": "excluded"}
CDS_OUTLIER = 0.10   # flag genomes whose CDS count is more than 10% from the median


def read_tsv(path):
    return list(csv.DictReader(open(path), delimiter="\t"))


def find_prokka(explicit):
    """Return (prokka executable, PATH string for the subprocess)."""
    if explicit:
        p = Path(explicit)
        return str(p), f"{p.parent}{os.pathsep}{os.environ['PATH']}"
    candidates = []
    try:
        base = subprocess.run(["conda", "info", "--base"], capture_output=True, text=True).stdout.strip()
        if base:
            candidates.append(Path(base) / "envs" / "prokka_env" / "bin" / "prokka")
    except FileNotFoundError:
        pass
    candidates += [Path.home() / "miniconda3" / "envs" / "prokka_env" / "bin" / "prokka",
                   Path.home() / "anaconda3" / "envs" / "prokka_env" / "bin" / "prokka"]
    for c in candidates:
        if c.exists():
            return str(c), f"{c.parent}{os.pathsep}{os.environ['PATH']}"
    w = shutil.which("prokka")
    if w:
        return w, os.environ["PATH"]
    sys.exit("prokka not found: expected conda env prokka_env (see docs/tool_versions.txt) or pass --prokka PATH")


def parse_stats(txt):
    """Prokka <prefix>.txt is 'key: value' lines (contigs, bases, CDS, rRNA, tRNA, tmRNA, ...)."""
    d = {}
    for line in Path(txt).read_text().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            d[k.strip()] = v.strip()
    return d


def annotate(job):
    acc, strain, tag, prokka, path_env, cpus, rerun = job
    d = OUT / acc
    gff = d / f"{acc}.gff"
    if gff.exists() and gff.stat().st_size > 0 and not rerun:
        return acc, "skipped (already done)", 0.0
    cmd = [prokka, "--outdir", str(d), "--prefix", acc, "--locustag", tag, "--genus", "Chlamydia",
           "--species", "trachomatis", "--strain", strain or acc, "--kingdom", "Bacteria", "--gcode", "11",
           "--cpus", str(cpus), "--force", str(DL / f"{acc}.fna")]
    env = dict(os.environ, PATH=path_env)
    t0 = time.time()
    p = subprocess.run(cmd, capture_output=True, text=True, env=env)
    (OUT / "logs").mkdir(parents=True, exist_ok=True)
    (OUT / "logs" / f"{acc}.log").write_text(p.stdout + "\n" + p.stderr)
    ok = p.returncode == 0 and gff.exists() and gff.stat().st_size > 0
    return acc, "ok" if ok else f"FAILED (exit {p.returncode}; see results/annotation/logs/{acc}.log)", time.time() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=3, help="genomes annotated in parallel")
    ap.add_argument("--cpus", type=int, default=2, help="CPUs per Prokka run")
    ap.add_argument("--tiers", default="primary,quality-review")
    ap.add_argument("--limit", type=int, default=0, help="annotate only the first N genomes (test run)")
    ap.add_argument("--prokka", default="")
    ap.add_argument("--rerun", action="store_true")
    args = ap.parse_args()

    meta = {r["accession"]: r for r in read_tsv(INV / "genome_metadata.tsv")}
    audit = {r["accession"]: r for r in read_tsv(INV / "provenance_audit.tsv")}
    want = set(args.tiers.split(","))
    accs = sorted(a for a in meta if TIER[audit[a]["final_verdict"]] in want)
    if args.limit:
        accs = accs[:args.limit]
    missing = [a for a in accs if not (DL / f"{a}.fna").exists()]
    if missing:
        sys.exit(f"{len(missing)} genome files missing in data/genomes_downloaded/ (run bin/01): {missing[:3]}...")
    prokka, path_env = find_prokka(args.prokka)
    ver = subprocess.run([prokka, "--version"], capture_output=True, text=True, env=dict(os.environ, PATH=path_env))
    print(f"== Prokka: {prokka} ({(ver.stdout + ver.stderr).strip()})")
    print(f"== annotating {len(accs)} genomes (tiers: {args.tiers}), {args.jobs} jobs x {args.cpus} cpus")
    OUT.mkdir(parents=True, exist_ok=True)

    jobs = [(a, meta[a]["strain"], f"CT{i:04d}", prokka, path_env, args.cpus, args.rerun) for i, a in enumerate(accs, 1)]
    failed, t_start, done = [], time.time(), 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as ex:
        for acc, status, secs in ex.map(annotate, jobs):
            done += 1
            print(f"  [{done:>3}/{len(accs)}] {acc} {status}" + (f" ({secs:.0f}s)" if secs else ""), flush=True)
            if status.startswith("FAILED"):
                failed.append(acc)
    print(f"== finished in {(time.time() - t_start) / 60:.1f} min; failures: {failed or 'none'}")

    rows = []
    for a in accs:
        txt = OUT / a / f"{a}.txt"
        if not txt.exists():
            continue
        s = parse_stats(txt)
        rows.append({"accession": a, "strain": meta[a]["strain"], "tier": TIER[audit[a]["final_verdict"]],
                     "contigs": s.get("contigs", ""), "bases": s.get("bases", ""), "CDS": int(s.get("CDS", 0)),
                     "rRNA": s.get("rRNA", ""), "tRNA": s.get("tRNA", ""), "tmRNA": s.get("tmRNA", ""), "flag": ""})
    if not rows:
        sys.exit("no annotation summaries found")
    med = statistics.median(r["CDS"] for r in rows)
    for r in rows:
        if abs(r["CDS"] - med) > CDS_OUTLIER * med:
            r["flag"] = f"CDS_COUNT_OUTLIER (median {med:.0f})"
    with open(OUT / "annotation_summary.tsv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter="\t")
        w.writeheader()
        w.writerows(rows)
    cds = [r["CDS"] for r in rows]
    print(f"\n== CDS per genome: median {med:.0f}, min {min(cds)}, max {max(cds)} ({len(rows)} annotated)")
    flagged = [r for r in rows if r["flag"]]
    print(f"== flagged CDS-count outliers: {len(flagged)}")
    for r in flagged:
        print(f"  {r['accession']} {r['strain'][:22]:<22} {r['tier']:<14} CDS {r['CDS']}")
    print(f"wrote {OUT.relative_to(ROOT)}/annotation_summary.tsv")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
