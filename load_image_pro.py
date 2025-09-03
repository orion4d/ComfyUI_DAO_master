# -*- coding: utf-8 -*-
# ComfyUI_DAO_master / load_image_pro.py
#
# Merged version with stable mask tools and functional model upscaling.
# FIX 2: Corrected absolute/relative path handling logic, which caused FileNotFoundError.

import os
from typing import Optional, Tuple, List

import numpy as np
import cv2
from PIL import Image
import torch

# --- ComfyUI imports (with fallbacks for standalone analysis) ---
try:
    from folder_paths import get_full_path, get_filename_list
    import comfy.utils
except ImportError:
    # Dummy classes for when running outside ComfyUI
    class MockFolderPaths:
        def get_full_path(self, dir_type, filename): return filename
        def get_filename_list(self, dir_type): return ["(no models found)"]
    folder_paths = MockFolderPaths()
    get_full_path = folder_paths.get_full_path
    get_filename_list = folder_paths.get_filename_list


# ---------- conversions tensor/np (from v1 - stable) ----------

def _img_tensor_to_uint8(img: torch.Tensor) -> np.ndarray:
    if img is None: return None
    if not isinstance(img, torch.Tensor) or img.ndim != 4: raise ValueError("IMAGE tensor must be [B,H,W,C] float32 0..1")
    arr = img[0].detach().cpu().numpy()
    return (np.clip(arr, 0.0, 1.0) * 255.0 + 0.5).astype(np.uint8)

def _img_uint8_to_tensor(arr: np.ndarray) -> torch.Tensor:
    f = (arr.astype(np.float32) / 255.0)[None, ...]
    return torch.from_numpy(f)

def _mask_tensor_to_float(mask: torch.Tensor, size_hw: Optional[Tuple[int, int]] = None) -> np.ndarray:
    if mask is None: return None
    m = mask.detach().cpu().numpy()
    if m.ndim == 3: m = m[0]
    m = m.astype(np.float32)
    if size_hw is not None and (m.shape[0], m.shape[1]) != size_hw:
        m = cv2.resize(m, (size_hw[1], size_hw[0]), interpolation=cv2.INTER_LINEAR)
    return np.clip(m, 0.0, 1.0)

def _mask_float_to_tensor(m: np.ndarray) -> torch.Tensor:
    m = np.clip(m.astype(np.float32), 0.0, 1.0)
    return torch.from_numpy(m)[None, ...]

def _read_rgba_from_path(path: str) -> Tuple[np.ndarray, Optional[np.ndarray]]:
    with Image.open(path) as im:
        im.load()
        if im.mode in ("RGBA", "LA"):
            im = im.convert("RGBA")
            rgba = np.array(im, dtype=np.uint8)
            return rgba[..., :3], rgba[..., 3].astype(np.float32) / 255.0
        im = im.convert("RGB")
        return np.array(im, dtype=np.uint8), None

# ----------------------- Outils de masque (from v1 - stable) ----------------------------

def _gaussian_blur_mask(m: np.ndarray, sigma_px: float) -> np.ndarray:
    if sigma_px <= 0: return m
    return cv2.GaussianBlur(m, (0, 0), sigmaX=float(sigma_px), sigmaY=float(sigma_px))

def _offset_mask_bin(bin8: np.ndarray, pixels: int) -> np.ndarray:
    if pixels == 0: return bin8
    steps = max(1, min(512, abs(int(pixels))))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    return cv2.dilate(bin8, kernel, iterations=steps) if pixels > 0 else cv2.erode(bin8, kernel, iterations=steps)

def _smooth_mask_bin(bin8: np.ndarray, strength_px: float) -> np.ndarray:
    if strength_px <= 0: return bin8
    r = int(max(1, min(128, round(strength_px))))
    k = max(3, 2 * r + 1)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
    sm = cv2.morphologyEx(bin8, cv2.MORPH_OPEN, kernel)
    return cv2.morphologyEx(sm, cv2.MORPH_CLOSE, kernel)

def _fill_holes_bin(bin8: np.ndarray) -> np.ndarray:
    h, w = bin8.shape[:2]
    flood = bin8.copy()
    mask_ff = np.zeros((h + 2, w + 2), np.uint8)
    cv2.floodFill(flood, mask_ff, (0, 0), 255)
    return cv2.bitwise_or(bin8, cv2.bitwise_not(flood))

# ------------------------------ Upscale (from v2, fixed) --------------------------------------

def _opencv_upscale(img: np.ndarray, factor: float, method: str) -> np.ndarray:
    if factor <= 0 or abs(factor - 1.0) < 1e-6: return img
    h, w = img.shape[:2]
    nh, nw = int(round(h * factor)), int(round(w * factor))
    interp_methods = {
        "nearest-exact": cv2.INTER_NEAREST_EXACT if hasattr(cv, "INTER_NEAREST_EXACT") else cv2.INTER_NEAREST,
        "bilinear": cv2.INTER_LINEAR, "area": cv2.INTER_AREA, "lanczos": cv2.INTER_LANCZOS4,
    }
    return cv2.resize(img, (nw, nh), interpolation=interp_methods.get(method, cv2.INTER_LANCZOS4))

def _upscale_with_model(rgb_u8: np.ndarray, factor: float, model_name: str) -> Optional[np.ndarray]:
    try:
        from comfy_extras.nodes_upscale_model import ImageUpscaleWithModel, UpscaleModelLoader
    except Exception as e:
        print(f"[Load Image Pro] Upscale model nodes not available: {e}")
        return None

    print(f"[Load Image Pro] Attempting to upscale with model: {model_name}")
    try:
        loader, upscaler = UpscaleModelLoader(), ImageUpscaleWithModel()
        upscale_model = loader.load_model(model_name)[0]
        img_tensor = _img_uint8_to_tensor(rgb_u8)
        upscaled_tensor = upscaler.upscale(upscale_model, img_tensor)[0]
        out_np = _img_tensor_to_uint8(upscaled_tensor)
        
        h, w = rgb_u8.shape[:2]
        target_h, target_w = int(round(h * factor)), int(round(w * factor))
        if out_np.shape[0] != target_h or out_np.shape[1] != target_w:
            print(f"[Load Image Pro] Model output size {out_np.shape[:2]} differs from target {(target_h, target_w)}. Resizing...")
            out_np = cv2.resize(out_np, (target_w, target_h), interpolation=cv2.INTER_AREA)
        
        print(f"[Load Image Pro] Upscale with model successful.")
        return out_np
    except Exception as e:
        import traceback
        print(f"[Load Image Pro] Upscaling with model '{model_name}' FAILED. Falling back to OpenCV.")
        print(traceback.format_exc())
        return None

# --------------------------------- Node --------------------------------------

class LoadImagePro:
    @classmethod
    def INPUT_TYPES(cls):
        try:
            models = get_filename_list("upscale_models")
            if not models: models = ["(no models found)"]
        except Exception: models = ["(no models found)"]

        return {
            "required": {
                "path": ("STRING", {"multiline": False, "default": ""}),
                "enable_mask_tools": ("BOOLEAN", {"default": False}), "mask_blur": ("INT", {"default": 0, "min": 0, "max": 256}),
                "mask_offset": ("INT", {"default": 0, "min": -256, "max": 256}), "smooth": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 100.0, "step": 0.5}),
                "fill_holes": ("BOOLEAN", {"default": False}), "invert_mask": ("BOOLEAN", {"default": False}),
                "enable_upscale": ("BOOLEAN", {"default": False}), "upscale_factor": ("FLOAT", {"default": 1.0, "min": 0.05, "max": 8.0, "step": 0.05}),
                "upscale_model": (models,), "upscale_method": (["lanczos", "nearest-exact", "bilinear", "area"], {"default": "lanczos"}),
            }, "optional": {"image": ("IMAGE",), "mask": ("MASK",),},
        }

    RETURN_TYPES = ("IMAGE", "IMAGE", "MASK", "IMAGE", "INT", "INT")
    RETURN_NAMES = ("image", "image_rgba", "mask", "mask_image", "width", "height")
    FUNCTION = "run"
    CATEGORY = "DAO_master/Images/IO"

    def _load_from_path(self, path: str) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        if not path: raise ValueError("Path is empty.")
        
        # --- CRITICAL FIX for path handling ---
        if os.path.isabs(path):
            full_path = path
        else:
            full_path = get_full_path("input", path)
            
        if not full_path or not os.path.isfile(full_path):
            raise FileNotFoundError(f"Image not found at path: {path} (resolved to: {full_path})")
            
        return _read_rgba_from_path(full_path)

    def _compose_rgba(self, rgb: np.ndarray, alpha_f: Optional[np.ndarray]) -> np.ndarray:
        H, W = rgb.shape[:2]
        if alpha_f is not None and alpha_f.shape[:2] != (H, W):
            alpha_f = cv2.resize(alpha_f, (W, H), interpolation=cv2.INTER_LINEAR)
        if alpha_f is None: alpha_f = np.ones((H, W), dtype=np.float32)
        a8 = (np.clip(alpha_f * 255.0, 0, 255) + 0.5).astype(np.uint8)
        return np.dstack((rgb, a8))

    def _apply_mask_tools(self, base_mask_f: np.ndarray, mask_blur: int, mask_offset: int, smooth: float, fill_holes: bool, invert_mask: bool) -> np.ndarray:
        m = np.clip(base_mask_f, 0.0, 1.0)
        bin8 = (m >= 0.5).astype(np.uint8) * 255
        if mask_offset != 0: bin8 = _offset_mask_bin(bin8, mask_offset)
        if fill_holes: bin8 = _fill_holes_bin(bin8)
        if smooth > 0: bin8 = _smooth_mask_bin(bin8, smooth)
        m = bin8.astype(np.float32) / 255.0
        if mask_blur > 0: m = _gaussian_blur_mask(m, float(mask_blur))
        if invert_mask: m = 1.0 - m
        return np.clip(m, 0.0, 1.0)

    def run(self, path: str = "", image=None, mask=None, **kwargs):
        if image is None and not path: raise ValueError("An 'image' input or a 'path' is required.")
        rgb_u8, alpha_from_png = self._load_from_path(path) if image is None else (_img_tensor_to_uint8(image), None)
        H, W = rgb_u8.shape[:2]

        mask_f = _mask_tensor_to_float(mask, (H, W)) if mask is not None else alpha_from_png

        if kwargs.get('enable_mask_tools', False):
            base_mask = mask_f if mask_f is not None else np.ones((H, W), dtype=np.float32)
            mask_f = self._apply_mask_tools(base_mask, **{k: v for k, v in kwargs.items() if k in ['mask_blur', 'mask_offset', 'smooth', 'fill_holes', 'invert_mask']})

        if kwargs.get('enable_upscale', False) and abs(kwargs.get('upscale_factor', 1.0) - 1.0) > 1e-6:
            factor, model, method = kwargs['upscale_factor'], kwargs['upscale_model'], kwargs['upscale_method']
            upscaled = _upscale_with_model(rgb_u8, factor, model) if model and "(no models" not in model else None
            rgb_u8 = upscaled if upscaled is not None else _opencv_upscale(rgb_u8, factor, method)
            if mask_f is not None:
                mask_f = cv2.resize(mask_f, (rgb_u8.shape[1], rgb_u8.shape[0]), interpolation=cv2.INTER_LINEAR)

        alpha_for_rgba = mask_f if mask_f is not None else alpha_from_png
        final_mask_f = mask_f if mask_f is not None else np.ones(rgb_u8.shape[:2], dtype=np.float32)
        
        mask_u8_3ch = np.repeat((np.clip(final_mask_f * 255.0, 0, 255).astype(np.uint8))[..., None], 3, axis=2)
        h, w = rgb_u8.shape[:2]
        
        return (_img_uint8_to_tensor(rgb_u8), _img_uint8_to_tensor(self._compose_rgba(rgb_u8, alpha_for_rgba)),
                _mask_float_to_tensor(final_mask_f), _img_uint8_to_tensor(mask_u8_3ch), w, h)

NODE_CLASS_MAPPINGS = { "Load Image Pro": LoadImagePro }
NODE_DISPLAY_NAME_MAPPINGS = { "Load Image Pro": "Load Image Pro (Path/Image → RGB/RGBA/Mask)" }