#!/usr/bin/env python3
"""bin/08: candidate region discovery -- combine bin/07's exclusivity-clean windows with within-species
conservation, to find sub-regions that are BOTH exclusivity-clean AND stable enough across the 97 primary
genomes to hold a primer/probe set.

Input : results/exclusivity/core_gene_exclusivity.tsv   exclusivity gaps per core gene (bin/07)
        results/pangenome/core_genes.fasta              representative sequence per core gene (bin/06)
        results/pangenome/aligned_gene_sequences/*.aln.fas   Panaroo's own per-gene, multi-genome alignments
                                                          (written by bin/06's panaroo run; NOT committed to
                                                          git -- large -- but still on disk locally)
Output: results/candidate_regions/candidate_regions.tsv    ranked table (committed)
        results/candidate_regions/candidate_regions.fasta  refined window sequence per candidate (committed)

D16 (see docs/PROJECT_STATE.md): a candidate window is defined by bin/07's "any species >=85% identity"
exclusivity gap (the realistic cross-reactivity threshold, not the stricter "any hit at all" one), and must
also be >=99% conserved, position by position, across the primary genomes that carry the gene (the same
99% consensus threshold used throughout this project). Only the single largest exclusivity gap per gene is
considered (a gene can have more than one qualifying gap; refining all of them is a possible later addition,
not done here).

Method per candidate gene:
  1. Take the best exclusivity-clean window (bin/07's all_id85_coords), in the coordinates of the gene's own
     representative sequence (core_genes.fasta).
  2. Load that gene's Panaroo alignment (one row per genome that carries the gene). Identify which aligned
     row IS the representative sequence by stripping gaps and matching it against core_genes.fasta directly
     (content-based matching -- robust to any sample/locus-tag naming Panaroo used for the alignment rows).
  3. Walk the representative's own positions through the exclusivity window; at each position, compute the
     fraction of genomes agreeing with the majority base at that alignment column (a genome with a gap there
     counts as disagreeing -- it is a deletion relative to the reference). A position is "conserved" if
     agreement is >=99%.
  4. Find the longest run of conserved positions inside the exclusivity window. That run is the refined
     candidate region.

Usage: bin/08_candidate_regions.py [--min-gap 150] [--min-region 100]
"""
import argparse
import csv
import difflib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXCL = ROOT / "results" / "exclusivity"
PAN = ROOT / "results" / "pangenome"
ALN_DIR = PAN / "aligned_gene_sequences"
OUT = ROOT / "results" / "candidate_regions"
CONSERVED_THRESHOLD = 0.99


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


def find_alignment_file(gene):
    """Panaroo's own filename for this gene's alignment; falls back to a fuzzy match if the exact
    name (with any of the punctuation Panaroo uses for merged/paralog gene names) isn't found."""
    candidates = [ALN_DIR / f"{gene}.aln.fas", ALN_DIR / f"{gene}.fasta.aln.fas", ALN_DIR / f"{gene}.aln.fasta"]
    for c in candidates:
        if c.exists():
            return c
    safe = re.sub(r"[^A-Za-z0-9]", "_", gene)
    for c in ALN_DIR.glob(f"*{safe[:12]}*"):
        return c
    return None


def find_reference_row(aln_seqs, ref_seq):
    """Which aligned row IS the representative sequence (core_genes.fasta), matched by content, not by ID.
    Returns (header, aligned_string) or (None, None, note) with a note explaining a fuzzy fallback."""
    ref_upper = ref_seq.upper()
    for header, aligned in aln_seqs.items():
        if aligned.replace("-", "").upper() == ref_upper:
            return header, aligned, "exact"
    # fallback: closest match by ungapped sequence similarity
    best = max(aln_seqs.items(), key=lambda kv: difflib.SequenceMatcher(
        None, kv[1].replace("-", "").upper(), ref_upper).ratio())
    ratio = difflib.SequenceMatcher(None, best[1].replace("-", "").upper(), ref_upper).ratio()
    return best[0], best[1], f"fuzzy match ({ratio:.2%})"


def position_map(aligned_ref):
    """ungapped position (0-based) -> alignment column (0-based), for one aligned row."""
    m = []
    for col, ch in enumerate(aligned_ref):
        if ch != "-":
            m.append(col)
    return m


def column_conserved(aln_seqs, col):
    bases = [seq[col].upper() for seq in aln_seqs.values()]
    total = len(bases)
    if total == 0:
        return False
    counts = {}
    for b in bases:
        counts[b] = counts.get(b, 0) + 1
    best = max(counts.values())
    return (best / total) >= CONSERVED_THRESHOLD


def longest_conserved_run(aln_seqs, colmap, start0, end0):
    """start0/end0: 0-based inclusive ungapped positions (the exclusivity window). Returns (run_start0,
    run_end0, run_len) in ungapped reference coordinates, or None if nothing passes."""
    flags = [column_conserved(aln_seqs, colmap[p]) for p in range(start0, end0 + 1)]
    best = None
    run_start = None
    for i, ok in enumerate(flags + [False]):
        if ok and run_start is None:
            run_start = i
        if not ok and run_start is not None:
            length = i - run_start
            if best is None or length > best[2]:
                best = (start0 + run_start, start0 + i - 1, length)
            run_start = None
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-gap", type=int, default=150, help="minimum exclusivity gap from bin/07 to consider")
    ap.add_argument("--min-region", type=int, default=100, help="minimum conserved run to report as a candidate")
    args = ap.parse_args()

    if not ALN_DIR.exists():
        sys.exit(f"{ALN_DIR.relative_to(ROOT)} not found -- it's produced locally by bin/06's panaroo run "
                  f"but is not committed to git. Run bin/06 again if it's missing.")

    excl = read_tsv(EXCL / "core_gene_exclusivity.tsv")
    seqs = read_fasta(PAN / "core_genes.fasta")
    candidates = [r for r in excl if int(r["all_id85_maxgap"]) >= args.min_gap and r["all_id85_coords"]]
    print(f"== {len(candidates)} of {len(excl)} core genes have an exclusivity-clean gap >= {args.min_gap} bp (id85)")

    rows, fasta_out, no_aln, no_match, no_region = [], [], [], [], []
    for r in candidates:
        gene = r["gene"]
        ref_seq = seqs.get(gene)
        if not ref_seq:
            continue
        start_s, end_s = r["all_id85_coords"].split("-")
        start0, end0 = int(start_s) - 1, int(end_s) - 1

        aln_path = find_alignment_file(gene)
        if not aln_path:
            no_aln.append(gene)
            continue
        aln_seqs = read_fasta(aln_path)
        if not aln_seqs:
            no_aln.append(gene)
            continue
        header, aligned_ref, match_note = find_reference_row(aln_seqs, ref_seq)
        if match_note.startswith("fuzzy") and float(match_note.split("(")[1].rstrip("%)")) < 95:
            no_match.append((gene, match_note))
            continue
        colmap = position_map(aligned_ref)
        if end0 >= len(colmap):
            end0 = len(colmap) - 1
        if start0 > end0:
            continue

        best = longest_conserved_run(aln_seqs, colmap, start0, end0)
        if not best or best[2] < args.min_region:
            no_region.append(gene)
            continue
        rs0, re0, length = best
        region_seq = ref_seq[rs0:re0 + 1]
        rows.append({
            "gene": gene, "gene_name": r["gene_name"], "annotation": r["annotation"],
            "avg_copies": r["avg_copies"], "gene_length": r["length"],
            "excl_window": r["all_id85_coords"], "excl_gap_len": r["all_id85_maxgap"],
            "n_species_genus": r["n_species_genus"], "n_species_clinical": r["n_species_clinical"],
            "n_genomes_aligned": len(aln_seqs), "ref_match": match_note,
            "region_start": rs0 + 1, "region_end": re0 + 1, "region_length": length,
        })
        fasta_out.append((gene, rs0 + 1, re0 + 1, region_seq))

    rows.sort(key=lambda r: (-r["region_length"], -float(r["avg_copies"]) if False else 0, r["gene"]))
    # rank: longest conserved+exclusivity-clean region first, tie-break by single-copy genes then gene name
    rows.sort(key=lambda r: (-r["region_length"], abs(float(r["avg_copies"]) - 1.0), r["gene"]))

    OUT.mkdir(parents=True, exist_ok=True)
    if rows:
        with open(OUT / "candidate_regions.tsv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter="\t")
            w.writeheader()
            w.writerows(rows)
        order = {r["gene"]: i for i, r in enumerate(rows)}
        fasta_out.sort(key=lambda t: order[t[0]])
        with open(OUT / "candidate_regions.fasta", "w") as f:
            for gene, s, e, seq in fasta_out:
                f.write(f">{gene}_{s}-{e}\n")
                for i in range(0, len(seq), 70):
                    f.write(seq[i:i + 70] + "\n")

    print(f"\n== {len(rows)} candidate regions found (exclusivity-clean AND >= {args.min_region} bp of "
          f">= {CONSERVED_THRESHOLD:.0%} conserved sequence)")
    if no_aln:
        print(f"  {len(no_aln)} genes skipped: no alignment file found, e.g. {no_aln[:5]}")
    if no_match:
        print(f"  {len(no_match)} genes skipped: representative sequence not confidently found in its "
              f"alignment, e.g. {no_match[:3]}")
    if no_region:
        print(f"  {len(no_region)} genes had a big enough exclusivity gap but no conserved run "
              f">= {args.min_region} bp inside it")
    print(f"\n== top 15 candidate regions:")
    for r in rows[:15]:
        print(f"  {r['gene']:14s} region={r['region_length']:4d}bp ({r['region_start']}-{r['region_end']}) "
              f"copies={r['avg_copies']:>5s} genus_sp={r['n_species_genus']:2s} clinical_sp={r['n_species_clinical']:2s}  "
              f"{r['annotation'][:40]}")
    if rows:
        print(f"\nwrote {OUT.relative_to(ROOT)}/ (candidate_regions.tsv, candidate_regions.fasta)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
