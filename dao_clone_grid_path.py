# -*- coding: utf-8 -*-
# ComfyUI_DAO_master / dao_clone_grid_path.py
#
# DAO Clone Grid Path
# - Charge des PNG/JPG d'un dossier (tri alpha), 1 image par clone
# - Boucle si pas assez, tronque si trop
# - shuffle + seed pour ordre aléatoire reproductible
# - Grille simple: count_x/count_y, spacing_x/y, offset_x/y
# - Décalages alternés: row_offset_x (lignes impaires), col_offset_y (colonnes impaires)
# - Canvas indépendant par défaut (custom)
#
# Sorties:
#   IMAGE: [1,H,W,4] en 0..1
#   MASK : [1,H,W]   en 0..1

import os, random
from typing import List
from PIL import Image, ImageChops
import numpy as np
import torch

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
    arr = np.array(img).astype(np.float32) / 255.0
    return torch.from_numpy(arr).unsqueeze(0)

def _maskL_to_tensor(maskL: Image.Image) -> torch.Tensor:
    arr = np.array(maskL).astype(np.float32) / 255.0
    return torch.from_numpy(arr).unsqueeze(0)

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

def _transform_sprite(sprite_rgba: Image.Image, scale: float, rotation_deg: float, opacity: float) -> Image.Image:
    img = sprite_rgba
    if scale != 1.0:
        sw, sh = img.size
        img = img.resize((max(1, int(sw * scale)), max(1, int(sh * scale))), Image.LANCZOS)
    if rotation_deg != 0.0:
        img = img.rotate(rotation_deg, expand=True, resample=Image.BICUBIC)
    if opacity < 1.0:
        r, g, b, a = img.split()
        a = a.point(lambda v: int(v * opacity))
        img = Image.merge("RGBA", (r, g, b, a))
    return img

class DAOCloneGridPath:
    """
    Grille basée dossier, avec décalages alternés.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "folder_path": ("STRING", {"default": ""}),
                # Canvas
                "canvas_mode": (["custom", "auto_from_grid"], {"default": "custom"}),
                "canvas_width": ("INT", {"default": 1024, "min": 1, "max": 32768}),
                "canvas_height": ("INT", {"default": 1024, "min": 1, "max": 32768}),
                "use_background": ("BOOLEAN", {"default": False}),
                "background_hex": ("STRING", {"default": "#00000000"}),
                # Layout
                "count_x": ("INT", {"default": 4, "min": 1, "max": 4096}),
                "count_y": ("INT", {"default": 4, "min": 1, "max": 4096}),
                "spacing_x": ("INT", {"default": 20, "min": -10000, "max": 10000}),
                "spacing_y": ("INT", {"default": 20, "min": -10000, "max": 10000}),
                "offset_x": ("INT", {"default": 0, "min": -10000, "max": 10000}),
                "offset_y": ("INT", {"default": 0, "min": -10000, "max": 10000}),
                "row_offset_x": ("INT", {"default": 0, "min": -10000, "max": 10000}),
                "col_offset_y": ("INT", {"default": 0, "min": -10000, "max": 10000}),
                # Apparence
                "rotation": ("FLOAT", {"default": 0.0, "min": -1440.0, "max": 1440.0, "step": 0.1}),
                "scale": ("FLOAT", {"default": 1.0, "min": 0.01, "max": 10.0, "step": 0.01}),
                "opacity": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                # Random
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
        canvas_mode: str = "custom",
        canvas_width: int = 1024,
        canvas_height: int = 1024,
        use_background: bool = False,
        background_hex: str = "#00000000",
        count_x: int = 4,
        count_y: int = 4,
        spacing_x: int = 20,
        spacing_y: int = 20,
        offset_x: int = 0,
        offset_y: int = 0,
        row_offset_x: int = 0,
        col_offset_y: int = 0,
        rotation: float = 0.0,
        scale: float = 1.0,
        opacity: float = 1.0,
        shuffle: bool = False,
        seed: int = 0,
    ):
        files = _list_images_sorted(folder_path)
        total_needed = count_x * count_y
        if shuffle:
            rnd = random.Random(seed)
            rnd.shuffle(files)
        if len(files) > total_needed:
            files = files[:total_needed]

        # Sprite de référence (pour step), basé sur la première image du set
        ref_sprite = _open_rgba(files[0])
        ref_sprite = _transform_sprite(ref_sprite, scale=scale, rotation_deg=rotation, opacity=opacity)
        sw, sh = ref_sprite.size

        # Canvas
        if canvas_mode == "auto_from_grid":
            cw = offset_x + count_x * sw + max(0, count_x - 1) * spacing_x + max(0, row_offset_x)
            ch = offset_y + count_y * sh + max(0, count_y - 1) * spacing_y + max(0, col_offset_y)
        else:  # custom
            cw, ch = canvas_width, canvas_height

        base = _make_canvas(cw, ch, use_background, background_hex)
        mask_canvas = Image.new("L", (cw, ch), 0)

        step_x = sw + spacing_x
        step_y = sh + spacing_y

        idx = 0
        N = len(files)

        for j in range(count_y):
            for i in range(count_x):
                path = files[idx % N]
                idx += 1

                sprite = _open_rgba(path)
                sprite = _transform_sprite(sprite, scale=scale, rotation_deg=rotation, opacity=opacity)
                ssw, ssh = sprite.size

                x = offset_x + i * step_x
                y = offset_y + j * step_y
                if row_offset_x != 0 and (j % 2 == 1):
                    x += row_offset_x
                if col_offset_y != 0 and (i % 2 == 1):
                    y += col_offset_y

                # centrer sur la "cell" (optionnel) : ici on cale en haut-gauche pour rester strict
                # Si on voulait centrer : x += (sw - ssw)//2 ; y += (sh - ssh)//2

                base.alpha_composite(sprite, (int(x), int(y)))

                # union mask
                _, _, _, a = sprite.split()
                placed = Image.new("L", (cw, ch), 0)
                placed.paste(a, (int(x), int(y)), a)
                mask_canvas = ImageChops.lighter(mask_canvas, placed)

        out_img = _rgba_pil_to_tensor(base)
        out_mask = _maskL_to_tensor(mask_canvas)
        return (out_img, out_mask)
