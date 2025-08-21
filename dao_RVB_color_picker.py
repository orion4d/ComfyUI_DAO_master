# -*- coding: utf-8 -*-
# ComfyUI_DAO_master / dao_RVB_color_picker.py
# RVB Color Picker + seed & modes (Manual / Random / Increment / Decrement)
# Fichiers de liste: ./RGB_List/*.txt, lignes: [Nom]{R, G, B}

import os, re, random, time
import torch
from aiohttp import web
from server import PromptServer

class DAORVBColorPicker:
    CATEGORY = "DAO_master/Color"
    FUNCTION = "pick"
    # image, hex, R, V, B, RVB, mask
    RETURN_TYPES = ("IMAGE", "STRING", "STRING", "STRING", "STRING", "STRING", "MASK")
    RETURN_NAMES = ("image", "hex", "R", "V", "B", "RVB", "mask")
    OUTPUT_NODE = False

    MODES = ["Manual", "Random", "Increment", "Decrement"]
    _CACHE = {}  # path -> (mtime, [(name, (R,G,B)), ...])

    # ----------------------------- UI schema -----------------------------
    @classmethod
    def INPUT_TYPES(cls):
        # list_file / color restent des STRING (menus gérés par JS → pas de "value not in list")
        return {
            "required": {
                "list_file": ("STRING", {"default": "", "multiline": False}),
                "color": ("STRING", {"default": "", "multiline": False}),  # "Nom R, G, B" ou "R, G, B"
                "mode": (cls.MODES, {"default": "Manual"}),
                "seed": ("INT", {"default": 0, "min": -2_147_483_648, "max": 2_147_483_647, "step": 1}),
                "width": ("INT", {"default": 64, "min": 1, "max": 4096, "step": 8}),
                "height": ("INT", {"default": 64, "min": 1, "max": 4096, "step": 8}),
            },
            "optional": {
                "mask": ("MASK",),
            }
        }

    # ----------------------------- Helpers -------------------------------
    @classmethod
    def _lists_dir(cls):
        return os.path.join(os.path.dirname(__file__), "RGB_List")

    @classmethod
    def _ensure_lists_dir(cls):
        d = cls._lists_dir()
        os.makedirs(d, exist_ok=True)
        return d

    @classmethod
    def _available_txts(cls):
        d = cls._ensure_lists_dir()
        try:
            return sorted([f for f in os.listdir(d) if f.lower().endswith(".txt")], key=str.lower)
        except Exception:
            return []

    @staticmethod
    def _clip8(x):
        try:
            return max(0, min(255, int(x)))
        except Exception:
            return 0

    @staticmethod
    def _parse_line(line: str):
        """
        Accepte:
          [Nom]{R, G, B}
          {R, G, B}[Nom]
        Ignore lignes vides, débutant par # ou //.
        """
        s = (line or "").strip()
        if not s or s.startswith("#") or s.startswith("//"):
            return None

        # Match R,G,B où R,G,B ∈ [-999..999] puis clamp 0..255
        rgx1 = re.search(r"\[\s*([^\]]+)\s*\]\s*\{\s*(-?\d{1,3})\s*,\s*(-?\d{1,3})\s*,\s*(-?\d{1,3})\s*\}", s)
        rgx2 = re.search(r"\{\s*(-?\d{1,3})\s*,\s*(-?\d{1,3})\s*,\s*(-?\d{1,3})\s*\}\s*\[\s*([^\]]+)\s*\]", s)

        if rgx1:
            name = (rgx1.group(1) or "").strip()
            r, g, b = (DAORVBColorPicker._clip8(rgx1.group(i)) for i in (2, 3, 4))
            return (name, (r, g, b))
        if rgx2:
            r, g, b = (DAORVBColorPicker._clip8(rgx2.group(i)) for i in (1, 2, 3))
            name = (rgx2.group(4) or "").strip()
            return (name, (r, g, b))
        return None

    @classmethod
    def _load_colors_from_file(cls, filename: str):
        if not filename:
            return []
        path = os.path.join(cls._ensure_lists_dir(), filename)
        if not os.path.isfile(path):
            return []
        try:
            mtime = os.path.getmtime(path)
            cached = cls._CACHE.get(path)
            if cached and cached[0] == mtime:
                return cached[1]
            pairs = []
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    p = cls._parse_line(line)
                    if p:
                        pairs.append(p)
            cls._CACHE[path] = (mtime, pairs)
            return pairs
        except Exception:
            return []

    @staticmethod
    def _rgb_to_hex(r, g, b):
        return f"#{int(r):02X}{int(g):02X}{int(b):02X}"

    @staticmethod
    def _rgb_to01(r, g, b):
        return (float(r) / 255.0, float(g) / 255.0, float(b) / 255.0)

    @staticmethod
    def _extract_rgb_from_string(s: str):
        """
        Extrait 3 entiers depuis une chaîne "Nom R, G, B" ou "R, G, B"
        """
        if not s:
            return None
        m = re.search(r"(-?\d{1,3})\s*,\s*(-?\d{1,3})\s*,\s*(-?\d{1,3})", str(s))
        if not m:
            return None
        r, g, b = (DAORVBColorPicker._clip8(m.group(i)) for i in (1, 2, 3))
        return (r, g, b)

    # ----------------------------- Execute -------------------------------
    def pick(self, list_file, color, mode, seed, width, height, mask=None):
        # Détermine le triplet RVB
        rgb = None

        if mode == "Manual" or not list_file:
            rgb = self._extract_rgb_from_string(color) if color else None
        else:
            items = self._load_colors_from_file(list_file)
            if items:
                n = len(items)
                if mode == "Random":
                    base = seed if seed != 0 else int(time.time_ns() & 0x7FFFFFFF)
                    idx = random.Random(base).randrange(n)
                elif mode == "Increment":
                    idx = (seed % n + n) % n
                elif mode == "Decrement":
                    idx = ((-seed) % n + n) % n
                else:
                    idx = 0
                rgb = items[idx][1]

        if not rgb:
            rgb = (255, 255, 255)

        r8, g8, b8 = rgb
        hex_str = self._rgb_to_hex(r8, g8, b8)
        r01, g01, b01 = self._rgb_to01(r8, g8, b8)

        # Image couleur unie
        img = torch.zeros((1, int(height), int(width), 3), dtype=torch.float32)
        img[:, :, :, 0] = r01
        img[:, :, :, 1] = g01
        img[:, :, :, 2] = b01

        # Mask sortie (reprend mask si fourni, sinon masque blanc de la taille de l'image)
        if mask is not None:
            mask_out = mask
        else:
            mask_out = torch.ones((1, int(height), int(width)), dtype=torch.float32)

        # Sorties strings
        r_s, g_s, b_s = str(r8), str(g8), str(b8)
        rgb_s = f"{r8}, {g8}, {b8}"

        return (img, hex_str, r_s, g_s, b_s, rgb_s, mask_out)

# ----------------------------- HTTP API --------------------------------
def _register_routes_once():
    ps = PromptServer.instance
    if getattr(ps, "_dao_rvb_picker_routes", False):
        return

    async def rvb_files(request):
        files = DAORVBColorPicker._available_txts()
        return web.json_response({"files": files})

    async def rvb_colors(request):
        filename = request.query.get("file", "")
        items = DAORVBColorPicker._load_colors_from_file(filename) if filename else []
        # format d’affichage: "Nom R, G, B"
        options = [f"{n} {r},{g},{b}" for n, (r, g, b) in items]
        return web.json_response({"colors": options})

    ps.routes.get("/dao/rvb_picker/files")(rvb_files)
    ps.routes.get("/dao/rvb_picker/colors")(rvb_colors)
    ps._dao_rvb_picker_routes = True

try:
    _register_routes_once()
except Exception as e:
    print(f"[DAO RVB Picker] Route registration error: {e}")
