# -*- coding: utf-8 -*-
# DAO_master — Blur (Gaussian) — IMAGE + MASK + drop shadow (couleur hex)
# Node: dao_Blur / class DAOBlur

import numpy as np
from PIL import Image, ImageOps, ImageFilter

try:
    import torch
except Exception:
    torch = None


# ---------- Helpers IMAGE/MASK ----------

def _tensor_to_pil(img):
    if img is None:
        return None
    if (torch is not None) and isinstance(img, torch.Tensor):
        arr = img[0].detach().cpu().numpy()
    else:
        arr = img[0]
    arr = (np.clip(arr, 0.0, 1.0) * 255.0).astype(np.uint8)
    if arr.ndim == 3 and arr.shape[-1] == 4:
        return Image.fromarray(arr, "RGBA")
    if arr.ndim == 3 and arr.shape[-1] >= 3:
        return Image.fromarray(arr[..., :3], "RGB")
    return Image.fromarray(arr.squeeze().astype(np.uint8), "L").convert("RGBA")


def _pil_to_tensor(img: Image.Image):
    arr = np.asarray(img).astype(np.float32) / 255.0
    if arr.ndim == 2:
        arr = np.stack([arr, arr, arr], axis=-1)
    return torch.from_numpy(arr).unsqueeze(0) if torch is not None else arr[None, ...]


def _mask_from_rgba(img: Image.Image):
    if img.mode != "RGBA":
        h, w = img.size[1], img.size[0]
        m = np.ones((h, w), np.float32)
        return torch.from_numpy(m).unsqueeze(0) if torch is not None else m[None, ...]
    a = np.asarray(img.split()[-1], np.float32) / 255.0
    return torch.from_numpy(a).unsqueeze(0) if torch is not None else a[None, ...]


def _mask_tensor_to_pil(mask):
    if mask is None:
        return None
    if (torch is not None) and isinstance(mask, torch.Tensor):
        arr = mask[0].detach().cpu().numpy()
    else:
        arr = mask[0]
    arr = (np.clip(arr, 0.0, 1.0) * 255.0).astype(np.uint8)
    return Image.fromarray(arr, "L")


def _pil_to_mask_tensor(img: Image.Image):
    g = img.convert("L")
    arr = np.asarray(g, dtype=np.float32) / 255.0
    return torch.from_numpy(arr).unsqueeze(0) if torch is not None else arr[None, ...]


# ---------- Color utils ----------

def _parse_hex_color(s: str):
    """
    Retourne (R,G,B,A) 0..255 depuis #RGB, #RGBA, #RRGGBB, #RRGGBBAA (insensible à la casse).
    Si invalide -> noir opaque.
    """
    if not isinstance(s, str):
        return (0, 0, 0, 255)
    x = s.strip()
    if x.startswith("#"):
        x = x[1:]
    x = x.lower()
    try:
        if len(x) == 3:  # RGB
            r, g, b = [int(c * 2, 16) for c in x]
            return (r, g, b, 255)
        if len(x) == 4:  # RGBA
            r, g, b, a = [int(c * 2, 16) for c in x]
            return (r, g, b, a)
        if len(x) == 6:  # RRGGBB
            r = int(x[0:2], 16); g = int(x[2:4], 16); b = int(x[4:6], 16)
            return (r, g, b, 255)
        if len(x) == 8:  # RRGGBBAA
            r = int(x[0:2], 16); g = int(x[2:4], 16); b = int(x[4:6], 16); a = int(x[6:8], 16)
            return (r, g, b, a)
    except Exception:
        pass
    return (0, 0, 0, 255)


# ---------- NODE ----------

class DAOBlur:
    CATEGORY = "DAO_master/Images/Filter"
    FUNCTION = "apply"
    RETURN_TYPES = ("IMAGE", "MASK", "IMAGE")
    RETURN_NAMES = ("image", "mask", "drop_shadow")
    OUTPUT_NODE = False

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "radius": ("FLOAT", {"default": 5.0, "min": 0.0, "max": 100.0, "step": 0.1}),
                "shadow_opacity": ("FLOAT", {"default": 50.0, "min": 0.0, "max": 100.0, "step": 0.1}),
                "shadow_color": ("STRING", {"default": "#000000"}),  # ← couleur hex
                "move_x": ("INT", {"default": 0, "min": -8192, "max": 8192}),
                "move_y": ("INT", {"default": 0, "min": -8192, "max": 8192}),
                "invert_drop_shadow": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "image": ("IMAGE", {}),
                "mask": ("MASK", {}),
                "mask_form": ("MASK", {}),
                "apply_mask_to_alpha": ("BOOLEAN", {"default": True}),
                "invert_mask": ("BOOLEAN", {"default": False}),
            },
        }

    def apply(self, radius, shadow_opacity, shadow_color, move_x, move_y, invert_drop_shadow,
              image=None, mask=None, mask_form=None,
              apply_mask_to_alpha=True, invert_mask=False):

        r = float(max(0.0, min(100.0, radius)))
        opacity_scale = float(max(0.0, min(100.0, shadow_opacity))) / 100.0
        cr, cg, cb, ca = _parse_hex_color(shadow_color)
        color_alpha_scale = (ca / 255.0) * opacity_scale  # alpha hex * opacité slider

        # --- Entrées -> PIL ---
        pil_img = _tensor_to_pil(image) if image is not None else None
        pil_msk = _mask_tensor_to_pil(mask) if mask is not None else None
        pil_form = _mask_tensor_to_pil(mask_form) if mask_form is not None else None

        if pil_img is None:
            pil_img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
        if pil_msk is None:
            pil_msk = _mask_tensor_to_pil(_mask_from_rgba(pil_img))

        if invert_mask:
            pil_msk = ImageOps.invert(pil_msk.convert("L"))

        # --- Blur image & mask ---
        pil_img = pil_img.convert("RGBA").filter(ImageFilter.GaussianBlur(r))
        pil_msk = pil_msk.convert("L").filter(ImageFilter.GaussianBlur(r))

        # --- Appliquer mask_form en intersection (multiplicative) ---
        if pil_form is not None:
            formL = pil_form.convert("L")
            a = np.asarray(pil_msk, dtype=np.float32)
            b = np.asarray(formL, dtype=np.float32) / 255.0
            a = np.clip(a * b, 0, 255).astype(np.uint8)
            pil_msk = Image.fromarray(a, "L")

        # --- Image principale : alpha depuis mask final (optionnel) ---
        if apply_mask_to_alpha:
            rch, gch, bch, _ = pil_img.split()
            pil_img = Image.merge("RGBA", (rch, gch, bch, pil_msk))

        # --- Drop Shadow colorée ---
        base_alpha = np.asarray(pil_msk, dtype=np.uint8)
        alpha_arr = (255 - base_alpha) if invert_drop_shadow else base_alpha.copy()

        if color_alpha_scale < 1.0:
            alpha_arr = (alpha_arr.astype(np.float32) * color_alpha_scale).clip(0, 255).astype(np.uint8)

        alpha_ds = Image.fromarray(alpha_arr, "L")
        w, h = pil_img.size
        r_img = Image.new("L", (w, h), int(cr))
        g_img = Image.new("L", (w, h), int(cg))
        b_img = Image.new("L", (w, h), int(cb))
        drop_shadow = Image.merge("RGBA", (r_img, g_img, b_img, alpha_ds))

        # offset
        if move_x != 0 or move_y != 0:
            canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            canvas.paste(drop_shadow, (int(move_x), int(move_y)))
            drop_shadow = canvas

        # --- Sorties ---
        return (_pil_to_tensor(pil_img),
                _pil_to_mask_tensor(pil_msk),
                _pil_to_tensor(drop_shadow))
