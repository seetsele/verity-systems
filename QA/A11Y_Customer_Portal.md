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
