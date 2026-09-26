#!/usr/bin/env python3
"""Extract top 15 fragments by size for web-BLAST validation."""

import csv
from pathlib import Path

ROOT = Path.home() / "projects" / "C_trachomatis_inclusivity_exclusivity"
TSV_FILE = ROOT / "results" / "consensus" / "candidate_fragments_divergence.tsv"
FASTA_FILE = ROOT / "results" / "consensus" / "consensus_regions_by_divergence.fasta"
OUT_FASTA = ROOT / "results" / "consensus" / "top15_for_blast.fasta"
OUT_TABLE = ROOT / "results" / "consensus" / "top15_for_blast.tsv"

# Read TSV and sort by fragment length (descending)
fragments = []
with open(TSV_FILE) as f:
    reader = csv.DictReader(f, delimiter='\t')
    for row in reader:
        fragments.append({
            'gene': row['gene'],
            'fragment_id': row['fragment_id'],
            'frag_start': int(row['frag_start']),
            'frag_end': int(row['frag_end']),
            'frag_length': int(row['frag_length']),
            'best_species': row['best_species'],
            'divergence_pct': float(row['divergence_pct']),
            'sequence': row['sequence']
        })

# Sort by length (largest first)
fragments_sorted = sorted(fragments, key=lambda x: -x['frag_length'])
top15 = fragments_sorted[:15]

print(f"TOP 15 FRAGMENTS BY SIZE FOR BLAST VALIDATION\n")
print(f"{'Rank':>3} {'Gene':15} {'Fragment':12} {'Size':>6} {'Species':25} {'Divergence%':>12}")
print("-" * 80)

# Write FASTA and table
with open(OUT_FASTA, 'w') as fasta_out:
    with open(OUT_TABLE, 'w') as tsv_out:
        tsv_out.write("rank\tgene\tfragment_id\tfrag_length\tbest_species\tdivergence_pct\tsequence\n")
        
        for rank, frag in enumerate(top15, 1):
            # Print summary
            print(f"{rank:3d} {frag['gene'][:14]:15} {frag['fragment_id']:12} {frag['frag_length']:6d} "
                  f"{frag['best_species'][:24]:25} {frag['divergence_pct']:12.2f}")
            
            # Write FASTA
            header = f"{frag['gene']}_{frag['fragment_id']}_{frag['frag_start']}-{frag['frag_end']} [rank {rank}; {frag['frag_length']}bp; {frag['divergence_pct']:.1f}% divergence from {frag['best_species']}]"
            fasta_out.write(f">{header}\n")
            seq = frag['sequence']
            for i in range(0, len(seq), 70):
                fasta_out.write(seq[i:i+70] + "\n")
            
            # Write TSV
            tsv_out.write(f"{rank}\t{frag['gene']}\t{frag['fragment_id']}\t{frag['frag_length']}\t"
                         f"{frag['best_species']}\t{frag['divergence_pct']:.2f}\t{frag['sequence']}\n")

print(f"\n{'='*80}")
print(f"Output FASTA: {OUT_FASTA}")
print(f"Output TSV:   {OUT_TABLE}")
print(f"Ready for web-BLAST validation against NCBI nt (exclude C. trachomatis txid813)")
print(f"{'='*80}\n")
