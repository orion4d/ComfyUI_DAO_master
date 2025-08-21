# -*- coding: utf-8 -*-
# ComfyUI_DAO_master / dao_hex_color_picker.py
# Hex Color Picker + seed & modes (Manual / Random / Increment / Decrement)

import os, re, random, time
import torch
from aiohttp import web
from server import PromptServer

class DAOHexColorPicker:
    CATEGORY = "DAO_master/Color"
    FUNCTION = "pick"
    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("image", "hex")
    OUTPUT_NODE = False

    MODES = ["Manual", "Random", "Increment", "Decrement"]
    _CACHE = {}  # path -> (mtime, [(name, #HEX), ...])

    # ----------------------------- UI schema -----------------------------
    @classmethod
    def INPUT_TYPES(cls):
        # list_file / color restent des STRING (menus gérés par JS → pas de "value not in list")
        return {
            "required": {
                "list_file": ("STRING", {"default": "", "multiline": False}),
                "color": ("STRING", {"default": "", "multiline": False}),  # utilisé en mode Manual
                "mode": (cls.MODES, {"default": "Manual"}),
                "seed": ("INT", {"default": 0, "min": -2_147_483_648, "max": 2_147_483_647, "step": 1}),
                "width": ("INT", {"default": 64, "min": 1, "max": 4096, "step": 8}),
                "height": ("INT", {"default": 64, "min": 1, "max": 4096, "step": 8}),
            }
        }

    # ----------------------------- Helpers -------------------------------
    @classmethod
    def _lists_dir(cls):
        return os.path.join(os.path.dirname(__file__), "hexadecimal_List")

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
    def _parse_line(line: str):
        s = (line or "").strip()
        if not s or s.startswith("#") or s.startswith("//"):
            return None
        # [Nom]{#RRGGBB}  ou  {#RRGGBB}[Nom]
        m = (re.search(r"\[\s*([^\]]+)\s*\]\s*\{\s*(#?[0-9a-f]{6,8})\s*\}", s, re.I)
             or re.search(r"\{\s*(#?[0-9a-f]{6,8})\s*\}\s*\[\s*([^\]]+)\s*\]", s, re.I))
        if not m:
            return None
        g = m.groups()
        if len(g) != 2:
            return None
        # ordonner (name, hex) indépendamment de l'ordre rencontré
        if s.find('[') < s.find('{'):
            name, hx = g[0], g[1]
        else:
            name, hx = g[1], g[0]
        name = (name or "").strip()
        hx = (hx or "").strip().upper()
        if not hx.startswith("#"):
            hx = "#" + hx
        if not re.fullmatch(r"#([0-9A-F]{6}|[0-9A-F]{8})", hx):
            return None
        return (name, hx)

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
    def _hex_to_rgb01(hx: str):
        hx = (hx or "").strip().lstrip("#").upper()
        if len(hx) >= 6:
            r = int(hx[0:2], 16) / 255.0
            g = int(hx[2:4], 16) / 255.0
            b = int(hx[4:6], 16) / 255.0
            return (r, g, b)
        return (1.0, 1.0, 1.0)

    # ----------------------------- Execute -------------------------------
    def pick(self, list_file, color, mode, seed, width, height):
        chosen_hex = None

        if mode == "Manual" or not list_file:
            # `color` attendu style "Nom #RRGGBB" ou "#RRGGBB"
            m = re.search(r"#([0-9A-F]{6,8})", str(color).upper()) if color else None
            chosen_hex = "#" + m.group(1)[:6] if m else "#FFFFFF"
        else:
            items = self._load_colors_from_file(list_file)
            if items:
                n = len(items)
                if mode == "Random":
                    # Seed randomisé si 0 → plus pratique
                    base = seed if seed != 0 else int(time.time_ns() & 0x7FFFFFFF)
                    idx = random.Random(base).randrange(n)
                elif mode == "Increment":
                    idx = (seed % n + n) % n
                elif mode == "Decrement":
                    idx = ((-seed) % n + n) % n
                else:
                    idx = 0
                chosen_hex = items[idx][1]
            else:
                chosen_hex = "#FFFFFF"

        r, g, b = self._hex_to_rgb01(chosen_hex)
        img = torch.zeros((1, int(height), int(width), 3), dtype=torch.float32)
        img[:, :, :, 0] = r
        img[:, :, :, 1] = g
        img[:, :, :, 2] = b
        return (img, chosen_hex)

# ----------------------------- HTTP API --------------------------------
def _register_routes_once():
    ps = PromptServer.instance
    if getattr(ps, "_dao_hex_picker_routes", False):
        return

    async def dao_hex_files(request):
        files = DAOHexColorPicker._available_txts()
        return web.json_response({"files": files})

    async def dao_hex_colors(request):
        filename = request.query.get("file", "")
        items = DAOHexColorPicker._load_colors_from_file(filename) if filename else []
        return web.json_response({"colors": [f"{n} {h}" for n, h in items]})

    ps.routes.get("/dao/hex_picker/files")(dao_hex_files)
    ps.routes.get("/dao/hex_picker/colors")(dao_hex_colors)
    ps._dao_hex_picker_routes = True

try:
    _register_routes_once()
except Exception as e:
    print(f"[DAO Hex Picker] Route registration error: {e}")
