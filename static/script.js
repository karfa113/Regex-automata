(function () {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const PT_TO_PX = 96 / 72;   // Graphviz sizes are in points

  let current = null;         // last successful conversion
  let sim = null;             // step-through state: {result, index}
  const zoomState = {};       // {diagramId: {natural, scale, manual}}

  /* ---------- helpers ---------- */

  function el(tag, props, children) {
    const node = document.createElement(tag);
    Object.assign(node, props || {});
    (children || []).forEach((c) => node.append(c));
    return node;
  }

  async function post(url, tests) {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        regex: $("regex").value,
        tests: tests,
        dead_state: $("dead-state").checked,
      }),
    });
    let data = {};
    try { data = await res.json(); } catch (e) { /* non-JSON error page */ }
    if (!res.ok) throw new Error(data.error || "The server could not process this request.");
    return data;
  }

  function showError(msg) {
    const box = $("error");
    box.textContent = msg;
    box.hidden = !msg;
  }

  /* ---------- diagrams and zoom ---------- */

  function applyZoom(id) {
    const z = zoomState[id];
    const svg = $(id).querySelector("svg");
    if (!z || !svg) return;
    svg.style.width = Math.round(z.natural * z.scale) + "px";
    svg.style.height = "auto";
  }

  // `exact` is the Fit button: shrink as far as needed. Otherwise keep text readable
  // (never below 0.8) and let wide diagrams scroll sideways.
  function fitDiagram(id, exact) {
    const z = zoomState[id];
    const box = $(id);
    if (!z || (z.manual && !exact)) return;
    const available = box.clientWidth - 34;
    if (available <= 0) return;                      // hidden right now; fit again when shown
    z.scale = Math.min(1.3, Math.max(exact ? 0.25 : 0.8, available / z.natural));
    applyZoom(id);
  }

  function setupZoom(id) {
    const svg = $(id).querySelector("svg");
    if (!svg) return;
    const vb = (svg.getAttribute("viewBox") || "").trim().split(/\s+/).map(Number);
    const width = vb[2] || svg.getBoundingClientRect().width || 600;
    zoomState[id] = { natural: width * PT_TO_PX, scale: 1, manual: false };
    fitDiagram(id);
    applyZoom(id);
  }

  async function drawDiagram(id, part) {
    const box = $(id);
    box.textContent = "";
    if (part.svg) {
      box.innerHTML = part.svg;
      setupZoom(id);
      return;
    }
    // Graphviz is not installed on the server: draw the DOT text in the browser instead.
    box.append(el("div", { className: "note", textContent: "Drawing diagram…" }));
    try {
      if (!window.__viz) {
        await new Promise((resolve, reject) => {
          const s = document.createElement("script");
          s.src = "https://cdn.jsdelivr.net/npm/@viz-js/viz@3.2.4/lib/viz-standalone.js";
          s.onload = resolve;
          s.onerror = reject;
          document.head.append(s);
        });
        window.__viz = await window.Viz.instance();
      }
      box.textContent = "";
      const svg = window.__viz.renderSVGElement(part.dot);
      box.append(svg);
      setupZoom(id);
    } catch (e) {
      box.textContent = "";
      box.append(el("div", {
        className: "note",
        textContent: "The diagram could not be drawn. Install Graphviz on the server (see the README) or check your connection.",
      }));
    }
  }

  function highlightState(name) {
    document.querySelectorAll("#dfa-diagram g.node.active").forEach((g) => g.classList.remove("active"));
    if (!name) return;
    document.querySelectorAll("#dfa-diagram g.node").forEach((g) => {
      const t = g.querySelector("title");
      if (t && t.textContent === name) g.classList.add("active");
    });
  }

  /* ---------- tables ---------- */

  function stateLabel(row) {
    return (row.start ? "→ " : "") + row.state + (row.accept ? " *" : "");
  }

  function renderTable(table, data, infoLabel) {
    table.textContent = "";
    const head = el("tr", {}, [el("th", { textContent: "State" })]);
    data.columns.forEach((c) => head.append(el("th", { textContent: c })));
    if (infoLabel) head.append(el("th", { textContent: infoLabel }));
    table.append(el("thead", {}, [head]));

    const body = el("tbody");
    data.rows.forEach((row) => {
      const tr = el("tr", { className: row.accept ? "is-accept" : "" });
      tr.append(el("td", { className: "state", textContent: stateLabel(row) }));
      data.columns.forEach((c) => tr.append(el("td", { textContent: row.cells[c] })));
      if (infoLabel) tr.append(el("td", { className: "info", textContent: row.info }));
      body.append(tr);
    });
    table.append(body);
  }

  /* ---------- construction details ---------- */

  function renderDetails(data) {
    const nfaList = $("nfa-steps");
    nfaList.textContent = "";
    data.nfa.steps.forEach((s) => nfaList.append(el("li", { textContent: s })));

    const rounds = $("min-rounds");
    rounds.textContent = "";
    data.dfa.rounds.forEach((r) => rounds.append(el("li", { textContent: r })));

    const box = $("subset-steps");
    box.textContent = "";
    data.subset.steps.forEach((step) => {
      const ul = el("ul");
      step.moves.forEach((m) => {
        const target = m.target ? `goes to ${m.target}` : "has no transition";
        ul.append(el("li", {
          textContent: `On '${m.symbol}': move gives ${m.move}, ε-closure is ${m.closure}, so it ${target}.`,
        }));
      });
      box.append(el("div", { className: "dstep" }, [
        el("div", {}, [
          el("strong", { textContent: step.state }),
          document.createTextNode(` is ${step.nfa_states}`),
        ]),
        ul,
      ]));
    });
  }

  /* ---------- convert ---------- */

  async function convert() {
    showError("");
    resetSim();
    if (!$("regex").value.trim()) {
      showError("The regular expression is empty.");
      $("regex").focus();
      return;
    }
    try {
      const data = await post("/api/convert", []);
      current = data;

      $("output").hidden = false;
      $("flow").hidden = false;
      $("count-nfa").textContent = data.counts.nfa;
      $("count-subset").textContent = data.counts.subset;
      $("count-min").textContent = data.counts.minimal;

      $("with-concat").textContent = data.with_concat;
      $("postfix").textContent = data.postfix;
      $("alphabet").textContent = "{" + data.alphabet.join(", ") + "}";

      renderTable($("nfa-table"), data.nfa.table, null);
      renderTable($("dfa-table"), data.dfa.table, data.dfa.table.info_label);
      renderTable($("subset-table"), data.subset.table, data.subset.table.info_label);
      renderDetails(data);

      await drawDiagram("nfa-diagram", data.nfa);
      await drawDiagram("dfa-diagram", data.dfa);
      await drawDiagram("subset-diagram", data.subset);
      fitVisibleDiagrams();

      $("batch-wrap").hidden = true;
    } catch (e) {
      current = null;
      $("output").hidden = true;
      $("flow").hidden = true;
      showError(e.message);
    }
  }

  function fitVisibleDiagrams() {
    ["nfa-diagram", "dfa-diagram", "subset-diagram"].forEach((id) => {
      const z = zoomState[id];
      if (z) { z.manual = false; fitDiagram(id); }
    });
  }

  /* ---------- tabs ---------- */

  function selectTab(name) {
    document.querySelectorAll(".tab").forEach((t) => {
      const on = t.dataset.tab === name;
      t.classList.toggle("is-active", on);
      t.setAttribute("aria-selected", on ? "true" : "false");
      t.tabIndex = on ? 0 : -1;
    });
    $("pane-nfa").hidden = name !== "nfa";
    $("pane-dfa").hidden = name !== "dfa";
    fitVisibleDiagrams();
  }

  function showDfaTab() {
    if ($("pane-dfa").hidden) selectTab("dfa");
  }

  /* ---------- string testing ---------- */

  function renderTape(str, done, active) {
    const tape = $("tape");
    tape.textContent = "";
    if (str.length === 0) {
      tape.append(el("span", { className: "status", textContent: "Empty string" }));
      return;
    }
    [...str].forEach((ch, i) => {
      let cls = "cell";
      if (i < done) cls += " done";
      else if (i === active) cls += " current";
      tape.append(el("div", { className: cls, textContent: ch }));
    });
  }

  function showVerdict(result) {
    const v = $("verdict");
    v.hidden = false;
    v.className = "verdict " + (result.accepted ? "ok" : "bad");
    v.textContent = (result.accepted ? "✓ " : "✕ ") + result.reason;
  }

  function resetSim() {
    sim = null;
    $("verdict").hidden = true;
    $("trace").textContent = "";
    $("tape").textContent = "";
    $("step-status").textContent = "";
    highlightState(null);
  }

  function traceItem(p) {
    return el("li", { textContent: `${p.from} reads '${p.symbol}' and moves to ${p.to}` });
  }

  async function fetchResult() {
    const data = await post("/api/test", [$("test-input").value]);
    return data.results[0];
  }

  async function runAll() {
    if (!current) return;
    showError("");
    resetSim();
    showDfaTab();
    try {
      const r = await fetchResult();
      renderTape(r.string, r.path.length, -1);
      r.path.forEach((p) => $("trace").append(traceItem(p)));
      showVerdict(r);
      highlightState(r.final_state);
    } catch (e) {
      showError(e.message);
    }
  }

  async function stepOnce() {
    if (!current) return;
    showError("");
    showDfaTab();
    try {
      if (!sim) {
        resetSim();
        const r = await fetchResult();
        sim = { result: r, index: 0 };
        renderTape(r.string, 0, 0);
        highlightState(r.start_state);
        $("step-status").textContent = `Starting in ${r.start_state}`;
        if (r.path.length === 0) showVerdict(r);      // empty string (or first symbol rejected)
        return;
      }
      const r = sim.result;
      if (sim.index < r.path.length) {
        const p = r.path[sim.index];
        $("trace").append(traceItem(p));
        sim.index += 1;
        renderTape(r.string, sim.index, sim.index);
        highlightState(p.to);
        $("step-status").textContent = `Read '${p.symbol}', now in ${p.to}`;
      }
      if (sim.index >= r.path.length) {
        showVerdict(r);
        highlightState(r.final_state);
      }
    } catch (e) {
      showError(e.message);
    }
  }

  async function runBatch() {
    if (!current) return;
    showError("");
    const lines = $("batch").value.split("\n").map((s) => s.replace(/\r$/, ""));
    while (lines.length && lines[lines.length - 1] === "") lines.pop();
    if (!lines.length) return;
    try {
      const data = await post("/api/test", lines);
      const table = $("batch-table");
      $("batch-wrap").hidden = false;
      table.textContent = "";
      table.append(el("thead", {}, [
        el("tr", {}, ["String", "Result", "Details"].map((t) => el("th", { textContent: t }))),
      ]));
      const body = el("tbody");
      data.results.forEach((r) => {
        body.append(el("tr", {}, [
          el("td", { textContent: r.string === "" ? "(empty string)" : r.string }),
          el("td", { className: r.accepted ? "ok" : "bad", textContent: r.accepted ? "✓ Accepted" : "✕ Rejected" }),
          el("td", { textContent: r.reason }),
        ]));
      });
      table.append(body);
    } catch (e) {
      showError(e.message);
    }
  }

  /* ---------- wiring ---------- */

  $("regex-form").addEventListener("submit", (e) => { e.preventDefault(); convert(); });
  $("dead-state").addEventListener("change", () => { if (current) convert(); });

  document.querySelectorAll(".chip").forEach((b) =>
    b.addEventListener("click", () => { $("regex").value = b.dataset.regex; convert(); })
  );

  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => selectTab(tab.dataset.tab));
    tab.addEventListener("keydown", (e) => {
      if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
        const next = tab.dataset.tab === "nfa" ? "dfa" : "nfa";
        selectTab(next);
        $("tab-" + next).focus();
      }
    });
  });

  document.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-zoom]");
    if (!btn) return;
    const id = btn.closest(".toolbar").dataset.for;
    const z = zoomState[id];
    if (!z) return;
    const mode = btn.dataset.zoom;
    if (mode === "fit") {
      z.manual = false;
      fitDiagram(id, true);
    } else {
      z.manual = true;
      z.scale = Math.min(3, Math.max(0.25, z.scale * (mode === "in" ? 1.2 : 1 / 1.2)));
      applyZoom(id);
    }
  });

  $("subset-details").addEventListener("toggle", () => {
    if ($("subset-details").open) fitDiagram("subset-diagram");
  });
  window.addEventListener("resize", fitVisibleDiagrams);

  $("run-btn").addEventListener("click", runAll);
  $("test-input").addEventListener("keydown", (e) => { if (e.key === "Enter") runAll(); });
  $("test-input").addEventListener("input", resetSim);
  $("step-btn").addEventListener("click", stepOnce);
  $("reset-btn").addEventListener("click", resetSim);
  $("batch-btn").addEventListener("click", runBatch);

  convert();
})();