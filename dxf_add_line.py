# ComfyUI_DXF/dxf_add_line.py
import ezdxf
from ezdxf.addons import Importer
from .dxf_utils import DXFDoc, _BaseAdd

class DXFAddLine(_BaseAdd):
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "dxf": ("DXF",),
            "x1": ("FLOAT", {"default": 0.0}),
            "y1": ("FLOAT", {"default": 0.0}),
            "x2": ("FLOAT", {"default": 20.0}),
            "y2": ("FLOAT", {"default": 0.0}),
        }}
    
    RETURN_TYPES = ("DXF",)
    FUNCTION = "add"
    CATEGORY = "DAO_master/DXF/Primitives"
    
    def add(self, dxf: DXFDoc, x1: float, y1: float, x2: float, y2: float):
        new_doc = ezdxf.new()
        importer = Importer(dxf.doc, new_doc)
        importer.import_modelspace()
        importer.finalize()
        
        new_msp = new_doc.modelspace()
        new_msp.add_line((x1, y1), (x2, y2))
        
        return (DXFDoc(doc=new_doc, msp=new_msp, units=dxf.units),)

NODE_CLASS_MAPPINGS = {"DXF Add Line": DXFAddLine}
NODE_DISPLAY_NAME_MAPPINGS = {"DXF Add Line": "DXF Add Line"}