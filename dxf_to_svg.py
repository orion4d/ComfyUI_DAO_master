# ComfyUI_DXF/dxf_to_svg.py
import os
import time
import math
from typing import List, Tuple

import ezdxf
import ezdxf.path
from svgpathtools import Path as SvgPath, Line

from .dxf_utils import DXFDoc, _bbox_from_entities


# ---------------------------- Géométrie utils ---------------------------- #

def _dist2(a: complex, b: complex) -> float:
    dx = (a.real - b.real)
    dy = (a.imag - b.imag)
    return dx * dx + dy * dy


def _poly_to_svgpath(poly: List[complex], closed: bool) -> SvgPath:
    p = SvgPath()
    if len(poly) < 2:
        return p
    for i in range(len(poly) - 1):
        p.append(Line(poly[i], poly[i + 1]))
    if closed:
        p.append(Line(poly[-1], poly[0]))
    return p


def _iter_all_entities(msp):
    """
    Itère les entités du DXF, en 'dépliant' les INSERT (BLOCKs) si possible.
    """
    for e in msp:
        if e.dxftype() == "INSERT":
            try:
                for ve in e.virtual_entities():
                    yield ve
            except Exception:
                yield e
        else:
            yield e


def _flatten_entity_to_poly(entity, flat_tol: float) -> List[complex]:
    """
    Aplati une entité DXF en une polyline (liste de points complexes).
    Retourne [] si l'entité n'est pas supportée.
    """
    try:
        path = ezdxf.path.make_path(entity)
        verts = list(path.flattening(distance=flat_tol))
        if len(verts) < 2:
            return []
        return [complex(v.x, v.y) for v in verts]
    except Exception:
        return []


def _join_polylines(polys: List[List[complex]], close_tol2: float) -> Tuple[List[List[complex]], List[List[complex]]]:
    """
    Assemble les polylines par leurs extrémités si elles se touchent (tolérance),
    puis sépare en (closed_loops, open_paths).
    """

    def _dedup(p: List[complex]) -> List[complex]:
        out = []
        prev = None
        for q in p:
            if prev is None or _dist2(prev, q) > 0.0:
                out.append(q)
                prev = q
        return out

    polys = [_dedup(p) for p in polys if len(p) >= 2]

    # Fusion progressive par extrémités qui coïncident (à tolérance près)
    changed = True
    while changed:
        changed = False
        i = 0
        while i < len(polys):
            a = polys[i]
            a0, a1 = a[0], a[-1]
            merged = False
            j = i + 1
            while j < len(polys):
                b = polys[j]
                b0, b1 = b[0], b[-1]

                if _dist2(a1, b0) <= close_tol2:
                    polys[i] = a + b[1:]
                    polys.pop(j); merged = True; changed = True; break
                elif _dist2(a1, b1) <= close_tol2:
                    polys[i] = a + list(reversed(b[:-1]))
                    polys.pop(j); merged = True; changed = True; break
                elif _dist2(a0, b0) <= close_tol2:
                    polys[i] = list(reversed(a[1:])) + b
                    polys.pop(j); merged = True; changed = True; break
                elif _dist2(a0, b1) <= close_tol2:
                    polys[i] = b + a[1:]
                    polys.pop(j); merged = True; changed = True; break
                else:
                    j += 1

            if not merged:
                i += 1

    closed, openp = [], []
    for p in polys:
        if len(p) >= 3 and _dist2(p[0], p[-1]) <= close_tol2:
            # évite d'avoir deux fois le même point en fin/début
            if _dist2(p[0], p[-1]) == 0.0:
                closed.append(p[:-1])
            else:
                closed.append(p)
        else:
            openp.append(p)
    return closed, openp


def _msp_to_compound_paths(msp, flat_tol: float, close_tol: float):
    """
    Convertit l'espace modèle en (closed_svg_paths, open_svg_paths)
    en fusionnant les segments et en fermant les boucles si nécessaire.
    """
    polylines: List[List[complex]] = []
    for e in _iter_all_entities(msp):
        pts = _flatten_entity_to_poly(e, flat_tol)
        if pts:
            polylines.append(pts)

    closed_loops, open_paths = _join_polylines(polylines, close_tol * close_tol)

    closed_svg = [_poly_to_svgpath(p, closed=True) for p in closed_loops]
    open_svg = [_poly_to_svgpath(p, closed=False) for p in open_paths]
    return closed_svg, open_svg


# ---------------------------- Node ComfyUI ---------------------------- #

class DxfToSvg:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "dxf": ("DXF",),

            # 1..100 : plus grand = courbes plus précises (tolérance d'aplatissement plus faible)
            "curve_quality": ("INT", {"default": 50, "min": 1, "max": 100}),

            # Échelle de la viewBox (zoom "virtuel")
            "scale": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 10.0, "step": 0.05}),

            # Marge autour du dessin (en % de la plus grande dimension)
            "padding_percent": ("FLOAT", {"default": 5.0, "min": 0.0, "max": 50.0, "step": 1.0}),

            # Tolérance de fermeture (en % de la taille du dessin). 0 => auto.
            "close_tolerance_percent": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0, "step": 0.005}),

            # Règle de remplissage (gestion des trous)
            "fill_rule": (["evenodd", "nonzero"], {"default": "evenodd"}),

            # Sortie fichier (optionnelle)
            "directory": ("STRING", {"default": "output/svg"}),
            "filename": ("STRING", {"default": "shape.svg"}),
            "timestamp_suffix": ("BOOLEAN", {"default": True}),
            "save_file": ("BOOLEAN", {"default": True}),
        }}

    RETURN_TYPES = ("SVG_TEXT", "STRING")
    RETURN_NAMES = ("svg_text", "path")
    FUNCTION = "convert"
    CATEGORY = "DAO_master/SVG/Convert"

    def convert(self, dxf: DXFDoc,
                curve_quality: int,
                scale: float,
                padding_percent: float,
                close_tolerance_percent: float,
                fill_rule: str,
                directory: str,
                filename: str,
                timestamp_suffix: bool,
                save_file: bool):

        # --- 1) Tolérances ---
        # Aplatissement (1→100) ~ 1.0 → 0.001
        flat_tol = 1.0 / (curve_quality ** 1.5)

        # Taille du dessin (pour close tolerance & viewBox)
        bbox = _bbox_from_entities(dxf.msp)
        if bbox is None:
            min_x = min_y = 0.0
            width = height = 100.0
            diag = 100.0
        else:
            min_x, min_y, max_x, max_y = bbox
            width, height = (max_x - min_x), (max_y - min_y)
            diag = max(width, height)

        # Tolérance de fermeture (en unités DXF)
        if close_tolerance_percent and close_tolerance_percent > 0.0:
            close_tol = diag * (close_tolerance_percent / 100.0)
        else:
            # auto : un mélange de taille & tolérance d'aplatissement
            close_tol = max(diag * 1e-4, flat_tol * diag * 0.25)

        # --- 2) ViewBox (centrée + padding + scale) ---
        if bbox is None:
            center_x, center_y = 50.0, 50.0
        else:
            center_x, center_y = min_x + width / 2.0, min_y + height / 2.0

        width = max(width, 1e-9) / max(scale, 1e-9)
        height = max(height, 1e-9) / max(scale, 1e-9)
        padding = max(width, height) * (padding_percent / 100.0)

        min_x = center_x - width / 2.0 - padding
        min_y = center_y - height / 2.0 - padding
        width += 2.0 * padding
        height += 2.0 * padding

        # --- 3) Chemins fermés/ouvert (avec assemblage tolérant) ---
        closed_svg, open_svg = _msp_to_compound_paths(dxf.msp, flat_tol, close_tol)

        # --- 4) Flip Y pour SVG ---
        flip_center_y = min_y + height / 2.0

        # --- 5) Construction du SVG ---
        svg_lines = []
        svg_lines.append(
            f'<svg viewBox="{min_x} {min_y} {width} {height}" xmlns="http://www.w3.org/2000/svg">'
        )
        svg_lines.append(
            f'  <g transform="translate(0 {2 * flip_center_y}) scale(1 -1)">'
        )

        # Boucles fermées fusionnées -> trous via fill-rule
        if closed_svg:
            parts = []
            for p in closed_svg:
                d = p.d()
                if not d.strip().lower().endswith('z'):
                    d += ' Z'
                parts.append(d)
            compound_d = " ".join(parts).strip()
            svg_lines.append(f'    <path d="{compound_d}" fill-rule="{fill_rule}" />')

        # Chemins ouverts -> traits (pas de fill)
        for p in open_svg:
            svg_lines.append(f'    <path d="{p.d()}" fill="none" />')

        svg_lines.append('  </g>')
        svg_lines.append('</svg>')
        svg_content = "\n".join(svg_lines)

        # --- 6) Écriture fichier optionnelle ---
        out_path = ""
        if save_file:
            os.makedirs(directory, exist_ok=True)
            base, ext = os.path.splitext(filename)
            ext = ext or ".svg"

            if timestamp_suffix:
                stamp = time.strftime("%Y%m%d_%H%M%S")
                final_path = os.path.join(directory, f"{base}_{stamp}{ext}")
            else:
                final_path = os.path.join(directory, base + ext)

            candidate = final_path
            i = 1
            while os.path.exists(candidate):
                candidate = (f"{os.path.splitext(final_path)[0]}_{i}.svg"
                             if timestamp_suffix else
                             os.path.join(directory, f"{base}_{i}{ext}"))
                i += 1

            with open(candidate, "w", encoding="utf-8") as f:
                f.write(svg_content)
            out_path = os.path.abspath(candidate)

        return svg_content, out_path


NODE_CLASS_MAPPINGS = {"DXF to SVG": DxfToSvg}
NODE_DISPLAY_NAME_MAPPINGS = {"DXF to SVG": "Convertisseur DXF vers SVG"}
