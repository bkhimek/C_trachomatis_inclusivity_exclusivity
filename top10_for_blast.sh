#!/bin/bash
# Quick one-liner to extract top 10 consensus regions by gap size and print as FASTA

cd ~/projects/C_trachomatis_inclusivity_exclusivity

python3 << 'SCRIPT'
import csv
from pathlib import Path

ROOT = Path.home() / "projects" / "C_trachomatis_inclusivity_exclusivity"
CAND = ROOT / "results" / "candidate_regions" / "candidate_regions.tsv"
CONS_FASTA = ROOT / "results" / "consensus" / "consensus_regions.fasta"

# Read candidates sorted by gap
rows = list(csv.DictReader(open(CAND), delimiter="\t"))
rows.sort(key=lambda r: -int(r["excl_gap_len"]))
top10 = rows[:10]

# Read consensus FASTA
seqs = {}
name, buf = None, []
for line in open(CONS_FASTA):
    line = line.rstrip("\n")
    if line.startswith(">"):
        if name:
            seqs[name] = "".join(buf)
        name = line[1:]
        buf = []
    else:
        buf.append(line.strip())
if name:
    seqs[name] = "".join(buf)

# Output table + FASTA
print("TOP 10 CONSENSUS REGIONS BY EXCLUSIVITY GAP (id85)\n")
print("Rank  Gene            Gap(bp)  Len(bp)  Region      Copies  Annotation")
print("=" * 80)

for i, r in enumerate(top10, 1):
    gene = r["gene"]
    gap = r["excl_gap_len"]
    length = r["region_length"]
    copies = r["avg_copies"]
    annot = r["annotation"][:35]
    region = f"{r['region_start']}-{r['region_end']}"

    header = f"{gene}_{region}"
    seq = seqs.get(header, "")

    print(f"{i:2d}.   {gene[:14]:14s} {gap:6s}  {length:6s}  {region:11s} {copies:>5s}  {annot}")

print("\n" + "=" * 80)
print("\nFASTA SEQUENCES FOR BLAST:\n")

for i, r in enumerate(top10, 1):
    gene = r["gene"]
    region = f"{r['region_start']}-{r['region_end']}"
    header = f"{gene}_{region}"
    seq = seqs.get(header, "")

    if seq:
        print(f">{header}  [rank {i}; gap {r['excl_gap_len']}bp; {r['annotation'][:40]}]")
        for j in range(0, len(seq), 70):
            print(seq[j:j+70])
        print()

SCRIPT
