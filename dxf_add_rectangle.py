# ComfyUI_DXF/dxf_add_rectangle.py
import ezdxf
from ezdxf.addons import Importer
from .dxf_utils import DXFDoc, _BaseAdd

class DXFAddRectangle(_BaseAdd):
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "dxf": ("DXF",),
            "x": ("FLOAT", {"default": 0.0}),
            "y": ("FLOAT", {"default": 0.0}),
            "width": ("FLOAT", {"default": 20.0, "min": 0.0001}),
            "height": ("FLOAT", {"default": 10.0, "min": 0.0001}),
            "centered": ("BOOLEAN", {"default": False}),
        }}
    
    RETURN_TYPES = ("DXF",)
    FUNCTION = "add"
    CATEGORY = "DAO_master/DXF/Primitives"
    
    def add(self, dxf: DXFDoc, x: float, y: float, width: float, height: float, centered: bool):
        new_doc = ezdxf.new()
        importer = Importer(dxf.doc, new_doc)
        importer.import_modelspace()
        importer.finalize()

        new_msp = new_doc.modelspace()
        if centered: x0 = x - width / 2.0; y0 = y - height / 2.0
        else: x0, y0 = x, y
        pts = [(x0, y0), (x0 + width, y0), (x0 + width, y0 + height), (x0, y0 + height)]
        new_msp.add_lwpolyline(pts, format="xy", dxfattribs={"closed": True})
        
        return (DXFDoc(doc=new_doc, msp=new_msp, units=dxf.units),)

NODE_CLASS_MAPPINGS = {"DXF Add Rectangle": DXFAddRectangle}
NODE_DISPLAY_NAME_MAPPINGS = {"DXF Add Rectangle": "DXF Add Rectangle"}