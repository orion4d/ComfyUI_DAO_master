# ComfyUI_DXF/dxf_import.py
import os
import ezdxf
from .dxf_utils import DXFDoc

class DXFImport:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "file_path": ("STRING", {"default": "C:/path/to/your/file.dxf"}),
        }}

    RETURN_TYPES = ("DXF",)
    FUNCTION = "load_dxf"
    CATEGORY = "DAO_master/DXF/IO"

    def load_dxf(self, file_path: str):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Fichier DXF non trouvé: {file_path}")

        try:
            doc = ezdxf.readfile(file_path)
            msp = doc.modelspace()
            # On ne peut pas connaître les unités, on met "unitless" par défaut
            dxf_doc = DXFDoc(doc=doc, msp=msp, units="unitless")
            print(f"DXF Import: Fichier '{os.path.basename(file_path)}' chargé avec {len(msp)} entités.")
            return (dxf_doc,)
        except Exception as e:
            raise IOError(f"Impossible de lire ou parser le fichier DXF: {e}")

NODE_CLASS_MAPPINGS = {"DXF Import": DXFImport}
NODE_DISPLAY_NAME_MAPPINGS = {"DXF Import": "DXF Import"}