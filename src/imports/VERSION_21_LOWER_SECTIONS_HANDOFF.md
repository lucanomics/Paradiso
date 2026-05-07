# Version 21: Paradiso Lower Sections Visual Reference & Handoff

## 1. Visual Reference (Version 21)

*This is a conceptual blueprint for the HTML/CSS implementation of the lower landing sections, grounded in the actual `index.html` structure.*

### General Atmosphere: "Civic Glass & Jeju Light"
The page sheds the heavy ocean backgrounds and aggressive dark-mode blocks of older versions. As the user scrolls below the primary Hero, the background transitions to a warm, soft ivory (`#fcfaf5`). All information panels sit on this canvas as delicate, frosted glass layers, casting very diffuse, low-opacity shadows. 

### Section-by-Section Breakdown

**A. Recommended Keywords (`landing-hints-section`)**
*   **Visual:** A gentle row of pill-shaped tags floating over the sand background.
*   **Style:** Background `rgba(255, 255, 255, 0.6)` with backdrop-blur. Text is dark civic green (`#085E48`). On hover, a soft lift (`translate-Y: -2px`) and the border turns a subtle mint (`rgba(14, 163, 123, 0.4)`).
*   **Vibe:** Unobtrusive, helpful public signage.

**B. Brand Bridge / Anagram Section (`brandHero` / `figma-brand-bridge`)**
*   **Visual:** The DIASPORA → PARADISO anagram animation.
*   **Style:** No dark or harsh gradient backgrounds. The canvas remains warm ivory. The large letters are strong, confident dark green. The connecting SVG tracking lines are drawn in a highly transparent mint green (`rgba(14, 163, 123, 0.3)`). 
*   **Vibe:** Like an elegant infographic printed on premium, heavy stationery. Clear, quiet, intelligent.

**C. Feature Spotlight (`brandFeature` / `figma-feature-section`)**
*   **Visual:** A split layout. One side contains refined typography explaining the platform's utility; the other side contains an abstract, soft-edged, light-filled aesthetic image (e.g., blurred light passing through glass or very light Jeju foliage, *not* a tourist destination shot).
*   **Style:** The text is highly legible Pretendard (`#085E48`). Badges or small accents use soft coral (`#FF8C7A`) sparingly. 
*   **Vibe:** Professional civic tech.

**D. Platform About / Values & Roadmap (`aboutMe` / `figma-about-section`)**
*   **Visual:** A bento-style grid of translucent glass cards detailing "브랜드 철학", "핵심 가치", "로드맵".
*   **Style:** Cards use a "Civic Glass" treatment: `background: rgba(255, 255, 255, 0.7)`, `backdrop-filter: blur(12px)`, `border: 1px solid rgba(8, 94, 72, 0.06)`. 
*   **Shadows:** `box-shadow: 0 10px 40px -10px rgba(8, 94, 72, 0.04)`.
*   **Vibe:** Organized, accessible, and structured, preventing the "scrapbook chaos" feeling.

---

## 2. What Was Inherited from Version 20
*   **Spacing Rhythm:** The generous vertical padding (`padding-top/bottom: 120px` to `160px`) that gives the content room to breathe.
*   **Glass/Light Layering:** The foundational concept of using frosted/translucent containers to separate content without resorting to harsh solid boxes.
*   **Color Palette:** The sophisticated combination of dark civic green (`#085E48`), mint (`#0EA37B`), warm sand/ivory (`#fcfaf5`), and coral (`#FF8C7A`).
*   **Card Hierarchy:** Grouping complex bureaucratic information into digestible, distinct "bento" style chunks.

## 3. What Was Improved in Version 21
*   **Total Removal of "Heavy" Elements:** Stripped away all deep sea/ocean photographic backgrounds and dark-mode gradient overlays from the lower sections. The page now feels consistently illuminated and trustworthy from top to bottom.
*   **Enhanced Readability (Civic Trust):** Text is now predominantly high-contrast dark green against off-white/glass backgrounds, moving away from "white text on dark backgrounds" which felt too much like a trendy SaaS or luxury portfolio.
*   **Brand De-cluttering:** Removed all references to the old "Paradiso 39" branding, symbol, and the explanatory tagline. Paradiso stands alone as a singular, confident brand name.
*   **Anti-Tourism Guardrails:** Shifted imagery and layouts to ensure it feels like a modern *public-service tool* (like a beautifully designed GovTech portal), rather than a travel agency selling Jeju vacation packages.

---

## 4. Implementation Handoff (Single-File HTML/CSS)

This guide provides the exact CSS strategies needed to update `index.html` to Version 21.

### A. Background Strategy
*   **Global Canvas:** `body { background-color: #fcfaf5; color: #085E48; }`
*   **Remove Old Backgrounds:** Search the CSS for any classes like `.figma-brand-bridge`, `.figma-about-section`, or `.footer-hero` that contain `background-image: url(...)`, `background: #085E48`, or `background: linear-gradient(...)` and **delete them**. 
*   **Sections:** Sections should be `background: transparent;` so the global sand color flows through seamlessly.

### B. Card Strategy (Civic Glass)
Update your CSS card classes (e.g., `.feature-card`, `.value-card`, `.roadmap-item`) to this standardized glass system:
```css
.civic-glass-card {
    background: rgba(255, 255, 255, 0.65);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(8, 94, 72, 0.06);
    border-radius: 24px;
    box-shadow: 0 12px 40px -12px rgba(8, 94, 72, 0.05);
    color: #085E48;
}
```

### C. Section Separation Strategy
*   Do not use different colored background strips to separate sections.
*   Use pure whitespace: `margin-bottom: 120px;` or `padding: 100px 0;`.
*   If a visual break is strictly necessary, use a hairline divider: `border-top: 1px solid rgba(8, 94, 72, 0.08);` with generous padding.

### D. Typography Hierarchy
*   **Headings (`h2`, `h3`):** `color: #085E48; font-weight: 700; letter-spacing: -0.02em;`
*   **Body (`p`):** `color: rgba(8, 94, 72, 0.75); font-weight: 500; line-height: 1.6;`
*   **Accents/Labels:** `color: #0EA37B; font-weight: 600; font-size: 0.85rem; letter-spacing: 0.05em; text-transform: uppercase;`
*   **Strip Whites:** Remove `color: #ffffff;` or `color: var(--t1)` (if it maps to white) from all lower-section text.

### E. Image Usage Strategy
*   **No Background Photos in Content Areas:** Do not use photos behind text.
*   **Floating Asset Placement:** If Jeju/nature images are used in lower sections, they should be placed inside contained elements (e.g., `border-radius: 24px; overflow: hidden;`) floating next to the text, acting as editorial inserts rather than heavy full-screen immersive backgrounds.

### F. Interaction Strategy
*   **Hover states:** Restrict to soft `.civic-glass-card:hover { transform: translateY(-3px); box-shadow: 0 16px 50px -10px rgba(8, 94, 72, 0.08); border-color: rgba(14, 163, 123, 0.2); }`. 
*   **Buttons:** Primary actions should be solid mint (`bg-[#0EA37B]`) or dark green (`bg-[#085E48]`) with white text.

### G. Strict Removal Checklist
1.  **Delete** the "39 — 출입국관리법령상..." text block.
2.  **Delete** any P/39 logo images (`<img>` or `background-image`).
3.  **Delete** all `.dark-mode`, `theme="dark"`, or gradient overlay CSS applied below the fold.
4.  **Delete** complex 3D hover effects (like tilt.js or extreme scale transitions) on the bento cards. Keep it flat and civic.