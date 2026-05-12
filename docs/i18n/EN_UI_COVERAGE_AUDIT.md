# English UI Coverage Audit

## What remained Korean

After PR #31, `UI_TRANSLATIONS.en` covered the upper landing flow, but several visible lower sections in `index.html` still rendered Korean in English mode. The largest gap started at the scrolled landing section headed `복잡한 체류, Paradiso에서 손쉽게.` Search result cards also used Korean UI labels and Korean visa names as the primary title.

## Fixed in this PR

- Lower landing sections now use the existing language system for English mode, including the brand hero, feature section, pathway/how/source/tool/reminder sections, platform/about copy, roadmap copy, footer hero, and final CTA.
- Registered-agent finder labels, empty/error states, map/copy/phone action labels, and result counts now switch through localized UI strings.
- Search result cards use English names as the primary title in English mode when structured English fields exist, with Korean retained as secondary context.
- Result chrome such as subcode counts, data date labels, manual domain badges, review labels, source labels, procedure headings, document group headings, warnings, and actions now switches to English in English mode.

## Intentionally Korean

Korean manual/source body text remains visible when the structured data only has Korean content. This includes source excerpts, document names from Korean manuals, agency names/addresses, and legal/manual terminology that has not yet been extracted into English fields.

## Manual QA checklist

- Switch the language menu to English and confirm the top hero remains English.
- Scroll to the lower brand hero and confirm the `Complex stay procedures` headline is visible.
- Confirm lower CTA/footer sections are English.
- Search `D-2`, `E-7`, `F-6`, and `F-6-1` in English mode.
- Confirm result labels/counts are English and English visa names appear first when available.
- Switch back to Korean and confirm the Korean landing/search flow still renders.
