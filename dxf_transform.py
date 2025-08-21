# ComfyUI_DXF/dxf_transform.py
import ezdxf
import math # <--- AJOUTER L'IMPORT MANQUANT
from ezdxf.addons import Importer
from .dxf_utils import DXFDoc, _BaseAdd, _bbox_from_entities

class DXFTransform(_BaseAdd):
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "dxf": ("DXF",),
            "translate_x": ("FLOAT", {"default": 0.0, "step": 1.0}),
            "translate_y": ("FLOAT", {"default": 0.0, "step": 1.0}),
            "scale": ("FLOAT", {"default": 1.0, "min": 0.001, "step": 0.01}),
            "rotation_degrees": ("FLOAT", {"default": 0.0, "min": -360.0, "max": 360.0, "step": 1.0}),
            "rotation_center": (["object_center", "origin"],),
        }}
    
    RETURN_TYPES = ("DXF",)
    FUNCTION = "transform"
    CATEGORY = "DAO_master/DXF/Modify"
    
    def transform(self, dxf: DXFDoc, translate_x: float, translate_y: float, scale: float, rotation_degrees: float, rotation_center: str):
        new_doc = ezdxf.new(); importer = Importer(dxf.doc, new_doc); importer.import_modelspace(); importer.finalize()
        new_msp = new_doc.modelspace()

        if abs(translate_x) < 1e-6 and abs(translate_y) < 1e-6 and abs(scale - 1.0) < 1e-6 and abs(rotation_degrees) < 1e-6:
            return (DXFDoc(doc=new_doc, msp=new_msp, units=dxf.units),)

        center_point = (0, 0)
        if rotation_center == "object_center":
            bbox = _bbox_from_entities(new_msp)
            if bbox:
                min_x, min_y, max_x, max_y = bbox
                center_point = ((min_x + max_x) / 2.0, (min_y + max_y) / 2.0)
        
        transform_chain = ezdxf.math.Matrix44()
        
        transform_chain @= ezdxf.math.Matrix44.translate(-center_point[0], -center_point[1], 0)
        transform_chain @= ezdxf.math.Matrix44.scale(scale, scale, 1)
        # --- CORRECTION : Utiliser math.radians() au lieu de ezdxf.math.radians() ---
        transform_chain @= ezdxf.math.Matrix44.z_rotate(math.radians(rotation_degrees))
        transform_chain @= ezdxf.math.Matrix44.translate(center_point[0], center_point[1], 0)
        transform_chain @= ezdxf.math.Matrix44.translate(translate_x, translate_y, 0)

        for entity in new_msp:
            try:
                entity.transform(transform_chain)
            except (AttributeError, TypeError):
                print(f"Avertissement : L'entité de type {entity.dxftype()} ne peut pas être transformée.")
                continue

        return (DXFDoc(doc=new_doc, msp=new_msp, units=dxf.units),)

NODE_CLASS_MAPPINGS = {"DXF Transform": DXFTransform}
NODE_DISPLAY_NAME_MAPPINGS = {"DXF Transform": "DXF Transform (Rotate, Scale, Move)"}