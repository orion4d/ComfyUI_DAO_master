# -*- coding: utf-8 -*-
# ComfyUI_DAO_master / dao_clone_circular_path.py
#
# DAO Clone Circular Path
# - Charge des PNG/JPG d'un dossier (tri alpha), 1 image par clone
# - Boucle si pas assez, tronque si trop
# - shuffle + seed pour ordre aléatoire reproductible
# - Anneau centré: radius, count, rotate (phase), object_rotation (par sprite), scale, opacity
# - use_background (BOOLEAN) + background_hex
#
# Sorties:
#   IMAGE: [1,H,W,4] en 0..1
#   MASK : [1,H,W]   en 0..1

import os, math, random
from typing import List, Optional
from PIL import Image, ImageChops
import numpy as np
import torch

# ---------- Utils fichiers & images ----------

_EXTS = {".png", ".jpg", ".jpeg"}

def _list_images_sorted(folder: str) -> List[str]:
    if not folder or not os.path.isdir(folder):
        raise ValueError(f"Dossier introuvable: {folder}")
    files = []
    for name in os.listdir(folder):
        p = os.path.join(folder, name)
        if os.path.isfile(p):
            ext = os.path.splitext(name)[1].lower()
            if ext in _EXTS:
                files.append(p)
    if not files:
        raise ValueError(f"Aucune image .png/.jpg/.jpeg trouvée dans: {folder}")
    files.sort(key=lambda s: os.path.basename(s).lower())
    return files

def _open_rgba(path: str) -> Image.Image:
    img = Image.open(path)
    return img.convert("RGBA")

def _rgba_pil_to_tensor(img: Image.Image) -> torch.Tensor:
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    arr = np.array(img).astype(np.float32) / 255.0  # [H,W,4]
    return torch.from_numpy(arr).unsqueeze(0)  # [1,H,W,4]

def _maskL_to_tensor(maskL: Image.Image) -> torch.Tensor:
    arr = np.array(maskL).astype(np.float32) / 255.0  # [H,W]
    return torch.from_numpy(arr).unsqueeze(0)  # [1,H,W]

def _parse_hex(color: str):
    if not color:
        return (0, 0, 0, 0)
    s = color.strip().lower()
    named = {
        "white": "#ffffff",
        "black": "#000000",
        "transparent": "#00000000",
        "none": "#00000000",
    }
    if s in named:
        s = named[s]
    if not s.startswith("#"):
        s = "#" + s
    if len(s) == 4:
        s = "#" + "".join(ch * 2 for ch in s[1:])
    if len(s) == 7:
        r = int(s[1:3], 16); g = int(s[3:5], 16); b = int(s[5:7], 16); a = 255
    elif len(s) == 9:
        r = int(s[1:3], 16); g = int(s[3:5], 16); b = int(s[5:7], 16); a = int(s[7:9], 16)
    else:
        r, g, b, a = 0, 0, 0, 0
    return (r, g, b, a)

def _make_canvas(w: int, h: int, use_bg: bool, bg_hex: str) -> Image.Image:
    return Image.new("RGBA", (w, h), _parse_hex(bg_hex) if use_bg else (0, 0, 0, 0))

def _transform_sprite(sprite_rgba: Image.Image, scale: float, object_rotation: float, opacity: float) -> Image.Image:
    img = sprite_rgba
    if scale != 1.0:
        sw, sh = img.size
        img = img.resize((max(1, int(sw * scale)), max(1, int(sh * scale))), Image.LANCZOS)
    if object_rotation != 0.0:
        img = img.rotate(object_rotation, expand=True, resample=Image.BICUBIC)
    if opacity < 1.0:
        r, g, b, a = img.split()
        a = a.point(lambda v: int(v * opacity))
        img = Image.merge("RGBA", (r, g, b, a))
    return img

# --------------- NODE ---------------

class DAOCloneCircularPath:
    """
    Clonage circulaire basé dossier.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "folder_path": ("STRING", {"default": ""}),
                "canvas_width": ("INT", {"default": 1024, "min": 1, "max": 32768}),
                "canvas_height": ("INT", {"default": 1024, "min": 1, "max": 32768}),
                "use_background": ("BOOLEAN", {"default": False}),
                "background_hex": ("STRING", {"default": "#00000000"}),
                "radius": ("FLOAT", {"default": 300.0, "min": 0.0, "max": 100000.0, "step": 1.0}),
                "count": ("INT", {"default": 12, "min": 1, "max": 20000}),
                "rotate": ("FLOAT", {"default": 0.0, "min": -1440.0, "max": 1440.0, "step": 0.1}),
                "object_rotation": ("FLOAT", {"default": 0.0, "min": -1440.0, "max": 1440.0, "step": 0.1}),
                "scale": ("FLOAT", {"default": 1.0, "min": 0.01, "max": 10.0, "step": 0.01}),
                "opacity": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "shuffle": ("BOOLEAN", {"default": False}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 2**31-1}),
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("image", "mask")
    FUNCTION = "run"
    CATEGORY = "DAO_master/Images/Clone"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

    def run(
        self,
        folder_path: str,
        canvas_width: int = 1024,
        canvas_height: int = 1024,
        use_background: bool = False,
        background_hex: str = "#00000000",
        radius: float = 300.0,
        count: int = 12,
        rotate: float = 0.0,
        object_rotation: float = 0.0,
        scale: float = 1.0,
        opacity: float = 1.0,
        shuffle: bool = False,
        seed: int = 0,
    ):
        files = _list_images_sorted(folder_path)
        if shuffle:
            rnd = random.Random(seed)
            rnd.shuffle(files)

        # Tronquer au besoin (on bouclera de toute façon via modulo)
        if len(files) > count:
            files = files[:count]

        base = _make_canvas(canvas_width, canvas_height, use_background, background_hex)
        mask_canvas = Image.new("L", (canvas_width, canvas_height), 0)

        if count > 50000:
            raise ValueError("Trop de clones (limite 50k)")

        cx = canvas_width / 2.0
        cy = canvas_height / 2.0

        for i in range(count):
            path = files[i % len(files)]
            sprite = _open_rgba(path)
            sprite = _transform_sprite(sprite, scale=scale, object_rotation=object_rotation, opacity=opacity)
            sw, sh = sprite.size

            ang = (i / count) * 360.0 + rotate
            rad = math.radians(ang)
            x = cx + radius * math.cos(rad) - sw / 2.0
            y = cy + radius * math.sin(rad) - sh / 2.0

            base.alpha_composite(sprite, (int(x), int(y)))

            # Union du mask
            _, _, _, a = sprite.split()
            placed = Image.new("L", (canvas_width, canvas_height), 0)
            placed.paste(a, (int(x), int(y)), a)
            mask_canvas = ImageChops.lighter(mask_canvas, placed)

        out_img = _rgba_pil_to_tensor(base)
        out_mask = _maskL_to_tensor(mask_canvas)
        return (out_img, out_mask)
