# Test results

Run: 2026-10-19 12:32 · 68 checks · **68 passed, 0 failed** · 36 s


## content

| Result | Check | Detail |
|---|---|---|
| PASS | banned-word / caps / !!! lint passes on en.yml and pl.yml |  |
| PASS | every [[…]] token is resolved in the output |  |
| PASS | no lorem / TODO text in the output |  |
| PASS | CHECKLIST.md matches the 89 placeholder keys found on pages |  |
| PASS | CHECKLIST.md lists every CONFIG item |  |
| PASS | style.css under 40 KB (33 KB) |  |
| PASS | site.js under 25 KB (19 KB) |  |
| PASS | one h1 per page, no skipped heading levels |  |

## links

| Result | Check | Detail |
|---|---|---|
| PASS | site/: every internal href returns 200 (43 unique paths) |  |
| PASS | site/: every #anchor target exists |  |
| PASS | site/: external links are well-formed |  |
| PASS | site/: every PL/EN switch points to the same page_id in the other language |  |
| PASS | site/: hreflang en, pl and x-default on every page |  |
| PASS | site/: <html lang> matches the page language |  |
| PASS | site/: every root-relative URL starts with the base path / |  |
| PASS | site/: sitemap.xml lists exactly the indexable built pages (32) |  |
| PASS | site/: sitemap has hreflang alternates for every URL |  |
| PASS | base path /doorstep/: every internal href returns 200 (43 unique paths) |  |
| PASS | base path /doorstep/: every #anchor target exists |  |
| PASS | base path /doorstep/: external links are well-formed |  |
| PASS | base path /doorstep/: every PL/EN switch points to the same page_id in the other language |  |
| PASS | base path /doorstep/: hreflang en, pl and x-default on every page |  |
| PASS | base path /doorstep/: <html lang> matches the page language |  |
| PASS | base path /doorstep/: every root-relative URL starts with the base path /doorstep/ |  |
| PASS | base path /doorstep/: sitemap.xml lists exactly the indexable built pages (32) |  |
| PASS | base path /doorstep/: sitemap has hreflang alternates for every URL |  |

## content

| Result | Check | Detail |
|---|---|---|
| PASS | SHOW_PLACEHOLDER_HIGHLIGHTS=False: no highlight markup or labels in the output |  |
| PASS | hidden mode: sentences around empty FILL IN items still read correctly |  |

## a11y

| Result | Check | Detail |
|---|---|---|
| PASS | axe-core: zero serious or critical violations on 34 pages × 2 viewports | {} |
| PASS | axe-core: moderate/minor findings (informational) | {'moderate:landmark-unique': 4, 'moderate:landmark-complementary-is-top-level': 4} |

## keyboard

| Result | Check | Detail |
|---|---|---|
| PASS | first Tab focuses the skip link |  |
| PASS | skip link moves focus to <main> |  |
| PASS | home: Tab reaches the students door card |  |
| PASS | door card opens /students/ with Enter |  |
| PASS | students: 'Send my dates' jumps to the inline form |  |
| PASS | empty submit by keyboard moves focus to the error summary |  |
| PASS | valid keyboard submit without a backend shows the FILL IN notice |  |
| PASS | focus is visible on every element reached by Tab |  |
| PASS | mobile: no focused element is hidden behind the sticky header or action bar |  |

## interact

| Result | Check | Detail |
|---|---|---|
| PASS | mobile menu opens, closes with Esc and returns focus |  |
| PASS | partners disclosure opens inside the mobile menu |  |
| PASS | desktop partners disclosure opens, closes with Esc, focus returns |  |
| PASS | FAQ <details> opens and pushes faq_open |  |
| PASS | copy-link copies the page URL and pushes share_copy |  |
| PASS | map facade loads nothing until clicked, then injects a titled Google Maps iframe |  |
| PASS | plain 'Open in Google Maps' link is present |  |
| PASS | empty submit: error summary shown and focused, inline errors linked by aria-describedby |  |
| PASS | form_error carries only form_id and field_count |  |
| PASS | ?for=parent preselects 'My child' on /start/ |  |
| PASS | UTMs from the landing page are carried into hidden form fields |  |
| PASS | referring persona page preselects 'Who is searching' (professional) |  |
| PASS | valid submit posts to the endpoint and redirects to /thanks/?form=search |  |
| PASS | generate_lead pushed with form_id, persona, lang and no personal data |  |
| PASS | thanks page shows the message for the search brief |  |
| PASS | submission includes hidden fields (form_id, utm_*, referrer) and the honeypot |  |
| PASS | consent banner shows on first visit; nothing loads before a choice |  |
| PASS | Reject: no GTM/GA requests, choice stored with a date |  |
| PASS | Reject persists across pages (banner hidden, still no requests) |  |
| PASS | footer 'Cookie settings' reopens the banner |  |
| PASS | Accept: GTM loads (verified by network interception) |  |
| PASS | consent banner does not cover the sticky action bar |  |
| PASS | JS off: navigation visible, forms have action/method/required, map link works |  |
| PASS | GSAP loads when motion is allowed; revealed content ends fully visible |  |
| PASS | prefers-reduced-motion: GSAP is not loaded |  |

## layout

| Result | Check | Detail |
|---|---|---|
| PASS | no horizontal overflow at 320, 390, 768, 1024 and 1440 px |  |
| PASS | tap targets ≥ 44px on mobile (buttons, links styled as targets, form controls) |  |
| PASS | Polish diacritics render in all three fonts (latin-ext files load on /pl/) |  |
| PASS | document.fonts.check passes for ąćęłńóśźż in every family |  |
