# ComfyUI_DXF/svg_save.py
import os
import time

class SvgSave:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "svg_text": ("SVG_TEXT",),
            "directory": ("STRING", {"default": "output/svg"}),
            "filename": ("STRING", {"default": "shape.svg"}),
            "timestamp_suffix": ("BOOLEAN", {"default": True}),
        }}
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("path",)
    FUNCTION = "save"
    CATEGORY = "DAO_master/SVG/IO"
    
    def save(self, svg_text: str, directory: str, filename: str, timestamp_suffix: bool):
        out_path = ""
        if svg_text and filename.strip():
            os.makedirs(directory, exist_ok=True)
            base, ext = os.path.splitext(filename); ext = ext or ".svg"
            
            if timestamp_suffix:
                stamp = time.strftime("%Y%m%d_%H%M%S")
                candidate = os.path.join(directory, f"{base}_{stamp}{ext}")
            else:
                candidate = os.path.join(directory, base + ext)
            
            i = 1; final_path = candidate
            while os.path.exists(final_path):
                if timestamp_suffix:
                    final_path = f"{os.path.splitext(candidate)[0]}_{i}.svg"
                else:
                    final_path = os.path.join(directory, f"{base}_{i}{ext}")
                i += 1
            
            with open(final_path, 'w', encoding='utf-8') as f:
                f.write(svg_text)
            out_path = os.path.abspath(final_path)
            
        return (out_path,)

NODE_CLASS_MAPPINGS = {"SVG Save": SvgSave}
NODE_DISPLAY_NAME_MAPPINGS = {"SVG Save": "SVG Save"}