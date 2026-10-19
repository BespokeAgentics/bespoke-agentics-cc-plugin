/* worklens example · project builders, the five motion demos, Glance and Tasks demos. */
(() => {
  const { h } = MI;
  const B = MI.b;
  // worklens shapes: a capture card's command bar, and a capture card.
  B.cmd = (title, state, label) => {
    const b = h("div", "m-cmdbar");
    b.innerHTML = `<span class="m-grow m-clip">${title}</span><span class="res"></span>${MI.arrow}`;
    const res = b.querySelector(".res");
    b.mk = MI.mark(state);
    b.lab = h("span", `mk-label${state === "bad" ? " bad" : ""}`, label);
    res.append(b.mk, b.lab);
    return b;
  };
  B.capture = (img, title) => {
    const c = h("div", "m-capture");
    c.innerHTML = `<img class="m-shot" src="${MI.img(img)}" alt="">${title ? `<div class="m-capbody"><div class="m-title m-clip">${title}</div></div>` : ""}`;
    return c;
  };

  // ---- The five motions -----------------------------------------------------
  const P = MI.primDemos;
  P.latch = (s, at) => {
    const p = MI.pad(s);
    const c = B.card("T-3", "Capture strip performance test", "In progress", "go", "sandbox-seed");
    p.appendChild(c);
    at(700, () => { c.pill.className = "m-pill warn"; c.pill.textContent = "In review"; MI.latch(c, "amber"); });
  };
  P.tick = (s, at) => {
    const p = MI.pad(s);
    const t = B.tile("Awaiting acceptance", "0", "Waiting on a human to accept");
    p.appendChild(t);
    at(700, () => MI.tick(t.v, "1", "up"));
    at(2400, () => MI.tick(t.v, "0", "down"));
  };
  P.settle = (s, at) => {
    const p = MI.pad(s);
    const box = h("div", "m-capture");
    const b = B.cmd("Performance test", "flight", "Running · 0:00");
    b.style.borderTop = "0";
    box.appendChild(b);
    p.appendChild(box);
    MI.count(at, b.lab, 0, 0, 2, 600, (n) => `Running · ${MI.elapsed(n)}`);
    at(1900, () => { MI.set(b.mk, "ok"); b.lab.className = "mk-label ink"; MI.tick(b.lab, "Fast · just now"); });
  };
  P.handoff = (s, at) => {
    const p = MI.pad(s);
    p.style.justifyContent = "flex-start";
    p.style.alignItems = "flex-end";
    p.style.paddingTop = "20px";
    const q = MI.btn("Queue critique", "fill");
    p.appendChild(q);
    const bar = B.hud(s, "");
    at(600, () => { MI.press(s, q); MI.ghost(s, q, bar.chip, "Critique"); });
    at(1150, () => { bar.chip.dot.replaceChildren(MI.mark("flight")); MI.tick(bar.chip.v, "1"); MI.latch(bar.chip, "accent"); });
  };
  P.echo = (s, at) => {
    const p = MI.pad(s);
    p.style.alignItems = "center";
    const b = MI.btn("Refresh now");
    p.appendChild(b);
    at(500, () => { MI.press(s, b); MI.echo(at, b, "No changes", 1500); });
    at(2700, () => { MI.press(s, b); MI.echo(at, b, "2 changes", 1500); });
  };

  // ---- Glance ---------------------------------------------------------------
  const D = MI.demos;
  const liveRow = (label = "Live · push") => {
    const r = h("div", "m-row");
    r.live = B.live();
    r.lab = h("span", null, label);
    r.append(r.live, r.lab);
    return r;
  };

  D.A1 = (s, at) => {
    const p = MI.pad(s);
    const conn = h("div", "m-row");
    const slot = h("span", "m-row");
    slot.appendChild(h("span", "m-conn-dot bad"));
    const lab = h("span", "m-strong", "Connection lost");
    lab.style.color = "var(--red)";
    conn.append(slot, lab);
    const checked = h("div", "m-mono m-muted", "Checked 11:10:42 PM");
    const tiles = h("div", "m-cols");
    tiles.style.gridTemplateColumns = "1fr 1fr";
    const t1 = B.tile("In progress", "1", "sandbox-seed");
    const t2 = B.tile("Awaiting", "0", "Waiting on a human");
    tiles.append(t1, t2);
    p.append(conn, checked, tiles);
    at(900, () => { slot.replaceChildren(MI.mark("retry")); lab.style.color = "var(--muted)"; MI.swap(lab, "Reconnecting…"); });
    at(2200, () => {
      const live = B.live();
      slot.replaceChildren(live);
      B.hop(s, live);
      lab.style.color = "var(--ink)";
      MI.swap(lab, "Back · offline 0:42 · 3 changes caught up");
      MI.tick(checked, "Checked 11:11:24 PM");
      MI.tick(t1.v, "2"); MI.latch(t1, "accent");
      MI.tick(t2.v, "1"); MI.latch(t2, "amber");
    });
    at(6200, () => { lab.style.color = ""; lab.classList.remove("m-strong"); MI.swap(lab, "Live · push"); });
  };

  D.A2 = (s, at) => {
    const p = MI.pad(s);
    const t = B.tile("In progress", "1", "sandbox-seed");
    p.appendChild(t);
    at(700, () => { MI.tick(t.v, "2"); MI.latch(t, "accent"); MI.swap(t.f, '<b style="color:var(--ink);font-weight:600">+1</b> · T-5 by sandbox-seed'); });
    at(3300, () => MI.swap(t.f, "sandbox-seed, chrome-validator"));
  };

  D.A3 = (s, at) => {
    const p = MI.pad(s);
    const t = B.tile("Reviewed complete", "1/8", "Accepted by a person", 0.125);
    p.appendChild(t);
    t.p.style.transition = MI.still(s) ? "none" : "transform .44s cubic-bezier(.16,1,.3,1)";
    at(700, () => { MI.tick(t.v, "2/8"); t.p.style.setProperty("--w", "0.25"); });
    at(2300, () => { MI.tick(t.v, "3/8"); t.p.style.setProperty("--w", "0.375"); });
  };

  D.A4 = (s, at) => {
    const p = MI.pad(s);
    const row = h("div", "m-cols");
    row.style.gridTemplateColumns = "1fr 1fr";
    const t1 = B.tile("In progress", "1", "sandbox-seed");
    const t2 = B.tile("Blocked", "1", "No update for 10+ min");
    row.append(t1, t2);
    const filt = h("div", "m-row m-small");
    filt.innerHTML = '<span class="m-muted">State</span>';
    const sel = h("span", "m-btn", "All states");
    filt.appendChild(sel);
    const col = B.col("Blocked", "1", "bad");
    col.body.appendChild(B.card("T-4", "Inspector model picker", "Blocked", "bad"));
    col.style.opacity = ".3";
    col.style.transition = MI.still(s) ? "none" : "opacity .24s";
    p.append(row, filt, col);
    at(700, () => { MI.press(s, t2); t2.style.borderColor = "var(--accent)"; });
    at(950, () => { MI.swap(sel, "Blocked"); col.style.opacity = "1"; MI.latch(col.head, "red", "m-wash"); });
  };

  D.A5 = (s, at) => {
    const p = MI.pad(s);
    p.style.alignItems = "flex-end";
    const live = liveRow();
    const ck = h("div", "m-mono m-muted", "Checked 11:10:42 PM");
    const b = h("span", "m-link", "Refresh now");
    p.append(live, ck, b);
    at(600, () => { MI.press(s, b); MI.tick(ck, "Checked 11:10:58 PM"); MI.echo(at, b, "No changes", 1600); });
    at(3000, () => { MI.press(s, b); MI.tick(ck, "Checked 11:11:20 PM"); MI.echo(at, b, "2 changes", 1600); });
  };

  D.A6 = (s, at) => {
    const p = MI.pad(s);
    p.style.alignItems = "flex-end";
    const live = liveRow();
    const ck = h("div", "m-mono m-muted");
    const t = h("span", null, "Checked 11:10:42 PM");
    const ago = h("span");
    ck.append(t, ago);
    ck.style.transition = "color .4s";
    p.append(live, ck);
    at(1400, () => { ago.textContent = " · 30 s ago"; ck.style.color = "var(--amber)"; });
    at(2400, () => { ago.textContent = " · 40 s ago"; });
    at(3400, () => { ago.textContent = " · 50 s ago"; });
    at(4400, () => { ck.style.color = ""; ago.textContent = ""; MI.tick(t, "Checked 11:11:36 PM"); });
  };

  // ---- Tasks ----------------------------------------------------------------
  D.B1 = (s, at) => {
    const p = MI.pad(s);
    const cols = h("div", "m-cols");
    cols.style.gridTemplateColumns = "1fr 1fr";
    const a = B.col("To do", "2");
    const b = B.col("In progress", "0", "go");
    const c1 = B.card("T-5", "Requests dock cancel", "Ready", "ok", "Unclaimed");
    const c2 = B.card("T-6", "Try it", "Ready", "ok", "Unclaimed");
    a.body.append(c1, c2);
    cols.append(a, b);
    p.appendChild(cols);
    at(700, () => {
      MI.flip(s, [c1, c2], () => b.body.appendChild(c1));
      c1.pill.className = "m-pill go";
      c1.pill.textContent = "In progress";
      MI.tick(a.n, "1", "down");
      MI.tick(b.n, "1");
      MI.latch(c1, "accent");
      MI.swap(c1.foot, 'moved by <b style="color:var(--ink);font-weight:600">sandbox-seed</b> · just now');
    });
    at(3600, () => MI.swap(c1.foot, "sandbox-seed"));
  };

  const listRow = (id, title, extra = "") => {
    const r = h("div", "m-listrow");
    r.innerHTML = `<span class="m-mono m-muted">${id}</span><span class="m-clip m-grow t">${title}</span>${extra}`;
    r.t = r.querySelector(".t");
    return r;
  };

  D.B2 = (s, at) => {
    const p = MI.pad(s);
    const f = h("div", "m-field m-oneline", '<span class="ph">Find a task, owner, or scope…</span><span class="txt"></span>');
    const cnt = h("div", "m-mono m-muted", "8 of 8 tasks");
    const data = [["T-1", "Critique slip as a left drawer", 1], ["T-3", "Capture strip performance test", 0], ["T-2", "Accept all as a right drawer", 1], ["T-4", "Inspector model picker", 0], ["T-5", "Requests dock cancel", 0]];
    const rows = data.map(([id, t, keep]) => Object.assign(listRow(id, t), { keep }));
    const list = h("div", "m-list");
    list.append(...rows);
    p.append(f, cnt, list);
    at(450, () => { f.classList.add("focus"); f.querySelector(".ph").remove(); });
    const end = MI.type(at, f.querySelector(".txt"), "drawer", 500, 80);
    at(end + 200, () => {
      const gone = rows.filter((r) => !r.keep);
      gone.forEach((r) => B.fade(s, r, 0, 150));
      MI.tick(cnt, "2 of 8 tasks", "down");
    });
    at(end + 380, () => {
      const stay = rows.filter((r) => r.keep);
      MI.flip(s, stay, () => rows.filter((r) => !r.keep).forEach((r) => r.remove()), 320);
    });
  };

  D.B3 = (s, at) => {
    const p = MI.pad(s);
    const f = h("div", "m-field m-oneline focus", '<span class="txt"></span><span class="m-caret"></span>');
    const r1 = listRow("T-4", "Inspector model picker");
    const r2 = listRow("T-3", "Capture strip performance test");
    const r3 = listRow("T-5", "Requests dock cancel");
    const foot = h("div", "m-small m-muted m-matchnote", "");
    r2.appendChild(foot);
    r2.classList.add("tall");
    const list = h("div", "m-list");
    list.append(r1, r2, r3);
    p.append(f, list);
    const end = MI.type(at, f.querySelector(".txt"), "inspector", 400, 70);
    at(end + 150, () => {
      r3.style.transition = "opacity .15s";
      r3.style.opacity = ".35";
      r1.t.innerHTML = '<mark class="m-mark">Inspector</mark> model picker';
      MI.swap(foot, 'matched scope · src/http/<mark class="m-mark">inspector</mark>.ts');
    });
  };

  D.B4 = (s, at) => {
    const p = MI.pad(s);
    const rows = [listRow("T-1", "Critique slip as a left drawer"), listRow("T-3", "Capture strip performance test"), listRow("T-4", "Inspector model picker")];
    const list = h("div", "m-list");
    list.append(...rows);
    p.appendChild(list);
    const src = rows[1];
    let d, scrim, ht, ey;
    at(700, () => MI.press(s, src));
    at(850, () => {
      scrim = h("div", "m-scrim");
      d = h("div", "m-drawer");
      d.innerHTML = '<div class="m-drawer-head"><div><div class="m-eyebrow ey">T-3 / Backlog</div><div class="m-title ht">Capture strip performance test</div></div><span class="m-btn">Close</span></div><div class="m-row"><span class="m-pill go">In progress</span><span class="m-small">sandbox-seed</span></div><div class="m-bar" style="width:86%"></div><div class="m-bar" style="width:64%"></div><div class="m-bar" style="width:74%"></div>';
      s.append(scrim, d);
      ht = d.querySelector(".ht");
      ey = d.querySelector(".ey");
      if (MI.still(s)) return;
      scrim.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 240 });
      [...d.children].slice(1).forEach((c) => c.animate([{ opacity: 0 }, { opacity: 0, offset: 0.4 }, { opacity: 1 }], { duration: 400 }));
      d.animate([{ opacity: 0, clipPath: "inset(0 0 0 100%)" }, { opacity: 1, clipPath: "inset(0 0 0 0)" }], { duration: 320, easing: MI.EASE });
      for (const [from, to] of [[src.t, ht], [src.querySelector(".m-mono"), ey]]) {
        const a = MI.rel(from, s);
        const b = MI.rel(to, s);
        to.style.transformOrigin = "0 0";
        to.animate([{ transform: `translate(${a.x - b.x}px,${a.y - b.y}px) scale(${a.h / b.h})` }, { transform: "none" }], { duration: 360, easing: MI.EASE });
      }
    });
    at(3200, () => {
      if (!d) return;
      if (MI.still(s)) { d.remove(); scrim.remove(); return; }
      const a = MI.rel(src.t, s);
      const b = MI.rel(ht, s);
      ht.animate([{ transform: "none" }, { transform: `translate(${a.x - b.x}px,${a.y - b.y}px) scale(${a.h / b.h})` }], { duration: 220, easing: "ease-in", fill: "forwards" });
      d.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 220, easing: "ease-in", fill: "forwards" }).onfinish = () => { d.remove(); };
      scrim.animate([{ opacity: 1 }, { opacity: 0 }], { duration: 150, fill: "forwards" }).onfinish = () => scrim.remove();
      MI.latch(src, "accent", "m-wash");
    });
  };

  D.B5 = (s, at) => {
    const p = MI.pad(s);
    const box = h("div", "m-panel m-box");
    const q = MI.btn("Whats this accomplish?", "fill");
    const st = h("div", "m-slot");
    const ans = h("p", "m-answer");
    box.append(q, st, ans);
    p.appendChild(box);
    let row;
    at(500, () => {
      MI.press(s, q);
      q.classList.add("wait");
      row = B.status("flight", "Explainer answering · 0:00");
      st.appendChild(row);
      B.enter(s, row, 3);
      MI.count(at, row.lab, 0, 0, 3, 900, (n) => `Explainer answering · ${MI.elapsed(n)}`);
    });
    const end = MI.type(at, ans, "Times each captured screen's responses, so a slow page shows on its card before anyone accepts the work.", 900, 22);
    at(end + 250, () => {
      B.settle(row, "ok", "Explainer answered · new");
      ans.classList.add("final");
      q.classList.remove("wait");
    });
  };

  D.B6 = (s, at) => {
    const p = MI.pad(s);
    const box = h("div", "m-panel m-box");
    const head = h("div", "m-row");
    head.innerHTML = '<span class="m-strong m-grow">Accept this work</span><span class="m-mono m-muted">T-3</span>';
    const st = B.status("warn", "Awaiting acceptance");
    const note = h("div", "m-field m-oneline", '<span class="ph">Optional note for the record</span>');
    const btn = MI.btn("Accept task", "fill");
    const r = h("div", "m-row");
    r.append(h("span", "m-grow"), btn);
    box.append(head, st, note, r);
    p.appendChild(box);
    at(700, () => {
      MI.press(s, btn);
      MI.set(st.mk, "flight");
      MI.swap(st.lab, "Saving the decision");
      btn.classList.add("wait");
    });
    at(1300, () => {
      btn.classList.remove("wait", "fill");
      MI.echo(at, btn, "Accepted · you are the reviewer", 0);
      B.settle(st, "ok", "Complete · accepted just now");
      MI.latch(box, "green");
      MI.burst(s, btn);
    });
  };

  D.B7 = (s, at) => {
    const p = MI.pad(s);
    const items = [["T-1", "Critique slip as a left drawer"], ["T-2", "Accept all as a right drawer"], ["T-6", "Try it"], ["T-7", "Approve bar at 390 px"]].map(([id, t]) => {
      const r = listRow(id, t);
      r.ck = B.check(true);
      r.prepend(r.ck);
      return r;
    });
    const list = h("div", "m-list");
    list.append(...items);
    const foot = h("div", "m-row");
    const cnt = h("span", "m-mono m-muted m-grow");
    cnt.innerHTML = '<span class="v">4</span> of 4 selected';
    const btn = MI.btn("", "fill");
    btn.querySelector(".lab").innerHTML = 'Accept <span class="v">4</span> tasks';
    foot.append(cnt, btn);
    p.append(list, foot);
    const set = (r, on, n, dir) => {
      MI.press(s, r.ck);
      r.ck.classList.toggle("on", on);
      MI.tick(cnt.querySelector(".v"), String(n), dir);
      MI.tick(btn.querySelector(".v"), String(n), dir);
    };
    at(700, () => set(items[1], false, 3, "down"));
    at(1800, () => set(items[3], false, 2, "down"));
    at(3100, () => set(items[1], true, 3, "up"));
  };

  D.B8 = (s, at) => {
    const p = MI.pad(s);
    const head = h("div", "m-row");
    const n = h("span", "m-mono m-muted", "1");
    head.append(h("span", "m-strong m-grow", "Evidence history"), n);
    const list = h("div", "m-list");
    const ev = (cmd, who) => h("div", "m-evidence", `<div class="m-mono">${cmd}</div><div class="m-small m-muted">${who}</div>`);
    const old = ev("pnpm test · 541 passed", "sandbox-seed · 03:17 PM");
    list.appendChild(old);
    p.append(head, list);
    at(900, () => {
      const fresh = ev("pnpm test:web · 49 passed", "sandbox-seed · just now");
      MI.flip(s, [old], () => list.prepend(fresh), 320);
      B.enter(s, fresh, -6);
      MI.latch(fresh, "green", "m-wash");
      MI.tick(n, "2");
    });
  };
})();
