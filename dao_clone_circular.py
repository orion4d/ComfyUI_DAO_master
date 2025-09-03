# -*- coding: utf-8 -*-
# ComfyUI_DAO_master / dao_clone_circular.py
#
# DAO Clone Circular
# - Centre automatiquement l’anneau au milieu du canvas.
# - radius = distance du centre aux clones.
# - rotate = rotation globale (phase) de l’anneau, en degrés.
# - object_rotation = rotation de chaque sprite autour de lui-même.
# - use_background (BOOLEAN) + background_hex (#RGB, #RRGGBB, #RRGGBBAA, "white", "black", "transparent").
# - Entrée mask (optionnelle) pour découper le sprite source.
# - Sortie mask = union des clones.
#
# Sorties:
#   IMAGE: [1,H,W,4] en 0..1
#   MASK : [1,H,W]   en 0..1
#
# Dépendances: Pillow, numpy, torch

import math
from typing import Optional
from PIL import Image, ImageChops
import numpy as np
import torch

# ---------- Utils robustes ----------

def _image_to_rgba_pil(t: torch.Tensor) -> Image.Image:
    """
    Accepte: [B,H,W,C], [H,W,C], [C,H,W]  (C=1/3/4), 0..1
    Retourne PIL RGBA.
    """
    if t is None:
        raise ValueError("Image tensor is None")

    if t.dim() == 4:  # [B,H,W,C]
        t = t[0]
    if t.dim() != 3:
        raise ValueError("Expected 3D or 4D tensor for image")

    # [C,H,W] -> [H,W,C]
    if t.shape[0] in (1, 3, 4) and (t.shape[-1] not in (1, 3, 4)):
        t = t.permute(1, 2, 0)

    if t.shape[-1] not in (1, 3, 4):
        raise ValueError(f"Unsupported channel count: {t.shape[-1]}")

    arr = t.detach().cpu().float().clamp(0, 1).numpy()  # [H,W,C]

    if arr.shape[-1] == 1:  # gray -> RGBA
        arr = np.repeat(arr, 3, axis=-1)
        a = np.ones((*arr.shape[:2], 1), dtype=arr.dtype)
        arr = np.concatenate([arr, a], axis=-1)
    elif arr.shape[-1] == 3:  # RGB -> RGBA
        a = np.ones((*arr.shape[:2], 1), dtype=arr.dtype)
        arr = np.concatenate([arr, a], axis=-1)

    u8 = (arr * 255.0 + 0.5).astype(np.uint8)
    return Image.fromarray(u8, mode="RGBA")


def _mask_to_L(mask_t: Optional[torch.Tensor], size) -> Optional[Image.Image]:
    """
    MASK attendu: [H,W] ou [1,H,W] ou [B,H,W], valeurs 0..1
    Retourne PIL 'L' 0..255 de la taille demandée (redimensionné si besoin).
    """
    if mask_t is None:
        return None

    t = mask_t
    if t.dim() == 3:  # [B,H,W] ou [1,H,W]
        t = t[0]
    if t.dim() != 2:
        raise ValueError("Mask must be 2D or 3D [1,H,W]")

    arr = t.detach().cpu().float().clamp(0, 1).numpy()  # [H,W]
    u8 = (arr * 255.0 + 0.5).astype(np.uint8)
    m = Image.fromarray(u8, mode="L")
    if m.size != size:
        m = m.resize(size, Image.LANCZOS)
    return m


def _rgba_pil_to_tensor(img: Image.Image) -> torch.Tensor:
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    arr = np.array(img).astype(np.float32) / 255.0  # [H,W,4]
    return torch.from_numpy(arr).unsqueeze(0)  # [1,H,W,4]


def _maskL_to_tensor(maskL: Image.Image) -> torch.Tensor:
    arr = np.array(maskL).astype(np.float32) / 255.0  # [H,W]
    return torch.from_numpy(arr).unsqueeze(0)  # [1,H,W]


def _parse_hex(color: str):
    """
    Accepte #RGB, #RRGGBB, #RRGGBBAA, et noms: white, black, transparent, none
    Retourne (r,g,b,a) en 0..255
    """
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

    # #RGB -> #RRGGBB
    if len(s) == 4:
        s = "#" + "".join(ch * 2 for ch in s[1:])

    if len(s) == 7:   # #RRGGBB
        r = int(s[1:3], 16); g = int(s[3:5], 16); b = int(s[5:7], 16); a = 255
    elif len(s) == 9: # #RRGGBBAA
        r = int(s[1:3], 16); g = int(s[3:5], 16); b = int(s[5:7], 16); a = int(s[7:9], 16)
    else:
        r, g, b, a = 0, 0, 0, 0
    return (r, g, b, a)


def _make_canvas(w: int, h: int, use_bg: bool, bg_hex: str) -> Image.Image:
    return Image.new("RGBA", (w, h), _parse_hex(bg_hex) if use_bg else (0, 0, 0, 0))


def _transform_sprite(sprite_rgba: Image.Image, mask_L: Optional[Image.Image],
                      scale: float, object_rotation: float, opacity: float) -> Image.Image:
    """
    Applique: mask (multiplie alpha), scale, rotation objet, opacity.
    Retourne un RGBA prêt à coller.
    """
    img = sprite_rgba

    # 1) appliquer mask sur alpha si fourni
    if mask_L is not None:
        r, g, b, a = img.split()
        # multiply alpha by mask (redimensionnée au sprite)
        if mask_L.size != img.size:
            m = mask_L.resize(img.size, Image.LANCZOS)
        else:
            m = mask_L
        a = ImageChops.multiply(a, m)
        img = Image.merge("RGBA", (r, g, b, a))

    # 2) scale
    if scale != 1.0:
        sw, sh = img.size
        img = img.resize((max(1, int(sw * scale)), max(1, int(sh * scale))), Image.LANCZOS)

    # 3) rotation objet
    if object_rotation != 0.0:
        img = img.rotate(object_rotation, expand=True, resample=Image.BICUBIC)

    # 4) opacity
    if opacity < 1.0:
        r, g, b, a = img.split()
        a = a.point(lambda v: int(v * opacity))
        img = Image.merge("RGBA", (r, g, b, a))

    return img


# --------------- NODE: DAO Clone Circular ---------------

class DAOCloneCircular:
    """
    Clone un sprite sur un cercle centré au canvas.
    - Le centre est (canvas_width/2, canvas_height/2).
    - `radius` est la distance du centre aux clones.
    - `rotate` décale l'anneau (phase) en degrés.
    - `object_rotation` fait tourner chaque sprite sur lui-même.
    - Entrée optionnelle MASK pour découper le sprite source.
    - Sorties: IMAGE (RGBA) + MASK (union des clones).
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
            },
            "optional": {
                "mask": ("MASK",),
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
        image: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
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
    ):
        sprite_rgba = _image_to_rgba_pil(image)
        mask_L_src = _mask_to_L(mask, sprite_rgba.size)

        base = _make_canvas(canvas_width, canvas_height, use_background, background_hex)
        mask_canvas = Image.new("L", (canvas_width, canvas_height), 0)

        if count > 50000:
            raise ValueError("Trop de clones (limite 50k)")

        # centre du canvas
        cx = canvas_width / 2.0
        cy = canvas_height / 2.0

        # Pré-transformations invariantes pour tous les clones
        base_sprite = _transform_sprite(
            sprite_rgba, mask_L_src, scale=scale, object_rotation=object_rotation, opacity=opacity
        )
        sw, sh = base_sprite.size

        # distribution angulaire uniforme 0..360 + phase 'rotate'
        for i in range(count):
            ang = (i / count) * 360.0 + rotate
            rad = math.radians(ang)

            x = cx + radius * math.cos(rad) - sw / 2.0
            y = cy + radius * math.sin(rad) - sh / 2.0

            # coller RGBA
            base.alpha_composite(base_sprite, (int(x), int(y)))

            # construire un alpha placé pour le mask de sortie
            _, _, _, a = base_sprite.split()
            placed = Image.new("L", (canvas_width, canvas_height), 0)
            placed.paste(a, (int(x), int(y)), a)
            mask_canvas = ImageChops.lighter(mask_canvas, placed)  # union (max)

        out_img = _rgba_pil_to_tensor(base)
        out_mask = _maskL_to_tensor(mask_canvas)
        return (out_img, out_mask)
