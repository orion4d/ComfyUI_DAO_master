# ComfyUI_DXF/svg_preview.py
# (imports inchangés)
import torch, numpy as np, io
from PIL import Image
from lxml import etree
try:
    import cairosvg
    _CAIRO_OK = True
except (ImportError, OSError):
    _CAIRO_OK = False

class SvgPreview:
    def __init__(self):
        if not _CAIRO_OK: raise ImportError("CairoSVG est requis. `pip install cairosvg`")

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "svg_text": ("SVG_TEXT",),
            "width": ("INT", {"default": 512, "min": 64, "max": 4096}),
            "height": ("INT", {"default": 512, "min": 64, "max": 4096}),
            "fit_mode": (["stretch", "fit_width", "fit_height", "contain"],),
            "bg_enabled": ("BOOLEAN", {"default": False}),
            "bg_color_hex": ("STRING", {"default": "#FFFFFF"}),
        }}
    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "preview"
    CATEGORY = "DAO_master/SVG"
    
    def preview(self, svg_text, width, height, fit_mode, bg_enabled, bg_color_hex):
        if not svg_text.strip():
            img = Image.new('RGB' if bg_enabled else 'RGBA', (width, height), bg_color_hex if bg_enabled else (0,0,0,0))
            img_np = np.array(img).astype(np.float32) / 255.0
            return (torch.from_numpy(img_np)[None,],)

        # Calculer les dimensions de rendu basées sur le fit_mode
        render_w, render_h = width, height
        if fit_mode != "stretch":
            try:
                root = etree.fromstring(svg_text.encode('utf-8'))
                viewBox = root.get('viewBox')
                if viewBox:
                    _, _, vb_w, vb_h = map(float, viewBox.split())
                    if vb_h > 0 and vb_w > 0:
                        aspect_ratio = vb_w / vb_h
                        if fit_mode == "fit_width":
                            render_h = int(width / aspect_ratio)
                        elif fit_mode == "fit_height":
                            render_w = int(height * aspect_ratio)
                        elif fit_mode == "contain":
                            if width / aspect_ratio <= height: # fit width
                                render_h = int(width / aspect_ratio)
                            else: # fit height
                                render_w = int(height * aspect_ratio)
            except Exception:
                pass # Garder les dimensions par défaut en cas d'erreur
        
        # Rendre le SVG en PNG avec un fond transparent
        png_data = cairosvg.svg2png(
            bytestring=svg_text.encode('utf-8'), 
            output_width=render_w, 
            output_height=render_h
        )
        rendered_img = Image.open(io.BytesIO(png_data))

        # Créer l'image finale
        if bg_enabled:
            final_img = Image.new('RGB', (width, height), bg_color_hex)
            paste_x = (width - rendered_img.width) // 2
            paste_y = (height - rendered_img.height) // 2
            final_img.paste(rendered_img, (paste_x, paste_y), rendered_img) # Utiliser le canal alpha du PNG comme masque
        else: # Pas de fond, on renvoie l'image rendue avec sa transparence
            final_img = rendered_img

        # Conversion en tenseur
        if final_img.mode == 'RGB':
            img_np = np.array(final_img).astype(np.float32) / 255.0
        else: # RGBA
            img_np = np.array(final_img.convert("RGBA")).astype(np.float32) / 255.0
            
        tensor = torch.from_numpy(img_np)[None,]
        return (tensor,)