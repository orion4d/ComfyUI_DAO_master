# ComfyUI_DXF/dxf_add_rounded_rectangle.py
import ezdxf
from ezdxf.addons import Importer
from .dxf_utils import DXFDoc, _BaseAdd
import math

class DXFAddRoundedRectangle(_BaseAdd):
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "dxf": ("DXF",),
            "x": ("FLOAT", {"default": 0.0}),
            "y": ("FLOAT", {"default": 0.0}),
            "width": ("FLOAT", {"default": 20.0, "min": 0.0001}),
            "height": ("FLOAT", {"default": 10.0, "min": 0.0001}),
            "radius": ("FLOAT", {"default": 2.0, "min": 0.0}),
            "centered": ("BOOLEAN", {"default": False}),
        }}
    
    RETURN_TYPES = ("DXF",)
    FUNCTION = "add"
    CATEGORY = "DAO_master/DXF/Primitives"
    
    def add(self, dxf: DXFDoc, x: float, y: float, width: float, height: float, radius: float, centered: bool):
        new_doc = ezdxf.new(); importer = Importer(dxf.doc, new_doc); importer.import_modelspace(); importer.finalize()
        new_msp = new_doc.modelspace()

        if centered: x0, y0 = x - width / 2.0, y - height / 2.0
        else: x0, y0 = x, y
        x1, y1 = x0 + width, y0 + height
        
        radius = min(radius, width / 2.0, height / 2.0)

        if radius <= 1e-6: # Si le rayon est quasi nul, on dessine un rectangle standard
            pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
            new_msp.add_lwpolyline(pts, format="xy", dxfattribs={"closed": True})
        else:
            # --- NOUVELLE LOGIQUE GÉOMÉTRIQUE CORRECTE ---
            # La valeur "bulge" pour un arc de 90 degrés est tan(90/4) = tan(22.5)
            # Le signe du bulge détermine la direction (horaire ou anti-horaire)
            bulge = math.tan(math.radians(22.5))

            # On définit les 4 points des coins, où les arcs sont dessinés.
            # Entre ces points, les segments sont des lignes droites (bulge=0).
            points = [
                (x0 + radius, y0, 0, 0, 0),          # Début de la ligne droite supérieure
                (x1 - radius, y0, 0, 0, bulge),      # Fin de la ligne sup., début de l'arc du coin droit
                (x1, y0 + radius, 0, 0, 0),          # Début de la ligne droite droite
                (x1, y1 - radius, 0, 0, bulge),      # Fin de la ligne droite, début de l'arc du coin bas
                (x1 - radius, y1, 0, 0, 0),          # Début de la ligne droite inférieure
                (x0 + radius, y1, 0, 0, bulge),      # Fin de la ligne inf., début de l'arc du coin gauche
                (x0, y1 - radius, 0, 0, 0),          # Début de la ligne droite gauche
                (x0, y0 + radius, 0, 0, bulge)       # Fin de la ligne gauche, début de l'arc du coin haut
            ]
            new_msp.add_lwpolyline(points, dxfattribs={"closed": True})
            
        return (DXFDoc(doc=new_doc, msp=new_msp, units=dxf.units),)

NODE_CLASS_MAPPINGS = {"DXF Add Rounded Rectangle": DXFAddRoundedRectangle}
NODE_DISPLAY_NAME_MAPPINGS = {"DXF Add Rounded Rectangle": "DXF Add Rounded Rectangle"}