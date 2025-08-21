# ComfyUI_DXF/dxf_utils.py
import time, ezdxf, torch
import numpy as np
from dataclasses import dataclass
from typing import Tuple, List, Optional, Any
from PIL import Image, ImageDraw, ImageChops
import ezdxf.path  # pour make_path(...)

@dataclass
class DXFDoc:
    doc: Any
    msp: Any
    units: str

_UNIT_TO_INSUNITS = {"unitless":0,"inch":1,"foot":2,"mile":3,"mm":4,"cm":5,"m":6,"px":0}

def _set_units(doc, units: str):
    doc.header["$INSUNITS"] = _UNIT_TO_INSUNITS.get(units, 0)

def _bbox_from_entities(msp) -> Optional[Tuple[float, float, float, float]]:
    """Boîte englobante manuelle, compatible CIRCLE/LINE/LW(POLYLINE)/ELLIPSE/SPLINE/ARC."""
    minx = miny = float("inf")
    maxx = maxy = float("-inf")
    found = False

    for e in msp:
        try:
            t = e.dxftype()
            if t == "CIRCLE":
                cx, cy, r = e.dxf.center.x, e.dxf.center.y, e.dxf.radius
                minx, maxx = min(minx, cx - r), max(maxx, cx + r)
                miny, maxy = min(miny, cy - r), max(maxy, cy + r)
                found = True

            elif t == "LINE":
                start, end = e.dxf.start, e.dxf.end
                for pt in (start, end):
                    minx, maxx = min(minx, pt.x), max(maxx, pt.x)
                    miny, maxy = min(miny, pt.y), max(maxy, pt.y)
                found = True

            elif t in ("LWPOLYLINE", "POLYLINE", "ELLIPSE", "SPLINE", "ARC"):
                path = ezdxf.path.make_path(e)
                # tolérance de flattening : plus petit = plus précis
                vertices = list(path.flattening(0.1))
                if vertices:
                    for v in vertices:
                        minx, maxx = min(minx, v.x), max(maxx, v.x)
                        miny, maxy = min(miny, v.y), max(maxy, v.y)
                    found = True
        except Exception:
            continue

    if not found:
        return None
    if maxx - minx < 1e-9:
        maxx += 1.0
    if maxy - miny < 1e-9:
        maxy += 1.0
    return (minx, miny, maxx, maxy)

def _world_to_image(points, bbox, size, margin=24):
    minx, miny, maxx, maxy = bbox
    w, h = maxx - minx, maxy - miny
    if w <= 0: w = 1.0
    if h <= 0: h = 1.0
    scale = max(1e-9, (size - 2 * margin) / max(w, h))
    ox, oy = (size - w * scale) * 0.5, (size - h * scale) * 0.5
    return [
        (int(round((x - minx) * scale + ox)),
         int(round((maxy - y) * scale + oy)))
        for x, y in points
    ]

def _parse_hex_color(s, default=(0, 0, 0, 255)):
    s = (s or "").strip().lstrip("#")
    try:
        if len(s) == 3:
            r, g, b, a = int(s[0]*2,16), int(s[1]*2,16), int(s[2]*2,16), 255
        elif len(s) == 6:
            r, g, b, a = int(s[0:2],16), int(s[2:4],16), int(s[4:6],16), 255
        elif len(s) == 8:
            r, g, b, a = int(s[0:2],16), int(s[2:4],16), int(s[4:6],16), int(s[6:8],16)
        else:
            return default
        return r, g, b, a
    except:
        return default

def _draw_grid(draw, size):
    step = max(32, size // 16)
    col = (225, 225, 225)
    for i in range(0, size, step):
        draw.line([(i, 0), (i, size-1)], fill=col)
        draw.line([(0, i), (size-1, i)], fill=col)

def _render_internal_rgb_and_mask(
    msp, size, line_width, stroke_hex, fill_enabled, fill_hex,
    bg_enabled, bg_hex, show_grid, want_transparent
):
    lw = int(max(0, line_width))
    sr, sg, sb, _ = _parse_hex_color(stroke_hex)
    fr, fg, fb, fa = _parse_hex_color(fill_hex)
    br, bgc, bb, _ = _parse_hex_color(bg_hex)

    stroke_color = (sr, sg, sb) if lw > 0 else None
    do_fill = bool(fill_enabled and fa > 0)
    fill_color = (fr, fg, fb)

    temp_bg_rgb = (br, bgc, bb) if (bg_enabled and not want_transparent) else (255, 255, 255)
    rgb_image = Image.new("RGB", (size, size), temp_bg_rgb)
    draw = ImageDraw.Draw(rgb_image, "RGB")

    # masque final (opacité) pour la sortie mask/transparence
    mask = Image.new("L", (size, size), 0)
    mdraw = ImageDraw.Draw(mask, "L")

    # masque 1 bit pour le remplissage pair-impair (XOR)
    fill_parity = Image.new("1", (size, size), 0)

    if show_grid and (bg_enabled and not want_transparent):
        _draw_grid(draw, size)

    bbox = _bbox_from_entities(msp)
    if bbox is None:
        img = Image.new("RGBA" if want_transparent else "RGB",
                        (size, size),
                        (0, 0, 0, 0) if want_transparent else temp_bg_rgb)
        return (img, mask)

    margin = 24

    closed_polys = []     # listes de points (pixels) pour polygones fermés
    closed_ellipses = []  # rectangles [x0,y0,x1,y1] pour cercles/ellipses

    for e in msp:
        t = e.dxftype()

        if t in ("LWPOLYLINE", "POLYLINE", "ELLIPSE", "SPLINE", "ARC"):
            path = ezdxf.path.make_path(e)
            pts_w = [(v.x, v.y) for v in path.flattening(distance=0.1)]
            if len(pts_w) >= 2:
                pix = _world_to_image(pts_w, bbox, size, margin)

                # fermé ?
                closed = False
                if hasattr(e, "is_closed"):
                    closed = bool(e.is_closed)
                if hasattr(e, "closed"):
                    closed = closed or bool(e.closed)
                # ellipse complète => fermé
                if t == "ELLIPSE" and getattr(e.dxf, "start_param", None) is None and getattr(e.dxf, "end_param", None) is None:
                    closed = True
                # spline/polyligne sans flag : test 1er/dernier point très proches
                if not closed and len(pts_w) >= 3:
                    x0,y0 = pts_w[0]; x1,y1 = pts_w[-1]
                    if (abs(x0-x1) + abs(y0-y1)) < 1e-6:
                        closed = True
                # un ARC n'est jamais fermé
                if t == "ARC":
                    closed = False

                if closed and len(pix) >= 3:
                    closed_polys.append(pix)
                    # contour
                    if stroke_color:
                        draw.line(pix + [pix[0]], fill=stroke_color, width=lw)
                        mdraw.line(pix + [pix[0]], fill=255, width=lw)
                else:
                    if stroke_color:
                        draw.line(pix, fill=stroke_color, width=lw)
                        mdraw.line(pix, fill=255, width=lw)

        elif t == "CIRCLE":
            cx, cy, r = float(e.dxf.center.x), float(e.dxf.center.y), float(e.dxf.radius)
            (x0, y0), (x1, y1) = _world_to_image([(cx - r, cy - r), (cx + r, cy + r)], bbox, size, margin)
            if x0 > x1: x0, x1 = x1, x0
            if y0 > y1: y0, y1 = y1, y0
            closed_ellipses.append([x0, y0, x1, y1])
            if stroke_color:
                draw.ellipse([x0, y0, x1, y1], outline=stroke_color, width=lw)
                mdraw.ellipse([x0, y0, x1, y1], outline=255, width=lw)

        elif t == "LINE":
            pix = _world_to_image([(e.dxf.start.x, e.dxf.start.y),
                                   (e.dxf.end.x,   e.dxf.end.y)], bbox, size, margin)
            if stroke_color:
                draw.line(pix, fill=stroke_color, width=lw)
                mdraw.line(pix, fill=255, width=lw)

    # ---- Remplissage pair-impair (fait le "trou") ----
    if do_fill:
        # polygones fermés
        for poly in closed_polys:
            tmp = Image.new("1", (size, size), 0)
            ImageDraw.Draw(tmp, "1").polygon(poly, fill=1)
            fill_parity = ImageChops.logical_xor(fill_parity, tmp)
        # cercles/ellipses
        for rect in closed_ellipses:
            tmp = Image.new("1", (size, size), 0)
            ImageDraw.Draw(tmp, "1").ellipse(rect, fill=1)
            fill_parity = ImageChops.logical_xor(fill_parity, tmp)

        # applique la couleur de fond dans les zones impaires (donut)
        fill_mask = fill_parity.convert("L").point(lambda p: 255 if p else 0)
        rgb_image.paste(fill_color, mask=fill_mask)
        mask.paste(255, mask=fill_mask)

    if want_transparent:
        final_image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        final_image.paste(rgb_image, (0, 0), mask)
        return final_image, mask
    else:
        return rgb_image, mask

def _to_image_tensor(img):
    img_conv = img.convert("RGBA") if img.mode == 'RGBA' else img.convert("RGB")
    arr = np.array(img_conv).astype(np.float32) / 255.0
    return torch.from_numpy(arr).unsqueeze(0)

def _to_mask_tensor(mask):
    arr = np.array(mask.convert("L")).astype(np.float32) / 255.0
    return torch.from_numpy(arr).unsqueeze(0)

class _BaseAdd:
    @classmethod
    def IS_CHANGED(cls, **kwargs): return time.time_ns()
