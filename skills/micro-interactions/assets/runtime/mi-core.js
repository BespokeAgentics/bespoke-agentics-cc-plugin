/* micro-interactions runtime · motion helpers, catalogue, filters, matrix, toggles. Do not edit per project.
   Contract (set by the project's data.js before this file loads):
     MI.prims  [{id,name,status:"ships"|"new",say,spec}]            the motion vocabulary
     MI.flows  [{id,name,say}]                                       the app's user flows
     MI.ideas  [{id,flow,prims[],impact 1-3,effort 1-3,first?,title,why,trigger,moves,reduced,where}]
     MI.firstOrder [[id, why-this-order], ...]                       build order of the first batch
     MI.meta   {effort:{1:"…",2:"…",3:"…"}}                          optional effort labels
   Demos (demos.js, loaded after this file): MI.demos[id] = (stage, at) => {...}; MI.primDemos[primId] likewise.
   `at(ms, fn)` schedules one step; every scheduled step is cancelled on replay. */
(() => {
  const MI = window.MI;
  const root = document.documentElement;
  const $ = (id) => document.getElementById(id);
  const EASE = "cubic-bezier(.16,1,.3,1)";
  MI.EASE = EASE;
  MI.demos = MI.demos || {};
  MI.primDemos = MI.primDemos || {};
  MI.reduced = () => root.dataset.motion === "reduced";
  const still = (s) => MI.reduced() || Boolean(s?.closest?.(".no-anim"));
  MI.still = still;

  // ---- DOM helpers --------------------------------------------------------
  const h = (tag, cls, html) => {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html != null) e.innerHTML = html;
    return e;
  };
  MI.h = h;
  MI.pad = (s, cls = "") => s.appendChild(h("div", `stage-pad ${cls}`.trim()));
  MI.mark = (state = "flight") => {
    const w = h("span", null, `<svg class="mk" data-s="${state}" viewBox="0 0 12 12" aria-hidden="true"><circle class="ring" cx="6" cy="6" r="4.5"/><circle class="core" cx="6" cy="6" r="4"/></svg>`);
    return w.firstChild;
  };
  MI.set = (mark, state) => mark.setAttribute("data-s", state);
  MI.arrow = '<svg class="m-arrow" viewBox="0 0 12 12" aria-hidden="true"><path d="M2.5 6h7M6.5 3l3 3-3 3"/></svg>';
  MI.btn = (label, cls = "") => {
    const b = h("span", `m-btn ${cls}`.trim());
    b.appendChild(h("span", "lab", label));
    return b;
  };
  MI.img = (name) => `assets/${name}.jpg`;

  // Position of el inside stage s, in the stage's own (unscaled) pixels.
  MI.rel = (el, s) => {
    const a = s.getBoundingClientRect();
    const r = el.getBoundingClientRect();
    const k = a.width / (s.offsetWidth || a.width) || 1;
    return { x: (r.left - a.left) / k, y: (r.top - a.top) / k, w: r.width / k, h: r.height / k };
  };

  // ---- The five motions ---------------------------------------------------
  // Tick: the board's gauge tick (0.28 s, 0.32 em, 2 px blur).
  MI.tick = (el, text, dir = "up") => {
    el.classList.add("m-tick");
    el.textContent = text;
    el.classList.remove("up", "down");
    void el.offsetWidth;
    if (!MI.reduced()) el.classList.add(dir);
  };
  // Latch: color only, so it stays under reduced motion.
  MI.latch = (el, hue = "accent", cls = "m-latch") => {
    el.style.setProperty("--latch", `var(--${hue})`);
    el.classList.remove(cls);
    void el.offsetWidth;
    el.classList.add(cls);
  };
  // Cross-fade a label in place (the control keeps focus).
  MI.swap = (el, html) => {
    el.innerHTML = html;
    if (!still(el)) el.animate([{ opacity: 0, transform: "translateY(3px)" }, { opacity: 1, transform: "none" }], { duration: 180, easing: EASE });
  };
  // Echo: the control answers in words, then becomes its lasting state.
  MI.echo = (at, btn, text, ms = 1600, then) => {
    const lab = btn.querySelector(".lab") || btn;
    const was = lab.innerHTML;
    MI.swap(lab, text);
    if (ms) at(ms, () => MI.swap(lab, then ?? was));
  };
  // Glide: FLIP the elements across a DOM change.
  MI.flip = (s, els, mutate, duration = 440) => {
    const list = [].concat(els);
    const first = list.map((e) => MI.rel(e, s));
    mutate();
    if (still(s)) return;
    list.forEach((e, i) => {
      const last = MI.rel(e, s);
      const dx = first[i].x - last.x;
      const dy = first[i].y - last.y;
      if (Math.abs(dx) < 0.5 && Math.abs(dy) < 0.5) return;
      e.animate([{ transform: `translate(${dx}px,${dy}px)` }, { transform: "none" }], { duration, easing: EASE });
    });
  };
  // Handoff: a ghost of the request travels to where it is tracked.
  MI.ghost = (s, from, to, label) => {
    if (still(s)) return;
    const a = MI.rel(from, s);
    const b = MI.rel(to, s);
    const g = h("span", "m-ghost", label);
    s.appendChild(g);
    const gw = g.offsetWidth;
    const gh = g.offsetHeight;
    const x0 = a.x + a.w / 2 - gw / 2;
    const y0 = a.y + a.h / 2 - gh / 2;
    const x1 = b.x + b.w / 2 - gw / 2;
    const y1 = b.y + b.h / 2 - gh / 2;
    const mx = (x0 + x1) / 2;
    const my = Math.min(y0, y1) - 26;
    g.animate(
      [
        { transform: `translate(${x0}px,${y0}px) scale(.9)`, opacity: 0 },
        { transform: `translate(${x0}px,${y0 - 6}px) scale(1)`, opacity: 1, offset: 0.14 },
        { transform: `translate(${mx}px,${my}px) scale(.85)`, opacity: 1, offset: 0.56 },
        { transform: `translate(${x1}px,${y1}px) scale(.45)`, opacity: 0 },
      ],
      { duration: 560, easing: "cubic-bezier(.45,0,.2,1)", fill: "forwards" },
    ).onfinish = () => g.remove();
  };
  // A press, so a viewer sees what the person clicked. Teaching aid, not product motion.
  MI.press = (s, el) => {
    if (still(s)) return;
    el.animate([{ transform: "scale(1)" }, { transform: "scale(.96)" }, { transform: "scale(1)" }], { duration: 180 });
    const r = MI.rel(el, s);
    const p = h("span", "m-press");
    s.appendChild(p);
    const x = r.x + r.w / 2 - 11;
    const y = r.y + r.h / 2 - 11;
    p.animate([{ transform: `translate(${x}px,${y}px) scale(.4)`, opacity: 0.6 }, { transform: `translate(${x}px,${y}px) scale(1.6)`, opacity: 0 }], { duration: 460, easing: EASE, fill: "forwards" }).onfinish = () => p.remove();
  };
  // A celebration burst: 14 discs and rings, 0.95 s. Inks are --flair-1..7, falling back to the state hues.
  const INKS = [1, 2, 3, 4, 5, 6, 7];
  const FALLBACK = ["accent", "amber", "green", "red", "accent", "amber", "green"];
  MI.burst = (s, el) => {
    if (still(s)) return;
    const r = MI.rel(el, s);
    const cx = r.x + r.w / 2 - 3.5;
    const cy = r.y + r.h / 2 - 3.5;
    for (let i = 0; i < 14; i++) {
      const ring = i % 3 === 0;
      const d = h("span", `m-burst${ring ? " ring" : ""}`);
      const ink = `var(--flair-${INKS[i % 7]},var(--${FALLBACK[i % 7]}))`;
      if (ring) d.style.color = ink;
      else d.style.background = ink;
      s.appendChild(d);
      const ang = (i / 14) * Math.PI * 2 + (i % 2) * 0.3;
      const dist = 36 + ((i * 37) % 34);
      d.animate(
        [
          { transform: `translate(${cx}px,${cy}px) scale(.3)`, opacity: 1 },
          { transform: `translate(${cx + Math.cos(ang) * dist}px,${cy + Math.sin(ang) * dist - 10}px) rotate(${(i * 47) % 180}deg) scale(1)`, opacity: 0 },
        ],
        { duration: 950, easing: EASE, fill: "forwards" },
      ).onfinish = () => d.remove();
    }
  };
  MI.type = (at, el, text, start, every = 34) => {
    for (let i = 1; i <= text.length; i++) at(start + i * every, () => { el.textContent = text.slice(0, i); });
    return start + text.length * every;
  };
  MI.elapsed = (n) => `${Math.floor(n / 60)}:${String(n % 60).padStart(2, "0")}`;
  MI.count = (at, el, start, from, to, step = 1000, fmt = MI.elapsed) => {
    for (let n = from; n <= to; n++) at(start + (n - from) * step, () => { el.textContent = fmt(n); });
  };

  // ---- Running a stage ----------------------------------------------------
  MI.run = (s, fn) => {
    (s._t || []).forEach(clearTimeout);
    s._t = [];
    s.getAnimations?.({ subtree: true }).forEach((a) => a.cancel());
    s.replaceChildren();
    const at = (ms, f) => { s._t.push(setTimeout(f, ms)); };
    try {
      fn(s, at);
    } catch (error) {
      console.error(error);
      s.textContent = `Demo failed: ${error.message}`;
    }
  };
  const play = (s) => {
    const id = s.dataset.demo;
    const fn = id.startsWith("p:") ? MI.primDemos[id.slice(2)] : MI.demos[id];
    if (!fn) { s.textContent = "Demo not built"; return; }
    s.dataset.played = "1";
    MI.run(s, fn);
  };
  MI.playStage = play;
  const seen = new IntersectionObserver((entries) => {
    for (const e of entries) {
      if (!e.isIntersecting || e.target.dataset.played) continue;
      play(e.target);
    }
  }, { threshold: 0.45 });
  const replayButton = (s, label) => {
    const b = h("button", "replay", '<svg aria-hidden="true"><use href="#i-restart"/></svg>Replay');
    b.type = "button";
    b.setAttribute("aria-label", `Replay ${label}`);
    b.addEventListener("click", () => play(s));
    return b;
  };

  // ---- Vocabulary -----------------------------------------------------------
  const vocab = $("vocab");
  vocab.style.setProperty("--n", String(MI.prims.length));
  for (const p of MI.prims) {
    const item = h("article", "vocab-item");
    const wrap = h("div", "idea-stage vocab-stage");
    const s = h("div", "stage");
    s.dataset.demo = `p:${p.id}`;
    s.setAttribute("role", "img");
    s.setAttribute("aria-label", `${p.name}: ${p.say}`);
    wrap.append(s, replayButton(s, p.name));
    const body = h("div", "vocab-body");
    body.innerHTML = `<h3>${p.name}<span class="status">${p.status === "ships" ? "ships today" : "new"}</span></h3><p>${p.say}</p><p class="spec">${p.spec}</p>`;
    item.append(wrap, body);
    vocab.appendChild(item);
    seen.observe(s);
  }

  // ---- Catalogue ------------------------------------------------------------
  const PRIM = Object.fromEntries(MI.prims.map((p) => [p.id, p]));
  const IMPACT = { 3: "High", 2: "Medium", 1: "Low" };
  const EFFORT = Object.assign({ 1: "Under half a day", 2: "About a day", 3: "Several days" }, MI.meta?.effort);
  const ideaCard = (idea) => {
    const a = h("article", "idea");
    a.id = `idea-${idea.id}`;
    a.dataset.flow = idea.flow;
    a.dataset.prims = idea.prims.join(" ");
    if (idea.first) a.dataset.first = "1";
    const st = h("div", "idea-stage");
    const s = h("div", "stage");
    s.dataset.demo = idea.id;
    s.setAttribute("role", "img");
    s.setAttribute("aria-label", `${idea.title}. ${idea.moves}`);
    st.append(s, replayButton(s, idea.id));
    const body = h("div", "idea-body");
    body.innerHTML = `
      <div class="idea-top"><span class="idea-id">${idea.id}</span>${idea.prims.map((p) => `<span class="tag">${PRIM[p].name}</span>`).join("")}${idea.first ? '<span class="tag first">First batch</span>' : ""}</div>
      <h4>${idea.title}</h4>
      <p class="why">${idea.why}</p>
      <dl><dt>When</dt><dd>${idea.trigger}</dd><dt>Moves</dt><dd>${idea.moves}</dd><dt>Reduced</dt><dd>${idea.reduced}</dd><dt>Where</dt><dd><code>${idea.where}</code></dd></dl>
      <div class="idea-foot"><span>Impact <b>${IMPACT[idea.impact]}</b></span><span>Effort <b>${EFFORT[idea.effort]}</b></span></div>`;
    a.append(st, body);
    seen.observe(s);
    return a;
  };
  const cat = $("catalogue");
  for (const flow of MI.flows) {
    const ideas = MI.ideas.filter((i) => i.flow === flow.id);
    const sec = h("section", "flow");
    sec.dataset.flow = flow.id;
    sec.innerHTML = `<div class="flow-head"><h3>${flow.name}</h3><span class="count">${ideas.length}</span><p>${flow.say}</p></div>`;
    const grid = h("div", "ideas");
    ideas.forEach((i) => grid.appendChild(ideaCard(i)));
    sec.appendChild(grid);
    cat.appendChild(sec);
  }
  const empty = h("p", "empty-filter", "No idea matches these filters.");
  empty.hidden = true;
  cat.appendChild(empty);

  // ---- Filters --------------------------------------------------------------
  const filter = { flow: "all", prim: "all", first: false };
  const chip = (group, value, label, n) => {
    const b = h("button", null, `${label} <span class="n">${n}</span>`);
    b.type = "button";
    b.dataset.value = value;
    b.setAttribute("aria-pressed", String(value === "all"));
    b.addEventListener("click", () => {
      filter[group] = value;
      b.parentElement.querySelectorAll("button").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
      apply();
    });
    return b;
  };
  $("flow-chips").append(chip("flow", "all", "All flows", MI.ideas.length), ...MI.flows.map((f) => chip("flow", f.id, f.name, MI.ideas.filter((i) => i.flow === f.id).length)));
  $("prim-chips").append(chip("prim", "all", "Any motion", MI.prims.length), ...MI.prims.map((p) => chip("prim", p.id, p.name, MI.ideas.filter((i) => i.prims.includes(p.id)).length)));
  $("only-first").addEventListener("change", (e) => { filter.first = e.target.checked; apply(); });
  const apply = () => {
    let shown = 0;
    cat.querySelectorAll(".idea").forEach((a) => {
      const ok = (filter.flow === "all" || a.dataset.flow === filter.flow)
        && (filter.prim === "all" || a.dataset.prims.split(" ").includes(filter.prim))
        && (!filter.first || a.dataset.first);
      a.hidden = !ok;
      if (ok) shown++;
    });
    cat.querySelectorAll(".flow").forEach((sec) => { sec.hidden = !sec.querySelector(".idea:not([hidden])"); });
    empty.hidden = shown > 0;
    $("filter-count").textContent = `Showing ${shown} of ${MI.ideas.length}`;
  };
  apply();
  const resetFilters = () => {
    filter.flow = "all"; filter.prim = "all"; filter.first = false;
    $("only-first").checked = false;
    document.querySelectorAll("#flow-chips button, #prim-chips button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.value === "all")));
    apply();
  };

  // Jump to an idea: show it, scroll, latch the card, replay its demo.
  const go = (id) => {
    const a = $(`idea-${id}`);
    if (!a) return;
    if (a.hidden) resetFilters();
    a.scrollIntoView({ behavior: MI.reduced() ? "auto" : "smooth", block: "center" });
    a.classList.remove("is-focus");
    void a.offsetWidth;
    a.classList.add("is-focus");
    history.replaceState(null, "", `#idea-${id}`);
    setTimeout(() => play(a.querySelector(".stage")), MI.reduced() ? 50 : 450);
  };
  MI.go = go;

  // ---- Where to start -------------------------------------------------------
  const matrix = $("matrix");
  const efforts = [1, 2, 3].filter((e) => MI.ideas.some((i) => i.effort === e));
  for (const imp of [3, 2, 1]) {
    matrix.appendChild(h("div", "axis y", IMPACT[imp]));
    for (const eff of efforts) {
      const cell = h("div", `cell${imp === 3 && eff === 1 ? " sweet" : ""}`);
      MI.ideas.filter((i) => i.impact === imp && i.effort === eff).forEach((i) => {
        const b = h("button", i.first ? "first" : null, i.id);
        b.type = "button";
        b.title = i.title;
        b.setAttribute("aria-label", `${i.id}: ${i.title}${i.first ? " (first batch)" : ""}`);
        b.addEventListener("click", () => go(i.id));
        cell.appendChild(b);
      });
      matrix.appendChild(cell);
    }
  }
  matrix.style.gridTemplateColumns = `72px repeat(${efforts.length},minmax(0,1fr))`;
  matrix.appendChild(h("div", "axis corner mono", "Impact"));
  efforts.forEach((e) => matrix.appendChild(h("div", "axis x", EFFORT[e])));

  MI.firstOrder = MI.firstOrder || MI.ideas.filter((i) => i.first).map((i) => [i.id, i.why]);
  const fb = $("first-batch");
  for (const [id, note] of MI.firstOrder) {
    const idea = MI.ideas.find((i) => i.id === id);
    if (!idea) { console.error(`MI.firstOrder names ${id}, which is not in MI.ideas`); continue; }
    const li = h("li");
    li.innerHTML = `<a href="#idea-${id}">${id} · ${idea.title}</a><span class="ref">${idea.where.split(/[,(]/)[0].trim()}</span><span class="w">${note}</span>`;
    li.querySelector("a").addEventListener("click", (e) => { e.preventDefault(); go(id); });
    fb.appendChild(li);
  }
  $("count-first").textContent = String(MI.ideas.filter((i) => i.first).length);
  $("count-ideas").textContent = String(MI.ideas.length);
  if ($("count-prims")) $("count-prims").textContent = String(MI.prims.length);

  // ---- Theme and motion -----------------------------------------------------
  const press = (attr, value) => document.querySelectorAll(`[${attr}]`).forEach((b) => b.setAttribute("aria-pressed", String(b.getAttribute(attr) === value)));
  const setTheme = (t) => { root.dataset.theme = t; press("data-theme-set", t); };
  const inView = (el) => { const r = el.getBoundingClientRect(); return r.bottom > 0 && r.top < innerHeight; };
  const setMotion = (m, replay) => {
    root.dataset.motion = m;
    press("data-motion-set", m);
    if (replay) document.querySelectorAll(".stage[data-played]").forEach((s) => { if (inView(s)) play(s); });
    document.dispatchEvent(new CustomEvent("mi:motion"));
  };
  setTheme(matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  setMotion(matchMedia("(prefers-reduced-motion: reduce)").matches ? "reduced" : "full");
  document.querySelectorAll("[data-theme-set]").forEach((b) => b.addEventListener("click", () => setTheme(b.dataset.themeSet)));
  document.querySelectorAll("[data-motion-set]").forEach((b) => b.addEventListener("click", () => setMotion(b.dataset.motionSet, true)));

  addEventListener("load", () => {
    const m = location.hash.match(/^#idea-([A-Za-z]+\d+)$/);
    if (m) go(m[1]);
  });
})();
