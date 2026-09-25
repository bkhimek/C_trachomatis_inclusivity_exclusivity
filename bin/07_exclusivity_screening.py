#!/usr/bin/env python3
"""bin/07: exclusivity screening of the core genes against the non-target species panel.

Input : results/pangenome/core_genes.fasta         874 core gene representative sequences (bin/06)
        results/pangenome/core_gene_summary.tsv    gene metadata (bin/06)
        results/pangenome/gene_presence_absence.csv  Panaroo's own presence/absence+annotation table
                                                    (kept locally by bin/06 though gitignored; used here
                                                    only to report average copy number per gene)
        data/panel/blastdb/{genus,clinical}.*      BLAST databases of the exclusivity panel: 10 genus-tier
                                                    Chlamydia species (31 genomes) + 25 clinical/STI/flora
                                                    species (92 genomes) = 123 non-target genomes, 35 species.
                                                    REUSED from the earlier trial run (bin/05_select_panel.py
                                                    + bin/06_build_panel_db.sh there, run 2026-09-20; scripts
                                                    archived in docs/archive/trial_panel_scripts/). The panel
                                                    definition was not affected by the reasons for the restart
                                                    (genome provenance, probe Tm gap), so it is reused as-is
                                                    rather than rebuilt. See docs/exclusivity_panel_species.txt
                                                    for the species list and rationale.
Output: results/exclusivity/blast_genus.tsv, blast_clinical.tsv   raw BLAST hits (gitignored, large)
        results/exclusivity/core_gene_exclusivity.tsv             per-gene exclusivity gap analysis (committed)

Method: BLAST each core gene against each tier's panel database (blastn, e-value 1e-5). For every core gene,
merge the query-coordinate intervals covered by ANY hit to that tier (at two identity floors: "any" hit, and
hits >=85% identity only) and find the GAPS -- stretches of the gene with no significant hit to the panel.
The largest gap ("maxgap") is the biggest exclusivity-clean window inside that gene, which is what a
candidate primer/probe region needs. A gap of >=150 bp is enough room for a full PCR amplicon with an
internal probe. This doubles as an early candidate-region signal, not just a pass/fail screen.

Usage: bin/07_exclusivity_screening.py [--threads 4] [--rerun]
"""
import argparse
import collections
import csv
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAN = ROOT / "results" / "pangenome"
OUT = ROOT / "results" / "exclusivity"
DB = ROOT / "data" / "panel" / "blastdb"
EVAL = "1e-5"
MIN_GAP = 150
ID_TOL = 85.0
TIERS = ("genus", "clinical")


def read_tsv(path):
    return list(csv.DictReader(open(path), delimiter="\t"))


def read_fasta(path):
    seqs, name, buf = {}, None, []
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


def read_avg_copies(path):
    """gene -> average copy number per genome, from Panaroo's gene_presence_absence.csv (optional)."""
    copies = {}
    if not path.exists():
        return copies
    for row in csv.DictReader(open(path)):
        gene = row.get("Gene", "")
        cells = [c for k, c in row.items() if k not in ("Gene", "Non-unique Gene name", "Annotation")
                 and c.strip()]
        if gene and cells:
            copies[gene] = sum(len(c.split(";")) for c in cells) / len(cells)
    return copies


def run_blast(query, db, out, threads):
    if out.exists():
        print(f"  reusing {out.relative_to(ROOT)} (use --rerun to recompute)")
        return
    cmd = ["blastn", "-task", "blastn", "-query", str(query), "-db", str(db), "-evalue", EVAL,
           "-dust", "no", "-num_threads", str(threads), "-max_target_seqs", "500",
           "-outfmt", "6 qseqid sseqid pident length qstart qend evalue bitscore", "-out", str(out)]
    print("  running blastn vs", db.name, "...")
    subprocess.run(cmd, check=True)


def merge(intervals):
    m = []
    for s, e in sorted(intervals):
        if m and s <= m[-1][1] + 1:
            m[-1][1] = max(m[-1][1], e)
        else:
            m.append([s, e])
    return m


def gaps(merged, length):
    g, pos = [], 1
    for s, e in merged:
        if s > pos:
            g.append((pos, s - 1))
        pos = max(pos, e + 1)
    if pos <= length:
        g.append((pos, length))
    return g


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--rerun", action="store_true")
    args = ap.parse_args()

    for tier in TIERS:
        if not (DB / f"{tier}.nsq").exists() and not (DB / f"{tier}.nal").exists():
            sys.exit(f"BLAST database data/panel/blastdb/{tier} not found -- copy data/panel/ over from the "
                      f"trial run first (see docs/HANDOVER.md)")

    OUT.mkdir(parents=True, exist_ok=True)
    seqs = read_fasta(PAN / "core_genes.fasta")
    summary = {r["gene"]: r for r in read_tsv(PAN / "core_gene_summary.tsv") if r["classification"] == "core"}
    missing = [g for g in summary if g not in seqs]
    if missing:
        sys.exit(f"{len(missing)} core genes have no sequence in core_genes.fasta: {missing[:5]}...")
    copies = read_avg_copies(PAN / "gene_presence_absence.csv")
    print(f"== {len(summary)} core genes to screen against the exclusivity panel")

    if args.rerun:
        for tier in TIERS:
            (OUT / f"blast_{tier}.tsv").unlink(missing_ok=True)
    for tier in TIERS:
        run_blast(PAN / "core_genes.fasta", DB / tier, OUT / f"blast_{tier}.tsv", args.threads)

    hits = {t: collections.defaultdict(list) for t in TIERS}
    for tier in TIERS:
        for line in open(OUT / f"blast_{tier}.tsv"):
            q, s, pid, ln, qs, qe, ev, bs = line.rstrip("\n").split("\t")
            species = s.split("|")[1] if "|" in s else s
            hits[tier][q].append((int(qs), int(qe), float(pid), species))

    rows = []
    for gene, meta in summary.items():
        length = len(seqs[gene])
        r = {"gene": gene, "gene_name": meta["gene_name"], "annotation": meta["annotation"],
             "n_primary_genomes": meta["n_genomes"], "avg_copies": f"{copies.get(gene, 1.0):.2f}",
             "length": length}
        for mode, minid in (("any", 0.0), ("id85", ID_TOL)):
            for tier_label in ("genus", "clinical", "all"):
                tiers = TIERS if tier_label == "all" else (tier_label,)
                iv = [(a, b) for t in tiers for a, b, p, sp in hits[t][gene] if p >= minid]
                gp = gaps(merge(iv), length)
                big = [g for g in gp if g[1] - g[0] + 1 >= MIN_GAP]
                best = max(gp, key=lambda g: g[1] - g[0], default=None)
                r[f"{tier_label}_{mode}_maxgap"] = (best[1] - best[0] + 1) if best else 0
                r[f"{tier_label}_{mode}_n150"] = len(big)
                if tier_label == "all":
                    r[f"all_{mode}_coords"] = f"{best[0]}-{best[1]}" if best else ""
        r["n_species_genus"] = len({sp for a, b, p, sp in hits["genus"][gene]})
        r["n_species_clinical"] = len({sp for a, b, p, sp in hits["clinical"][gene]})
        rows.append(r)
    rows.sort(key=lambda r: -r["all_any_maxgap"])

    with open(OUT / "core_gene_exclusivity.tsv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter="\t")
        w.writeheader()
        w.writerows(rows)

    print("\n== core genes with an exclusivity-clean gap >= 150 bp (union of panel hits):")
    for mode in ("any", "id85"):
        for tier_label in ("genus", "clinical", "all"):
            n = sum(1 for r in rows if r[f"{tier_label}_{mode}_n150"] > 0)
            print(f"  {tier_label:9s} {mode:5s}: {n:4d} of {len(rows)}")
    print("\n== top 15 core genes by largest exclusivity-clean gap (strict: any-identity hit vs genus+clinical):")
    for r in rows[:15]:
        print(f"  {r['gene']:14s} len={r['length']:5d} maxgap={r['all_any_maxgap']:5d} ({r['all_any_coords']}) "
              f"id85gap={r['all_id85_maxgap']:5d} copies={r['avg_copies']:>5s}  {r['annotation'][:40]}")
    print(f"\nwrote {OUT.relative_to(ROOT)}/core_gene_exclusivity.tsv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
