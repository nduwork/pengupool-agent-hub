#!/usr/bin/env python3
"""Self-test for the shared SVG draft check (scripts/svg_check.py copies).

Every fixture is a known failure, warning or clean control; the unit checks pin
the maths. The test fails if a check is removed: worst-glyph contrast, not-visible
text, tspan/gradient scoring, minimum glyph, size, overflow, every safe-area edge,
SMIL, var(), no-opaque-background, resvg stderr/return/missing, PNG decoding and
the decode-error branch, or drift between the two copies.

Run: python3 scripts/svg_check_selftest.py
"""
import importlib.util
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import types
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COPIES = [
    os.path.join(ROOT, "agents/apps/frontend-ui-agent/skills/pengupool-ui-design/scripts/svg_check.py"),
    os.path.join(ROOT, "agents/apps/motion-video-agent/skills/motion-video/scripts/svg_check.py"),
]
WHITE = '<rect x="0" y="0" width="400" height="200" fill="#ffffff"/>'


def svg(body, w=400, h=200):
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
            'viewBox="0 0 %d %d">%s</svg>' % (w, h, w, h, body))


BAD = svg(WHITE +
          '<rect id="a" x="10" y="10" width="120" height="60" fill="#0d9488"/>'
          '<rect id="b" x="80" y="40" width="120" height="60" fill="#e5e7eb"/>'
          '<text id="label" x="20" y="35" font-size="14" fill="#ffffff">fails aa</text>'
          '<animateMotion dur="1s" path="M0,0 L10,0"/>')
OVERFLOW = svg(WHITE + '<text id="long" x="20" y="100" font-size="16" fill="#000000">%s</text>'
               % ("a line far too long for the frame " * 3))
BOXOVER = svg(WHITE + '<rect id="box" x="10" y="10" width="60" height="40" fill="#ffffff"/>'
              '<text id="bt" x="15" y="30" font-size="16" fill="#000000">overflowing label</text>')
VIDEO = svg('<rect x="0" y="0" width="390" height="844" fill="#ffffff"/>'
            '<rect id="edge" x="10" y="300" width="100" height="100" fill="#e5e7eb"/>'
            '<text id="mid" x="195" y="422" font-size="16" fill="#000000" text-anchor="middle">ok</text>',
            w=390, h=844)
MIDDLE = svg('<rect x="0" y="0" width="390" height="844" fill="#ffffff"/>'
             '<text id="top" x="195" y="80" font-size="12" fill="#000000" text-anchor="middle">top band</text>',
             w=390, h=844)
LARGE = svg(WHITE + '<text id="t18" x="10" y="40" font-size="18" fill="#0d9488">normal 18px</text>'
            '<text id="t19" x="10" y="80" font-size="19" font-weight="bold" fill="#0d9488">bold 19px</text>')
VAR = svg(WHITE + '<rect x="10" y="10" width="100" height="50" fill="var(--panel)"/>')
MASK = svg(WHITE + '<rect id="m" x="10" y="10" width="100" height="100" fill="#ffffff" mask="url(#nope)"/>')

STYLEFILL = svg(WHITE + '<text id="s" x="20" y="60" font-size="20" fill="#111111" '
                'style="fill:#fefefe">style beats attribute</text>')
ALPHA0 = svg(WHITE + '<text id="a" x="20" y="60" font-size="20" fill="#000000" '
             'fill-opacity="0">invisible</text>')
PATHBG = svg('<path d="M0 0 H400 V200 H0 Z" fill="#111111"/>'
             '<text id="p" x="20" y="60" font-size="20" fill="#111111">same as path</text>')
TSPAN = svg(WHITE + '<text id="ts" x="20" y="60" font-size="20" fill="#111111">'
            '<tspan fill="#fefefe">pale tspan</tspan></text>')
STROKE = svg(WHITE + '<text id="st" x="20" y="60" font-size="20" fill="none" '
             'stroke="#fefefe">stroked</text>')
HIDDEN = svg('<text id="h" x="20" y="60" font-size="20" fill="#111111">under a rect</text>'
             '<rect x="0" y="0" width="400" height="200" fill="#111111"/>')
SIZERULE = svg('<style>.h{font-size:48px}</style>' + WHITE +
               '<text class="h" id="sr" x="380" y="100" fill="#000000">'
               'this caption is long and will run off the frame</text>')
DEFAULT16 = svg(WHITE + '<text id="d" x="20" y="100" fill="#000000">'
                'this default-size caption is long enough to run past the frame edge</text>')
SANE = svg(WHITE + '<style>.ok{fill:#000000}</style>'
           '<text class="ok" id="ok" x="20" y="60" font-size="16">style fills are fine now</text>')

PRICE = svg(WHITE + '<text id="p" x="20" y="80" font-size="16" fill="#111111">$49 '
            '<tspan fill="#cccccc">per month billed yearly</tspan></text>')
GRADIENT = svg('<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="0">'
               '<stop offset="0" stop-color="#ffffff"/><stop offset="1" stop-color="#000000"/>'
               '</linearGradient></defs><rect x="0" y="0" width="400" height="200" fill="url(#g)"/>'
               '<text id="gt" x="10" y="80" font-size="10" fill="#ffffff" textLength="380">'
               'AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA</text>')
PALEDOT = svg(WHITE + '<text id="d" x="20" y="80" font-size="16" fill="#fefefe">'
              'Pale words <tspan fill="#000000">.</tspan></text>')
TSPAN_OK = svg(WHITE + '<text id="tk" x="20" y="80" font-size="16" fill="#111111">$49 '
              '<tspan fill="#111111">per month</tspan></text>')

# one low glyph among many readable ones: only the minimum catches it
MIN_GLYPH = svg(WHITE + '<rect x="178" y="40" width="18" height="24" fill="#333333"/>'
                '<text id="mg" x="20 60 100 140 180 220 260 300 340 380" y="60" '
                'font-size="16" fill="#000000">HHHHHHHHHH</text>')
SMALL_GREY = svg(WHITE + '<text id="sg" x="20" y="60" font-size="10" fill="#767676">'
                 'sample label sentence</text>')
# a region between 3:1 and half the best pixel must still WARN (old worst_region dropped it)
MEDIUM = ('<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300" viewBox="0 0 400 300">'
          '<rect width="400" height="300" fill="#ffffff"/><path d="M0 60H120V120H0Z" fill="#bbbbbb"/>'
          '<text id="md" x="20" y="100" font-size="20" fill="#707070">Cross over white</text></svg>')
TIGHT = ('<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300" viewBox="0 0 400 300">'
         '<rect width="400" height="300" fill="#ffffff"/><path d="M0 60H100V120H0Z" fill="#111111"/>'
         '<text x="20" y="100" font-family="sans-serif" font-size="30" letter-spacing="-3" '
         'fill="#dddddd">Crossing</text></svg>')
ITALIC = ('<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300" viewBox="0 0 400 300">'
          '<rect width="400" height="300" fill="#ffffff"/><path d="M0 60H100V120H0Z" fill="#111111"/>'
          '<text x="20" y="100" font-family="sans-serif" font-size="30" font-style="italic" '
          'fill="#dddddd">Crossing</text></svg>')
ROTATE_GRAD = ('<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300" viewBox="0 0 400 300">'
               '<rect width="400" height="300" fill="#fff"/><defs><linearGradient id="g" '
               'gradientUnits="userSpaceOnUse" x1="0" x2="300"><stop offset="0" stop-color="#000"/>'
               '<stop offset="0.5" stop-color="#000"/><stop offset="0.5" stop-color="#eee"/>'
               '<stop offset="1" stop-color="#eee"/></linearGradient></defs>'
               '<g transform="translate(300,0) rotate(90)"><text x="100" y="100" font-size="30" '
               'font-family="sans-serif" fill="url(#g)">IIIIIIIIIIII</text></g></svg>')

NO_BG = svg('<text id="t" x="20" y="60" font-size="20" fill="#111111">no background rect</text>')
NESTED = svg('<rect id="outer" x="0" y="0" width="400" height="200" fill="#ffffff"/>'
             '<rect id="inner" x="50" y="50" width="100" height="50" fill="#e5e7eb"/>')
EDGE_R = svg('<rect x="0" y="0" width="1280" height="720" fill="#ffffff"/>'
             '<rect id="r" x="1200" y="300" width="100" height="100" fill="#e5e7eb"/>', 1280, 720)
EDGE_B = svg('<rect x="0" y="0" width="1280" height="720" fill="#ffffff"/>'
             '<rect id="b" x="600" y="640" width="100" height="100" fill="#e5e7eb"/>', 1280, 720)
EDGE_T = svg('<rect x="0" y="0" width="1280" height="720" fill="#ffffff"/>'
             '<rect id="t" x="600" y="10" width="100" height="50" fill="#e5e7eb"/>', 1280, 720)
ANCHOR_END = svg(WHITE + '<text id="e" x="390" y="100" font-size="16" fill="#000000" '
                'text-anchor="end">a caption that ends at the right edge</text>')
ANCHOR_MID = svg(WHITE + '<text id="m" x="200" y="100" font-size="16" fill="#000000" '
                'text-anchor="middle">a caption centred in the frame</text>')
TX = svg(WHITE + '<g transform="translate(180,0)">'
         '<rect id="g1" x="10" y="10" width="120" height="60" fill="#e5e7eb"/></g>'
         '<rect id="r2" x="80" y="40" width="120" height="60" fill="#eeeeee"/>')
ROTATE = svg('<rect x="0" y="0" width="400" height="400" fill="#ffffff"/>'
             '<text id="r" transform="rotate(90 200 200)" x="200" y="120" font-size="16" '
             'fill="#fefefe">rotated pale</text>', 400, 400)
VIEWBOX = ('<svg xmlns="http://www.w3.org/2000/svg" width="400" height="200" viewBox="100 100 400 200">'
           '<rect x="100" y="100" width="400" height="200" fill="#ffffff"/>'
           '<text id="v" x="120" y="160" font-size="16" fill="#000000">readable offset</text></svg>')
SMIL_SET = svg(WHITE + '<text id="s" x="20" y="60" font-size="16" fill="#000000">x'
               '<set attributeName="fill" to="#000"/></text>')
SIZE_UNK = svg('<style>.a .b{font-size:48px}</style>' + WHITE +
               '<text class="b" id="su" x="20" y="80" fill="#000000">x</text>')
WEIGHT_UNK = svg('<style>.a .b{font-weight:bold}</style>' + WHITE +
                 '<text class="b" id="wu" x="20" y="80" font-size="16" fill="#000000">x</text>')
ANCHOR_UNK = svg('<style>.a .b{text-anchor:end}</style>' + WHITE +
                 '<text class="b" id="au" x="20" y="80" font-size="16" fill="#000000">x</text>')

GOOD = svg(WHITE + '<rect id="a" x="10" y="10" width="120" height="60" fill="#ffffff"/>'
           '<rect id="b" x="200" y="10" width="120" height="60" fill="#e5e7eb"/>'
           '<text id="label" x="20" y="45" font-size="14" fill="#000000">clean</text>')


def load(path):
    spec = importlib.util.spec_from_file_location("svg_check_%d" % abs(hash(path)), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write(text):
    fd, path = tempfile.mkstemp(suffix=".svg")
    with os.fdopen(fd, "w") as f:
        f.write(text)
    return path


def craft_png(w, h, rows):
    raw = b"".join(bytes([f]) + data for f, data in rows)

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


def main():
    assert open(COPIES[0], "rb").read() == open(COPIES[1], "rb").read(), \
        "the two svg_check.py copies differ; keep them byte-identical"
    mod = load(COPIES[0])

    def run(text, video=False):
        return mod.check(write(text), video=video)

    def has(ps, word):
        return any(word in p for p in ps)

    # maths pinned: luminance / alpha-compositing mutations fail here
    assert abs(mod.contrast((255, 0, 0), (255, 255, 255)) - 3.998) < 0.01, "luminance changed"
    assert abs(mod.contrast((0, 0, 255), (255, 255, 255)) - 8.59) < 0.02, "luminance changed"
    assert mod.pixel(bytes([0, 0, 0, 128]), 4, 0) == (127, 127, 127), "alpha compositing changed"

    # one pin on the WARN threshold; contrast no longer has a FAIL threshold
    assert mod.NEED_NORMAL == 4.5, "WARN threshold changed"
    assert mod.SPECK_MIN == 5, "speck threshold changed"
    speck = {(r, 0): 1.0 for r in range(4)}                      # 4-pixel speck, ignored
    speck.update({(10 + c, 10): 6.0 for c in range(10)})          # 10-pixel glyph
    assert mod.component_bests(speck) == [6.0], "speck threshold changed"
    assert mod.component_bests({(0, 0): 5.0}) == [5.0], "all-speck fallback changed"
    two = {(0, c): 2.0 for c in range(6)}
    two.update({(10, c): 9.0 for c in range(6)})
    assert min(mod.component_bests(two)) == 2.0, "worst component not taken"

    # exact checks FAIL and block
    f, w = run(BAD)
    assert has(f, "overlap") and has(f, "SMIL"), "BAD failures: %s" % f
    assert has(w, "advisory"), "BAD contrast should warn: %s" % w
    assert has(run(OVERFLOW)[0], "runs past the frame"), "frame overflow"
    assert has(run(BOXOVER)[0], "runs past #box"), "box overflow"
    assert has(run(VIDEO, video=True)[0], "safe area"), "--video safe area"
    assert not has(run(VIDEO)[0], "safe area"), "safe area without --video"
    assert has(run(MIDDLE, video=True)[0], "middle 75%"), "portrait middle 75%%"
    assert has(run(EDGE_R, video=True)[0], "safe area"), "right safe-area edge"
    assert has(run(EDGE_B, video=True)[0], "safe area"), "bottom safe-area edge"
    assert has(run(EDGE_T, video=True)[0], "safe area"), "top safe-area edge"
    assert has(run(VAR)[0], "var()"), "var()"
    assert has(run(SMIL_SET)[0], "SMIL"), "<set> not caught"
    assert not has(run(NESTED)[0], "overlap"), "nested rect flagged as overlap"
    assert not has(run(ANCHOR_END)[0], "overflow"), "anchor=end ignored"
    assert not has(run(ANCHOR_MID)[0], "overflow"), "anchor=middle ignored"
    assert has(run(TX)[0], "overlap"), "translate ignored"
    assert not has(run(VIEWBOX)[0], "overflow"), "viewBox origin mishandled"
    if shutil.which("resvg"):
        assert has(run(MASK)[0], "resvg warning"), "non-fallback stderr should FAIL"

    # contrast is advisory: WARN, never a failure
    for text, word in ((STYLEFILL, "contrast"), (ALPHA0, "not visible"), (PATHBG, "not visible"),
                       (TSPAN, "contrast"), (STROKE, "contrast"), (HIDDEN, "not visible"),
                       (PRICE, "contrast"), (GRADIENT, "contrast"), (PALEDOT, "contrast"),
                       (MIN_GLYPH, "contrast"), (ROTATE, "contrast"), (ITALIC, "contrast"),
                       (ROTATE_GRAD, "contrast")):
        failures, warns = run(text)
        assert not failures, "%s should not FAIL: %s" % (text[:24], failures)
        assert has(warns, word), "%s not warned: %s" % (text[:24], warns)
    for text in (TSPAN_OK, SANE):
        failures, warns = run(text)
        assert not failures and not has(warns, "contrast"), "%s wrongly flagged" % text[:24]
    assert not run(TIGHT)[0], "tight text must not FAIL"
    assert has(run(SMALL_GREY)[1], "contrast"), "small grey should warn"
    f, w = run(MEDIUM)
    assert not f and has(w, "contrast"), "medium 3:1-AA region must WARN: %s %s" % (f, w)
    f, w = run(LARGE)
    assert has(w, "#t18"), "18px normal should warn: %s %s" % (f, w)
    assert not has(f, "#t19") and not has(w, "#t19"), "bold 19px should pass"

    # advisory warnings, not failures
    assert not run(NO_BG)[0] and has(run(NO_BG)[1], "no opaque background"), "translucent"
    assert not run(SIZE_UNK)[0] and has(run(SIZE_UNK)[1], "font size unknown"), "size unknown"
    assert not run(WEIGHT_UNK)[0] and has(run(WEIGHT_UNK)[1], "weight unknown"), "weight unknown"
    assert not run(ANCHOR_UNK)[0] and has(run(ANCHOR_UNK)[1], "text anchor unknown"), "anchor unknown"

    # PNG filter 3 (Average): decode must reconstruct the raw pixels
    png = craft_png(1, 2, [(0, bytes([100, 150, 200, 255])), (3, bytes([0, 241, 226, 128]))])
    path = tempfile.mkstemp(suffix=".png")[1]
    open(path, "wb").write(png)
    w_, h_, ch, raw = mod.decode_png(path)
    assert (w_, h_, ch) == (1, 2, 4) and mod.pixel(raw, ch, 0) == (100, 150, 200) \
        and mod.pixel(raw, ch, 1) == (50, 60, 70), "PNG Average filter"

    # decode-error branch
    orig_decode = mod.decode_png
    mod.decode_png = lambda _: (_ for _ in ()).throw(ValueError("boom"))
    try:
        assert has(run(GOOD)[0], "PNG decode failed"), "decode error not reported"
    finally:
        mod.decode_png = orig_decode

    # resvg failure / absence branches
    orig_render = mod.render
    mod.render = lambda p: (p, types.SimpleNamespace(returncode=1, stderr="boom"))
    try:
        assert has(run(GOOD)[0], "resvg failed"), "resvg return code ignored"
    finally:
        mod.render = orig_render
    orig_which = mod.shutil.which
    mod.shutil.which = lambda _: None
    try:
        assert has(run(GOOD)[0], "resvg not found"), "resvg-missing branch"
    finally:
        mod.shutil.which = orig_which

    if shutil.which("node"):
        d = tempfile.mkdtemp()
        svgp = os.path.join(d, "draft-v01.svg")
        open(svgp, "w").write(GOOD)
        open(svgp + ".check.txt", "w").write(
            "WARN: borderline contrast: '<svg/onload=1> x' (4.35:1)\n")
        js = os.path.join(ROOT, "agents/apps/frontend-ui-agent/skills/pengupool-ui-design/scripts/draft-review.mjs")
        out = subprocess.run(["node", js, svgp], capture_output=True, text=True).stdout
        assert "&lt;svg/onload=1&gt;" in out and "<svg/onload=1>" not in out, \
            "review page does not escape WARN text"

    def cli(text):
        return subprocess.run([sys.executable, "-I", COPIES[0], write(text)],
                              capture_output=True, text=True).returncode
    assert cli(OVERFLOW) == 1, "an exact failure must exit 1"
    assert cli(STYLEFILL) == 0, "a contrast warning must exit 0"

    f, w = run(GOOD)
    assert not any(k in p for p in f for k in
                   ("overlap", "contrast", "SMIL", "overflow", "safe area", "opaque")), \
        "clean fixture wrongly failed: %s" % f
    assert not w, "clean fixture wrongly warned: %s" % w
    print("ok: worst-glyph contrast, not-visible, size, overflow, safe-area, SMIL, var(), "
          "opaque, resvg and PNG checks all bite")


if __name__ == "__main__":
    main()
