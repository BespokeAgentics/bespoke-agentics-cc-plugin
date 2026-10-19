/* micro-interactions runtime · MI.b, builders for the mini-app the demos run on. Do not edit per project;
   add project shapes (B.myThing = …) at the top of the project's demos file instead.
   Every builder returns an element with named parts attached (t.v, c.pill, col.body, bar.chip.v …). */
(() => {
  const { h } = MI;
  const B = (MI.b = {});

  B.tile = (lab, num, foot, prog) => {
    const t = h("div", "m-tile");
    t.innerHTML = `<span class="lab">${lab}</span><span class="num"><span class="v">${num}</span></span>${prog != null ? `<div class="m-prog"><i style="--w:${prog}"></i></div>` : ""}<span class="foot">${foot}</span>`;
    t.v = t.querySelector(".v");
    t.f = t.querySelector(".foot");
    t.p = t.querySelector(".m-prog i");
    return t;
  };
  B.card = (id, title, pill, pcls, foot = "") => {
    const c = h("div", "m-card");
    c.innerHTML = `<div class="m-row"><span class="m-mono">${id}</span><span class="m-grow"></span><span class="m-pill ${pcls}">${pill}</span></div><div class="m-title" style="margin:5px 0 3px">${title}</div><div class="m-small m-muted foot">${foot}</div>`;
    c.pill = c.querySelector(".m-pill");
    c.foot = c.querySelector(".foot");
    c.ttl = c.querySelector(".m-title");
    return c;
  };
  B.col = (name, n, cls = "") => {
    const c = h("div", "m-col");
    c.innerHTML = `<div class="m-colhead ${cls}"><span>${name}</span><span class="m-mono n">${n}</span></div>`;
    c.body = h("div", "m-colbody");
    c.appendChild(c.body);
    c.n = c.querySelector(".n");
    c.head = c.querySelector(".m-colhead");
    return c;
  };
  // A bar docked to the stage's bottom edge: a tab, a one-line ticker, a counted chip. Labels in the app's words.
  B.hud = (s, tick = "", count = 0, { tab = "Activity", chip: chipLabel = "Your requests" } = {}) => {
    const bar = h("div", "m-hud");
    bar.innerHTML = `<span class="m-hudtab">${tab}</span><span class="m-ticker"><span>${tick}</span></span>`;
    const chip = h("span", "m-chip");
    chip.innerHTML = `<span class="mk-slot"></span><span class="lab">${chipLabel}</span><span class="v m-mono">${count}</span>`;
    bar.appendChild(chip);
    s.appendChild(bar);
    bar.chip = chip;
    chip.v = chip.querySelector(".v");
    chip.dot = chip.querySelector(".mk-slot");
    bar.ticker = bar.querySelector(".m-ticker");
    return bar;
  };
  B.status = (state, label, cls = "") => {
    const r = h("div", "m-row m-statusline");
    r.mk = MI.mark(state);
    r.lab = h("span", `mk-label ${cls}`.trim(), label);
    r.append(r.mk, r.lab);
    return r;
  };
  B.settle = (row, state, label, labelCls = "ink") => {
    MI.set(row.mk, state);
    row.lab.className = `mk-label ${labelCls}`;
    MI.tick(row.lab, label);
  };
  B.hop = (s, live) => {
    if (MI.still(s)) return;
    [...live.children].forEach((d, i) => d.animate(
      [{ transform: "none" }, { transform: "translateY(-5px)", offset: 0.25 }, { transform: "translateY(1px)", offset: 0.4 }, { transform: "none", offset: 0.55 }, { transform: "none" }],
      { duration: 900, delay: i * 150 },
    ));
  };
  B.check = (on = true) => h("span", `m-check${on ? " on" : ""}`, '<svg viewBox="0 0 10 10" aria-hidden="true"><path d="M2 5.2l2 2 4-4.4"/></svg>');
  B.svgArrow = (dir = "right") => `<svg class="m-arrow" viewBox="0 0 12 12" aria-hidden="true"${dir === "left" ? ' style="transform:scaleX(-1)"' : ""}><path d="M2.5 6h7M6.5 3l3 3-3 3"/></svg>`;
  B.live = () => h("span", "m-live", "<i></i><i></i><i></i>");
  B.enter = (s, el, dy = 6) => {
    if (MI.still(s)) return;
    el.animate([{ opacity: 0, transform: `translateY(${dy}px)` }, { opacity: 1, transform: "none" }], { duration: 240, easing: MI.EASE });
  };
  B.fade = (s, el, to = 0, ms = 150) => {
    if (MI.still(s)) { el.style.opacity = String(to); return; }
    el.animate([{ opacity: to ? 0 : 1 }, { opacity: to }], { duration: ms, fill: "forwards" });
  };
  // Shared-element move with scale (FLIP).
  B.flipScale = (s, el, mutate, duration = 440) => {
    const a = MI.rel(el, s);
    mutate();
    if (MI.still(s)) return;
    const b = MI.rel(el, s);
    const k = a.w / b.w;
    el.style.transformOrigin = "0 0";
    el.animate([{ transform: `translate(${a.x - b.x}px,${a.y - b.y}px) scale(${k})` }, { transform: "none" }], { duration, easing: MI.EASE });
  };

})();
