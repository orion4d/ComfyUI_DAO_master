# ComfyUI_DAO_master/path_to_image.py
# -*- coding: utf-8 -*-
import os, json
from typing import Tuple
from PIL import Image, PngImagePlugin, ExifTags
import numpy as np
import torch

def _to_image_tensor(arr: np.ndarray) -> torch.Tensor:
    """
    arr: H x W x C (uint8 or float) -> 1 x H x W x C (float32 0..1)
    """
    if arr.dtype != np.float32:
        arr = arr.astype(np.float32) / 255.0
    if arr.ndim != 3:
        raise ValueError("Expected HxWxC array for IMAGE")
    return torch.from_numpy(np.ascontiguousarray(arr)).unsqueeze(0)

def _to_mask_tensor(alpha: np.ndarray | None, hw: Tuple[int,int]) -> torch.Tensor:
    """
    alpha: H x W (0..255 or 0..1) or None -> 1 x H x W (float32 0..1)
    """
    if alpha is None:
        h, w = hw
        return torch.ones((1, h, w), dtype=torch.float32)
    if alpha.dtype != np.float32:
        alpha = alpha.astype(np.float32) / 255.0
    alpha = np.clip(alpha, 0.0, 1.0)
    return torch.from_numpy(np.ascontiguousarray(alpha)).unsqueeze(0)

def _mask_to_image(mask: torch.Tensor) -> torch.Tensor:
    """
    mask: 1 x H x W -> 1 x H x W x 3
    """
    return mask.unsqueeze(-1).repeat(1, 1, 1, 3)

def _read_png_text(img: Image.Image) -> dict:
    out = {}
    if hasattr(img, "text") and isinstance(img.text, dict):
        for k, v in img.text.items():
            out[k] = v if isinstance(v, str) else str(v)
    if hasattr(img, "info") and isinstance(img.info, dict):
        for k, v in img.info.items():
            if k not in out:
                out[k] = v if isinstance(v, str) else (v.decode("utf-8", "ignore") if isinstance(v, bytes) else str(v))
    return out

def _read_exif_text(img: Image.Image) -> str:
    try:
        exif = img.getexif()
        if not exif:
            return ""
        rev = {ExifTags.TAGS.get(k, k): v for k, v in exif.items()}
        pairs = []
        for k, v in rev.items():
            if isinstance(v, (str, int, float)):
                pairs.append(f"{k}={v}")
        return "\n".join(pairs)
    except Exception:
        return ""

class PathToImage:
    """
    Path → Image (RGB & RGBA / Mask / Meta)
    Aucune preview intégrée (on évite les erreurs de dtype).
    """
    CATEGORY = "DAO_master/Images/IO"
    RETURN_TYPES = ("IMAGE", "IMAGE", "MASK", "IMAGE", "STRING", "STRING", "INT", "INT")
    RETURN_NAMES = ("image", "image_rgba", "mask", "mask_image", "json", "metadata", "width", "height")
    FUNCTION = "load"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "path": ("STRING", {"multiline": False, "placeholder": r"D:\images\foo.png"}),
            }
        }

    def load(self, path: str):
        p = os.path.expanduser(str(path or "")).strip().strip('"')
        if not p or not os.path.isfile(p):
            # Valeurs neutres pour éviter tout plantage
            rgb = _to_image_tensor(np.zeros((1, 1, 3), dtype=np.uint8))
            rgba = _to_image_tensor(np.zeros((1, 1, 4), dtype=np.uint8))
            mask = _to_mask_tensor(None, (1, 1))
            mask_img = _mask_to_image(mask)
            return (rgb, rgba, mask, mask_img, "", "", 1, 1)

        with Image.open(p) as im:
            im_rgba = im.convert("RGBA")
            w, h = im_rgba.size
            arr_rgba = np.array(im_rgba, dtype=np.uint8)  # H x W x 4

        arr_rgb = arr_rgba[:, :, :3]
        alpha_np = arr_rgba[:, :, 3] if arr_rgba.shape[2] == 4 else None

        t_rgba = _to_image_tensor(arr_rgba)          # 1 x H x W x 4
        t_rgb  = _to_image_tensor(arr_rgb)           # 1 x H x W x 3
        t_mask = _to_mask_tensor(alpha_np, (h, w))   # 1 x H x W
        t_mask_img = _mask_to_image(t_mask)          # 1 x H x W x 3

        json_txt = ""
        meta_txt = ""
        try:
            with Image.open(p) as im2:
                info = _read_png_text(im2) if isinstance(im2, PngImagePlugin.PngImageFile) else {}
                for k in ("workflow", "json"):
                    if k in info and isinstance(info[k], str):
                        json_txt = info[k]
                        break
                for k in ("parameters", "Description", "comment"):
                    if k in info and isinstance(info[k], str):
                        meta_txt = info[k]
                        break
                if not meta_txt:
                    exif_text = _read_exif_text(im2)
                    if exif_text:
                        meta_txt = exif_text
        except Exception:
            pass

        return (t_rgb, t_rgba, t_mask, t_mask_img, json_txt, meta_txt, w, h)
