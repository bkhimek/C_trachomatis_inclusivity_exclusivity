#!/usr/bin/env python3
"""bin/06: pangenome analysis with Panaroo on the primary-tier annotated genomes.

Input : results/annotation/<accession>/<accession>.gff  (Prokka output, from bin/05)
        data/genome_inventory/provenance_audit.tsv        (tiers, from bin/02)
Output: results/pangenome/                        Panaroo's own outputs (mostly gitignored, see .gitignore)
        results/pangenome/core_gene_summary.tsv   committed: one row per gene cluster, with presence
                                                   count/pct among primary genomes, classification,
                                                   annotation, sequence length
        results/pangenome/core_genes.fasta        committed: one representative nucleotide sequence
                                                   per CORE gene cluster, input for bin/07 exclusivity
                                                   screening
        results/pangenome/pangenome_summary.txt   committed copy of Panaroo's own summary

Why primary tier only: per D13, the primary tier is what builds the consensus/inclusivity claim.
Quality-review genomes are annotated (bin/05) so they CAN be tested later (e.g. BLASTing a finished
primer/probe against them) but they do not shape which genes/regions count as "core".

Panaroo lives in the conda env "panaroo_env" (not on the base PATH), the same pattern as bin/05's
prokka_env lookup. Override with --panaroo /path/to/panaroo.

Core gene threshold: a gene present in >=99% of primary genomes is "core" (matches the 99% consensus
target used later). Panaroo is told the same cutoff so its own summary agrees with core_gene_summary.tsv.

Resumable: if results/pangenome/gene_presence_absence.Rtab already exists, Panaroo is not re-run
(use --rerun to force). Usage: bin/06_panaroo_pangenome.py [--threads 6] [--core-threshold 0.99] [--rerun]
"""
import argparse
import csv
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INV = ROOT / "data" / "genome_inventory"
ANNOT = ROOT / "results" / "annotation"
OUT = ROOT / "results" / "pangenome"
TIER = {"INCLUDE": "primary", "QUALITY_REVIEW": "quality-review", "REVIEW": "unresolved", "EXCLUDE": "excluded"}


def read_tsv(path):
    return list(csv.DictReader(open(path), delimiter="\t"))


def find_panaroo(explicit):
    if explicit:
        p = Path(explicit)
        return str(p), f"{p.parent}{os.pathsep}{os.environ['PATH']}"
    candidates = []
    try:
        base = subprocess.run(["conda", "info", "--base"], capture_output=True, text=True).stdout.strip()
        if base:
            candidates.append(Path(base) / "envs" / "panaroo_env" / "bin" / "panaroo")
    except FileNotFoundError:
        pass
    candidates += [Path.home() / "miniconda3" / "envs" / "panaroo_env" / "bin" / "panaroo",
                   Path.home() / "anaconda3" / "envs" / "panaroo_env" / "bin" / "panaroo"]
    for c in candidates:
        if c.exists():
            return str(c), f"{c.parent}{os.pathsep}{os.environ['PATH']}"
    w = shutil.which("panaroo")
    if w:
        return w, os.environ["PATH"]
    sys.exit("panaroo not found: expected conda env panaroo_env (see docs/tool_versions.txt) or pass --panaroo PATH")


def run_panaroo(gffs, threads, core_threshold, panaroo, path_env, rerun):
    OUT.mkdir(parents=True, exist_ok=True)
    rtab = OUT / "gene_presence_absence.Rtab"
    if rtab.exists() and not rerun:
        print(f"  reusing {OUT.relative_to(ROOT)}/ (use --rerun to recompute)")
        return
    cmd = [panaroo, "-i", *[str(g) for g in gffs], "-o", str(OUT), "-t", str(threads),
           "--clean-mode", "strict", "-a", "core", "--core_threshold", str(core_threshold),
           "--remove-invalid-genes"]
    print("  running panaroo on", len(gffs), "genomes (this can take a while)...")
    p = subprocess.run(cmd, capture_output=True, text=True, env=dict(os.environ, PATH=path_env))
    (OUT / "panaroo_run.log").write_text(p.stdout + "\n" + p.stderr)
    if p.returncode != 0 or not rtab.exists():
        sys.exit(f"panaroo failed (full log: results/pangenome/panaroo_run.log):\n{p.stderr[-1500:]}")


def load_rtab(path):
    rows = list(csv.reader(open(path), delimiter="\t"))
    genomes = rows[0][1:]
    counts = {}
    for r in rows[1:]:
        gene, vals = r[0], r[1:]
        counts[gene] = sum(1 for v in vals if v not in ("0", ""))
    return counts, len(genomes)


def load_annotations(path):
    """Gene -> (non-unique name, annotation/product) from Panaroo's gene_presence_absence.csv."""
    ann = {}
    if not path.exists():
        return ann
    for row in csv.DictReader(open(path)):
        gene = row.get("Gene", "")
        if gene:
            ann[gene] = (row.get("Non-unique Gene name", "") or "", row.get("Annotation", "") or "")
    return ann


def load_ref_seqs(path):
    """Gene -> nucleotide sequence, from Panaroo's pan_genome_reference.fa. The first whitespace-delimited
    token of each header is the gene/group name, matching the Rtab and gene_presence_absence.csv 'Gene' column."""
    seqs, name, buf = {}, None, []
    if not path.exists():
        return seqs
    for line in open(path):
        line = line.rstrip("\n")
        if line.startswith(">"):
            if name:
                seqs[name] = "".join(buf)
            name, buf = line[1:].split()[0], []
        else:
            buf.append(line.strip())
    if name:
        seqs[name] = "".join(buf)
    return seqs


def classify(pct):
    if pct >= 99:
        return "core"
    if pct >= 95:
        return "soft-core"
    if pct >= 15:
        return "shell"
    return "cloud"


def build_summary(n_genomes, counts, ann, seqs, core_threshold):
    rows = []
    for gene, n in counts.items():
        pct = 100 * n / n_genomes
        name, product = ann.get(gene, ("", ""))
        rows.append({"gene": gene, "gene_name": name, "annotation": product, "n_genomes": n,
                     "n_total": n_genomes, "pct": f"{pct:.1f}", "classification": classify(pct),
                     "seq_length": len(seqs.get(gene, ""))})
    rows.sort(key=lambda r: (-float(r["pct"]), r["gene"]))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--threads", type=int, default=6)
    ap.add_argument("--core-threshold", type=float, default=0.99)
    ap.add_argument("--panaroo", default="")
    ap.add_argument("--rerun", action="store_true")
    args = ap.parse_args()

    audit = {r["accession"]: r for r in read_tsv(INV / "provenance_audit.tsv")}
    primary = sorted(a for a, r in audit.items() if TIER[r["final_verdict"]] == "primary")
    gffs = [ANNOT / a / f"{a}.gff" for a in primary]
    missing = [a for a, g in zip(primary, gffs) if not g.exists()]
    if missing:
        sys.exit(f"{len(missing)} primary genomes have no Prokka .gff (run bin/05): {missing[:5]}...")
    print(f"== {len(primary)} primary-tier genomes with annotation")

    panaroo, path_env = find_panaroo(args.panaroo)
    ver = subprocess.run([panaroo, "--version"], capture_output=True, text=True, env=dict(os.environ, PATH=path_env))
    print(f"== Panaroo: {panaroo} ({(ver.stdout + ver.stderr).strip()})")
    run_panaroo(gffs, args.threads, args.core_threshold, panaroo, path_env, args.rerun)

    counts, n_genomes = load_rtab(OUT / "gene_presence_absence.Rtab")
    if n_genomes != len(primary):
        print(f"  NOTE: Rtab has {n_genomes} genome columns, expected {len(primary)}")
    ann = load_annotations(OUT / "gene_presence_absence.csv")
    seqs = load_ref_seqs(OUT / "pan_genome_reference.fa")
    rows = build_summary(n_genomes, counts, ann, seqs, args.core_threshold)

    with open(OUT / "core_gene_summary.tsv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter="\t")
        w.writeheader()
        w.writerows(rows)

    core = [r for r in rows if r["classification"] == "core"]
    with open(OUT / "core_genes.fasta", "w") as f:
        for r in core:
            seq = seqs.get(r["gene"], "")
            if seq:
                label = r["gene_name"] or r["gene"]
                f.write(f">{r['gene']} {label} | {r['annotation']}\n")
                for i in range(0, len(seq), 70):
                    f.write(seq[i:i + 70] + "\n")

    summary_txt = OUT / "summary_statistics.txt"
    if summary_txt.exists():
        shutil.copy(summary_txt, OUT / "pangenome_summary.txt")

    dist = {}
    for r in rows:
        dist[r["classification"]] = dist.get(r["classification"], 0) + 1
    print(f"\n== Pangenome on {n_genomes} primary genomes: {len(rows)} gene clusters")
    for cls in ("core", "soft-core", "shell", "cloud"):
        print(f"  {cls:<10} {dist.get(cls, 0)}")
    have_seq = sum(1 for r in core if seqs.get(r["gene"]))
    print(f"\n== {len(core)} core genes (>= {args.core_threshold * 100:.0f}% of primary genomes); "
          f"{have_seq} written to core_genes.fasta with a representative sequence")
    missing_seq = [r["gene"] for r in core if not seqs.get(r["gene"])]
    if missing_seq:
        print(f"  NOTE: {len(missing_seq)} core genes have no sequence in pan_genome_reference.fa: {missing_seq[:5]}...")
    print(f"wrote {OUT.relative_to(ROOT)}/ (core_gene_summary.tsv, core_genes.fasta, pangenome_summary.txt)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
