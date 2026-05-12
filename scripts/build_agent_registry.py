#!/usr/bin/env python3
"""Build the official civil petition proxy agency registry JSON.

The source workbook is published by the Korean immigration service as
"출입국업무 민원신청대행 등록기관 현황".  This script intentionally uses only
the standard library so the generated JSON is reproducible in the static site
repo without external data dependencies.
"""

from __future__ import annotations

import json
import re
import sys
import zipfile
from collections import OrderedDict
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
SOURCE_XLSX = ROOT / "data" / "sources" / "민원대행_등록기관_2026-04-30.xlsx"
OUT_JSON = ROOT / "data" / "agent_registry_2026-04-30.json"
SOURCE_DATE = "2026-04-30"
SOURCE_LABEL = "출입국업무 민원신청대행 등록기관 현황"
OFFICIAL_SOURCE_URL = "https://www.hikorea.go.kr/cvlappl/CvlapplAgentInfo.pt"

MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
NS = {"a": MAIN_NS, "r": REL_NS, "pr": PKG_REL_NS}

EXPECTED_HEADERS = {
    "A": "연번",
    "B": "대행기관명",
    "C": "대행기관 주소",
    "D": "전화번호",
}

PROVINCE_ALIASES = {
    "서울특별시": "서울",
    "부산광역시": "부산",
    "대구광역시": "대구",
    "인천광역시": "인천",
    "광주광역시": "광주",
    "대전광역시": "대전",
    "울산광역시": "울산",
    "세종특별자치시": "세종",
    "경기도": "경기",
    "강원특별자치도": "강원",
    "강원도": "강원",
    "충청북도": "충북",
    "충청남도": "충남",
    "전북특별자치도": "전북",
    "전라북도": "전북",
    "전라남도": "전남",
    "경상북도": "경북",
    "경상남도": "경남",
    "제주특별자치도": "제주",
}


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def column_name(cell_ref: str) -> str:
    match = re.match(r"[A-Z]+", cell_ref or "")
    return match.group(0) if match else ""


def load_shared_strings(zf: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in zf.namelist():
        return []
    root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    values: list[str] = []
    for item in root.findall("a:si", NS):
        values.append("".join(t.text or "" for t in item.findall(".//a:t", NS)))
    return values


def cell_value(cell: ET.Element, shared_strings: list[str]) -> str:
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        return "".join(t.text or "" for t in cell.findall(".//a:t", NS)).strip()
    value = cell.find("a:v", NS)
    if value is None or value.text is None:
        return ""
    raw = value.text.strip()
    if cell_type == "s":
        return shared_strings[int(raw)].strip()
    return raw.strip()


def workbook_sheet_paths(zf: zipfile.ZipFile) -> list[tuple[str, str]]:
    workbook = ET.fromstring(zf.read("xl/workbook.xml"))
    rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    rel_map = {rel.attrib["Id"]: rel.attrib["Target"] for rel in rels}
    paths: list[tuple[str, str]] = []
    for sheet in workbook.findall("a:sheets/a:sheet", NS):
        rid = sheet.attrib.get(f"{{{REL_NS}}}id")
        target = rel_map.get(rid or "")
        if not target:
            continue
        if target.startswith("/"):
            path = target.lstrip("/")
        else:
            path = "xl/" + target.lstrip("./")
        paths.append((sheet.attrib.get("name", "Sheet"), path))
    return paths


def read_first_sheet_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        fail(f"source XLSX not found: {path}")
    with zipfile.ZipFile(path) as zf:
        shared_strings = load_shared_strings(zf)
        sheet_paths = workbook_sheet_paths(zf)
        if not sheet_paths:
            fail("workbook does not contain any worksheets")
        _, sheet_path = sheet_paths[0]
        sheet = ET.fromstring(zf.read(sheet_path))
        rows: list[dict[str, str]] = []
        for row in sheet.findall("a:sheetData/a:row", NS):
            row_values = {
                column_name(cell.attrib.get("r", "")): cell_value(cell, shared_strings)
                for cell in row.findall("a:c", NS)
            }
            if any(row_values.values()):
                rows.append(row_values)
        return rows


def find_header_index(rows: list[dict[str, str]]) -> int:
    for idx, row in enumerate(rows):
        if all(row.get(col) == header for col, header in EXPECTED_HEADERS.items()):
            return idx
    fail("could not find expected headers: 연번, 대행기관명, 대행기관 주소, 전화번호")


def normalize_phone(phone: str) -> str:
    return re.sub(r"\s+", " ", str(phone or "")).strip()


def display_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone)
    if len(digits) == 11 and digits.startswith("010"):
        return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
    if len(digits) == 10 and digits.startswith("02"):
        return f"{digits[:2]}-{digits[2:6]}-{digits[6:]}"
    if len(digits) == 9 and digits.startswith("02"):
        return f"{digits[:2]}-{digits[2:5]}-{digits[5:]}"
    if len(digits) == 10:
        return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
    return ""


def parse_regions(address: str) -> tuple[str, str]:
    parts = [p for p in re.split(r"\s+", address.strip()) if p]
    if not parts:
        return "", ""
    province = parts[0]
    city_or_district = ""
    for part in parts[1:4]:
        clean = part.rstrip(",")
        if re.search(r"(시|군|구)$", clean):
            city_or_district = clean
            break
    return province, city_or_district


def normalized_search_text(*parts: str) -> str:
    text = " ".join(str(part or "") for part in parts)
    text = re.sub(r"\s+", " ", text).strip().lower()
    compact_phone = re.sub(r"\D", "", text)
    return f"{text} {compact_phone}".strip()


def build_records(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    header_idx = find_header_index(rows)
    records: list[dict[str, str]] = []
    for row in rows[header_idx + 1 :]:
        serial = row.get("A", "").strip()
        name = row.get("B", "").strip()
        address = row.get("C", "").strip()
        phone = normalize_phone(row.get("D", ""))
        if not (serial or name or address or phone):
            continue
        if not (serial and name and address):
            fail(f"incomplete registry row after header: {row}")
        province, city_or_district = parse_regions(address)
        record: OrderedDict[str, str] = OrderedDict()
        record["id"] = f"agent-{int(float(serial)):04d}" if re.fullmatch(r"\d+(?:\\.0)?", serial) else f"agent-{serial}"
        record["serial_number"] = str(int(float(serial))) if re.fullmatch(r"\d+(?:\\.0)?", serial) else serial
        record["name"] = name
        record["address"] = address
        record["phone"] = phone
        pretty_phone = display_phone(phone)
        if pretty_phone and pretty_phone != phone:
            record["display_phone"] = pretty_phone
        record["province"] = province
        record["region1"] = province
        record["province_short"] = PROVINCE_ALIASES.get(province, province)
        record["city_or_district"] = city_or_district
        record["region2"] = city_or_district
        record["normalized_search_text"] = normalized_search_text(
            name,
            address,
            phone,
            pretty_phone,
            province,
            PROVINCE_ALIASES.get(province, ""),
            city_or_district,
        )
        record["source_date"] = SOURCE_DATE
        record["source_label"] = SOURCE_LABEL
        records.append(record)
    return records


def build_payload(records: list[dict[str, str]]) -> OrderedDict:
    regions = list(OrderedDict.fromkeys(record["province"] for record in records if record.get("province")))
    payload: OrderedDict = OrderedDict()
    payload["_meta"] = OrderedDict(
        [
            ("is_sample", False),
            ("data_status", "official_registry"),
            ("source_date", SOURCE_DATE),
            ("source_label", SOURCE_LABEL),
            ("official_source_url", OFFICIAL_SOURCE_URL),
            ("source_file", "data/sources/민원대행_등록기관_2026-04-30.xlsx"),
            ("supporting_pdf", "data/sources/민원대행_등록기관_2026-04-30.pdf"),
            ("schema_version", 2),
            (
                "agency_fields",
                [
                    "id",
                    "serial_number",
                    "name",
                    "address",
                    "phone",
                    "province",
                    "region1",
                    "city_or_district",
                    "region2",
                    "normalized_search_text",
                    "source_date",
                    "source_label",
                ],
            ),
        ]
    )
    payload["regions"] = regions
    payload["agencies"] = records
    return payload


def print_validation(records: list[dict[str, str]]) -> None:
    print(f"total record count: {len(records)}")
    print("first 3 records:")
    print(json.dumps(records[:3], ensure_ascii=False, indent=2))
    for term in ["강릉", "안산", "제주", "비자"]:
        needle = term.lower()
        count = sum(1 for record in records if needle in record.get("normalized_search_text", ""))
        print(f"sample search count [{term}]: {count}")


def main() -> int:
    rows = read_first_sheet_rows(SOURCE_XLSX)
    records = build_records(rows)
    if not records:
        fail("no agency records generated from source XLSX")
    payload = build_payload(records)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print_validation(records)
    return 0


if __name__ == "__main__":
    sys.exit(main())
