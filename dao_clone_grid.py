# -*- coding: utf-8 -*-
# ComfyUI_DAO_master / dao_clone_grid.py
#
# DAO Clone Grid (X/Y)
# - Canvas indépendant (par défaut: custom, via canvas_width/height)
# - count_x, count_y : nombre d’objets en X/Y
# - spacing_x, spacing_y : écart (gap) entre objets
# - offset_x, offset_y : position du 1er objet (en haut-gauche)
# - row_offset_x : décalage horizontal appliqué UNE LIGNE SUR DEUX (lignes impaires)
# - col_offset_y : décalage vertical appliqué UNE COLONNE SUR DEUX (colonnes impaires)
# - use_background (BOOLEAN) + background_hex (#RGB, #RRGGBB, #RRGGBBAA, "white", "black", "transparent")
# - mask en entrée (optionnel) ; mask de sortie = union des clones
# - scale, rotation (par objet), opacity
#
# Sorties:
#   IMAGE: [1,H,W,4] en 0..1
#   MASK : [1,H,W]   en 0..1

from typing import Optional, Tuple
import numpy as np
from PIL import Image, ImageChops
import torch

# --------- Utils tensor <-> PIL (robustes) ----------

def _image_to_rgba_pil(t: torch.Tensor) -> Image.Image:
    """
    Accepte: [B,H,W,C], [H,W,C], [C,H,W] (C=1/3/4), 0..1 -> PIL RGBA.
    """
    if t is None:
        raise ValueError("Image tensor is None")

    if t.dim() == 4:   # [B,H,W,C]
        t = t[0]
    if t.dim() != 3:
        raise ValueError("Expected 3D or 4D tensor for image")

    # [C,H,W] -> [H,W,C]
    if t.shape[0] in (1, 3, 4) and (t.shape[-1] not in (1, 3, 4)):
        t = t.permute(1, 2, 0)

    if t.shape[-1] not in (1, 3, 4):
        raise ValueError(f"Unsupported channel count: {t.shape[-1]}")

    arr = t.detach().cpu().float().clamp(0, 1).numpy()  # [H,W,C]
    if arr.shape[-1] == 1:   # Gray -> RGBA
        arr = np.repeat(arr, 3, axis=-1)
        a = np.ones((*arr.shape[:2], 1), dtype=arr.dtype)
        arr = np.concatenate([arr, a], axis=-1)
    elif arr.shape[-1] == 3: # RGB -> RGBA
        a = np.ones((*arr.shape[:2], 1), dtype=arr.dtype)
        arr = np.concatenate([arr, a], axis=-1)

    u8 = (arr * 255.0 + 0.5).astype(np.uint8)
    return Image.fromarray(u8, mode="RGBA")


def _mask_to_L(mask_t: Optional[torch.Tensor], size) -> Optional[Image.Image]:
    """
    MASK attendu: [H,W] ou [1,H,W] ou [B,H,W], 0..1 -> PIL 'L' (0..255)
    """
    if mask_t is None:
        return None

    t = mask_t
    if t.dim() == 3:  # [B,H,W] ou [1,H,W]
        t = t[0]
    if t.dim() != 2:
        raise ValueError("Mask must be 2D or 3D [1,H,W]")

    arr = t.detach().cpu().float().clamp(0, 1).numpy()
    u8 = (arr * 255.0 + 0.5).astype(np.uint8)
    m = Image.fromarray(u8, mode="L")
    if m.size != size:
        m = m.resize(size, Image.LANCZOS)
    return m


def _rgba_pil_to_tensor(img: Image.Image) -> torch.Tensor:
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    arr = np.array(img).astype(np.float32) / 255.0  # [H,W,4]
    return torch.from_numpy(arr).unsqueeze(0)       # [1,H,W,4]


def _maskL_to_tensor(maskL: Image.Image) -> torch.Tensor:
    arr = np.array(maskL).astype(np.float32) / 255.0  # [H,W]
    return torch.from_numpy(arr).unsqueeze(0)         # [1,H,W]


def _parse_hex(color: str):
    """
    #RGB, #RRGGBB, #RRGGBBAA + noms: white, black, transparent, none
    -> tuple (r,g,b,a) 0..255
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
    if len(s) == 4:  # #RGB -> #RRGGBB
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
                      scale: float, rotation_deg: float, opacity: float) -> Image.Image:
    """
    Applique: mask (alpha*=mask), scale, rotation, opacity -> RGBA
    """
    img = sprite_rgba

    # mask sur alpha
    if mask_L is not None:
        r, g, b, a = img.split()
        m = mask_L.resize(img.size, Image.LANCZOS) if mask_L.size != img.size else mask_L
        a = ImageChops.multiply(a, m)
        img = Image.merge("RGBA", (r, g, b, a))

    # scale
    if scale != 1.0:
        sw, sh = img.size
        img = img.resize((max(1, int(sw * scale)), max(1, int(sh * scale))), Image.LANCZOS)

    # rotation par objet
    if rotation_deg != 0.0:
        img = img.rotate(rotation_deg, expand=True, resample=Image.BICUBIC)

    # opacity
    if opacity < 1.0:
        r, g, b, a = img.split()
        a = a.point(lambda v: int(v * opacity))
        img = Image.merge("RGBA", (r, g, b, a))

    return img


def _auto_canvas_size(sprite_size: Tuple[int, int], count_x: int, count_y: int,
                      spacing_x: int, spacing_y: int, offset_x: int, offset_y: int,
                      scale: float) -> Tuple[int, int]:
    """
    Calcule (w,h) = offset + count*size + (count-1)*spacing
    (approximation qui n’intègre pas les décalages alternés ; pratique pour pré-dimensionner)
    """
    sw, sh = sprite_size
    sw = max(1, int(sw * scale))
    sh = max(1, int(sh * scale))
    w = offset_x + count_x * sw + max(0, count_x - 1) * spacing_x
    h = offset_y + count_y * sh + max(0, count_y - 1) * spacing_y
    return max(1, w), max(1, h)


# -------------------- NODE GRID --------------------

class DAOCloneGrid:
    """
    Grille simple & prévisible.
    - Canvas indépendant (par défaut 'custom').
    - Premier clone en haut-gauche (offset_x/offset_y).
    - count_x/count_y + spacing_x/spacing_y.
    - Décalages alternés : row_offset_x (lignes impaires), col_offset_y (colonnes impaires).
    - Entrée mask optionnelle. Sortie mask = union des clones.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
            },
            "optional": {
                "mask": ("MASK",),

                # Canvas
                "canvas_mode": (["custom", "auto_from_grid", "match_input"], {"default": "custom"}),
                "canvas_width": ("INT", {"default": 1024, "min": 1, "max": 32768}),
                "canvas_height": ("INT", {"default": 1024, "min": 1, "max": 32768}),
                "use_background": ("BOOLEAN", {"default": False}),
                "background_hex": ("STRING", {"default": "#00000000"}),

                # Layout basique
                "count_x": ("INT", {"default": 4, "min": 1, "max": 4096}),
                "count_y": ("INT", {"default": 4, "min": 1, "max": 4096}),
                "spacing_x": ("INT", {"default": 20, "min": -10000, "max": 10000}),
                "spacing_y": ("INT", {"default": 20, "min": -10000, "max": 10000}),
                "offset_x": ("INT", {"default": 0, "min": -10000, "max": 10000}),
                "offset_y": ("INT", {"default": 0, "min": -10000, "max": 10000}),

                # Décalages alternés
                "row_offset_x": ("INT", {"default": 0, "min": -10000, "max": 10000}),
                "col_offset_y": ("INT", {"default": 0, "min": -10000, "max": 10000}),

                # Apparence
                "rotation": ("FLOAT", {"default": 0.0, "min": -1440.0, "max": 1440.0, "step": 0.1}),
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
    ):
        sprite_rgba = _image_to_rgba_pil(image)
        mask_L_src = _mask_to_L(mask, sprite_rgba.size)

        # Sprite transformé (mask/scale/rotation/opacity)
        sprite_t = _transform_sprite(sprite_rgba, mask_L_src, scale=scale,
                                     rotation_deg=rotation, opacity=opacity)
        sw, sh = sprite_t.size

        # Canvas
        if canvas_mode == "match_input":
            cw, ch = sprite_rgba.size
        elif canvas_mode == "auto_from_grid":
            cw, ch = _auto_canvas_size((sw, sh), count_x, count_y, spacing_x, spacing_y,
                                       offset_x, offset_y, 1.0)
        else:  # "custom"
            cw, ch = canvas_width, canvas_height

        base = _make_canvas(cw, ch, use_background, background_hex)
        mask_canvas = Image.new("L", (cw, ch), 0)

        total = count_x * count_y
        if total > 50000:
            raise ValueError("Trop de clones (limite 50k)")

        step_x = sw + spacing_x
        step_y = sh + spacing_y

        for j in range(count_y):
            for i in range(count_x):
                x = offset_x + i * step_x
                y = offset_y + j * step_y

                # Décalages alternés
                if row_offset_x != 0 and (j % 2 == 1):
                    x += row_offset_x
                if col_offset_y != 0 and (i % 2 == 1):
                    y += col_offset_y

                base.alpha_composite(sprite_t, (int(x), int(y)))

                # union du mask
                _, _, _, a = sprite_t.split()
                placed = Image.new("L", (cw, ch), 0)
                placed.paste(a, (int(x), int(y)), a)
                mask_canvas = ImageChops.lighter(mask_canvas, placed)

        out_img = _rgba_pil_to_tensor(base)
        out_mask = _maskL_to_tensor(mask_canvas)
        return (out_img, out_mask)
