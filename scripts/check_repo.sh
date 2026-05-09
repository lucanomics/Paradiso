#!/usr/bin/env bash
set -euo pipefail

echo "[1/4] Validating visa_data.json format..."
python3 -m json.tool visa_data.json > /tmp/visa_data_check.json

echo "[2/4] Validating representative manual-aware visa schema..."
python3 - <<'PY'
import json
import sys
import re

with open("visa_data.json", encoding="utf-8") as f:
    visas = json.load(f)
with open("doc_master.json", encoding="utf-8") as f:
    docs = json.load(f)

doc_ids = {d.get("id") for d in docs if isinstance(d, dict)}
records = {v.get("code"): v for v in visas if isinstance(v, dict)}
required = ["C-3", "D-2", "F-6", "K-STAR"]
missing = [code for code in required if code not in records]
if missing:
    raise SystemExit(f"Missing representative manual-aware records: {', '.join(missing)}")

def iter_doc_refs(value):
    if isinstance(value, list):
        for item in value:
            yield item
    elif isinstance(value, dict):
        for item in value.values():
            yield from iter_doc_refs(item)

errors = []
for code in required:
    record = records[code]
    for field in ("manualDomains", "procedures", "sourceManualStatus"):
        if field not in record:
            errors.append(f"{code}: missing {field}")
    status = record.get("sourceManualStatus") or {}
    if status.get("needsManualReview") is not True:
        errors.append(f"{code}: representative record must remain needsManualReview=true")
    procedures = record.get("procedures") or {}
    for proc_name, proc in procedures.items():
        for doc_ref in iter_doc_refs((proc or {}).get("requiredDocs", [])):
            if isinstance(doc_ref, str) and doc_ref.startswith("doc_") and doc_ref not in doc_ids:
                errors.append(f"{code}.{proc_name}: unknown doc_master id {doc_ref}")

status_code_re = re.compile(r"^(?:[A-H]-\d|K-STAR$|REGION-S$)")
for record in visas:
    code = record.get("code")
    if not isinstance(code, str) or not status_code_re.match(code):
        continue
    procedures = record.get("procedures") or {}
    audit = record.get("manualRequiredDocAudit")
    for proc_name in ("extension", "registration"):
        proc = procedures.get(proc_name)
        if not isinstance(proc, dict):
            errors.append(f"{code}: missing procedures.{proc_name}")
            continue
        refs = proc.get("manualRefs")
        docs_group = proc.get("requiredDocs")
        if not isinstance(refs, list) or not refs:
            errors.append(f"{code}.{proc_name}: missing manualRefs")
        if not isinstance(docs_group, dict) or not isinstance(docs_group.get("requiredDocs"), list):
            errors.append(f"{code}.{proc_name}: requiredDocs.requiredDocs must be a list")
    if not isinstance(audit, dict):
        errors.append(f"{code}: missing manualRequiredDocAudit")
    elif audit.get("manualVersion") != "2026.5":
        errors.append(f"{code}: manualRequiredDocAudit.manualVersion must be 2026.5")

if errors:
    raise SystemExit("\\n".join(errors))
PY

echo "[3/4] Running git diff --check..."
git diff --check -- index.html visa_data.json doc_master.json scripts/check_repo.sh docs/data docs/design

echo "[4/4] Scanning key user-facing files for forbidden branding strings..."
KEY_FILES=(
  "index.html"
  "ai.html"
  "visa_data.json"
  "moonshot_backend_fastapi.py"
)

FORBIDDEN_REGEX='Moonshot|moonshot|Paradiso 39|PARADISO 39|paradiso 39|Paradiso39|PARADISO39|paradiso39|P/39|p39'

EXISTING_FILES=()
for file in "${KEY_FILES[@]}"; do
  if [[ -f "$file" ]]; then
    EXISTING_FILES+=("$file")
  else
    echo "INFO: Skipping missing optional file: $file"
  fi
done

if [[ ${#EXISTING_FILES[@]} -eq 0 ]]; then
  echo "WARNING: No key files found to scan."
else
  if command -v rg >/dev/null 2>&1; then
    if rg -n -i -e "$FORBIDDEN_REGEX" "${EXISTING_FILES[@]}"; then
      echo "ERROR: Found forbidden branding string(s) in key user-facing files." >&2
      exit 1
    fi
  else
    echo "INFO: ripgrep (rg) not found; using grep fallback."
    if grep -RniE "$FORBIDDEN_REGEX" "${EXISTING_FILES[@]}"; then
      echo "ERROR: Found forbidden branding string(s) in key user-facing files." >&2
      exit 1
    fi
  fi
fi

echo "Success: repository validation passed. JSON is valid, representative manual schema is valid, git diff check is clean, and no forbidden branding strings were found in existing key user-facing files."
