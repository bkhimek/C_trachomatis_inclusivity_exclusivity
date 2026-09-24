#!/usr/bin/env python3
"""bin/01: build the RefSeq complete C. trachomatis genome inventory and download the genomes.

Steps
  1. Query NCBI Datasets for RefSeq complete assemblies of taxon 813 (C. trachomatis).
     Raw records are kept in data/genome_inventory/assembly_reports.jsonl (audit trail).
  2. Flatten the records to data/genome_inventory/genome_metadata.tsv (input of bin/02).
  3. Download the genomes, verify md5 checksums and sequence lengths against NCBI's reported
     length, and write data/genome_inventory/genome_files.tsv.

Usage: bin/01_download_refseq_genomes.py [--refresh] [--skip-download]
  --refresh        re-query NCBI even if assembly_reports.jsonl exists (reports what changed)
  --skip-download  build the inventory only

The set is NOT forced to a fixed size: the expected count is only reported for comparison.
"""
import argparse
import csv
import hashlib
import json
import subprocess
import sys
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INV = ROOT / "data" / "genome_inventory"
DL = ROOT / "data" / "genomes_downloaded"
REPORTS = INV / "assembly_reports.jsonl"
ACC_FILE = INV / "refseq_complete_accessions.txt"
META = INV / "genome_metadata.tsv"
FILES = INV / "genome_files.tsv"
TAXON = "813"
EXPECTED = 125  # from the handover; compared, never enforced
PLASMID_MAX_LEN = 20000

META_COLS = [
    "accession", "paired_genbank", "assembly_name", "organism_name", "strain", "isolate", "serovar",
    "biosample", "bioproject", "bioproject_all", "bioproject_titles", "submitter", "release_date",
    "sequencing_tech", "assembly_method", "assembly_level", "assembly_status", "source_database",
    "total_length", "gc_percent", "n_contigs", "n_chromosomes", "collection_date", "geo_loc_name",
    "host", "isolation_source", "host_disease", "ani_status", "ani_match", "checkm_completeness",
    "checkm_contamination", "biosample_text",
]


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def g(d, *path, default=""):
    for k in path:
        if not isinstance(d, dict):
            return default
        d = d.get(k)
        if d is None:
            return default
    return d


def load_reports(path=REPORTS):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def query_reports():
    old = {r["accession"] for r in load_reports()} if REPORTS.exists() else set()
    p = run(["datasets", "summary", "genome", "taxon", TAXON, "--assembly-source", "RefSeq",
             "--assembly-level", "complete", "--as-json-lines"])
    if p.returncode != 0 or not p.stdout.strip():
        sys.exit(f"datasets summary failed: {p.stderr[:500]}")
    REPORTS.write_text(p.stdout)
    new = {r["accession"] for r in load_reports()}
    if old:
        print(f"  changes vs previous query: added {sorted(new - old)}, removed {sorted(old - new)}")


def clean(v):
    return str(v).replace("\t", " ").replace("\n", " ").replace("\r", " ").strip()


def flatten(r):
    info = r.get("assembly_info", {}) or {}
    bs = info.get("biosample", {}) or {}
    st = r.get("assembly_stats", {}) or {}
    org = r.get("organism", {}) or {}
    ani = r.get("average_nucleotide_identity", {}) or {}
    ck = r.get("checkm_info", {}) or {}
    attrs = {a.get("name"): a.get("value") for a in (bs.get("attributes") or []) if a.get("name")}

    pairs = []
    for lin in info.get("bioproject_lineage") or []:
        for bp in lin.get("bioprojects") or []:
            pairs.append((bp.get("accession", ""), bp.get("title", "")))
    primary = info.get("bioproject_accession") or (pairs[0][0] if pairs else "")
    all_bps = []
    titles = []
    for acc, title in pairs:
        if acc and acc not in all_bps:
            all_bps.append(acc)
        if title and title not in titles:
            titles.append(title)
    if primary and primary not in all_bps:
        all_bps.append(primary)

    strain = g(org, "infraspecific_names", "strain") or attrs.get("strain", "") or bs.get("isolate", "")
    text_parts = [f"{k}={v}" for k, v in attrs.items()]
    title = g(bs, "description", "title")
    if title:
        text_parts.append(f"title={title}")
    comments = info.get("comments", "")
    if comments:
        text_parts.append(f"comments={comments}")

    row = {
        "accession": r.get("accession", ""),
        "paired_genbank": r.get("paired_accession", "") or g(info, "paired_assembly", "accession"),
        "assembly_name": info.get("assembly_name", ""),
        "organism_name": org.get("organism_name", ""),
        "strain": strain,
        "isolate": bs.get("isolate", ""),
        "serovar": bs.get("serovar", ""),
        "biosample": bs.get("accession", ""),
        "bioproject": primary,
        "bioproject_all": ";".join(all_bps),
        "bioproject_titles": " | ".join(titles),
        "submitter": info.get("submitter", ""),
        "release_date": info.get("release_date", ""),
        "sequencing_tech": info.get("sequencing_tech", ""),
        "assembly_method": info.get("assembly_method", ""),
        "assembly_level": info.get("assembly_level", ""),
        "assembly_status": info.get("assembly_status", ""),
        "source_database": r.get("source_database", ""),
        "total_length": st.get("total_sequence_length", ""),
        "gc_percent": st.get("gc_percent", ""),
        "n_contigs": st.get("number_of_contigs", ""),
        "n_chromosomes": st.get("total_number_of_chromosomes", ""),
        "collection_date": bs.get("collection_date", ""),
        "geo_loc_name": bs.get("geo_loc_name", ""),
        "host": bs.get("host", ""),
        "isolation_source": bs.get("isolation_source", ""),
        "host_disease": attrs.get("host_disease", ""),
        "ani_status": ani.get("taxonomy_check_status", ""),
        "ani_match": ani.get("match_status", ""),
        "checkm_completeness": ck.get("completeness", ""),
        "checkm_contamination": ck.get("contamination", ""),
        "biosample_text": "; ".join(text_parts)[:800],
    }
    return {k: clean(v) for k, v in row.items()}


def fasta_lengths(path):
    lens, cur = [], 0
    with open(path) as f:
        for line in f:
            if line.startswith(">"):
                if cur:
                    lens.append(cur)
                cur = 0
            else:
                cur += len(line.strip())
    if cur:
        lens.append(cur)
    return lens


def download(accs, reported_len):
    DL.mkdir(parents=True, exist_ok=True)
    bundle = DL / "ncbi_bundle.zip"
    for attempt in range(1, 4):
        p = run(["datasets", "download", "genome", "accession", "--inputfile", str(ACC_FILE),
                 "--include", "genome", "--filename", str(bundle)])
        if p.returncode == 0 and bundle.exists():
            break
        print(f"  download attempt {attempt} failed: {p.stderr[:300]}")
        time.sleep(10 * attempt)
    else:
        sys.exit("download failed after 3 attempts")

    z = zipfile.ZipFile(bundle)
    names = z.namelist()
    md5s = {}
    for n in names:
        if n.endswith("md5sum.txt"):
            for line in z.read(n).decode().splitlines():
                parts = line.split(None, 1)
                if len(parts) == 2:
                    md5s[parts[1].strip().lstrip("*")] = parts[0]
    rows = []
    for n in names:
        if not n.endswith(".fna"):
            continue
        acc = Path(n).parent.name
        dest = DL / f"{acc}.fna"
        h = hashlib.md5()
        with z.open(n) as src, open(dest, "wb") as out:
            for chunk in iter(lambda: src.read(1 << 20), b""):
                h.update(chunk)
                out.write(chunk)
        expected = md5s.get(n)
        md5_ok = "NA" if expected is None else str(h.hexdigest() == expected)
        lens = fasta_lengths(dest)
        total = sum(lens)
        rep = reported_len.get(acc, "")
        rows.append({
            "accession": acc, "file": dest.name, "md5_ok": md5_ok, "n_sequences": len(lens),
            "total_len": total, "reported_len": rep,
            "length_match": str(str(total) == str(rep)),
            "longest_seq": max(lens) if lens else 0,
            "small_replicons": sum(1 for x in lens if x < PLASMID_MAX_LEN),
        })
    rows.sort(key=lambda x: x["accession"])
    with open(FILES, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter="\t")
        w.writeheader()
        w.writerows(rows)

    got = {r["accession"] for r in rows}
    print(f"  downloaded {len(got)}/{len(accs)} genomes; missing: {sorted(set(accs) - got) or 'none'}")
    print(f"  md5 failures: {[r['accession'] for r in rows if r['md5_ok'] == 'False'] or 'none'}"
          f" | md5 not checkable: {sum(r['md5_ok'] == 'NA' for r in rows)}")
    print(f"  length mismatches vs NCBI report: {[r['accession'] for r in rows if r['length_match'] == 'False'] or 'none'}")
    print(f"  genomes with a small replicon (<{PLASMID_MAX_LEN} nt, likely plasmid): "
          f"{sum(r['small_replicons'] > 0 for r in rows)}/{len(rows)}")
    dist = {}
    for r in rows:
        dist[r["n_sequences"]] = dist.get(r["n_sequences"], 0) + 1
    print(f"  sequences per genome file: {dict(sorted(dist.items()))}")
    bad = [r for r in rows if r["md5_ok"] == "False" or r["length_match"] == "False"]
    return len(got) == len(accs) and not bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--skip-download", action="store_true")
    args = ap.parse_args()
    INV.mkdir(parents=True, exist_ok=True)

    if args.refresh or not REPORTS.exists():
        print("== Querying NCBI Datasets")
        query_reports()
    recs = load_reports()
    print(f"== {len(recs)} RefSeq complete records (handover expected {EXPECTED}"
          f"{'' if len(recs) == EXPECTED else ' -> DIFFERENT, see docs/PROJECT_STATE.md D1'})")
    rows = sorted((flatten(r) for r in recs), key=lambda x: x["accession"])
    accs = [r["accession"] for r in rows]
    ACC_FILE.write_text("\n".join(accs) + "\n")
    with open(META, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=META_COLS, delimiter="\t")
        w.writeheader()
        w.writerows(rows)
    print(f"  wrote {META.relative_to(ROOT)} ({len(rows)} rows), {ACC_FILE.relative_to(ROOT)}")

    if args.skip_download:
        return 0
    print("== Downloading genomes")
    ok = download(accs, {r["accession"]: r["total_length"] for r in rows})
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
