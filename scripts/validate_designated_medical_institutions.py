#!/usr/bin/env python3
"""
Validate data/designated_medical_institutions_2026_04_30.json.
Exits non-zero if any check fails.
"""
import json, sys, os, re

DATA_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'designated_medical_institutions_2026_04_30.json')

def fail(msg):
    print(f"FAIL: {msg}", file=sys.stderr)
    sys.exit(1)

with open(DATA_FILE, encoding='utf-8') as f:
    try:
        data = json.load(f)
    except json.JSONDecodeError as e:
        fail(f"JSON parse error: {e}")

# Structure
if not isinstance(data, dict):
    fail("Root must be a dict")
for key in ("_meta", "regions", "institutions"):
    if key not in data:
        fail(f"Missing top-level key: {key}")

meta = data["_meta"]
for key in ("source_title", "source_date", "source_file", "record_count"):
    if not meta.get(key):
        fail(f"_meta missing required field: {key}")

if meta["source_date"] != "2026-04-30":
    fail(f"Unexpected source_date: {meta['source_date']}")

institutions = data["institutions"]
if not isinstance(institutions, list) or len(institutions) == 0:
    fail("institutions must be a non-empty list")

if len(institutions) != meta["record_count"]:
    fail(f"record_count {meta['record_count']} != actual {len(institutions)}")

if len(institutions) < 900:
    fail(f"Suspiciously few records: {len(institutions)} (expected 1000+)")

# Per-record checks
REQUIRED_FIELDS = ("id", "serial_no", "region", "institution_name", "address", "source_date")
REGIONS = {'강원','경기','경남','경북','광주','대구','대전','부산','서울','세종','울산','인천','전남','전북','제주','충남','충북'}
REPL_CHAR_RE = re.compile(r'[�\x00]')

errors = []
for i, rec in enumerate(institutions):
    for field in REQUIRED_FIELDS:
        if field not in rec:
            errors.append(f"Record {i}: missing field {field}")
            continue
    name = rec.get("institution_name", "")
    if not name.strip():
        errors.append(f"Record {i} (id={rec.get('id')}): empty institution_name")
    region = rec.get("region", "")
    if not region.strip():
        errors.append(f"Record {i} (id={rec.get('id')}): empty region")
    elif region not in REGIONS:
        errors.append(f"Record {i} (id={rec.get('id')}): unknown region {region!r}")
    if rec.get("source_date") != "2026-04-30":
        errors.append(f"Record {i}: source_date {rec.get('source_date')!r}")
    for field in ("institution_name", "address"):
        val = rec.get(field, "")
        if REPL_CHAR_RE.search(val):
            errors.append(f"Record {i}: replacement/null char in {field}")

if errors:
    for e in errors:
        print(f"ERROR: {e}", file=sys.stderr)
    fail(f"{len(errors)} validation error(s) found")

# Region coverage
regions_in_data = {r["region"] for r in institutions}
for required_region in ("서울", "제주"):
    if required_region not in regions_in_data:
        fail(f"No records for required region: {required_region}")

print(f"OK: {len(institutions)} records validated across {len(regions_in_data)} regions.")
print(f"Regions: {sorted(regions_in_data)}")
