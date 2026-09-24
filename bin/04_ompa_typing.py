#!/usr/bin/env python3
"""bin/04: extract ompA from every genome and check serovar (genovar) diversity.

Input : data/genomes_downloaded/<accession>.fna, genome_metadata.tsv (bin/01), provenance_audit.tsv (bin/02)
        data/reference/ompA_reference.fasta (fetched once from a reference genome's annotated CDS, see below)
Output: results/ompA/ompA_typing.tsv        per genome: ompA coordinates, identity to reference, serovar label,
                                            nearest-neighbour ompA type and whether it agrees
        results/ompA/ompA_sequences.fasta   extracted ompA sequences
        results/ompA/ompA_aligned.fasta     MAFFT alignment
        results/ompA/ompA_summary.txt       the printed summary

Method: BLAST the reference ompA against each genome, merge the hits into one locus, extend to the
reference length, extract, align with MAFFT and compute pairwise identity. Serovar labels come from
the BioSample serovar field or the strain name (e.g. "E/Bour" -> E). Each labelled genome is then
typed by its nearest neighbour among the OTHER labelled genomes; agreement between own label and
neighbour label shows the ompA extraction and the labels are consistent. No external genotype
database is used, so this is a diversity and consistency check, not formal genotyping.

Usage: bin/04_ompa_typing.py [--threads 4] [--ref-acc GCF_...]
"""
import argparse
import collections
import csv
import io
import re
import statistics
import subprocess
import sys
import zipfile
from pathlib import Path

from Bio import SeqIO
from Bio.Seq import Seq

ROOT = Path(__file__).resolve().parent.parent
INV = ROOT / "data" / "genome_inventory"
DL = ROOT / "data" / "genomes_downloaded"
REF = ROOT / "data" / "reference" / "ompA_reference.fasta"
OUT = ROOT / "results" / "ompA"
TIER = {"INCLUDE": "primary", "QUALITY_REVIEW": "quality-review", "REVIEW": "unresolved", "EXCLUDE": "excluded"}
LABELS = ["A", "B", "Ba", "C", "D", "Da", "E", "F", "G", "H", "I", "Ia", "J", "Ja", "K", "L1", "L2", "L2a", "L2b", "L2c", "L3"]
LABEL_RX = re.compile(r"^(L1|L2a|L2b|L2c|L3|L2|Ba|Da|Ia|Ja|[A-K])(?=$|[/\-_(\d\s])")
MIN_ALIGNED = 500


def read_tsv(path):
    return list(csv.DictReader(open(path), delimiter="\t"))


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def ensure_reference(meta, audit, ref_acc):
    if REF.exists():
        rec = next(SeqIO.parse(REF, "fasta"))
        print(f"  reference ompA: {rec.id} ({len(rec.seq)} nt) from {REF.relative_to(ROOT)}")
        return rec
    if not ref_acc:
        cands = [a for a, m in meta.items() if m["strain"].lower() == "d/uw-3/cx" and audit[a]["final_verdict"] == "INCLUDE"]
        if not cands:
            sys.exit("no D/UW-3/CX primary genome found; pass --ref-acc GCF_... or place data/reference/ompA_reference.fasta")
        ref_acc = sorted(cands)[0]
    print(f"  fetching annotated CDS of {ref_acc} to extract the ompA reference")
    zpath = ROOT / "results" / "ompA" / "ref_cds.zip"
    zpath.parent.mkdir(parents=True, exist_ok=True)
    p = run(["datasets", "download", "genome", "accession", ref_acc, "--include", "cds", "--filename", str(zpath)])
    if p.returncode != 0:
        sys.exit(f"datasets download failed: {p.stderr[:400]}")
    z = zipfile.ZipFile(zpath)
    name = next((n for n in z.namelist() if n.endswith("cds_from_genomic.fna")), None)
    if not name:
        sys.exit("no cds_from_genomic.fna in the download")
    best = None
    for rec in SeqIO.parse(io.StringIO(z.read(name).decode()), "fasta"):
        d = rec.description.lower()
        if ("[gene=ompa]" in d or "major outer membrane protein" in d) and 1000 <= len(rec.seq) <= 1400:
            best = rec
            break
    if best is None:
        sys.exit("ompA not found in the reference CDS file: place a reference at data/reference/ompA_reference.fasta")
    best.id, best.description = f"ompA_ref|{ref_acc}", ""
    REF.parent.mkdir(parents=True, exist_ok=True)
    SeqIO.write(best, REF, "fasta")
    zpath.unlink()
    print(f"  saved {REF.relative_to(ROOT)} ({len(best.seq)} nt)")
    return best


def serovar_label(m):
    s = m.get("serovar", "").strip()
    for lab in LABELS:
        if s.lower() == lab.lower():
            return lab
    strain = m.get("strain", "").strip()
    strain = re.sub(r"^RC-", "", strain)
    mt = LABEL_RX.match(strain)
    if mt:
        return mt.group(1)
    if "LGV II" in strain or "LGV2" in strain:
        return "L2"
    return ""


def group_of(label):
    return re.sub(r"[a-z]$", "", label) if label else ""


def extract(acc, ref_rec, threads=1):
    fna = DL / f"{acc}.fna"
    qlen = len(ref_rec.seq)
    p = run(["blastn", "-task", "blastn", "-query", str(REF), "-subject", str(fna), "-evalue", "1e-20",
             "-outfmt", "6 sseqid sstart send pident length qstart qend bitscore"])
    hsps = []
    for line in p.stdout.splitlines():
        sid, ss, se, pid, ln, qs, qe, bs = line.split("\t")
        hsps.append((sid, int(ss), int(se), float(pid), int(ln), int(qs), int(qe), float(bs)))
    if not hsps:
        return None
    top = max(hsps, key=lambda h: h[7])
    strand = "+" if top[1] <= top[2] else "-"
    same = [h for h in hsps if h[0] == top[0] and (h[1] <= h[2]) == (strand == "+")
            and max(min(h[1], h[2]), min(top[1], top[2])) - min(max(h[1], h[2]), max(top[1], top[2])) < 500]
    lo = min(min(h[1], h[2]) for h in same)
    hi = max(max(h[1], h[2]) for h in same)
    qmin, qmax = min(h[5] for h in same), max(h[6] for h in same)
    left, right = (qmin - 1, qlen - qmax) if strand == "+" else (qlen - qmax, qmin - 1)
    contig = SeqIO.to_dict(SeqIO.parse(fna, "fasta"))[top[0]]
    a, b = max(1, lo - left), min(len(contig.seq), hi + right)
    seq = contig.seq[a - 1:b]
    if strand == "-":
        seq = seq.reverse_complement()
    aligned_q = sum(h[6] - h[5] + 1 for h in same)
    ident = sum(h[3] * (h[6] - h[5] + 1) for h in same) / aligned_q
    return {"contig": top[0], "start": a, "end": b, "strand": strand, "seq": str(seq).upper(),
            "identity_to_ref": ident, "coverage": min(1.0, aligned_q / qlen)}


def identity(a, b):
    same = tot = 0
    for x, y in zip(a, b):
        if x != "-" and y != "-":
            tot += 1
            same += x == y
    return (100.0 * same / tot) if tot >= MIN_ALIGNED else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--ref-acc", default="")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    meta = {r["accession"]: r for r in read_tsv(INV / "genome_metadata.tsv")}
    audit = {r["accession"]: r for r in read_tsv(INV / "provenance_audit.tsv")}
    accs = sorted(meta)
    tier = {a: TIER[audit[a]["final_verdict"]] for a in accs}
    print(f"== ompA extraction from {len(accs)} genomes")
    ref = ensure_reference(meta, audit, args.ref_acc)

    found, failed = {}, []
    for a in accs:
        r = extract(a, ref)
        if r is None or r["coverage"] < 0.8 or len(r["seq"]) < 900:
            failed.append(a)
        else:
            found[a] = r
    print(f"  extracted ompA from {len(found)}/{len(accs)} genomes; failed: "
          f"{[(a, meta[a]['strain']) for a in failed] or 'none'}")
    ids = [a for a in accs if a in found]
    SeqIO.write([SeqIO.SeqRecord(Seq(found[a]["seq"]), id=a, description=meta[a]["strain"]) for a in ids],
                OUT / "ompA_sequences.fasta", "fasta")
    p = run(["mafft", "--auto", "--thread", str(args.threads), str(OUT / "ompA_sequences.fasta")])
    if p.returncode != 0 or not p.stdout.strip():
        sys.exit(f"mafft failed: {p.stderr[-400:]}")
    (OUT / "ompA_aligned.fasta").write_text(p.stdout)
    aln = {rec.id: str(rec.seq).upper() for rec in SeqIO.parse(io.StringIO(p.stdout), "fasta")}

    label = {a: serovar_label(meta[a]) for a in ids}
    labelled = [a for a in ids if label[a]]
    print(f"  serovar label available for {len(labelled)}/{len(ids)} genomes (BioSample serovar or strain name)")

    label_count = collections.Counter(label[a] for a in labelled)
    rows, ident_cache = [], {}
    def ident(a, b):
        k = (a, b) if a < b else (b, a)
        if k not in ident_cache:
            ident_cache[k] = identity(aln[a], aln[b])
        return ident_cache[k]

    for a in ids:
        best, best_labels, nn = -1.0, set(), ""
        for b in labelled:
            if b == a:
                continue
            v = ident(a, b)
            if v is None:
                continue
            if v > best + 1e-9:
                best, best_labels, nn = v, {label[b]}, b
            elif abs(v - best) <= 1e-9:
                best_labels.add(label[b])
        pred = "/".join(sorted(best_labels))
        own = label[a]
        if not own:
            agrees = ""
        elif label_count[own] == 1:
            agrees = "singleton"  # no other genome carries this label, so leave-one-out typing cannot test it
        elif own in best_labels:
            agrees = "yes"
        elif group_of(own) in {group_of(x) for x in best_labels}:
            agrees = "group"
        else:
            agrees = "NO"
        f = found[a]
        rows.append({"accession": a, "strain": meta[a]["strain"], "tier": tier[a], "contig": f["contig"], "start": f["start"],
                     "end": f["end"], "strand": f["strand"], "length": len(f["seq"]),
                     "identity_to_ref": f"{f['identity_to_ref']:.2f}", "coverage": f"{f['coverage']:.2f}",
                     "own_label": own, "nn_label": pred, "nn_identity": f"{best:.2f}" if best >= 0 else "",
                     "nn_accession": nn, "agrees": agrees})
    for a in failed:
        rows.append({"accession": a, "strain": meta[a]["strain"], "tier": tier[a], "contig": "", "start": "", "end": "",
                     "strand": "", "length": "", "identity_to_ref": "", "coverage": "", "own_label": "", "nn_label": "",
                     "nn_identity": "", "nn_accession": "", "agrees": "EXTRACTION_FAILED"})
    with open(OUT / "ompA_typing.tsv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()), delimiter="\t")
        w.writeheader()
        w.writerows(rows)

    L = []
    for t in ("primary", "quality-review", "excluded"):
        sel = [r for r in rows if r["tier"] == t and r["identity_to_ref"]]
        if sel:
            pid = [float(r["identity_to_ref"]) for r in sel]
            L.append(f"  {t:<15} n={len(sel):<3} identity to reference: min {min(pid):.1f}, median {statistics.median(pid):.1f}; "
                     f"lengths {min(int(r['length']) for r in sel)}-{max(int(r['length']) for r in sel)}")
    prim = [r for r in rows if r["tier"] == "primary" and r["identity_to_ref"]]
    distinct = len({found[r["accession"]]["seq"] for r in prim})
    L.append(f"\n  distinct ompA sequences among {len(prim)} primary genomes: {distinct}")
    counts = collections.Counter((r["own_label"] or (r["nn_label"] + "?")) for r in prim)
    L.append("  primary genomes by serovar (a trailing ? means predicted from the nearest neighbour, no label of its own):")
    L.append("   " + ", ".join(f"{k}:{v}" for k, v in sorted(counts.items())))
    distinct_groups = {group_of(k.rstrip("?")) for k in counts if k.rstrip("?") and "/" not in k}
    L.append(f"  distinct serovar groups in the primary set: {len(distinct_groups)} -> "
             f"{'PASS' if len(distinct_groups) >= 8 else 'BELOW'} the handover checkpoint of at least 8")
    lab = [r for r in rows if r["agrees"] in ("yes", "group", "NO")]
    L.append(f"  label vs nearest-neighbour ompA type (labels shared by 2+ genomes): exact {sum(r['agrees'] == 'yes' for r in lab)}, "
             f"same group {sum(r['agrees'] == 'group' for r in lab)}, disagree {sum(r['agrees'] == 'NO' for r in lab)} of {len(lab)}; "
             f"untestable singletons: {sum(r['agrees'] == 'singleton' for r in rows)}")
    for r in rows:
        if r["agrees"] in ("NO", "group"):
            L.append(f"    {r['agrees']:<5} {r['accession']} {r['strain'][:22]:<22} {r['tier']:<14} label {r['own_label']:<4} "
                     f"nearest {r['nn_label']} ({r['nn_identity']}%)")
    text = "\n".join(L)
    (OUT / "ompA_summary.txt").write_text(text + "\n")
    print(text)
    print(f"\nwrote {OUT.relative_to(ROOT)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
