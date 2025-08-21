# ComfyUI_DXF/dxf_add_ellipse.py
import ezdxf
from ezdxf.addons import Importer
from .dxf_utils import DXFDoc, _BaseAdd

class DXFAddEllipse(_BaseAdd):
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "dxf": ("DXF",),
            "cx": ("FLOAT", {"default": 0.0}),
            "cy": ("FLOAT", {"default": 0.0}),
            "major_axis_x": ("FLOAT", {"default": 20.0}),
            "major_axis_y": ("FLOAT", {"default": 0.0}),
            "ratio": ("FLOAT", {"default": 0.5, "min": 0.0001, "max": 1.0}),
        }}
    
    RETURN_TYPES = ("DXF",)
    FUNCTION = "add"
    CATEGORY = "DAO_master/DXF/Primitives"
    
    def add(self, dxf: DXFDoc, cx: float, cy: float, major_axis_x: float, major_axis_y: float, ratio: float):
        new_doc = ezdxf.new(); importer = Importer(dxf.doc, new_doc); importer.import_modelspace(); importer.finalize()
        new_msp = new_doc.modelspace()

        new_msp.add_ellipse(center=(cx, cy), major_axis=(major_axis_x, major_axis_y), ratio=ratio)
            
        return (DXFDoc(doc=new_doc, msp=new_msp, units=dxf.units),)

NODE_CLASS_MAPPINGS = {"DXF Add Ellipse": DXFAddEllipse}
NODE_DISPLAY_NAME_MAPPINGS = {"DXF Add Ellipse": "DXF Add Ellipse"}