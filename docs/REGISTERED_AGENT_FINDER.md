# Registered immigration agent finder

Status: **official registry data integrated** from the uploaded Ministry of Justice / HiKorea source workbook dated 2026-04-30.

## Source of truth

- XLSX source: `data/sources/민원대행_등록기관_2026-04-30.xlsx`
- Supporting PDF reference: `data/sources/민원대행_등록기관_2026-04-30.pdf`
- Generated JSON: `data/agent_registry_2026-04-30.json`
- Official source label: `출입국업무 민원신청대행 등록기관 현황`

The XLSX is the source of truth. The PDF is retained only as supporting source evidence.

## Build

Run:

```bash
python3 scripts/build_agent_registry.py
```

The script uses only the Python standard library to read the workbook XML and writes deterministic JSON. It prints the total record count, first three records, and sample search counts for `강릉`, `안산`, `제주`, and `비자`.

## UI behavior

`index.html` loads `data/agent_registry_2026-04-30.json` in the `#agentFinder` section.

The finder supports keyword matching by agency name, address, province/city keyword, and phone fragments through each record's `normalized_search_text`. The region filter is generated from the actual dataset's province values, not hardcoded sample regions.

The UI displays a clear source/date note and does not fall back to sample data when the JSON cannot be loaded. If loading fails, it shows the error state and leaves the result list empty.
