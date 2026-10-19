/* Doorstep · site.js
   Progressive enhancement only: every page works without it, except the map
   facade and the consent banner. Never sends form contents to analytics. */
(function () {
  'use strict';
  var d = document, w = window, html = d.documentElement, body = d.body;
  var ds = body.dataset, page = ds.page || '', lang = ds.lang || 'en', persona = ds.persona || '';
  var MIN_FILL_MS = 3000;
  var WHO_PERSONA = { student: 'lena', parent: 'katrin', professional: 'marco' };
  var PAGE_WHO = { students: 'student', parents: 'parent', professionals: 'professional' };

  function $(sel, root) { return (root || d).querySelector(sel); }
  function $$(sel, root) { return Array.prototype.slice.call((root || d).querySelectorAll(sel)); }
  function store(kind) {
    return {
      get: function (k) { try { return w[kind].getItem(k); } catch (e) { return null; } },
      set: function (k, v) { try { w[kind].setItem(k, v); } catch (e) { /* private mode */ } }
    };
  }
  var local = store('localStorage'), session = store('sessionStorage');

  /* ---------- Measurement: Consent Mode v2, everything denied before any tag ---------- */
  w.dataLayer = w.dataLayer || [];
  function gtag() { w.dataLayer.push(arguments); }
  w.gtag = w.gtag || gtag;
  gtag('consent', 'default', {
    ad_storage: 'denied', ad_user_data: 'denied', ad_personalization: 'denied',
    analytics_storage: 'denied', functionality_storage: 'denied',
    personalization_storage: 'denied', security_storage: 'granted', wait_for_update: 500
  });
  var tagsLoaded = false, ga4Direct = false;

  function track(event, params) {
    var o = { event: event };
    for (var k in params) { if (params.hasOwnProperty(k)) o[k] = params[k]; }
    w.dataLayer.push(o);
    if (ga4Direct) w.gtag('event', event, params);
  }

  function inject(src) {
    var s = d.createElement('script');
    s.async = true; s.src = src; d.head.appendChild(s);
  }

  function loadTags() {
    if (tagsLoaded) return;
    if (ds.gtm) {
      w.dataLayer.push({ 'gtm.start': Date.now(), event: 'gtm.js' });
      inject('https://www.googletagmanager.com/gtm.js?id=' + encodeURIComponent(ds.gtm));
    } else if (ds.ga4) {
      inject('https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(ds.ga4));
      w.gtag('js', new Date());
      w.gtag('config', ds.ga4);
      ga4Direct = true;
    } else {
      return;
    }
    tagsLoaded = true;
  }

  /* ---------- Consent banner ---------- */
  var CONSENT_KEY = 'doorstep_consent';
  var banner = $('#consent');

  function readConsent() {
    try {
      var c = JSON.parse(local.get(CONSENT_KEY));
      return c && c.v === 1 ? c : null;
    } catch (e) { return null; }
  }

  function applyConsent(c) {
    var ad = c.marketing ? 'granted' : 'denied';
    w.gtag('consent', 'update', {
      analytics_storage: c.analytics ? 'granted' : 'denied',
      ad_storage: ad, ad_user_data: ad, ad_personalization: ad, functionality_storage: ad
    });
    if (c.analytics || c.marketing) loadTags();
    if (c.marketing) loadMap(false);
  }

  function showBanner(focus) {
    if (!banner) return;
    banner.hidden = false;
    var c = readConsent();
    $('#consent-analytics').checked = !!(c && c.analytics);
    $('#consent-marketing').checked = !!(c && c.marketing);
    html.style.setProperty('--consent-h', banner.offsetHeight + 'px');
    if (focus) $('[data-consent=reject]', banner).focus();
  }

  function hideBanner() {
    if (!banner) return;
    banner.hidden = true;
    html.style.removeProperty('--consent-h');
  }

  function saveConsent(analytics, marketing) {
    var c = { v: 1, analytics: !!analytics, marketing: !!marketing, date: new Date().toISOString() };
    local.set(CONSENT_KEY, JSON.stringify(c));
    applyConsent(c);
    hideBanner();
  }

  if (banner) {
    banner.addEventListener('click', function (e) {
      var b = e.target.closest('[data-consent]');
      if (!b) return;
      var act = b.getAttribute('data-consent');
      if (act === 'accept') saveConsent(true, true);
      else if (act === 'reject') saveConsent(false, false);
      else if (act === 'save') saveConsent($('#consent-analytics').checked, $('#consent-marketing').checked);
      else if (act === 'settings') {
        var panel = $('#consent-settings'), open = panel.hidden;
        panel.hidden = !open;
        b.setAttribute('aria-expanded', String(open));
        html.style.setProperty('--consent-h', banner.offsetHeight + 'px');
      }
    });
  }
  $$('[data-consent-open]').forEach(function (b) {
    b.addEventListener('click', function () { showBanner(true); });
  });
  var stored = readConsent();
  if (stored) applyConsent(stored); else showBanner(false);

  /* ---------- Mobile menu and partners disclosure ---------- */
  var menuBtn = $('.menu-toggle'), nav = $('#main-nav');
  var subBtn = $('.sub-toggle'), subLi = subBtn && subBtn.closest('.has-sub');

  function setMenu(open, refocus) {
    if (!menuBtn) return;
    menuBtn.setAttribute('aria-expanded', String(open));
    nav.classList.toggle('open', open);
    html.classList.toggle('menu-open', open);
    if (!open && refocus) menuBtn.focus();
  }
  function setSub(open, refocus) {
    if (!subBtn) return;
    subBtn.setAttribute('aria-expanded', String(open));
    subLi.classList.toggle('open', open);
    if (!open && refocus) subBtn.focus();
  }
  if (menuBtn) menuBtn.addEventListener('click', function () {
    setMenu(menuBtn.getAttribute('aria-expanded') !== 'true');
  });
  if (subBtn) subBtn.addEventListener('click', function () {
    setSub(subBtn.getAttribute('aria-expanded') !== 'true');
  });
  d.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') return;
    if (subBtn && subBtn.getAttribute('aria-expanded') === 'true') setSub(false, true);
    else if (menuBtn && menuBtn.getAttribute('aria-expanded') === 'true') setMenu(false, true);
  });
  d.addEventListener('click', function (e) {
    if (subLi && !subLi.contains(e.target)) setSub(false);
  });
  if (subLi) subLi.addEventListener('focusout', function (e) {
    if (w.innerWidth >= 1024 && e.relatedTarget && !subLi.contains(e.relatedTarget)) setSub(false);
  });
  w.addEventListener('resize', function () { if (w.innerWidth >= 1024) setMenu(false); });

  /* ---------- Focus not obscured (WCAG 2.4.11): keep focus clear of the sticky header and bar.
     Browsers ignore scroll-padding when moving focus, so nudge the page ourselves. ---------- */
  d.addEventListener('focusin', function (e) {
    var el = e.target;
    if (!el.getBoundingClientRect || el.closest('.site-header, .action-bar, .consent, .main-nav.open')) return;
    var r = el.getBoundingClientRect(), header = $('.site-header'), bar = $('.action-bar');
    var top = header ? header.getBoundingClientRect().bottom : 0;
    var bottom = w.innerHeight;
    if (bar && bar.offsetHeight) bottom = Math.min(bottom, bar.getBoundingClientRect().top);
    if (banner && !banner.hidden) bottom = Math.min(bottom, banner.getBoundingClientRect().top);
    if (r.bottom > bottom - 8) w.scrollBy(0, r.bottom - bottom + 24);
    else if (r.top < top + 8) w.scrollBy(0, r.top - top - 24);
  });

  /* ---------- Click measurement (no personal data) ---------- */
  d.addEventListener('click', function (e) {
    var a = e.target.closest('a, button');
    if (!a) return;
    var href = a.getAttribute('href') || '', base = { page: page, persona: persona };
    if (a.hasAttribute('data-door')) {
      track('door_click', { persona: a.getAttribute('data-door'), position: Number(a.getAttribute('data-position')) });
    }
    if (a.hasAttribute('data-cta')) {
      track('cta_click', { cta_id: a.getAttribute('data-cta'), page: page, persona: persona, location: a.getAttribute('data-loc') || '' });
    }
    if (/^https:\/\/wa\.me\//.test(href)) track('whatsapp_click', base);
    else if (href.indexOf('mailto:') === 0) track('email_click', base);
    else if (href.indexOf('tel:') === 0) track('phone_click', base);
    if (a.hasAttribute('data-booking')) track('booking_click', { page: page });
    if (a.classList.contains('lang-switch')) track('lang_switch', { from: lang, to: a.getAttribute('data-to'), page: page });
  });

  $$('details[data-q]').forEach(function (det) {
    det.addEventListener('toggle', function () {
      if (det.open) track('faq_open', { question_id: det.getAttribute('data-q') });
    });
  });

  var guide = $('[data-guide]');
  if (guide) {
    var guideDone = false;
    w.addEventListener('scroll', function () {
      if (guideDone) return;
      var seen = (w.scrollY + w.innerHeight) / d.documentElement.scrollHeight;
      if (seen >= 0.75) { guideDone = true; track('guide_read', { guide_id: guide.getAttribute('data-guide') }); }
    }, { passive: true });
  }

  /* ---------- Copy link (students page) ---------- */
  $$('[data-copy]').forEach(function (b) {
    b.addEventListener('click', function () {
      var url = location.origin + location.pathname, out = $('[data-copy-status]');
      function done() { if (out) out.textContent = b.getAttribute('data-done'); track('share_copy', { page: page }); }
      if (navigator.clipboard && w.isSecureContext) {
        navigator.clipboard.writeText(url).then(done, fallback);
      } else { fallback(); }
      function fallback() {
        var t = d.createElement('textarea');
        t.value = url; t.setAttribute('readonly', ''); t.style.position = 'fixed'; t.style.opacity = '0';
        body.appendChild(t); t.select();
        try { d.execCommand('copy'); } catch (e) { /* ignore */ }
        body.removeChild(t); done();
      }
    });
  });

  /* ---------- Map facade (contact page) ---------- */
  function loadMap(byClick) {
    var box = $('.map[data-map-src]');
    if (!box || $('iframe', box)) return;
    var f = d.createElement('iframe');
    f.title = box.getAttribute('data-map-title');
    f.src = box.getAttribute('data-map-src');
    f.loading = 'lazy';
    f.referrerPolicy = 'no-referrer-when-downgrade';
    box.innerHTML = '';
    box.appendChild(f);
    track('map_load', { page: page });
    if (byClick) f.focus();
  }
  $$('[data-map-load]').forEach(function (b) { b.addEventListener('click', function () { loadMap(true); }); });

  /* ---------- UTM and referrer: captured on landing, kept for the session ---------- */
  var q = new URLSearchParams(location.search);
  ['utm_source', 'utm_medium', 'utm_campaign'].forEach(function (k) {
    if (q.get(k)) session.set(k, q.get(k).slice(0, 100));
  });
  if (session.get('referrer') === null) {
    var ref = '';
    try { ref = d.referrer ? new URL(d.referrer).host : ''; } catch (e) { ref = ''; }
    session.set('referrer', ref && ref !== location.host ? ref : '(direct)');
  }
  if (PAGE_WHO[page]) session.set('last_who', PAGE_WHO[page]);

  /* ---------- Forms ---------- */
  var BRIEF_KEYS = ['arrival', 'months', 'budget', 'area', 'place', 'furnished'];

  function fieldInput(f) {
    return f.tagName === 'FIELDSET' ? null : $('input[name=consent], input:not([type=hidden]), select, textarea', f);
  }

  function isEmail(v) { return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v); }
  function isPhone(v) { return /^\+?[\d\s().-]{7,20}$/.test(v) && v.replace(/\D/g, '').length >= 7; }

  function formatOk(input, v) {
    var kind = input.getAttribute('data-msg-format') ? input.name : '';
    if (input.type === 'email') return isEmail(v);
    if (input.type === 'date') return !input.validity.badInput && !isNaN(Date.parse(v));
    if (input.type === 'number') {
      var n = Number(v), min = input.min !== '' ? Number(input.min) : -Infinity, max = input.max !== '' ? Number(input.max) : Infinity;
      return !isNaN(n) && n >= min && n <= max;
    }
    if (kind === 'contact') return isEmail(v) || isPhone(v);
    if (input.type === 'tel') return isPhone(v);
    return true;
  }

  function validate(form) {
    var errors = [];
    $$('[data-field]', form).forEach(function (f) {
      if (f.tagName === 'FIELDSET') {
        if (f.hasAttribute('data-required') && !$('input:checked', f)) {
          errors.push({ field: f, target: $('input', f), msg: f.getAttribute('data-msg-required') });
        }
        return;
      }
      var input = fieldInput(f);
      if (!input) return;
      var v = input.type === 'checkbox' ? (input.checked ? 'yes' : '') : input.value.trim();
      if (input.required && !v) {
        errors.push({ field: f, target: input, msg: input.getAttribute('data-msg-required') });
      } else if (v && input.getAttribute('data-msg-format') && !formatOk(input, v)) {
        errors.push({ field: f, target: input, msg: input.getAttribute('data-msg-format') });
      }
    });
    return errors;
  }

  function errorId(f) {
    var input = f.tagName === 'FIELDSET' ? f : fieldInput(f);
    return input.id + '-error';
  }

  function clearErrors(form) {
    $$('.has-error', form).forEach(function (f) {
      f.classList.remove('has-error');
      var p = d.getElementById(errorId(f));
      if (p) { p.hidden = true; p.textContent = ''; }
      var input = f.tagName === 'FIELDSET' ? f : fieldInput(f);
      input.removeAttribute('aria-invalid');
      var desc = (input.getAttribute('aria-describedby') || '').split(' ').filter(function (id) { return id && id !== errorId(f); });
      if (desc.length) input.setAttribute('aria-describedby', desc.join(' ')); else input.removeAttribute('aria-describedby');
    });
    var s = $('.error-summary', form);
    s.hidden = true;
  }

  function showErrors(form, errors) {
    var summary = $('.error-summary', form), list = $('ul', summary);
    list.innerHTML = '';
    errors.forEach(function (er) {
      var f = er.field, id = errorId(f), p = d.getElementById(id);
      f.classList.add('has-error');
      if (p) { p.textContent = er.msg; p.hidden = false; }
      var input = f.tagName === 'FIELDSET' ? f : er.target;
      input.setAttribute('aria-invalid', 'true');
      var desc = (input.getAttribute('aria-describedby') || '').split(' ').filter(Boolean);
      if (desc.indexOf(id) < 0) desc.push(id);
      input.setAttribute('aria-describedby', desc.join(' '));
      var li = d.createElement('li'), a = d.createElement('a');
      a.href = '#' + er.target.id; a.textContent = er.msg;
      a.addEventListener('click', function (e) { e.preventDefault(); er.target.focus(); });
      li.appendChild(a); list.appendChild(li);
    });
    summary.hidden = false;
    summary.focus();
  }

  function setStatus(form, html_, cls) {
    var s = $('.form-status', form);
    s.className = 'form-status' + (cls ? ' ' + cls : '');
    s.innerHTML = html_;
  }

  function personaFor(form) {
    var who = $('[name=who]:checked', form) || $('input[type=hidden][name=who]', form);
    return form.getAttribute('data-persona') || (who && WHO_PERSONA[who.value]) || '';
  }

  function saveBrief(form) {
    var brief = {};
    BRIEF_KEYS.forEach(function (k) {
      var el = $('[name=' + k + ']:checked', form) || $('[name=' + k + ']:not([type=radio])', form);
      if (el && el.value) brief[k] = el.value;
    });
    session.set('brief', JSON.stringify(brief));
  }

  function prefillBrief(form) {
    var brief = {};
    try { brief = JSON.parse(session.get('brief')) || {}; } catch (e) { brief = {}; }
    Object.keys(brief).forEach(function (k) {
      var radio = $('[name=' + k + '][value="' + brief[k] + '"]', form);
      var field = $('[name=' + k + ']:not([type=radio])', form);
      if (radio) radio.checked = true; else if (field && !field.value) field.value = brief[k];
    });
    var who = q.get('for') || session.get('last_who');
    var r = who && $('[name=who][value="' + who + '"]', form);
    if (r) r.checked = true;
  }

  function preselectTimezone(form) {
    var sel = $('select[name=timezone]', form);
    if (!sel) return;
    var tz = '';
    try { tz = Intl.DateTimeFormat().resolvedOptions().timeZone; } catch (e) { return; }
    var match = $$('option', sel).filter(function (o) { return o.value === tz; })[0];
    if (match) sel.value = tz;
  }

  $$('form[data-form]').forEach(function (form) {
    var formId = form.getAttribute('data-form'), started = false, t0 = Date.now();
    form.noValidate = true;
    ['utm_source', 'utm_medium', 'utm_campaign', 'referrer'].forEach(function (k) {
      var el = form.elements[k];
      if (el) el.value = session.get(k) || '';
    });
    if (formId === 'search') {
      prefillBrief(form);
      form.addEventListener('change', function () { saveBrief(form); });
    }
    if (formId === 'call') preselectTimezone(form);

    form.addEventListener('focusin', function () {
      if (!started) { started = true; track('form_start', { form_id: formId }); }
    });

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      clearErrors(form);
      setStatus(form, '');
      var errors = validate(form);
      if (errors.length) {
        showErrors(form, errors);
        track('form_error', { form_id: formId, field_count: errors.length });
        return;
      }
      if (form.elements.website && form.elements.website.value) return; // honeypot
      var elapsed = Date.now() - t0;
      form.elements.fill_ms.value = String(elapsed);
      var status = $('.form-status', form);
      if (elapsed < MIN_FILL_MS) { setStatus(form, status.getAttribute('data-failed')); return; }
      var endpoint = form.getAttribute('data-endpoint');
      if (!endpoint) {
        var label = body.getAttribute('data-fill-label'), msg = status.getAttribute('data-no-backend');
        setStatus(form, label ? '<mark class="ph ph-fill" data-ph="form_endpoint">' + label + ': ' + msg + '</mark>' : msg);
        return;
      }
      var btn = $('.btn-submit', form);
      btn.disabled = true;
      setStatus(form, status.getAttribute('data-sending'));
      fetch(endpoint, { method: 'POST', body: new FormData(form), headers: { Accept: 'application/json' } })
        .then(function (r) {
          if (!r.ok) throw new Error(String(r.status));
          if (formId === 'search') saveBrief(form);
          track('generate_lead', { form_id: formId, persona: personaFor(form), lang: lang });
          var next = ds.thanks + '?form=' + encodeURIComponent(formId);
          setTimeout(function () { location.href = next; }, 200);
        })
        .catch(function () {
          btn.disabled = false;
          setStatus(form, status.getAttribute('data-failed'));
        });
    });
  });

  /* ---------- Thank-you page: message for ?form= ---------- */
  var which = q.get('form');
  if (which && $('[data-thanks-for="' + which + '"]')) {
    $$('[data-thanks-for]').forEach(function (el) { el.hidden = el.getAttribute('data-thanks-for') !== which; });
  }

  /* ---------- Minimal GSAP: below-the-fold reveals and a stamp press. Skipped for reduced motion. ---------- */
  var reduce = w.matchMedia && w.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (ds.gsap && !reduce) {
    var s = d.createElement('script');
    s.src = ds.gsap;
    s.onload = function () {
      var g = w.gsap;
      if (!g) return;
      var stamp = $('.hero-side [data-stamp]');
      if (stamp) g.from(stamp, { scale: 1.25, rotation: -6, duration: 0.45, delay: 0.2, ease: 'back.out(2.5)', clearProps: 'transform' });
      var later = $$('[data-reveal]').filter(function (el) { return el.getBoundingClientRect().top > w.innerHeight; });
      g.set(later, { opacity: 0, y: 20 });
      // Reveal anything that has reached the viewport or been scrolled past (anchor jumps, End key)
      var ticking = false;
      function reveal() {
        ticking = false;
        later = later.filter(function (el) {
          if (el.getBoundingClientRect().top > w.innerHeight * 0.92) return true;
          g.to(el, { opacity: 1, y: 0, duration: 0.5, ease: 'power2.out', clearProps: 'opacity,transform' });
          return false;
        });
        if (!later.length) w.removeEventListener('scroll', onScroll);
      }
      function onScroll() { if (!ticking) { ticking = true; w.requestAnimationFrame(reveal); } }
      w.addEventListener('scroll', onScroll, { passive: true });
      d.addEventListener('focusin', reveal);
      w.addEventListener('beforeprint', function () { g.set(later, { clearProps: 'opacity,transform' }); });
    };
    d.head.appendChild(s);
  }
})();
