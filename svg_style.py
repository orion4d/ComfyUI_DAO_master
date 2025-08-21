# ComfyUI_DXF/svg_style.py
from lxml import etree

class SvgStyle:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "svg_text": ("SVG_TEXT",),
            "fill_enabled": ("BOOLEAN", {"default": True}),
            "fill_color": ("STRING", {"default": "#00A2FF", "multiline": False}),
            "stroke_color": ("STRING", {"default": "#000000", "multiline": False}),
            "stroke_width": ("FLOAT", {"default": 1.0, "min": 0.0, "step": 0.1}),
        }}
    RETURN_TYPES = ("SVG_TEXT",)
    FUNCTION = "style_svg"
    CATEGORY = "DAO_master/SVG"

    def style_svg(self, svg_text, fill_enabled, fill_color, stroke_color, stroke_width):
        if not svg_text or not svg_text.strip(): return (svg_text,)
        parser = etree.XMLParser(remove_blank_text=True)
        root = etree.fromstring(svg_text.encode('utf-8'), parser)
        ns = {'svg': 'http://www.w3.org/2000/svg'}

        for path in root.xpath('//svg:path', namespaces=ns):
            path.set('fill', fill_color if fill_enabled else 'none')
            if stroke_width > 0:
                path.set('stroke', stroke_color)
                path.set('stroke-width', str(stroke_width))
            else:
                path.set('stroke', 'none')
        
        return (etree.tostring(root, pretty_print=True).decode('utf-8'),)

NODE_CLASS_MAPPINGS = {"SVG Style": SvgStyle}
NODE_DISPLAY_NAME_MAPPINGS = {"SVG Style": "Style SVG (Remplissage/Contour)"}