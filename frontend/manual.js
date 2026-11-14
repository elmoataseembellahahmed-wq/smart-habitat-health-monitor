// Manual test page: type readings by hand, or upload a whole mission as CSV.
// Plain JavaScript, no external libraries.

const $ = (id) => document.getElementById(id);
const st = { mission: null, qlang: "en", clang: "en", last: null, sel: null };

function el(tag, attrs = {}, ...kids) {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") n.className = v;
    else if (k === "onclick") n.addEventListener("click", v);
    else n.setAttribute(k, v);
  }
  for (const c of kids) if (c != null) n.append(c instanceof Node ? c : document.createTextNode(String(c)));
  return n;
}

async function api(path, opts = {}) {
  const res = await fetch(path, opts);
  const text = await res.text();
  let body;
  try { body = JSON.parse(text); } catch { body = text; }
  if (!res.ok) throw new Error(body?.detail || text || res.status);
  return body;
}
const post = (path, data, type = "application/json") =>
  api(path, { method: "POST", headers: { "Content-Type": type }, body: type === "application/json" ? JSON.stringify(data) : data });

// ---------- tabs ----------
function tab(which) {
  $("quick").hidden = which !== "quick";
  $("csv").hidden = which !== "csv";
  $("tabQuick").classList.toggle("on", which === "quick");
  $("tabCsv").classList.toggle("on", which === "csv");
}

// ---------- quick check ----------
const EXTRA = { camera_minutes: ["Camera time (face in view)", "min"], exercise_minutes: ["Exercise", "min"] };

function buildFields() {
  const box = $("qfields");
  const sig = st.mission.signals;
  const keys = Object.keys(sig).filter((k) => !sig[k].derived);
  box.replaceChildren(
    ...keys.map((k) => el("label", {}, el("span", {}, sig[k].name, " ", el("span", { class: "u" }, sig[k].unit)),
      el("input", { id: `f_${k}`, type: "number", step: "any" }),
      el("span", { class: "n", id: `n_${k}` }, ""))),
    ...Object.entries(EXTRA).map(([k, [name, unit]]) => el("label", {}, el("span", {}, name, " ", el("span", { class: "u" }, unit)),
      el("input", { id: `f_${k}`, type: "number", step: "any" }))));
}

async function fillNormal() {
  const aid = $("qaid").value;
  const d = await api(`/api/manual/defaults?aid=${aid}`);
  $("qday").textContent = d.day;
  for (const [k, v] of Object.entries(d.values)) {
    const inp = $(`f_${k}`);
    if (inp) inp.value = v ?? "";
  }
  for (const [k, v] of Object.entries(d.normal)) {
    const n = $(`n_${k}`);
    if (n) n.textContent = `this astronaut's normal: ${v}`;
  }
  $("c_co2").value = d.cabin.co2;
  $("c_rad").value = d.cabin.radiation;
}

function readForm() {
  const values = {};
  document.querySelectorAll("#qfields input").forEach((i) => { values[i.id.slice(2)] = i.value === "" ? null : Number(i.value); });
  return { aid: $("qaid").value, values, cabin: { co2: $("c_co2").value, radiation: $("c_rad").value } };
}

function showQuick(r) {
  st.last = r;
  const d = r.decision;
  const name = st.mission.crew.find((c) => c.id === r.aid)?.name || r.aid;
  $("qhead").replaceChildren(el("div", { class: "qhead" },
    el("span", { class: "big" }, `${name}, day ${r.day}`),
    el("span", { class: `badge ${d.state}` }, d.state),
    el("span", { class: "role" }, `score ${d.score} · data ${d.coverage.confidence} · AI ${d.ai.level}`)));
  $("qhistory").replaceChildren(el("span", {}, "Days you added:"),
    ...r.history.map((h) => el("span", { class: `badge ${h.state}`, title: `score ${h.score}` },
      `${h.day} ${st.mission.crew.find((c) => c.id === h.aid)?.name || h.aid}: ${h.state}`)));
  $("qreport").textContent = st.qlang === "ar" ? r.report_ar : r.report_en;
  $("qreport").dir = st.qlang === "ar" ? "rtl" : "ltr";
  $("qday").textContent = r.day + 1;
}

async function evaluate(e) {
  e.preventDefault();
  try { showQuick(await post("/api/manual/day", readForm())); }
  catch (err) { $("qreport").textContent = `Error: ${err.message}`; }
}

async function resetQuick() {
  await post("/api/manual/reset", {});
  st.last = null;
  $("qhead").replaceChildren(); $("qhistory").replaceChildren();
  $("qreport").textContent = "Manual days cleared. Evaluate a day to start again.";
  await fillNormal();
}

function setQLang(l) {
  st.qlang = l;
  $("qen").classList.toggle("on", l === "en"); $("qar").classList.toggle("on", l === "ar");
  if (st.last) showQuick(st.last);
}

// ---------- whole mission ----------
async function upload(file) {
  $("csvmsg").replaceChildren(el("p", { class: "role" }, "Analysing the mission... (about 10 seconds for 125 days)"));
  $("csvgrid").replaceChildren(); $("csvwide").replaceChildren();
  let r;
  try { r = await post("/api/manual/upload", await file.text(), "text/csv"); }
  catch (err) { $("csvmsg").replaceChildren(el("p", { class: "errors" }, `Error: ${err.message}`)); return; }
  if (!r.ok) {
    $("csvmsg").replaceChildren(el("p", { class: "errors" }, "The file needs fixing:"),
      el("ul", { class: "errors" }, ...r.errors.map((x) => el("li", {}, x))));
    return;
  }
  st.upload = r;
  $("csvmsg").replaceChildren(el("p", {}, `Loaded ${r.crew.length} astronaut(s), days ${r.days[0]}-${r.days[1]}. `,
    "Days 1-14 teach each person's normal; every later day is judged below. Click a day to read its report."));
  const days = r.grid[r.crew[0].id].map((x) => x.day);
  const head = el("tr", {}, el("th", {}, ""), ...days.map((d) => el("td", { class: "daynum", title: `day ${d}` }, d % 10 === 0 ? d : "")));
  const rows = r.crew.map((c) => el("tr", {}, el("th", {}, `${c.name} (${c.id})`),
    ...r.grid[c.id].map((x) => {
      const marks = [x.sensor_check.length ? "s" : "", x.band_check ? "b" : "", x.drift.length ? "d" : ""].join("");
      const td = el("td", { class: x.state, title: `day ${x.day}: ${x.state}, score ${x.score}, AI ${x.ai}, data ${x.confidence}` +
        (x.sensor_check.length ? `, sensor check: ${x.sensor_check.join(", ")}` : "") +
        (x.band_check ? `, band swapped with ${x.band_check}` : "") + (x.drift.length ? `, slow drift: ${x.drift.join(", ")}` : "") }, marks);
      td.addEventListener("click", () => { st.sel = { aid: c.id, day: x.day, td }; loadCsvReport(); });
      return td;
    })));
  $("csvgrid").replaceChildren(el("table", {}, head, ...rows),
    el("div", { class: "legend2" }, "Green Normal · amber Watch · red Act · letters: s = sensor check, b = band swap, d = slow drift"));
  const wide = Object.entries(r.crew_wide);
  if (wide.length) $("csvwide").replaceChildren(el("h3", {}, "Crew-wide events"),
    el("ul", {}, ...wide.map(([d, notes]) => el("li", {}, el("b", {}, `Day ${d}: `), notes.join(" ")))));
}

async function loadCsvReport() {
  if (!st.sel) return;
  document.querySelectorAll(".cgrid td.sel").forEach((t) => t.classList.remove("sel"));
  st.sel.td.classList.add("sel");
  const txt = await api(`/api/manual/upload/report/${encodeURIComponent(st.sel.aid)}?day=${st.sel.day}&lang=${st.clang}`);
  $("creport").textContent = txt;
  $("creport").dir = st.clang === "ar" ? "rtl" : "ltr";
}

function setCLang(l) {
  st.clang = l;
  $("cen").classList.toggle("on", l === "en"); $("car").classList.toggle("on", l === "ar");
  loadCsvReport();
}

async function init() {
  st.mission = await api("/api/mission");
  $("qaid").replaceChildren(...st.mission.crew.map((c) => el("option", { value: c.id }, `${c.name} (${c.role})`)));
  buildFields();
  await fillNormal();
  $("qaid").addEventListener("change", fillNormal);
  $("qform").addEventListener("submit", evaluate);
  $("qnormal").addEventListener("click", fillNormal);
  $("qreset").addEventListener("click", resetQuick);
  $("qen").addEventListener("click", () => setQLang("en"));
  $("qar").addEventListener("click", () => setQLang("ar"));
  $("cen").addEventListener("click", () => setCLang("en"));
  $("car").addEventListener("click", () => setCLang("ar"));
  $("tabQuick").addEventListener("click", () => tab("quick"));
  $("tabCsv").addEventListener("click", () => tab("csv"));
  $("file").addEventListener("change", (e) => e.target.files[0] && upload(e.target.files[0]));
}

init().catch((err) => { $("qreport").textContent = `Could not load: ${err.message}. Is the server running?`; });
