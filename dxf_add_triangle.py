# ComfyUI_DXF/dxf_add_triangle.py
import ezdxf
from ezdxf.addons import Importer
from .dxf_utils import DXFDoc, _BaseAdd

class DXFAddTriangle(_BaseAdd):
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "dxf": ("DXF",),
            "x1": ("FLOAT", {"default": 0.0}),
            "y1": ("FLOAT", {"default": 0.0}),
            "x2": ("FLOAT", {"default": 20.0}),
            "y2": ("FLOAT", {"default": 0.0}),
            "x3": ("FLOAT", {"default": 10.0}),
            "y3": ("FLOAT", {"default": 15.0}),
        }}
    
    RETURN_TYPES = ("DXF",)
    FUNCTION = "add"
    CATEGORY = "DAO_master/DXF/Primitives"
    
    def add(self, dxf: DXFDoc, x1: float, y1: float, x2: float, y2: float, x3: float, y3: float):
        new_doc = ezdxf.new() # Était "new__doc"
        
        importer = Importer(dxf.doc, new_doc)
        importer.import_modelspace()
        importer.finalize()
        
        new_msp = new_doc.modelspace()
        pts = [(x1, y1), (x2, y2), (x3, y3)]
        new_msp.add_lwpolyline(pts, format="xy", dxfattribs={"closed": True})
        
        return (DXFDoc(doc=new_doc, msp=new_msp, units=dxf.units),)

NODE_CLASS_MAPPINGS = {"DXF Add Triangle": DXFAddTriangle}
NODE_DISPLAY_NAME_MAPPINGS = {"DXF Add Triangle": "DXF Add Triangle"}