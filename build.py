#!/usr/bin/env python3
"""Doorstep static site generator.

    python build.py            build site/
    python build.py --zip      build, then write doorstep-website.zip
    python build.py --strict   fail if any FILL IN item is empty or the copy lint warns

Edit the CONFIG block below. Copy lives in src/content/{en,pl}.yml,
markup in src/templates/. Nothing else needs touching for normal edits.
"""

# =============================================================================
# CONFIG: every missing or uncertain fact lives here, and only here.
#
#   "key": ""                       a FILL IN item: a fact B01 does not state.
#                                   Empty renders a yellow "FILL IN" mark.
#   "key": {"value": ..., "source": ..., "confirmed": False}
#                                   a CONFIRM item: taken from B01 but marked
#                                   [H]/[Confirm], or inferred. Renders the value
#                                   with a blue "confirm" tag until confirmed=True.
#                                   "value" is a string, or {"en": ..., "pl": ...}.
#
# Any FILL IN item can also be set from the environment, e.g.
#   DOORSTEP_FORM_ENDPOINT=https://... python build.py
# which is how the GitHub Actions workflow injects values kept in repo settings.
# =============================================================================

PRIMARY_LANG = "en"                  # "en": EN at /, PL at /pl/.  "pl": PL at /, EN at /en/.
SHOW_PLACEHOLDER_HIGHLIGHTS = True   # False: hide all FILL IN / confirm styling and labels
BASE_PATH = "/"                      # "/" for a custom domain or user.github.io;
                                     # "/repo-name/" for a GitHub project page
USE_GSAP = True                      # minimal entrance animations (self-hosted GSAP, skipped
                                     # for prefers-reduced-motion and when JS is off)

CONFIG = {
    # --- Website -------------------------------------------------------------
    "site_url": "",                  # e.g. https://doorstep.example (no trailing slash)
    "og_image": "",                  # absolute URL or /assets/img/og.jpg, 1200x630
    "search_console_verification": "",

    # --- Legal entity (B01 §2: registration + OC insurance before the first paid case)
    "legal_name": "",
    "legal_form": "",                # e.g. sp. z o.o. or jednoosobowa działalność gospodarcza
    "nip": "",
    "regon": "",
    "krs_or_ceidg": "",
    "registered_address": "",        # filled: shown on About/Contact and centres the map
    "oc_insurer": "",
    "oc_policy": "",

    # --- Contact ---------------------------------------------------------------
    "email": "",
    "phone": "",                     # E.164, e.g. +48...
    "whatsapp": "",                  # E.164 digits for wa.me, e.g. 48123456789
    "instagram": "",                 # full URL
    "linkedin": "",                  # full URL
    "booking_url": "",               # Calendly/Cal.com link; filled: replaces the call form
    "contact_hours": "",
    "reply_time": "",
    "payment_methods": "",

    # --- Team (B01 names the five founders; nothing else about them) ----------
    "team_bora_role": "", "team_bora_languages": "", "team_bora_photo": "", "team_bora_bio": "",
    "team_arsen_role": "", "team_arsen_languages": "", "team_arsen_photo": "", "team_arsen_bio": "",
    "team_adon_role": "", "team_adon_languages": "", "team_adon_photo": "", "team_adon_bio": "",
    "team_nikola_role": "", "team_nikola_languages": "", "team_nikola_photo": "", "team_nikola_bio": "",
    "team_nina_role": "", "team_nina_languages": "", "team_nina_photo": "", "team_nina_bio": "",
    "team_contact_students": "",     # name + channel of the person who answers students
    "team_contact_parents": "",
    "team_contact_professionals": "",
    "team_contact_partners": "",

    # --- Service details --------------------------------------------------------
    "viewing_photo": "",             # path to a real viewing photo (JPEG; .webp/.avif siblings used if present)
    "viewing_checklist": "",
    "districts_by_campus": "",
    "aftercare_contact": "",
    "capacity_per_intake": "",       # optional: only if the team wants to show it

    # --- Partners ---------------------------------------------------------------
    "university_annual_fee": "",
    "data_processing_summary": "",
    "liability_terms": "",
    "references": "",
    "proposal_pdf": "",              # URL of the one-page proposal PDF

    # --- Content still to write --------------------------------------------------
    "first_week_content": "",
    "privacy_policy_body": "",
    "terms_body": "",
    "cookie_policy_body": "",

    # --- Forms and measurement ------------------------------------------------
    "form_endpoint": "",             # https URL of the form service; all five forms post here
    "gtm_id": "",                    # GTM-XXXXXXX, or use ga4_id instead
    "ga4_id": "",                    # G-XXXXXXXXXX

    # --- CONFIRM: fees and money (B01 §2) -------------------------------------
    "fee_student": {"value": {"en": "690 PLN", "pl": "690 zł"}, "source": "B01 §2 [H]", "confirmed": False},
    "fee_professional": {"value": {"en": "1,290 PLN", "pl": "1290 zł"}, "source": "B01 §2 [H]", "confirmed": False},
    "fee_university_student": {"value": {"en": "290 PLN", "pl": "290 zł"}, "source": "B01 §2 [H]", "confirmed": False},
    "fees_gross_vat": {"value": {"en": "Prices include 23% VAT.", "pl": "Ceny zawierają 23% VAT."},
                       "source": "B01 §2 [Confirm]", "confirmed": False},
    "pay_on_signing": {"value": {"en": "Paid when you sign", "pl": "Płacisz przy podpisaniu umowy"},
                       "source": "B01 §2 [H]", "confirmed": False},
    "no_home_no_fee": {"value": {"en": "No home, no fee.", "pl": "Nie ma mieszkania, nie ma opłaty."},
                       "source": "B01 §2 [H]", "confirmed": False},
    "referral_fee": {"value": {"en": "50% of one month's rent per signed tenancy",
                               "pl": "50% miesięcznego czynszu za każdą podpisaną umowę najmu"},
                     "source": "B01 §2 [H]", "confirmed": False},

    # --- CONFIRM: team and process ----------------------------------------------
    "languages": {"value": {"en": "Polish, Ukrainian, Macedonian and German; English as our working language",
                            "pl": "polski, ukraiński, macedoński i niemiecki; na co dzień pracujemy po angielsku"},
                  "source": "B01 §2 [Confirm]", "confirmed": False},
    "shortlist_accepts_dates": {"value": {"en": "Every option on your shortlist accepts your dates.",
                                          "pl": "Każda opcja z listy akceptuje Twoje daty."},
                                "source": "inferred from B01 §4 Lena (five-month stays)", "confirmed": False},
    "travel_time_per_option": {"value": {"en": "and give the travel time to campus with every option",
                                         "pl": "i przy każdej opcji podajemy czas dojazdu na uczelnię"},
                               "source": "inferred from B01 §4 Lena pain points", "confirmed": False},
    "shortlist_days": {"value": "", "source": "inferred; B01 says only 'within days'", "confirmed": False},
    "written_cost_summary": {"value": {"en": "You get a written cost summary before you decide.",
                                       "pl": "Przed decyzją dostajesz pisemne podsumowanie kosztów."},
                             "source": "B01 §4 Katrin closing criteria; process inferred", "confirmed": False},
    "first_month_checkin": {"value": {"en": "In the first month we check in with you and your child.",
                                      "pl": "W pierwszym miesiącu odzywamy się do Ciebie i do Twojego dziecka."},
                            "source": "B01 §5 Katrin stage 4 opportunity", "confirmed": False},
    "setup_list": {"value": {"en": "a one-page setup list for internet, utilities and registration",
                             "pl": "jednostronicową listę: internet, media i zameldowanie"},
                   "source": "B01 §5 Marco stage 4 opportunity", "confirmed": False},
    "pilot_terms": {"value": {"en": "A one-semester pilot with a clear exit.",
                              "pl": "Pilotaż na jeden semestr z jasną możliwością zakończenia."},
                    "source": "B01 §5 Agnieszka stage 3 opportunity", "confirmed": False},
    "intake_report": {"value": {"en": "After each intake: students helped, issues raised, how each was resolved.",
                                "pl": "Po każdym naborze: ilu studentom pomogliśmy, jakie były problemy i jak je rozwiązaliśmy."},
                      "source": "B01 §5 Agnieszka stage 4 opportunity", "confirmed": False},
    "intake_summary_landlords": {"value": {"en": "After each intake you receive a summary of placements and their status.",
                                           "pl": "Po każdym naborze otrzymuje Pan zestawienie umów i ich statusu."},
                                 "source": "B01 §5 Piotr stage 5 opportunity", "confirmed": False},
    "rules_checklist": {"value": {"en": "Before signing, we show every tenant your house rules.",
                                  "pl": "Przed podpisaniem pokazujemy każdemu najemcy regulamin."},
                        "source": "B01 §7 example + §5 Piotr stage 3 opportunity", "confirmed": False},
    "foreigner_friendly_landlords": {"value": {"en": "We only shortlist landlords who accept foreign tenants.",
                                               "pl": "Na listę trafiają tylko wynajmujący, którzy przyjmują najemców z zagranicy."},
                                     "source": "inferred from B01 §4 Marco pain points", "confirmed": False},
    "payer_differs": {"value": {"en": "Yes. You can pay for your child's search; the contract can still be in your child's name.",
                                "pl": "Tak. Możesz zapłacić za wyszukiwanie dla dziecka, a umowa może być na jego nazwisko."},
                      "source": "inferred from B01 §4 Katrin (she pays, the child lives there)", "confirmed": False},
    "call_length": {"value": {"en": "20-minute", "pl": "20-minutową"}, "source": "inferred", "confirmed": False},
    "fake_listing_patterns": {"value": {"en": "Team review of this list", "pl": "Zespół sprawdza tę listę"},
                              "source": "general knowledge, needs team review", "confirmed": False},
    "glossary_reviewed": {"value": {"en": "Team review of these definitions", "pl": "Zespół sprawdza te definicje"},
                          "source": "general knowledge beyond B01 §3/§7, needs team review", "confirmed": False},
}

# FILL IN items the site can go live without.
OPTIONAL_FILL = {"capacity_per_intake", "search_console_verification", "gtm_id", "ga4_id",
                 "booking_url", "viewing_photo", "cookie_policy_body", "instagram", "linkedin"}

# =============================================================================
# End of CONFIG. Below is the generator.
# =============================================================================

import argparse
import base64
import datetime as _dt
import hashlib
import html
import json
import os
import re
import shutil
import sys
import zipfile
from pathlib import Path
from urllib.parse import quote, quote_plus

try:
    import yaml
    from jinja2 import Environment, FileSystemLoader, StrictUndefined
    from markupsafe import Markup
except ImportError:  # pragma: no cover
    sys.exit("Missing dependencies. Run: pip install -r requirements.txt")

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
LANGS = ("en", "pl")
PH_COLOURS = {"fill": "#FFE94D", "confirm": "#DCE7FF"}

# page id, template, EN slug, PL slug, persona (B01), bottom bar, indexable
PAGES = [
    ("home", "home.html", "", "", "", "people", True),
    ("students", "students.html", "students", "studenci", "lena", "people", True),
    ("parents", "parents.html", "parents", "rodzice", "katrin", "parents", True),
    ("professionals", "professionals.html", "professionals", "praca", "marco", "people", True),
    ("universities", "universities.html", "universities", "uczelnie", "agnieszka", "uni", True),
    ("landlords", "landlords.html", "landlords", "wynajmujacy", "piotr", "landlord", True),
    ("how", "how.html", "how-it-works", "jak-to-dziala", "", "people", True),
    ("about", "about.html", "about", "o-nas", "", "people", True),
    ("start", "start.html", "start", "start", "", "", True),
    ("contact", "contact.html", "contact", "kontakt", "", "", True),
    ("guides", "guides.html", "guides", "poradniki", "", "people", True),
    ("guide_fake", "guide_fake.html", "guides/fake-listings", "poradniki/falszywe-ogloszenia", "", "people", True),
    ("guide_words", "guide_words.html", "guides/rental-words", "poradniki/slowniczek-najmu", "", "people", True),
    ("guide_first", "guide_first.html", "guides/first-week", "poradniki/pierwszy-tydzien", "", "people", True),
    ("thanks", "thanks.html", "thanks", "dziekujemy", "", "", False),
    ("privacy", "legal.html", "privacy", "prywatnosc", "", "", True),
    ("terms", "legal.html", "terms", "regulamin", "", "", True),
]
PAGE = {p[0]: dict(id=p[0], template=p[1], slug={"en": p[2], "pl": p[3]}, persona=p[4],
                   bar=p[5], indexable=p[6]) for p in PAGES}

BANNED = {
    "en": ["best", "perfect", "dream", "unbeatable", "ultimate", "seamless", "hassle-free", "premium",
           "world-class", "innovative", "solutions", "ai-powered", "end-to-end", "comprehensive",
           "leads", "users", "clients", "customers"],
    "pl": ["najlepsz\\w*", "idealn\\w*", "wymarzon\\w*", "bezkonkurencyjn\\w*", "kompleksowe rozwiązania",
           "innowacyjn\\w*", "marzeń", "klient\\w*", "użytkowni\\w*"],
}
CAPS_ALLOWED = {"RODO", "GDPR", "REGON", "CEIDG", "WCAG", "HTML", "JSON", "FILL", "UZUPEŁNIJ", "NIP", "KRS",
                "PLN", "VAT", "ESN", "OLX", "ID", "UTC", "GMT", "CET", "EET", "WET", "IBB", "PAS", "JLL",
                "CEE", "EUR", "USD", "PDF", "IBAN"}

TOKEN = re.compile(r"\[\[(fill|confirm|url|pl):([^\]]+)\]\]")
OPTIONAL = re.compile(r"\{\?(.+?)\?\}", re.S)


class Optional(StrictUndefined):
    """Missing keys are falsy in {% if %}, but printing one still fails the build."""
    __bool__ = lambda self: False


class Site:
    """Holds settings for one build and renders text tokens."""

    def __init__(self, highlights, base_path, out):
        self.highlights = highlights
        self.base = "/" + base_path.strip("/") + "/" if base_path.strip("/") else "/"
        self.out = out
        self.cfg = {}
        for k, v in CONFIG.items():
            if isinstance(v, dict):
                self.cfg[k] = v
            else:
                # a non-empty environment variable wins (used by the GitHub Actions workflow)
                self.cfg[k] = (os.environ.get("DOORSTEP_" + k.upper(), "").strip() or v).strip()
        self.usage = {}          # key -> set of (page_id, lang)
        self.page = None
        self.lang = None
        self.content = {}

    # --- config access -------------------------------------------------------
    def kind(self, key):
        if key not in self.cfg:
            raise KeyError(f"Unknown CONFIG key '{key}' (page {self.page}, {self.lang})")
        return "confirm" if isinstance(self.cfg[key], dict) else "fill"

    def note(self, key):
        self.usage.setdefault(key, set()).add((self.page, self.lang))

    def raw(self, key, lang=None):
        """Plain value of a CONFIG item ('' when empty). Records usage."""
        self.note(key)
        v = self.cfg[key]
        if isinstance(v, dict):
            v = v["value"]
            if isinstance(v, dict):
                v = v[lang or self.lang]
        return v or ""

    def label(self, key):
        labels = self.content[self.lang]["common"]["fill_labels"]
        return labels.get(key) or key.replace("_", " ")

    # --- token rendering -------------------------------------------------------
    def token(self, kind, arg, plain):
        """Return (html, missing). missing=True when the value is an empty fill."""
        if kind == "url":
            pid, _, anchor = arg.partition("#")
            return self.url(pid) + ("#" + anchor if anchor else ""), False
        if kind == "pl":
            return f'<span lang="pl">{arg}</span>' if self.lang != "pl" else arg, False
        key = arg.strip()
        actual = self.kind(key)
        if actual != kind:
            raise ValueError(f"[[{kind}:{key}]] but CONFIG says it is a {actual} item")
        value = self.raw(key)
        show = self.highlights and not plain
        ui = self.content[self.lang]["common"]["ph"]
        if kind == "fill":
            if value:
                return value, False
            if show:
                return (f'<mark class="ph ph-fill" data-ph="{key}">{ui["fill"]}: {self.label(key)}</mark>', True)
            return "", True
        confirmed = self.cfg[key].get("confirmed")
        if not value:  # confirm item without a value yet (e.g. shortlist_days)
            if show:
                return (f'<span class="ph ph-confirm" data-ph="{key}">{ui["unset"]}: {self.label(key)} '
                        f'<small>{ui["confirm"]}</small></span>', True)
            return "", True
        if show and not confirmed:
            return (f'<span class="ph ph-confirm" data-ph="{key}">{value} <small>{ui["confirm"]}</small></span>',
                    False)
        return value, False

    def text(self, s, plain=False):
        """Render a copy string. Returns '' if it depends on an empty fill and highlights are off."""
        if s is None:
            return ""
        s = str(s)

        def sub(chunk):
            missing = False

            def rep(m):
                nonlocal missing
                out, miss = self.token(m.group(1), m.group(2), plain)
                missing = missing or miss
                return out
            return TOKEN.sub(rep, chunk), missing

        def opt(m):
            out, miss = sub(m.group(1))
            if miss and (plain or not self.highlights):
                return ""
            return out
        s = OPTIONAL.sub(opt, s)
        out, miss = sub(s)
        if miss and (plain or not self.highlights):
            return ""
        return out.strip()

    def plain(self, s):
        """Text for meta tags and JSON-LD: no markup, never placeholders."""
        out = self.text(s, plain=True)
        return html.unescape(re.sub(r"<[^>]+>", "", out)).strip()

    # --- URLs -------------------------------------------------------------------
    def prefix(self, lang):
        return "" if lang == PRIMARY_LANG else lang + "/"

    def path(self, pid, lang=None):
        lang = lang or self.lang
        slug = PAGE[pid]["slug"][lang]
        return self.prefix(lang) + (slug + "/" if slug else "")

    def url(self, pid, lang=None):
        if pid not in PAGE:
            raise KeyError(f"[[url:{pid}]] is not a page (page {self.page}, {self.lang})")
        return self.base + self.path(pid, lang)

    def absolute(self, pid, lang=None):
        site = self.cfg["site_url"].rstrip("/")
        return (site + self.url(pid, lang)) if site else self.url(pid, lang)

    def asset(self, rel):
        return self.base + "assets/" + rel


# =============================================================================
# Content loading and checks
# =============================================================================

def load_content():
    data = {}
    for lang in LANGS:
        with open(SRC / "content" / f"{lang}.yml", encoding="utf-8") as fh:
            data[lang] = yaml.safe_load(fh)
    problems = compare_structure(data["en"], data["pl"], "")
    if problems:
        sys.exit("en.yml and pl.yml differ in structure:\n  " + "\n  ".join(problems[:30]))
    return data


def compare_structure(a, b, where):
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a:
                out.append(f"{where}.{k} only in pl.yml")
            elif k not in b:
                out.append(f"{where}.{k} only in en.yml")
            else:
                out += compare_structure(a[k], b[k], f"{where}.{k}")
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append(f"{where}: {len(a)} items in en.yml, {len(b)} in pl.yml")
        for i, (x, y) in enumerate(zip(a, b)):
            out += compare_structure(x, y, f"{where}[{i}]")
    elif type(a) is not type(b) and not (a is None or b is None):
        out.append(f"{where}: different types")
    return out


def lint_copy():
    """Copy rules from B01 §7. Returns a list of warnings."""
    warnings = []
    for lang in LANGS:
        path = SRC / "content" / f"{lang}.yml"
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if line.lstrip().startswith("#"):
                continue
            # strip tokens, tag names and URLs before checking words
            text = TOKEN.sub(" ", line)
            text = re.sub(r"<[^>]+>|https?://\S+|^\s*[\w-]+:", " ", text)
            for word in BANNED[lang] + (BANNED["en"] if lang == "pl" else []):
                if re.search(rf"(?<![\w-]){word}(?![\w-])", text, re.I):
                    warnings.append(f"{path.name}:{n}: banned word '{word}'")
            if "!!!" in text:
                warnings.append(f"{path.name}:{n}: '!!!'")
            for caps in re.findall(r"\b[A-ZĄĆĘŁŃÓŚŹŻ]{4,}\b", text):
                if caps not in CAPS_ALLOWED:
                    warnings.append(f"{path.name}:{n}: all-caps word '{caps}'")
            if re.search(r"\blorem\b|\bTODO\b", text, re.I):
                warnings.append(f"{path.name}:{n}: lorem/TODO text")
    return warnings


# =============================================================================
# Rendering
# =============================================================================

def make_env(site):
    env = Environment(loader=FileSystemLoader(SRC / "templates"), autoescape=True,
                      undefined=Optional, trim_blocks=True, lstrip_blocks=True)

    def t(s):
        return Markup(site.text(s))

    def cfg(key):
        return site.raw(key)

    env.globals.update(
        t=t, plain=site.plain, cfg=cfg, url=site.url, asset=site.asset, root=lambda rel: site.base + rel,
        filled=lambda key: bool(site.raw(key)),
        highlights=site.highlights,
        fill=lambda key: Markup(site.text(f"[[fill:{key}]]")),
        confirm=lambda key: Markup(site.text(f"[[confirm:{key}]]")),
        quote_plus=quote_plus, quote=quote,
    )
    env.filters["tojson_ld"] = lambda obj: Markup(json.dumps(obj, ensure_ascii=False, indent=1)
                                                  .replace("</", "<\\/"))
    return env


def wa_link(site, text):
    num = re.sub(r"\D", "", site.raw("whatsapp"))
    if not num:
        return ""
    return f"https://wa.me/{num}?text={quote(text)}"


def org_jsonld(site, lang):
    """Organisation data: filled fields only, never placeholders."""
    c = site.content[lang]["common"]
    org = {"@context": "https://schema.org", "@type": "ProfessionalService", "name": "Doorstep",
           "description": site.plain(c["org_description"]),
           "areaServed": {"@type": "City", "name": "Warsaw" if lang == "en" else "Warszawa"},
           "foundingDate": "2026",
           "founder": [{"@type": "Person", "name": n} for n in c["founders"]]}
    if site.cfg["site_url"]:
        org["url"] = site.absolute("home", lang)
    for key, prop in (("legal_name", "legalName"), ("email", "email"), ("phone", "telephone"),
                      ("nip", "taxID")):
        if site.raw(key):
            org[prop] = site.raw(key)
    if site.raw("registered_address"):
        org["address"] = site.raw("registered_address")
    same = [site.raw(k) for k in ("instagram", "linkedin") if site.raw(k)]
    if same:
        org["sameAs"] = same
    return org


def faq_jsonld(site, items):
    qa = []
    for item in items:
        a = site.plain(item["a"])
        if a:
            qa.append({"@type": "Question", "name": site.plain(item["q"]),
                       "acceptedAnswer": {"@type": "Answer", "text": a}})
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": qa} if qa else None


def crumbs_jsonld(site, pid, lang):
    c = site.content[lang]
    items = [("home", c["common"]["nav"]["home"]), ("guides", c["guides"]["meta"]["crumb"]),
             (pid, c[pid]["meta"]["crumb"])]
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": name,
                                 "item": site.absolute(p, lang)} for i, (p, name) in enumerate(items)]}


def render_pages(site, env, version, inline_hash_src):
    built = []
    other = {"en": "pl", "pl": "en"}
    for lang in LANGS:
        for pid, page in PAGE.items():
            site.page, site.lang = pid, lang
            c = site.content[lang]
            pc = c[pid] if pid in c else c["legal"][pid]
            title = site.plain(pc["meta"]["title"])
            desc = site.plain(pc["meta"]["description"])
            jsonld = []
            if pid in ("home", "about", "contact"):
                jsonld.append(org_jsonld(site, lang))
            if "faq" in pc:
                f = faq_jsonld(site, pc["faq"]["items"])
                if f:
                    jsonld.append(f)
            if pid.startswith("guide_"):
                jsonld.append(crumbs_jsonld(site, pid, lang))
            ctx = dict(
                page=page, pid=pid, lang=lang, other_lang=other[lang], c=pc, common=c["common"],
                L=c, other_common=site.content[other[lang]]["common"],
                meta=dict(title=title, description=desc),
                canonical=site.absolute(pid, lang),
                alternates=[dict(hreflang=l, href=site.absolute(pid, l)) for l in LANGS] +
                           [dict(hreflang="x-default", href=site.absolute(pid, PRIMARY_LANG))],
                switch_url=site.url(pid, other[lang]),
                noindex=not site.cfg["site_url"] or not page["indexable"],
                jsonld=jsonld, version=version, use_gsap=USE_GSAP,
                og_image=absolute_asset(site, site.raw("og_image")),
                wa=lambda text: wa_link(site, text),
                map_query=site.raw("registered_address") or "Warszawa",
                inline_js=inline_hash_src, persona=page["persona"],
            )
            out_html = env.get_template(page["template"]).render(**ctx)
            check_page(out_html, pid, lang, title, desc)
            target = site.out / site.path(pid, lang) / "index.html"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(out_html, encoding="utf-8")
            built.append((pid, lang))
    # bilingual 404
    site.page, site.lang = "404", PRIMARY_LANG
    c = site.content
    out_html = env.get_template("404.html").render(
        L=c, lang=PRIMARY_LANG, version=version, use_gsap=USE_GSAP, inline_js=inline_hash_src,
        common=c[PRIMARY_LANG]["common"], page=dict(id="404", bar="", persona=""), pid="404")
    (site.out / "404.html").write_text(out_html, encoding="utf-8")
    return built


def absolute_asset(site, value):
    if not value:
        return ""
    if value.startswith("http"):
        return value
    return site.cfg["site_url"].rstrip("/") + site.base + value.lstrip("/")


def check_page(out_html, pid, lang, title, desc):
    left = re.findall(r"\[\[[^\]]*\]\]|\{\?|\?\}", out_html)
    if left:
        sys.exit(f"Unresolved tokens on {pid} ({lang}): {left[:5]}")
    if out_html.count("<h1") != 1:
        sys.exit(f"{pid} ({lang}) must have exactly one <h1>, has {out_html.count('<h1')}")
    if len(title) > 60:
        WARN.append(f"title over 60 chars on {pid} ({lang}): {len(title)}")
    if len(desc) > 155:
        WARN.append(f"description over 155 chars on {pid} ({lang}): {len(desc)}")


WARN = []


# =============================================================================
# Static files, sitemap, checklist, zip
# =============================================================================

def copy_static(site):
    shutil.copytree(SRC / "static", site.out, dirs_exist_ok=True)
    if not USE_GSAP:
        shutil.rmtree(site.out / "assets" / "vendor", ignore_errors=True)
    (site.out / ".nojekyll").write_text("")
    manifest = {"name": "Doorstep", "short_name": "Doorstep", "start_url": site.base, "scope": site.base,
                "display": "browser", "background_color": "#F7F4EE", "theme_color": "#1E4D3E",
                "icons": [{"src": site.base + "apple-touch-icon.png", "sizes": "180x180", "type": "image/png"},
                          {"src": site.base + "favicon.svg", "sizes": "any", "type": "image/svg+xml"}]}
    (site.out / "site.webmanifest").write_text(json.dumps(manifest, indent=2))


def asset_version():
    h = hashlib.sha1()
    for name in ("style.css", "site.js"):
        h.update((SRC / "static" / "assets" / name).read_bytes())
    return h.hexdigest()[:8]


def write_sitemap(site):
    today = _dt.date.today().isoformat()
    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    if not site.cfg["site_url"]:
        lines.append("<!-- FILL IN site_url in build.py: sitemap URLs must be absolute before going live -->")
    lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
                 'xmlns:xhtml="http://www.w3.org/1999/xhtml">')
    for pid, page in PAGE.items():
        if not page["indexable"]:
            continue
        for lang in LANGS:
            lines.append("  <url>")
            lines.append(f"    <loc>{site.absolute(pid, lang)}</loc>")
            for alt in LANGS:
                lines.append(f'    <xhtml:link rel="alternate" hreflang="{alt}" href="{site.absolute(pid, alt)}"/>')
            lines.append(f'    <xhtml:link rel="alternate" hreflang="x-default" '
                         f'href="{site.absolute(pid, PRIMARY_LANG)}"/>')
            lines.append(f"    <lastmod>{today}</lastmod>")
            lines.append("  </url>")
    lines.append("</urlset>")
    (site.out / "sitemap.xml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    sm = (site.cfg["site_url"].rstrip("/") + site.base + "sitemap.xml") if site.cfg["site_url"] else \
        site.base + "sitemap.xml"
    rules = "Disallow: /\n" if not site.cfg["site_url"] else "Allow: /\n"
    (site.out / "robots.txt").write_text(f"User-agent: *\n{rules}\nSitemap: {sm}\n")


def empty_fills(site):
    return [k for k, v in site.cfg.items() if not isinstance(v, dict) and not v]


def write_checklist(site, path):
    def where(key):
        uses = sorted(site.usage.get(key, set()), key=lambda x: (list(PAGE).index(x[0]) if x[0] in PAGE else 99, x[1]))
        if not uses:
            return "not used on a page (config only)"
        if {(p, l) for p in PAGE for l in LANGS} <= set(uses):
            return "every page, EN + PL"
        return ", ".join(f"{p} ({l})" for p, l in uses)

    lines = ["# Doorstep: what to FILL IN and CONFIRM", "",
             "Generated by `python build.py`. Do not edit by hand: change `CONFIG` in `build.py`.", "",
             f"- FILL IN items still empty: **{len(empty_fills(site))}** of "
             f"{sum(1 for v in site.cfg.values() if not isinstance(v, dict))}",
             f"- CONFIRM items not yet confirmed: **{sum(1 for v in site.cfg.values() if isinstance(v, dict) and not v['confirmed'])}**"
             f" of {sum(1 for v in site.cfg.values() if isinstance(v, dict))}",
             f"- Placeholder highlights: **{'on' if SHOW_PLACEHOLDER_HIGHLIGHTS else 'off'}**", "",
             "## Fill in", "",
             "Facts B01 does not state. Empty items show a yellow, dashed **FILL IN** mark.", "",
             "| Key | Type | Current value | Source | Required to go live | Appears on |",
             "|---|---|---|---|---|---|"]
    for k, v in site.cfg.items():
        if isinstance(v, dict):
            continue
        val = v.replace("|", "\\|") if v else "_(empty)_"
        lines.append(f"| `{k}` | FILL IN | {val} | not in B01 | "
                     f"{'optional' if k in OPTIONAL_FILL else 'yes'} | {where(k)} |")
    lines += ["", "## Confirm", "",
              "Values from B01 marked [H] or [Confirm], or inferred. They show with a blue, dotted "
              "**confirm** tag until `confirmed` is set to `True`.", "",
              "| Key | Type | Current value (EN / PL) | Source | Confirmed | Appears on |",
              "|---|---|---|---|---|---|"]
    for k, v in site.cfg.items():
        if not isinstance(v, dict):
            continue
        val = v["value"]
        val = f"{val['en']} / {val['pl']}" if isinstance(val, dict) else (val or "_(empty: team to set)_")
        lines.append(f"| `{k}` | CONFIRM | {val.replace('|', '/')} | {v['source']} | "
                     f"{'yes' if v['confirmed'] else 'no'} | {where(k)} |")
    lines += ["", "## Before going live", "",
              "- [ ] Connect the form backend (`form_endpoint`) and test one real submission per form "
              "(search brief, book a call, proposal request, partnership enquiry, contact).",
              "- [ ] Replace placeholders with real viewing and team photos, with consent from anyone pictured.",
              "- [ ] Have the privacy policy, terms and cookie policy written by someone qualified "
              "(RODO/GDPR: controller, purposes, retention, processors including the form service, Google "
              "and WhatsApp/Meta).",
              "- [ ] Configure the consent banner categories and GA4/GTM (`gtm_id` or `ga4_id`), and mark "
              "`generate_lead`, `whatsapp_click` and `booking_click` as key events in GA4.",
              "- [ ] Complete business registration and OC insurance before the first paid case (B01 §2), "
              "and put the numbers on the site (`nip`, `regon`, `krs_or_ceidg`, `oc_insurer`, `oc_policy`).",
              "- [ ] Confirm fees as gross prices with 23% VAT (`fees_gross_vat`, `fee_*`).",
              "- [ ] Set `site_url`, which removes `noindex`, then submit the sitemap in Search Console.",
              "- [ ] Set `SHOW_PLACEHOLDER_HIGHLIGHTS = False` and run `python build.py --strict`.", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


ZIP_INCLUDE = ["site", "src", "build.py", "requirements.txt", "tests", "CHECKLIST.md", "README.md",
               ".github", ".gitignore"]
ZIP_SKIP = {"__pycache__", ".pytest_cache", "node_modules", ".DS_Store"}


def make_zip(path):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for item in ZIP_INCLUDE:
            p = ROOT / item
            if p.is_file():
                z.write(p, item)
            elif p.is_dir():
                for f in sorted(p.rglob("*")):
                    if f.is_file() and not (set(f.relative_to(ROOT).parts) & ZIP_SKIP):
                        z.write(f, str(f.relative_to(ROOT)))
    print(f"Wrote {path.name} ({path.stat().st_size // 1024} KB)")


# =============================================================================
# Main
# =============================================================================

INLINE_JS = "document.documentElement.className=document.documentElement.className.replace('no-js','js')"


def build(out=None, highlights=None, base_path=None, quiet=False, checklist=True):
    highlights = SHOW_PLACEHOLDER_HIGHLIGHTS if highlights is None else highlights
    env_hide = os.environ.get("DOORSTEP_HIDE_PLACEHOLDERS")
    if env_hide:
        highlights = env_hide.lower() not in ("1", "true", "yes")
    base_path = base_path or os.environ.get("DOORSTEP_BASE_PATH") or BASE_PATH
    out = Path(out) if out else ROOT / "site"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    site = Site(highlights, base_path, out)
    site.content = load_content()
    env = make_env(site)
    copy_static(site)
    version = asset_version()
    built = render_pages(site, env, version, INLINE_JS)
    write_sitemap(site)
    if checklist:
        write_checklist(site, ROOT / "CHECKLIST.md")
    if not quiet:
        print(f"Built {len(built) + 1} pages ({len(PAGE)} x {len(LANGS)} languages + 404) "
              f"into {out.relative_to(ROOT) if out.is_relative_to(ROOT) else out}, base path {site.base}")
    return site


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--zip", action="store_true", help="also write doorstep-website.zip")
    ap.add_argument("--strict", action="store_true", help="fail on empty FILL IN items or copy-lint warnings")
    ap.add_argument("--out", help="output folder (default: site/)")
    ap.add_argument("--base-path", help="override BASE_PATH, e.g. /doorstep/")
    ap.add_argument("--no-highlights", action="store_true", help="build as if SHOW_PLACEHOLDER_HIGHLIGHTS=False")
    args = ap.parse_args()

    lint = lint_copy()
    site = build(out=args.out, highlights=False if args.no_highlights else None, base_path=args.base_path,
                 checklist=not args.out)

    for w in lint:
        print("LINT  ", w)
    for w in WARN:
        print("WARN  ", w)
    empty = empty_fills(site)
    required = [k for k in empty if k not in OPTIONAL_FILL]
    if empty:
        print(f"FILL  {len(empty)} FILL IN items still empty ({len(required)} required to go live): "
              + ", ".join(empty))
    if not site.cfg["site_url"]:
        print("WARN   site_url is empty: every page is noindex and robots.txt disallows crawling.")
    if not (site.cfg["gtm_id"] or site.cfg["ga4_id"]):
        print("WARN   neither gtm_id nor ga4_id is set: no analytics will load.")
    unconfirmed = [k for k, v in site.cfg.items() if isinstance(v, dict) and not v["confirmed"]]
    if unconfirmed:
        print(f"CONFIRM {len(unconfirmed)} items not yet confirmed (see CHECKLIST.md)")

    if args.strict:
        fails = []
        if required:
            fails.append(f"{len(required)} required FILL IN items are empty")
        if lint:
            fails.append(f"{len(lint)} copy-lint warnings")
        if site.highlights:
            print("WARN   --strict with SHOW_PLACEHOLDER_HIGHLIGHTS=True")
        if fails:
            sys.exit("STRICT: " + "; ".join(fails))
    if args.zip:
        make_zip(ROOT / "doorstep-website.zip")


if __name__ == "__main__":
    main()
