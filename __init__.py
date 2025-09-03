# -*- coding: utf-8 -*-
# ComfyUI_DAO_master / __init__.py

NODE_ID = "DAO_master" 

from .dxf_new import DXFNew
from .dxf_add_circle import DXFAddCircle
from .dxf_add_rectangle import DXFAddRectangle
from .dxf_add_triangle import DXFAddTriangle
from .dxf_add_line import DXFAddLine
from .dxf_preview import DXFPreview
from .dxf_save import DXFSave
from .dxf_stats import DXFStats
from .dxf_import import DXFImport
from .dxf_to_svg import DxfToSvg
from .svg_style import SvgStyle
from .svg_boolean import SvgBoolean
from .svg_preview import SvgPreview
from .svg_passthrough import SvgPassthrough
from .dxf_add_rounded_rectangle import DXFAddRoundedRectangle
from .dxf_add_polygon import DXFAddPolygon
from .dxf_add_ellipse import DXFAddEllipse
from .dxf_add_star import DXFAddStar
from .dxf_transform import DXFTransform
from .svg_save import SvgSave
from .convertSVGtoIMG import ConvertSVGtoIMG
from .convertIMGtoSVG import ConvertIMGtoSVG
from .dao_RVB_color_picker import DAORVBColorPicker
from .dao_text_maker import DAOTextMaker
from .dao_move import DAOMove
from .dao_blur import DAOBlur
from .svg_load import SVGLoad
from .folder_file_pro import FolderFilePro
from .path_to_image import PathToImage
from .load_image_pro import LoadImagePro
from .dao_clone_grid import DAOCloneGrid
from .dao_clone_circular import DAOCloneCircular
from .dao_clone_circular_path import DAOCloneCircularPath
from .dao_clone_grid_path import DAOCloneGridPath
from .mosaic_nodes import (
    MosaicTileExport,
    MosaicTileAssemble,
    MosaicAssembleFromFolder,
)

# Dictionnaires de mapping
NODE_CLASS_MAPPINGS = {
    "DXF New": DXFNew,
    "DXF Add Circle": DXFAddCircle,
    "DXF Add Rectangle": DXFAddRectangle,
    "DXF Add Rounded Rectangle": DXFAddRoundedRectangle,
    "DXF Add Triangle": DXFAddTriangle,
    "DXF Add Polygon": DXFAddPolygon,
    "DXF Add Line": DXFAddLine,
    "DXF Add Ellipse": DXFAddEllipse,
    "DXF Add Star": DXFAddStar,
    "DXF Preview": DXFPreview,
    "DXF Save": DXFSave,
    "DXF Stats": DXFStats,
    "DXF Import": DXFImport,
    "DXF to SVG": DxfToSvg,
    "DXF Transform": DXFTransform,
    "SVG Style": SvgStyle,
    "SVG Boolean": SvgBoolean,
    "SVG Preview": SvgPreview,
    "SVG Passthrough": SvgPassthrough,
    "SVG Save": SvgSave,
    "ConvertSVGtoIMG": ConvertSVGtoIMG,
    "ConvertIMGtoSVG": ConvertIMGtoSVG,
    "DAO RVB Color Picker": DAORVBColorPicker,
    "DAO Text Maker": DAOTextMaker,
    "DAO Move": DAOMove,
    "DAO Blur": DAOBlur,
    "SVG Load": SVGLoad,
    "Folder File Pro": FolderFilePro,
    "Path To Image": PathToImage,
    "Load Image Pro": LoadImagePro,
    "DAO Clone Grid": DAOCloneGrid,
    "DAO Clone Circular": DAOCloneCircular,
    "DAO Clone Circular Path": DAOCloneCircularPath,
    "DAO Clone Grid Path": DAOCloneGridPath,
    "MosaicTileExport": MosaicTileExport,
    "MosaicTileAssemble": MosaicTileAssemble,
    "MosaicAssembleFromFolder": MosaicAssembleFromFolder,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DXF New": "DXF New (ezdxf)",
    "DXF Add Circle": "DXF Add Circle",
    "DXF Add Rectangle": "DXF Add Rectangle",
    "DXF Add Rounded Rectangle": "DXF Add Rounded Rectangle",
    "DXF Add Triangle": "DXF Add Triangle",
    "DXF Add Polygon": "DXF Add Polygon",
    "DXF Add Line": "DXF Add Line",
    "DXF Add Ellipse": "DXF Add Ellipse",
    "DXF Add Star": "DXF Add Star",
    "DXF Preview": "DXF Preview (from DXF)",
    "DXF Save": "DXF Save",
    "DXF Stats": "DXF Stats (bbox & count)",
    "DXF Import": "DXF Import",
    "DXF to SVG": "Convertisseur DXF vers SVG",
    "DXF Transform": "DXF Transform (Rotate, Scale, Move)",
    "SVG Style": "Style SVG (Remplissage/Contour)",
    "SVG Boolean": "Opération Booléenne SVG",
    "SVG Preview": "Prévisualisation SVG",
    "SVG Passthrough": "SVG Passthrough (Text vers String)",
    "SVG Save": "SVG Save",
    "ConvertSVGtoIMG": "Convert SVG → IMG (+colors)",
    "ConvertIMGtoSVG": "Convert IMG → SVG (1-bit)",
    "DAO RVB Color Picker": "RVB Color Picker",
    "DAO Text Maker": "Text Maker",
    "DAO Move": "Move-Scale-Rotate-Sym",
    "DAO Blur": "Blur (Gaussian)",
    "SVG Load": "SVG Load (fichier → SVG_TEXT)",
    "Folder File Pro": "Folder File Pro (dir → file_path)",
    "Path To Image": "Path → Image (+RGBA/Mask/Meta)",
    "Load Image Pro": "Load Image Pro (Path/Image → RGB/RGBA/Mask/Upscale)",
    "DAO Clone Grid": "Clone Grid (X/Y)",
    "DAO Clone Circular": "Clone Circular",
    "DAO Clone Circular Path": "Clone Circular (Path)",
    "DAO Clone Grid Path": "Clone Grid (Path)",
    "MosaicTileExport": "Mosaic: Tile & Export",
    "MosaicTileAssemble": "Mosaic: Assemble (Batch)",
    "MosaicAssembleFromFolder": "Mosaic: Assemble (Folder)",
}

WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]

print(f"### Loading: {NODE_ID}")
print(f"    - Mapped {len(NODE_CLASS_MAPPINGS)} nodes")