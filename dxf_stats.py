# ComfyUI-DXF/nodes/dxf_stats.py
from .dxf_utils import DXFDoc, _bbox_from_entities

class DXFStats:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"dxf": ("DXF",)}}
    
    RETURN_TYPES = ("STRING", "INT")
    RETURN_NAMES = ("bbox", "count")
    FUNCTION = "stats"
    CATEGORY = "DAO_master/DXF/Utils"
    
    def stats(self, dxf: DXFDoc):
        bbox = _bbox_from_entities(dxf.msp)
        count = len(dxf.msp)
        return (str(bbox) if bbox else "None", count)

NODE_CLASS_MAPPINGS = {"DXF Stats": DXFStats}
NODE_DISPLAY_NAME_MAPPINGS = {"DXF Stats": "DXF Stats (bbox & count)"}