# ComfyUI-DXF/nodes/dxf_new.py
import time
import ezdxf
from .dxf_utils import DXFDoc, _set_units

class DXFNew:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "units": (["unitless", "mm", "cm", "m", "inch", "foot", "px"], {"default": "mm"}),
        }}
    
    RETURN_TYPES = ("DXF",)
    FUNCTION = "create"
    CATEGORY = "DAO_master/DXF"
    
    @classmethod
    def IS_CHANGED(cls, **kwargs): return time.time_ns()
    
    def create(self, units: str):
        doc = ezdxf.new(setup=True)
        _set_units(doc, units)
        msp = doc.modelspace()
        return (DXFDoc(doc=doc, msp=msp, units=units),)

NODE_CLASS_MAPPINGS = {"DXF New": DXFNew}
NODE_DISPLAY_NAME_MAPPINGS = {"DXF New": "DXF New (ezdxf)"}