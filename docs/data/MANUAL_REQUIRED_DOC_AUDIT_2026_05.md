# 2026.5 Required Document Audit

## Scope

This audit pass checks the current `visa_data.json` stay-status records against the locally supplied `체류민원_0504.pdf` manual.

- Source: `체류민원_0504.pdf`
- Manual version: 2026.5
- Publisher: Ministry of Justice, Korea Immigration Service
- Page count checked locally: 774 pages
- Data scope: 체류기간 연장, 체류자격 변경, 체류자격 부여, 자격외활동, 근무처 변경·추가, 재입국, 외국인등록 수수료 안내 and existing required-document procedures

The pass updates all current regular/special stay records that map to a manual section: `A-1` through `H-2`, `F-4`, `K-STAR`, and `REGION-S`. Non-status helper records such as FAQ, scenario, common-warning, and K-ETA records are not treated as visa/stay categories in this pass.

## What Changed

Each audited stay record now has:

- `procedures.extension`
- `procedures.registration`
- `manualRequiredDocAudit`
- `sourceManualStatus.stayManualVersion = "2026.5"`
- `sourceManualStatus.needsManualReview = true`

Where the PDF text extraction produced a clean document list, the list is reflected in the procedure-specific `requiredDocs.requiredDocs` group. Where the extracted text was ambiguous, mixed with adjacent procedures, or not clearly a document list, the UI-facing list is set to `매뉴얼 확인 필요`.

The search UI also applies the common 2026.5 stay-manual fee table to every available stay procedure:

- 자격외활동 and 근무처 변경·추가: government revenue stamp 120,000 KRW
- 체류자격 부여: government revenue stamp 80,000 KRW
- 체류자격 변경: government revenue stamp 100,000 KRW, with F-5 at 200,000 KRW and F-6 at 40,000 KRW
- 체류기간 연장: government revenue stamp 60,000 KRW, with F-6 at 30,000 KRW
- 재입국: single 30,000 KRW, multiple 50,000 KRW
- 외국인등록증 발급 및 재발급: 35,000 KRW

## Confidence Model

This is not a final legal data verification.

The manual is a scanned/structured PDF with page text that sometimes merges headings, repeated lines, table cells, and adjacent procedures. For that reason:

- `auto_extracted_needs_review` means the item came from the 2026.5 stay manual but still requires human source-page review.
- `needs_manual_review` means the system found the manual section but did not safely structure a UI-facing list.
- `verified` remains `false` for all records updated in this pass.

## Known Manual-Review Hotspots

The following categories need a human second pass before they should be marked verified:

- `F-6`: multiple subcases (`F-6-1`, `F-6-2`, `F-6-3`) and life-event conditions.
- `D-2` / `D-4`: school, program, certification, and institutional status exceptions.
- `E-7`: occupational-code-specific guarantees and extra evidence.
- `F-2` / `F-5`: points, income, criminal-record, family, and special-track variants.
- `H-2` / `F-4`: overseas Korean rules and employment-management variants.
- `K-STAR`: F-2/F-5/family-track documents are grouped in the special-track manual section.
- `REGION-S`: regional/special-track pilots need separate track-level modeling.

## Do Not Claim

Do not mark any updated record as fully verified until a human reviewer checks the page references against the 2026.5 manual PDFs and confirms that procedure-specific exceptions have been modeled.
