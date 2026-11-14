// Astronaut Health Monitor dashboard. Plain JavaScript, no external libraries,
// so it works fully offline on board.

const state = {
  mission: null,
  day: null,
  selected: "B",
  role: "surgeon",   // whose view: surgeon, commander, or an astronaut id
  lang: "en",
  system: null,
  autoSystem: true,
  series: {},       // series[aid][signal] = {...}
  status: null,
  timer: null,
};

const $ = (id) => document.getElementById(id);

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") node.className = v;
    else if (k === "onclick") node.addEventListener("click", v);
    else node.setAttribute(k, v);
  }
  for (const c of children) {
    if (c == null) continue;
    node.append(c instanceof Node ? c : document.createTextNode(String(c)));
  }
  return node;
}

async function api(path, asText = false) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`${path}: ${res.status}`);
  return asText ? res.text() : res.json();
}

function missingWord(s) {
  if (s.private) return "private";
  if (s.fault === "skipped") return "skipped (optional)";
  if (s.fault) return "unavailable (sensor check)";
  if (s.untrusted) return "set aside (band check)";
  return "not seen";
}

function fmt(value, decimals) {
  if (value === null || value === undefined) return "not seen";
  return decimals ? Number(value).toFixed(decimals) : String(Math.round(value));
}

// ---------- rendering ----------

function renderCabin(cabin) {
  const box = $("cabin");
  box.replaceChildren(
    ...cabin.map((c) => {
      const meta = state.mission.cabin_signals[c.signal];
      const label = c.level ? ` (${c.level.toUpperCase()})` : " (ok)";
      return el("span", { class: `chip ${c.level || ""}`, title: c.note || "" },
        `${c.name}: ${fmt(c.value, meta.decimals)} ${c.unit}${label}`,
        c.note ? el("span", { class: "role" }, ` · ${c.note}`) : null);
    })
  );
}

function renderCrewWide(cw) {
  $("crewwide").replaceChildren(...(cw?.notes || []).map((n) => el("div", {}, el("strong", {}, "Crew-wide: "), n)));
}

function renderCrew(crew) {
  const box = $("crew");
  box.replaceChildren(
    ...crew.map((m) => {
      // Headline: the most important personal problem; cabin air only if it's the only one.
      if (m.restricted) {
        return el("button", { class: `card ${m.state} ${m.id === state.selected ? "selected" : ""}`, type: "button",
            onclick: () => { state.selected = m.id; render(); } },
          el("div", { class: "row" },
            el("div", {}, el("div", { class: "name" }, m.name), el("div", { class: "role" }, m.role)),
            el("span", { class: `badge ${m.state}` }, m.state)),
          el("div", { class: "why" }, m.note));
      }
      const personal = m.patterns.find((p) => p.id === "stress_fatigue") || m.patterns.find((p) => p.id !== "cabin_air");
      const top = (personal || m.patterns[0])?.title || m.flags[0]?.reason || "All signals within personal normal.";
      const trend = el("div", { class: "trend", title: "Last 5 days" },
        ...m.trend.map((t) => el("span", { class: t.state, title: `Day ${t.day}: ${t.state}` })));
      return el("button", {
          class: `card ${m.state} ${m.id === state.selected ? "selected" : ""}`,
          type: "button",
          onclick: () => { state.selected = m.id; render(); },
        },
        el("div", { class: "row" },
          el("div", {}, el("div", { class: "name" }, m.name), el("div", { class: "role" }, m.role)),
          el("span", { class: `badge ${m.state}` }, m.state)),
        el("div", { class: "row" }, el("span", { class: "role" },
          `Score ${m.score} · ${m.routine.normal_streak} day${m.routine.normal_streak === 1 ? "" : "s"} in Normal`), trend),
        el("div", { class: "row" },
          el("span", { class: "role" }, `AI anomaly ${m.ai.score.toFixed(2)}`),
          el("span", { class: `ai-tag ${m.ai.level}` }, m.ai.level === "normal" ? "AI: normal" : `AI: ${m.ai.level}`)),
        m.coverage && m.coverage.confidence !== "full"
          ? el("div", { class: `role conf-${m.coverage.confidence}` }, `Data: ${m.coverage.confidence} confidence`) : null,
        m.sensor_faults?.length ? el("div", { class: "role conf-limited" }, `Sensor check: ${m.sensor_faults.map((f) => f.device_name).join(", ")}`) : null,
        el("div", { class: "why" }, top));
    })
  );
}

function listOrEmpty(id, items, make, emptyText) {
  const box = $(id);
  box.replaceChildren(...(items.length ? items.map(make) : [el("li", { class: "empty" }, emptyText)]));
}

function sparkline(series, upToDay, level) {
  const W = 220, H = 48, pad = 4;
  const pts = series.points;
  const vals = pts.map((p) => p.value).filter((v) => v !== null && v !== undefined);
  if (!vals.length || series.baseline_mean == null) return null;
  const band = 2.5 * series.baseline_sd;
  const lo = Math.min(...vals, series.baseline_mean - band);
  const hi = Math.max(...vals, series.baseline_mean + band);
  const x = (i) => pad + (i / (pts.length - 1)) * (W - 2 * pad);
  const y = (v) => H - pad - ((v - lo) / (hi - lo || 1)) * (H - 2 * pad);
  const ns = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(ns, "svg");
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  svg.setAttribute("preserveAspectRatio", "none");

  const rect = document.createElementNS(ns, "rect");
  const top = y(series.baseline_mean + band), bottom = y(series.baseline_mean - band);
  rect.setAttribute("x", 0); rect.setAttribute("width", W);
  rect.setAttribute("y", top); rect.setAttribute("height", Math.max(1, bottom - top));
  rect.setAttribute("fill", "rgba(63,191,127,0.12)");
  svg.append(rect);

  const shown = pts.filter((p) => p.day <= upToDay);
  const path = document.createElementNS(ns, "polyline");
  // Unavailable readings (sensor faults) are left out of the line, never drawn as values.
  path.setAttribute("points", shown.map((p, i) => (p.value == null ? null : `${x(i)},${y(p.value)}`)).filter(Boolean).join(" "));
  path.setAttribute("fill", "none");
  path.setAttribute("stroke", "#6aa9ff");
  path.setAttribute("stroke-width", "1.5");
  path.setAttribute("vector-effect", "non-scaling-stroke");
  svg.append(path);

  if (shown.length && shown[shown.length - 1].value != null) {
    const last = shown[shown.length - 1];
    const dot = document.createElementNS(ns, "circle");
    dot.setAttribute("cx", x(shown.length - 1));
    dot.setAttribute("cy", y(last.value));
    dot.setAttribute("r", 3);
    dot.setAttribute("fill", level ? (level === "mild" ? "#f2b134" : "#ef5b5b") : "#3fbf7f");
    svg.append(dot);
  }
  return svg;
}

// ---------- body figure ----------

const STATUS_WORD = { normal: "Normal", watch: "Watch", act: "Act", info: "No daily sensor" };
const STATUS_RANK = { act: 3, watch: 2, normal: 1, info: 0 };

function renderBody(m) {
  if (m.restricted) {
    document.querySelectorAll("#bodySvg .part").forEach((g) => g.setAttribute("class", "part info"));
    $("bodyInfo").replaceChildren(el("p", { class: "restricted" }, m.note));
    return;
  }
  const systems = m.systems;
  // Keep the user's choice; otherwise open the most urgent body system.
  if (!state.system || !systems[state.system] || state.autoSystem) {
    state.system = Object.keys(systems).sort((a, b) => STATUS_RANK[systems[b].status] - STATUS_RANK[systems[a].status])[0];
    state.autoSystem = true;
  }
  document.querySelectorAll("#bodySvg .part").forEach((g) => {
    const key = g.dataset.system;
    g.setAttribute("class", `part ${systems[key].status} ${key === state.system ? "selected" : ""}`);
    g.setAttribute("aria-label", `${state.mission.body_systems[key].name}: ${STATUS_WORD[systems[key].status]}`);
  });

  const key = state.system, sys = systems[key], meta = state.mission.body_systems[key];
  const byKey = Object.fromEntries(m.signals.map((s) => [s.signal, s]));
  const rows = sys.signals.map((k) => {
    const s = byKey[k], sm = state.mission.signals[k];
    return el("tr", { class: s.level || "" },
      el("td", {}, el("div", {}, s.source === "wristband" ? "Fatigue estimate (wristband)" : s.name),
        el("div", { class: "about" }, s.note || sm.about)),
      el("td", { class: "v" }, s.missing ? missingWord(s) : `${fmt(s.value, sm.decimals)} ${s.unit}`),
      el("td", { class: "about" }, s.baseline == null ? "" : `normal ${fmt(s.baseline, sm.decimals)}`));
  });
  $("bodyInfo").replaceChildren(...[
    el("div", { class: "sys-head" }, el("h4", {}, meta.name),
      el("span", { class: `sys-status ${sys.status}` }, STATUS_WORD[sys.status])),
    el("p", {}, el("b", {}, "What it does: "), meta.does),
    el("p", {}, el("b", {}, "In space: "), meta.space),
    meta.measured ? el("p", {}, el("b", {}, "What we measure: "), meta.measured) : null,
    el("div", { class: "lbl" }, "Spaceflight hazards"),
    el("div", { class: "chips" }, ...meta.hazards.map((h) => el("span", { class: "chip-h" }, h))),
    rows.length ? el("div", { class: "lbl" }, "Readings today") : null,
    rows.length ? el("table", { class: "readings" }, ...rows) : null,
    el("div", { class: "lbl" }, "What to do"),
    el("ul", {}, ...sys.actions.map((a) => el("li", {}, a)))].filter(Boolean));
}

function bindBody() {
  document.querySelectorAll("#bodySvg .part").forEach((g) => {
    const pick = () => {
      state.system = g.dataset.system;
      state.autoSystem = false;
      const m = state.status.crew.find((c) => c.id === state.selected);
      if (m) renderBody(m);
    };
    g.addEventListener("click", pick);
    g.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); pick(); } });
  });
}

function renderSensors(live) {
  const devs = state.mission.devices;
  $("sensors").replaceChildren(...Object.entries(devs).map(([key, d]) => {
    const isCam = key === "camera";
    const status = isCam && live && live.length
      ? (live.some((x) => !x.simulated) ? "live webcam connected" : "demo camera running") : "simulated";
    return el("div", { class: "sensor" }, el("strong", {}, d.name),
      el("div", {}, d.measures), el("div", { class: "role" }, d.how_often),
      el("div", { class: `st ${status.includes("webcam") || status.includes("demo") ? "on" : ""}` }, status));
  }));
}

const ATYPE = { escalate: "escalate", equipment: "equipment", confirm: "confirm first", "self-care": "self-care", none: "" };
function actionType(a) {
  const t = a.toLowerCase();
  if (/flight surgeon|psychologist|commander|notify/.test(t)) return "escalate";
  if (/re-check|re-measure|confirm|check-in|check in/.test(t)) return "confirm";
  if (/scrubber|sensor|wristband|patch|strap|camera/.test(t)) return "equipment";
  if (/no action|nothing to do/.test(t)) return "none";
  return "self-care";
}

// The astronaut's first view: what changed, how sure the system is, what to do, when to escalate.
function renderSummary(m) {
  if (m.restricted) { $("summary").replaceChildren(el("div", {}, el("b", {}, "Shared with crewmates"), m.note)); return; }
  const changed = m.band_check ? "Wristband check: the band seems swapped. No health alarm."
    : ((m.patterns.find((p) => p.id === "stress_fatigue") || m.patterns[0])?.title || (m.flags[0] ? `${m.flags.length} signal(s) outside your normal` : "Nothing: all within your normal."));
  const cov = m.coverage;
  const next = m.actions[0] || "No action needed.";
  const esc = m.state === "ACT" ? "Now: send the report to the flight surgeon at the next contact window."
    : m.state === "WATCH" ? "If this continues tomorrow, it becomes ACT and goes to the flight surgeon."
    : "Nothing to escalate.";
  $("summary").replaceChildren(
    el("div", {}, el("b", {}, "What changed"), changed),
    el("div", {}, el("b", {}, "How sure"), el("span", { class: `conf-${cov.confidence}` }, `${cov.confidence} confidence`), ` · ${cov.note}`),
    el("div", {}, el("b", {}, "Do next"), next),
    el("div", {}, el("b", {}, "When to escalate"), esc));
}

function renderDetail(m) {
  $("detailTitle").textContent = `${m.name} (${m.role}), day ${state.day}`;
  const badge = $("detailBadge");
  badge.className = `badge ${m.state}`;
  badge.textContent = m.state;
  renderSummary(m);
  if (m.restricted) {
    ["patterns", "reasons", "rules", "actions", "routine"].forEach((id) => $(id).replaceChildren());
    $("ai").replaceChildren(); $("signals").replaceChildren(el("p", { class: "restricted" }, m.note));
    return;
  }

  listOrEmpty("patterns", m.patterns,
    (p) => el("li", {}, el("strong", {}, p.title), " - ", p.explain),
    "No risk pattern detected.");
  listOrEmpty("reasons", m.flags,
    (f) => el("li", {}, el("span", { class: `lvl ${f.level}` }, f.level), f.reason),
    "All signals are within this astronaut's normal range.");
  listOrEmpty("rules", m.rules_fired, (r) => el("li", {}, r), "No rule fired: state is NORMAL.");
  // Data-integrity notes: a swapped wristband, or a slow drift since the start of the mission.
  const extra = [];
  (m.sensor_faults || []).forEach((f) => extra.push(el("li", { class: "integrity" },
    el("strong", {}, `Sensor check (${f.device_name}): `), f.messages.join(" "), " ", f.action)));
  if (m.self_report_skipped) extra.push(el("li", { class: "integrity" }, el("strong", {}, "Diary: "),
    "skipped today (optional), so mood was not assessed."));
  if (m.band_check) extra.push(el("li", { class: "integrity" }, el("strong", {}, "Wristband check: "), m.band_check.message));
  (m.drift || []).forEach((x) => extra.push(el("li", { class: "integrity" }, el("strong", {}, "Slow drift: "), x.reason)));
  if (extra.length) $("reasons").prepend(...extra);
  const ai = m.ai;
  const pct = Math.min(100, Math.max(0, (ai.score - 0.3) / 0.5 * 100));
  const thr = Math.min(100, Math.max(0, (ai.threshold - 0.3) / 0.5 * 100));
  $("ai").replaceChildren(
    el("div", { class: "ai-row" },
      el("strong", {}, ai.score.toFixed(2)),
      el("span", { class: `ai-tag ${ai.level}` }, ai.level),
      el("span", { class: "role" }, `unusual above ${ai.threshold.toFixed(2)}`)),
    (() => {
      const bar = el("div", { class: "ai-bar" });
      bar.append(el("span", { class: `fill ${ai.level}`, style: `width:${pct}%` }),
                 el("span", { class: "mark", style: `left:${thr}%`, title: "threshold" }));
      return bar;
    })(),
    el("p", { class: "ai-note" }, ai.note));
  $("actions").replaceChildren(...m.actions.map((a) => el("li", {},
    ATYPE[actionType(a)] ? el("span", { class: "atype" }, ATYPE[actionType(a)]) : null, a)));
  const r = m.routine;
  $("routine").replaceChildren(
    ...r.reminders.map((x) => el("li", {},
      el("span", { class: `due ${x.due_in_days === 0 ? "today" : ""}` },
        x.due_in_days === 0 ? "today" : `in ${x.due_in_days} d`),
      el("b", {}, x.task), " - ", x.why)),
    el("li", {}, el("span", { class: "due streak" }, `${r.normal_streak}`),
      el("b", {}, "Days in a row in Normal"),
      r.normal_streak >= 7 ? " - great run, keep the routine going." : ""));

  const sigBox = $("signals");
  sigBox.replaceChildren(
    ...m.signals.map((s) => {
      const meta = state.mission.signals[s.signal];
      const ser = state.series[m.id]?.[s.signal];
      return el("div", { class: `sig ${s.level ? "flag-" + s.level : ""}` },
        el("div", { class: "t" }, `${s.source === "wristband" ? "Fatigue estimate" : s.name} - ${state.mission.devices[s.device].name}`),
        s.note ? el("div", { class: "about" }, s.note) : null,
        el("div", { class: "v" }, s.missing ? missingWord(s) : `${fmt(s.value, meta.decimals)} ${s.unit}`,
          s.baseline == null ? null : el("span", { class: "role" }, `  normal ${fmt(s.baseline, meta.decimals)}`)),
        ser && !s.private ? sparkline(ser, state.day, s.level) : null);
    })
  );
}

async function render() {
  $("dayLabel").textContent = state.day;
  state.status = await api(`/api/status?day=${state.day}&role=${state.role}`);
  renderCabin(state.status.cabin);
  renderCrewWide(state.status.crew_wide);
  renderCrew(state.status.crew);
  const m = state.status.crew.find((c) => c.id === state.selected) || state.status.crew[0];
  renderDetail(m);
  renderBody(m);
  await loadReport(m.id);
}

async function loadReport(aid) {
  const pre = $("report");
  pre.textContent = await api(`/api/report/${aid}?day=${state.day}&lang=${state.lang}&role=${state.role}`, true);
  pre.dir = state.lang === "ar" ? "rtl" : "ltr";
  pre.lang = state.lang;
}

function setLang(lang) {
  state.lang = lang;
  $("langEn").classList.toggle("on", lang === "en");
  $("langAr").classList.toggle("on", lang === "ar");
  if (state.status) loadReport(state.selected).catch(showError);
}

// ---------- live camera ----------

async function pollLive() {
  const box = $("live");
  let r;
  try { r = await api("/api/live"); } catch { return; }
  state.live = r.readings || [];
  renderSensors(state.live);
  if (!r.connected) {
    box.className = "live";
    box.replaceChildren(
      el("div", { class: "live-head" }, el("strong", {}, "Cabin camera"),
        el("span", { class: "role" }, "not connected")),
      el("div", { class: "role", style: "margin-top:6px" },
        "Real input from your webcam: run ", el("code", {}, "python camera/live_camera.py --band B"),
        " in a second terminal while this server is running. --band is the wristband near the camera."));
    return;
  }
  // One block per camera that is reporting (normally one in the demo).
  const order = { ACT: 3, WATCH: 2, NORMAL: 1 };
  const worst = state.live.reduce((a, b) => ((order[b.state] || 0) > (order[a.state] || 0) ? b : a));
  box.className = `live ${worst.state}`;
  const stat = (label, value) => el("div", {}, el("strong", {}, value), label);
  const pct = (v) => (v != null ? `${Math.round(v * 100)}%` : "-");
  box.replaceChildren(...state.live.map((x) => {
    const t = x.today || {};
    const peak = t.peak_hour ? `${String(t.peak_hour.hour).padStart(2, "0")}:00 (${pct(t.peak_hour.perclos)} closed)` : "-";
    return el("div", { class: "live-item" },
      el("div", { class: "live-head" },
        el("span", { class: "live-dot", title: "live" }),
        el("strong", {}, `Cabin camera · wristband ${x.band} → ${x.astronaut} ${x.simulated ? "(demo camera, simulated)" : "(real webcam)"}`),
        el("span", { class: `badge ${x.state.replace(/ /g, "")}` }, x.state)),
      el("div", { class: "live-stats" },
        stat("blinks per minute", x.blink_rate ?? "-"),
        stat("eyes closed, last min", pct(x.perclos)),
        stat("long closures, last min", x.long_closures ?? "-"),
        stat("fatigue score /100", x.fatigue_score ?? "-"),
        stat("personal normal (blinks/min)", x.baseline_blink_rate ?? "learning")),
      el("div", { class: "live-stats today" },
        stat("minutes in view today", t.face_minutes ?? "-"),
        stat("eyes closed today", pct(t.perclos)),
        stat("microsleeps today", t.microsleeps ?? "-"),
        stat("most tired hour", peak)),
      el("ul", {}, ...(x.reasons || []).concat(x.actions || []).map((s) => el("li", {}, s))));
  }));
}

// ---------- controls ----------

function setDay(d) {
  state.day = d;
  $("day").value = d;
  render().catch(showError);
}

function togglePlay() {
  const btn = $("play");
  if (state.timer) {
    clearTimeout(state.timer);
    state.timer = null;
    btn.innerHTML = "&#9654; Play";
    return;
  }
  // Start the story just after the baseline window if we're at the end.
  if (state.day >= state.mission.last_day) setDay(state.mission.baseline_days[1] + 1);
  btn.innerHTML = "&#10074;&#10074; Pause";
  // Quiet weeks play fast; the story days (from day 115) play slowly.
  const step = () => {
    if (state.day >= state.mission.last_day) return togglePlay();
    setDay(state.day + 1);
    state.timer = setTimeout(step, state.day >= 115 ? 1500 : 150);
  };
  state.timer = setTimeout(step, 150);
}

function showError(err) {
  console.error(err);
  $("report").textContent = `Could not load data: ${err.message}. Is the backend running?`;
}

// Load every signal's history for the charts, as the current role may see it.
async function loadSeries() {
  const jobs = [];
  for (const m of state.mission.crew) {
    state.series[m.id] = {};
    for (const key of Object.keys(state.mission.signals)) {
      jobs.push(api(`/api/series/${m.id}/${key}?role=${state.role}`).then((s) => { state.series[m.id][key] = s; }));
    }
  }
  await Promise.all(jobs);
}

async function init() {
  state.mission = await api("/api/mission");
  const slider = $("day");
  slider.min = state.mission.first_day;
  slider.max = state.mission.last_day;
  slider.addEventListener("input", () => setDay(Number(slider.value)));
  bindBody();
  renderSensors([]);
  $("play").addEventListener("click", togglePlay);
  $("role").addEventListener("change", (e) => {
    state.role = e.target.value;
    if (!["surgeon", "commander"].includes(state.role)) state.selected = state.role;
    loadSeries().then(render).catch(showError);
  });
  $("copy").addEventListener("click", () => navigator.clipboard?.writeText($("report").textContent));
  $("langEn").addEventListener("click", () => setLang("en"));
  $("langAr").addEventListener("click", () => setLang("ar"));
  // The browser's print dialog has "Save as PDF"; the print styles show only the report.
  $("pdf").addEventListener("click", () => window.print());

  await loadSeries();
  setDay(state.mission.last_day - 1);
  pollLive();
  setInterval(pollLive, 1500);
}

init().catch(showError);
