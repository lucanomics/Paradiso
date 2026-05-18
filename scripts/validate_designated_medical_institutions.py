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

# record_count must match actual length
if len(institutions) != meta["record_count"]:
    fail(f"record_count {meta['record_count']} != actual {len(institutions)}")

if len(institutions) < 900:
    fail(f"Suspiciously few records: {len(institutions)} (expected 1000+)")

# Per-record checks
REQUIRED_FIELDS = ("id", "serial_no", "region", "institution_name", "address", "source_date")
REGIONS = {'강원','경기','경남','경북','광주','대구','대전','부산','서울','세종','울산','인천','전남','전북','제주','충남','충북'}
REPL_CHAR_RE = re.compile(r'[�\x00]')
DIGIT_RE = re.compile(r'\d')
# Conservative: province keyword + space + city/county keyword + space (genuine address pattern)
ADDRESS_LIKE_RE = re.compile(r'(특별자치도|광역시|특별시|특별자치시)\s+\S+시\s')

errors = []
serial_values = []

for i, rec in enumerate(institutions):
    for field in REQUIRED_FIELDS:
        if field not in rec:
            errors.append(f"Record {i}: missing field {field}")
            continue

    name = rec.get("institution_name", "")
    region = rec.get("region", "")
    address = rec.get("address", "")
    phone = rec.get("phone", "")
    serial_no = rec.get("serial_no")

    # serial_no must be an integer
    if not isinstance(serial_no, int):
        errors.append(f"Record {i} (id={rec.get('id')}): serial_no is not an integer: {serial_no!r}")
    else:
        serial_values.append(serial_no)

    # institution_name must not be empty
    if not name.strip():
        errors.append(f"Record {i} (id={rec.get('id')}): empty institution_name")

    # region must be valid
    if not region.strip():
        errors.append(f"Record {i} (id={rec.get('id')}): empty region")
    elif region not in REGIONS:
        errors.append(f"Record {i} (id={rec.get('id')}): unknown region {region!r}")

    # source_date per record
    if rec.get("source_date") != "2026-04-30":
        errors.append(f"Record {i}: source_date {rec.get('source_date')!r}")

    # Check for replacement/null characters
    for field in ("institution_name", "address"):
        val = rec.get(field, "")
        if REPL_CHAR_RE.search(val):
            errors.append(f"Record {i}: replacement/null char in {field}")

    # phone must be present, non-empty, and contain at least one digit
    if not phone.strip():
        errors.append(f"Record {i} (id={rec.get('id')}, name={name!r}): empty phone")
    elif not DIGIT_RE.search(phone):
        errors.append(f"Record {i} (id={rec.get('id')}): phone has no digits: {phone!r}")

    # address must not start with a phone-number-like string
    if address and re.match(r'^\d[\d\-]+$', address.strip()):
        errors.append(f"Record {i} (id={rec.get('id')}): address looks like a phone number: {address!r}")

    # institution_name should not contain a full address-like substring
    if ADDRESS_LIKE_RE.search(name):
        errors.append(f"Record {i} (id={rec.get('id')}): institution_name contains address-like text: {name!r}")

if errors:
    for e in errors:
        print(f"ERROR: {e}", file=sys.stderr)
    fail(f"{len(errors)} validation error(s) found")

# serial_no uniqueness
serial_set = set(serial_values)
if len(serial_values) != len(serial_set):
    dupes = [s for s in serial_set if serial_values.count(s) > 1]
    fail(f"Duplicate serial_no values: {sorted(dupes)}")

# serial_no continuity: must be 1..max with no gaps
max_serial = max(serial_values)
missing_serials = [s for s in range(1, max_serial + 1) if s not in serial_set]
if missing_serials:
    fail(f"Missing serial_no values (gaps in 1..{max_serial}): {missing_serials[:10]}")

# max_serial must equal record_count (when serials are continuous from 1)
if max_serial != meta["record_count"]:
    fail(f"max serial_no {max_serial} != _meta.record_count {meta['record_count']}")

# Region coverage
regions_in_data = {r["region"] for r in institutions}
for required_region in ("서울", "제주"):
    if required_region not in regions_in_data:
        fail(f"No records for required region: {required_region}")

# Known-record assertions: verify specific source-backed records
KNOWN_RECORDS = {
    540: {
        "region": "대전",
        "institution_name": "(사)한국건강관리협회 대전광역시 충청남도지부",
        "address": "대전광역시 서구 계룡로 611",
        "phone": "042-530-2243",
    },
    1092: {
        "region": "충북",
        "institution_name": "(사)대한산업보건협회 충북지역본부",
        "address": "충청북도 청주시 흥덕구 직지대로 397",
        "phone": "043-263-7137",
    },
    1093: {
        "region": "충북",
        "institution_name": "(사)한국건강관리협회 충청북도 세종특별자치시지부",
        "address": "충청북도 청주시 흥덕구 직지대로 631",
        "phone": "043-299-5765",
    },
    1096: {
        "region": "충북",
        "institution_name": "충청북도 충주의료원",
        "address": "충청북도 충주시 사직산21길 34",
        "phone": "043-841-0166",
    },
}

rec_by_serial = {r["serial_no"]: r for r in institutions}
known_errors = []
for serial_no, expected in KNOWN_RECORDS.items():
    rec = rec_by_serial.get(serial_no)
    if rec is None:
        known_errors.append(f"serial_no {serial_no}: record missing")
        continue
    for field, val in expected.items():
        if rec.get(field) != val:
            known_errors.append(
                f"serial_no {serial_no} field {field!r}: "
                f"expected {val!r}, got {rec.get(field)!r}"
            )
if known_errors:
    for e in known_errors:
        print(f"KNOWN-RECORD ERROR: {e}", file=sys.stderr)
    fail(f"{len(known_errors)} known-record assertion(s) failed")

print(f"OK: {len(institutions)} records validated across {len(regions_in_data)} regions.")
print(f"Serial range: 1–{max_serial} (continuous). Regions: {sorted(regions_in_data)}")
