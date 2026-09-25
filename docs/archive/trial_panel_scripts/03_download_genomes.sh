#!/usr/bin/env bash
# Usage: ./bin/03_download_genomes.sh <accession_list.txt> <outdir> [chunk_size]
# Downloads genomes in small chunks with retries; skips accessions already present.
set -uo pipefail
LIST=$(realpath "$1"); OUT="$2"; CHUNK=${3:-25}
mkdir -p "$OUT"; OUT=$(realpath "$OUT"); TMP="$OUT/../_tmp_dl"; mkdir -p "$TMP"
todo="$TMP/todo.txt"; : > "$todo"
while read -r acc; do [ -s "$OUT/$acc.fna" ] || echo "$acc" >> "$todo"; done < "$LIST"
echo "to download: $(wc -l < "$todo") of $(wc -l < "$LIST")"
split -l "$CHUNK" -d "$todo" "$TMP/chunk_"
for c in "$TMP"/chunk_*; do
  [ -e "$c" ] || continue
  for try in 1 2 3; do
    rm -rf "$TMP/pkg" "$TMP/pkg.zip"
    if datasets download genome accession --inputfile "$c" --include genome --filename "$TMP/pkg.zip" >/dev/null 2>&1 \
       && unzip -oq "$TMP/pkg.zip" -d "$TMP/pkg"; then
      for d in "$TMP"/pkg/ncbi_dataset/data/GC*; do acc=$(basename "$d"); cp "$d"/*.fna "$OUT/$acc.fna"; done
      echo "$(basename $c): ok (try $try)"; break
    else
      echo "$(basename $c): failed try $try"; sleep 5
    fi
  done
done
rm -rf "$TMP"
have=$(ls "$OUT"/*.fna 2>/dev/null | wc -l)
echo "genomes in $OUT: $have / $(wc -l < "$LIST")"
