#!/usr/bin/env node
// Build the local review page for one round of an SVG draft. The owner opens the
// resulting HTML from file:// (no server, no publishing) and sees the rendered PNG,
// the zoomable SVG and the previous version side by side, with one feedback box per
// element id. Copy/download the notes and paste them back to the agent.
//
// Usage: node scripts/draft-review.mjs draft-v02.svg [draft-v01.svg] > review.html
// Put `<name>.svg`, `<name>.png` (from `resvg <name>.svg <name>.png`) and the previous
// round's files in a drafts/ folder outside the build tree. Never overwrite a round.
//
// The page prefixes its own ids, classes and CSS variables with `rv-` so a draft's
// own names cannot restyle the chrome or hijack its buttons, and it keys the feedback
// store on a hash of the draft (not its name), so two projects using draft-v01.svg
// never share notes.
import { readFileSync, existsSync } from "node:fs";

const [curPath, prevPath] = process.argv.slice(2);
if (!curPath) {
  console.error("usage: node draft-review.mjs draft-vNN.svg [draft-vNN-1.svg] > review.html");
  process.exit(2);
}

const read = (p) => readFileSync(p, "utf8");
const pngOf = (p) => {
  const candidate = p.replace(/\.svg$/i, ".png");
  return existsSync(candidate) ? "data:image/png;base64," + readFileSync(candidate).toString("base64") : null;
};

// A stable key from the draft's content: a revised draft starts with empty boxes,
// and unrelated projects never collide on a shared drafts/draft-v01.svg name.
const hash = (s) => {
  let h = 5381;
  for (const c of s) h = (h * 33 ^ c.charCodeAt(0)) >>> 0;
  return h.toString(16);
};

// A feedback box per discussable part: every id in the draft. The label is the id, and
// the draft's own text gives the reviewer context when it exists.
const elements = (svg) => {
  const seen = new Set();
  const out = [];
  for (const m of svg.matchAll(/<([a-zA-Z][\w:-]*)\b([^>]*?)\bid="([^"]+)"/g)) {
    const id = m[3];
    if (seen.has(id) || id === "bg" || id === "background") continue;
    seen.add(id);
    let text = "";
    const after = svg.slice(m.index);
    const end = after.indexOf("</" + m[1] + ">");
    if (m[1] === "text" && end !== -1) text = after.slice(0, end).replace(/<[^>]+>/g, "").trim();
    out.push({ id, tag: m[1], text });
  }
  return out;
};

// The check writes borderline-contrast lines as WARN; if its output was saved
// next to the draft, show those warnings here, above the draft.
const checkFile = [curPath + ".check.txt", curPath.replace(/\.svg$/i, ".check.txt")]
  .find(existsSync);
const warns = checkFile
  ? read(checkFile).split("\n").filter((l) => l.startsWith("WARN:")).map((l) => l.slice(5).trim())
  : [];

// A draft can carry web-sourced text, so anything shown on this page is escaped.
const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;")
  .replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");

const cur = read(curPath);
const prev = prevPath ? read(prevPath) : null;
const curPng = pngOf(curPath);
const prevPng = prevPath ? pngOf(prevPath) : null;
const parts = elements(cur);
const contentKey = "draft-review:" + hash(cur);

const pane = (title, svg, png) => `
<section class="rv-pane"><h2>${title}</h2>
${png ? `<div class="rv-shot"><img src="${png}" alt="${title} rendered PNG"></div>` : ""}
<div class="rv-zoom"><div class="rv-inner" data-zoom>${svg}</div></div>
<input class="rv-zr" type="range" min="50" max="400" value="100" aria-label="Zoom ${title}">
</section>`;

const cards = parts.map((e) => `
<div class="rv-fb"><label for="rv-fb-${e.id}"><code>${e.id}</code>${e.text ? ` — ${e.text}` : ""} <span class="rv-tag">${e.tag}</span></label>
<textarea id="rv-fb-${e.id}" data-id="${e.id}" placeholder="Feedback on #${e.id}"></textarea></div>`).join("");

process.stdout.write(`<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Draft review — ${curPath}</title><style>
:root{--rv-bg:#f6f5f2;--rv-fg:#1c1c1c;--rv-muted:#6b6b6b;--rv-line:#d9d6cf;--rv-card:#fff}
@media (prefers-color-scheme:dark){:root{--rv-bg:#161616;--rv-fg:#eee;--rv-muted:#9a9a9a;--rv-line:#333;--rv-card:#1f1f1f}}
*{box-sizing:border-box}body{margin:0;background:var(--rv-bg);color:var(--rv-fg);font:14px/1.45 system-ui,sans-serif}
main{max-width:1200px;margin:0 auto;padding:16px}h1{font-size:18px;margin:4px 0 12px}
.rv-panes{display:grid;grid-template-columns:1fr 1fr;gap:16px}@media(max-width:760px){.rv-panes{grid-template-columns:1fr}}
.rv-pane{background:var(--rv-card);border:1px solid var(--rv-line);padding:12px}.rv-pane h2{font-size:13px;margin:0 0 8px;color:var(--rv-muted)}
.rv-shot img{max-width:100%;display:block;border:1px solid var(--rv-line)}
.rv-zoom{overflow:auto;margin-top:8px;background:var(--rv-bg);border:1px solid var(--rv-line)}
.rv-zoom svg{display:block;width:100%;height:auto;min-width:300px}
.rv-zr{width:100%;margin-top:6px}
.rv-fbs{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:10px;margin-top:16px}
.rv-fb{background:var(--rv-card);border:1px solid var(--rv-line);padding:10px}
.rv-fb label{font-size:12px;display:block;margin-bottom:4px}.rv-tag{color:var(--rv-muted)}
textarea{width:100%;min-height:56px;font:inherit;background:var(--rv-bg);color:var(--rv-fg);border:1px solid var(--rv-line)}
.rv-bar{display:flex;gap:8px;align-items:center;margin:12px 0}
button{font:inherit;padding:6px 12px;border:1px solid var(--rv-line);background:var(--rv-card);color:var(--rv-fg);cursor:pointer}
.rv-meta{color:var(--rv-muted);font-size:12px}
.rv-warn{border:1px solid #d9480f;padding:8px 12px;margin:8px 0 16px;background:var(--rv-card)}
.rv-warn ul{margin:4px 0 0;padding-left:18px;font-size:13px}
</style></head><body><main>
<h1>Draft review — ${curPath}${prev ? " vs " + prevPath : ""}</h1>
${warns.length ? `<div class="rv-warn"><strong>Check warnings — judge these by eye</strong><ul>${
  warns.map((w) => `<li>${esc(w)}</li>`).join("")}</ul></div>` : ""}
<div class="rv-panes">
${pane("Current", cur, curPng)}
${prev ? pane("Previous", prev, prevPng) : ""}
</div>
<div class="rv-bar"><button id="rv-copy">Copy feedback</button><button id="rv-dl">Download feedback.md</button><span id="rv-msg" class="rv-meta"></span></div>
<div class="rv-fbs">${cards || '<p class="rv-meta">This draft has no element ids; add one id per discussable part.</p>'}</div>
</main><script>
const KEY="${contentKey}";
const rvCopy=document.getElementById("rv-copy"),rvDl=document.getElementById("rv-dl"),rvMsg=document.getElementById("rv-msg");
const store={get:k=>{try{return localStorage.getItem(KEY+k)||""}catch{return""}},set:(k,v)=>{try{localStorage.setItem(KEY+k,v)}catch{}}};
document.querySelectorAll("textarea[data-id]").forEach(t=>{t.value=store.get(t.dataset.id);t.oninput=()=>store.set(t.dataset.id,t.value)});
document.querySelectorAll(".rv-pane").forEach(p=>{const z=p.querySelector(".rv-zr"),svg=p.querySelector(".rv-inner svg");
if(!z||!svg)return;z.oninput=()=>{svg.style.width=z.value+"%"}});
function feedback(){const rows=[...document.querySelectorAll("textarea[data-id]")].filter(t=>t.value.trim()).map(t=>"- **"+"#"+t.dataset.id+"**: "+t.value.trim());
return "# Draft feedback — ${curPath}\\n\\n"+(rows.join("\\n")||"- Approved as is.")+"\\n"}
rvCopy.onclick=async()=>{try{await navigator.clipboard.writeText(feedback());rvMsg.textContent="Copied. Paste it back to the agent."}catch{rvMsg.textContent="Copy blocked; use Download."}};
rvDl.onclick=()=>{const a=document.createElement("a");a.href=URL.createObjectURL(new Blob([feedback()],{type:"text/markdown"}));a.download="feedback.md";a.click()};
</script></body></html>
`);
