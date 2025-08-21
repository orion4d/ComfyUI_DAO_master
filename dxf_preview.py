# ComfyUI_DXF/dxf_preview.py
import time
import torch
# --- CORRECTION DE L'IMPORT : On ne charge plus la fonction supprimée ---
from .dxf_utils import (DXFDoc, _render_internal_rgb_and_mask, 
                         _to_image_tensor, _to_mask_tensor)

class DXFPreview:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "dxf": ("DXF",),
            # --- SIMPLIFICATION : Le paramètre "renderer" a été supprimé ---
            "size": ("INT", {"default": 512, "min": 128, "max": 4096, "step": 64}),
            "line_width": ("INT", {"default": 3, "min": 0, "max": 1000}),
            "stroke_hex": ("STRING", {"default": "#000000"}),
            "fill_enabled": ("BOOLEAN", {"default": False}),
            "fill_hex": ("STRING", {"default": "#00A2FF"}),
            "bg_enabled": ("BOOLEAN", {"default": True}),
            "bg_hex": ("STRING", {"default": "#F5F5F5"}),
            "show_grid": ("BOOLEAN", {"default": True}),
            "transparent_bg": ("BOOLEAN", {"default": False}),
            "emit_mask": ("BOOLEAN", {"default": False}),
        }}
    
    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("image", "mask")
    FUNCTION = "preview"
    CATEGORY = "DAO_master/DXF/Utils"
    
    @classmethod
    def IS_CHANGED(cls, **kwargs): return time.time_ns()
    
    # --- SIMPLIFICATION : La logique "if renderer" a été supprimée ---
    def preview(self, dxf: DXFDoc, size: int, line_width: int,
                stroke_hex: str, fill_enabled: bool, fill_hex: str, bg_enabled: bool,
                bg_hex: str, show_grid: bool, transparent_bg: bool, emit_mask: bool):
        
        # On utilise directement et uniquement notre moteur de rendu interne
        img, mask = _render_internal_rgb_and_mask(
            dxf.msp, size, line_width, stroke_hex,
            fill_enabled, fill_hex, bg_enabled, bg_hex,
            show_grid, transparent_bg
        )
        
        img_t = _to_image_tensor(img)
        mask_t = _to_mask_tensor(mask) if emit_mask else torch.zeros((1, img_t.shape[1], img_t.shape[2]), dtype=torch.float32)
        
        return (img_t, mask_t)

NODE_CLASS_MAPPINGS = {"DXF Preview": DXFPreview}
NODE_DISPLAY_NAME_MAPPINGS = {"DXF Preview": "DXF Preview (from DXF)"}