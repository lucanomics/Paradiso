# Manual-Based Interface Rebuild Review

## Designer Diagnosis

The previous result interface read like a flat legal note card. It surfaced a visa code and a few document buttons, but it did not make the code hierarchy obvious, did not separate issuance from stay procedures, and forced users to infer subcodes from body text.

For a civic-tech product, that creates avoidable risk. Users need a calm hierarchy that shows what is known, what is procedure-specific, and what still requires manual confirmation.

## Redesigned Information Hierarchy

The rebuilt result anatomy should be:

1. base code and names
2. manual domain badges
3. verification/review badge
4. explicit subcode section
5. procedure controls
6. procedure-specific document groups
7. common warning box
8. source reference block
9. optional action buttons for existing modals and AI analysis

This gives users a stable scan path: identify the visa, choose the procedure, read only the documents for that procedure, then verify caveats and source status.

## Result Card Anatomy

The card header should show:

- base code badge
- Korean name and English name when available
- domain badge for 사증발급, 체류민원, or 공통/양쪽
- review badge for 2026.5 manual status
- stay period cap when available

The expanded body should not be a wall of text. Subcodes use compact cards. Procedure content sits behind segmented controls so required documents are comparable but not all dumped onto the screen at once.

## Mobile Behavior

The mobile layout should be single-column with no horizontal page overflow. Procedure tabs may scroll horizontally inside their own row, but the page itself must stay within the viewport. Korean text should use readable line-height and `word-break: keep-all` where it improves comprehension.

## Accessibility Concerns

- Procedure buttons need visible active and inactive states.
- Disabled procedures should be muted but still understandable.
- Source and warning boxes need clear visual distinction without alarmist styling.
- Controls should remain keyboard reachable through native buttons.
- Text must not rely on color alone; labels carry meaning.

## Deferred Improvements

- Manual page-linked citations after source PDFs are committed and audited.
- Full dataset migration for every visa category.
- Better document master normalization for vague placeholder IDs.
- Procedure filtering from search intent, for example searching “F-6 연장” directly opening the extension panel.
- More explicit screen-reader roles for tab/panel relationships after the static markup stabilizes.
