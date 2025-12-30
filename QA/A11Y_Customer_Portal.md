# Accessibility QA: Customer Portal

Summary:
- Performed automated accessibility scans and fixes for `public/customer-portal.html`.
- Added ARIA regions for hero, demo terminal, and floating cards; added skip link; associated labels; added SVG titles; marked decorative icons `aria-hidden`.

Scans & Reports (saved in `reports/`):
- Axe (before): `reports/axe-customer-portal-public.json` (region/landmark failures)
- Axe (after): `reports/axe-customer-portal-postfix.json` (0 violations)
- Lighthouse accessibility: `reports/lighthouse-accessibility-postfix.json` and `reports/lighthouse-accessibility.html`

Files changed (branch `qa/customer-portal-a11y`):
- `public/customer-portal.html` — ARIA/semantic improvements, label/link fixes, skip link and focus styles.
- `reports/*` — axe & Lighthouse reports and HTML output

Manual checks performed:
- Verified skip link and `#main` target.
- Validated keyboard focus styles and tab order.
- Confirmed OAuth dev banner is an ARIA live region (`role="status" aria-live="polite"`).

Remaining recommended actions:
1. Manual cross-browser visual checks (Chrome, Firefox, Edge, Safari) and capture screenshots. (Playwright installation was started; screenshots pending.)
2. Run color-contrast checks (WCAG 2.1 AA) across key elements (hero title, action buttons, badges).
3. Add screenshots to `reports/screenshots/` and attach them to the PR.
4. Consider running a repo-wide axe scan and triaging other pages referenced in `reports/`.

How to reproduce local checks:
- Start static server: `npm run dev` (runs `python -m http.server 8000`)
- Run axe: `npx @axe-core/cli http://localhost:8000/public/customer-portal.html --save ./reports/axe-customer-portal-postfix.json`
- Run lighthouse: `npx lighthouse http://localhost:8000/public/customer-portal.html --only-categories=accessibility --output=html --output-path=./reports/lighthouse-accessibility.html`

PR & Next steps:
- Branch: `qa/customer-portal-a11y` (pushed)
- Create PR at: https://github.com/seetsele/verity-systems/pull/new/qa/customer-portal-a11y

If you want, I can:
- Finish Playwright screenshots and attach them to the PR, or
- Run color-contrast checks and add a small patch for any low-contrast elements.

Contact: dev+support@verity.com

---

## Update (2025-12-30)
- **Added** an interactive comparison UI at `public/compare.html` (search + provider filters) to help decision makers explore feature differences.
- **Scans run:** axe & Lighthouse on `index.html`, `compare.html`, and `customer-portal.html`. Reports saved under `reports/` with timestamps in filenames (e.g., `axe-compare-fresh.json`, `lighthouse-index-fresh.json`).
- **Results:**
  - `compare.html` — 0 axe violations after fixes; Lighthouse accessibility report saved.
  - `customer-portal.html` — 0 axe violations; Lighthouse report saved.
  - `index.html` — axe found a small set of issues (button-name for `#mobileMenuBtn`, link-name for `.footer-logo`, color-contrast issue `.demo-hint`, plus many `region` / landmark warnings across the page). Recommend triaging high-severity issues first (button/link names and color-contrast).

**Next steps:**
- Address the `index.html` findings (add accessible labels to mobile menu & footer links, improve contrast for low-contrast elements) and re-run scans.
- Capture cross-browser screenshots for the compare page and attach them to the PR.
- Update the PR description to include these fresh reports and a short summary of the remaining index issues.

