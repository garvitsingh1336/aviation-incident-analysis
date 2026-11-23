# Design System Specification: Luxury Editorial Real Estate Aesthetic

Inspired by **Ronas IT | UI/UX Team: "Luxury Real Estate Agency Website Design"** (Dribbble shot `27242101`).

---

## 1. Design Philosophy & Aesthetic Core

The goal of this design system is to transform standard dashboard interfaces into a **high-end, editorial, quiet-luxury experience**. It moves away from cold corporate tech blues and sterile dashboards toward a warm, cultured, architectural presence reminiscent of high-end design publications (Kinfolk, Architectural Digest, Sotheby's International Realty).

### Key Pillars:
1. **Milky Beige & Charcoal Contrast**: A warm, serene oyster/parchment background (`#f8f6f0` to `#f3efe6`) paired with deep, velvety charcoal typography (`#121212` and `#242422`) instead of generic grays.
2. **Refined Editorial Typography**: High-contrast, expressive serif headlines for section titles and brand presentation paired with crisp geometric sans-serif for numbers, metadata, and body copy.
3. **Generous White Space & Micro-Borders**: Breathing room between cards, razor-thin borders (`1px solid rgba(18, 18, 18, 0.08)`), and soft layered shadows that feel floating rather than flat.
4. **Subtle Warm Gold & Bronze Accents**: Understated champagne/bronze accents (`#c5a059` and `#b08844`) that evoke craftsmanship, luxury, and prestige without being garish.
5. **Architectural Card Architecture**: Cards feature rounded, tactile radii (`14px`), gentle border highlights, and delicate backdrop blurs.

---

## 2. Color Palette & Tokens

### Light Theme (Default: Architectural Warmth)
| Token | Hex / Value | Description |
| :--- | :--- | :--- |
| `--page` | `#f8f6f0` | Soft milky beige/warm ivory canvas |
| `--surface-1` | `#ffffff` | Pure ivory surface for cards and primary containers |
| `--surface-2` | `#f1eee5` | Secondary container wash, inputs, table rows on hover |
| `--surface-3` | `#e7e3d6` | Elevated borders and divider backgrounds |
| `--text-primary` | `#161614` | Deep charcoal black for headlines and prominent text |
| `--text-secondary` | `#4a4740` | Muted taupe/charcoal for subtitles and descriptions |
| `--muted` | `#868175` | Warm stone gray for metadata, timestamps, badges |
| `--border` | `rgba(22, 22, 20, 0.08)` | Ultra-fine architectural borders |
| `--border-strong` | `rgba(22, 22, 20, 0.16)` | Focused borders and prominent card dividers |
| `--accent` | `#b58d4a` | Refined warm gold / champagne bronze |
| `--accent-hover` | `#9c7634` | Deep bronze hover state |
| `--accent-wash` | `rgba(181, 141, 74, 0.12)` | Subtle tinted glow for active tabs and badges |

### Dark Theme (Nocturne Luxury: Charcoal & Onyx)
| Token | Hex / Value | Description |
| :--- | :--- | :--- |
| `--page` | `#10100e` | Deep obsidian & warm charcoal background |
| `--surface-1` | `#191816` | Dark espresso/charcoal card surface |
| `--surface-2` | `#23221e` | Elevated dark stone surface |
| `--surface-3` | `#2d2b26` | Deep divider borders and secondary widgets |
| `--text-primary` | `#f5f3ec` | Warm alabaster white for crisp reading |
| `--text-secondary` | `#b8b4a8` | Warm gray secondary text |
| `--muted` | `#7a776e` | Muted bronze-slate for timestamps and secondary metrics |
| `--border` | `rgba(245, 243, 236, 0.08)` | Delicate luminous borders |
| `--border-strong` | `rgba(245, 243, 236, 0.16)` | Prominent card dividers |
| `--accent` | `#d4ab63` | Radiant warm champagne gold |
| `--accent-wash` | `rgba(212, 171, 99, 0.15)` | Subtle golden ambient glow |

### Luxury Data Visualization & Accent Series
* **Series 1 (Champagne Bronze)**: `#b58d4a`
* **Series 2 (Terracotta Amber)**: `#c76943`
* **Series 3 (Earthy Sage / Olive)**: `#3e8265`
* **Series 4 (Warm Saffron)**: `#d49b28`
* **Series 5 (Dusty Plum / Rose)**: `#a4597b`
* **Series 6 (Deep Slate Forest)**: `#2d6653`
* **Series 7 (Smoky Amethyst)**: `#6e5b9e`
* **Series 8 (Heritage Crimson)**: `#b84242`

---

## 3. Typography Hierarchy

```css
--font-display: 'Playfair Display', 'Cormorant Garamond', 'Didot', 'Georgia', serif;
--font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
```

* **Display & Hero Titles**: Modern high-contrast serif font (`Playfair Display` or `Georgia`), letter-spacing: `-0.02em`, font-weight `600` or `500`.
* **Section Headers (`h2`, `h3`)**: Serif with subtle tracking and balanced line-heights.
* **Badges, Metrics, & Navigation**: Crisp, highly legible Sans-Serif (`Inter`), uppercase tracking `+0.05em` on small micro-labels.
* **Body Copy**: Refined sans-serif with generous line-height (`1.6`) for optimal editorial readability.

---

## 4. UI Components & Patterns

### 1. Navigation & Brand Header
* **Sidebar**:
  * Clean vertical orientation with a refined champagne-gold monogram logo.
  * Active navigation items feature a soft gold wash background (`--accent-wash`), a dedicated left accent bar, and high-contrast charcoal text.
  * Subtle hover transitions (`cubic-bezier(0.16, 1, 0.3, 1)`).
* **Topbar**:
  * Frosted glass blur effect (`backdrop-filter: blur(12px)`).
  * Prominent serif title with subtitle highlighting the analytical intelligence suite.
  * Sleek theme switch and status pills.

### 2. Analytical Cards & Metric Tiles
* Rounded corners: `14px`.
* Soft elevated drop shadows: `0 4px 20px rgba(0, 0, 0, 0.04), 0 1px 3px rgba(0, 0, 0, 0.02)`.
* Card headers with subtle category tags and gold numeral callouts.

### 3. Search & Interactive Elements
* Floating capsule-style search input with generous padding and warm ivory background.
* Filter pills with soft rounded outlines and active bronze fill.
* Clean SVG charts styled with the warm heritage palette.

---

## 5. Application to Aviation Incident Intelligence

Translating this luxury design into the Aviation Incident Analysis application:
* Incident cards are formatted like exclusive dossier profiles.
* Top metrics (Total Reports, Discovered Topics, Contributing Factors, Trend Trajectories) look like curated portfolio metrics.
* The 2D incident cluster map and co-occurrence graphs use soft golden, bronze, and sage coordinates.
* Semantic search feels like a refined concierge search engine for complex aviation intelligence.
