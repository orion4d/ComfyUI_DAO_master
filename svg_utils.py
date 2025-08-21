# ComfyUI_DXF/svg_utils.py
import pyclipper
from lxml import etree
from svgpathtools import parse_path, Line, Arc, CubicBezier, QuadraticBezier

SCALE_FACTOR = 10000.0

def svg_string_to_clipper_paths(svg_text, curve_samples=60):
    if not svg_text or not svg_text.strip(): return []
    parser = etree.XMLParser(recover=True)
    root = etree.fromstring(svg_text.encode('utf-8'), parser)
    ns = {'svg': 'http://www.w3.org/2000/svg'}
    clipper_paths = []

    for path_element in root.xpath('//svg:path', namespaces=ns):
        d_string = path_element.get('d');
        if not d_string: continue
        path_obj = parse_path(d_string)
        if not path_obj: continue

        polygon = []
        # --- LOGIQUE D'ÉCHANTILLONNAGE DE HAUTE QUALITÉ ---
        for segment in path_obj:
            # On calcule le nombre de points en fonction de la longueur du segment
            # pour une qualité adaptative.
            length = segment.length()
            if length < 1.0: # Pour les très petits segments
                 num_samples = 2
            else:
                 num_samples = max(2, int(length / (100.0 / curve_samples)))

            # Si c'est une ligne, 2 points suffisent
            if isinstance(segment, Line): num_samples = 2

            for i in range(num_samples):
                point = segment.point(i / (num_samples - 1))
                polygon.append((int(point.real * SCALE_FACTOR), int(point.imag * SCALE_FACTOR)))
        
        if len(polygon) > 2:
            unique_polygon = [p for i, p in enumerate(polygon) if i == 0 or p != polygon[i-1]]
            if len(unique_polygon) > 2:
                clipper_paths.append(unique_polygon)

    return clipper_paths

def clipper_solution_to_svg_path_d(solution):
    d_string = ""
    if not solution: return d_string
    for path in solution:
        if not path or len(path) < 3: continue
        d_string += f"M {path[0][0] / SCALE_FACTOR} {path[0][1] / SCALE_FACTOR} "
        for point in path[1:]: d_string += f"L {point[0] / SCALE_FACTOR} {point[1] / SCALE_FACTOR} "
        d_string += "Z "
    return d_string.strip()