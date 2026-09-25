#!/usr/bin/env python3
"""Select exclusivity-panel genomes: reference/representative first, then evenly spaced complete RefSeq genomes."""
import json, subprocess, csv
rows = [l.rstrip("\n").split("|") for l in open("docs/exclusivity_panel_species.txt") if l.strip() and not l.startswith("#")]
out, total = [], 0
print(f"{'tier':9s} {'species':30s} {'max':>3s} {'avail':>5s} {'picked':>6s}")
for tier, sp, n, why in rows:
    n = int(n)
    r = subprocess.run(["datasets","summary","genome","taxon",sp,"--assembly-source","RefSeq",
                        "--assembly-level","complete","--as-json-lines"], capture_output=True, text=True)
    recs = sorted((json.loads(l) for l in r.stdout.splitlines() if l.strip()), key=lambda d: d["accession"])
    if not recs:
        print(f"{tier:9s} {sp:30s} {n:3d} {0:5d} {0:6d}   <-- WARN: nothing found. {r.stderr.strip()[:100]}"); continue
    cat = lambda d: d.get("assembly_info", {}).get("refseq_category", "")
    ref = [d for d in recs if cat(d) in ("reference genome", "representative genome")][:1]
    rest = [d for d in recs if d not in ref]
    pick = list(ref); k = n - len(pick)
    if k > 0 and rest:
        pick += rest if len(rest) <= k else [rest[int(i * len(rest) / k)] for i in range(k)]
    for d in pick:
        out.append([tier, sp, d["accession"], d.get("organism", {}).get("organism_name", ""),
                    d.get("organism", {}).get("infraspecific_names", {}).get("strain", ""), cat(d),
                    d.get("assembly_stats", {}).get("total_sequence_length", "")])
    total += len(pick)
    print(f"{tier:9s} {sp:30s} {n:3d} {len(recs):5d} {len(pick):6d}")
with open("docs/exclusivity_panel_accessions.tsv", "w", newline="") as fh:
    w = csv.writer(fh, delimiter="\t")
    w.writerow(["tier","species","accession","organism_name","strain","refseq_category","length"]); w.writerows(out)
print("total genomes selected:", total)
