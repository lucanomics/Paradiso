# Visual Reference Redesign: Paradiso Lower Sections

## Core Visual Strategy: The "Civic Glass" Direction
The lower sections of the Paradiso landing page will transition entirely to a **calm, light-filled civic gateway**. The heavy, dark oceanic themes, jarring solid color blocks (like bright coral or heavy dark green), and dark gradient overlays will be removed. 

The new layout relies on a soft warm ivory/sand base (`#fcfaf5`), acting as a clean canvas. Content is organized into "frosted glass" cards with very light, airy shadows and translucent borders, conveying transparency and public trust. The Jeju-inspired atmosphere is maintained through highly desaturated, low-opacity background textures or clean, rounded editorial image inserts, rather than full-screen dark overlays.

### Section-by-Section Visual Reference

#### 1. Feature / Value Cards (StatBridge)
*   **Current Issue:** Heavy dark green and solid coral backgrounds create a segmented, heavy feel.
*   **Redesign:** Change all solid-colored cards to a translucent white (`bg-white/60`) over the warm sand background. Apply a subtle backdrop blur.
*   **Interaction:** On hover, cards subtly lift (`translate-y-1`) with a soft glow in the mint brand color, rather than dramatic color changes. Text remains dark civic green (`#085E48`) for maximum readability.

#### 2. Architecture & Trust (FeatureTrust)
*   **Current Issue:** Technical grids and contrasting primary colors (Red/Green/Blue) feel too much like a B2B SaaS product.
*   **Redesign:** Remove the harsh technical grid. Use soft, organic spacing. The three layers (Data, Intelligence, Application) are presented as floating white panels separated by thin, elegant divider lines (`border-[#085E48]/5`). Accent icons use a soft mint or subtle coral wash, entirely avoiding harsh tech-style contrasts.

#### 3. Anagram Transition (DIASPORA -> PARADISO)
*   **Current Issue:** Typically relies on a dark background to make the animation "pop."
*   **Redesign:** Keep the background light ivory. The wordmark is rendered in dark civic green. The SVG connecting lines that map the anagram are rendered in a delicate, semi-transparent mint (`rgba(14, 163, 123, 0.4)`). The transition feels like fine ink on premium paper—quiet, elegant, and highly legible.

#### 4. Footer & Closing CTA
*   **Current Issue:** Uses a heavy dark green background with a black gradient overlay (`bg-gradient-to-t from-black/80`), making it feel disconnected and heavy.
*   **Redesign:** Remove the black gradient completely. Place the Jeju forest image at 15-20% opacity using `mix-blend-multiply` or `mix-blend-luminosity` directly over the warm sand background. 
*   **Typography:** Change all footer text from white to the dark civic green (`#085E48`). The large Paradiso brush wordmark should be applied in a muted dark green or soft mint to blend naturally into the paper-like background. Buttons become solid civic green instead of white/glass.

---

## Implementation Handoff

**Background & Canvas System**
*   **Base Color:** Force `#fcfaf5` on all section wrappers. Remove any `bg-[#085E48]` or `bg-black/80` full-width backgrounds.
*   **Dividers:** Avoid hard visual stops between sections. Use generous vertical padding (`py-32`) and subtle 1px lines (`bg-[#085E48]/5`) to separate thoughts.

**Card & Container System**
*   **Glass Setup:** `bg-white/60 backdrop-blur-md`
*   **Borders:** `border border-[#085E48]/5` or `border-white/40`
*   **Shadows:** `shadow-[0_8px_30px_rgba(8,94,72,0.03)]` (Extremely soft, large spread, very low opacity).

**Typography Hierarchy**
*   **Headings:** `text-[#085E48] tracking-tight`. No white text in the lower sections except inside primary CTA buttons.
*   **Body:** `text-[#085E48]/70` or `text-[#085E48]/60`. Ensure contrast ratios remain accessible while feeling soft.
*   **Accents:** Use soft mint (`#0EA37B`) or coral (`#FF8C7A`) sparingly for small labels or active states.

**What to Strip Out (CSS / Selectors to Update)**
*   Remove all `text-white` classes from headings and paragraphs in the lower sections (especially `FooterCTA`).
*   Remove `bg-[#085E48]` from card backgrounds (replace with glass variants).
*   Remove `from-black/80 via-black/40` overlay gradients.
*   Remove any hard drop-shadows or playful rotate/scale hover effects on the Bento layout. Replace with reduced-motion-safe, soft opacity or slight shadow lifts.