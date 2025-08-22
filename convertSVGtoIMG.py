# convertSVGtoIMG.py — v12.3 (Suppression de l'entrée svg_path pour plus de clarté)
import os, re, io, json, traceback
import numpy as np
from PIL import Image, ImageDraw
from xml.etree import ElementTree as ET

# ... [TOUTES LES FONCTIONS HELPER RESTENT IDENTIQUES] ...
try: from svgpathtools import parse_path, Path
except Exception: parse_path = None
try: import torch
except Exception: torch = None
from shapely.geometry import Polygon, LinearRing, LineString, MultiLineString, Point, box, MultiPolygon
from shapely.ops import unary_union
from shapely import affinity

def _pil_image_to_comfy_image(img, keep_alpha=False):
    arr = np.array(img).astype(np.float32)/255.0
    if arr.ndim == 2: arr = np.stack([arr,arr,arr], -1)
    if not keep_alpha and arr.shape[-1] == 4: arr = arr[...,:3]
    return torch.from_numpy(arr).unsqueeze(0) if torch is not None else arr[None,...]
def _pil_mask_to_comfy_mask(mask_img):
    m = np.array(mask_img.convert("L")).astype(np.float32)/255.0
    return torch.from_numpy(m).unsqueeze(0) if torch is not None else m[None,...]
# ... [Toutes les autres fonctions helpers jusqu'à la classe du Node] ...
def _parse_style_inline(style_str):
    out = {}
    if not style_str: return out
    for item in style_str.split(";"):
        if ":" in item:
            k,v = item.split(":",1); out[k.strip()] = v.strip()
    return out
def _strip_css_comments(s): return re.sub(r"/\*.*?\*/","",s,flags=re.S)
def _parse_css_classes(root):
    css = {}
    for st in root.findall(".//{http://www.w3.org/2000/svg}style"):
        txt = "".join(st.itertext()) or ""
        if not txt:
            continue
        txt = _strip_css_comments(txt)
        # .foo{...} et ".foo, .bar { ... }"
        for m in re.finditer(r"\.([A-Za-z0-9_-]+(?:\s*,\s*\.[A-Za-z0-9_-]+)*)\s*\{([^}]*)\}", txt, flags=re.S):
            selectors = [s.strip().lstrip(".") for s in m.group(1).split(",")]
            body = m.group(2)
            decl = _parse_style_inline(body)
            for cls in selectors:
                cur = css.get(cls, {}).copy()
                cur.update(decl)
                css[cls] = cur
    return css

def _hex_norm(v):
    if not v: return None
    v = v.strip().lower()
    if v in ("none","transparent"): return None
    if v.startswith("url("): return "degraded"
    m = re.match(r'rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', v)
    if m: r,g,b = (int(m.group(1)), int(m.group(2)), int(m.group(3))); return f'#{r:02x}{g:02x}{b:02x}'
    if re.match(r'^#([0-9a-f]{3})$', v): a,b,c = v[1],v[2],v[3]; return f'#{a}{a}{b}{b}{c}{c}'
    if re.match(r'^#([0-9a-f]{6})$', v): return v
    return v
def _rgb_from_hex(h):
    if not h or not isinstance(h,str) or not h.startswith("#") or len(h)!=7: return None
    return [int(h[1:3],16),int(h[3:5],16),int(h[5:7],16)]
def _parse_len(val, fallback=0.0):
    if val is None: return fallback
    s = str(val).strip().lower()
    m = re.match(r'^([+-]?\d*\.?\d+)\s*([a-z%]*)$', s)
    if not m:
        try: return float(s)
        except Exception: return fallback
    num = float(m.group(1)); unit = m.group(2)
    conv = {"":1.0,"px":1.0,"pt":96.0/72.0,"pc":16.0,"in":96.0,"mm":96.0/25.4,"cm":96.0/2.54,"q":96.0/101.6}
    return num * conv.get(unit, 1.0)
def _parse_transform_attr(attr):
    out=[]
    if not attr: return out
    try:
        for cmd,arg in re.findall(r'(\w+)\s*\(([^)]+)\)', attr.strip()):
            args=[float(a) for a in arg.replace(","," ").split()]
            out.append((cmd,args))
    except Exception: pass
    return out
def _apply_transform_chain(geom, chain):
    if not chain: return geom
    for cmd,args in chain:
        if cmd=="translate": geom=affinity.translate(geom, xoff=args[0], yoff=args[1] if len(args)>1 else 0.0)
        elif cmd=="scale": sx=args[0]; sy=args[1] if len(args)>1 else sx; geom=affinity.scale(geom, xfact=sx, yfact=sy, origin=(0,0))
        elif cmd=="rotate": geom=affinity.rotate(geom, args[0], origin=(0,0))
        elif cmd=="matrix" and len(args)==6: a,b,c,d,e,f = args; geom=affinity.affine_transform(geom,[a,b,c,d,e,f])
    return geom
def _parse_hex_any(h):
    if isinstance(h,dict): r,g,b=int(h.get('r',0)),int(h.get('g',0)),int(h.get('b',0)); return (max(0,min(255,r)),max(0,min(255,g)),max(0,min(255,b)))
    if not isinstance(h,str): return (255,255,255)
    s=h.strip().lower()
    if s.startswith('#') and len(s)==7:
        try: return (int(s[1:3],16),int(s[3:5],16),int(s[5:7],16))
        except Exception: return (255,255,255)
    m=re.match(r'rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', s)
    if m: return (int(m.group(1)),int(m.group(2)),int(m.group(3)))
    return (255,255,255)
XLINK="{http://www.w3.org/1999/xlink}href"
def _collect_styles(el, inh, css):
    style_inline=_parse_style_inline(el.get("style",""))
    cls_decl={}
    cls_attr = el.get("class","")
    if cls_attr:
        for c in cls_attr.split():
            if c in css: cls_decl.update(css[c])
    fill_here,stroke_here,sw_here=el.get("fill"),el.get("stroke"),el.get("stroke-width")
    if not fill_here: fill_here = style_inline.get("fill") or cls_decl.get("fill")
    if not stroke_here: stroke_here = style_inline.get("stroke") or cls_decl.get("stroke")
    if not sw_here: sw_here = style_inline.get("stroke-width") or cls_decl.get("stroke-width")
    eff_fill=_hex_norm(fill_here) if fill_here is not None else inh["fill"]
    eff_stroke=_hex_norm(stroke_here) if stroke_here is not None else inh["stroke"]
    eff_sw=_parse_len(sw_here, inh["stroke_width"])
    return eff_fill, eff_stroke, eff_sw
def _collect_shapes(svg_bytes):
    root = ET.fromstring(svg_bytes); css=_parse_css_classes(root); shapes=[]; visited_uses=set()
    def resolve_ref(href):
        if not href: return None
        if href.startswith("#"): href=href[1:]
        return root.find(f".//*[@id='{href}']")
    def add_fill(poly, col):
        try:
            g=poly if (poly.is_valid and poly.area> 1e-8) else poly.buffer(0)
            if g.is_valid and not g.is_empty and g.area>1e-8: shapes.append({"geom": g, "paint": col, "kind":"fill"})
        except: pass
    def add_stroke_lines(lines, width, col):
        w=width if width>0 else 1.5
        try:
            buf=lines.buffer(w*0.5, cap_style=1, join_style=1)
            buf=buf if (buf.is_valid and not buf.is_empty) else buf.buffer(0)
            if buf.is_valid and not buf.is_empty and buf.area> 1e-8: shapes.append({"geom": buf, "paint": col, "kind":"stroke"})
        except: pass
    def add_stroke_polygon(poly, width, col):
        try: add_stroke_lines(poly.exterior, width, col)
        except: pass
    def walk(el, inh):
        eff_fill, eff_stroke, eff_sw = _collect_styles(el, inh, css)
        tr_chain = inh["transform"] + _parse_transform_attr(el.get("transform"))
        tag = el.tag.split("}")[-1]
        try:
            if tag=="use":
                href=el.get(XLINK) or el.get("href"); ref=resolve_ref(href)
                if ref is not None:
                    key=(ref.get("id",""), id(ref))
                    if key in visited_uses: return
                    visited_uses.add(key)
                    dx=_parse_len(el.get("x",0)); dy=_parse_len(el.get("y",0))
                    inh2={"fill":eff_fill,"stroke":eff_stroke,"stroke_width":eff_sw,"transform":tr_chain+[("translate",[dx,dy])]}
                    walk(ref, inh2)
                return
            if tag=="rect":
                x,y,w,h=_parse_len(el.get("x",0)),_parse_len(el.get("y",0)),_parse_len(el.get("width",0)),_parse_len(el.get("height",0))
                if w>0 and h>0:
                    p=box(x,y,x+w,y+h); p=_apply_transform_chain(p,tr_chain)
                    if eff_fill is not None: add_fill(p, eff_fill)
                    if eff_stroke is not None and eff_sw>0: add_stroke_polygon(p,eff_sw,eff_stroke)
            elif tag in ("circle","ellipse"):
                cx,cy=_parse_len(el.get("cx",0)),_parse_len(el.get("cy",0))
                if tag=="circle": r=max(_parse_len(el.get("r",0)),0.1); p=Point(cx,cy).buffer(r,96)
                else: rx,ry=max(_parse_len(el.get("rx",0)),0.1),max(_parse_len(el.get("ry",0)),0.1); p=Point(cx,cy).buffer(1.0,96); p=affinity.scale(p,xfact=rx,yfact=ry,origin=(cx,cy))
                p=_apply_transform_chain(p,tr_chain)
                if eff_fill is not None: add_fill(p, eff_fill)
                if eff_stroke is not None and eff_sw>0: add_stroke_polygon(p,eff_sw,eff_stroke)
            elif tag=="polygon" or tag=="polyline":
                raw=(el.get("points","") or "").replace(","," "); vals=[v for v in raw.split() if v]; pts=[]
                if len(vals)>=4 and len(vals)%2==0:
                    for i in range(0,len(vals),2): pts.append((float(vals[i]), float(vals[i+1])))
                if len(pts)>=3:
                    is_closed = (tag=="polygon") or (np.linalg.norm(np.array(pts[0])-np.array(pts[-1]))< 1e-3)
                    if is_closed:
                        if np.linalg.norm(np.array(pts[0])-np.array(pts[-1]))>1e-6: pts.append(pts[0])
                        p=Polygon(LinearRing(pts)); p=_apply_transform_chain(p,tr_chain)
                        if eff_fill is not None: add_fill(p, eff_fill)
                        if eff_stroke is not None and eff_sw>0: add_stroke_polygon(p,eff_sw,eff_stroke)
                    else:
                        ls=LineString(pts); ls=_apply_transform_chain(ls,tr_chain)
                        if eff_stroke is not None: add_stroke_lines(ls,eff_sw,eff_stroke)
                        else: shapes.append({"geom": ls, "paint": eff_fill, "kind":"open"})
            elif tag=="path" and parse_path is not None:
                d=el.get("d","");
                if d:
                    try: pth:Path=parse_path(d)
                    except: pth=None
                    if pth:
                        try: subs=pth.continuous_subpaths()
                        except: subs=[pth]
                        rings, open_lines = [], []
                        for sp in subs:
                            pts = [ (seg.point(t).real, seg.point(t).imag) for seg in sp for t in np.linspace(0,1, max(2,int(seg.length()/2)+2)) ]
                            if len(pts)<2: continue
                            closed = (np.linalg.norm(np.array(pts[0])-np.array(pts[-1]))<1e-3) or sp.isclosed()
                            if closed and len(pts)>=3:
                                if np.linalg.norm(np.array(pts[0])-np.array(pts[-1]))>1e-6: pts.append(pts[0])
                                try:
                                    poly_i=Polygon(LinearRing(pts))
                                    if poly_i.is_valid and poly_i.area>1e-9: poly_i=_apply_transform_chain(poly_i,tr_chain); rings.append(poly_i)
                                except: pass
                            else: ls=LineString(pts); ls=_apply_transform_chain(ls,tr_chain); open_lines.append(ls)
                        if rings and eff_fill is not None:
                            geom_fill=unary_union(rings).buffer(0)
                            if geom_fill and not geom_fill.is_empty: shapes.append({"geom": geom_fill, "paint": eff_fill, "kind":"fill"})
                        if open_lines:
                            ml = MultiLineString(open_lines)
                            if eff_stroke is not None: add_stroke_lines(ml,eff_sw,eff_stroke)
                            else: shapes.append({"geom": ml, "paint": eff_fill, "kind":"open"})
            child_inh={"fill":eff_fill,"stroke":eff_stroke,"stroke_width":eff_sw,"transform":inh["transform"]+_parse_transform_attr(el.get("transform"))}
            for ch in list(el): walk(ch, child_inh)
        except: pass
    walk(root, {"fill":None,"stroke":None,"stroke_width":0.0,"transform":[]})
    return shapes, root
def _viewbox_aspect(root, shapes):
    vb=root.get("viewBox")
    if vb:
        parts=[p for p in vb.replace(","," ").split() if p]
        if len(parts)==4:
            try: _,_,vw,vh=[float(x) for x in parts]; return (vw/vh) if vw>0 and vh>0 else 1.0
            except: pass
    try:
        vw=float((root.get("width") or "0").replace("px","")); vh=float((root.get("height") or "0").replace("px",""))
        if vw>0 and vh>0: return vw/vh
    except: pass
    polys=[s["geom"] for s in shapes if hasattr(s["geom"],"bounds")]
    if not polys: return 1.0
    minx,miny=min(p.bounds[0] for p in polys),min(p.bounds[1] for p in polys)
    maxx,maxy=max(p.bounds[2] for p in polys),max(p.bounds[3] for p in polys)
    w,h=maxx-minx,maxy-miny
    return (w/h) if (w>0 and h>0) else 1.0
def _rasterize_native(shapes, out_w, out_h, bg_hex, transparent, pad_px, stroke_only, open_subpaths_px):
    out_w,out_h,pad_px=int(out_w),int(out_h),int(max(0,pad_px))
    mode="RGBA" if transparent else "RGB"; fill=(0,0,0,0) if transparent else _parse_hex_any(bg_hex)
    if not shapes: return Image.new(mode,(out_w,out_h),fill)
    geoms=[s["geom"] for s in shapes if hasattr(s["geom"],"bounds")]
    minx,miny=min(g.bounds[0] for g in geoms),min(g.bounds[1] for g in geoms)
    maxx,maxy=max(g.bounds[2] for g in geoms),max(g.bounds[3] for g in geoms)
    w,h=float(maxx-minx),float(maxy-miny)
    if w<=1e-12 or h<=1e-12: return Image.new(mode,(out_w,out_h),fill)
    s=min(float(out_w-2*pad_px)/max(w,1e-8), float(out_h-2*pad_px)/max(h,1e-8))
    offx,offy=float(pad_px)+(float(out_w-2*pad_px)-s*w)*0.5, float(pad_px)+(float(out_h-2*pad_px)-s*h)*0.5
    def to_px(pt): return (int(round((float(pt[0])-minx)*s+offx)), int(round((float(pt[1])-miny)*s+offy)))
    bg=_parse_hex_any(bg_hex); img=Image.new(mode,(out_w,out_h),(0,0,0,0) if transparent else bg)
    draw=ImageDraw.Draw(img)
    def paint_polygon(p, color_rgb):
        ex=[to_px(v) for v in p.exterior.coords]
        draw.polygon(ex, fill=(color_rgb+(255,)) if transparent else color_rgb)
        for hole in p.interiors: hx=[to_px(v) for v in hole.coords]; draw.polygon(hx, fill=(0,0,0,0) if transparent else bg)
    for sshape in shapes:
        kind,geom,paint=sshape.get("kind","fill"),sshape["geom"],sshape["paint"]
        col_rgb=_parse_hex_any(paint) if (isinstance(paint,str) and paint!="degraded") else (255,255,255)
        if (stroke_only and kind not in ("stroke","open")) or ((not stroke_only) and kind not in ("fill","stroke","open")): continue
        if isinstance(geom, (Polygon,MultiPolygon)):
            if kind=="fill" or (not stroke_only and kind=="stroke"):
                polys = geom.geoms if isinstance(geom,MultiPolygon) else [geom]
                for p in polys: paint_polygon(p, col_rgb)
        elif kind=="open" and open_subpaths_px>0:
            w_geom=(open_subpaths_px/max(s,1e-8))*0.5
            try:
                buf=geom.buffer(w_geom,cap_style=1,join_style=1)
                if buf.is_valid and not buf.is_empty:
                    polys = buf.geoms if isinstance(buf,MultiPolygon) else [buf]
                    for p in polys: paint_polygon(p, col_rgb)
            except: pass
    return img
def _rasterize_cairo(svg_bytes, width, transparent_bg, background_hex, pad_px):
    try: import cairosvg
    except Exception as e: raise RuntimeError("CairoSVG n'est pas installé. `pip install cairosvg`.") from e
    bg = 'rgba(0,0,0,0)' if transparent_bg else _rgba_str(_parse_hex_any(background_hex))
    png_bytes = cairosvg.svg2png(bytestring=svg_bytes, output_width=int(width), background_color=bg)
    im = Image.open(io.BytesIO(png_bytes)).convert("RGBA" if transparent_bg else "RGB")
    if pad_px>0:
        w,h=im.size; mode="RGBA" if transparent_bg else "RGB"
        canvas=Image.new(mode,(w+2*pad_px,h+2*pad_px),(0,0,0,0) if transparent_bg else _parse_hex_any(background_hex))
        canvas.paste(im,(pad_px,pad_px), im if im.mode=="RGBA" else None)
        im=canvas
    return im
def _rgba_str(rgb): return f"rgba({rgb[0]},{rgb[1]},{rgb[2]},1)" if len(rgb)==3 else "rgba(0,0,0,1)"
def _mask_coverage(img, background_hex):
    if img.mode=="RGBA": return float((np.array(img.split()[-1])>0).mean())
    arr,bg=np.array(img),_parse_hex_any(background_hex)
    diff=(arr[:,:,0]!=bg[0])|(arr[:,:,1]!=bg[1])|(arr[:,:,2]!=bg[2])
    return float(diff.mean())

# ---------- Node ----------
class ConvertSVGtoIMG:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required":{
                "svg_text": ("SVG_TEXT", {"multiline": True, "default": ""}),
            },
            "optional": {
                # "svg_path": ("STRING", {"default": ""}),  <-- SUPPRIMÉ
                "width": ("INT", {"default": 512, "min":16, "max":4096}),
                "scale_in_canvas": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 2.0, "step": 0.01}),
                "transparent_bg": ("BOOLEAN", {"default": False}),
                "background_hex": ("STRING", {"default": "#000000"}),
                "pad_px": ("INT", {"default": 0, "min":0, "max":512}),
                "keep_alpha_as_mask": ("BOOLEAN", {"default": True}),
                "stroke_only": ("BOOLEAN", {"default": False}),
                "open_subpaths_px": ("INT", {"default": 0, "min":0, "max":512}),
                "renderer": (["auto","native","cairosvg"], {"default": "auto"}),
            }
        }

    RETURN_TYPES=("IMAGE","MASK","STRING")
    RETURN_NAMES=("image","mask","colors_json")
    FUNCTION="run"
    CATEGORY = "DAO_master/SVG/Convert"

    def run(self, svg_text, width=512, scale_in_canvas=1.0, transparent_bg=False, 
            background_hex="#000000", pad_px=0, keep_alpha_as_mask=True, stroke_only=False, 
            open_subpaths_px=0, renderer="auto"):

        # --- LOGIQUE D'ENTRÉE SIMPLIFIÉE ---
        if not svg_text or not svg_text.strip():
            raise ValueError("Aucune entrée SVG (svg_text) n'a été fournie.")
        
        svg_bytes = svg_text.strip().encode('utf-8')
        
        try:
            root = ET.fromstring(svg_bytes)
            viewBox = root.get('viewBox')
            if viewBox and abs(scale_in_canvas - 1.0) > 1e-6:
                vx, vy, vw, vh = map(float, viewBox.split())
                new_w, new_h = vw / scale_in_canvas, vh / scale_in_canvas
                new_x, new_y = vx - (new_w - vw) / 2, vy - (new_h - vh) / 2
                root.set('viewBox', f'{new_x} {new_y} {new_w} {new_h}')
                svg_bytes = ET.tostring(root, encoding='utf-8')
        except Exception as e: print(f"Avertissement: Impossible d'ajuster la viewBox du SVG: {e}")

        shapes, root = _collect_shapes(svg_bytes)
        report=[]
        for i,s in enumerate(shapes):
            paint,kind=s["paint"],s.get("kind","fill")
            entry={"index":i,"kind":kind,"type":"flat","hex":paint,"rgb":_rgb_from_hex(paint)} if paint not in ("degraded",None) else {"index":i,"kind":kind,"type":paint or "none"}
            report.append(entry)

        aspect=_viewbox_aspect(root, shapes)
        out_w=int(width); out_h=max(1,int(round(out_w/max(aspect,1e-8))))

        img = None
        if renderer in ("native","auto"):
            try: img = _rasterize_native(shapes, out_w, out_h, bg_hex=background_hex, transparent=transparent_bg, pad_px=int(pad_px), stroke_only=bool(stroke_only), open_subpaths_px=int(open_subpaths_px))
            except Exception as e: print(f"Erreur du renderer 'native': {e}"); img = None
        if img is None or (renderer == "auto" and _mask_coverage(img, background_hex) < 0.005):
            try: img = _rasterize_cairo(svg_bytes, out_w, transparent_bg, background_hex, pad_px)
            except Exception as e: raise RuntimeError(f"Les deux renderers ont échoué. Erreur CairoSVG: {e}")

        if keep_alpha_as_mask:
            if img.mode=="RGBA": mask_img=img.split()[-1]
            else:
                bg=_parse_hex_any(background_hex); arr=np.array(img.convert("RGB"))
                diff=(arr[:,:,0]!=bg[0])|(arr[:,:,1]!=bg[1])|(arr[:,:,2]!=bg[2])
                mask_arr=diff.astype(np.uint8)*255; mask_img=Image.fromarray(mask_arr,mode="L")
        else: mask_img = Image.new("L", img.size, 255)

        return (_pil_image_to_comfy_image(img, keep_alpha=transparent_bg), _pil_mask_to_comfy_mask(mask_img), json.dumps(report, ensure_ascii=False, indent=2))

NODE_CLASS_MAPPINGS={"ConvertSVGtoIMG": ConvertSVGtoIMG}
NODE_DISPLAY_NAME_MAPPINGS={"ConvertSVGtoIMG": "Convert SVG → IMG (+colors)"}