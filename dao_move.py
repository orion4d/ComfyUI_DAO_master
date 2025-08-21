# -*- coding: utf-8 -*-
# DAO_master — Move / Scale / Rotate / Symmetry (IMAGE only)
# Node: Move-Scale-Rotate-Sym
# - Entrées : IMAGE (obligatoire), MASK (optionnel)
# - Sorties : IMAGE, MASK
# - Options :
#     * angle_deg / scale / dx / dy
#     * pivot_mode: center | top_left | custom (+ pivot_x / pivot_y)
#     * flip_h / flip_v
#     * apply_mask_to_alpha : insère MASK comme canal alpha (préserve la transparence PNG)
#     * invert_mask : inverse le MASK entrant (utile si masque inversé)

import numpy as np
from PIL import Image, ImageOps

try:
    import torch
except Exception:
    torch = None


# =========================
#      IMAGE / MASK I/O
# =========================

def _tensor_to_pil(img):
    if img is None:
        return None
    # ComfyUI IMAGE = float32 [B,H,W,C] in 0..1
    if (torch is not None) and isinstance(img, torch.Tensor):
        arr = img[0].detach().cpu().numpy()
    else:
        arr = img[0]
    arr = (np.clip(arr, 0.0, 1.0) * 255.0).astype(np.uint8)
    if arr.ndim == 3 and arr.shape[-1] == 4:
        return Image.fromarray(arr, "RGBA")
    if arr.ndim == 3 and arr.shape[-1] >= 3:
        return Image.fromarray(arr[..., :3], "RGB")
    # grayscale fallback
    return Image.fromarray(arr.squeeze().astype(np.uint8), "L").convert("RGBA")


def _pil_to_tensor(img: Image.Image):
    arr = np.asarray(img).astype(np.float32) / 255.0
    if arr.ndim == 2:
        arr = np.stack([arr, arr, arr], axis=-1)
    return torch.from_numpy(arr).unsqueeze(0) if torch is not None else arr[None, ...]


def _mask_from_rgba(img: Image.Image):
    """Extrait alpha en MASK [B,H,W] (0..1). Si pas d'alpha -> tout opaque."""
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


# =========================
#      AFFINE HELPERS
# =========================

import numpy as np

def _inv_affine_uniform(scale: float, angle_deg: float, dx: float, dy: float, cx: float, cy: float):
    """Inverse pour PIL.Image.transform (output->input) avec pivot (cx,cy)."""
    s = max(1e-8, float(scale))
    th = np.deg2rad(angle_deg)
    c, s_ = np.cos(th), np.sin(th)

    t1 = np.array([[1, 0, -cx],
                   [0, 1, -cy],
                   [0, 0, 1]], float)
    S = np.array([[s, 0, 0],
                  [0, s, 0],
                  [0, 0, 1]], float)
    R = np.array([[c, -s_, 0],
                  [s_,  c, 0],
                  [0,   0, 1]], float)
    t2 = np.array([[1, 0, cx],
                   [0, 1, cy],
                   [0, 0, 1]], float)
    t3 = np.array([[1, 0, dx],
                   [0, 1, dy],
                   [0, 0, 1]], float)

    F = t3 @ t2 @ R @ S @ t1
    inv = np.linalg.inv(F)
    a, b, c0 = inv[0, 0], inv[0, 1], inv[0, 2]
    d, e, f0 = inv[1, 0], inv[1, 1], inv[1, 2]
    return (a, b, c0, d, e, f0)


# =========================
#         NODE
# =========================

class DAOMove:
    """Node: Move-Scale-Rotate-Sym (IMAGE only)"""
    CATEGORY = "DAO_master/Utils"
    FUNCTION = "apply"
    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("image", "mask")
    OUTPUT_NODE = False

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE", {}),
                "angle_deg": ("FLOAT", {"default": 0.0, "min": -360.0, "max": 360.0, "step": 0.1}),
                "scale": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01}),
                "dx": ("INT", {"default": 0, "min": -8192, "max": 8192}),
                "dy": ("INT", {"default": 0, "min": -8192, "max": 8192}),
                "pivot_mode": (["center", "top_left", "custom"], {"default": "center"}),
                "pivot_x": ("FLOAT", {"default": 0.0, "min": -8192.0, "max": 8192.0}),
                "pivot_y": ("FLOAT", {"default": 0.0, "min": -8192.0, "max": 8192.0}),
                "flip_h": ("BOOLEAN", {"default": False}),
                "flip_v": ("BOOLEAN", {"default": False}),
                "apply_mask_to_alpha": ("BOOLEAN", {"default": True}),
                "invert_mask": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "mask": ("MASK", {}),
            },
        }

    def apply(self, image, angle_deg, scale, dx, dy,
              pivot_mode, pivot_x, pivot_y,
              flip_h, flip_v, apply_mask_to_alpha, invert_mask,
              mask=None):

        # ---- 1) Entrées -> PIL ----
        pil_img = _tensor_to_pil(image)            # RGB/RGBA
        pil_msk = _mask_tensor_to_pil(mask) if mask is not None else None

        # Si pas de mask, on prend l'alpha s'il existe, sinon tout opaque
        if pil_msk is None:
            pil_msk = _mask_tensor_to_pil(_mask_from_rgba(pil_img))

        # Inversion éventuelle du mask
        if invert_mask and pil_msk is not None:
            pil_msk = ImageOps.invert(pil_msk.convert("L"))

        # Appliquer le mask comme alpha sur l'image pour préserver la transparence
        base = pil_img.convert("RGBA")
        if apply_mask_to_alpha and pil_msk is not None:
            a = pil_msk.convert("L")
            r, g, b, _ = base.split()
            base = Image.merge("RGBA", (r, g, b, a))

        # ---- 2) Affine ----
        w, h = base.size
        if pivot_mode == "center":
            cx, cy = w / 2.0, h / 2.0
        elif pivot_mode == "top_left":
            cx, cy = 0.0, 0.0
        else:  # custom
            cx, cy = float(pivot_x), float(pivot_y)

        coeffs = _inv_affine_uniform(scale, angle_deg, dx, dy, cx, cy)
        out_img = base.transform((w, h), Image.AFFINE, coeffs,
                                 resample=Image.BICUBIC, fillcolor=(0, 0, 0, 0))
        out_msk = pil_msk.transform((w, h), Image.AFFINE, coeffs,
                                    resample=Image.NEAREST, fillcolor=0)

        # ---- 3) Flips ----
        if flip_h:
            out_img = ImageOps.mirror(out_img)
            out_msk = ImageOps.mirror(out_msk)
        if flip_v:
            out_img = ImageOps.flip(out_img)
            out_msk = ImageOps.flip(out_msk)

        # ---- 4) Sorties ----
        return (_pil_to_tensor(out_img), _pil_to_mask_tensor(out_msk))
