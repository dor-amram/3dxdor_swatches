#!/usr/bin/env bash
# Rebuild swatches.json from Hub data already saved in build/live/{fdm,resin}/*.json.
# Run from the repo root. Exit 0 = nothing changed (published file restored), 1 = changed, other = error.
set -euo pipefail
ROOT=$(pwd); B=$ROOT/build
test -d "$B/live/fdm" && test -d "$B/live/resin" || { echo "missing build/live data" >&2; exit 2; }
mkdir -p "$B/ext"
[ -d "$B/ext/SpoolmanDB" ] || git clone -q --depth 1 https://github.com/Donkie/SpoolmanDB "$B/ext/SpoolmanDB"
curl -sSfL -o "$B/ext/bbl_colors.json" https://raw.githubusercontent.com/bambulab/BambuStudio/master/resources/profiles/BBL/filament/filaments_color_codes.json
cd "$B"
python3 "$ROOT/tools/swatch_match.py"
node "$ROOT/tools/swatch_gen.js"
cd "$ROOT"
set +e; python3 tools/diff.py swatches.json build/swatches.json; rc=$?; set -e
if [ $rc -eq 1 ]; then cp build/swatches.json swatches.json; echo "CHANGED"; else echo "NO CHANGE"; fi
exit $rc
