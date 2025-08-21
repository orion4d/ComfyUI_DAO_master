# convertIMGtoSVG.py — v2.2.0 (Ajout sortie svg_text)
# IMG -> SVG (1-bit) via Potrace. Sorties: svg_path (STRING), svg_text (STRING), preview (IMAGE)

import os, re, shutil, subprocess, tempfile, time, traceback
import numpy as np
from PIL import Image
try:
    import torch
except Exception:
    torch = None

# ---------- helpers (inchangés) ----------
def _as_float(x, d):
    try: v = float(x); return v if v==v and v not in (float("inf"), float("-inf")) else d
    except Exception: return d
def _as_int(x, d):
    try: return int(float(x))
    except Exception: return d
def _sanitize_name(name: str) -> str:
    name = (name or "").strip() or "img2svg"
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name)
def _to_abs_outdir(path: str) -> str:
    path = os.path.expanduser(os.path.expandvars((path or "").strip())) or os.path.join(os.getcwd(), "output", "svg")
    if not os.path.isabs(path): path = os.path.abspath(os.path.join(os.getcwd(), path))
    os.makedirs(path, exist_ok=True)
    return path
def _image_from_comfy(img):
    if torch is not None and isinstance(img, torch.Tensor): arr = img[0].detach().cpu().numpy()
    else: arr = np.asarray(img)[0]
    arr = np.clip(arr, 0.0, 1.0)
    if arr.shape[-1] == 4: arr = arr[..., :3]
    rgb = (arr * 255.0 + 0.5).astype(np.uint8)
    return Image.fromarray(rgb, mode="RGB")
def _pil_to_comfy_image(img):
    arr = np.array(img).astype(np.float32) / 255.0
    if arr.ndim == 2: arr = np.stack([arr, arr, arr], -1)
    return torch.from_numpy(arr).unsqueeze(0) if torch is not None else arr[None, ...]

# ---------- binarisation (inchangée) ----------
def _gray(pil):
    return np.array(pil.convert("L"), dtype=np.uint8)
def _otsu(gray):
    hist = np.bincount(gray.ravel(), minlength=256).astype(np.float64)
    w = hist.sum();
    if w == 0: return 128
    sum_all = np.dot(np.arange(256), hist)
    sumB, wB, varMax, threshold = 0.0, 0.0, -1.0, 128
    for t in range(256):
        wB += hist[t];
        if wB == 0: continue
        wF = w - wB;
        if wF == 0: break
        sumB += t * hist[t]; mB = sumB / wB; mF = (sum_all - sumB) / wF
        var = wB * wF * (mB - mF) ** 2
        if var > varMax: varMax, threshold = var, t
    return threshold
def _mask_object(gray, thr, invert):
    return (gray < thr) if not invert else (gray >= thr)

# ---------- potrace (inchangé) ----------
def _potrace_bin_ok():
    return shutil.which("potrace") is not None
def _write_pbm(mask_obj_bool, path):
    pbm_data = mask_obj_bool.astype(np.uint8)
    height, width = pbm_data.shape
    header = f"P1\n{width} {height}\n"
    with open(path, 'w', encoding='ascii') as f:
        f.write(header)
        np.savetxt(f, pbm_data, fmt='%d')
def _trace_bin(mask_obj_bool, turd=2, amax=1.0, opt=0.2, policy="minority"):
    with tempfile.TemporaryDirectory() as td:
        pbm_path = os.path.join(td, "in.pbm")
        svg_path = os.path.join(td, "out.svg")
        try:
            _write_pbm(mask_obj_bool, pbm_path)
            cmd = ["potrace", "-s", "-o", svg_path, "-t", str(int(turd)), "-a", str(float(amax)), "-O", str(float(opt)), "-z", str(policy), "--tight", pbm_path]
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            with open(svg_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            raise RuntimeError("Le binaire 'potrace' est introuvable. Veuillez l'installer et vous assurer qu'il est dans le PATH.")
        except subprocess.CalledProcessError:
            raise RuntimeError("Erreur lors de l'exécution de Potrace. L'image est peut-être invalide (trop petite, vide...).")
def _trace_py(mask_obj_bool, turd=2, amax=1.0, opt=0.2, policy="minority"):
    try: import potrace as P
    except Exception as e: raise RuntimeError("Module 'potrace' introuvable. Installez le binaire ou `pip install potrace`.") from e
    bmp = P.Bitmap(mask_obj_bool.astype(np.uint8))
    path = bmp.trace(turdsize=int(turd), alphamax=float(amax), opttolerance=float(opt), turnpolicy=getattr(P, policy.upper(), P.MINORITY))
    if hasattr(path, "to_svg"): return path.to_svg()
    raise RuntimeError("API potrace python sans to_svg; installez le binaire.")
def _wrap_fillrule(svg_text, fill_rule="nonzero"):
    try:
        i = svg_text.lower().find("<path")
        if i != -1: return (svg_text[:i] + f'<g style="fill-rule:{fill_rule};">' + svg_text[i:].replace("</svg>", "</g></svg>"))
    except Exception: pass
    return svg_text

# ---------- Node ----------
class ConvertIMGtoSVG:
    @classmethod
    def INPUT_TYPES(cls): return {"required": {"image": ("IMAGE",),"threshold": ("INT", {"default": 128, "min": 0, "max": 255}),"auto_otsu": ("BOOLEAN", {"default": True}),"invert": ("BOOLEAN", {"default": False}),"turdsize": ("INT", {"default": 2, "min": 0, "max": 1000}),"alphamax": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 5.0}),"opttolerance": ("FLOAT", {"default": 0.2, "min": 0.0, "max": 5.0}),"turnpolicy": (["minority", "majority", "black", "white", "left", "right"], {"default": "minority"}),"fill_rule": (["nonzero", "evenodd"], {"default": "nonzero"}),"backend": (["auto", "potrace_bin", "potrace_py"], {"default": "auto"}),"save_svg": ("BOOLEAN", {"default": True}),"auto_prefix": ("BOOLEAN", {"default": True}),"out_dir": ("STRING", {"default": "output/svg"}),"out_name": ("STRING", {"default": "img2svg"}),}}

    # --- MODIFICATION DES SORTIES ---
    RETURN_TYPES = ("STRING", "SVG_TEXT", "IMAGE")
    RETURN_NAMES = ("svg_path", "svg_text", "preview")
    FUNCTION = "run"
    CATEGORY = "DAO_master/SVG/Convert"

    def run(self, image, threshold, auto_otsu, invert, turdsize, alphamax, opttolerance, turnpolicy, fill_rule, backend, save_svg, auto_prefix, out_dir, out_name):
        pil = _image_from_comfy(image)
        g = _gray(pil)
        thr = _otsu(g) if auto_otsu else int(_as_int(threshold, 128))
        mask_obj = _mask_object(g, thr, invert=invert)
        
        svg_text = ""
        try:
            if backend == "potrace_bin" or (backend == "auto" and _potrace_bin_ok()):
                svg_text = _trace_bin(mask_obj, _as_int(turdsize, 2), _as_float(alphamax, 1.0), _as_float(opttolerance, 0.2), turnpolicy)
            else:
                svg_text = _trace_py(mask_obj, _as_int(turdsize, 2), _as_float(alphamax, 1.0), _as_float(opttolerance, 0.2), turnpolicy)
            svg_text = _wrap_fillrule(svg_text, fill_rule)
        except Exception as e:
            print("--- ERREUR ConvertIMGtoSVG (Traçage) ---"); traceback.print_exc(); print("-----------------------------------------")
            prev_err = Image.fromarray((mask_obj.astype(np.uint8) * 255), "L").convert("RGB")
            # En cas d'erreur, on renvoie des valeurs vides pour toutes les sorties
            return ("", "", _pil_to_comfy_image(prev_err))

        svg_path = ""
        if save_svg:
            base = _to_abs_outdir(out_dir); name = _sanitize_name(out_name)
            if auto_prefix: name = f"{name}_{time.strftime('%Y%m%d-%H%M%S')}"
            if not name.lower().endswith(".svg"): name += ".svg"
            svg_path = os.path.join(base, name)
            try:
                with open(svg_path, "w", encoding="utf-8") as f: f.write(svg_text)
                print(f"SVG sauvegardé avec succès : {svg_path}")
            except Exception:
                print(f"--- ERREUR ConvertIMGtoSVG (Sauvegarde) ---"); print(f"Impossible de sauvegarder le fichier SVG à l'emplacement : {svg_path}"); traceback.print_exc(); print("-------------------------------------------")
                svg_path = ""

        prev = Image.fromarray((mask_obj.astype(np.uint8) * 255), "L").convert("RGB")
        # --- MODIFICATION DU RETURN ---
        return (svg_path, svg_text, _pil_to_comfy_image(prev))

NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS = {"ConvertIMGtoSVG": ConvertIMGtoSVG}, {"ConvertIMGtoSVG": "Convert IMG → SVG (1-bit)"}