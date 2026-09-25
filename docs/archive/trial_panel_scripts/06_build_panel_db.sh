#!/usr/bin/env bash
# Downloads the exclusivity panel and builds one BLAST database per tier (genus, clinical).
set -euo pipefail
PANEL=docs/exclusivity_panel_accessions.tsv
GEN=data/panel/genomes; DB=data/panel/blastdb; mkdir -p "$GEN" "$DB"
tail -n +2 "$PANEL" | cut -f3 > data/panel/panel_accessions.txt
./bin/03_download_genomes.sh data/panel/panel_accessions.txt "$GEN" 25
for tier in genus clinical; do
  : > "$DB/$tier.fna"
  awk -F'\t' -v t="$tier" 'NR>1 && $1==t {gsub(" ","_",$2); print $3"\t"$2}' "$PANEL" | while IFS=$'\t' read -r acc sp; do
    sed "s/^>\([^ ]*\).*/>${acc}|${sp}|\1/" "$GEN/$acc.fna" >> "$DB/$tier.fna"
  done
  makeblastdb -in "$DB/$tier.fna" -dbtype nucl -out "$DB/$tier" -title "ct_exclusivity_$tier" > /dev/null
  echo "$tier: $(grep -c '>' "$DB/$tier.fna") sequences | $(blastdbcmd -db "$DB/$tier" -info | grep 'total bases')"
done
sha256sum "$DB/genus.fna" "$DB/clinical.fna" data/panel/panel_accessions.txt > docs/panel_checksums.txt
echo "done"
