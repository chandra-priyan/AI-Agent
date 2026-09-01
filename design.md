# Design — Autonomous Data Scientist

A locked design system for this app. Every page redesign reads this file before emitting code. Do not regenerate per page — extend or amend this file when the system needs to grow.

## Genre
modern-minimal

## Theme
- `--color-paper`: #FFFFFF (white)
- `--color-paper-2`: #F4F4F5 (light ash)
- `--color-ink`: #111111 (black)
- `--color-ink-2`: #18181B (dark text)
- `--color-accent`: #6D28D9 (primary violet)
- `--color-rule`: #E4E4E7 (border)
- `--color-text-secondary`: #71717A (secondary text)
- `--color-success`: #16A34A
- `--color-warning`: #D97706
- `--color-error`: #DC2626

## Typography
- Display: Inter, weight 500/600, style normal (roman)
- Body: Inter, weight 400
- Mono: SF Mono, JetBrains Mono, Fira Code, monospace, weight 400
- Display tracking: -0.02em
- Type scale anchor:
  - Page titles: 28px - 32px
  - Section headings: 18px - 20px
  - Body text: 14px - 16px
  - Secondary/Caption: 12px - 14px

## Spacing
4-point named scale. Pages must use named custom property tokens (`var(--space-md)`), never raw values.

## Motion
- Easings: cubic-bezier(0.16, 1, 0.3, 1) named `--ease-out`
- Reveal pattern: opacity-only fade, 150ms.
- Reduced-motion fallback: opacity-only, ≤ 150ms.

## Microinteractions stance
- Silent success (no promotional toasts)
- Hover delay: 200ms transitions
- Active state transition: scale(0.98) or background-color tint.

## CTA voice
- Primary CTA: solid background, ink-contrast text, sharp/restrained border radius.
- Secondary CTA: border outlines, subtle hover background color changes.

## Per-page allowances
- App pages: no heavy rounded corners, no gradients, flat colors, high data density.

## What pages MUST share
- Sidebar layouts, monochrome page headers, and standard borders.
- Monotype status badges.

## Exports

### tokens.css
```css
:root {
  --color-paper: #FFFFFF;
  --color-paper-2: #F4F4F5;
  --color-ink: #111111;
  --color-ink-2: #18181B;
  --color-rule: #E4E4E7;
  --color-accent: #6D28D9;
  --color-text-secondary: #71717A;
  --color-success: #16A34A;
  --color-warning: #D97706;
  --color-error: #DC2626;

  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --font-mono: 'JetBrains Mono', 'Geist Mono', 'SF Mono', monospace;

  --space-3xs: 0.25rem;
  --space-2xs: 0.5rem;
  --space-xs: 0.75rem;
  --space-sm: 1.0rem;
  --space-md: 1.5rem;
  --space-lg: 2.0rem;
  --space-xl: 3.0rem;

  --text-xs: 0.75rem;    /* 12px */
  --text-sm: 0.875rem;   /* 14px */
  --text-base: 1.0rem;   /* 16px */
  --text-lg: 1.125rem;   /* 18px */
  --text-xl: 1.25rem;    /* 20px */
  --text-2xl: 1.75rem;   /* 28px */
  --text-3xl: 2.0rem;    /* 32px */

  --radius-sm: 4px;
  --radius-md: 6px;
  --radius-lg: 8px;

  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
  --dur-short: 180ms;
}
```
