#!/usr/bin/env python3
"""bin/02: genome provenance audit (runs BEFORE any downstream analysis).

Input : data/genome_inventory/genome_metadata.tsv (from bin/01)
        config/provenance_exclude_bioprojects.tsv  (known-bad BioProjects -> EXCLUDE)
        config/provenance_overrides.tsv            (manual decisions with reasons)
Output: data/genome_inventory/provenance_audit.tsv       per-genome flags and verdicts
        data/genome_inventory/provenance_audit_log.txt   human-readable summary
        data/genome_inventory/genomes_included.txt       accessions with final verdict INCLUDE
        data/genome_inventory/genome_inventory_final.tsv metadata of included genomes

Verdicts
  EXCLUDE  hard rule: known-bad BioProject, not RefSeq, not Complete Genome, not current
  REVIEW   strong flag (engineering/selection markers in names or descriptions, ANI/CheckM/size
           anomalies, odd contig count, non-C. trachomatis organism name). Needs a human decision,
           recorded in config/provenance_overrides.tsv. REVIEW genomes are NOT in genomes_included.txt.
  INCLUDE  no strong flag. Manual decisions in the overrides file: INCLUDE (primary tier: consensus
           and inclusivity), QUALITY (quality-review tier: natural isolates with suspicious quality
           metrics, tested for inclusivity but not used for consensus), EXCLUDE, or REVIEW (hold).
Weak notes (sparse metadata, name qualifiers, duplicate strain names, dominant BioProject) are
recorded but never change the verdict.
"""
import collections
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INV = ROOT / "data" / "genome_inventory"
META = INV / "genome_metadata.tsv"
EXCL = ROOT / "config" / "provenance_exclude_bioprojects.tsv"
OVR = ROOT / "config" / "provenance_overrides.tsv"

DOMINANT_SHARE = 0.10
SIZE_RANGE = (1_000_000, 1_120_000)  # C. trachomatis is ~1.04 Mb (plasmid adds ~7.5 kb)
MAX_CONTIGS = 3
MIN_CHECKM_COMPLETENESS = 90.0
MAX_CHECKM_CONTAMINATION = 5.0

# (regex, flags, label). Scanned in strain, organism name, isolate, assembly name,
# BioProject titles and BioSample text.
STRONG_PATTERNS = [
    (r"::", 0, "insertion/construct marker '::'"),
    (r"\bTn\(|\bTn\d|transposon", re.I, "transposon"),
    (r"tet(R|\d)", 0, "tetracycline-resistance marker/selection (tetR/tetN)"),
    (r"tetracycline[- ]resist", re.I, "tetracycline resistance"),
    (r"rifamp|\brif[RrSs]?\b", re.I, "rifampicin marker/selection"),
    (r"spectinomycin|\bspc[RrSs]?\b", re.I, "spectinomycin marker/selection"),
    (r"mutant|mutagen", re.I, "mutant/mutagenesis"),
    (r"recombinan|transformant|transformation", re.I, "recombinant/transformant"),
    (r"engineer|construct|knock-?out|lateral gene transfer|\bLGT\b", re.I, "engineering language"),
    (r"in vitro (selected|evolved)|laboratory[- ]selected|serial passage", re.I, "laboratory selection/passage"),
]
# Applied to BioProject titles only (experiment-style titles that the name patterns miss).
TITLE_PATTERNS = [
    (r"laborator(y|ies)[- ]adapt|adapted to (cell|tissue) culture|\bpassag", re.I, "laboratory adaptation/passage"),
    (r"\brequired for\b|\bis essential\b|gene function", re.I, "gene-function study language"),
    (r"re-?sequencing", re.I, "re-sequencing of laboratory strains (check for passage/derivatives)"),
]
SCAN_FIELDS = ["strain", "organism_name", "isolate", "assembly_name", "bioproject_titles", "biosample_text"]


def read_config(path, ncols):
    out = []
    if not path.exists():
        return out
    for line in path.read_text().splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        parts = line.split(None, ncols - 1)  # tab- or space-separated; last column keeps its spaces
        parts += [""] * (ncols - len(parts))
        out.append([p.strip() for p in parts])
    return out


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def main():
    if not META.exists():
        sys.exit("genome_metadata.tsv not found: run bin/01 first")
    rows = list(csv.DictReader(open(META), delimiter="\t"))
    excluded_bps = {a: reason for a, reason in read_config(EXCL, 2)}
    overrides = {a: (d.upper(), reason) for a, d, reason in read_config(OVR, 3)}

    bp_counts = collections.Counter(r["bioproject"] for r in rows)
    strain_counts = collections.Counter(r["strain"].lower() for r in rows if r["strain"])
    n = len(rows)

    audit = []
    for r in rows:
        hard, strong, weak = [], [], []
        for bp in filter(None, r["bioproject_all"].split(";")):
            if bp in excluded_bps:
                hard.append(f"known-bad BioProject {bp}: {excluded_bps[bp]}")
        if not r["accession"].startswith("GCF_"):
            hard.append("not a RefSeq (GCF_) accession")
        if r["assembly_level"] != "Complete Genome":
            hard.append(f"assembly level {r['assembly_level']!r}")
        if r["assembly_status"] != "current":
            hard.append(f"assembly status {r['assembly_status']!r}")

        found = collections.OrderedDict()
        for field in SCAN_FIELDS:
            text = r.get(field, "")
            for rx, fl, label in STRONG_PATTERNS:
                m = re.search(rx, text, fl)
                if m:
                    found.setdefault((label, m.group(0)), []).append(field)
        for rx, fl, label in TITLE_PATTERNS:
            m = re.search(rx, r.get("bioproject_titles", ""), fl)
            if m:
                found.setdefault((label, m.group(0)), []).append("bioproject_titles")
        for (label, hit), fields in found.items():
            strong.append(f"{label} '{hit}' in {'/'.join(fields)}")
        if not r["organism_name"].startswith("Chlamydia trachomatis"):
            strong.append(f"organism name {r['organism_name']!r}")
        if r["ani_status"] and r["ani_status"] != "OK":
            strong.append(f"ANI taxonomy check {r['ani_status']}")
        if r["ani_match"] and r["ani_match"] != "species_match":
            strong.append(f"ANI match status {r['ani_match']}")
        comp, cont = num(r["checkm_completeness"]), num(r["checkm_contamination"])
        if comp is not None and comp < MIN_CHECKM_COMPLETENESS:
            strong.append(f"CheckM completeness {comp}")
        if cont is not None and cont > MAX_CHECKM_CONTAMINATION:
            strong.append(f"CheckM contamination {cont}")
        length, contigs = num(r["total_length"]), num(r["n_contigs"])
        if length is not None and not (SIZE_RANGE[0] <= length <= SIZE_RANGE[1]):
            strong.append(f"genome length {int(length)} outside {SIZE_RANGE}")
        if contigs is not None and contigs > MAX_CONTIGS:
            strong.append(f"{int(contigs)} contigs")

        if not (r["collection_date"] or r["geo_loc_name"] or r["host"]):
            weak.append("sparse_metadata (no collection date, location or host)")
        if re.search(r"\([a-z]\)", r["strain"]):
            weak.append("name_qualifier_in_parentheses")
        if r["strain"] and strain_counts[r["strain"].lower()] > 1:
            weak.append("duplicate_strain_name")
        if r["bioproject"] and bp_counts[r["bioproject"]] / n >= DOMINANT_SHARE:
            weak.append(f"dominant_bioproject ({bp_counts[r['bioproject']]}/{n})")

        auto = "EXCLUDE" if hard else "REVIEW" if strong else "INCLUDE"
        ov = overrides.get(r["accession"])
        final = ov[0] if ov else auto
        if final in ("QUALITY", "QUALITY_REVIEW"):
            final = "QUALITY_REVIEW"
        if final not in ("INCLUDE", "QUALITY_REVIEW", "EXCLUDE", "REVIEW"):
            sys.exit(f"invalid decision {final!r} for {r['accession']} in provenance_overrides.tsv "
                     "(use INCLUDE, QUALITY, EXCLUDE or REVIEW)")
        audit.append({
            "accession": r["accession"], "strain": r["strain"], "bioproject": r["bioproject"],
            "auto_verdict": auto, "override": ov[0] if ov else "", "override_reason": ov[1] if ov else "",
            "final_verdict": final,
            "hard_flags": " || ".join(hard), "strong_flags": " || ".join(strong), "weak_notes": " || ".join(weak),
        })

    by_acc = {r["accession"]: r for r in rows}
    with open(INV / "provenance_audit.tsv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(audit[0].keys()), delimiter="\t")
        w.writeheader()
        w.writerows(audit)
    included = [a["accession"] for a in audit if a["final_verdict"] == "INCLUDE"]
    quality = [a["accession"] for a in audit if a["final_verdict"] == "QUALITY_REVIEW"]
    excluded = [a["accession"] for a in audit if a["final_verdict"] == "EXCLUDE"]
    (INV / "genomes_included.txt").write_text("\n".join(included) + "\n")
    (INV / "genomes_quality_review.txt").write_text("\n".join(quality) + ("\n" if quality else ""))
    (INV / "genomes_excluded.txt").write_text("\n".join(excluded) + ("\n" if excluded else ""))
    with open(INV / "genome_inventory_final.tsv", "w", newline="") as f:
        cols = list(rows[0].keys()) + ["tier", "auto_verdict", "weak_notes"]
        w = csv.DictWriter(f, fieldnames=cols, delimiter="\t")
        w.writeheader()
        for a in audit:
            if a["final_verdict"] in ("INCLUDE", "QUALITY_REVIEW"):
                d = dict(by_acc[a["accession"]])
                d["tier"] = "primary" if a["final_verdict"] == "INCLUDE" else "quality_review"
                d["auto_verdict"], d["weak_notes"] = a["auto_verdict"], a["weak_notes"]
                w.writerow(d)

    L = []
    fc = collections.Counter(a["final_verdict"] for a in audit)
    ac = collections.Counter(a["auto_verdict"] for a in audit)
    L.append(f"PROVENANCE AUDIT: {n} genomes")
    L.append(f"  config loaded: {len(excluded_bps)} known-bad BioProjects, {len(overrides)} manual overrides")
    L.append(f"  automatic verdicts: {dict(ac)}")
    L.append(f"  final tiers (after overrides): primary {len(included)}, quality-review {len(quality)}, "
             f"excluded {len(excluded)}, unresolved REVIEW {fc.get('REVIEW', 0)}")
    unresolved = [a for a in audit if a["final_verdict"] == "REVIEW"]
    L.append(f"  unresolved REVIEW: {len(unresolved)} (decide each in config/provenance_overrides.tsv)")
    L.append("\nBIOPROJECTS (count, verdicts, title)")
    tally = collections.defaultdict(collections.Counter)
    titles, subs = {}, {}
    for a in audit:
        tally[a["bioproject"]][a["final_verdict"]] += 1
    for r in rows:
        titles.setdefault(r["bioproject"], r["bioproject_titles"])
        subs.setdefault(r["bioproject"], r["submitter"])
    for bp, c in sorted(tally.items(), key=lambda kv: -sum(kv[1].values())):
        L.append(f"  {bp:<14} n={sum(c.values()):<3} {dict(c)}  [{subs[bp][:28]}] {titles[bp][:90]}")
    L.append("\nEXCLUDE / REVIEW GENOMES")
    for a in audit:
        if a["final_verdict"] != "INCLUDE":
            L.append(f"  {a['final_verdict']:<7} {a['accession']}  {a['strain']:<22} {a['bioproject']:<13} "
                     f"{(a['hard_flags'] or a['strong_flags'])[:170]}")
    wc = collections.Counter(w.split(" (")[0] for a in audit for w in a["weak_notes"].split(" || ") if w)
    L.append(f"\nWEAK NOTES (informational only): {dict(wc)}")
    dup = sorted({a["strain"] for a in audit if "duplicate_strain_name" in a["weak_notes"]})
    L.append(f"  strain names appearing more than once: {dup or 'none'}")
    text = "\n".join(L)
    (INV / "provenance_audit_log.txt").write_text(text + "\n")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
