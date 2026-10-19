/* micro-interactions runtime · the walkthrough player. Do not edit per project.
   The project's walk.js sets, before this file loads:
     MI.walk = {
       width: 1000, height: 510,                 // the mock app's own size; it is scaled to fit
       intro: "Press Play. …",                   // caption before step 1
       steps: [{ t: "Step title", ids: ["B1"], say: "What happens and why" }, …],
       build(stage, h) { …; return el },         // draws the mock app into `stage`, returns named parts
       run: [(el, ctx) => msUntilDone, …],       // one function per step; schedule with ctx.at(ms, fn)
     };
   ctx = { at, stage, sync }. While a step is fast-forwarded (a jump), ctx.sync is true, ctx.at runs
   its function at once and MI.reduced() is true, so steps replay without motion in order. */
(() => {
  const W = window.MI.walk;
  if (!W) return;
  const { h } = MI;
  const $ = (id) => document.getElementById(id);
  const frame = $("walk-frame");
  const stage = $("walk-stage");
  stage.style.width = `${W.width}px`;
  stage.style.height = `${W.height}px`;

  const timers = [];
  const ctx = { stage, sync: false };
  ctx.at = (ms, f) => (ctx.sync ? f() : timers.push(setTimeout(f, ms)));
  const clear = () => { while (timers.length) clearTimeout(timers.pop()); };
  let el = {};
  const build = () => {
    stage.getAnimations?.({ subtree: true }).forEach((a) => a.cancel());
    stage.replaceChildren();
    el = W.build(stage, h) || {};
  };

  const list = $("walk-steps");
  const caption = $("walk-caption");
  const playBtn = $("walk-play");
  let step = -1;
  let playing = false;
  let chain = null;
  W.steps.forEach((s, i) => {
    const li = h("li");
    const b = h("button", null, `<span class="n">${i + 1}</span><span class="t">${s.t}</span><span class="ids">${(s.ids || []).join(" · ")}</span>`);
    b.type = "button";
    b.addEventListener("click", () => { stop(); jump(i); });
    li.appendChild(b);
    list.appendChild(li);
  });
  const mark = () => [...list.children].forEach((li, i) => {
    if (i === step) li.setAttribute("aria-current", "step");
    else li.removeAttribute("aria-current");
    li.classList.toggle("done", i < step);
  });
  const setPlay = (on) => {
    playing = on;
    playBtn.querySelector("use").setAttribute("href", on ? "#i-pause" : "#i-play");
    playBtn.querySelector("span").textContent = on ? "Pause" : step >= W.steps.length - 1 ? "Play again" : "Play";
  };
  const stop = () => { clearTimeout(chain); setPlay(false); };
  const doStep = (i) => {
    step = i;
    mark();
    caption.textContent = `${i + 1} of ${W.steps.length} · ${W.steps[i].say}`;
    return W.run[i](el, ctx) || 2000;
  };
  // A jump rebuilds the app and fast-forwards earlier steps without motion, so every step starts honest.
  const jump = (target) => {
    clear();
    build();
    const keep = MI.reduced;
    MI.reduced = () => true;
    ctx.sync = true;
    try {
      for (let i = 0; i < target; i++) W.run[i](el, ctx);
    } finally {
      ctx.sync = false;
      MI.reduced = keep;
    }
    stage.getAnimations?.({ subtree: true }).forEach((a) => a.finish());
    stage.querySelectorAll(".m-latch,.m-wash,.m-tick").forEach((e) => e.classList.remove("m-latch", "m-wash", "up", "down"));
    return doStep(target);
  };
  const reset = () => { clear(); build(); step = -1; mark(); };
  const advance = (i) => (i === step + 1 ? doStep(i) : jump(i));
  const next = () => {
    if (step >= W.steps.length - 1) { setPlay(false); return; }
    const ms = advance(step + 1);
    if (playing) chain = setTimeout(next, ms + 500);
  };
  playBtn.addEventListener("click", () => {
    if (playing) { stop(); return; }
    if (step >= W.steps.length - 1) reset();
    setPlay(true);
    next();
  });
  $("walk-step").addEventListener("click", () => {
    stop();
    if (step >= W.steps.length - 1) reset();
    advance(step + 1);
    setPlay(false);
  });
  $("walk-restart").addEventListener("click", () => {
    stop();
    reset();
    caption.textContent = W.intro || "Press Play.";
    setPlay(false);
  });
  caption.textContent = W.intro || "Press Play.";

  const fit = () => {
    const k = Math.min(1, frame.clientWidth / W.width);
    stage.style.transform = `scale(${k})`;
    frame.style.height = `${W.height * k}px`;
  };
  new ResizeObserver(fit).observe(frame);
  build();
  fit();
})();
