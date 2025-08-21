# ComfyUI_DXF/dxf_add_star.py
import ezdxf
from ezdxf.addons import Importer
from .dxf_utils import DXFDoc, _BaseAdd
import math

class DXFAddStar(_BaseAdd):
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "dxf": ("DXF",),
            "cx": ("FLOAT", {"default": 0.0}),
            "cy": ("FLOAT", {"default": 0.0}),
            "outer_radius": ("FLOAT", {"default": 20.0, "min": 0.0001}),
            "inner_radius": ("FLOAT", {"default": 10.0, "min": 0.0001}),
            "num_points": ("INT", {"default": 5, "min": 3, "max": 100}),
        }}
    
    RETURN_TYPES = ("DXF",)
    FUNCTION = "add"
    CATEGORY = "DAO_master/DXF/Primitives"
    
    def add(self, dxf: DXFDoc, cx: float, cy: float, outer_radius: float, inner_radius: float, num_points: int):
        new_doc = ezdxf.new(); importer = Importer(dxf.doc, new_doc); importer.import_modelspace(); importer.finalize()
        new_msp = new_doc.modelspace()
        
        # S'assurer que le rayon intérieur est plus petit
        if inner_radius > outer_radius:
            inner_radius, outer_radius = outer_radius, inner_radius
            
        points = []
        total_vertices = 2 * num_points
        for i in range(total_vertices):
            angle = (2 * math.pi / total_vertices) * i
            radius = outer_radius if i % 2 == 0 else inner_radius
            pt_x = cx + radius * math.cos(angle)
            pt_y = cy + radius * math.sin(angle)
            points.append((pt_x, pt_y))

        new_msp.add_lwpolyline(points, format="xy", dxfattribs={"closed": True})
            
        return (DXFDoc(doc=new_doc, msp=new_msp, units=dxf.units),)

NODE_CLASS_MAPPINGS = {"DXF Add Star": DXFAddStar}
NODE_DISPLAY_NAME_MAPPINGS = {"DXF Add Star": "DXF Add Star"}