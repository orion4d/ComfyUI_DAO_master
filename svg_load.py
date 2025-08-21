# -*- coding: utf-8 -*-
# ComfyUI_DAO_master — SVG Load (avec mise à l’échelle optionnelle)
#
# Entrée : chemin de fichier .svg
# Sortie : SVG_TEXT (+ chemin en bonus)
#
import os
import xml.etree.ElementTree as ET

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)

def _parse_len(val):
    """Essaye d'extraire un float depuis '512', '512px', '200.5'… Retourne None si échec."""
    if val is None:
        return None
    s = str(val).strip().lower()
    # enlève unités courantes sans conversion (px, pt, mm… on ne convertit pas ici)
    for suf in ("px", "pt", "mm", "cm", "in", "pc", "%"):
        if s.endswith(suf):
            s = s[: -len(suf)].strip()
            break
    try:
        return float(s)
    except Exception:
        return None

def _ensure_viewbox(root):
    """Si pas de viewBox mais width/height numériques, crée viewBox='0 0 w h'."""
    if root.get("viewBox"):
        return
    w = _parse_len(root.get("width"))
    h = _parse_len(root.get("height"))
    if w and h and w > 0 and h > 0:
        root.set("viewBox", f"0 0 {w:g} {h:g}")

def _scale_content(root, scale: float, center_on_viewbox: bool):
    """Enveloppe le contenu dans un <g transform='...'> pour mise à l’échelle."""
    if abs(scale - 1.0) < 1e-9:
        return

    # calcule centre (si viewBox) pour scaler autour du centre
    cx = cy = 0.0
    if center_on_viewbox and root.get("viewBox"):
        try:
            minx, miny, w, h = [float(x) for x in root.get("viewBox").replace(",", " ").split()]
            cx = minx + w / 2.0
            cy = miny + h / 2.0
        except Exception:
            cx = cy = 0.0

    g = ET.Element(f"{{{SVG_NS}}}g")
    if cx == 0 and cy == 0:
        g.set("transform", f"scale({scale})")
    else:
        # translate(cx,cy) scale(s) translate(-cx,-cy)
        g.set("transform", f"translate({cx} {cy}) scale({scale}) translate({-cx} {-cy})")

    # déplace tous les enfants existants sous le <g>
    children = list(root)
    for ch in children:
        root.remove(ch)
        g.append(ch)
    root.append(g)

def _scale_canvas(root, scale: float):
    """Multiplie width/height si numériques. Laisse la viewBox telle quelle."""
    if abs(scale - 1.0) < 1e-9:
        return
    w = _parse_len(root.get("width"))
    h = _parse_len(root.get("height"))
    if w and h:
        root.set("width", f"{w * scale:g}")
        root.set("height", f"{h * scale:g}")

class SVGLoad:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "file_path": ("STRING", {"default": "input.svg"}),
            # mise à l'échelle du contenu (groupe <g> avec transform)
            "scale": ("FLOAT", {"default": 1.0, "min": 0.01, "max": 100.0, "step": 0.01}),
            # si true, on scale autour du centre de la viewBox (si disponible)
            "center_on_viewbox": ("BOOLEAN", {"default": True}),
            # en plus, multiplier width/height du canvas si présents
            "scale_canvas": ("BOOLEAN", {"default": False}),
            # crée viewBox depuis width/height si manquant
            "ensure_viewbox": ("BOOLEAN", {"default": True}),
        }}

    RETURN_TYPES = ("SVG_TEXT", "STRING")
    RETURN_NAMES = ("svg_text", "path")
    FUNCTION = "load"
    CATEGORY = "DAO_master/SVG/IO"

    def load(self, file_path: str, scale: float, center_on_viewbox: bool,
             scale_canvas: bool, ensure_viewbox: bool):

        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"SVGLoad: fichier introuvable: {file_path}")

        # lecture brute
        with open(file_path, "r", encoding="utf-8") as f:
            raw = f.read()

        # parse & modifications
        try:
            root = ET.fromstring(raw)
            if ensure_viewbox:
                _ensure_viewbox(root)
            if scale_canvas:
                _scale_canvas(root, scale)
            if scale is not None and scale != 1.0:
                _scale_content(root, scale, center_on_viewbox)

            svg_text = ET.tostring(root, encoding="unicode")
        except Exception:
            # si parse casse (doctype exotique…), renvoie le texte brut
            svg_text = raw

        return (svg_text, os.path.abspath(file_path))


NODE_CLASS_MAPPINGS = {"SVG Load": SVGLoad}
NODE_DISPLAY_NAME_MAPPINGS = {"SVG Load": "SVG Load (fichier → SVG_TEXT)"}
