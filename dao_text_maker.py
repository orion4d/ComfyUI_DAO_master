# -*- coding: utf-8 -*-
# DAO Text Maker — IMAGE + SVG + MASK, alpha en %, largeur alpha, vectorisation "holes safe"

import os, re
import numpy as np
from aiohttp import web
from server import PromptServer

try:
    import torch
except Exception:
    torch = None

from PIL import Image, ImageDraw, ImageFont

# Vectorisation propre (polygones) pour Illustrator
try:
    from matplotlib.textpath import TextPath
    from matplotlib.font_manager import FontProperties
    _HAS_MPL = True
except Exception:
    _HAS_MPL = False


# ---------- helpers ----------

_HEX_ANY = re.compile(r"#([0-9A-Fa-f]{3,8})")

def _rgb_from_any_hex(s: str, default=(0, 0, 0)):
    """Extrait le 1er #hex (#RGB/#RGBA/#RRGGBB/#RRGGBBAA)."""
    if not s:
        return default
    m = _HEX_ANY.search(str(s))
    if not m:
        return default
    h = m.group(1)
    try:
        if len(h) == 3:       # RGB
            r, g, b = (int(c*2, 16) for c in h)
        elif len(h) == 4:     # RGBA -> ignore A
            r, g, b, _ = (int(c*2, 16) for c in h)
        elif len(h) == 6:     # RRGGBB
            r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
        else:                 # RRGGBBAA
            r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
        return (r, g, b)
    except Exception:
        return default

def _alpha_pct_to_01(a):
    """
    Accepte 0..100 (%) ou 0..1 (fraction). Convertit en [0,1].
    """
    try:
        v = float(a)
    except Exception:
        return 1.0
    if v <= 1.0:
        return max(0.0, min(1.0, v))
    return max(0.0, min(1.0, v / 100.0))

def _to_tensor_rgb(img: Image.Image):
    arr = np.asarray(img, dtype=np.float32) / 255.0
    if arr.ndim == 2:
        arr = np.stack([arr, arr, arr], axis=-1)
    arr = arr[..., :3]
    return torch.from_numpy(arr).unsqueeze(0) if torch is not None else arr[None, ...]

def _to_tensor_mask(mask: Image.Image):
    arr = np.asarray(mask, dtype=np.float32) / 255.0
    return torch.from_numpy(arr).unsqueeze(0) if torch is not None else arr[None, ...]

def _load_font(font_path: str, size: int):
    try:
        if font_path and os.path.isfile(font_path):
            return ImageFont.truetype(font_path, size=size, layout_engine=ImageFont.Layout.BASIC)
    except Exception:
        pass
    try:
        return ImageFont.load_default()
    except Exception:
        return None


# ---------- SVG builders ----------

def _make_svg_text(lines, width, height, font_family, font_size,
                   fill_hex, fill_alpha, stroke_hex, stroke_width, stroke_alpha, align):
    ta = {"center": "middle", "left": "start", "right": "end"}.get(align, "middle")
    x = width // 2 if ta == "middle" else (0 if ta == "start" else width)
    line_h = font_size * 1.2
    start_y = height/2 - (len(lines)-1)*line_h/2

    fill = (fill_hex or "#000000").strip()
    stroke = (stroke_hex or "#000000").strip()
    fill_op = _alpha_pct_to_01(fill_alpha)
    stroke_op = _alpha_pct_to_01(stroke_alpha)

    tspans = []
    for i, ln in enumerate(lines):
        dy = 0 if i == 0 else line_h
        esc = ln.replace("&","&amp;").replace("<","&lt;")
        if i == 0:
            tspans.append(f'<tspan x="{x}" y="{start_y:.2f}">{esc}</tspan>')
        else:
            tspans.append(f'<tspan x="{x}" dy="{dy:.2f}">{esc}</tspan>')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
  <g>
    <text text-anchor="{ta}" dominant-baseline="middle"
          font-family="{font_family}" font-size="{font_size}"
          fill="{fill}" fill-opacity="{fill_op}"
          stroke="{stroke}" stroke-width="{stroke_width}"
          stroke-opacity="{stroke_op}">{''.join(tspans)}</text>
  </g>
</svg>'''

def _make_svg_paths(lines, width, height, font_path, font_size,
                    fill_hex, fill_alpha, stroke_hex, stroke_width, stroke_alpha, align):
    """
    Vectorisation robuste : 1 seul <path> par ligne, trous OK (evenodd),
    et alignements 'left' / 'center' / 'right' identiques à PIL.
    """
    if not _HAS_MPL:
        ff = os.path.basename(font_path) if font_path else "sans-serif"
        return _make_svg_text(lines, width, height, ff, font_size,
                              fill_hex, fill_alpha, stroke_hex, stroke_width, stroke_alpha, align)

    # --- couleurs / opacités ---
    fill = (fill_hex or "#000000").strip()
    stroke = (stroke_hex or "#000000").strip()
    fill_op = _alpha_pct_to_01(fill_alpha)
    stroke_op = _alpha_pct_to_01(stroke_alpha)

    # --- font pour TextPath (vecteur) ---
    fp = FontProperties(fname=font_path if font_path else None, size=font_size)

    # --- font PIL pour mesurer la largeur "logique" (comme PIL dessine) ---
    try:
        pil_font = ImageFont.truetype(font_path, size=font_size, layout_engine=ImageFont.Layout.BASIC) \
                   if font_path else ImageFont.load_default()
    except Exception:
        pil_font = ImageFont.load_default()
    dummy = Image.new("L", (1, 1))
    draw = ImageDraw.Draw(dummy)

    # --- placement vertical (milieu de ligne) ---
    line_h = font_size * 1.2
    start_y = height/2 - (len(lines)-1)*line_h/2

    def poly_to_d(poly, tx, ty):
        if len(poly) == 0:
            return ""
        parts = []
        for j, (x, y) in enumerate(poly):
            X = x + tx
            Ysvg = height - (y + ty)      # inversion Y pour SVG
            parts.append(("M" if j == 0 else "L") + f" {X:.3f} {Ysvg:.3f}")
        parts.append("Z")
        return " ".join(parts)

    paths = []
    for i, ln in enumerate(lines):
        if not ln:
            continue

        # 1) largeur mesurée à la PIL (comme le rendu bitmap)
        #    -> textbbox avec ancre 'lm' (left/middle) à x=0 donne un bbox
        #       dont la largeur correspond à la logique PIL.
        bx0, by0, bx1, by1 = draw.textbbox((0, 0), ln, font=pil_font, anchor="lm")
        logical_w = bx1 - bx0

        # 2) position horizontale désirée selon align (en coordonnées canvas)
        if align == "left":
            desired_left = 0.0
        elif align == "right":
            desired_left = float(width) - float(logical_w)
        else:  # center
            desired_left = float(width)/2.0 - float(logical_w)/2.0

        # 3) géométrie réelle des contours (TextPath)
        tp = TextPath((0, 0), ln, prop=fp, size=font_size)
        bb = tp.get_extents()
        cx = (bb.x0 + bb.x1) / 2.0
        cy = (bb.y0 + bb.y1) / 2.0

        # 4) translation horizontale : on veut que le bord gauche du contour
        #    (bb.x0) tombe sur desired_left -> tx = desired_left - bb.x0
        tx = desired_left - bb.x0

        # 5) translation verticale : on veut que le centre vertical tombe à dest_cy
        dest_cy = start_y + i * line_h
        ty = (height - dest_cy) - cy  # correspond au flip Y dans poly_to_d

        # 6) concatène les sous-polygones de la ligne en un seul path
        d_all = []
        for poly in tp.to_polygons():
            d = poly_to_d(np.asarray(poly), tx, ty)
            if d:
                d_all.append(d)
        if not d_all:
            continue

        d_str = " ".join(d_all)
        paths.append(
            f'<path d="{d_str}" fill="{fill}" fill-opacity="{fill_op}" '
            f'stroke="{stroke}" stroke-width="{stroke_width}" stroke-opacity="{stroke_op}" '
            f'fill-rule="evenodd" clip-rule="evenodd"/>'
        )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">
  <g>{''.join(paths)}</g>
</svg>'''

# ---------- node ----------

class DAOTextMaker:
    CATEGORY = "DAO_master/Text"
    FUNCTION = "render"
    RETURN_TYPES = ("IMAGE", "SVG_TEXT", "MASK")
    RETURN_NAMES = ("image", "svg", "mask")
    OUTPUT_NODE = False

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"default": "HELLO DAO!\nTEST", "multiline": True}),
                "font_file": ("STRING", {"default": "", "multiline": False}),
                "font_size": ("INT", {"default": 128, "min": 4, "max": 4096}),
                "canvas_width": ("INT", {"default": 1024, "min": 16, "max": 8192, "step": 1}),
                "canvas_height": ("INT", {"default": 512, "min": 16, "max": 8192, "step": 1}),

                # Couleurs / alpha (en %)
                "fill_hex": ("STRING", {"default": "#FFFFFF"}),
                "fill_alpha": ("FLOAT", {"default": 100.0, "min": 0.0, "max": 100.0}),

                # Contour visuel
                "stroke_width": ("INT", {"default": 0, "min": 0, "max": 256}),
                "stroke_hex": ("STRING", {"default": "#000000"}),
                "stroke_alpha": ("FLOAT", {"default": 100.0, "min": 0.0, "max": 100.0}),

                # Fond
                "bg_transparent": ("BOOLEAN", {"default": True}),
                "bg_hex": ("STRING", {"default": "#000000"}),

                # Alignement / SVG / sortie
                "align": (["center", "left", "right"], {"default": "center"}),
                "svg_vectorize": ("BOOLEAN", {"default": True}),
                "image_rgba": ("BOOLEAN", {"default": True}),

                # Epaisseur supplémentaire du MASK (n’influence pas le rendu visuel)
                "stroke_width_alpha": ("INT", {"default": 0, "min": 0, "max": 256}),
            }
        }

    # Fonts utils
    @classmethod
    def _fonts_dir(cls):
        return os.path.join(os.path.dirname(__file__), "Fonts")
    @classmethod
    def _ensure_fonts_dir(cls):
        d = cls._fonts_dir(); os.makedirs(d, exist_ok=True); return d
    @classmethod
    def _available_fonts(cls):
        d = cls._ensure_fonts_dir()
        try:
            return sorted([f for f in os.listdir(d) if f.lower().endswith((".ttf",".otf",".ttc",".otc"))], key=str.lower)
        except Exception:
            return []

    def render(self, text, font_file, font_size, canvas_width, canvas_height,
               fill_hex, fill_alpha, stroke_width, stroke_hex, stroke_alpha,
               bg_transparent, bg_hex, align, svg_vectorize, image_rgba,
               stroke_width_alpha):

        W = int(canvas_width); H = int(canvas_height)
        fill_rgb   = _rgb_from_any_hex(fill_hex, default=(255,255,255))
        stroke_rgb = _rgb_from_any_hex(stroke_hex, default=(0,0,0))
        bg_rgb     = _rgb_from_any_hex(bg_hex, default=(0,0,0))
        fill_op   = _alpha_pct_to_01(fill_alpha)
        stroke_op = _alpha_pct_to_01(stroke_alpha)
        stroke_w  = max(0, int(stroke_width))
        grow_alpha = max(0, int(stroke_width_alpha))

        # Police
        font_path = font_file
        if font_path and not os.path.isabs(font_path):
            font_path = os.path.join(self._fonts_dir(), font_path)
        font = _load_font(font_path, int(font_size)) or ImageFont.load_default()

        # --- calque texte (RGBA) pour rendu visuel ---
        text_rgba = Image.new("RGBA", (W, H), (0,0,0,0))
        draw = ImageDraw.Draw(text_rgba)

        lines = (text or "").splitlines() or [""]
        line_h = int(font_size * 1.2)
        start_y = H/2 - (len(lines)-1)*line_h/2
        anchor = {"center":"mm", "left":"lm", "right":"rm"}[align]
        x = W//2 if align=="center" else (0 if align=="left" else W)

        for i, ln in enumerate(lines):
            y = start_y + i*line_h
            draw.text(
                (x, y), ln, font=font,
                fill=(fill_rgb[0], fill_rgb[1], fill_rgb[2], int(round(fill_op*255))),
                stroke_width=stroke_w,
                stroke_fill=(stroke_rgb[0], stroke_rgb[1], stroke_rgb[2], int(round(stroke_op*255))),
                anchor=anchor
            )

        # --- MASK : forme du texte avec marge alpha supplémentaire ---
        mask_L = Image.new("L", (W, H), 0)
        mdraw = ImageDraw.Draw(mask_L)
        for i, ln in enumerate(lines):
            y = start_y + i*line_h
            mdraw.text(
                (x, y), ln, font=font,
                fill=255,
                stroke_width=stroke_w + grow_alpha,  # << épaisseur supplémentaire uniquement sur le MASK
                stroke_fill=255,
                anchor=anchor
            )
        mask_out = _to_tensor_mask(mask_L)

        # --- compose fond + texte (pour sortie IMAGE) ---
        if bg_transparent:
            base = Image.new("RGBA", (W, H), (0,0,0,0))
        else:
            base = Image.new("RGBA", (W, H), (bg_rgb[0], bg_rgb[1], bg_rgb[2], 255))
        rgba = Image.alpha_composite(base, text_rgba)

        # IMAGE de sortie
        if bg_transparent and image_rgba:
            arr = (np.asarray(rgba, dtype=np.float32) / 255.0)  # HxWx4
            image_out = torch.from_numpy(arr).unsqueeze(0) if torch is not None else arr[None, ...]
        else:
            image_out = _to_tensor_rgb(rgba.convert("RGB"))

        # --- SVG ---
        if svg_vectorize:
            svg = _make_svg_paths(lines, W, H, font_path, int(font_size),
                                  fill_hex, fill_alpha, stroke_hex, stroke_w, stroke_alpha, align)
        else:
            svg = _make_svg_text(lines, W, H,
                                 font_family=os.path.basename(font_path) if font_path else "sans-serif",
                                 font_size=int(font_size),
                                 fill_hex=fill_hex, fill_alpha=fill_alpha,
                                 stroke_hex=stroke_hex, stroke_width=stroke_w, stroke_alpha=stroke_alpha,
                                 align=align)

        return (image_out, svg, mask_out)


# ---------- HTTP (fonts listing) ----------

def _register_routes_once():
    ps = PromptServer.instance
    if getattr(ps, "_dao_text_maker_routes", False):
        return
    async def list_fonts(request):
        files = DAOTextMaker._available_fonts()
        return web.json_response({"fonts": files})
    ps.routes.get("/dao/text/fonts")(list_fonts)
    ps._dao_text_maker_routes = True

try:
    _register_routes_once()
except Exception as e:
    print(f"[DAO Text Maker] Route registration error: {e}")
