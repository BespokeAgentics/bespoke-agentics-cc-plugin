/* <project> · the catalogue. Contract: see the header of runtime/mi-core.js and references/ideation.md.
   This line must stay first: the runtime reads window.MI. */
window.MI = window.MI || {};

// 4-6 motions: the ones that already ship first (status "ships"), then new ones.
MI.prims = [
  { id: "latch", name: "Latch", status: "ships", say: "<the question it answers, in one sentence>", spec: "<duration · distance · what survives reduced motion>" },
];

// 4-7 flows, named in the app's own words.
MI.flows = [
  { id: "<flow-id>", name: "<Flow name>", say: "<the surfaces it crosses>" },
];

// Ids are a flow letter plus a number (A1, B3), letters in flow order. Every field is required; first is optional.
MI.ideas = [
  { id: "A1", flow: "<flow-id>", prims: ["latch"], impact: 3, effort: 1, first: true,
    title: "<what the person will notice>",
    why: "<the current behavior and its cost>",
    trigger: "<the exact event>",
    moves: "<what moves, how far, how long, in the app's labels>",
    reduced: "<what stays under reduced motion; never 'nothing'>",
    where: "<function() · file>" },
];

// Build order of the first batch, shared work first: [id, why this position].
MI.firstOrder = [
  ["A1", "<why it goes first>"],
];

// Optional: rename the effort columns.
// MI.meta = { effort: { 1: "Under half a day", 2: "About a day", 3: "Several days" } };
