#!/usr/bin/env bash
set -euo pipefail

echo "[1/3] Validating visa_data.json format..."
python3 -m json.tool visa_data.json > /tmp/visa_data_check.json

echo "[2/3] Running git diff --check..."
git diff --check

echo "[3/3] Scanning key user-facing files for forbidden branding strings..."
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

echo "Success: repository validation passed. JSON is valid, git diff check is clean, and no forbidden branding strings were found in existing key user-facing files."
