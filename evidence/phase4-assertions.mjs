// Phase 4 verification: nav partial over file:// — DOM shape, no-JS render, visual.
// Usage: node evidence/phase4-assertions.mjs
import { spawn } from "node:child_process";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const URL = "file:///Users/wesleymatos/projects/personal/oss-site/www/index.html";
const PORT = 9224;

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
    } catch {}
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
await send("Runtime.enable");
const results = [];
const check = (label, ok, detail = "") => results.push({ label, ok, detail: String(detail) });

async function loadPage() {
  await send("Page.navigate", { url: URL });
  await sleep(1500);
}

// --- with JS ---
await loadPage();
const navShape = await evaluate(`(() => {
  const navs = document.querySelectorAll("nav.site-nav");
  const nav = navs[0];
  if (!nav) return null;
  const cur = nav.querySelectorAll('a[aria-current="page"]');
  return {
    count: navs.length,
    parentTag: nav.parentElement.tagName,
    inCatalog: !!nav.closest("#catalog"),
    inHeader: !!nav.closest(".site-header"),
    links: Array.from(nav.querySelectorAll("a")).map(a => a.textContent.trim()),
    hrefs: Array.from(nav.querySelectorAll("a")).map(a => a.href),
    ariaCurrentCount: cur.length,
    ariaCurrentHref: cur[0] ? cur[0].href : null,
    beforeCatalog: (nav.nextElementSibling || document.body.firstElementChild) !== null &&
                   (nav.compareDocumentPosition(document.getElementById("catalog")) &
                    Node.DOCUMENT_POSITION_FOLLOWING) !== 0,
  };
})()`);
check("exactly one nav.site-nav", navShape && navShape.count === 1, JSON.stringify(navShape));
check("nav is a direct child of <body>",
  navShape && navShape.parentTag === "BODY", navShape && navShape.parentTag);
check("nav not inside #catalog or .site-header",
  navShape && !navShape.inCatalog && !navShape.inHeader);
check("nav has 5 links", navShape && navShape.links.length === 5,
  JSON.stringify(navShape && navShape.links));
check("exactly one aria-current, pointing at oss.wesleymatos.dev",
  navShape && navShape.ariaCurrentCount === 1 &&
  navShape.ariaCurrentHref === "https://oss.wesleymatos.dev/",
  JSON.stringify(navShape && navShape.ariaCurrentHref));
check("nav sits above #catalog in DOM order", navShape && navShape.beforeCatalog);

const backLink = await evaluate(`({
  html: document.querySelectorAll(".back-link").length,
})`);
check(".back-link absent from DOM", backLink.html === 0);

const navVisible = await evaluate(`(() => {
  const nav = document.querySelector("nav.site-nav");
  const r = nav.getBoundingClientRect();
  const cs = getComputedStyle(nav);
  const page = document.querySelector(".page").getBoundingClientRect();
  return {
    pos: cs.position, top: r.top, right: window.innerWidth - r.right,
    z: parseInt(cs.zIndex, 10), pageZ: parseInt(getComputedStyle(document.querySelector(".page")).zIndex, 10),
    abovePage: page.top + 22 <= r.top + 10,
    display: cs.display,
  };
})()`);
check("nav fixed top-right (top≈22px, right≈26px), z above .page",
  navVisible.pos === "fixed" && Math.abs(navVisible.top - 22) < 2 &&
  Math.abs(navVisible.right - 26) < 2 && navVisible.z === 3 && navVisible.z > navVisible.pageZ,
  JSON.stringify(navVisible));

const shot = await send("Page.captureScreenshot", { format: "png" });
if (shot.result?.data)
  writeFileSync(join(import.meta.dirname, "phase4-viewport.png"), Buffer.from(shot.result.data, "base64"));

// --- with JS disabled ---
await send("Emulation.setScriptExecutionDisabled", { value: true });
await loadPage();
const noJs = await evaluate(`(() => {
  const nav = document.querySelector("nav.site-nav");
  return {
    navPresent: !!nav,
    links: nav ? nav.querySelectorAll("a").length : 0,
    catalogEmpty: document.getElementById("catalog").children.length === 0,
  };
})()`);
check("no-JS: nav still renders with 5 links (static markup); catalog empty is pre-existing",
  noJs.navPresent && noJs.links === 5 && noJs.catalogEmpty, JSON.stringify(noJs));
await send("Emulation.setScriptExecutionDisabled", { value: false });

console.log("screenshot: evidence/phase4-viewport.png");
console.log("\n=== RESULTS ===");
let failed = 0;
for (const r of results) {
  if (!r.ok) failed++;
  console.log(`${r.ok ? "PASS" : "FAIL"}: ${r.label}${r.detail ? " — " + r.detail : ""}`);
}
console.log(`\nTOTAL: ${results.length - failed}/${results.length} passed`);
process.exit(failed ? 1 : 0);
