# ComfyUI_DXF/dxf_add_circle.py
import ezdxf
from ezdxf.addons import Importer
from .dxf_utils import DXFDoc, _BaseAdd

class DXFAddCircle(_BaseAdd):
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "dxf": ("DXF",),
            "cx": ("FLOAT", {"default": 0.0}),
            "cy": ("FLOAT", {"default": 0.0}),
            "radius": ("FLOAT", {"default": 10.0, "min": 0.0001}),
        }}
    
    RETURN_TYPES = ("DXF",)
    FUNCTION = "add"
    CATEGORY = "DAO_master/DXF/Primitives"
    
    def add(self, dxf: DXFDoc, cx: float, cy: float, radius: float):
        # Créer un nouveau document vierge pour la sortie
        new_doc = ezdxf.new()
        
        # Importer le contenu de l'ancien document dans le nouveau
        importer = Importer(dxf.doc, new_doc)
        importer.import_modelspace()
        importer.finalize()
        
        # Ajouter le nouveau cercle au document fraîchement copié
        new_msp = new_doc.modelspace()
        new_msp.add_circle(center=(cx, cy), radius=radius)
        
        return (DXFDoc(doc=new_doc, msp=new_msp, units=dxf.units),)

NODE_CLASS_MAPPINGS = {"DXF Add Circle": DXFAddCircle}
NODE_DISPLAY_NAME_MAPPINGS = {"DXF Add Circle": "DXF Add Circle"}