# Registered immigration agent finder — scaffold

Status: **placeholder / sample data only.** Not production-ready and not a substitute for the official directory.

This document describes the scaffold added to `index.html` (section `#agentFinder`, titled "가까운 행정 도움 찾기") and the seed dataset at `data/registered_agents.json`.

## Purpose

Provide a future-ready, accessible UI surface so users can browse officially registered Korean immigration civil-affairs agencies (출입국민원 대행기관) by region, search by keyword, copy addresses, and jump out to Naver Map / Kakao Map for directions.

The shipped scaffold renders sample rows only. The intent is to wire up a vetted dataset later, sourced from the official directory below.

## Official source

- 하이코리아 — 출입국민원 대행기관 조회:
  https://www.hikorea.go.kr/cvlappl/CvlapplAgentInfo.pt

The UI links out to this URL from the disclaimer and from the error state. Paradiso does not scrape, mirror, or guarantee freshness of the official registry; users are directed to consult it before relying on any listing.

## Files in this scaffold

| Path | Purpose |
| --- | --- |
| `data/registered_agents.json` | Seed dataset. Sample-only. Every agency has `is_sample: true` and a name prefixed with `[샘플]`. `_meta.is_sample` and `_meta.data_status: "placeholder"` are set. |
| `index.html` (section `#agentFinder`) | UI: sample banner, official-source disclaimer, region filter, keyword search, result count, agency cards (네이버지도 / 카카오맵 / 주소 복사 / 전화), empty + error states. |
| `index.html` (script tail) | Loader: fetches the JSON, populates regions, filters, renders cards, handles address-copy with clipboard fallback. |

## Data shape

```jsonc
{
  "_meta": {
    "is_sample": true,
    "data_status": "placeholder",
    "official_source_url": "https://www.hikorea.go.kr/cvlappl/CvlapplAgentInfo.pt",
    "official_source_label": "하이코리아 — 출입국민원 대행기관 조회",
    "last_reviewed": "YYYY-MM-DD",
    "schema_version": 1,
    "agency_fields": ["id", "name", "region", "address", "phone", "registration_no", "map_query", "is_sample"]
  },
  "regions": ["서울", "경기·인천", "..."],
  "agencies": [
    {
      "id": "sample-seoul-1",
      "name": "[샘플] ...",
      "region": "서울",
      "address": "서울특별시 ...",
      "phone": "",
      "registration_no": "",
      "map_query": "서울 ...",
      "is_sample": true
    }
  ]
}
```

Field notes:

- `name` — display name. Sample rows MUST start with `[샘플]`.
- `region` — must match a string from `regions`.
- `address` — full Korean address. If empty, the card omits both the `<address>` line and the `주소 복사` button.
- `phone` — optional. If empty, the phone button is omitted. If present, format `02-000-0000` style for display; the `tel:` href is stripped of non-digit/`+`/`-` characters.
- `map_query` — short string passed (URL-encoded) to Naver Map and Kakao Map search URLs. Fall back is `address`, then `name`.
- `is_sample` — required `true` on every sample row.

## UI behavior

- The sample-data banner renders only when `_meta.is_sample === true`.
- Result count copy:
  - With an active region/keyword filter: `전체 N개 중 M개 샘플 항목 표시` (or `… 대행기관 표시` when not sample).
  - With no filter: `M개의 샘플 항목 표시` (or `… 대행기관 표시` when not sample).
- Empty state: shown when filtered results are zero.
- Error state: shown when `fetch` rejects or the response is not OK; links the official source.

## Map links

- Naver: `https://map.naver.com/p/search/{encodeURIComponent(map_query)}`
- Kakao: `https://map.kakao.com/link/search/{encodeURIComponent(map_query)}`

No Naver/Kakao SDKs are embedded; these are plain outbound links. No geolocation permission is requested.

## Address copy

The `주소 복사` button is rendered only when `address` is present. It uses `navigator.clipboard.writeText` when available, and falls back to a hidden `<textarea>` + `document.execCommand('copy')` otherwise. Feedback uses the existing `showToast` convention (`success` on copy, `warning` on failure).

## Updating the dataset later

When real data is curated:

1. Verify each row against the official Hi Korea directory immediately before publishing.
2. Drop the `[샘플]` prefix from `name` and set `is_sample: false` per row.
3. Set `_meta.is_sample: false` and `_meta.data_status` to a non-placeholder value (e.g., `"curated"`).
4. Update `_meta.last_reviewed`.
5. Confirm `regions[]` still matches the union of `region` values across `agencies[]`.

Until those steps are completed, the sample banner remains visible to users, the placeholder status is preserved, and the disclaimer continues to point users to the official directory.

## Out of scope (intentionally not in this scaffold)

- No scraping or automated harvesting of the registry.
- No OCR.
- No GPS, "current location", or `navigator.geolocation` usage.
- No Naver / Kakao / Google map SDKs or API keys embedded.
- No recommendation, ranking, or endorsement of specific agencies.
