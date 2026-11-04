#!/usr/bin/env python3
"""Check a hand-written SVG draft before showing it to the owner for review.

Contrast is measured from the PNG the owner actually sees, not from parsing
paint. For each text (and each <tspan>) the whole frame is rendered once with it
and once without it; pixels that change are its visible glyphs, and the score is
the WORST glyph's best contrast. Rendering the whole frame (not a guessed band)
covers multiple x positions, rotate, scale, dy, per-tspan y and textLength. A
text that changes no pixel is "not visible".

Contrast is ADVISORY. Every contrast result, including "text not visible", is a
WARN shown on the review page for the owner to confirm by eye; contrast never
blocks a draft. It measures the worst 2-D connected component's best contrast
against WCAG AA (4.5:1, or 3:1 for large text). A glyph that exactly matches its
background changes no pixel and is a known limit; a fully invisible text still
warns.

Exact checks FAIL and block:
  - resvg exits 0 and prints no stderr except font fallback (a WARN)
  - no fill uses var()
  - no two labelled rects partially overlap (nesting is fine)
  - no text overruns its box, or the frame, when its positioning is simple
  - --video: nothing within 60 px of an edge; portrait key text in the middle
    75 % vertically, when positioning is simple
  - no SMIL (animate/animateTransform/animateMotion/animateColor/set)
  - PNG decode errors
A translucent draft and unknown font metrics only WARN.

Geometry only understands translate offsets and a single x/y; a rotated or
scaled element is still contrast-checked, but its overflow/safe-area is skipped
with a WARN rather than guessed.

Usage: python3 scripts/svg_check.py draft.svg [--video]
Exit 0 clean (warnings allowed); exit 1 on a failure. Prints WARN lines.

A byte-identical copy lives in motion-video-agent's skill scripts directory;
the two skills install from separate subdirectories, so it cannot be shared
across them. Keep them in sync (ponytail: accepted duplication).
"""
import argparse
import copy
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zlib

LARGE_PX = 24.0
LARGE_BOLD_PX = 18.66
NEED_NORMAL = 4.5     # the WARN threshold for normal-size text
SPECK_MIN = 5         # pixels; a smaller component is anti-alias, not a glyph
EDGE_PX = 60.0
CHAR_W = 0.6  # rough advance per character, in em
SMIL = {"animate", "animateTransform", "animateMotion", "animateColor", "set"}
SIMPLE = re.compile(r"^(?:[a-zA-Z][\w-]*|\.[\w-]+|#[\w-]+)$")
ET.register_namespace("", "http://www.w3.org/2000/svg")


def local(tag):
    return tag.rsplit("}", 1)[-1]


def num(value, default=0.0):
    try:
        return float(re.match(r"[-+]?[\d.]+", value.strip()).group(0))
    except (AttributeError, TypeError):
        return default


def px(value):
    """A px length, or None when the value is missing or not a plain px number."""
    if value is None:
        return None
    m = re.fullmatch(r"\s*([\d.]+)\s*(?:px)?\s*", value)
    return float(m.group(1)) if m else None


def single(value):
    return value is None or re.fullmatch(r"\s*[-+]?[\d.]+\s*", value) is not None


def decls(text):
    out = {}
    for part in text.split(";"):
        if ":" in part:
            k, v = part.split(":", 1)
            out[k.strip().lower()] = v.strip()
    return out


def walk(root):
    """Yield (element, tx, ty) with group translate offsets accumulated."""
    def visit(el, tx, ty):
        m = re.fullmatch(r"\s*translate\(\s*([-\d.]+)(?:[ ,]+([-\d.]+))?\s*\)\s*",
                         el.get("transform") or "")
        if m:
            tx += float(m.group(1))
            ty += float(m.group(2) or 0)
        yield el, tx, ty
        for child in el:
            yield from visit(child, tx, ty)
    return visit(root, 0.0, 0.0)


def plain_placement(el):
    """True when translate offsets and a single x/y describe the element."""
    if re.sub(r"translate\([^)]*\)", "", el.get("transform") or "").strip():
        return False
    if not (single(el.get("x")) and single(el.get("y"))):
        return False
    return not any(single(ts.get(p)) is False for ts in el.iter()
                   if local(ts.tag) == "tspan" for p in ("x", "y", "dx", "dy"))


def simple_match(part, el):
    if part.startswith("."):
        return part[1:] in (el.get("class") or "").split()
    if part.startswith("#"):
        return part[1:] == el.get("id")
    return part == local(el.tag)


def could_touch(part, el):
    toks = re.split(r"[>+~]", part)
    tail = toks[-1].split() if toks and toks[-1].split() else []
    last = re.sub(r"::?[\w-]+(?:\([^)]*\))?", "", tail[-1] if tail else "")
    m = re.fullmatch(r"([a-zA-Z][\w-]*)?((?:[.#][\w-]+)*)", last)
    if not m:
        return False
    stag, rest = m.group(1), m.group(2)
    if stag and stag != local(el.tag):
        return False
    ids = re.findall(r"#([\w-]+)", rest)
    want = re.findall(r"\.([\w-]+)", rest)
    if ids and el.get("id") not in ids:
        return False
    return all(c in (el.get("class") or "").split() for c in want)


def metric(el, rules, prop):
    """(value, unsure): inline style, then matching simple rules, then attribute."""
    inline = decls(el.get("style", "")).get(prop)
    if inline is not None:
        return inline, False
    chosen, unsure = None, False
    for selector, props in rules:
        if prop not in props:
            continue
        for part in (p.strip() for p in selector.split(",")):
            if not part:
                continue
            if SIMPLE.match(part):
                if simple_match(part, el):
                    chosen = props[prop]
            elif could_touch(part, el):
                unsure = True
    if unsure:
        return None, True
    return (chosen if chosen is not None else el.get(prop)), False


def style_rules(style):
    return [(m.group(1).strip(), decls(m.group(2)))
            for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", style)]


def collect(root):
    style = "".join(el.text for el in root.iter() if local(el.tag) == "style" and el.text)
    rules = style_rules(style)
    vb = root.get("viewBox", "").split()
    if len(vb) == 4 and "%" not in (root.get("width") or "") + (root.get("height") or ""):
        canvas = {"x": num(vb[0]), "y": num(vb[1]), "w": num(vb[2]), "h": num(vb[3])}
    else:
        canvas = {"x": 0.0, "y": 0.0, "w": num(root.get("width")), "h": num(root.get("height"))}
    if len(vb) == 4 and (not canvas["w"] or not canvas["h"]):
        canvas = {"x": num(vb[0]), "y": num(vb[1]), "w": num(vb[2]), "h": num(vb[3])}
    rects, texts, smil = [], [], []
    for el, tx, ty in walk(root):
        tag = local(el.tag)
        if tag in SMIL:
            smil.append(el.get("id") or tag)
        if tag == "rect":
            rects.append({"id": el.get("id", ""), "x": num(el.get("x")) + tx,
                          "y": num(el.get("y")) + ty, "w": num(el.get("width")),
                          "h": num(el.get("height")), "plain": plain_placement(el)})
        elif tag == "text":
            raw, unsure = metric(el, rules, "font-size")
            size = None if unsure else px(raw if raw is not None else "16")
            wraw, wunsure = metric(el, rules, "font-weight")
            arw, aunsure = metric(el, rules, "text-anchor")
            i = len(texts)
            el.set("data-check", "t%d" % i)
            tspans = []
            for ts in el.iter():
                if local(ts.tag) == "tspan" and "".join(ts.itertext()).strip():
                    marker = "t%d-%d" % (i, len(tspans))
                    ts.set("data-check", marker)
                    tspans.append((marker, "".join(ts.itertext()).strip()))
            texts.append({
                "el": el, "marker": "t%d" % i, "tspans": tspans, "plain": plain_placement(el),
                "id": el.get("id", ""), "x": num(el.get("x")) + tx,
                "y": num(el.get("y")) + ty, "size": size, "unsure": unsure,
                "weight_unsure": wunsure, "anchor_unsure": aunsure,
                "bold": (wraw or "").lower() in ("bold", "bolder") or num(wraw or "0") >= 700,
                "anchor": "middle" if (arw or "").strip() == "middle"
                          else "end" if (arw or "").strip() == "end" else "start",
                "content": "".join(el.itertext()).strip(),
            })
    return canvas, rects, texts, smil, style


def text_box(t):
    w = len(t["content"]) * (t["size"] or 0) * CHAR_W
    if t["anchor"] == "middle":
        x = t["x"] - w / 2
    elif t["anchor"] == "end":
        x = t["x"] - w
    else:
        x = t["x"]
    size = t["size"] or 0
    return x, t["y"] - size, w, size * 1.15


def contains(a, b):
    return (a["x"] <= b["x"] + 0.5 and a["y"] <= b["y"] + 0.5
            and a["x"] + a["w"] >= b["x"] + b["w"] - 0.5
            and a["y"] + a["h"] >= b["y"] + b["h"] - 0.5)


def innermost(x, y, rects):
    hits = [r for r in rects if r["w"] > 0 and r["h"] > 0
            and r["x"] <= x <= r["x"] + r["w"] and r["y"] <= y <= r["y"] + r["h"]]
    return min(hits, key=lambda r: r["w"] * r["h"]) if hits else None


# --- PNG decode (stdlib zlib; resvg writes 8-bit, non-interlaced) ------------

def decode_png(path):
    data = open(path, "rb").read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG")
    pos, idat, ihdr = 8, b"", None
    while pos + 8 <= len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        typ, chunk = data[pos + 4:pos + 8], data[pos + 8:pos + 8 + length]
        pos += 12 + length
        if typ == b"IHDR":
            ihdr = struct.unpack(">IIBBBBB", chunk)
        elif typ == b"IDAT":
            idat += chunk
        elif typ == b"IEND":
            break
    if ihdr is None:
        raise ValueError("no IHDR")
    w, h, depth, ctype, _, _, interlace = ihdr
    if depth != 8 or interlace or ctype == 3:
        raise ValueError("unsupported PNG (depth %s, type %s, interlace %s)" % (depth, ctype, interlace))
    ch = {0: 1, 2: 3, 4: 2, 6: 4}[ctype]
    raw, stride, prev, p = zlib.decompress(idat), w * ch, bytearray(w * ch), 0
    out = bytearray()
    for _ in range(h):
        f = raw[p]
        line = bytearray(raw[p + 1:p + 1 + stride])
        p += 1 + stride
        if f == 1:
            for i in range(ch, stride):
                line[i] = (line[i] + line[i - ch]) & 255
        elif f == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 255
        elif f == 3:
            for i in range(stride):
                a = line[i - ch] if i >= ch else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 255
        elif f == 4:
            for i in range(stride):
                a = line[i - ch] if i >= ch else 0
                b = prev[i]
                c = prev[i - ch] if i >= ch else 0
                pa, pb, pc = abs(b - c), abs(a - c), abs(a + b - 2 * c)
                pr = a if pa <= pb and pa <= pc else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 255
        out.extend(line)
        prev = line
    return w, h, ch, bytes(out)


def pixel(raw, ch, i):
    o = i * ch
    if ch == 4:
        r, g, b, a = raw[o], raw[o + 1], raw[o + 2], raw[o + 3]
    elif ch == 3:
        r, g, b, a = raw[o], raw[o + 1], raw[o + 2], 255
    elif ch == 2:
        r = g = b = raw[o]
        a = raw[o + 1]
    else:
        r = g = b = raw[o]
        a = 255
    if a == 255:
        return (r, g, b)
    return ((r * a + 255 * (255 - a)) // 255,
            (g * a + 255 * (255 - a)) // 255,
            (b * a + 255 * (255 - a)) // 255)


def luminance(rgb):
    def chan(c):
        c /= 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (chan(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def diff_changed(full, without):
    """{(row, col): contrast} for pixels that changed when the element was
    removed, or None when it is the same size and nothing changed."""
    fw, fh, fch, fraw = full
    ww, wh, wch, wraw = without
    if (fw, fh) != (ww, wh):
        return None
    changed = {}
    for r in range(fh):
        fo, wo = r * fw * fch, r * ww * wch
        if fch == wch and fraw[fo:fo + fw * fch] == wraw[wo:wo + ww * wch]:
            continue
        for c in range(fw):
            a, b = pixel(fraw, fch, r * fw + c), pixel(wraw, wch, r * ww + c)
            if a != b:
                changed[(r, c)] = contrast(a, b)
    return changed or None


def component_bests(changed):
    """Best contrast per 2-D connected component (4-connectivity)."""
    seen, comps = set(), []
    for start in changed:
        if start in seen:
            continue
        stack, best, n = [start], 0.0, 0
        seen.add(start)
        while stack:
            r, c = stack.pop()
            n += 1
            best = max(best, changed[(r, c)])
            for q in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if q in changed and q not in seen:
                    seen.add(q)
                    stack.append(q)
        if n >= SPECK_MIN:
            comps.append(best)
    return comps or [max(changed.values())]


def contrast_score(changed):
    """Worst 2-D connected component's best contrast. Advisory only: the owner
    confirms contrast by eye on the review page."""
    return min(component_bests(changed))


def has_transparency(full):
    ch, raw = full[2], full[3]
    if ch == 4:
        return min(raw[3::4]) < 255
    if ch == 2:
        return min(raw[1::2]) < 255
    return False


def render(path):
    out = os.path.join(tempfile.mkdtemp(), "r.png")
    return out, subprocess.run(["resvg", path, out], capture_output=True, text=True)


def render_without(root, marker):
    tree = copy.deepcopy(root)
    for parent in tree.iter():
        for child in list(parent):
            if child.get("data-check") == marker:
                parent.remove(child)
                break
    path = os.path.join(tempfile.mkdtemp(), "without.svg")
    ET.ElementTree(tree).write(path, encoding="utf-8", xml_declaration=True)
    return render(path)[0]


def check(path, video=False):
    failures, warnings = [], []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as e:
        return ["not valid SVG/XML: %s" % e], []
    canvas, rects, texts, smil, style = collect(root)

    if re.search(r"fill\s*[:=]\s*[\"']?[^\"'};]*var\(", open(path, encoding="utf-8").read()):
        failures.append("var() in a fill: resvg renders it black; use literal hex with data-token")
    if smil:
        failures.append("SMIL in draft: %s" % ", ".join(smil))

    labelled = [r for r in rects if r["id"] and r["w"] > 0 and r["h"] > 0]
    for r in labelled:
        if not r["plain"]:
            warnings.append("overflow/safe-area not checked (rotated or scaled): #%s" % r["id"])
    for i, a in enumerate(labelled):
        for b in labelled[i + 1:]:
            if not (a["plain"] and b["plain"]) or contains(a, b) or contains(b, a):
                continue
            ox = min(a["x"] + a["w"], b["x"] + b["w"]) - max(a["x"], b["x"])
            oy = min(a["y"] + a["h"], b["y"] + b["h"]) - max(a["y"], b["y"])
            if ox > 2 and oy > 2:
                failures.append("overlap: #%s x #%s (%dx%d px)" % (a["id"], b["id"], ox, oy))

    for t in texts:
        name = "#" + t["id"] if t["id"] else "'" + t["content"][:16] + "'"
        if t["unsure"] or (t["size"] is None and t["content"]):
            warnings.append("font size unknown: %s (put font-size inline or in a simple rule)" % name)
        if t["weight_unsure"]:
            warnings.append("font weight unknown: %s" % name)
        if t["anchor_unsure"]:
            warnings.append("text anchor unknown: %s" % name)
        if t["content"] and not t["plain"]:
            warnings.append("overflow/safe-area not checked (rotated or scaled): %s" % name)
        if not t["content"] or t["size"] is None or not t["plain"]:
            continue
        x, y, w, h = text_box(t)
        box = innermost(t["x"], t["y"], rects)
        if box and (x < box["x"] - 2 or y < box["y"] - 2
                    or x + w > box["x"] + box["w"] + 2 or y + h > box["y"] + box["h"] + 2):
            failures.append("text overflow: %s runs past %s"
                            % (name, "#" + box["id"] if box["id"] else "its box"))
        if canvas["w"] and canvas["h"] and (x < canvas["x"] - 1 or y < canvas["y"] - 1
                                            or x + w > canvas["x"] + canvas["w"] + 1
                                            or y + h > canvas["y"] + canvas["h"] + 1):
            failures.append("text overflow: %s runs past the frame" % name)

    if video and canvas["w"] and canvas["h"]:
        portrait = canvas["h"] > canvas["w"]
        boxes = [(r["id"], r["x"], r["y"], r["w"], r["h"]) for r in labelled if r["plain"]]
        boxes += [(t["id"] or t["content"][:16], *text_box(t))
                  for t in texts if t["content"] and t["size"] and t["plain"]]
        for eid, x, y, w, h in boxes:
            if w >= canvas["w"] and h >= canvas["h"]:
                continue
            left, top = x - canvas["x"], y - canvas["y"]
            right, bottom = canvas["x"] + canvas["w"] - (x + w), canvas["y"] + canvas["h"] - (y + h)
            if left < EDGE_PX or top < EDGE_PX or right < EDGE_PX or bottom < EDGE_PX:
                failures.append("safe area: #%s within %.0fpx of an edge" % (eid, EDGE_PX))
            if portrait and not canvas["y"] + canvas["h"] * 0.125 <= y + h / 2 <= canvas["y"] + canvas["h"] * 0.875:
                failures.append("safe area: #%s outside middle 75%% vertically" % eid)

    if not shutil.which("resvg"):
        failures.append("resvg not found; install it (brew install resvg)")
        return failures, warnings
    full_png, r = render(path)
    if r.returncode != 0:
        return failures + ["resvg failed: %s" % (r.stderr.strip() or "exit %d" % r.returncode)], warnings
    for line in r.stderr.strip().splitlines():
        if "fallback" in line.lower():
            warnings.append("font fallback, advisory (name a font that covers it): %s" % line)
        else:
            failures.append("resvg warning: %s" % line)
    try:
        full = decode_png(full_png)
    except (ValueError, OSError) as e:
        return failures + ["PNG decode failed: %s" % e], warnings
    if has_transparency(full):
        warnings.append("no opaque background: the draft is translucent; the review page shows "
                        "light or dark, so contrast is unknown")

    for t in texts:
        if not t["content"]:
            continue
        name = "#" + t["id"] if t["id"] else "'" + t["content"][:16] + "'"
        need = 3.0 if (t["size"] or 0) >= LARGE_PX or (t["bold"] and (t["size"] or 0) >= LARGE_BOLD_PX) else NEED_NORMAL
        passes = [(t["marker"], name)] + [
            (marker, "%s tspan '%s'" % (name, text[:16])) for marker, text in t["tspans"]]
        for marker, part in passes:
            try:
                without = decode_png(render_without(root, marker))
            except (ValueError, OSError) as e:
                failures.append("PNG decode failed: %s" % e)
                break
            changed = diff_changed(full, without)
            if changed is None:
                warnings.append("text not visible, advisory: %s" % part)
                continue
            score = contrast_score(changed)
            if score < need:
                warnings.append("contrast %.2f:1, advisory — check by eye on the review page: %s"
                                % (score, part))
    return failures, warnings


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("svg")
    ap.add_argument("--video", action="store_true", help="apply video safe-area rules")
    args = ap.parse_args()
    failures, warnings = check(args.svg, video=args.video)
    for line in failures:
        print(line)
    for line in warnings:
        print("WARN: " + line)
    if failures:
        sys.exit(1)
    print(("clean with %d warning(s): %s" if warnings else "clean: %s")
          % ((len(warnings), args.svg) if warnings else args.svg))


if __name__ == "__main__":
    main()
