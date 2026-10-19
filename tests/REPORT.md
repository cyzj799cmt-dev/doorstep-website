# Test report

Browser: Chromium (Playwright 1.5x, headless), axe-core 4.10.2. Runner: `python tests/run_tests.py`.
The per-check table from the last run is in [`results.md`](results.md): **69 checks, 69 passed**.

## What was tested

| Area | How |
|---|---|
| Screenshots | 17 pages × 2 languages × 390×844 and 1440×900, full page, in `screenshots/{en,pl}/`. A second set built with `SHOW_PLACEHOLDER_HIGHLIGHTS=False` is in `screenshots/no-highlights/`, and the consent banner on mobile is `consent-banner-mobile.png`. All were reviewed by eye. |
| Links and anchors | Every page in the normal build and in a build served under `/doorstep/` (GitHub project page): every internal `href`/`src`/`action` returns 200, every `#anchor` exists, every PL/EN switch points to the same `page_id` in the other language with `hreflang` and `lang`, `<html lang>` is right, hreflang `en`/`pl`/`x-default` is on every page, `sitemap.xml` lists exactly the indexable pages with alternates, and external URLs are well-formed. |
| Accessibility | axe-core (WCAG 2.0/2.1/2.2 A+AA and best practice) on all 34 pages at desktop and mobile: zero serious or critical violations. Keyboard-only journey: skip link → home door card → students → "Send my dates" → empty submit (focus moves to the error summary) → fix by keyboard → submit, with focus visibility checked on every Tab stop. Focus-not-obscured: Tab through three long pages at 390 px with the sticky header and bar. |
| Interactions | Mobile menu (Esc closes and returns focus), partners disclosure on mobile and desktop, FAQ + `faq_open`, copy-link + `share_copy`, map facade → titled iframe (and the no-JS map link), empty-submit error summary and inline errors with `aria-describedby`, `form_error` without values, valid submit to a mocked endpoint → `/thanks/?form=search` with `generate_lead` (`form_id`, `persona`, `lang` only, no name or email), hidden fields and honeypot in the POST body, `?for=parent` and referring-page preselect, UTM capture into hidden fields, consent (nothing before a choice; Reject → no GTM/GA requests; Accept → GTM requested, verified by network interception; choice persists; "Cookie settings" reopens), banner above the sticky bar, JavaScript off (nav visible, forms post with native `required`), GSAP loads only without reduced motion and leaves all content visible. |
| Layout | No horizontal overflow at 320, 390, 768, 1024 and 1440 px on all 34 pages. Tap targets ≥ 44 px on mobile. Polish diacritics: latin-ext files for all three families load on `/pl/`, and `document.fonts.check` passes for ąćęłńóśźż. |
| Content | Banned-word / all-caps / `!!!` lint on both copy files, no `lorem`/`TODO`, no unresolved `[[…]]`, CHECKLIST.md matches the placeholders found on each page and lists every CONFIG item, one `h1` per page with no skipped heading levels, CSS 34 KB (< 40), JS 19 KB (< 25), and in no-highlight mode no label leaks and no dangling "Label:" sentences. |
| Lighthouse (extra, mobile) | Performance 91–97, Accessibility 100, Best Practices 100 on `/`, `/students/`, `/pl/rodzice/` and `/start/`, measured against the local Python server, which does not gzip (GitHub Pages does). SEO is 42 while `site_url` is empty, because the site is deliberately `noindex`. With `site_url` set, SEO is 100 on `/`, `/pl/rodzice/` and `/guides/fake-listings/`. |

## What failed, and what was fixed

1. **Header overflow on mobile (46 px at 390 px).** `.btn{display:inline-flex}` overrode `.header-cta{display:none}` (same specificity, later rule). Fixed by scoping it to `.site-header .header-cta`.
2. **Overflow at 320 px on `/pl/rodzice/` and `/pl/wynajmujacy/`.** Grid tracks grew to the min-content of placeholder captions, long confirm values and a long CTA. Fixed with `min-width:0` on grid children, `overflow-wrap` on record and table values, and `max-width:100%` on buttons.
3. **Focus hidden behind the sticky action bar** (radio buttons and footer links on `/students/` at 390 px). Chromium ignores `scroll-padding` when moving focus by Tab. Fixed with a small `focusin` handler that scrolls the focused element clear of the header, the bar and the consent banner. With JavaScript off, the header and bar are not sticky, so nothing can cover focus.
4. **No visible focus on the date field's calendar button.** It lives in the input's shadow DOM, so `:focus`/`:focus-visible` don't match the input. Fixed with `:focus-within` on form inputs and a ring on `::-webkit-calendar-picker-indicator`.
5. **Hidden-highlight mode leaked or left gaps.** The `data-fill-label="FILL IN"` attribute was always present; "Email:" stayed with no address; "One-page summary (PDF):" stayed with no link; there were empty `<p>`/`<dd>` for named contacts and team facts; and, found in screenshot review, the check-us list showed ticks with no text. All are now rendered only when there is something to show, and the no-backend form message is plain text.
6. **Polish H1 auto-hyphenated** ("miesz-kanie", "Warsza-wie"), found in screenshot review. Removed `hyphens:auto`.
7. **Parents CTA split into three columns** because a confirm span inside an `inline-flex` button became its own flex item. The label is now wrapped in one span.
8. **GSAP reveal left elements invisible after a jump** (IntersectionObserver never fires for elements skipped by an anchor link or the End key). The reveal is now based on scroll position, also runs on focus, and is skipped entirely for reduced motion.
9. **Copy lint:** "najlepsze" in the Polish universities copy, and five meta titles or descriptions over the length limit. Rewritten.
10. **Build: an empty environment variable overwrote a filled CONFIG value** (relevant on GitHub Actions when a repository variable is unset). Now only non-empty variables override.
11. Test-side fixes: the FAQ check now waits for the async `toggle` event. In the keyboard journey the date is set with `fill()`, because Chromium orders date segments by OS locale; every other field is typed by keyboard.

## Deliberate choices

- `/thanks/` is `noindex` and left out of `sitemap.xml`; the sitemap lists the 16 indexable pages × 2 languages.
- **Motion:** the brief allows only hover and focus transitions up to 150 ms. At the owner's request there is also a minimal, optional GSAP layer: a stamp "press" on the hero card and a 0.5 s fade-up for sections below the fold. It is off for `prefers-reduced-motion`, never hides content without JavaScript, and is removed with `USE_GSAP = False`.
- Next.js was considered and not used. The brief requires no framework or bundler, and plain static output deploys to GitHub Pages without any adapter.
