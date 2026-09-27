#!/usr/bin/env python3
"""
bin/12_extract_plasmid_contigs.py

Extract the plasmid contig (the shorter of two FASTA records) from the 34
already-downloaded RefSeq C. trachomatis genome assemblies that carry a small
second replicon, per data/genome_inventory/genome_files.tsv (small_replicons==1,
written by bin/01 at download time -- independent of anything in the plasmid
handover).

Why these 34, and not a fresh 128-genome plasmid curation: PLASMID_OLIGO_DESIGN_
HANDOVER.md (2026-09-27) claimed a separately-curated 128-plasmid RefSeq set
already existed and was aligned/consensus-built. It does not -- checked directly:
data/plasmid_inventory/, data/plasmids_downloaded/, results/oligos_plasmid/ are
all empty placeholders. These 34 genomes are real, already on disk, and their
second replicon is consistently 7,415-7,510 bp -- matching the well-documented
~7.5 kb C. trachomatis plasmid size -- so this is the fastest path to real
plasmid sequence data. See docs/PROJECT_STATE.md, 2026-09-27 plasmid-investigation
update, for the full story.

Input:  data/genomes_downloaded/<accession>.fna  (must already exist locally --
        NOT committed to git, NOT synced to OneDrive; this is why this script
        must be run in WSL, not by the cloud assistant)
Output: data/plasmids_downloaded/<accession>_plasmid.fna    (one file per genome)
        data/plasmids_downloaded/plasmids_34_combined.fasta (all extracted, for
                                                               a MAFFT alignment
                                                               step next)
        A printed summary table (accession, tier, n_seqs_in_file, plasmid_len, flag)

Run from the repo root:
    python bin/12_extract_plasmid_contigs.py
"""
import csv
from pathlib import Path

from Bio import SeqIO

REPO = Path(__file__).resolve().parents[1]
GENOMES_DIR = REPO / "data" / "genomes_downloaded"
OUT_DIR = REPO / "data" / "plasmids_downloaded"
GENOME_FILES_TSV = REPO / "data" / "genome_inventory" / "genome_files.tsv"
FINAL_TSV = REPO / "data" / "genome_inventory" / "genome_inventory_final.tsv"

EXPECTED_N = 34
PLASMID_MIN_BP = 7000
PLASMID_MAX_BP = 8000


def load_tier():
    tier = {}
    with open(FINAL_TSV) as f:
        for row in csv.DictReader(f, delimiter="\t"):
            tier[row["accession"]] = row.get("tier", "")
    return tier


def load_flagged_accessions():
    accessions = []
    with open(GENOME_FILES_TSV) as f:
        for row in csv.DictReader(f, delimiter="\t"):
            if row.get("small_replicons") == "1":
                accessions.append((row["accession"], row["file"]))
    return accessions


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tier = load_tier()
    accessions = load_flagged_accessions()

    print(f"Found {len(accessions)} genomes flagged small_replicons==1 in genome_files.tsv")
    if len(accessions) != EXPECTED_N:
        print(
            f"WARNING: expected {EXPECTED_N} (per the 2026-09-27 project-state finding); "
            f"got {len(accessions)}. genome_files.tsv may have changed since that finding was "
            f"written -- re-check docs/PROJECT_STATE.md before trusting the rest of this run.\n"
        )
    else:
        print()

    combined_records = []
    rows_out = []
    missing = []

    for acc, fname in accessions:
        fpath = GENOMES_DIR / fname
        if not fpath.exists():
            missing.append((acc, fname))
            continue

        records = list(SeqIO.parse(fpath, "fasta"))
        if len(records) != 2:
            rows_out.append(
                (acc, tier.get(acc, "?"), len(records), "N/A", f"FLAG: expected 2 seqs, found {len(records)}")
            )
            continue

        records.sort(key=lambda r: len(r.seq))
        plasmid_rec, chrom_rec = records[0], records[1]
        plen = len(plasmid_rec.seq)

        if PLASMID_MIN_BP <= plen <= PLASMID_MAX_BP:
            flag = "ok"
        else:
            flag = f"FLAG: {plen}bp outside expected {PLASMID_MIN_BP}-{PLASMID_MAX_BP}bp plasmid range"

        plasmid_rec.id = f"{acc}_plasmid"
        plasmid_rec.description = (
            f"{acc} plasmid contig, {plen}bp, extracted from {fname} "
            f"(chromosome contig in same file was {len(chrom_rec.seq)}bp)"
        )
        SeqIO.write(plasmid_rec, OUT_DIR / f"{acc}_plasmid.fna", "fasta")
        combined_records.append(plasmid_rec)
        rows_out.append((acc, tier.get(acc, "?"), len(records), plen, flag))

    if combined_records:
        SeqIO.write(combined_records, OUT_DIR / "plasmids_34_combined.fasta", "fasta")

    print(f"{'accession':<18}{'tier':<16}{'n_seqs':<8}{'plasmid_len':<14}{'flag'}")
    for r in rows_out:
        print(f"{r[0]:<18}{r[1]:<16}{r[2]:<8}{str(r[3]):<14}{r[4]}")

    if missing:
        print(f"\n{len(missing)} genome file(s) not found under {GENOMES_DIR}:")
        for acc, fname in missing:
            print(f"  {acc}\t{fname}")
        print(
            "(If these files were downloaded to a different path by bin/01, point GENOMES_DIR at it and re-run.)"
        )

    print(f"\nExtracted {len(combined_records)} plasmid contigs -> {OUT_DIR / 'plasmids_34_combined.fasta'}")


if __name__ == "__main__":
    main()
