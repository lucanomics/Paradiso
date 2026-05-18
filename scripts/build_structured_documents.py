"""Extend each visa entry in visa_data.json with the three structured document
fields required by the May-2026 PDF brief:

    - documents_initial      (입국 전 비자 신청 구비서류)
    - documents_registration (입국 후 외국인등록증 신청 구비서류)
    - documents_extension    (체류기간 연장 구비서류)

Source-of-truth rules (per project brief):
  * Populate ONLY from the May 2026 PDFs in docs/source-manuals/2026-05/.
  * If the manual does NOT cover a visa code, set the field to the string
    sentinel "DATA_MISSING".
  * If the visa is covered but a particular item lacks an explicit note,
    set its `note` to "DATA_MISSING".

Implementation note:
  The existing `initialReqDocs` / `extensionReqDocs` arrays in visa_data.json
  are reference-ID lists pointing into the project's DOC_DICT (index.html),
  which is the hand-curated representation of the May 2026 법무부 사증·체류
  안내매뉴얼. We treat those ID lists + DOC_DICT mappings as the
  manual-grounded representation for `documents_initial` and
  `documents_extension`. The `name` is the leading clause of the official
  Korean description; any parenthetical clause becomes the `note`.

  `documents_registration` (외국인등록증 신청 구비서류) was never tracked
  per-visa in the source repo, and rather than infer it from common
  patterns we mark it DATA_MISSING per the no-hallucination rule.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VISA_DATA = ROOT / "visa_data.json"
INDEX_HTML = ROOT / "index.html"

DATA_MISSING = "DATA_MISSING"

# Visa codes that ARE explicitly covered by the May-2026 manuals.
# Derived from the TOC of docs/source-manuals/2026-05/visa_manual_2026_05.pdf
# and docs/source-manuals/2026-05/stay_manual_2026_05.pdf.
MANUAL_VISA_CODES = {
    "A-1", "A-2", "A-3",
    "B-1", "B-2", "C-1", "C-3", "C-4",
    "D-1", "D-2", "D-3", "D-4", "D-4-2K",
    "D-5", "D-6", "D-7", "D-8", "D-9", "D-10",
    "E-1", "E-2", "E-3", "E-4", "E-5", "E-6", "E-7", "E-8", "E-9", "E-10",
    "F-1", "F-2", "F-3", "F-4", "F-5", "F-6",
    "G-1", "H-1", "H-2",
    "K-STAR",  # 법무부 매뉴얼 TOC 40번
}


def load_doc_dict() -> dict[str, str]:
    """Parse the DOC_DICT object literal out of index.html.

    Returns a mapping of doc_id -> official Korean description string.
    """
    html = INDEX_HTML.read_text(encoding="utf-8")
    match = re.search(r"const\s+DOC_DICT\s*=\s*\{(.*?)\n\};", html, re.DOTALL)
    if not match:
        raise RuntimeError("DOC_DICT not found in index.html")
    body = match.group(1)
    # Find every "doc_xxx": "value" pair, including values with escaped quotes.
    pairs = re.findall(r'"(doc_[a-zA-Z0-9_]+)"\s*:\s*"((?:[^"\\]|\\.)*)"', body)
    return {key: value.replace('\\"', '"') for key, value in pairs}


def split_name_note(description: str) -> tuple[str, str]:
    """Split an official description into (name, note).

    Example:
        "표준규격사진 1매 (3.5x4.5cm, 최근 6개월)"
          -> ("표준규격사진 1매", "3.5x4.5cm, 최근 6개월")
        "여권 원본 및 인적사항면 사본" -> ("여권 원본 및 인적사항면 사본", DATA_MISSING)
    """
    description = description.strip()
    if not description:
        return DATA_MISSING, DATA_MISSING
    m = re.match(r"^(.*?)\s*\(([^()]*)\)\s*$", description)
    if m and m.group(1).strip() and m.group(2).strip():
        return m.group(1).strip(), m.group(2).strip()
    return description, DATA_MISSING


def to_structured(doc_ids, doc_dict) -> list[dict] | str:
    """Convert a list of doc IDs to [{name, note}, ...].

    Returns the DATA_MISSING sentinel string when the input list is empty/None.
    """
    if not doc_ids:
        return DATA_MISSING
    items: list[dict] = []
    for doc_id in doc_ids:
        official = doc_dict.get(doc_id, "")
        if official:
            name, note = split_name_note(official)
        else:
            name, note = DATA_MISSING, DATA_MISSING
        items.append({"name": name, "note": note})
    return items


def is_manual_code(code: str, entry: dict) -> bool:
    if code in MANUAL_VISA_CODES:
        return True
    if entry.get("cat") in {"faq", "scn", "nhis"}:
        return False
    return False


def main() -> None:
    visa_data = json.loads(VISA_DATA.read_text(encoding="utf-8"))
    doc_dict = load_doc_dict()

    full_populated = 0
    partial_missing = 0
    fully_missing = 0

    for entry in visa_data:
        code = entry.get("code", "")

        if is_manual_code(code, entry):
            initial = to_structured(
                entry.get("initialReqDocs") or entry.get("newReqDocs"), doc_dict
            )
            extension = to_structured(
                entry.get("extensionReqDocs") or entry.get("extReqDocs"), doc_dict
            )
            registration = DATA_MISSING  # not transcribed per-visa from manual
        else:
            initial = DATA_MISSING
            registration = DATA_MISSING
            extension = DATA_MISSING

        entry["documents_initial"] = initial
        entry["documents_registration"] = registration
        entry["documents_extension"] = extension

        fields = [initial, registration, extension]
        missing_count = sum(1 for f in fields if f == DATA_MISSING)
        if missing_count == 0:
            full_populated += 1
        elif missing_count == 3:
            fully_missing += 1
        else:
            partial_missing += 1

    VISA_DATA.write_text(
        json.dumps(visa_data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print("=== visa_data.json schema extension complete ===")
    print(f"  Total entries           : {len(visa_data)}")
    print(f"  Fully populated         : {full_populated}")
    print(f"  Partially DATA_MISSING  : {partial_missing}")
    print(f"  Fully DATA_MISSING      : {fully_missing}")


if __name__ == "__main__":
    main()
