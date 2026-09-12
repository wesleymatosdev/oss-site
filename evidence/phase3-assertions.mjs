// Phase 3 verification: headless-Chrome assertions against the real rendered page over file://
// Usage: node evidence/phase3-assertions.mjs
import { spawn } from "node:child_process";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const URL = "file:///Users/wesleymatos/projects/personal/oss-site/www/index.html";
const PORT = 9223;

const chrome = spawn(CHROME, [
  `--remote-debugging-port=${PORT}`,
  `--user-data-dir=${mkdtempSync(join(tmpdir(), "oss-cdp-"))}`,
  "--headless=new", "--no-first-run", "--no-default-browser-check",
  "--disable-gpu", "about:blank",
], { stdio: "ignore" });
process.on("exit", () => chrome.kill());

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function wsConnect() {
  for (let i = 0; i < 50; i++) {
    try {
      const list = await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json();
      const page = list.find((t) => t.type === "page");
      if (page) return new WebSocket(page.webSocketDebuggerUrl);
    } catch { /* chrome not up yet */ }
    await sleep(200);
  }
  throw new Error("chrome devtools endpoint never came up");
}

const ws = await wsConnect();
let mid = 0;
const pending = new Map();
ws.onmessage = (ev) => {
  const msg = JSON.parse(ev.data);
  if (msg.id && pending.has(msg.id)) { pending.get(msg.id)(msg); pending.delete(msg.id); }
};
function send(method, params = {}) {
  const id = ++mid;
  ws.send(JSON.stringify({ id, method, params }));
  return new Promise((res) => pending.set(id, res));
}
async function evaluate(expr) {
  const r = await send("Runtime.evaluate", { expression: expr, returnByValue: true });
  if (r.result?.exceptionDetails) throw new Error(JSON.stringify(r.result.exceptionDetails));
  return r.result?.result?.value;
}

await new Promise((r) => (ws.onopen = r));
await send("Page.enable");
await send("Page.navigate", { url: URL });
await sleep(1500); // load + app.js render

const results = [];
const check = (label, ok, detail = "") =>
  results.push({ label, ok, detail: String(detail) });

// --- counts ---
const cardFull = await evaluate(`document.querySelectorAll(".card-full").length`);
check(".card-full count == 21", cardFull === 21, cardFull);
const cardTotal = await evaluate(`document.querySelectorAll(".card").length`);
check("total .card count == 77", cardTotal === 77, cardTotal);

const groupCounts = await evaluate(`Array.from(document.querySelectorAll(".group")).map(g => ({
  id: g.dataset.group,
  claimed: parseInt(g.querySelector(".group-count").textContent.replace(/[^0-9]/g, ""), 10),
  actual: g.querySelectorAll(".card").length,
}))`);
const badGroups = groupCounts.filter((g) => g.claimed !== g.actual);
check("per-group group-count == DOM .card children (both wrappers)",
  groupCounts.length === 8 && badGroups.length === 0,
  JSON.stringify(badGroups.length ? badGroups : groupCounts.map((g) => `${g.id}:${g.actual}`)));

// --- filter behavior ---
const setFilter = (v) => evaluate(`(() => {
  const i = document.getElementById("filter");
  i.value = ${JSON.stringify(v)};
  i.dispatchEvent(new Event("input", { bubbles: true }));
})()`);
const visible = () => evaluate(
  `Array.from(document.querySelectorAll(".card")).filter(el => el.style.display !== "none").length`);
const countText = () => evaluate(`document.getElementById("count").textContent`);

await setFilter("rust");
const rustVisible = await visible();
const rustCount = await countText();
check('filter "rust": #count == "N of 77 projects", N == visible cards',
  rustCount === `${rustVisible} of 77 projects`, `${rustCount} (visible=${rustVisible})`);

await setFilter("zzzz");
const zzzzVisible = await visible();
const groupsHidden = await evaluate(
  `Array.from(document.querySelectorAll(".group")).every(g => g.style.display === "none")`);
const zzzzCount = await countText();
check('filter "zzzz": every .group hidden, count "0 of 77"',
  zzzzVisible === 0 && groupsHidden && zzzzCount === "0 of 77 projects",
  `visible=${zzzzVisible} groupsHidden=${groupsHidden} count=${zzzzCount}`);

await setFilter("");
const clearVisible = await visible();
const clearCount = await countText();
check('filter cleared: 77 visible, count "77 projects"',
  clearVisible === 77 && clearCount === "77 projects", `${clearCount} (visible=${clearVisible})`);

// --- section-specific assertions ---
const section = (name) => `document.querySelector(".card-full h3") ? (() => {
  const cards = Array.from(document.querySelectorAll(".card-full"));
  const c = cards.find(x => x.querySelector(".card-name").textContent === ${JSON.stringify(name)});
  if (!c) return null;
  return {
    starBtns: c.querySelectorAll("a.star-btn").length,
    githubLinks: c.querySelectorAll('a[href*="github.com"]').length,
    siteBtns: Array.from(c.querySelectorAll("a.site-btn")).map(a => a.href),
    soon: c.querySelectorAll(".badge.soon").length,
    stateNote: (c.querySelector(".state-note") || {}).textContent || null,
    state: (c.querySelector(".badge.state") || {}).textContent || null,
    text: c.textContent,
  };
})() : null`;

const consoleArt = await evaluate(section("console-art"));
check("console-art: no star/repo anchor, has private-source note",
  consoleArt && consoleArt.starBtns === 0 && consoleArt.githubLinks === 0 &&
  /never published/.test(consoleArt.stateNote),
  JSON.stringify(consoleArt && { s: consoleArt.starBtns, g: consoleArt.githubLinks, n: consoleArt.stateNote }));

const website = await evaluate(section("website"));
check("website: site anchor -> wesleymatos.dev, no repo anchor",
  website && website.githubLinks === 0 &&
  website.siteBtns.includes("https://wesleymatos.dev/"),
  JSON.stringify(website && { g: website.githubLinks, site: website.siteBtns }));

for (const name of ["fleet-bus", "auto-permissions"]) {
  const s = await evaluate(section(name));
  check(`${name}: .badge.soon present, no repo anchor`,
    s && s.soon === 1 && s.starBtns === 0 && s.githubLinks === 0,
    JSON.stringify(s && { soon: s.soon, stars: s.starBtns, gh: s.githubLinks }));
}

const stars = await evaluate(`Array.from(document.querySelectorAll(".stars")).map(el => ({
  text: el.textContent, in: el.closest(".card").querySelector(".card-name").textContent }))`);
check('exactly one stars chip: spinning-cube "★ 3 stars"',
  stars.length === 1 && stars[0].in === "spinning-cube" && stars[0].text.includes("3 stars"),
  JSON.stringify(stars));

const sessionRc = await evaluate(section("session-rc"));
check('session-rc state badge "v0 — working"',
  sessionRc && sessionRc.state === "v0 — working", JSON.stringify(sessionRc && sessionRc.state));
const unfitRs = await evaluate(section("unfit-rs"));
check('unfit-rs state "PoC — unmaintained" + Lavish note',
  unfitRs && unfitRs.state === "PoC — unmaintained" && /Lavish/.test(unfitRs.stateNote),
  JSON.stringify(unfitRs && { s: unfitRs.state, n: unfitRs.stateNote }));

// every full section has a purpose paragraph and a state badge
const fullShape = await evaluate(`(() => {
  const bad = [];
  document.querySelectorAll(".card-full").forEach(c => {
    const n = c.querySelector(".card-name").textContent;
    if (!c.querySelector(".card-purpose")) bad.push(n + ":no-purpose");
    if (!c.querySelector(".badge.state")) bad.push(n + ":no-state");
  });
  return bad;
})()`);
check("every .card-full has .card-purpose and .badge.state", fullShape.length === 0,
  JSON.stringify(fullShape));

// private/local full sections must have no repo anchor (public && url gating)
const privateFulls = await evaluate(`(() => {
  const out = [];
  document.querySelectorAll(".card-full").forEach(c => {
    const n = c.querySelector(".card-name").textContent;
    const hasRepo = c.querySelectorAll('a[href*="github.com"]').length > 0;
    const star = c.querySelectorAll("a.star-btn").length;
    if (["console-art","fleet-bus","auto-permissions","website"].includes(n) && (hasRepo || star))
      out.push(n);
  });
  return out;
})()`);
check("private/local sections expose no repo anchors", privateFulls.length === 0,
  JSON.stringify(privateFulls));

// --- screenshot (full page) ---
const shot = await send("Page.captureScreenshot", {
  format: "png", captureBeyondViewport: true,
});
const { writeFileSync } = await import("node:fs");
if (shot.result?.data) {
  writeFileSync(join(import.meta.dirname, "phase3-fullpage.png"),
    Buffer.from(shot.result.data, "base64"));
  console.log("screenshot: evidence/phase3-fullpage.png");
}

console.log("\n=== RESULTS ===");
let failed = 0;
for (const r of results) {
  if (!r.ok) failed++;
  console.log(`${r.ok ? "PASS" : "FAIL"}: ${r.label}${r.detail ? " — " + r.detail : ""}`);
}
console.log(`\nTOTAL: ${results.length - failed}/${results.length} passed`);
process.exit(failed ? 1 : 0);
