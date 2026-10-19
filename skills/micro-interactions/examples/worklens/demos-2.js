/* worklens example · Visual progress, Agents, Your requests and HUD demos. */
(() => {
  const { h, b: B } = MI;
  const D = MI.demos;

  // ---- Visual progress ------------------------------------------------------
  D.C1 = (s, at) => {
    const p = MI.pad(s);
    p.style.justifyContent = "flex-start";
    const head = h("div", "m-row m-small");
    const lab = h("span", "m-mono m-muted m-grow", "9 captures · newest first");
    const slot = h("span");
    head.append(lab, slot);
    const strip = h("div", "m-strip");
    const c1 = B.capture("accept-all-review", "Accept all review");
    const c2 = B.capture("run-slip-desktop-light", "Run slip · desktop light");
    strip.append(c1, c2);
    p.append(head, strip);
    at(800, () => {
      const fresh = B.capture("accept-all-as-a-right-drawer", "Accept all as a right drawer");
      MI.flip(s, [c1, c2], () => strip.prepend(fresh));
      if (!MI.still(s)) fresh.animate([{ opacity: 0, transform: "translateX(-14px)" }, { opacity: 1, transform: "none" }], { duration: 440, easing: MI.EASE });
      MI.latch(fresh, "accent");
      MI.tick(lab, "10 captures · newest first");
    });
    at(3300, () => {
      const pill = h("span", "m-pillnew", `1 new screenshot ${B.svgArrow("left")}`);
      slot.replaceChildren(pill);
      B.enter(s, pill, 4);
      MI.tick(lab, "4–5 of 11 · you scrolled");
    });
  };

  D.C2 = (s, at) => {
    const p = MI.pad(s);
    const head = h("div", "m-row m-small");
    const lab = h("span", "m-mono m-muted m-grow", "1–3 of 9");
    const prev = h("span", "m-btn", B.svgArrow("left"));
    const next = h("span", "m-btn", B.svgArrow());
    prev.style.opacity = ".45";
    head.append(lab, prev, next);
    const strip = h("div", "m-strip m-strip3");
    const imgs = ["accept-all-as-a-right-drawer", "critique-slip-as-a-left-drawer", "accept-all-review", "run-slip-desktop-light", "accept-all-review", "critique-slip-as-a-left-drawer"];
    const track = h("div", "m-track");
    imgs.forEach((i) => track.appendChild(B.capture(i)));
    strip.appendChild(track);
    p.append(head, strip);
    track.style.transition = MI.still(s) ? "none" : "transform .44s cubic-bezier(.16,1,.3,1)";
    at(800, () => { MI.press(s, next); track.style.transform = "translateX(calc(-100% / 2))"; MI.tick(lab, "4–6 of 9"); prev.style.opacity = "1"; });
    at(2600, () => { MI.press(s, prev); track.style.transform = "none"; MI.tick(lab, "1–3 of 9", "down"); prev.style.opacity = ".45"; });
  };

  const drawer = (s, title, w = "62%") => {
    const d = h("div", "m-drawer");
    d.style.width = w;
    d.innerHTML = `<div class="m-drawer-head"><span class="m-title">${title}</span><span class="m-btn">Close</span></div>`;
    s.appendChild(d);
    return d;
  };

  D.C3 = (s, at) => {
    const scrim = h("div", "m-scrim");
    s.appendChild(scrim);
    const pv = drawer(s, "Accept all as a right drawer", "82%");
    const img = h("img", "m-shot m-preview");
    img.src = MI.img("accept-all-as-a-right-drawer");
    img.alt = "";
    const bar = h("div", "m-capture");
    const crit = h("div", "m-cmdbar", `<span class="m-grow">Critique this screen</span>${MI.arrow}`);
    crit.style.borderTop = "0";
    bar.appendChild(crit);
    pv.append(img, bar);
    at(800, () => MI.press(s, crit));
    at(950, () => {
      const sl = h("div", "m-slip");
      const left = h("div", "m-col");
      const right = h("div", "m-col");
      right.innerHTML = '<div class="m-small m-strong">What kind of critique?</div><div class="m-row"><span class="m-btn">Layout</span><span class="m-btn">Copy</span></div><div class="m-field"><span class="ph">Say what you see…</span></div>';
      sl.append(left, right);
      const fade = [bar, pv.querySelector(".m-drawer-head .m-title")];
      B.flipScale(s, img, () => {
        left.appendChild(img);
        img.classList.remove("m-preview");
        bar.remove();
        pv.querySelector(".m-drawer-head .m-title").textContent = "Critique this screen";
        pv.appendChild(sl);
        pv.style.width = "82%";
      });
      if (!MI.still(s)) right.animate([{ opacity: 0 }, { opacity: 0, offset: 0.35 }, { opacity: 1 }], { duration: 420 });
      void fade;
    });
  };

  D.C4 = (s, at) => {
    const p = MI.pad(s);
    const kinds = h("div", "m-row");
    const k1 = h("span", "m-btn", "Layout");
    const k2 = h("span", "m-btn", "Copy");
    const k3 = h("span", "m-btn", "Contrast");
    kinds.append(k1, k2, k3);
    const f = h("div", "m-field focus", '<span class="txt"></span><span class="m-caret"></span>');
    const box = h("div", "m-agent");
    box.innerHTML = '<div>The agent receives</div><div class="m-mono">[worklens board] Critique · Accept all @ 705b6b9</div><div class="line m-small"></div>';
    const line = box.querySelector(".line");
    p.append(kinds, f, box);
    const kindsSel = [];
    const refresh = (t) => { MI.latch(line, "accent", "m-wash"); line.textContent = `${kindsSel.join(", ") || "No kind"} · ${t || "…"}`; };
    at(500, () => { MI.press(s, k1); k1.classList.add("hot"); kindsSel.push("Layout"); refresh(""); });
    at(1100, () => { MI.press(s, k2); k2.classList.add("hot"); kindsSel.push("Copy"); refresh(""); });
    const txt = "The Accept button sits below the fold at 390 px.";
    const el = f.querySelector(".txt");
    for (let i = 1; i <= txt.length; i++) at(1600 + i * 32, () => { el.textContent = txt.slice(0, i); line.textContent = `${kindsSel.join(", ")} · ${txt.slice(0, i)}`; });
    at(1600 + txt.length * 32 + 60, () => MI.latch(line, "accent", "m-wash"));
  };

  const receipt = () => {
    const r = h("div", "m-panel m-box");
    const top = h("div", "m-row");
    r.st = B.status("flight", "Queued for the next agent");
    top.append(r.st);
    const steps = h("div", "m-steps");
    const mk = (t) => h("span", "m-step", `<span class="m-mono">${t}</span>`);
    r.s1 = mk("Queued"); r.s2 = mk("Delivered"); r.s3 = mk("Replied");
    r.l1 = h("span", "m-step-line", "<i></i>");
    r.l2 = h("span", "m-step-line", "<i></i>");
    steps.append(r.s1, r.l1, r.s2, r.l2, r.s3);
    steps.style.alignSelf = "stretch";
    r.append(top, steps);
    return r;
  };

  D.C5 = (s, at) => {
    const p = MI.pad(s);
    p.style.justifyContent = "flex-start";
    p.style.paddingTop = "18px";
    const form = h("div", "m-panel m-box");
    const f = h("div", "m-field", "The Accept button sits below the fold at 390 px.");
    const q = MI.btn("Queue critique", "fill");
    const r = h("div", "m-row");
    r.append(h("span", "m-grow"), q);
    form.append(f, r);
    p.appendChild(form);
    const bar = B.hud(s, "", 0);
    at(700, () => MI.press(s, q));
    at(850, () => {
      MI.ghost(s, q, bar.chip, "Critique · Accept all");
      const rc = receipt();
      rc.s1.classList.add("on");
      B.flipScale(s, form, () => { form.replaceChildren(...rc.childNodes); });
    });
    at(1420, () => {
      bar.chip.dot.replaceChildren(MI.mark("flight"));
      MI.tick(bar.chip.v, "1");
      MI.latch(bar.chip, "accent");
    });
  };

  D.C6 = (s, at) => {
    const p = MI.pad(s);
    const r = receipt();
    p.appendChild(r);
    at(300, () => r.s1.classList.add("on"));
    at(1300, () => { r.l1.classList.add("on"); });
    at(1600, () => { r.s2.classList.add("on"); MI.swap(r.st.lab, "Delivered to chrome-validator · reply not in yet"); });
    at(3200, () => { r.l2.classList.add("on"); });
    at(3500, () => { r.s3.classList.add("on"); B.settle(r.st, "ok", "chrome-validator replied · new"); });
  };

  D.C7 = (s, at) => {
    const p = MI.pad(s);
    const st = B.status("ok", "Good · Fast", "ink");
    const m = h("div", "m-metrics");
    const metric = (lab, val) => {
      const e = h("div", "m-metric", `<div class="lab">${lab}</div><div class="val"><span class="v">${val}</span><span class="m-delta"></span></div>`);
      e.v = e.querySelector(".v");
      e.d = e.querySelector(".m-delta");
      return e;
    };
    const a = metric("First byte (median)", "38 ms");
    const b = metric("Full response", "41 ms");
    const c = metric("Page size", "14 KB");
    const d = metric("Scripts and stylesheets", "4 files, 220 KB");
    m.append(a, b, c, d);
    const again = MI.btn("Run again", "fill");
    const rr = h("div", "m-row");
    rr.append(h("span", "m-grow"), again);
    p.append(st, m, rr);
    at(600, () => { MI.press(s, again); MI.set(st.mk, "flight"); MI.swap(st.lab, "Running · 0:01"); });
    at(1700, () => {
      MI.set(st.mk, "ok");
      MI.tick(st.lab, "Good · Fast");
      const set = (e, v, dv, cls, dir) => { MI.tick(e.v, v, dir); e.d.className = `m-delta ${cls}`; MI.swap(e.d, dv); };
      set(a, "26 ms", "−12 ms", "ok", "down");
      set(b, "29 ms", "−12 ms", "ok", "down");
      set(c, "15 KB", "+1 KB", "warn", "up");
      e0(d);
    });
    const e0 = (e) => { e.d.className = "m-delta"; MI.swap(e.d, '<span class="m-muted">same</span>'); };
  };

  D.C8 = (s, at) => {
    const p = MI.pad(s);
    const cap = B.capture("accept-all-as-a-right-drawer", "Accept all as a right drawer");
    cap.classList.add("m-capture-short");
    const bar = B.cmd("Perform performance test", "flight", "Running · 0:00");
    const bar2 = h("div", "m-cmdbar", `<span class="m-grow">Critique this screen</span><span class="res"><span class="mk-label">1 open</span></span>${MI.arrow}`);
    cap.append(bar, bar2);
    p.appendChild(cap);
    MI.count(at, bar.lab, 0, 0, 2, 600, (n) => `Running · ${MI.elapsed(n)}`);
    at(1900, () => { MI.set(bar.mk, "ok"); bar.lab.className = "mk-label ink"; MI.tick(bar.lab, "Fast · just now"); });
    at(3900, () => { MI.set(bar.mk, "flight"); bar.lab.className = "mk-label"; MI.swap(bar.lab, "Running · 0:00"); });
    at(5200, () => { MI.set(bar.mk, "bad"); bar.lab.className = "mk-label bad"; MI.tick(bar.lab, "Not reachable · just now"); });
  };

  // ---- Agents ---------------------------------------------------------------
  const bulletin = () => {
    const b = h("div", "m-panel m-box m-bulletin");
    b.innerHTML = '<div class="m-row" style="align-self:stretch"><div class="m-grow"><div class="m-eyebrow">FROM THE AGENTS</div><div class="m-title">Current activity</div></div></div>';
    return b;
  };

  D.D1 = (s, at) => {
    const p = MI.pad(s);
    const b = bulletin();
    const btn = MI.btn("Request an update", "fill");
    b.querySelector(".m-row").appendChild(btn);
    const steps = h("div", "m-steps");
    const names = ["Queued", "Received", "Working", "Replied"];
    const el = names.map((n) => h("span", "m-step", `<span class="m-mono">${n}</span>`));
    const lines = [0, 1, 2].map(() => h("span", "m-step-line", "<i></i>"));
    el.forEach((e, i) => { steps.appendChild(e); if (lines[i]) steps.appendChild(lines[i]); });
    steps.style.alignSelf = "stretch";
    steps.style.opacity = ".35";
    const st = B.status("flight", "Waiting for 2 agents");
    st.style.visibility = "hidden";
    b.append(st, steps);
    p.appendChild(b);
    at(600, () => {
      MI.press(s, btn);
      MI.echo(at, btn, "Asked 2 agents", 1800);
      st.style.visibility = "";
      steps.style.opacity = "1";
      el[0].classList.add("on");
    });
    at(1700, () => { lines[0].classList.add("on"); el[1].classList.add("on"); MI.swap(st.lab, "Received by 2 · hosted/reviewer working"); });
    at(2700, () => { lines[1].classList.add("on"); el[2].classList.add("on"); });
    at(4200, () => { lines[2].classList.add("on"); el[3].classList.add("on"); B.settle(st, "ok", "2 of 2 replied"); });
  };

  D.D2 = (s, at) => {
    const p = MI.pad(s);
    const b = bulletin();
    const grid = h("div", "m-replies");
    const reply = (who, t, items) => {
      const r = h("div", "m-reply");
      r.innerHTML = `<div class="m-row"><span class="m-strong m-grow m-clip">${who}</span><span class="m-mono m-muted t">${t}</span></div><ul>${items.map((i) => `<li>${i}</li>`).join("")}</ul>`;
      return r;
    };
    grid.appendChild(reply("chrome-validator", "11:02 PM", ["Validated the slip from the right", "Withdraw works by keyboard"]));
    b.appendChild(grid);
    p.appendChild(b);
    at(900, () => {
      const r = reply("sandbox-seed", "just now", ["T-3 in progress: timing all 9 captures", "Needs the per-URL decision"]);
      grid.appendChild(r);
      B.enter(s, r, 6);
      MI.latch(r, "accent", "m-replylatch");
    });
  };

  D.D3 = (s, at) => {
    const p = MI.pad(s);
    const head = h("div", "m-row");
    head.innerHTML = '<span class="m-eyebrow m-grow">FROM THE SESSION LOGS</span><span class="m-pill warn">inferred</span>';
    const card = h("div", "m-steward m-steward-draw");
    card.innerHTML = '<div class="m-strong m-small">chrome-validator · read in the log</div><ul class="m-bul"><li>Opened the critique slip three times</li><li>Ran the web suite: 49 passed</li><li>Waiting on the per-URL decision</li></ul><div class="m-mono m-muted m-small">egress audit · 2.1 KB redacted</div>';
    p.append(head, card);
    const lis = [...card.querySelectorAll("li"), card.querySelector(".m-mono")];
    card.style.setProperty("--draw", "0");
    lis.forEach((l) => { l.style.opacity = "0"; });
    if (MI.still(s)) { at(400, () => { card.style.setProperty("--draw", "1"); lis.forEach((l) => { l.style.opacity = "1"; }); }); return; }
    at(400, () => {
      const t0 = performance.now();
      const step = (t) => {
        const k = Math.min(1, (t - t0) / 500);
        card.style.setProperty("--draw", String(1 - (1 - k) ** 3));
        if (k < 1) requestAnimationFrame(step);
      };
      requestAnimationFrame(step);
    });
    lis.forEach((l, i) => at(800 + i * 90, () => { l.style.opacity = "1"; B.enter(s, l, 3); }));
  };

  D.D4 = (s, at) => {
    const p = MI.pad(s);
    const steps = h("div", "m-steps");
    steps.innerHTML = '<span class="m-step on"><span class="m-mono">Received</span></span><span class="m-step-line on"><i></i></span><span class="m-step on"><span class="m-mono">Working</span></span>';
    const st = B.status("flight", "hosted/reviewer");
    const line = h("div", "m-small m-muted m-liveline");
    const v = h("span", null, "Reading assets/board/board.js");
    line.appendChild(v);
    p.append(steps, st, line);
    const words = ["Running pnpm test:web", "Comparing 9 captures", "Writing the reply"];
    words.forEach((w, i) => at(1100 + i * 1100, () => MI.tick(v, w)));
    at(4600, () => { B.settle(st, "ok", "hosted/reviewer replied"); v.textContent = ""; });
  };

  D.D5 = (s, at) => {
    const p = MI.pad(s);
    const b = bulletin();
    const btn = MI.btn("Request an update", "fill");
    btn.classList.add("wait");
    b.querySelector(".m-row").appendChild(btn);
    const st = B.status("flight", "Waiting · 4:58 left");
    b.appendChild(st);
    p.appendChild(b);
    MI.count(at, st.lab, 0, 298, 300, 500, (n) => `Waiting · ${MI.elapsed(300 - n)} left`);
    at(1600, () => {
      B.settle(st, "idle", "Window ended · no agent checked in", "");
      btn.classList.remove("wait");
      MI.echo(at, btn, "Ask again", 0);
    });
  };

  // ---- Your requests --------------------------------------------------------
  D.E1 = (s, at) => {
    const p = MI.pad(s);
    p.appendChild(h("div", "m-bar"));
    p.appendChild(h("div", "m-bar", null)).style.width = "70%";
    const bar = B.hud(s, '<span class="type">board.run.started</span> Performance test on Accept all', 1);
    bar.chip.dot.replaceChildren(MI.mark("flight"));
    at(900, () => { bar.chip.dot.firstChild.setAttribute("data-s", "ok"); MI.swap(bar.chip.querySelector(".lab"), "1 new"); MI.latch(bar.chip, "green"); });
    at(3100, () => { bar.chip.dot.firstChild.setAttribute("data-s", "bad"); MI.tick(bar.chip.v, "2"); MI.swap(bar.chip.querySelector(".lab"), "1 failed"); MI.latch(bar.chip, "red"); });
  };

  D.E2 = (s, at) => {
    const tab = h("div", "m-tabbar");
    tab.innerHTML = '<span class="m-tabitem"><span class="fav"></span><span class="tt">(2) worklens · work board</span></span>';
    s.appendChild(tab);
    const p = MI.pad(s);
    p.style.opacity = ".25";
    p.append(h("div", "m-bar"), h("div", "m-bar"));
    const bar = B.hud(s, '<span class="type">store</span> Board preferences saved', 2);
    bar.chip.dot.replaceChildren(MI.mark("bad"));
    at(800, () => {
      p.style.transition = "opacity .3s";
      p.style.opacity = "1";
      const line = h("span", null, '<b style="color:var(--ink);font-weight:600">While you were away:</b> 1 answer, 1 failed run · <u>Show</u>');
      const old = bar.ticker.firstChild;
      bar.ticker.appendChild(line);
      if (!MI.still(s)) {
        old.animate([{ transform: "none", opacity: 1 }, { transform: "translateY(-100%)", opacity: 0 }], { duration: 200, fill: "forwards" });
        line.animate([{ transform: "translateY(100%)", opacity: 0 }, { transform: "none", opacity: 1 }], { duration: 260, easing: MI.EASE });
      }
      setTimeout(() => old.remove(), 220);
      MI.latch(bar.ticker, "accent", "m-wash");
    });
  };

  const dockRow = (state, label, detail, action, fill) => {
    const r = h("div", "m-dockrow");
    r.mk = MI.mark(state);
    r.lab = h("div", "m-grow", `<div class="m-small m-strong m-clip">${label}</div><div class="m-small m-muted m-clip d">${detail}</div>`);
    r.d = r.lab.querySelector(".d");
    r.act = MI.btn(action, fill ? "fill" : "");
    r.append(r.mk, r.lab, r.act);
    return r;
  };
  const dock = (s) => {
    const d = h("div", "m-dock");
    d.innerHTML = '<div class="m-row m-dockhead"><span class="m-strong m-grow">Your requests</span></div>';
    s.appendChild(d);
    return d;
  };

  D.E3 = (s, at) => {
    const d = dock(s);
    const r = dockRow("flight", "T-3 · Whats this accomplish?", "Explainer answering · 0:41", "Watch");
    const r2 = dockRow("idle", "Get Status", "2 of 2 replied", "Open");
    d.append(r, r2);
    MI.count(at, r.d, 0, 41, 43, 600, (n) => `Explainer answering · ${MI.elapsed(n)}`);
    at(1900, () => {
      MI.set(r.mk, "ok");
      MI.swap(r.d, "Answered · new");
      MI.echo(at, r.act, "Read answer", 0);
      r.act.classList.add("hot");
    });
  };

  D.E4 = (s, at) => {
    const d = dock(s);
    const clear = MI.btn("Clear finished");
    d.querySelector(".m-dockhead").appendChild(clear);
    const rows = [
      dockRow("idle", "Critique · Accept all", "chrome-validator replied", "Open"),
      dockRow("idle", "Performance test · Run slip", "Fast", "Open"),
      dockRow("flight", "Get Status", "Waiting for 1 agent · 0:12", "Watch"),
    ];
    d.append(...rows);
    at(800, () => {
      MI.press(s, clear);
      const gone = rows.slice(0, 2);
      if (!MI.still(s)) gone.forEach((r) => r.animate([{ opacity: 1, transform: "none" }, { opacity: 0, transform: "translateX(12px)" }], { duration: 180, fill: "forwards" }));
      setTimeout(() => { MI.flip(s, [rows[2]], () => gone.forEach((r) => r.remove()), 260); }, MI.still(s) ? 0 : 190);
      MI.echo(at, clear, 'Cleared 2 · <u>Undo</u>', 0);
      clear.classList.add("hot");
    });
    at(2600, () => {
      MI.press(s, clear);
      MI.flip(s, [rows[2]], () => { d.insertBefore(rows[0], rows[2]); d.insertBefore(rows[1], rows[2]); }, 260);
      rows.slice(0, 2).forEach((r) => { r.getAnimations().forEach((a) => a.cancel()); B.enter(s, r, 0); MI.latch(r, "accent", "m-wash"); });
      MI.echo(at, clear, "Restored 2", 1400, "Clear finished");
      clear.classList.remove("hot");
    });
  };

  D.E5 = (s, at) => {
    const d = dock(s);
    const r = dockRow("bad", "Performance test · Critique slip", '<span style="color:var(--red)">Not reachable · 6 min ago</span>', "Try again", true);
    d.appendChild(r);
    at(800, () => {
      MI.press(s, r.act);
      MI.set(r.mk, "flight");
      MI.swap(r.d, "Trying again · 0:00");
      r.act.classList.remove("fill");
      MI.echo(at, r.act, "Cancel", 0);
    });
    MI.count(at, r.d, 1400, 1, 2, 800, (n) => `Trying again · ${MI.elapsed(n)}`);
    at(3200, () => { MI.set(r.mk, "ok"); MI.swap(r.d, "Fast · just now"); MI.echo(at, r.act, "See results", 0); });
  };

  // ---- HUD ------------------------------------------------------------------
  D.F1 = (s, at) => {
    const p = MI.pad(s);
    p.style.opacity = ".3";
    p.append(h("div", "m-bar"), h("div", "m-bar"));
    const bar = B.hud(s, '<span class="m-mono m-muted">23:05:51</span><span class="type">store</span> Critique queued for the next agent', 0);
    bar.chip.remove();
    const roll = (html) => {
      const old = bar.ticker.firstChild;
      const n = h("span", null, html);
      bar.ticker.appendChild(n);
      if (!MI.still(s)) {
        old.animate([{ transform: "none", opacity: 1 }, { transform: "translateY(-100%)", opacity: 0 }], { duration: 160, fill: "forwards" });
        n.animate([{ transform: "translateY(100%)", opacity: 0 }, { transform: "none", opacity: 1 }], { duration: 220, easing: MI.EASE });
      }
      setTimeout(() => old.remove(), 170);
    };
    at(700, () => roll('<span class="m-mono m-muted">23:05:58</span><span class="type">board.run.started</span> Performance test on Critique slip'));
    at(1500, () => roll('<span class="m-mono m-muted">23:06:01</span><span class="type warn">board.run.settled</span> <span class="warn">Not reachable</span>'));
    at(2500, () => roll('<span class="m-mono m-muted">23:06:09</span><span class="type">board.critique.created</span> Critique queued'));
  };

  const logRow = (t, k, txt, cls = "") => h("div", `m-logrow ${cls}`.trim(), `<span class="t">${t}</span><span class="k">${k}</span><span class="m-clip">${txt}</span>`);

  D.F2 = (s, at) => {
    const box = h("div", "m-hudbox");
    const log = h("div", "m-log");
    ["23:00:10", "23:02:27", "23:02:27", "23:05:20"].forEach((t, i) => log.appendChild(logRow(t, ["board.status.created", "board.run.started", "board.run.settled", "board.run.started"][i], ["Get Status requested", "Performance test started", "Not reachable", "Performance test started"][i])));
    const head = h("div", "m-row m-hudhead");
    const follow = MI.btn("Follow");
    head.append(h("span", "m-strong m-grow", "Activity"), follow);
    const pill = h("span", "m-pillnew m-jump", 'Jump to latest · <span class="v">0</span> new');
    pill.style.visibility = "hidden";
    box.append(head, log, pill);
    s.appendChild(box);
    at(500, () => { MI.swap(follow.querySelector(".lab"), "Follow off"); });
    [900, 1500, 1900].forEach((t, i) => at(t, () => {
      pill.style.visibility = "";
      if (i === 0) B.enter(s, pill, 6);
      MI.tick(pill.querySelector(".v"), String(i + 1));
    }));
    at(3000, () => {
      MI.press(s, pill);
      pill.style.visibility = "hidden";
      const fresh = [logRow("23:06:01", "board.run.settled", "Not reachable"), logRow("23:06:09", "board.critique.created", "Critique queued"), logRow("23:06:12", "board.tasks.created", "board added 1 task(s)")];
      MI.flip(s, [...log.children], () => { fresh.forEach((r) => log.appendChild(r)); while (log.children.length > 4) log.firstChild.remove(); }, 360);
      fresh.forEach((r) => MI.latch(r, "accent", "m-wash"));
      MI.swap(follow.querySelector(".lab"), "Follow");
    });
  };

  D.F3 = (s, at) => {
    const box = h("div", "m-hudbox");
    const log = h("div", "m-log");
    log.append(logRow("23:06:01", "worker.turn", "hosted/reviewer started a turn"), logRow("23:06:02", "worker.tool", "read assets/board/board.js"));
    const tray = h("div", "m-traylabel", "Live text · not final");
    const live = h("div", "m-logrow live", '<span class="t">23:06:04</span><span class="k">text</span><span class="m-clip tx"></span>');
    box.append(log, tray, live);
    s.appendChild(box);
    const tx = live.querySelector(".tx");
    const end = MI.type(at, tx, "The capture strip times each screen once; T-3 needs the per-URL call.", 300, 24);
    at(end + 300, () => {
      live.style.borderInlineStartStyle = "solid";
      live.classList.add("settling");
      MI.swap(live.querySelector(".k"), "worker.reply");
      live.querySelector(".k").style.color = "var(--accent)";
      live.style.color = "var(--ink)";
    });
    at(end + 900, () => {
      MI.flip(s, [live], () => { log.appendChild(live); live.classList.remove("live"); tray.style.visibility = "hidden"; }, 440);
      MI.latch(live, "accent", "m-wash");
    });
  };

  D.F4 = (s, at) => {
    const box = h("div", "m-hudbox");
    const head = h("div", "m-row m-hudhead");
    const pause = MI.btn("Pause");
    head.append(h("span", "m-strong m-grow", "Activity"), pause);
    const log = h("div", "m-log");
    log.append(logRow("23:06:01", "board.run.settled", "Not reachable"), logRow("23:06:09", "board.critique.created", "Critique queued"));
    box.append(head, log);
    s.appendChild(box);
    at(500, () => { MI.press(s, pause); pause.classList.add("is-on"); MI.swap(pause.querySelector(".lab"), 'Paused · <span class="v">0</span> held'); });
    [1300, 1800, 2200, 2900].forEach((t, i) => at(t, () => MI.tick(pause.querySelector(".v"), String(i + 1))));
    at(3800, () => {
      MI.press(s, pause);
      pause.classList.remove("is-on");
      MI.swap(pause.querySelector(".lab"), "Pause");
      const fresh = [0, 1, 2, 3].map((i) => logRow(`23:06:1${i}`, "worker.tool", ["read hud.js", "read requests.js", "ran pnpm lint", "ran pnpm test"][i]));
      fresh.forEach((r) => { log.appendChild(r); MI.latch(r, "accent", "m-wash"); });
      while (log.children.length > 4) log.firstChild.remove();
    });
  };

  D.F5 = (s, at) => {
    const page = MI.pad(s);
    page.style.justifyContent = "flex-start";
    page.append(h("div", "m-bar"), h("div", "m-bar"));
    const box = h("div", "m-hudbox m-hudsnap");
    box.innerHTML = '<div class="m-grip"></div><div class="m-row m-hudhead"><span class="m-strong m-grow">Activity</span><span class="m-mono m-muted hh">⅓ window</span></div>';
    const log = h("div", "m-log");
    for (let i = 0; i < 6; i++) log.appendChild(logRow(`23:06:0${i}`, "worker.tool", "read assets/board/board.js"));
    box.appendChild(log);
    s.appendChild(box);
    box.style.height = "36%";
    box.style.transition = MI.still(s) ? "none" : "height .44s cubic-bezier(.16,1,.3,1)";
    const grip = box.querySelector(".m-grip");
    at(800, () => { MI.press(s, grip); box.style.height = "72%"; MI.tick(box.querySelector(".hh"), "⅔ window"); });
    at(2600, () => { MI.press(s, grip); box.style.height = "36%"; MI.tick(box.querySelector(".hh"), "⅓ window", "down"); });
  };
})();
