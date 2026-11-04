#!/usr/bin/env node
// Render a time-pure HTML scene to PNG frames: for frame i, call window.renderAt(i / fps), seek the CSS /
// Web Animations that were running since page load to the same time, and screenshot to <out>/<i:04d>.png.
// --verify renders the frames again in reverse order and fails if any frame's hash differs.
// Usage: node scripts/render.mjs --url <page> [--fps 30] [--duration 4 | --frames 0,45,84] [--out out/frames]
//                                [--width 1920] [--height 1080] [--scale 1] [--gpu] [--verify]
import { createHash } from "node:crypto";
import { mkdirSync, readFileSync, rmSync } from "node:fs";
import { parseArgs } from "node:util";
import { chromium } from "playwright";

const { values: a } = parseArgs({
  options: {
    url: { type: "string" }, out: { type: "string", default: "out/frames" },
    fps: { type: "string", default: "30" }, duration: { type: "string" }, frames: { type: "string" },
    width: { type: "string", default: "1920" }, height: { type: "string", default: "1080" },
    scale: { type: "string", default: "1" }, gpu: { type: "boolean", default: false },
    verify: { type: "boolean", default: false },
  },
});
const die = (msg, code = 1) => { console.error(msg); process.exit(code); };
if (!a.url || !(a.duration || a.frames)) die("need --url and one of --duration or --frames", 2);
const pos = (k) => { const n = Number(a[k]); if (!(n > 0)) die(`--${k} must be a positive number`, 2); return n; };
const fps = pos("fps"), width = pos("width"), height = pos("height"), scale = pos("scale");
const frames = a.frames
  ? [...new Set(a.frames.split(",").map((s) => (/^\d+$/.test(s.trim()) ? Number(s) : die(`bad frame ${s}`, 2))))]
  : [...Array(Math.round(pos("duration") * fps)).keys()]; // 0..N-1: a loop's frame N is frame 0

// Compositor-thread CSS animations ignore a seek until the next commit, so the first frame shows a
// wall-clock position; run them on the main thread instead.
// Without the GPU flags headless Chromium draws WebGL on the CPU (SwiftShader). macOS uses Metal by default.
const gpu = ["--enable-gpu", "--ignore-gpu-blocklist"];
const args = ["--disable-threaded-animation",
  ...(!a.gpu ? [] : process.platform === "linux" ? ["--use-angle=vulkan", ...gpu] : gpu)];
const browser = await chromium.launch({ args });
const fail = async (msg) => { await browser.close(); die(msg); };
const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: scale });
// A throw inside the scene would leave a stale picture on screen; stop instead.
let pageError = null;
page.on("pageerror", (e) => { pageError ??= e.message; });
await page.goto(a.url, { waitUntil: "load" });
if (pageError) await fail(`page error: ${pageError}`);
// fonts.ready alone misses faces nothing has used yet; load every declared face and decode every image.
await page.evaluate(async () => {
  await Promise.all([...document.fonts].map((f) => f.load().catch(() => {})));
  await document.fonts.ready;
  await Promise.all([...document.images].map((i) => i.decode().catch(() => {})));
});
if (!(await page.evaluate(() => typeof window.renderAt === "function"))) await fail("the page does not expose window.renderAt(t)");
// Animations running since load start at t = 0, so render.mjs can seek them to t. Any other animation
// is the scene's own: renderAt must pause and seek it.
await page.evaluate(() => { window.__fromLoad = new Set(document.getAnimations()); });
if (a.gpu) console.log("gpu:", await page.evaluate(() => {
  const g = document.createElement("canvas").getContext("webgl");
  const e = g && g.getExtension("WEBGL_debug_renderer_info");
  return e ? g.getParameter(e.UNMASKED_RENDERER_WEBGL) : "none";
}));

const file = (dir, i) => `${dir}/${String(i).padStart(4, "0")}.png`;
async function shoot(list, dir) {
  mkdirSync(dir, { recursive: true });
  for (const i of list) {
    const err = await page.evaluate(async (t) => {
      try { await window.renderAt(t); } catch (e) { return `renderAt threw: ${e.message}`; }
      for (const an of document.getAnimations()) {
        if (window.__fromLoad.has(an)) { an.pause(); an.currentTime = t * 1000; }
        else if (an.playState === "running") return "an animation renderAt started is running; pause and seek it in renderAt";
      }
      // The scene owns <video>: it seeks in renderAt and awaits 'seeked'. A playing one runs on the wall clock.
      if ([...document.querySelectorAll("video")].some((v) => !v.paused)) return "a <video> is playing";
    }, i / fps);
    if (err || pageError) await fail(`frame ${i}: ${err || `page error: ${pageError}`}`);
    await page.screenshot({ path: file(dir, i) });
  }
}

await shoot(frames, a.out);
if (a.verify) {
  const dir = `${a.out}/.verify`;
  await shoot([...frames].reverse(), dir);
  const hash = (p) => createHash("sha256").update(readFileSync(p)).digest("hex");
  const bad = frames.filter((i) => hash(file(a.out, i)) !== hash(file(dir, i)));
  if (bad.length) await fail(`not deterministic: frame(s) ${bad.join(",")} differ when rendered in reverse order (kept in ${dir})`);
  rmSync(dir, { recursive: true });
  console.log("verify: every frame identical in reverse order");
}
await browser.close();
console.log(`${frames.length} frame(s) → ${a.out}`);
