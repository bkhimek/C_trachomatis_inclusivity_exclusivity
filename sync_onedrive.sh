#!/usr/bin/env bash
# Mirror the working tree (without .git or large data) to the OneDrive project folder.
set -euo pipefail
OD="/mnt/c/Users/krist/OneDrive/Documents/Projects/C_trachomatis_inclusivity_exclusivity"
cd "$(dirname "$0")"
mkdir -p "$OD"
tar --exclude=.git --exclude=data/genomes_downloaded --exclude=data/plasmids_downloaded \
    --exclude=data/blast_databases -cf - . | tar -xf - -C "$OD"
echo "Mirrored to $OD"
