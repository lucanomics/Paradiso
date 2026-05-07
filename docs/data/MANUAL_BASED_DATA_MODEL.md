# Manual-Based Visa Data Model

## Why the Flat Model Is Insufficient

Paradiso's legacy visa records were useful for search, but they treated each visa as a mostly flat card. That makes it hard to distinguish a base code such as `F-6` from a detailed subcode such as `F-6-1`, and it blends visa issuance, stay procedures, required documents, warnings, and source references into one body of text.

The 2026.5 Ministry of Justice manuals are procedure-oriented. A manual-based interface therefore needs structured data that can answer: which manual domain applies, which procedure is being requested, which subcode is relevant, which documents belong to that procedure, and whether the information has been verified against the manual.

## Base Code and Subcode Model

Each base visa record should keep the existing `code`, `name`, `cat`, and legacy search fields for compatibility, while adding manual-aware fields:

- `code`: base code, for example `F-6`
- `nameKo` / `nameEn`: display names
- `subcodes`: detailed subcodes, each with `code`, `nameKo`, `summary`, `eligibility`, and `manualRefs`
- `manualDomains`: one or both of `visa_issuance` and `stay_sojourn`

The UI should always render subcodes in a separate “세부코드” section. Subcodes must not be hidden only inside prose.

## Manual Domain and Procedure Model

Manual domains answer which source manual governs a record:

- `visa_issuance`: 사증민원 manual
- `stay_sojourn`: 체류민원 manual

Procedures answer what the applicant is trying to do. Supported procedure keys are:

- `visaIssuance`
- `certificateOfVisaIssuance`
- `statusGrant`
- `statusChange`
- `extension`
- `registration`
- `activitiesOutsideStatus`
- `workplaceChange`
- `reentry`

Each procedure should include `available`, `eligibility`, grouped `requiredDocs`, `notes`, and `manualRefs`. If a procedure is plausible but not yet verified, it should be visible only with `매뉴얼 확인 필요` rather than invented document content.

## Required Documents

Procedure document groups should use document IDs from `doc_master.json` or clear literal text when no master document exists yet:

- `commonDocs`
- `requiredDocs`
- `additionalDocs`
- `conditionalDocs`

Legacy arrays such as `newReqDocs`, `initialReqDocs`, `extReqDocs`, `extensionReqDocs`, and `changeReqDocs` remain valid during migration. Rendering code must adapt both old and new structures.

## Manual References

Manual references should describe the source, not overstate verification:

- `manualName`
- `manualVersion`
- `pageRange`
- `confidence`
- `needsManualReview`

Representative data in this PR uses `2026.5` manual versions and marks page ranges as needing review unless they have been manually verified. Existing `visa_data.json` and `doc_master.json` are implementation data, not source truth.

## Migration Plan

1. Keep old fields working for search and modals.
2. Add manual-aware fields to representative records only.
3. Verify high-priority categories against the 2026.5 manuals.
4. Expand procedure-specific document groups category by category.
5. Add page ranges only after direct manual review.
6. Remove legacy duplication only after the full dataset has a verified migration path.

## Data Safety Rules

- Do not invent legal content.
- Do not claim full dataset accuracy from representative samples.
- Use `needsManualReview: true` when page references or procedure documents are not confirmed.
- Keep source manual facts separate from implementation convenience fields.
