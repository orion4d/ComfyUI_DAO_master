# ComfyUI-DXF/nodes/dxf_save.py
import os
import time
from .dxf_utils import DXFDoc

class DXFSave:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "dxf": ("DXF",),
            "directory": ("STRING", {"default": "output/dxf"}),
            "filename": ("STRING", {"default": "shape.dxf"}),
            "timestamp_suffix": ("BOOLEAN", {"default": True}),
            "save_file": ("BOOLEAN", {"default": True}),
        }}
    
    RETURN_TYPES = ("DXF", "STRING")
    RETURN_NAMES = ("dxf", "path")
    FUNCTION = "save"
    CATEGORY = "DAO_master/DXF/Utils"
    
    @classmethod
    def IS_CHANGED(cls, **kwargs): return time.time_ns()
    
    def save(self, dxf: DXFDoc, directory: str, filename: str, timestamp_suffix: bool, save_file: bool):
        out_path = ""
        if save_file and filename.strip():
            os.makedirs(directory or ".", exist_ok=True)
            base, ext = os.path.splitext(filename); ext = ext or ".dxf"
            if timestamp_suffix:
                stamp = time.strftime("%Y%m%d_%H%M%S")
                candidate = os.path.join(directory, f"{base}_{stamp}{ext}")
            else:
                candidate = os.path.join(directory, base + ext)
            
            # Anti-overwrite logic
            i = 1
            final_path = candidate
            base_path, extension = os.path.splitext(candidate)
            while os.path.exists(final_path):
                final_path = f"{base_path}_{i}{extension}"
                i += 1
            
            dxf.doc.saveas(final_path)
            out_path = os.path.abspath(final_path)
        return (dxf, out_path)

NODE_CLASS_MAPPINGS = {"DXF Save": DXFSave}
NODE_DISPLAY_NAME_MAPPINGS = {"DXF Save": "DXF Save"}