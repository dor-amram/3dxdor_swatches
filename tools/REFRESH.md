# Swatch refresh runbook

Rebuilds `swatches.json` from the 3DxDor Management Hub and publishes it. Used by the monthly scheduled task and by manual "refresh swatches" requests.

Hub (private Claude artifact, read with the ArtifactData tool): https://claude.ai/artifact/4rkTFN84voejQGpa91xvdC

## Steps (repo root)
1. `rm -rf build/live` and read the Hub into it with ArtifactData `list`, `query.limit` 1000, `out_dir` = `<repo>/build/live`:
   - collection `fdm`
   - collection `resin`
   Check the document counts look sane (the run before this one had ~260 fdm and ~36 resin). If either collection comes back empty or the read fails, stop and report; do not publish.
2. `./tools/refresh.sh` — fetches SpoolmanDB and the Bambu colour table into `build/ext`, matches, generates `build/swatches.json`, and diffs against the published file.
   - Exit 0 = **no change**: stop. Do not commit or push.
   - Exit 1 = changed: `swatches.json` has been replaced. Continue.
   - Any other exit = error: stop and report.
3. Read the generator output:
   - `brand leaks: []` and `cost-ish keys: false` are required. Otherwise restore with `git checkout swatches.json`, stop and report.
   - `hebrew missing: [...]`: add each missing colour name / finish label to `tools/he.json` (Hebrew; polymer acronyms and product codes such as PLA, PA6, 95A, SP64 stay in Latin script), then rerun `./tools/refresh.sh` until the list is empty. Publish these translations; list them in the report for review.
4. Commit `swatches.json` (and `tools/he.json` if changed) and push to `main`. GitHub Pages republishes in a few minutes. Commit as `Claude <noreply@anthropic.com>`.
5. Report: the diff summary (added / removed / availability changes), the new Hebrew translations, and new items whose colour source is "approximate". For approximate new items, optionally look for a maker-published hex (maker colour chart or product page, Polymaker HEX table, filamentcolors.xyz measured swatches) and **list candidates with source URLs for Dor's approval — do not add them to `tools/hex_overrides.json` without approval**. Never invent a hex.

## Not part of the monthly run
- The PDF colour card (`colours-he.pdf`, `python3 tools/card.py`) is rebuilt only when Dor asks.
- Hex overrides are added only after Dor approves them.

## Files
| File | Role |
|---|---|
| `tools/swatch_match.py` | Matches Hub items to SpoolmanDB / Bambu Studio colour data (tiers: verified, close, generic, approx) |
| `tools/swatch_gen.js` | Builds the customer-safe `swatches.json` (no brand, cost, grams, sources); availability; effects; Hebrew labels; privacy scan |
| `tools/calc.js` | Remaining-filament calculation shared with the Hub |
| `tools/hex_overrides.json` | Approved colour codes with source URLs |
| `tools/he.json` | Hebrew colour names, finish labels and material labels |
| `tools/diff.py` | Change summary between published and new data |
