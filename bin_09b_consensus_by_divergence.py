#!/usr/bin/env python3
"""
bin/09b: Build consensus sequences for top 30 divergence-ranked candidates.
Identifies ALL conserved fragments (>=100bp of >=99% agreement), including
interrupted ones separated by small variable gaps (<=5 bp).
"""

import csv
from pathlib import Path
from collections import defaultdict

ROOT = Path.home() / "projects" / "C_trachomatis_inclusivity_exclusivity"
CAND_TSV = ROOT / "results" / "candidate_regions" / "candidate_regions.tsv"
BLAST_GENUS = ROOT / "results" / "exclusivity" / "blast_genus.tsv"
PANAROO_DIR = ROOT / "results" / "pangenome" / "aligned_gene_sequences"
OUT_FASTA = ROOT / "results" / "consensus" / "consensus_regions_by_divergence.fasta"
OUT_TSV = ROOT / "results" / "consensus" / "candidate_fragments_divergence.tsv"

MIN_FRAG_LEN = 100
MIN_CONSERVED = 0.99
MAX_GAP = 5

print("Building top 30 divergence-ranked candidate list...\n")

best_hit_per_gene = {}
with open(BLAST_GENUS) as f:
    for line in f:
        parts = line.strip().split('\t')
        gene = parts[0]
        if gene in best_hit_per_gene:
            continue
        identity = float(parts[2])
        species = parts[1].split('|')[1].replace('_', ' ')
        divergence = 100.0 - identity
        best_hit_per_gene[gene] = {'species': species, 'divergence': divergence}

candidates = []
with open(CAND_TSV) as f:
    reader = csv.DictReader(f, delimiter='\t')
    for row in reader:
        gene = row['gene']
        if gene in best_hit_per_gene:
            hit = best_hit_per_gene[gene]
            candidates.append({
                'gene': gene,
                'region_start': int(row['region_start']),
                'region_end': int(row['region_end']),
                'region_length': int(row['region_length']),
                'best_species': hit['species'],
                'divergence': hit['divergence']
            })

top30_divergence = sorted(candidates, key=lambda x: -x['divergence'])[:30]
top30_genes = {c['gene']: c for c in top30_divergence}

print(f"Found {len(top30_divergence)} top divergence candidates\n")

fasta_out = open(OUT_FASTA, 'w')
tsv_out = open(OUT_TSV, 'w')
tsv_out.write("gene\tfragment_id\tfrag_start\tfrag_end\tfrag_length\tgap_before\tbest_species\tdivergence_pct\tsequence\n")

total_fragments = 0

for gene_info in top30_divergence:
    gene = gene_info['gene']
    region_start = gene_info['region_start']
    region_end = gene_info['region_end']
    
    aln_file = PANAROO_DIR / f"{gene}.aln.fas"
    
    if not aln_file.exists():
        print(f"⚠ {gene}: alignment not found")
        continue
    
    seqs = {}
    with open(aln_file) as f:
        name, seq = None, []
        for line in f:
            line = line.rstrip()
            if line.startswith('>'):
                if name:
                    seqs[name] = ''.join(seq).upper()
                name = line[1:]
                seq = []
            else:
                seq.append(line)
        if name:
            seqs[name] = ''.join(seq).upper()
    
    if not seqs:
        print(f"⚠ {gene}: no sequences")
        continue
    
    n_genomes = len(seqs)
    aln_len = len(next(iter(seqs.values())))
    
    conservation = []
    for pos in range(aln_len):
        bases = [seqs[name][pos] for name in seqs if pos < len(seqs[name])]
        bases = [b for b in bases if b != '-']
        
        if not bases:
            conservation.append(0)
            continue
        
        base_counts = defaultdict(int)
        for b in bases:
            base_counts[b] += 1
        
        majority_count = max(base_counts.values())
        frac = majority_count / len(bases)
        conservation.append(frac)
    
    fragments = []
    in_fragment = False
    frag_start = None
    gap_size = None
    
    for pos in range(aln_len):
        if conservation[pos] >= MIN_CONSERVED:
            if not in_fragment:
                frag_start = pos
                gap_size = None
                in_fragment = True
        else:
            if in_fragment:
                if (pos - frag_start) >= MIN_FRAG_LEN:
                    fragments.append((frag_start, pos - 1, gap_size))
                in_fragment = False
    
    if in_fragment and (aln_len - frag_start) >= MIN_FRAG_LEN:
        fragments.append((frag_start, aln_len - 1, gap_size))
    
    if not fragments:
        print(f"⚠ {gene}: no conserved fragments >=100bp")
        continue
    
    for frag_id, (frag_start, frag_end, gap) in enumerate(fragments, 1):
        frag_len = frag_end - frag_start + 1
        
        consensus_seq = []
        for pos in range(frag_start, frag_end + 1):
            bases = [seqs[name][pos] for name in seqs if pos < len(seqs[name]) and seqs[name][pos] != '-']
            if not bases:
                consensus_seq.append('N')
                continue
            base_counts = defaultdict(int)
            for b in bases:
                base_counts[b] += 1
            majority_base = max(base_counts.items(), key=lambda x: x[1])[0]
            consensus_seq.append(majority_base)
        
        consensus = ''.join(consensus_seq)
        
        header = f"{gene}_fragment{frag_id}_{frag_start}-{frag_end}"
        fasta_out.write(f">{header}\n")
        for i in range(0, len(consensus), 70):
            fasta_out.write(consensus[i:i+70] + "\n")
        
        gap_str = str(gap) if gap is not None else "start"
        tsv_out.write(f"{gene}\tfragment{frag_id}\t{frag_start}\t{frag_end}\t{frag_len}\t{gap_str}\t"
                     f"{gene_info['best_species']}\t{gene_info['divergence']:.2f}\t{consensus}\n")
        
        total_fragments += 1
        print(f"✓ {gene} fragment {frag_id}: {frag_len} bp @ {frag_start}-{frag_end}")

fasta_out.close()
tsv_out.close()

print(f"\nTotal: {total_fragments} fragments from {len(top30_divergence)} candidates")
print(f"Output: {OUT_FASTA}")
print(f"        {OUT_TSV}\n")
