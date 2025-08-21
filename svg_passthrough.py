# ComfyUI_DXF/svg_passthrough.py

class SvgPassthrough:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "svg_text": ("SVG_TEXT",),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("string",)
    FUNCTION = "passthrough"
    CATEGORY = "DAO_master/SVG/Utils"

    def passthrough(self, svg_text):
        """
        Ce node agit comme un simple adaptateur. Il prend le SVG_TEXT
        et le renvoie en tant que STRING standard pour la compatibilité.
        """
        return (svg_text,)

NODE_CLASS_MAPPINGS = {"SVG Passthrough": SvgPassthrough}
NODE_DISPLAY_NAME_MAPPINGS = {"SVG Passthrough": "SVG Passthrough (Text vers String)"}