#!/usr/bin/env python3
"""bin/18: do the 7 locked chromosomal oligo sets still bind the 10 quality-review genomes?

Closes the D13 check that D26 had set aside (user chose to run it, 2026-10-02).

Why: per D13 the quality-review tier is kept out of Panaroo and the consensus (bin/06, bin/08-09), but
every finished oligo set was supposed to be tested against those genomes and reported separately. They were
annotated (bin/05) precisely so this could be done. Until now it was never run for the chromosomal panel
(the plasmid equivalent was done in bin/15).

Input : config/final_chromosomal_oligos.tsv      21 oligos = the 7 final-panel sets (D22)
        data/genome_inventory/provenance_audit.tsv (tiers, from bin/02)
        data/genome_inventory/genome_files.tsv     (file names, from bin/01)
        data/genomes_downloaded/<file>             genome FASTA (WSL only, never committed)
Output: results/qr_oligo_check/oligo_hits.tsv      one row per oligo x genome (best hit + detail)
        results/qr_oligo_check/set_by_genome.tsv   one row per set x genome (verdict)
        results/qr_oligo_check/summary.txt         per-set counts, quality-review vs control, every non-clean case
        reports/qr_oligo_check.xlsx                human-readable version (gitignored, reaches OneDrive via sync)

Control: the same check is run on the primary-tier genomes. A "binds nothing" result is only meaningful if the
method demonstrably finds the oligos where they should be, so the control must come out almost all clean;
the script prints a WARNING if it does not.

Method (BLAST+ blastn-short, Expect=1000, DUST off as D18, but word_size=4 instead of 7: with 7, an oligo whose
  mismatches are scattered so that no 7-mer matches exactly is invisible, and "not found" would be reported
  as FAIL for the wrong reason; reward/penalty 1/-1
  instead of the blastn-short default 1/-3, so alignments run through internal mismatches instead of stopping
  at them; local genomes, no web BLAST):
  - per oligo and genome, every hit is rescored from the alignment itself: mismatches = oligo length minus
    matching bases, so unaligned ends and gaps count against the oligo (effective mismatches, "eff_mm")
  - oligo class: EXACT (0 mm, no gaps) | NEAR (<=2 mm, no gaps) | WEAK (3-5 mm, or gapped, or a primer
    mismatch in its last 3 nt, which is what matters most for extension) | NONE (>=6 mm or no hit)
  - pair-level geometry (D20 logic, applied to inclusivity): F, R and probe must sit on the same contig, F and R
    on opposite strands facing each other, amplicon <= 1000 bp, probe inside the amplicon. All combinations of
    candidate hits are tried; the best valid one is reported.
  - set verdict per genome: EXACT (all oligos exact) | OK (all EXACT/NEAR) | AT_RISK (geometry fine, at least
    one oligo WEAK) | FAIL (an oligo has no usable site, or the three do not form an amplicon)
  - amplicon length is compared with the control median; a difference of >20 nt is flagged (possible indel)

Usage: bin/18_qr_oligo_check.py [--threads 4] [--no-control] [--root PATH]
Needs blastn and makeblastdb on PATH (BLAST+ 2.17 is in conda base). Resumable: nothing is cached, a full run
takes a few minutes.
"""
import argparse
import csv
import itertools
import shutil
import statistics
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parent.parent
TIER = {"INCLUDE": "primary", "QUALITY_REVIEW": "quality-review", "REVIEW": "unresolved", "EXCLUDE": "excluded"}

OK_MAX_MM = 2        # <= this many effective mismatches (no gaps) = binds fine
FAIL_MIN_MM = 6      # >= this many = no usable site
THREE_PRIME_N = 3    # primer mismatches in the last N nt are treated as serious
MAX_AMPLICON = 1000
AMPLICON_DRIFT = 20  # nt difference from the control median that gets flagged
TOP_CANDIDATES = 6   # hits per oligo kept for geometry search
BLAST_FIELDS = ("qseqid sseqid sstart send qstart qend qlen length nident mismatch gaps evalue bitscore "
                "qseq sseq")
CLASS_ORDER = {"EXACT": 0, "NEAR": 1, "WEAK": 2, "NONE": 3}


def read_tsv(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


class Hit:
    __slots__ = ("oligo", "sid", "strand", "lo", "hi", "qlen", "eff_mm", "mm_pos", "gaps", "three_prime",
                 "bits")

    def __init__(self, oligo, sid, strand, lo, hi, qlen, eff_mm, mm_pos, gaps, three_prime, bits):
        self.oligo, self.sid, self.strand, self.lo, self.hi = oligo, sid, strand, lo, hi
        self.qlen, self.eff_mm, self.mm_pos, self.gaps = qlen, eff_mm, mm_pos, gaps
        self.three_prime, self.bits = three_prime, bits


def parse_hit(line):
    f = line.rstrip("\n").split("\t")
    qid, sid = f[0], f[1]
    sstart, send, qstart, qend, qlen = (int(x) for x in f[2:7])
    bits = float(f[12])
    qseq, sseq = f[13], f[14]
    matched = [False] * qlen
    qpos = qstart - 1
    gaps = 0
    for a, b in zip(qseq, sseq):
        if a == "-":            # insertion in the subject: no query base consumed
            gaps += 1
            continue
        if b == "-":            # query base with no subject base
            gaps += 1
            qpos += 1
            continue
        if a.upper() == b.upper():
            matched[qpos] = True
        qpos += 1
    mm_pos = [i + 1 for i, m in enumerate(matched) if not m]
    return Hit(qid, sid, "+" if sstart <= send else "-", min(sstart, send), max(sstart, send), qlen,
               qlen - sum(matched), mm_pos, gaps, any(p > qlen - THREE_PRIME_N for p in mm_pos), bits)


def classify(hit, role):
    if hit is None or hit.eff_mm >= FAIL_MIN_MM:
        return "NONE"
    if hit.gaps:
        return "WEAK"
    if role in ("F", "R") and hit.three_prime:
        return "WEAK"
    if hit.eff_mm == 0:
        return "EXACT"
    return "NEAR" if hit.eff_mm <= OK_MAX_MM else "WEAK"


def geometry(f, r, p):
    """Return amplicon length if F/R/probe form a plausible amplicon, else None."""
    if not (f.sid == r.sid == p.sid) or f.strand == r.strand:
        return None
    plus, minus = (f, r) if f.strand == "+" else (r, f)
    if not plus.lo < minus.lo:
        return None
    lo, hi = min(plus.lo, minus.lo), max(plus.hi, minus.hi)
    amp = hi - lo + 1
    if amp > MAX_AMPLICON or not (lo <= p.lo and p.hi <= hi):
        return None
    return amp


def run_blast(blastn, makeblastdb, fasta, query, threads, tmp):
    db = Path(tmp) / "db"
    subprocess.run([makeblastdb, "-in", str(fasta), "-dbtype", "nucl", "-out", str(db)],
                   check=True, capture_output=True)
    res = subprocess.run(
        [blastn, "-task", "blastn-short", "-query", str(query), "-db", str(db), "-word_size", "4", "-reward", "1", "-penalty", "-1", "-gapopen", "5", "-gapextend", "2",
         "-evalue", "1000", "-dust", "no", "-soft_masking", "false", "-strand", "both",
         "-max_target_seqs", "100", "-max_hsps", "20", "-num_threads", str(threads),
         "-outfmt", f"6 {BLAST_FIELDS}"], check=True, capture_output=True, text=True)
    hits = defaultdict(list)
    for line in res.stdout.splitlines():
        if line.strip():
            h = parse_hit(line)
            hits[h.oligo].append(h)
    return hits


def evaluate_set(set_id, roles, hits):
    """roles: {'F': name, 'R': name, 'probe': name}. Returns dict with verdict, chosen hits, amplicon, reason."""
    cand = {}
    for role, name in roles.items():
        usable = sorted((h for h in hits.get(name, []) if h.eff_mm < FAIL_MIN_MM),
                        key=lambda h: (h.eff_mm, -h.bits))
        seen, uniq = set(), []
        for h in usable:        # drop duplicate HSPs on the same coordinates
            key = (h.sid, h.strand, h.lo, h.hi)
            if key not in seen:
                seen.add(key)
                uniq.append(h)
        cand[role] = uniq[:TOP_CANDIDATES]
    missing = [roles[r] for r in ("F", "R", "probe") if not cand[r]]
    if missing:
        return {"verdict": "FAIL", "chosen": {}, "amplicon": "", "reason": "no usable site for " + ", ".join(missing)}
    best = None
    for f, r, p in itertools.product(cand["F"], cand["R"], cand["probe"]):
        amp = geometry(f, r, p)
        if amp is None:
            continue
        cls = [classify(f, "F"), classify(r, "R"), classify(p, "probe")]
        score = (max(CLASS_ORDER[c] for c in cls), f.eff_mm + r.eff_mm + p.eff_mm)
        if best is None or score < best[0]:
            best = (score, f, r, p, amp, cls)
    if best is None:
        return {"verdict": "FAIL", "chosen": {r: cand[r][0] for r in cand}, "amplicon": "",
                "reason": "oligos bind but do not form an amplicon (contig/strand/order/size)"}
    _, f, r, p, amp, cls = best
    if all(c == "EXACT" for c in cls):
        verdict, reason = "EXACT", ""
    elif all(c in ("EXACT", "NEAR") for c in cls):
        verdict, reason = "OK", ""
    else:
        verdict = "AT_RISK"
        bad = [f"{n} ({c}, {h.eff_mm} mm at {h.mm_pos}{', 3-prime' if h.three_prime and role != 'probe' else ''}"
               f"{', gapped' if h.gaps else ''})"
               for n, c, h, role in zip((roles["F"], roles["R"], roles["probe"]), cls, (f, r, p), ("F", "R", "probe"))
               if c in ("WEAK", "NONE")]
        reason = "; ".join(bad)
    return {"verdict": verdict, "chosen": {"F": f, "R": r, "probe": p}, "amplicon": amp, "reason": reason}


def write_tsv(path, header, rows):
    with open(path, "w", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(header)
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--threads", type=int, default=4)
    ap.add_argument("--no-control", action="store_true", help="skip the primary-tier control run")
    ap.add_argument("--root", default=str(DEFAULT_ROOT))
    args = ap.parse_args()

    root = Path(args.root)
    inv, genomes, out, reports = (root / "data/genome_inventory", root / "data/genomes_downloaded",
                                  root / "results/qr_oligo_check", root / "reports")
    blastn, makeblastdb = shutil.which("blastn"), shutil.which("makeblastdb")
    if not (blastn and makeblastdb):
        sys.exit("blastn/makeblastdb not found on PATH (BLAST+ is in conda base)")

    oligos = read_tsv(root / "config/final_chromosomal_oligos.tsv")
    sets = defaultdict(dict)
    for o in oligos:
        sets[o["set_id"]][o["role"]] = o["name"]
    for s, r in sets.items():
        if set(r) != {"F", "R", "probe"}:
            sys.exit(f"set {s} does not have exactly F, R and probe")
    print(f"== {len(oligos)} oligos in {len(sets)} sets")

    audit = read_tsv(inv / "provenance_audit.tsv")
    files = {r["accession"]: r["file"] for r in read_tsv(inv / "genome_files.tsv")}
    groups = {"quality-review": [], "primary": []}
    strain = {}
    for r in audit:
        t = TIER.get(r["final_verdict"])
        strain[r["accession"]] = r["strain"]
        if t in groups:
            groups[t].append(r["accession"])
    for t in groups:
        groups[t].sort()
    print(f"== {len(groups['quality-review'])} quality-review genomes, {len(groups['primary'])} primary (control)")
    if len(groups["quality-review"]) != 10:
        print(f"   NOTE: expected 10 quality-review genomes, found {len(groups['quality-review'])}")
    todo = [("quality-review", a) for a in groups["quality-review"]]
    if not args.no_control:
        todo += [("primary", a) for a in groups["primary"]]

    out.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        query = Path(tmp) / "oligos.fa"
        query.write_text("".join(f">{o['name']}\n{o['sequence'].upper()}\n" for o in oligos))
        seq_of = {o["name"]: o["sequence"].upper() for o in oligos}
        role_of = {o["name"]: o["role"] for o in oligos}

        hit_rows, set_rows, results = [], [], {}
        for i, (tier, acc) in enumerate(todo, 1):
            fasta = genomes / files.get(acc, f"{acc}.fna")
            if not fasta.exists():
                sys.exit(f"missing genome file {fasta} (genomes live in WSL data/genomes_downloaded/)")
            work = Path(tmp) / acc
            work.mkdir()
            hits = run_blast(blastn, makeblastdb, fasta, query, args.threads, work)
            shutil.rmtree(work)
            for s, roles in sets.items():
                ev = evaluate_set(s, roles, hits)
                results[(tier, acc, s)] = ev
                set_rows.append([tier, acc, strain.get(acc, ""), s, ev["verdict"], ev["amplicon"], ev["reason"]])
                for role in ("F", "R", "probe"):
                    name = roles[role]
                    h = ev["chosen"].get(role)
                    if h is None:
                        allh = sorted(hits.get(name, []), key=lambda x: (x.eff_mm, -x.bits))
                        h = allh[0] if allh else None
                    n_loci = len({(x.sid, x.strand, x.lo, x.hi) for x in hits.get(name, []) if x.eff_mm <= OK_MAX_MM})
                    cls = classify(h, role)
                    hit_rows.append([tier, acc, strain.get(acc, ""), s, name, role, len(seq_of[name]),
                                     cls, h.eff_mm if h else "", ",".join(map(str, h.mm_pos)) if h else "",
                                     h.gaps if h else "", int(h.three_prime) if h else "",
                                     h.sid if h else "", h.strand if h else "", h.lo if h else "",
                                     h.hi if h else "", n_loci])
            print(f"   [{i}/{len(todo)}] {tier:14s} {acc}")

    hdr_hits = ["tier", "accession", "strain", "set", "oligo", "role", "length", "class", "eff_mm", "mm_positions",
                "gap_cols", "primer3prime_mm", "contig", "strand", "start", "end", "loci_le2mm"]
    write_tsv(out / "oligo_hits.tsv", hdr_hits, hit_rows)
    ctrl_amps = defaultdict(list)
    for (tier, acc, s), ev in results.items():
        if tier == "primary" and ev["amplicon"] != "":
            ctrl_amps[s].append(ev["amplicon"])
    ctrl_median = {s: statistics.median(v) for s, v in ctrl_amps.items() if v}
    for row in set_rows:                      # add the amplicon-drift flag
        s, amp = row[3], row[5]
        drift = ""
        if row[0] == "quality-review" and amp != "" and s in ctrl_median and abs(amp - ctrl_median[s]) > AMPLICON_DRIFT:
            drift = f"amplicon {amp} vs control median {ctrl_median[s]:.0f}"
        row.append(drift)
    write_tsv(out / "set_by_genome.tsv", ["tier", "accession", "strain", "set", "verdict", "amplicon_bp",
                                          "detail", "amplicon_drift"], set_rows)

    # ---- summary
    lines = ["Quality-review genomes vs the 7 locked chromosomal oligo sets (bin/18)", ""]
    lines.append(f"Verdicts per set. quality-review = {len(groups['quality-review'])} genomes"
                 + ("" if args.no_control else f", control (primary tier) = {len(groups['primary'])} genomes") + ".")
    lines.append("")
    order = ["EXACT", "OK", "AT_RISK", "FAIL"]
    lines.append(f"{'set':14s} {'group':15s} " + " ".join(f"{v:>8s}" for v in order) + "   amplicon bp (min/median/max)")
    warn = []
    for s in sets:
        for tier in ("quality-review", "primary"):
            if tier == "primary" and args.no_control:
                continue
            c = Counter(results[(tier, a, s)]["verdict"] for a in groups[tier])
            amps = [results[(tier, a, s)]["amplicon"] for a in groups[tier] if results[(tier, a, s)]["amplicon"] != ""]
            amp_txt = f"{min(amps)}/{statistics.median(amps):.0f}/{max(amps)}" if amps else "-"
            lines.append(f"{s:14s} {tier:15s} " + " ".join(f"{c.get(v, 0):8d}" for v in order) + f"   {amp_txt}")
            if tier == "primary":
                bad = (c.get("AT_RISK", 0) + c.get("FAIL", 0)) / max(1, len(groups["primary"]))
                if bad > 0.05:
                    warn.append(f"{s}: {bad:.0%} of control genomes are AT_RISK/FAIL")
    lines.append("")
    if args.no_control:
        lines.append("Control skipped (--no-control): a clean result is NOT validated against known-positive genomes.")
    elif warn:
        lines.append("WARNING: control genomes should be almost all clean. Do not trust the quality-review result until this is explained:")
        lines += [f"  - {w}" for w in warn]
    else:
        lines.append("Control check: every set binds >=95% of the primary-tier genomes cleanly, so the method finds the oligos where they belong.")
    lines.append("")
    lines.append("Every quality-review case that is not EXACT:")
    n_listed = 0
    for row in sorted(set_rows, key=lambda r: (r[3], r[1])):
        if row[0] == "quality-review" and (row[4] != "EXACT" or row[7]):
            n_listed += 1
            lines.append(f"  {row[3]:14s} {row[1]} {row[2]:14s} {row[4]:8s} {row[6]} {row[7]}".rstrip())
    if not n_listed:
        lines.append("  none: all 7 sets are EXACT in all quality-review genomes")
    (out / "summary.txt").write_text("\n".join(lines) + "\n")
    print("\n" + "\n".join(lines))

    # ---- xlsx
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill
        fills = {"EXACT": "C6EFCE", "OK": "E2F0D9", "AT_RISK": "FFEB9C", "FAIL": "FFC7CE"}
        wb = Workbook()
        ws = wb.active
        ws.title = "QR matrix"
        qr = groups["quality-review"]
        ws.append(["set"] + [f"{strain.get(a, '')} ({a})" for a in qr])
        for s in sets:
            ws.append([s] + [results[("quality-review", a, s)]["verdict"] for a in qr])
        for row in ws.iter_rows(min_row=2, min_col=2):
            for c in row:
                c.fill = PatternFill("solid", fgColor=fills.get(c.value, "FFFFFF"))
        for c in ws[1]:
            c.font = Font(bold=True)
        ws.column_dimensions["A"].width = 16
        for col in "BCDEFGHIJK":
            ws.column_dimensions[col].width = 24
        ws2 = wb.create_sheet("Per-set detail (QR)")
        ws2.append(["accession", "strain", "set", "verdict", "amplicon_bp", "detail", "amplicon_drift"])
        for r in set_rows:
            if r[0] == "quality-review":
                ws2.append(r[1:])
        ws3 = wb.create_sheet("Per-oligo detail (QR)")
        ws3.append(hdr_hits[1:])
        for r in hit_rows:
            if r[0] == "quality-review":
                ws3.append(r[1:])
        ws4 = wb.create_sheet("Summary")
        for ln in lines:
            ws4.append([ln])
        ws4.column_dimensions["A"].width = 140
        wb.save(reports / "qr_oligo_check.xlsx")
        print(f"\nwrote {reports / 'qr_oligo_check.xlsx'}")
    except ImportError:
        print("openpyxl not available: skipped the xlsx (the .tsv/.txt outputs are complete)")


if __name__ == "__main__":
    main()
