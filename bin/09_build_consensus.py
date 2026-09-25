#!/usr/bin/env python3
"""bin/09: build the population-consensus sequence for the top candidate regions from bin/08.

Input : results/candidate_regions/candidate_regions.tsv   ranked candidates (bin/08)
        results/pangenome/core_genes.fasta                representative sequence per core gene (bin/06)
        results/pangenome/aligned_gene_sequences/*.aln.fas  Panaroo's per-gene alignments (from bin/06,
                                                            local disk only, not committed to git)
Output: results/consensus/consensus_regions.fasta   majority-base consensus per selected region (committed)
        results/consensus/consensus_variability.tsv per-position report, non-invariant positions only (committed)

bin/08's region FASTA uses one representative genome's own sequence. That genome can carry a minority
base at a position that is still >=99% conserved (up to 1% of genomes may disagree there). This script
instead computes the true majority base at every position across all genomes carrying the gene, which is
what the Primer3 design step should use.

Usage: bin/09_build_consensus.py [--top 30]
"""
import argparse
import collections
import csv
import difflib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAND = ROOT / "results" / "candidate_regions"
PAN = ROOT / "results" / "pangenome"
ALN_DIR = PAN / "aligned_gene_sequences"
OUT = ROOT / "results" / "consensus"


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
    candidates = [ALN_DIR / f"{gene}.aln.fas", ALN_DIR / f"{gene}.fasta.aln.fas", ALN_DIR / f"{gene}.aln.fasta"]
    for c in candidates:
        if c.exists():
            return c
    safe = re.sub(r"[^A-Za-z0-9]", "_", gene)
    for c in ALN_DIR.glob(f"*{safe[:12]}*"):
        return c
    return None


def find_reference_row(aln_seqs, ref_seq):
    ref_upper = ref_seq.upper()
    for header, aligned in aln_seqs.items():
        if aligned.replace("-", "").upper() == ref_upper:
            return header, aligned
    best = max(aln_seqs.items(), key=lambda kv: difflib.SequenceMatcher(
        None, kv[1].replace("-", "").upper(), ref_upper).ratio())
    return best


def position_map(aligned_ref):
    return [col for col, ch in enumerate(aligned_ref) if ch != "-"]


def majority(bases):
    counts = collections.Counter(b.upper() for b in bases)
    base, n = counts.most_common(1)[0]
    return base, n, len(bases), counts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=30, help="how many top-ranked candidates to build consensus for")
    args = ap.parse_args()

    rows = read_tsv(CAND / "candidate_regions.tsv")
    shortlist = rows[:args.top]
    seqs = read_fasta(PAN / "core_genes.fasta")
    print(f"== building consensus for the top {len(shortlist)} of {len(rows)} candidate regions")

    fasta_out, var_rows, skipped = [], [], []
    for r in shortlist:
        gene = r["gene"]
        ref_seq = seqs.get(gene)
        aln_path = find_alignment_file(gene)
        if not ref_seq or not aln_path:
            skipped.append(gene)
            continue
        aln_seqs = read_fasta(aln_path)
        if not aln_seqs:
            skipped.append(gene)
            continue
        header, aligned_ref = find_reference_row(aln_seqs, ref_seq)
        colmap = position_map(aligned_ref)
        start0, end0 = int(r["region_start"]) - 1, int(r["region_end"]) - 1
        if end0 >= len(colmap):
            skipped.append(gene)
            continue

        cons_bases, n_variant = [], 0
        for pos in range(start0, end0 + 1):
            col = colmap[pos]
            bases = [s[col].upper() for s in aln_seqs.values()]
            base, n, total, counts = majority(bases)
            cons_bases.append(base if base != "-" else "N")
            if len(counts) > 1:
                n_variant += 1
                alts = ", ".join(f"{b}:{c}" for b, c in counts.most_common() if b != base)
                var_rows.append({
                    "gene": gene, "region_pos_1based": pos - start0 + 1, "majority_base": base,
                    "majority_count": n, "n_genomes": total, "majority_frac": f"{n / total:.4f}",
                    "alt_alleles": alts,
                })
        cons_seq = "".join(cons_bases)
        fasta_out.append((gene, r["region_start"], r["region_end"], cons_seq))
        if n_variant:
            print(f"  {gene:14s} {len(cons_seq):4d} bp, {n_variant} position(s) with minor variation "
                  f"(still >=99% conserved by construction)")

    OUT.mkdir(parents=True, exist_ok=True)
    with open(OUT / "consensus_regions.fasta", "w") as f:
        for gene, s, e, seq in fasta_out:
            f.write(f">{gene}_{s}-{e}\n")
            for i in range(0, len(seq), 70):
                f.write(seq[i:i + 70] + "\n")
    if var_rows:
        with open(OUT / "consensus_variability.tsv", "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(var_rows[0].keys()), delimiter="\t")
            w.writeheader()
            w.writerows(var_rows)
    else:
        (OUT / "consensus_variability.tsv").write_text(
            "gene\tregion_pos_1based\tmajority_base\tmajority_count\tn_genomes\tmajority_frac\talt_alleles\n")

    print(f"\n== {len(fasta_out)} consensus regions written; {len(skipped)} skipped "
          f"(missing alignment or out-of-range): {skipped[:5]}")
    fully_invariant = sum(1 for gene, *_ in fasta_out if not any(v["gene"] == gene for v in var_rows))
    print(f"== {fully_invariant} of {len(fasta_out)} regions are 100% invariant across all genomes carrying the gene")
    print(f"\nwrote {OUT.relative_to(ROOT)}/ (consensus_regions.fasta, consensus_variability.tsv)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
