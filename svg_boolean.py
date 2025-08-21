# ComfyUI_DXF/svg_boolean.py
from lxml import etree
import pyclipper
from .svg_utils import svg_string_to_clipper_paths, clipper_solution_to_svg_path_d

class SvgBoolean:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "svg_a": ("SVG_TEXT",),
            "svg_b": ("SVG_TEXT",),
            "operation": (["union", "difference", "intersection", "xor"],),
            # --- AJOUT DU CONTRÔLE DE QUALITÉ ---
            "curve_quality": ("INT", {"default": 60, "min": 10, "max": 400}),
        }}
    RETURN_TYPES = ("SVG_TEXT",)
    FUNCTION = "execute"
    CATEGORY = "DAO_master/SVG"

    def execute(self, svg_a, svg_b, operation, curve_quality):
        # --- ON PASSE LE PARAMÈTRE AUX FONCTIONS DE CONVERSION ---
        paths_a = svg_string_to_clipper_paths(svg_a, curve_quality)
        paths_b = svg_string_to_clipper_paths(svg_b, curve_quality)

        if not paths_a: raise ValueError("Le SVG 'A' est vide.")
        if not paths_b and operation != "union": raise ValueError("Le SVG 'B' est requis.")

        pc = pyclipper.Pyclipper()
        pc.AddPaths(paths_a, pyclipper.PT_SUBJECT, True)
        if paths_b: pc.AddPaths(paths_b, pyclipper.PT_CLIP, True)

        op_map = {"union": pyclipper.CT_UNION, "difference": pyclipper.CT_DIFFERENCE, "intersection": pyclipper.CT_INTERSECTION, "xor": pyclipper.CT_XOR}
        solution = pc.Execute(op_map[operation], pyclipper.PFT_EVENODD, pyclipper.PFT_EVENODD)
        result_d = clipper_solution_to_svg_path_d(solution)
        
        # ... (le reste du code pour la viewBox est inchangé) ...
        viewBox = "0 0 512 512"
        try:
            root_a = etree.fromstring(svg_a.encode('utf-8'))
            root_b = etree.fromstring(svg_b.encode('utf-8'))
            vb_a = list(map(float, root_a.get('viewBox').split()))
            vb_b = list(map(float, root_b.get('viewBox').split()))
            min_x,min_y = min(vb_a[0],vb_b[0]), min(vb_a[1],vb_b[1])
            max_x,max_y = max(vb_a[0]+vb_a[2],vb_b[0]+vb_b[2]), max(vb_a[1]+vb_a[3],vb_b[1]+vb_b[3])
            viewBox = f"{min_x} {min_y} {max_x - min_x} {max_y - min_y}"
        except Exception:
             try:
                root_a = etree.fromstring(svg_a.encode('utf-8'))
                if 'viewBox' in root_a.attrib: viewBox = root_a.attrib['viewBox']
             except Exception: pass

        result_svg = f'<svg viewBox="{viewBox}" xmlns="http://www.w3.org/2000/svg">\n  <path d="{result_d}" />\n</svg>'
        return (result_svg,)

NODE_CLASS_MAPPINGS = {"SVG Boolean": SvgBoolean}
NODE_DISPLAY_NAME_MAPPINGS = {"SVG Boolean": "Opération Booléenne SVG"}