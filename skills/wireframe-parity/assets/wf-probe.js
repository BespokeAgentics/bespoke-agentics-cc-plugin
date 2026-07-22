/* ══════════════════════════════════════════════════════════════════════════
   wf-probe.js — standalone, dependency-free measurement kit for parity review.

   Injected via browser automation (claude-in-chrome `javascript_tool` /
   evaluate) into BOTH the served wireframe AND the running implemented app, so
   identical code measures both sides and the diff is apples-to-apples. Sets
   `window.__wfProbe`; returns plain JSON from every method.

   The geometry/contrast/markup/focusables/behaviour methods are byte-faithful
   to the interactive-wireframe scaffold's `__wf` kit (assets/wireframe-
   scaffold.html) so a re-measured wireframe matches its spec's frozen
   Verification numbers exactly. Two parity-specific additions are marked
   PARITY: `texts()` (rendered-label/enum fidelity) and `token()` (design-token
   comparison). `state()` reads `window.WF?.S` so it is harmless off-wireframe.

   env() returns `path` (pathname) only, never location.href — the automation
   bridge refuses a payload containing a URL/query string, which would block the
   whole result.
   ══════════════════════════════════════════════════════════════════════════ */
window.__wfProbe = (() => {
  const r2 = n => Math.round(n * 100) / 100;
  const px = el => { const b = el.getBoundingClientRect();
    return { top: r2(b.top), bottom: r2(b.bottom), left: r2(b.left), right: r2(b.right), w: r2(b.width), h: r2(b.height) }; };
  const parseRGB = s => { const m = (s || '').match(/-?[\d.]+/g); return m ? m.slice(0, 4).map(Number) : null; };
  const lum = ([r, g, b]) => { const f = c => { c /= 255; return c <= .04045 ? c / 12.92 : Math.pow((c + .055) / 1.055, 2.4); };
    return .2126 * f(r) + .7152 * f(g) + .0722 * f(b); };
  const over = (fg, bg) => { const a = fg[3] ?? 1; return [0, 1, 2].map(i => fg[i] * a + bg[i] * (1 - a)); };
  const effBg = el => {
    let node = el, acc = null;
    while (node && node.nodeType === 1) {
      const c = parseRGB(getComputedStyle(node).backgroundColor);
      if (c && (c[3] ?? 1) > 0) acc = acc ? over(acc, c) : c;
      if (acc && (acc[3] ?? 1) >= 1) return acc.slice(0, 3);
      node = node.parentElement;
    }
    return acc ? over(acc, [255, 255, 255]) : [255, 255, 255];
  };
  const hex = c => '#' + c.map(x => Math.round(x).toString(16).padStart(2, '0')).join('');

  const P = {
    version: '1.0.0',

    env() {
      return {
        visibilityState: document.visibilityState,
        documentFocused: document.hasFocus(),
        trustworthyForBehaviour: document.visibilityState === 'visible',
        viewport: { w: innerWidth, h: innerHeight, dpr: devicePixelRatio },
        scrollY: Math.round(scrollY),
        docHeight: document.documentElement.scrollHeight,
        reducedMotion: matchMedia('(prefers-reduced-motion: reduce)').matches,
        path: location.pathname,
      };
    },

    rect(sel) { const e = document.querySelector(sel); return e ? px(e) : { error: `no match: ${sel}` }; },

    bands(selectors) {
      const rows = selectors.map(s => { const e = document.querySelector(s);
        return e ? { sel: s, ...px(e) } : { sel: s, error: 'no match' }; });
      rows.forEach((row, i) => { const next = rows[i + 1];
        if (next && !row.error && !next.error) row.gapToNext = r2(next.top - row.bottom); });
      return { rows, contiguous: rows.every(r => r.gapToNext === undefined || r.gapToNext === 0) };
    },

    contrast(sel) {
      const e = document.querySelector(sel); if (!e) return { error: `no match: ${sel}` };
      const cs = getComputedStyle(e);
      const fgRaw = parseRGB(cs.color) || [0, 0, 0];
      const bg = effBg(e);
      const fg = (fgRaw[3] ?? 1) < 1 ? over(fgRaw, bg) : fgRaw.slice(0, 3);
      const L1 = lum(fg), L2 = lum(bg);
      const ratio = r2((Math.max(L1, L2) + .05) / (Math.min(L1, L2) + .05));
      const size = parseFloat(cs.fontSize), bold = +cs.fontWeight >= 700;
      const large = size >= 24 || (bold && size >= 18.66);
      return { sel, text: (e.textContent || '').trim().slice(0, 40), fg: hex(fg), bg: hex(bg),
               fontSize: size, bold, large, ratio, AA: ratio >= (large ? 3 : 4.5), AAA: ratio >= (large ? 4.5 : 7) };
    },

    markup(scope = 'body') {
      const root = document.querySelector(scope) || document.body;
      const q = s => [...root.querySelectorAll(s)];
      const name = e => (e.getAttribute('aria-label') || e.getAttribute('title') || e.textContent || '').trim();
      const ids = q('[id]').map(e => e.id);
      return {
        nestedInteractive: q('button button, button a, a a, a button').map(e => e.outerHTML.slice(0, 90)),
        unnamedControls: q('button, a[href], [role=button]').filter(e => !name(e)).map(e => e.outerHTML.slice(0, 90)),
        danglingAriaControls: q('[aria-controls]').filter(e => !document.getElementById(e.getAttribute('aria-controls')))
          .map(e => e.getAttribute('aria-controls')),
        toggleWithoutExpanded: q('[aria-controls]').filter(e => !e.hasAttribute('aria-expanded')).map(e => e.id || e.className),
        duplicateIds: ids.filter((v, i) => ids.indexOf(v) !== i),
        imagesWithoutAlt: q('img:not([alt])').length,
      };
    },

    focusables(scope = 'body') {
      const sel = 'a[href],button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea,[tabindex]:not([tabindex="-1"])';
      const root = document.querySelector(scope) || document.body;
      const rendered = [], notRendered = [];
      for (const e of root.querySelectorAll(sel)) {
        const label = (e.getAttribute('aria-label') || e.textContent || e.value || '').trim().slice(0, 30);
        const box = e.getClientRects().length > 0 && getComputedStyle(e).visibility !== 'hidden';
        if (!box) { notRendered.push(label); continue; }
        const b = e.getBoundingClientRect();
        rendered.push({ label, tag: e.tagName.toLowerCase(), top: r2(b.top),
          onScreen: b.bottom > 0 && b.top < innerHeight && b.right > 0 && b.left < innerWidth });
      }
      return { tabbable: rendered.length, notRendered: notRendered.length,
               offScreen: rendered.filter(x => !x.onScreen) };
    },

    scrollTo(y) { window.scrollTo(0, y); dispatchEvent(new Event('scroll')); return Math.round(scrollY); },

    noMotion(on = true) { document.body.classList.toggle('wf-no-motion', on); void document.body.offsetHeight; return on; },

    focusIn(sel) { const e = document.querySelector(sel); if (!e) return `no match: ${sel}`;
      e.dispatchEvent(new FocusEvent('focusin', { bubbles: true })); return 'dispatched'; },

    seq(steps, observe) {
      const obs = observe || (() => ({ y: Math.round(scrollY) }));
      return steps.map(s => { if (typeof s === 'function') s(); else if (s.scrollTo !== undefined) P.scrollTo(s.scrollTo);
        else if (s.click) document.querySelector(s.click)?.click();
        return { step: s.label || (s.scrollTo !== undefined ? `scrollTo ${s.scrollTo}` : s.click || 'fn'), ...obs() }; });
    },

    /* PARITY: rendered-label/enum fidelity. Does the app show the real strings
       the wireframe used ("Internal Review", not "in_review")? Returns the
       trimmed visible text of each match — compare arrays across the two sides. */
    texts(selectors) {
      const one = s => [...document.querySelectorAll(s)].map(e => (e.textContent || '').trim().replace(/\s+/g, ' '));
      return Array.isArray(selectors)
        ? Object.fromEntries(selectors.map(s => [s, one(s)]))
        : one(selectors);
    },

    /* PARITY: computed design-token value, to compare the app's live token
       against the wireframe's `:root` value (e.g. --accent). */
    token(name, sel = 'body') {
      const e = document.querySelector(sel) || document.body;
      const v = getComputedStyle(e).getPropertyValue(name).trim();
      return v || null;
    },

    /* Harmless off-wireframe: the app has no WF, so returns null there. */
    state() { return window.WF && window.WF.S ? JSON.parse(JSON.stringify(window.WF.S)) : null; },

    /* Drift check: the method set a parity run relies on. Compare against the
       scaffold's __wf to catch silent divergence. */
    methods() { return Object.keys(P).filter(k => typeof P[k] === 'function').sort(); },
  };
  return P;
})();
