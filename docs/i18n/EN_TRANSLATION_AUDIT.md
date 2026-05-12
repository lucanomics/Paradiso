# English UI Translation Audit

Scope: `UI_TRANSLATIONS.en` inside `index.html` only. Korean source (`UI_TRANSLATIONS.ko`)
was treated as authoritative. Other language packs (zh, zhHant, ja, fr, id, hi, ne,
es, esLatam, th, vi, km, ar, mn, fa, ru) were not modified in this pass.

## Summary of findings

- **Key parity**: `en` has every top-level key present in `ko`. No missing keys, no
  extra keys.
- **Array length parity**: `landingHints` (14 items) and `quickFilters` (13 items)
  match `ko` in both length and order.
- **Korean leakage**: one Hangul character left inside an English string —
  `landingHints[9]` was literally `'TB certificate 대상'`. This is the most critical
  defect found.
- **Terminology consistency**: a few strings used overly bureaucratic or dated
  English (e.g. "Alien registration", "Admin tools", "Public-source based",
  "Final check with official sources"). These were normalised to plain,
  public-service English while keeping the underlying meaning.
- **Legal disclaimer overclaiming risk**: the existing `reference` string already
  disclaims legal advice, but referred to "application agency service", which is
  not standard English in the Korean immigration context. The task brief asks for
  "filing service" or "representation service". Updated accordingly.
- **Punctuation**: `dataReady` used a hyphen between the count and source; the
  Korean source has a unitless count. Both were tightened (em dash, explicit
  "items").
- **Brand voice**: `heroSub` second clause re-used the brand name awkwardly
  ("Paradiso keeps the path connected to official sources"). Replaced with a
  brand-neutral phrasing.
- **No structural changes** were made to `tx()`, `applyLanguage()`,
  `LANGUAGE_OPTIONS`, CSS, search logic, visa data, or layout. No HTML markup
  outside the translations object was touched.

## Changed keys

| Key | Old English | Revised English | Reason |
| --- | --- | --- | --- |
| `heroTitle` | `Moved by what matters.` | `Moved by what matters,` | Korean source uses a comma to flow into `heroEm`; the previous period broke that flow. |
| `heroSub` | `Explore Korea's 39 residence statuses by purpose and situation.<br>Paradiso keeps the path connected to official sources.` | `Explore Korea's 39 residence statuses by purpose and situation.<br>Every path stays connected to official sources.` | Brand name was already in `heroEyebrow`; second clause now reads as plain public-service copy. |
| `proof1` | `Public-source based` | `Based on public sources` | Natural English word order. |
| `proof3` | `Final check with official sources` | `Always verify with official sources` | Clearer call to action; matches the civic-tech intent of the Korean source. |
| `toolsLabel` | `Admin tools` | `Administrative tools` | "Admin" reads as IT/system administration; the section is civic administrative tools. |
| `qaAria` | `Frequently used admin tools` | `Frequently used administrative tools` | Same reason, consistency with `toolsLabel`. |
| `jurisdiction` | `Find immigration office jurisdiction` | `Find your immigration office` | "Jurisdiction" as a noun was awkward; the tool finds the office that has jurisdiction over the user. |
| `visaLabel` | `Choose stay pathway` | `Choose a residence pathway` | "Stay pathway" is not idiomatic; "residence pathway" matches `heroEyebrow`/`heroSub` terminology. |
| `inTrackDesc` | `Alien registration, extension, status change, and other in-Korea stay services` | `Foreigner registration, extension of stay, status change, and other in-Korea services` | Korean source is "외국인등록" (foreigner registration). "Alien" is dated; "Foreigner registration" matches modern Korean Immigration Service English usage while remaining recognisable. |
| `dataReady` | `Data loaded ({count}) - {source}` | `Data loaded ({count} items) — {source}` | Adds an explicit unit; uses an em dash separator. Placeholders preserved. |
| `sourceStatic` | `static backup` | `Static backup` | Sentence-case to match other source labels. |
| `sourceOffline` | `offline built-in data` | `Offline built-in data` | Same; capitalisation only. |
| `reference` | `Paradiso provides reference information based on public laws and manuals. It is not legal advice or application agency service. Confirm final decisions with immigration offices, HiKorea, or a qualified professional.` | `Paradiso provides reference information based on public laws and official manuals. It is not legal advice, and it is not a filing or representation service. Please confirm any final decision with an immigration office, HiKorea, or a qualified professional.` | Per brief: replace "application agency service" with filing/representation wording. Slightly softened tone ("Please confirm"). No legal overclaiming. |
| `landingHints[3]` | `Same-day/exception visit` | `Same-day expiry / special cases` | Original Korean is "만료 당일/임산부 등" (expiration day / pregnant women etc.) — not about visit type. New phrasing is accurate without listing specific demographic groups. |
| `landingHints[8]` | `F-3 income requirement` | `Dependent (F-3) income` | Korean source is "동반(F-3) 소득요건"; "Dependent" preserves the F-3 family-companion context. |
| `landingHints[9]` | `TB certificate 대상` | `TB certificate requirement` | **Critical**: Korean Hangul leakage. "대상" means "those it applies to". Replaced with plain English. |

## Items intentionally not changed

- `heroEyebrow` — Brand line; already concise and consistent.
- `entryATitle` / `entryASub` / `entryBTitle` / `entryBSub` — Readable; reflect the
  Korean source faithfully. "I can only explain my situation" is slightly stilted
  but is the user's voice, not the app's voice, so left as-is.
- `searchOpen` / `searchOpenAria` / `searchClose` — Clear.
- `jobCode` ("Occupation and industry codes") — Tool label is accurate; matches
  the Korean "취업신고용 업종·직종 코드" closely enough.
- `preTrackTitle` / `preTrackDesc` / `inTrackTitle` / `preTrackAria` / `inTrackAria`
  — Acceptable; only the description of the in-track was adjusted (see table).
- `qAria` / `qPlaceholder` / `dataLoading` / `xbAria` / `submitSearch` — Standard
  microcopy.
- `ctrlsAria` / `fold` / `unfold` / `hintsTitle` / `hintsAria` — Standard.
- `aiSecondaryAria` / `aiLink` / `scrollAria` — Standard.
- `sourceApi` (`API`) — Concise and unambiguous in context.
- `landingHints` items not listed in the changed table — Already clean English,
  consistent with the Korean source.
- `quickFilters` — All entries are short tags that already read naturally in
  English; no changes.

## Out of scope

- The page contains additional Korean-only HTML (e.g. the jurisdiction help card
  in the markup around lines 4960–4980) which is not part of `UI_TRANSLATIONS`.
  Internationalising those static blocks is a larger refactor and was explicitly
  out of scope for this pass.
- The Korean, Chinese (both variants), Japanese, and Russian translation packs
  were not edited per the brief, even where they appear to contain minor leakage
  from other scripts.
