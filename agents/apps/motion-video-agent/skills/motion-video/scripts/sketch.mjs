#!/usr/bin/env node
// Build a local storyboard sketch from shots.json: one self-contained HTML page (opens from file://)
// with a wireframe animatic, a scrubber, one card per shot and a feedback box per shot.
// The page exposes window.renderAt(t); `?stage` shows only the stage, so render.mjs can make an animatic.
// Usage: node scripts/sketch.mjs shots.json > sketch.html
//
// shots.json: {title, fps, width, height, shots: [{id, from, to, beat, hero, transition, notes,
//   elements: [{label, color, x0, y0, x1, y1, w, h, ease}]}]}
// from/to are frames; x/y/w/h are % of the stage; x0,y0 → x1,y1 over the shot with the named ease.
import { readFileSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";

const path = process.argv[2];
if (!path) { console.error("usage: node scripts/sketch.mjs shots.json > sketch.html"); process.exit(2); }
const data = JSON.parse(readFileSync(path, "utf8"));
for (const k of ["fps", "width", "height", "shots"]) if (data[k] == null) throw new Error(`shots.json: no ${k}`);
// One hand-written SVG key frame per shot, beside shots.json as shot-<id>.svg, shows the
// drawn pose the wireframe only boxes. Element ids here become the scene code's ids.
const dir = dirname(path);
for (const s of data.shots) {
  const f = join(dir, `shot-${s.id}.svg`);
  if (existsSync(f)) s.keySvg = readFileSync(f, "utf8");
}
const json = JSON.stringify(data).replace(/</g, "\\u003c");

process.stdout.write(`<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Sketch</title><style>
:root{--bg:#f6f5f2;--fg:#1c1c1c;--muted:#6b6b6b;--line:#d9d6cf;--card:#fff;--stage:#e9e7e1;--accent:#d9480f}
@media (prefers-color-scheme:dark){:root{--bg:#161616;--fg:#eee;--muted:#9a9a9a;--line:#333;--card:#1f1f1f;--stage:#262626;--accent:#ff8a4c}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.45 system-ui,sans-serif}
main{max-width:1100px;margin:0 auto;padding:16px}h1{font-size:18px;margin:4px 0 12px}
#stage{position:relative;width:100%;background:var(--stage);border:1px solid var(--line);overflow:hidden}
.el{position:absolute;border:2px solid currentColor;display:flex;align-items:center;justify-content:center;
font-size:12px;text-align:center;padding:2px;overflow:hidden}
#cap{position:absolute;left:8px;bottom:6px;font:12px ui-monospace,monospace;color:var(--muted)}
.bar{display:flex;gap:8px;align-items:center;margin:8px 0 16px}.bar input{flex:1}
button{font:inherit;padding:6px 12px;border:1px solid var(--line);background:var(--card);color:var(--fg);cursor:pointer}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px}
.card{background:var(--card);border:1px solid var(--line);padding:12px}.card.on{border-color:var(--accent)}
.card h2{font-size:14px;margin:0 0 4px}.meta{color:var(--muted);font-size:12px}
.key svg{display:block;width:100%;height:auto;background:var(--stage);border:1px solid var(--line);margin-top:8px}
textarea{width:100%;min-height:64px;margin-top:8px;font:inherit;background:var(--bg);color:var(--fg);border:1px solid var(--line)}
body.only main{max-width:none;padding:0}body.only .ui{display:none}body.only #stage{border:0}
</style></head><body><main>
<h1 class="ui" id="title"></h1><div id="stage"><div id="cap"></div></div>
<div class="bar ui"><button id="play">Play</button><input id="scrub" type="range" min="0" step="1" aria-label="Frame"><span id="fr"></span></div>
<div class="bar ui"><button id="copy">Copy feedback</button><button id="dl">Download feedback.md</button><span id="msg" class="meta"></span></div>
<div class="cards ui" id="cards"></div></main>
<script>
const D=${json};
const EASE={linear:[0,0,1,1],"ease-out-expo":[.16,1,.3,1],"ease-out-quint":[.22,1,.36,1],
"ease-in-out-quart":[.76,0,.24,1],"ease-in-expo":[.7,0,.84,0],"ease-out-back":[.34,1.56,.64,1]};
function bez([a,b,c,d],x){if(x<=0||x>=1)return x;let lo=0,hi=1,t=x;for(let i=0;i<30;i++){t=(lo+hi)/2;
const X=3*a*t*(1-t)**2+3*c*t*t*(1-t)+t**3;if(X<x)lo=t;else hi=t}return 3*b*t*(1-t)**2+3*d*t*t*(1-t)+t**3}
const last=Math.max(...D.shots.map(s=>s.to)),stage=document.getElementById("stage"),cap=document.getElementById("cap");
const only=new URLSearchParams(location.search).has("stage");
if(only){document.body.classList.add("only");stage.style.height="100vh"}else stage.style.aspectRatio=D.width+"/"+D.height;
document.getElementById("title").textContent=(D.title||"Sketch")+" — "+D.width+"×"+D.height+", "+D.fps+" fps, "+(last/D.fps).toFixed(1)+" s";
const shotAt=f=>D.shots.find(s=>f>=s.from&&f<s.to)||D.shots[D.shots.length-1];
window.renderAt=t=>{const f=Math.round(t*D.fps),s=shotAt(f);stage.querySelectorAll(".el").forEach(e=>e.remove());
for(const e of s.elements||[]){const p=bez(EASE[e.ease]||EASE.linear,Math.min(1,Math.max(0,(f-s.from)/Math.max(1,s.to-s.from))));
const d=document.createElement("div");d.className="el";d.textContent=e.label||"";d.style.color=e.color||"var(--fg)";
const x1=e.x1??e.x0,y1=e.y1??e.y0;Object.assign(d.style,{left:(e.x0+(x1-e.x0)*p)+"%",top:(e.y0+(y1-e.y0)*p)+"%",width:(e.w||20)+"%",height:(e.h||10)+"%"});stage.appendChild(d)}
cap.textContent="f"+f+" · "+s.id+(s.hero?" · "+s.hero:"");
document.querySelectorAll(".card").forEach(c=>c.classList.toggle("on",c.dataset.id===String(s.id)));
scrub.value=f;fr.textContent="frame "+f+" / "+last};
// Keyed by the shots' content: a revised shots.json starts with empty boxes, not last round's notes.
let h=5381;for(const c of JSON.stringify(D))h=(h*33^c.charCodeAt(0))>>>0;const KEY="sketch:"+h+":";const store={get:k=>{try{return localStorage.getItem(KEY+k)||""}catch{return""}},
set:(k,v)=>{try{localStorage.setItem(KEY+k,v)}catch{}}};
for(const s of D.shots){const c=document.createElement("div");c.className="card";c.dataset.id=s.id;
const h=document.createElement("h2");h.textContent=s.id+(s.beat?" — "+s.beat:"");
const m=document.createElement("div");m.className="meta";m.textContent="frames "+s.from+"–"+s.to+" ("+((s.to-s.from)/D.fps).toFixed(1)+" s)"+(s.transition?" · out: "+s.transition:"");
const p=document.createElement("div");p.textContent=[s.hero&&"Hero: "+s.hero,s.notes].filter(Boolean).join(" · ");
const ta=document.createElement("textarea");ta.placeholder="Feedback on "+s.id+" (cite frames)";ta.value=store.get(s.id);
ta.oninput=()=>store.set(s.id,ta.value);ta.dataset.id=s.id;c.onclick=e=>{if(e.target!==ta){stop();window.renderAt(s.from/D.fps)}};
c.append(h,m,p);
if(s.keySvg){const k=document.createElement("div");k.className="key";k.innerHTML=s.keySvg;c.append(k)}
c.append(ta);cards.appendChild(c)}
function feedback(){const rows=[...document.querySelectorAll("textarea")].filter(t=>t.value.trim()).map(t=>"- **"+t.dataset.id+"**: "+t.value.trim());
return "# Sketch feedback — "+(D.title||"")+"\\n\\n"+(rows.join("\\n")||"- Approved as is.")+"\\n"}
copy.onclick=async()=>{try{await navigator.clipboard.writeText(feedback());msg.textContent="Copied. Paste it back to the agent."}catch{msg.textContent="Copy blocked; use Download."}};
dl.onclick=()=>{const a=document.createElement("a");a.href=URL.createObjectURL(new Blob([feedback()],{type:"text/markdown"}));a.download="feedback.md";a.click()};
scrub.max=last-1;scrub.oninput=()=>{stop();window.renderAt(scrub.value/D.fps)};
let timer=null;function stop(){clearInterval(timer);timer=null;play.textContent="Play"}
play.onclick=()=>{if(timer)return stop();play.textContent="Pause";let f=+scrub.value;
timer=setInterval(()=>{f=(f+1)%last;window.renderAt(f/D.fps)},1000/D.fps)};
window.renderAt(0);
</script></body></html>
`);
