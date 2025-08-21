# ComfyUI_DXF/dxf_add_polygon.py
import ezdxf
from ezdxf.addons import Importer
from .dxf_utils import DXFDoc, _BaseAdd
import math

class DXFAddPolygon(_BaseAdd): # <-- Le nom de la classe est corrigé ici
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "dxf": ("DXF",),
            "cx": ("FLOAT", {"default": 0.0}),
            "cy": ("FLOAT", {"default": 0.0}),
            "radius": ("FLOAT", {"default": 10.0, "min": 0.0001}),
            "num_sides": ("INT", {"default": 6, "min": 3, "max": 100}),
        }}
    
    RETURN_TYPES = ("DXF",)
    FUNCTION = "add"
    CATEGORY = "DAO_master/DXF/Primitives"
    
    def add(self, dxf: DXFDoc, cx: float, cy: float, radius: float, num_sides: int):
        new_doc = ezdxf.new(); importer = Importer(dxf.doc, new_doc); importer.import_modelspace(); importer.finalize()
        new_msp = new_doc.modelspace()
        
        points = []
        for i in range(num_sides):
            angle = (2 * math.pi / num_sides) * i
            pt_x = cx + radius * math.cos(angle)
            pt_y = cy + radius * math.sin(angle)
            points.append((pt_x, pt_y))
            
        new_msp.add_lwpolyline(points, format="xy", dxfattribs={"closed": True})
            
        return (DXFDoc(doc=new_doc, msp=new_msp, units=dxf.units),)

NODE_CLASS_MAPPINGS = {"DXF Add Polygon": DXFAddPolygon}
NODE_DISPLAY_NAME_MAPPINGS = {"DXF Add Polygon": "DXF Add Polygon"}