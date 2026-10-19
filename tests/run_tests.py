#!/usr/bin/env python3
"""Doorstep browser tests: Playwright (Chromium) + axe-core.

    pip install -r tests/requirements.txt && python -m playwright install chromium
    python tests/run_tests.py              # everything
    python tests/run_tests.py --quick      # skip screenshots

Builds four variants of the site:
  site/                         the normal build (highlights on), what you deploy
  .test-build/hidden/           SHOW_PLACEHOLDER_HIGHLIGHTS=False, for the second screenshot set
  .test-build/wired/            gtm_id + form_endpoint set to test values, for consent and submit tests
  .test-build/bp/doorstep/      BASE_PATH=/doorstep/, as on a GitHub project page
serves each with Python's http.server, and writes tests/results.md.
Exit code 1 if anything fails.
"""
import argparse
import functools
import http.server
import json
import os
import re
import subprocess
import sys
import threading
import time
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
TESTS = ROOT / "tests"
SHOTS = TESTS / "screenshots"
AXE = TESTS / "vendor" / "axe.min.js"
sys.path.insert(0, str(ROOT))
import build  # noqa: E402

RESULTS = []
CONSENT_SET = ("localStorage.setItem('doorstep_consent', JSON.stringify("
               "{v:1,analytics:false,marketing:false,date:'2026-10-19'}))")
DL_LOG = """
(function(){
  var dl = window.dataLayer = window.dataLayer || [];
  var push = dl.push;
  dl.push = function(){
    var r = push.apply(dl, arguments);
    try {
      var log = JSON.parse(sessionStorage.getItem('__dl') || '[]');
      for (var i = 0; i < arguments.length; i++) { var a = arguments[i]; if (a && a.event && !a['gtm.start']) log.push(a); }
      sessionStorage.setItem('__dl', JSON.stringify(log));
    } catch (e) {}
    return r;
  };
})();
"""


def record(section, name, ok, detail=""):
    RESULTS.append({"section": section, "name": name, "ok": bool(ok), "detail": str(detail)[:600]})
    mark = "PASS" if ok else "FAIL"
    print(f"  {mark}  [{section}] {name}" + (f": {detail}" if detail and not ok else ""))


# ----------------------------------------------------------------------------- builds and servers

def run_build(args, env=None):
    e = dict(os.environ, **(env or {}))
    out = subprocess.run([sys.executable, str(ROOT / "build.py")] + args, env=e, capture_output=True, text=True)
    if out.returncode:
        sys.exit("build failed:\n" + out.stdout + out.stderr)
    return out.stdout


def serve(directory, port):
    handler = functools.partial(QuietHandler, directory=str(directory))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def pages(base_url, base_path="/"):
    """Every built page: (pid, lang, url)."""
    site = build.Site(True, base_path, ROOT / "site")
    return [(pid, lang, base_url.rstrip("/") + site.url(pid, lang)) for lang in build.LANGS for pid in build.PAGE]


# ----------------------------------------------------------------------------- static HTML parsing

class Collect(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.ids, self.alts, self.switch, self.html_lang = [], set(), {}, None, None
        self.headings = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "html":
            self.html_lang = a.get("lang")
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.headings.append(int(tag[1]))
        for attr in ("href", "src", "action"):
            if a.get(attr) and tag in ("a", "link", "script", "img", "form", "iframe"):
                self.links.append((tag, attr, a[attr], a))
        if tag == "link" and a.get("rel") == "alternate" and a.get("hreflang"):
            self.alts[a["hreflang"]] = a["href"]
        if tag == "a" and "lang-switch" in (a.get("class") or ""):
            self.switch = a


def parse(path):
    c = Collect()
    c.feed(path.read_text(encoding="utf-8"))
    return c


def file_for(site_dir, base_path, url_path):
    rel = url_path[len(base_path):] if url_path.startswith(base_path) else None
    if rel is None:
        return None
    p = site_dir / rel
    if url_path.endswith("/"):
        p = p / "index.html"
    return p


def test_links(site_dir, base_url, base_path, label):
    """Crawl every page: internal hrefs 200, anchors exist, switch -> counterpart, sitemap = pages."""
    site = build.Site(True, base_path, site_dir)
    parsed = {}
    for f in site_dir.rglob("*.html"):
        parsed[f] = parse(f)
    status_cache, bad, bad_anchor, external_bad = {}, [], [], []
    for f, c in parsed.items():
        page_url = base_url + "/" + str(f.relative_to(site_dir)).replace("index.html", "")
        for tag, attr, val, attrs in c.links:
            u = urlparse(val)
            if u.scheme in ("mailto", "tel"):
                continue
            if u.scheme in ("http", "https") and u.netloc not in ("127.0.0.1", "localhost") and not val.startswith(base_url):
                if not u.netloc or " " in val:
                    external_bad.append(val)
                continue
            full = urljoin(page_url, val)
            pu = urlparse(full)
            key = pu.path
            if key not in status_cache:
                try:
                    with urllib.request.urlopen(f"{pu.scheme}://{pu.netloc}{pu.path}") as r:
                        status_cache[key] = r.status
                except Exception as e:  # noqa: BLE001
                    status_cache[key] = getattr(e, "code", 0)
            if status_cache[key] != 200:
                bad.append(f"{f.relative_to(site_dir)} -> {val} ({status_cache[key]})")
            if pu.fragment:
                same = pu.path == urlparse(page_url).path
                target = f if same else file_for(site_dir, base_path, pu.path)
                if target not in parsed or pu.fragment not in parsed[target].ids:
                    bad_anchor.append(f"{f.relative_to(site_dir)} -> {val}")
    record("links", f"{label}: every internal href returns 200 ({len(status_cache)} unique paths)", not bad, bad[:10])
    record("links", f"{label}: every #anchor target exists", not bad_anchor, bad_anchor[:10])
    record("links", f"{label}: external links are well-formed", not external_bad, external_bad[:10])

    switch_bad, alt_bad, lang_bad, base_bad = [], [], [], []
    for pid in build.PAGE:
        for lang in build.LANGS:
            f = site_dir / site.path(pid, lang) / "index.html"
            c = parsed.get(f)
            if c is None:
                switch_bad.append(f"missing {pid} {lang}")
                continue
            other = "pl" if lang == "en" else "en"
            sw = c.switch or {}
            if sw.get("href") != site.url(pid, other) or sw.get("hreflang") != other or sw.get("lang") != other:
                switch_bad.append(f"{pid} ({lang}): {sw.get('href')}")
            if set(c.alts) != {"en", "pl", "x-default"}:
                alt_bad.append(f"{pid} ({lang})")
            if c.html_lang != lang:
                lang_bad.append(f"{pid} ({lang}): html lang={c.html_lang}")
            for tag, attr, val, attrs in c.links:
                if val.startswith("/") and not val.startswith(base_path):
                    base_bad.append(f"{pid} ({lang}): {val}")
    record("links", f"{label}: every PL/EN switch points to the same page_id in the other language", not switch_bad, switch_bad[:10])
    record("links", f"{label}: hreflang en, pl and x-default on every page", not alt_bad, alt_bad[:10])
    record("links", f"{label}: <html lang> matches the page language", not lang_bad, lang_bad[:10])
    record("links", f"{label}: every root-relative URL starts with the base path {base_path}", not base_bad, base_bad[:10])

    sm = (site_dir / "sitemap.xml").read_text()
    locs = set(re.findall(r"<loc>(.*?)</loc>", sm))
    expected = {site.absolute(pid, lang) for pid, p in build.PAGE.items() if p["indexable"] for lang in build.LANGS}
    record("links", f"{label}: sitemap.xml lists exactly the indexable built pages ({len(expected)})",
           locs == expected, sorted(locs ^ expected)[:10])
    alts_in_sm = len(re.findall(r'hreflang="x-default"', sm))
    record("links", f"{label}: sitemap has hreflang alternates for every URL", alts_in_sm == len(expected))


# ----------------------------------------------------------------------------- content checks

def test_content(site_dir):
    lint = build.lint_copy()
    record("content", "banned-word / caps / !!! lint passes on en.yml and pl.yml", not lint, lint[:10])
    leftovers, lorem = [], []
    for f in site_dir.rglob("*.html"):
        s = f.read_text(encoding="utf-8")
        if re.search(r"\[\[|\{\?|\?\}", s):
            leftovers.append(str(f.relative_to(site_dir)))
        text = re.sub(r"<script.*?</script>|<!--.*?-->|<[^>]+>", " ", s, flags=re.S)
        if re.search(r"\blorem\b|\bTODO\b", text, re.I):
            lorem.append(str(f.relative_to(site_dir)))
    record("content", "every [[…]] token is resolved in the output", not leftovers, leftovers[:10])
    record("content", "no lorem / TODO text in the output", not lorem, lorem[:10])

    # CHECKLIST.md must match the placeholders found on the pages
    checklist = (ROOT / "CHECKLIST.md").read_text(encoding="utf-8")
    rows = {}
    for line in checklist.splitlines():
        m = re.match(r"\| `([a-z0-9_]+)` \| (FILL IN|CONFIRM) \|.*\| ([^|]*) \|$", line)
        if m:
            rows[m.group(1)] = m.group(3)
    site = build.Site(True, "/", site_dir)
    found, mismatch = {}, []
    for pid in build.PAGE:
        for lang in build.LANGS:
            html_ = (site_dir / site.path(pid, lang) / "index.html").read_text(encoding="utf-8")
            for key in set(re.findall(r'data-ph="([a-z0-9_]+)"', html_)):
                found.setdefault(key, set()).add(f"{pid} ({lang})")
    for key, where in found.items():
        if key not in rows:
            mismatch.append(f"{key} on pages but not in CHECKLIST.md")
            continue
        listed = set(x.strip() for x in rows[key].split(","))
        if rows[key].strip() == "every page, EN + PL":
            listed = {f"{p} ({l})" for p in build.PAGE for l in build.LANGS}
        missing = where - listed
        if missing:
            mismatch.append(f"{key}: CHECKLIST misses {sorted(missing)[:3]}")
    record("content", f"CHECKLIST.md matches the {len(found)} placeholder keys found on pages", not mismatch, mismatch[:10])
    in_cfg = set(build.CONFIG)
    record("content", "CHECKLIST.md lists every CONFIG item", set(rows) == in_cfg, sorted(in_cfg ^ set(rows))[:10])

    css = (site_dir / "assets" / "style.css").stat().st_size
    js = (site_dir / "assets" / "site.js").stat().st_size
    record("content", f"style.css under 40 KB ({css // 1024} KB)", css < 40 * 1024)
    record("content", f"site.js under 25 KB ({js // 1024} KB)", js < 25 * 1024)

    heading_bad = []
    for f in site_dir.rglob("index.html"):
        c = parse(f)
        hs = c.headings
        if hs.count(1) != 1:
            heading_bad.append(f"{f.relative_to(site_dir)}: {hs.count(1)} h1")
        for a, b in zip(hs, hs[1:]):
            if b > a + 1:
                heading_bad.append(f"{f.relative_to(site_dir)}: h{a} -> h{b}")
                break
    record("content", "one h1 per page, no skipped heading levels", not heading_bad, heading_bad[:10])


# ----------------------------------------------------------------------------- browser tests

def ctx(browser, w=1440, h=900, consent=True, js=True, log=False, **kw):
    c = browser.new_context(viewport={"width": w, "height": h}, reduced_motion="reduce", java_script_enabled=js,
                            locale="en-US", **kw)
    if consent:
        c.add_init_script(CONSENT_SET)
    if log:
        c.add_init_script(DL_LOG)
    return c


def screenshots(browser, url_pages, folder):
    n = 0
    for vw, vh, tag in ((390, 844, "mobile"), (1440, 900, "desktop")):
        c = ctx(browser, vw, vh)
        p = c.new_page()
        for pid, lang, url in url_pages:
            out = folder / lang / f"{pid}-{tag}.png"
            out.parent.mkdir(parents=True, exist_ok=True)
            p.goto(url)
            p.evaluate("document.fonts.ready")
            p.screenshot(path=str(out), full_page=True)
            n += 1
        c.close()
    return n


def test_axe(browser, url_pages):
    summary = {}
    for vw, vh, tag in ((1440, 900, "desktop"), (390, 844, "mobile")):
        c = ctx(browser, vw, vh)
        p = c.new_page()
        for pid, lang, url in url_pages:
            p.goto(url)
            p.add_script_tag(path=str(AXE))
            res = p.evaluate("""async () => {
              const r = await axe.run(document, {runOnly: {type: 'tag', values: ['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa','best-practice']}});
              return r.violations.map(v => ({id: v.id, impact: v.impact, n: v.nodes.length, target: v.nodes[0].target.join(' ')}));
            }""")
            for v in res:
                summary.setdefault((v["impact"], v["id"]), []).append(f"{pid}/{lang}/{tag} {v['target']}")
        c.close()
    serious = {k: v for k, v in summary.items() if k[0] in ("serious", "critical")}
    record("a11y", f"axe-core: zero serious or critical violations on {len(url_pages)} pages × 2 viewports",
           not serious, {f"{k[0]}:{k[1]}": v[:3] for k, v in serious.items()})
    minor = {f"{k[0]}:{k[1]}": len(v) for k, v in summary.items() if k[0] not in ("serious", "critical")}
    record("a11y", "axe-core: moderate/minor findings (informational)", True, minor or "none")
    return summary


FOCUS_JS = """() => {
  const el = document.activeElement; if (!el || el === document.body) return {ok: false, what: 'body'};
  const cs = getComputedStyle(el);
  const visible = (cs.outlineStyle !== 'none' && parseFloat(cs.outlineWidth) >= 2) || cs.boxShadow !== 'none';
  return {ok: visible, what: el.tagName + '.' + (el.className || '') + ' ' + (el.textContent || el.name || '').trim().slice(0, 30)};
}"""


def tab_until(p, js_pred, limit=80):
    bad = []
    for _ in range(limit):
        p.keyboard.press("Tab")
        f = p.evaluate(FOCUS_JS)
        if not f["ok"]:
            bad.append(f["what"])
        if p.evaluate(js_pred):
            return True, bad
    return False, bad


def test_keyboard(browser, base):
    c = ctx(browser, 1440, 900)
    p = c.new_page()
    p.goto(base + "/")
    p.keyboard.press("Tab")
    record("keyboard", "first Tab focuses the skip link", p.evaluate("document.activeElement.classList.contains('skip')"))
    p.keyboard.press("Enter")
    record("keyboard", "skip link moves focus to <main>", p.evaluate("document.activeElement.id === 'main'"))
    ok, bad = tab_until(p, "document.activeElement.dataset.door === 'lena'")
    record("keyboard", "home: Tab reaches the students door card", ok)
    p.keyboard.press("Enter")
    p.wait_for_url("**/students/")
    record("keyboard", "door card opens /students/ with Enter", p.url.endswith("/students/"))
    ok2, bad2 = tab_until(p, "document.activeElement.dataset.cta === 'send_dates'")
    p.keyboard.press("Enter")
    record("keyboard", "students: 'Send my dates' jumps to the inline form", ok2 and p.url.endswith("#brief"))
    ok3, bad3 = tab_until(p, "document.activeElement.classList.contains('btn-submit')")
    p.keyboard.press("Enter")
    p.wait_for_timeout(200)
    record("keyboard", "empty submit by keyboard moves focus to the error summary",
           ok3 and p.evaluate("document.activeElement.classList.contains('error-summary')"))
    # fix the form by keyboard: first summary link -> first field
    p.keyboard.press("Tab")
    p.keyboard.press("Enter")
    # Chromium splits <input type=date> into segments ordered by OS locale, so set the value directly,
    # then carry on by keyboard from the next field.
    p.fill("#brief [name=arrival]", "2027-08-28")
    p.focus("#brief [name=months]")
    p.keyboard.type("5")
    p.keyboard.press("Tab"); p.keyboard.type("1800")
    p.keyboard.press("Tab"); p.keyboard.type("SGH Warsaw School of Economics")
    p.keyboard.press("Tab"); p.keyboard.type("Test Person")
    p.keyboard.press("Tab"); p.keyboard.type("test@example.com")
    p.keyboard.press("Tab"); p.keyboard.press("Space")   # channel radio
    p.keyboard.press("Tab"); p.keyboard.press("Space")   # consent
    p.wait_for_timeout(3200)                             # minimum fill time
    ok4, bad4 = tab_until(p, "document.activeElement.classList.contains('btn-submit')", 10)
    p.keyboard.press("Enter")
    p.wait_for_timeout(300)
    status = p.evaluate("document.querySelector('#brief .form-status').innerText")
    record("keyboard", "valid keyboard submit without a backend shows the FILL IN notice", "FILL IN" in status, status)
    allbad = bad + bad2 + bad3 + bad4
    record("keyboard", "focus is visible on every element reached by Tab", not allbad, allbad[:5])
    c.close()

    # Focus not obscured by the sticky header or the sticky action bar (mobile)
    c = ctx(browser, 390, 844)
    p = c.new_page()
    hidden = []
    for path in ("/students/", "/pl/rodzice/", "/universities/"):
        p.goto(base + path)
        for _ in range(140):
            p.keyboard.press("Tab")
            r = p.evaluate("""() => {
              const el = document.activeElement; if (!el || el === document.body) return null;
              if (el.closest('.site-header, .action-bar, .consent') || el.classList.contains('skip')) return null;
              const b = el.getBoundingClientRect();
              const top = document.querySelector('.site-header').getBoundingClientRect().bottom;
              const bar = document.querySelector('.action-bar');
              const bottom = bar ? bar.getBoundingClientRect().top : innerHeight;
              return {hidden: b.bottom <= top || b.top >= bottom, what: el.tagName + ' ' + (el.textContent || el.name || '').trim().slice(0, 30)};
            }""")
            if r and r["hidden"]:
                hidden.append(f"{path}: {r['what']}")
    record("keyboard", "mobile: no focused element is hidden behind the sticky header or action bar", not hidden, hidden[:5])
    c.close()


def test_interactions(browser, base, wired):
    # mobile menu
    c = ctx(browser, 390, 844)
    p = c.new_page()
    p.goto(base + "/")
    p.click(".menu-toggle")
    opened = p.evaluate("document.querySelector('.menu-toggle').getAttribute('aria-expanded') === 'true'") and p.is_visible("#main-nav")
    p.keyboard.press("Escape")
    closed = p.evaluate("document.querySelector('.menu-toggle').getAttribute('aria-expanded') === 'false'") and not p.is_visible("#main-nav")
    back = p.evaluate("document.activeElement.classList.contains('menu-toggle')")
    record("interact", "mobile menu opens, closes with Esc and returns focus", opened and closed and back)
    p.click(".menu-toggle")
    p.click(".sub-toggle")
    record("interact", "partners disclosure opens inside the mobile menu", p.is_visible("#sub-partners a"))
    c.close()

    c = ctx(browser, 1440, 900)
    p = c.new_page()
    p.goto(base + "/")
    p.click(".sub-toggle")
    o = p.is_visible("#sub-partners")
    p.keyboard.press("Escape")
    record("interact", "desktop partners disclosure opens, closes with Esc, focus returns",
           o and not p.is_visible("#sub-partners") and p.evaluate("document.activeElement.classList.contains('sub-toggle')"))

    # FAQ
    p.goto(base + "/how-it-works/")
    p.click("details[data-q] summary")
    p.wait_for_timeout(150)
    dl = p.evaluate("window.dataLayer.filter(e => e.event === 'faq_open')")
    record("interact", "FAQ <details> opens and pushes faq_open",
           p.evaluate("document.querySelector('details[data-q]').open") and dl and "question_id" in dl[0])

    # Copy link
    c2 = ctx(browser, 1440, 900, permissions=["clipboard-read", "clipboard-write"])
    p2 = c2.new_page()
    p2.goto(base + "/students/")
    p2.click("[data-copy]")
    p2.wait_for_timeout(200)
    clip = p2.evaluate("navigator.clipboard.readText()")
    record("interact", "copy-link copies the page URL and pushes share_copy",
           clip.endswith("/students/") and p2.evaluate("window.dataLayer.some(e => e.event === 'share_copy')"), clip)
    c2.close()

    # Map facade
    p.route("https://www.google.com/**", lambda r: r.fulfill(status=200, body="<html></html>", content_type="text/html"))
    p.goto(base + "/contact/")
    before = p.evaluate("document.querySelectorAll('.map iframe').length")
    p.click("[data-map-load]")
    iframe = p.evaluate("(() => { const f = document.querySelector('.map iframe'); return f ? {title: f.title, src: f.src} : null })()")
    record("interact", "map facade loads nothing until clicked, then injects a titled Google Maps iframe",
           before == 0 and iframe and iframe["title"] and "google.com/maps" in iframe["src"], iframe)
    link = p.get_attribute("a[href*='maps/search']", "href")
    record("interact", "plain 'Open in Google Maps' link is present", bool(link) and "query=Warszawa" in link, link)

    # Empty submit
    p.goto(base + "/start/")
    p.click("#f-search .btn-submit")
    p.wait_for_timeout(150)
    ok = p.is_visible("#f-search .error-summary") and p.evaluate("document.activeElement.classList.contains('error-summary')")
    inline = p.evaluate("[...document.querySelectorAll('#f-search .field-error:not([hidden])')].length")
    described = p.evaluate("document.querySelector('#f-search-name').getAttribute('aria-describedby') || ''")
    fe = p.evaluate("window.dataLayer.filter(e => e.event === 'form_error')")
    record("interact", "empty submit: error summary shown and focused, inline errors linked by aria-describedby",
           ok and inline >= 5 and "f-search-name-error" in described, f"inline={inline} described={described}")
    record("interact", "form_error carries only form_id and field_count",
           fe and set(fe[0]) == {"event", "form_id", "field_count"}, fe[:1])

    # ?for=parent preselect, UTM capture
    p.goto(base + "/?utm_source=esn_group&utm_medium=whatsapp&utm_campaign=autumn_intake")
    p.goto(base + "/start/?for=parent")
    record("interact", "?for=parent preselects 'My child' on /start/",
           p.evaluate("document.querySelector('[name=who][value=parent]').checked"))
    utm = p.evaluate("['utm_source','utm_medium','utm_campaign'].map(k => document.querySelector('#f-search [name=' + k + ']').value)")
    record("interact", "UTMs from the landing page are carried into hidden form fields",
           utm == ["esn_group", "whatsapp", "autumn_intake"], utm)
    p.goto(base + "/professionals/")
    p.goto(base + "/start/")
    record("interact", "referring persona page preselects 'Who is searching' (professional)",
           p.evaluate("document.querySelector('[name=who][value=professional]').checked"))
    c.close()

    # Valid submit with a mocked endpoint (wired build)
    c = ctx(browser, 1440, 900, log=True)
    p = c.new_page()
    posted = []

    def handle(route):
        posted.append(route.request.post_data or "")
        route.fulfill(status=200, body='{"ok":true}', content_type="application/json",
                      headers={"Access-Control-Allow-Origin": "*"})
    p.route("https://forms.example.test/**", handle)
    p.goto(wired + "/start/")
    p.check("#f-search [name=who][value=student]")
    p.fill("#f-search-arrival", "2027-08-28")
    p.fill("#f-search-months", "5")
    p.fill("#f-search-budget", "1800")
    p.fill("#f-search-area", "SGH")
    p.fill("#f-search-name", "Test Person")
    p.fill("#f-search-contact", "test.person@example.com")
    p.check("#f-search-consent")
    p.wait_for_timeout(3200)
    p.click("#f-search .btn-submit")
    p.wait_for_url("**/thanks/?form=search", timeout=8000)
    log = p.evaluate("JSON.parse(sessionStorage.getItem('__dl') || '[]')")
    lead = [e for e in log if e.get("event") == "generate_lead"]
    leak = "Test Person" in json.dumps(log) or "example.com" in json.dumps(log)
    record("interact", "valid submit posts to the endpoint and redirects to /thanks/?form=search",
           posted and "Test Person" in posted[0] and p.url.endswith("/thanks/?form=search"))
    record("interact", "generate_lead pushed with form_id, persona, lang and no personal data",
           lead and set(lead[0]) == {"event", "form_id", "persona", "lang"} and lead[0]["persona"] == "lena" and not leak, lead)
    record("interact", "thanks page shows the message for the search brief",
           p.is_visible("[data-thanks-for=search]") and not p.is_visible("[data-thanks-for=default]"))
    hp_ok = all(k in posted[0] for k in ("form_id", "utm_source", "referrer", "fill_ms", "website"))
    record("interact", "submission includes hidden fields (form_id, utm_*, referrer) and the honeypot", hp_ok)
    c.close()

    # Consent: reject loads no Google tags, accept loads them
    for choice in ("reject", "accept"):
        c = ctx(browser, 1440, 900, consent=False)
        p = c.new_page()
        reqs = []
        p.route("https://www.googletagmanager.com/**", lambda r: (reqs.append(r.request.url), r.fulfill(status=200, body="")))
        p.route("https://www.google-analytics.com/**", lambda r: (reqs.append(r.request.url), r.fulfill(status=200, body="")))
        p.goto(wired + "/")
        shown = p.is_visible("#consent")
        before = len(reqs)
        p.click(f"[data-consent={choice}]")
        p.wait_for_timeout(600)
        stored = p.evaluate("JSON.parse(localStorage.getItem('doorstep_consent'))")
        if choice == "reject":
            record("interact", "consent banner shows on first visit; nothing loads before a choice", shown and before == 0)
            record("interact", "Reject: no GTM/GA requests, choice stored with a date",
                   not reqs and stored and stored["analytics"] is False and stored.get("date"), reqs)
            p.goto(wired + "/students/")
            p.wait_for_timeout(300)
            record("interact", "Reject persists across pages (banner hidden, still no requests)",
                   not p.is_visible("#consent") and not reqs)
            p.click("[data-consent-open]")
            record("interact", "footer 'Cookie settings' reopens the banner", p.is_visible("#consent"))
        else:
            record("interact", "Accept: GTM loads (verified by network interception)",
                   any("gtm.js?id=GTM-TEST123" in u for u in reqs), reqs)
        c.close()

    # Banner sits above the sticky bar on mobile
    c = ctx(browser, 390, 844, consent=False)
    p = c.new_page()
    p.goto(base + "/students/")
    geo = p.evaluate("""() => ({banner: document.querySelector('#consent').getBoundingClientRect().bottom,
                                bar: document.querySelector('.action-bar').getBoundingClientRect().top})""")
    record("interact", "consent banner does not cover the sticky action bar", geo["banner"] <= geo["bar"], geo)
    SHOTS.mkdir(parents=True, exist_ok=True)
    p.screenshot(path=str(SHOTS / "consent-banner-mobile.png"))
    c.close()

    # JavaScript off: pages still work
    c = ctx(browser, 390, 844, js=False)
    p = c.new_page()
    p.goto(base + "/students/")
    nav_ok = p.is_visible("#main-nav a[href$='/parents/']")
    js_only_hidden = not p.is_visible(".menu-toggle")
    form = p.evaluate("(() => { const f = document.querySelector('#brief'); return {action: f.getAttribute('action'), method: f.method, req: f.querySelectorAll('[required]').length} })()")
    p.goto(base + "/contact/")
    maplink = p.is_visible("a[href*='maps/search']")
    record("interact", "JS off: navigation visible, forms have action/method/required, map link works",
           nav_ok and js_only_hidden and form["req"] >= 6 and form["method"] == "post" and maplink, form)
    c.close()


def test_layout(browser, url_pages):
    over = []
    for w in (320, 390, 768, 1024, 1440):
        c = ctx(browser, w, 900)
        p = c.new_page()
        for pid, lang, url in url_pages:
            p.goto(url)
            sw = p.evaluate("document.documentElement.scrollWidth")
            if sw > w:
                over.append(f"{pid}/{lang}@{w}: {sw}")
        c.close()
    record("layout", "no horizontal overflow at 320, 390, 768, 1024 and 1440 px", not over, over[:10])

    c = ctx(browser, 390, 844)
    p = c.new_page()
    small = []
    for pid, lang, url in url_pages:
        p.goto(url)
        res = p.evaluate("""() => [...document.querySelectorAll(
            '.btn, .door, .lang-switch, .menu-toggle, .text-link, summary, .nav-list a, .form input:not([type=hidden]):not([type=checkbox]):not([type=radio]), .form select, .check, .action-bar a')]
            .filter(e => e.offsetParent !== null && !e.closest('.hp'))
            .map(e => [e.className || e.tagName, Math.round(e.getBoundingClientRect().height)])
            .filter(x => x[1] < 44)""")
        small += [f"{pid}/{lang}: {r}" for r in res]
    record("layout", "tap targets ≥ 44px on mobile (buttons, links styled as targets, form controls)", not small, small[:10])

    # Polish diacritics in all three fonts
    p.goto(url_pages[0][2].split("/")[0] + "//" + url_pages[0][2].split("/")[2] + "/pl/")
    p.evaluate("document.fonts.ready")
    p.wait_for_timeout(300)
    loaded = p.evaluate("performance.getEntriesByType('resource').map(r => r.name).filter(n => n.includes('latin-ext'))")
    fams = ["bricolage-grotesque-latin-ext", "instrument-sans-latin-ext", "ibm-plex-mono-latin-ext"]
    record("layout", "Polish diacritics render in all three fonts (latin-ext files load on /pl/)",
           all(any(f in n for n in loaded) for f in fams), loaded)
    checks = p.evaluate("""() => ['Bricolage Grotesque', 'Instrument Sans', 'IBM Plex Mono']
        .map(f => document.fonts.check('16px "' + f + '"', 'ąćęłńóśźż ĄĆĘŁŃÓŚŹŻ'))""")
    record("layout", "document.fonts.check passes for ąćęłńóśźż in every family", all(checks), checks)
    c.close()


def test_gsap(browser, base):
    """With motion allowed, GSAP loads and below-the-fold content ends visible."""
    c = browser.new_context(viewport={"width": 1440, "height": 900})
    c.add_init_script(CONSENT_SET)
    p = c.new_page()
    p.goto(base + "/")
    p.wait_for_timeout(800)
    has = p.evaluate("!!window.gsap")
    p.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    p.wait_for_timeout(1200)
    hidden = p.evaluate("[...document.querySelectorAll('[data-reveal]')].filter(e => getComputedStyle(e).opacity !== '1').length")
    record("interact", "GSAP loads when motion is allowed; revealed content ends fully visible", has and hidden == 0, hidden)
    c.close()
    c = ctx(browser, 1440, 900)
    p = c.new_page()
    p.goto(base + "/")
    p.wait_for_timeout(500)
    record("interact", "prefers-reduced-motion: GSAP is not loaded", not p.evaluate("!!window.gsap"))
    c.close()


# ----------------------------------------------------------------------------- main

def write_results(started):
    fails = [r for r in RESULTS if not r["ok"]]
    lines = ["# Test results", "", f"Run: {time.strftime('%Y-%m-%d %H:%M')} · {len(RESULTS)} checks · "
             f"**{len(RESULTS) - len(fails)} passed, {len(fails)} failed** · {int(time.time() - started)} s", ""]
    section = None
    for r in RESULTS:
        if r["section"] != section:
            section = r["section"]
            lines += ["", f"## {section}", "", "| Result | Check | Detail |", "|---|---|---|"]
        detail = r["detail"].replace("|", "/").replace("\n", " ") if (not r["ok"] or r["section"] == "a11y") else ""
        lines.append(f"| {'PASS' if r['ok'] else 'FAIL'} | {r['name']} | {detail} |")
    (TESTS / "results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return fails


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="skip screenshots")
    args = ap.parse_args()
    started = time.time()

    print("Building variants…")
    run_build([])
    tb = ROOT / ".test-build"
    run_build(["--out", str(tb / "hidden"), "--no-highlights"])
    run_build(["--out", str(tb / "wired")], {"DOORSTEP_GTM_ID": "GTM-TEST123",
                                               "DOORSTEP_FORM_ENDPOINT": "https://forms.example.test/f/doorstep"})
    run_build(["--out", str(tb / "bp" / "doorstep"), "--base-path", "/doorstep/"])

    servers = [serve(ROOT / "site", 8811), serve(tb / "hidden", 8812), serve(tb / "wired", 8813), serve(tb / "bp", 8814)]
    base, hidden, wired, bp = "http://127.0.0.1:8811", "http://127.0.0.1:8812", "http://127.0.0.1:8813", "http://127.0.0.1:8814"
    main_pages = pages(base)

    print("Static checks…")
    test_content(ROOT / "site")
    test_links(ROOT / "site", base, "/", "site/")
    test_links(tb / "bp" / "doorstep", bp + "/doorstep", "/doorstep/", "base path /doorstep/")
    test_content_hidden(tb / "hidden")

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        if not args.quick:
            print("Screenshots…")
            n = screenshots(browser, main_pages, SHOTS)
            n += screenshots(browser, pages(hidden), SHOTS / "no-highlights")
            record("screens", f"{n} full-page screenshots at 390×844 and 1440×900 (with and without highlights)", True)
        print("Accessibility…")
        test_axe(browser, main_pages)
        print("Keyboard…")
        test_keyboard(browser, base)
        print("Interactions…")
        test_interactions(browser, base, wired)
        test_gsap(browser, base)
        print("Layout…")
        test_layout(browser, main_pages)
        browser.close()
    for s in servers:
        s.shutdown()
    fails = write_results(started)
    print(f"\n{len(RESULTS) - len(fails)} passed, {len(fails)} failed. Details: tests/results.md")
    sys.exit(1 if fails else 0)


def test_content_hidden(site_dir):
    marks = [str(f.relative_to(site_dir)) for f in site_dir.rglob("*.html")
             if re.search(r'class="ph |FILL IN|UZUPEŁNIJ|do potwierdzenia|>confirm<', f.read_text(encoding="utf-8"))]
    record("content", "SHOW_PLACEHOLDER_HIGHLIGHTS=False: no highlight markup or labels in the output", not marks, marks[:10])
    dangling = []
    for f in site_dir.rglob("index.html"):
        text = re.sub(r"<script.*?</script>|<[^>]+>", " ", f.read_text(encoding="utf-8"), flags=re.S)
        raw = f.read_text(encoding="utf-8")
        for m in re.finditer(r"[^>]{0,40}(:\s*</(li|dd|span|strong)>|:\s*</p>(?!\s*<(ul|figure))|<(dd|li|p)>\s*</|, policy\s*\.|\(\s*\))", raw):
            dangling.append(f"{f.relative_to(site_dir)}: …{m.group(0).strip()[-60:]}")
    record("content", "hidden mode: sentences around empty FILL IN items still read correctly", not dangling, dangling[:10])


if __name__ == "__main__":
    main()
