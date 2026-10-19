/* worklens example · the walkthrough: one task, start to finish, on a 1000 × 510 mock board.
   Runtime contract: see assets/runtime/mi-walk.js. */
(() => {
  const { h, b: B } = MI;
  const W = (MI.walk = { width: 1000, height: 510 });
  W.intro = "Press Play. The board starts quiet: nothing moves until something happens.";
  W.steps = [
    { t: "An agent claims T-5", ids: ["B1", "A2"],
      say: "sandbox-seed starts T-5. The card glides to In progress and says who moved it; the In progress tile ticks and names the change." },
    { t: "You run the performance test", ids: ["C5", "C8"],
      say: "You press Run on a capture. A ghost of the request travels to Your requests, whose count ticks. The bar shows a dashed ring: running, not final." },
    { t: "The run settles", ids: ["C8", "E1"],
      say: "The dashed ring closes into a green dot: Fast · just now. The requests chip latches green and says 1 new." },
    { t: "The agent asks for acceptance", ids: ["B1", "A2"],
      say: "sandbox-seed marks T-5 ready. The card glides to Awaiting acceptance; the gate pulse lights; the tile ticks 0 → 1." },
    { t: "You accept", ids: ["B6", "A3"],
      say: "The decision is recorded first (Accepted · you are the reviewer), then the burst. The card glides to Complete and the completion bar grows from where it was." },
    { t: "The connection drops and comes back", ids: ["A1"],
      say: "The light goes red, then a dashed amber ring while retrying. Back online, it says how long it was away and how much it caught up." },
  ];

  // el is the object build() returns; the step functions receive it.
  let el = {};
  W.build = (stage) => {
    W.stage = stage;
    el = {};
    const wrap = h("div", "w-board");
    const hero = h("div", "w-hero");
    hero.innerHTML = '<div><div class="m-eyebrow">LOCAL WORKSPACE</div><div class="w-h1">worklens</div><div class="m-small m-muted">0 sprints · 8 tasks · tasks live on this board</div></div>';
    const conn = h("div", "w-conn");
    el.connSlot = h("span", "m-row");
    el.live = B.live();
    el.connSlot.appendChild(el.live);
    el.connLab = h("span", null, "Live · push");
    const cr = h("div", "m-row");
    cr.append(el.connSlot, el.connLab);
    el.checked = h("div", "m-mono m-muted", "Checked 11:10:42 PM");
    conn.append(cr, el.checked);
    hero.appendChild(conn);

    const tiles = h("div", "w-tiles");
    el.tDone = B.tile("Reviewed complete", "1/8", "Accepted by a person", 0.125);
    el.tProg = B.tile("In progress", "1", "sandbox-seed");
    el.tWait = B.tile("Awaiting acceptance", "0", "Waiting on a human to accept");
    el.tBlock = B.tile("Blocked", "1", "No update for 10+ min");
    el.tWait.querySelector(".lab").prepend((el.gate = h("span", "m-gate")));
    el.gate.style.visibility = "hidden";
    tiles.append(el.tDone, el.tProg, el.tWait, el.tBlock);
    el.tDone.p.style.transition = "transform .44s cubic-bezier(.16,1,.3,1)";

    const lower = h("div", "w-lower");
    const cols = h("div", "m-cols w-cols");
    el.cTodo = B.col("To do", "2");
    el.cProg = B.col("In progress", "1", "go");
    el.cWait = B.col("Awaiting acceptance", "0", "warn");
    el.cDone = B.col("Complete", "1", "ok");
    el.card5 = B.card("T-5", "Requests dock cancel", "Ready", "ok", "Unclaimed");
    el.cTodo.body.append(el.card5, B.card("T-6", "Try it", "Ready", "ok", "Unclaimed"));
    el.cProg.body.append(B.card("T-3", "Capture strip performance test", "In progress", "go", "sandbox-seed"));
    el.cWait.body.append((el.noWait = h("div", "w-none", "No tasks")));
    el.cDone.body.append(B.card("T-2", "Accept all as a right drawer", "Complete", "ok", "sandbox-seed"));
    cols.append(el.cTodo, el.cProg, el.cWait, el.cDone);

    el.cap = B.capture("accept-all-as-a-right-drawer", "Accept all as a right drawer");
    el.cap.classList.add("w-cap");
    el.run = B.cmd("Perform performance test", "idle", "Fast · 1 h ago");
    el.crit = h("div", "m-cmdbar", `<span class="m-grow">Critique this screen</span><span class="res"><span class="mk-label">1 open</span></span>${MI.arrow}`);
    el.cap.append(el.run, el.crit);
    lower.append(cols, el.cap);

    wrap.append(hero, tiles, lower);
    stage.appendChild(wrap);
    el.hud = B.hud(stage, '<span class="m-mono m-muted">23:05:51</span><span class="type">store</span> Critique queued for the next agent', 0);
    el.hud.chip.dot.replaceChildren(MI.mark("idle"));
    MI.set(el.run.mk, "ok");
    return el;
  };

  // `sync` is true while the runtime fast-forwards earlier steps (see the runtime's ctx.sync).
  let sync = false;
  const tickerSay = (html) => {
    const t = el.hud.ticker;
    [...t.children].slice(0, -1).forEach((c) => c.remove());
    const old = t.firstChild;
    const n = h("span", null, html);
    t.appendChild(n);
    if (sync) { old?.remove(); return; }
    if (!MI.reduced()) {
      old?.animate([{ transform: "none", opacity: 1 }, { transform: "translateY(-100%)", opacity: 0 }], { duration: 160, fill: "forwards" });
      n.animate([{ transform: "translateY(100%)", opacity: 0 }, { transform: "none", opacity: 1 }], { duration: 220, easing: MI.EASE });
    }
    setTimeout(() => old?.remove(), 170);
  };
  const move = (card, toCol, fromCol, pill, pcls, hue, foot) => {
    const sibs = [...fromCol.body.children, ...toCol.body.children].filter((c) => c !== card && c.classList.contains("m-card"));
    MI.flip(W.stage, [card, ...sibs], () => {
      toCol.body.prepend(card);
      if (toCol === el.cWait) el.noWait.remove();
    });
    card.pill.className = `m-pill ${pcls}`;
    card.pill.textContent = pill;
    MI.latch(card, hue);
    MI.swap(card.foot, foot);
  };
  const press = (e) => MI.press(W.stage, e);


  W.run = [
    (el, ctx) => { const { at, stage } = ctx; sync = ctx.sync; // 1 · claim
      at(300, () => {
        move(el.card5, el.cProg, el.cTodo, "In progress", "go", "accent", 'moved by <b style="color:var(--ink);font-weight:600">sandbox-seed</b> · just now');
        MI.tick(el.cTodo.n, "1", "down"); MI.tick(el.cProg.n, "2");
        MI.tick(el.tProg.v, "2"); MI.latch(el.tProg, "accent");
        MI.swap(el.tProg.f, '<b style="color:var(--ink);font-weight:600">+1</b> · T-5 by sandbox-seed');
        tickerSay('<span class="m-mono m-muted">23:06:02</span><span class="type">status:in_progress</span> sandbox-seed · T-5 todo → in_progress');
      });
      at(3300, () => { MI.swap(el.card5.foot, "sandbox-seed"); MI.swap(el.tProg.f, "sandbox-seed"); });
      return 3600;
    },
    (el, ctx) => { const { at, stage } = ctx; sync = ctx.sync; // 2 · run
      at(300, () => press(el.run));
      at(420, () => {
        MI.ghost(stage, el.run, el.hud.chip, "Performance test");
        MI.set(el.run.mk, "flight");
        el.run.lab.className = "mk-label";
        MI.swap(el.run.lab, "Running · 0:00");
        tickerSay('<span class="m-mono m-muted">23:06:10</span><span class="type">board.run.started</span> Performance test on Accept all');
      });
      at(1000, () => { el.hud.chip.dot.replaceChildren(MI.mark("flight")); MI.tick(el.hud.chip.v, "1"); MI.latch(el.hud.chip, "accent"); });
      MI.count(at, el.run.lab, 1400, 1, 2, 900, (n) => `Running · ${MI.elapsed(n)}`);
      return 3200;
    },
    (el, ctx) => { const { at, stage } = ctx; sync = ctx.sync; // 3 · settle
      at(300, () => {
        MI.set(el.run.mk, "ok"); el.run.lab.className = "mk-label ink"; MI.tick(el.run.lab, "Fast · just now");
        el.hud.chip.dot.firstChild.setAttribute("data-s", "ok");
        MI.swap(el.hud.chip.querySelector(".lab"), "1 new"); MI.latch(el.hud.chip, "green");
        tickerSay('<span class="m-mono m-muted">23:06:13</span><span class="type">board.run.settled</span> Performance test: Fast');
      });
      return 2800;
    },
    (el, ctx) => { const { at, stage } = ctx; sync = ctx.sync; // 4 · review
      at(300, () => {
        move(el.card5, el.cWait, el.cProg, "In review", "warn", "amber", 'moved by <b style="color:var(--ink);font-weight:600">sandbox-seed</b> · 2 proofs');
        MI.tick(el.cProg.n, "1", "down"); MI.tick(el.cWait.n, "1");
        MI.tick(el.tProg.v, "1", "down");
        MI.tick(el.tWait.v, "1"); MI.latch(el.tWait, "amber");
        el.gate.style.visibility = "";
        if (!MI.reduced()) el.gate.animate([{ boxShadow: "0 0 0 0 #ffc4008c" }, { boxShadow: "0 0 0 7px #ffc40000" }], { duration: 1600, iterations: 2 });
        tickerSay('<span class="m-mono m-muted">23:07:40</span><span class="type">status:in_review</span> sandbox-seed · T-5 ready for acceptance');
      });
      at(3300, () => MI.swap(el.card5.foot, "sandbox-seed · 2 proofs"));
      return 3600;
    },
    (el, ctx) => { const { at, stage } = ctx; sync = ctx.sync; // 5 · accept
      let btn;
      at(200, () => {
        btn = MI.btn("Accept task", "fill");
        btn.classList.add("w-accept");
        el.card5.appendChild(btn);
        B.enter(stage, btn, 4);
      });
      at(900, () => press(btn));
      at(1050, () => {
        btn.classList.remove("fill");
        MI.echo(at, btn, "Accepted · you are the reviewer", 0);
        MI.burst(stage, btn);
      });
      at(2300, () => {
        btn.remove();
        move(el.card5, el.cDone, el.cWait, "Complete", "ok", "green", "accepted by you · just now");
        el.cWait.body.appendChild(el.noWait);
        MI.tick(el.cWait.n, "0", "down"); MI.tick(el.cDone.n, "2");
        MI.tick(el.tWait.v, "0", "down"); el.gate.style.visibility = "hidden";
        MI.tick(el.tDone.v, "2/8"); el.tDone.p.style.setProperty("--w", "0.25"); MI.latch(el.tDone, "green");
        tickerSay('<span class="m-mono m-muted">23:08:02</span><span class="type">status:done</span> board · T-5 in_review → done');
      });
      return 4800;
    },
    (el, ctx) => { const { at, stage } = ctx; sync = ctx.sync; // 6 · offline and back
      at(300, () => {
        el.connSlot.replaceChildren(h("span", "m-conn-dot bad"));
        el.connLab.style.color = "var(--red)";
        MI.swap(el.connLab, "Connection lost");
      });
      at(1500, () => { el.connSlot.replaceChildren(MI.mark("retry")); el.connLab.style.color = "var(--muted)"; MI.swap(el.connLab, "Reconnecting…"); });
      at(2900, () => {
        const live = B.live();
        el.connSlot.replaceChildren(live);
        B.hop(stage, live);
        el.connLab.style.color = "var(--ink)";
        MI.swap(el.connLab, "Back · offline 0:42 · 3 changes caught up");
        MI.tick(el.checked, "Checked 11:11:24 PM");
        MI.tick(el.tBlock.v, "0", "down"); MI.latch(el.tBlock, "green");
      });
      at(6400, () => { el.connLab.style.color = ""; MI.swap(el.connLab, "Live · push"); });
      return 6800;
    },
  ];
})();
