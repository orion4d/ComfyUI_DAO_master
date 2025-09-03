import os, math, glob, time, re
from typing import List, Tuple, Dict
import numpy as np
from PIL import Image

try:
    import torch
except Exception:
    torch = None

# ==== Utils communs ====

def _tensor_to_numpy_single(img: "torch.Tensor") -> np.ndarray:
    if img is None:
        raise ValueError("Image tensor is None.")
    if img.ndim == 4:
        img = img[0]
    if img.ndim != 3:
        raise ValueError(f"Unexpected image ndim={img.ndim}, expected 3 or 4.")
    arr = img.detach().cpu().numpy()
    arr = np.clip(arr, 0.0, 1.0)
    arr = (arr * 255.0 + 0.5).astype(np.uint8)
    return arr

def _tensor_batch_to_numpy(imgs: "torch.Tensor") -> np.ndarray:
    if imgs is None or imgs.ndim != 4:
        raise ValueError("Expected IMAGE batch with shape (N,H,W,C).")
    arr = imgs.detach().cpu().numpy()
    arr = np.clip(arr, 0.0, 1.0)
    arr = (arr * 255.0 + 0.5).astype(np.uint8)
    return arr

def _numpy_to_tensor(arr: np.ndarray) -> "torch.Tensor":
    if arr.ndim == 3:
        arr = arr[None, ...]
    t = torch.from_numpy(arr.astype(np.float32) / 255.0)
    return t

def _ensure_mode(arr: np.ndarray) -> Tuple[np.ndarray, str]:
    C = arr.shape[2]
    if C == 1:
        arr = np.repeat(arr, 3, axis=2)
        return arr, "RGB"
    elif C == 3:
        return arr, "RGB"
    elif C == 4:
        return arr, "RGBA"
    else:
        arr = arr[:, :, :3]
        return arr, "RGB"

def _save_pil(img: Image.Image, path: str, filetype: str, quality: int = 95) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    ft = filetype.lower()
    if ft == "png":
        img.save(path, format="PNG", compress_level=4)
    elif ft in ("jpg", "jpeg"):
        if img.mode in ("RGBA", "LA"):
            img = img.convert("RGB")
        img.save(path, format="JPEG", quality=int(quality), subsampling=1, optimize=True)
    else:
        img.save(path)

def _parse_hex_color(hex_str: str) -> Tuple[int, int, int]:
    s = hex_str.strip().lstrip("#")
    if len(s) == 3:
        s = "".join([ch*2 for ch in s])
    if len(s) != 6:
        raise ValueError(f"Invalid hex color: {hex_str}")
    return int(s[0:2],16), int(s[2:4],16), int(s[4:6],16)

def _make_canvas(width: int, height: int, rgba: bool, bg_rgb=(0,0,0), bg_alpha: int = 0) -> np.ndarray:
    if rgba:
        canvas = np.zeros((height, width, 4), dtype=np.uint8)
        canvas[...,0] = bg_rgb[0]; canvas[...,1] = bg_rgb[1]; canvas[...,2] = bg_rgb[2]; canvas[...,3] = np.clip(bg_alpha,0,255)
    else:
        canvas = np.zeros((height, width, 3), dtype=np.uint8)
        canvas[...,0] = bg_rgb[0]; canvas[...,1] = bg_rgb[1]; canvas[...,2] = bg_rgb[2]
    return canvas

def _index_to_rowcol(idx: int, rows: int, cols: int, mode: str) -> Tuple[int,int]:
    if mode == "row_major":
        return idx // cols, idx % cols
    if mode == "column_major":
        return idx % rows, idx // rows
    if mode == "snake_row":
        r, c = idx // cols, idx % cols
        return (r, cols-1-c) if (r % 2) else (r, c)
    if mode == "snake_col":
        c, r = idx // rows, idx % rows
        return (rows-1-r, c) if (c % 2) else (r, c)
    # fallback
    return idx // cols, idx % cols

# ---- Blend helpers ----

def _alpha_over(dst: np.ndarray, src: np.ndarray) -> np.ndarray:
    # src over dst; handle RGB or RGBA
    if dst.shape[2] == 4:
        Cd = dst[...,:3].astype(np.float32); Ad = (dst[...,3:4].astype(np.float32))/255.0
    else:
        Cd = dst.astype(np.float32); Ad = np.ones(dst.shape[:2]+(1,), np.float32)

    if src.shape[2] == 4:
        Cs = src[...,:3].astype(np.float32); As = (src[...,3:4].astype(np.float32))/255.0
    else:
        Cs = src.astype(np.float32); As = np.ones(src.shape[:2]+(1,), np.float32)

    Co = Cs + Cd * (1.0 - As)
    Ao = As + Ad * (1.0 - As)

    out_rgb = np.clip(Co, 0, 255)
    if dst.shape[2] == 4:
        out_a = np.clip(Ao*255.0, 0, 255)
        out = np.concatenate([out_rgb, out_a], axis=2).astype(np.uint8)
    else:
        out = out_rgb.astype(np.uint8)
    return out

def _apply_op(dst: np.ndarray, src: np.ndarray, op: str) -> np.ndarray:
    # operates channel-wise (on all channels; alpha treated like color if present)
    if op == "add":
        return np.clip(dst.astype(np.int16) + src.astype(np.int16), 0, 255).astype(np.uint8)
    if op == "multiply":
        return ((dst.astype(np.float32) * src.astype(np.float32)) / 255.0).astype(np.uint8)
    if op == "screen":
        return (255 - ((255 - dst.astype(np.int16)) * (255 - src.astype(np.int16)) // 255)).astype(np.uint8)
    if op == "lighten":
        return np.maximum(dst, src)
    if op == "darken":
        return np.minimum(dst, src)
    if op == "max":
        return np.maximum(dst, src)
    if op == "min":
        return np.minimum(dst, src)
    if op == "average":
        return ((dst.astype(np.uint16) + src.astype(np.uint16)) // 2).astype(np.uint8)
    # default 'last'
    return src

def _feather_mask(h: int, w: int, fx: int, fy: int, mode: str = "linear") -> np.ndarray:
    """Return 2D weight mask (h,w,1) in [0,1] that ramps on the 4 edges with radii fx,fy."""
    wx = np.ones((w,), np.float32)
    wy = np.ones((h,), np.float32)
    if fx > 0:
        ramp = np.linspace(0.0, 1.0, fx, dtype=np.float32)
        if mode == "cosine":
            ramp = (1 - np.cos(np.linspace(0, np.pi, fx, dtype=np.float32))) * 0.5
        wx[:fx] = ramp
        wx[-fx:] = ramp[::-1]
    if fy > 0:
        ramp = np.linspace(0.0, 1.0, fy, dtype=np.float32)
        if mode == "cosine":
            ramp = (1 - np.cos(np.linspace(0, np.pi, fy, dtype=np.float32))) * 0.5
        wy[:fy] = ramp
        wy[-fy:] = ramp[::-1]
    mask = wy[:,None] * wx[None,:]
    return mask[...,None]  # (h,w,1)

def _blend_place(dst: np.ndarray, src: np.ndarray, y: int, x: int, *,
                 mode: str = "last", weighted_w: float = 0.5,
                 feather_px: int = 0, feather_kind: str = "linear"):
    Hs, Ws = src.shape[0], src.shape[1]
    patch = dst[y:y+Hs, x:x+Ws, :]

    if mode == "alpha_over":
        patch[:] = _alpha_over(patch, src)
        return

    if mode in ("feather_linear","feather_cosine"):
        fk = "cosine" if mode.endswith("cosine") else "linear"
        fx = fy = max(0, int(feather_px))
        mask = _feather_mask(Hs, Ws, fx, fy, fk).astype(np.float32)
        src_f = src.astype(np.float32)
        dst_f = patch.astype(np.float32)
        out = dst_f * (1.0 - mask) + src_f * mask
        patch[:] = np.clip(out, 0, 255).astype(np.uint8)
        return

    if mode == "weighted":
        w = float(np.clip(weighted_w, 0.0, 1.0))
        src_f = src.astype(np.float32)
        dst_f = patch.astype(np.float32)
        out = dst_f * (1.0 - w) + src_f * w
        patch[:] = np.clip(out, 0, 255).astype(np.uint8)
        return

    # compositing ops
    patch[:] = _apply_op(patch, src, op=mode)

# ==== Node 1: Tile & Export ====

class MosaicTileExport:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "rows": ("INT", {"default": 2, "min": 1, "max": 512}),
                "cols": ("INT", {"default": 2, "min": 1, "max": 512}),
            },
            "optional": {
                "fit_mode": (["crop", "pad"], {"default": "crop"}),
                "filetype": (["png", "jpg"], {"default": "png"}),
                "quality": ("INT", {"default": 95, "min": 1, "max": 100}),
                "basename": ("STRING", {"default": "tiles"}),
                "subfolder": ("STRING", {"default": ""}),
            },
        }

    RETURN_TYPES = ("IMAGE", "STRING",)
    RETURN_NAMES = ("tiles_batch", "output_dir",)
    FUNCTION = "tile_and_export"
    CATEGORY = "DAO_master/Images/Mosaic"

    def _compute_tile_sizes(self, H, W, rows, cols, fit_mode):
        if fit_mode == "crop":
            th, tw = H // rows, W // cols
            if th < 1 or tw < 1:
                raise ValueError("Avec 'crop', rows/cols trop grands.")
            return th, tw, th*rows, tw*cols
        th, tw = math.ceil(H/rows), math.ceil(W/cols)
        return th, tw, th*rows, tw*cols

    def _pad_canvas(self, arr, used_H, used_W, mode):
        if mode == "RGBA":
            canvas = np.zeros((used_H, used_W, 4), dtype=np.uint8)
        else:
            canvas = np.zeros((used_H, used_W, 3), dtype=np.uint8)
        H, W = arr.shape[0], arr.shape[1]
        canvas[:H,:W,:arr.shape[2]] = arr
        return canvas

    def _slice_grid(self, base, rows, cols, th, tw):
        tiles = []
        for r in range(rows):
            for c in range(cols):
                y0, x0 = r*th, c*tw
                tiles.append(base[y0:y0+th, x0:x0+tw, :])
        return tiles

    def tile_and_export(self, image, rows, cols, fit_mode="crop",
                        filetype="png", quality=95, basename="tiles", subfolder=""):
        if torch is None:
            raise RuntimeError("PyTorch requis par ComfyUI n'est pas disponible.")
        np_img = _tensor_to_numpy_single(image)
        np_img, mode = _ensure_mode(np_img)
        H, W, _ = np_img.shape
        th, tw, used_H, used_W = self._compute_tile_sizes(H, W, rows, cols, fit_mode)
        base = np_img[:used_H,:used_W,:] if fit_mode=="crop" else self._pad_canvas(np_img, used_H, used_W, mode)
        tiles = self._slice_grid(base, rows, cols, th, tw)

        root_out = os.path.join("output","tiles"); ts = time.strftime("%Y%m%d-%H%M%S")
        safe_sub = subfolder.strip().replace("\\","/")
        out_dir = os.path.join(root_out, safe_sub, f"{basename}_{rows}x{cols}_{ts}") if safe_sub \
                  else os.path.join(root_out, f"{basename}_{rows}x{cols}_{ts}")
        os.makedirs(out_dir, exist_ok=True)

        saved = []
        for i,tile in enumerate(tiles):
            r, c = i//cols, i%cols
            pil = Image.fromarray(tile, mode=mode)
            fpath = os.path.join(out_dir, f"{basename}_r{r:02d}_c{c:02d}.{filetype}")
            _save_pil(pil, fpath, filetype=filetype, quality=quality)
            saved.append(fpath)

        batch = np.stack(tiles, axis=0)
        return (_numpy_to_tensor(batch), out_dir + "\n" + "\n".join(saved))

# ==== Node 2: Assemble (Batch) ====

class MosaicTileAssemble:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "tiles": ("IMAGE",),
                "rows": ("INT", {"default": 2, "min": 1, "max": 512}),
                "cols": ("INT", {"default": 2, "min": 1, "max": 512}),
            },
            "optional": {
                "order_mode": (["row_major","column_major","snake_row","snake_col"], {"default":"row_major"}),
                "offset_x": ("INT", {"default": 0, "min": -10000, "max": 10000}),
                "offset_y": ("INT", {"default": 0, "min": -10000, "max": 10000}),
                "gutter": ("INT", {"default": 0, "min": -4096, "max": 4096}),
                "overlap_x": ("INT", {"default": 0, "min": 0, "max": 4096}),
                "overlap_y": ("INT", {"default": 0, "min": 0, "max": 4096}),
                "overlap_blend": ([
                    "last","average","alpha_over","add","multiply","screen","lighten","darken","max","min",
                    "weighted","feather_linear","feather_cosine"
                ], {"default": "last"}),
                "blend_weight": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0}),
                "feather_px": ("INT", {"default": 0, "min": 0, "max": 2048}),

                "export": ("BOOLEAN", {"default": False}),
                "filetype": (["png","jpg"], {"default":"png"}),
                "quality": ("INT", {"default":95, "min":1, "max":100}),
                "basename": ("STRING", {"default":"mosaic"}),
                "subfolder": ("STRING", {"default":""}),
                "bg_color": ("STRING", {"default":"#000000"}),
                "bg_alpha": ("INT", {"default":0, "min":0, "max":255}),
            },
        }

    RETURN_TYPES = ("IMAGE","STRING",)
    RETURN_NAMES = ("image","save_path",)
    FUNCTION = "assemble"
    CATEGORY = "DAO_master/Images/Mosaic"

    def assemble(self, tiles, rows, cols, order_mode="row_major",
                 offset_x=0, offset_y=0, gutter=0, overlap_x=0, overlap_y=0,
                 overlap_blend="last", blend_weight=0.5, feather_px=0,
                 export=False, filetype="png", quality=95, basename="mosaic", subfolder="",
                 bg_color="#000000", bg_alpha=0):
        if torch is None:
            raise RuntimeError("PyTorch requis par ComfyUI n'est pas disponible.")

        arr = _tensor_batch_to_numpy(tiles)  # (N,H,W,C)
        N, Ht, Wt, C = arr.shape
        expected = rows*cols
        if N != expected:
            raise ValueError(f"Batch={N} mais rows*cols={expected}")
        if C not in (3,4):
            arr = arr[...,:3]; C = 3
        rgba = (C==4)

        bg_rgb = _parse_hex_color(bg_color)
        stride_x = max(1, Wt + gutter - overlap_x)
        stride_y = max(1, Ht + gutter - overlap_y)
        canvas_H = offset_y + rows*Ht + max(0, rows-1)*(gutter - overlap_y)
        canvas_W = offset_x + cols*Wt + max(0, cols-1)*(gutter - overlap_x)
        canvas_H = max(canvas_H, Ht + offset_y); canvas_W = max(canvas_W, Wt + offset_x)
        canvas = _make_canvas(canvas_W, canvas_H, rgba=rgba, bg_rgb=bg_rgb, bg_alpha=bg_alpha)

        for i in range(N):
            r, c = _index_to_rowcol(i, rows, cols, order_mode)
            y = offset_y + r*stride_y; x = offset_x + c*stride_x
            tile = arr[i]
            if tile.shape[2] != C:
                if C==3 and tile.shape[2]==4: tile = tile[...,:3]
                if C==4 and tile.shape[2]==3:
                    a = 255*np.ones((Ht,Wt,1), np.uint8); tile = np.concatenate([tile,a], axis=2)
            # crop si placement partiellement en dehors
            y0, x0 = max(0,y), max(0,x); dy, dx = y0-y, x0-x
            y1, x1 = min(canvas.shape[0], y+Ht), min(canvas.shape[1], x+Wt)
            if y1<=y0 or x1<=x0: continue
            src = tile[dy:dy+(y1-y0), dx:dx+(x1-x0), :]
            _blend_place(canvas[y0:y1, x0:x1, :], src, 0, 0,
                         mode=overlap_blend, weighted_w=blend_weight, feather_px=feather_px)

        pil = Image.fromarray(canvas, mode=("RGBA" if rgba else "RGB"))
        save_path = ""
        if export:
            root_out = os.path.join("output","tiles"); ts = time.strftime("%Y%m%d-%H%M%S")
            folder = os.path.join(root_out, subfolder) if subfolder.strip() else root_out
            os.makedirs(folder, exist_ok=True)
            fname = f"{basename}_{rows}x{cols}_{canvas.shape[1]}x{canvas.shape[0]}_{ts}.{filetype}"
            save_path = os.path.join(folder, fname)
            _save_pil(pil, save_path, filetype=filetype, quality=quality)

        return (_numpy_to_tensor(np.array(pil)), save_path or "")

# ==== Node 3: Assemble (Folder) avec regex_filename_order ====

class MosaicAssembleFromFolder:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "folder": ("STRING", {"default":"output/tiles"}),
                "glob_pattern": ("STRING", {"default":"*.png"}),
                "rows": ("INT", {"default":2, "min":1, "max":1024}),
                "cols": ("INT", {"default":2, "min":1, "max":1024}),
            },
            "optional": {
                "sort_mode": (["name_asc","name_desc","mtime_asc","mtime_desc"], {"default":"name_asc"}),

                "order_mode": ([
                    "row_major","column_major","snake_row","snake_col","regex_filename_order"
                ], {"default":"row_major"}),

                # regex settings (used only when order_mode == 'regex_filename_order')
                "regex_row": ("STRING", {"default": r"r(\d+)", "multiline": False}),
                "regex_col": ("STRING", {"default": r"c(\d+)", "multiline": False}),
                "base_index": ("INT", {"default": 0, "min": 0, "max": 10}),
                "fallback_order": (["row_major","column_major","snake_row","snake_col"], {"default":"row_major"}),

                "offset_x": ("INT", {"default": 0, "min": -10000, "max": 10000}),
                "offset_y": ("INT", {"default": 0, "min": -10000, "max": 10000}),
                "gutter": ("INT", {"default": 0, "min": -4096, "max": 4096}),
                "overlap_x": ("INT", {"default": 0, "min": 0, "max": 4096}),
                "overlap_y": ("INT", {"default": 0, "min": 0, "max": 4096}),
                "overlap_blend": ([
                    "last","average","alpha_over","add","multiply","screen","lighten","darken","max","min",
                    "weighted","feather_linear","feather_cosine"
                ], {"default": "last"}),
                "blend_weight": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0}),
                "feather_px": ("INT", {"default": 0, "min": 0, "max": 2048}),

                "enforce_tile_size": ("BOOLEAN", {"default": True}),
                "target_w": ("INT", {"default": 0, "min": 0, "max": 8192}),
                "target_h": ("INT", {"default": 0, "min": 0, "max": 8192}),

                "export": ("BOOLEAN", {"default": True}),
                "filetype": (["png","jpg"], {"default":"png"}),
                "quality": ("INT", {"default":95, "min":1, "max":100}),
                "basename": ("STRING", {"default":"mosaic_from_folder"}),
                "subfolder": ("STRING", {"default":""}),
                "bg_color": ("STRING", {"default":"#000000"}),
                "bg_alpha": ("INT", {"default":0, "min":0, "max":255}),
            },
        }

    RETURN_TYPES = ("IMAGE","STRING",)
    RETURN_NAMES = ("image","save_path",)
    FUNCTION = "assemble_from_folder"
    CATEGORY = "DAO_master/Images/Mosaic"

    def _collect_files(self, folder: str, pattern: str, sort_mode: str) -> List[str]:
        folder = folder.strip().strip('"'); search = os.path.join(folder, pattern.strip())
        files = glob.glob(search)
        if not files: return []
        if sort_mode == "name_asc":
            files.sort(key=lambda p: os.path.basename(p).lower())
        elif sort_mode == "name_desc":
            files.sort(key=lambda p: os.path.basename(p).lower(), reverse=True)
        elif sort_mode == "mtime_asc":
            files.sort(key=lambda p: os.path.getmtime(p))
        elif sort_mode == "mtime_desc":
            files.sort(key=lambda p: os.path.getmtime(p), reverse=True)
        return files

    def _regex_map(self, files: List[str], rows: int, cols: int, regex_row: str, regex_col: str, base_index: int) -> Dict[Tuple[int,int], str]:
        rx_r = re.compile(regex_row); rx_c = re.compile(regex_col)
        placed: Dict[Tuple[int,int], str] = {}
        for p in files:
            name = os.path.basename(p)
            mr = rx_r.search(name); mc = rx_c.search(name)
            if not mr or not mc: continue
            try:
                r = int(mr.group(1)) - base_index
                c = int(mc.group(1)) - base_index
            except Exception:
                continue
            if 0 <= r < rows and 0 <= c < cols and (r,c) not in placed:
                placed[(r,c)] = p
        return placed

    def assemble_from_folder(self, folder, glob_pattern, rows, cols,
                             sort_mode="name_asc",
                             order_mode="row_major",
                             regex_row=r"r(\d+)", regex_col=r"c(\d+)", base_index=0, fallback_order="row_major",
                             offset_x=0, offset_y=0, gutter=0, overlap_x=0, overlap_y=0,
                             overlap_blend="last", blend_weight=0.5, feather_px=0,
                             enforce_tile_size=True, target_w=0, target_h=0,
                             export=True, filetype="png", quality=95, basename="mosaic_from_folder", subfolder="",
                             bg_color="#000000", bg_alpha=0):
        if torch is None:
            raise RuntimeError("PyTorch requis par ComfyUI n'est pas disponible.")

        files = self._collect_files(folder, glob_pattern, sort_mode)
        expected = rows*cols
        if len(files) < expected:
            raise ValueError(f"Pas assez d'images ({len(files)}) pour {rows}x{cols} ({expected}).")

        # Détermine l'ordre/mapping
        use_regex = (order_mode == "regex_filename_order")
        mapping: Dict[Tuple[int,int], str] = {}
        if use_regex:
            mapping = self._regex_map(files, rows, cols, regex_row, regex_col, base_index)
            # Compléter les cases manquantes avec l'ordre fallback
            remaining = [f for f in files if f not in mapping.values()]
            idx_rem = 0
            for i in range(expected):
                r, c = _index_to_rowcol(i, rows, cols, fallback_order)
                if (r,c) not in mapping and idx_rem < len(remaining):
                    mapping[(r,c)] = remaining[idx_rem]; idx_rem += 1
        else:
            # ordre standard à partir de files[:expected]
            mapping = {}
            for i in range(expected):
                r, c = _index_to_rowcol(i, rows, cols, order_mode)
                mapping[(r,c)] = files[i]

        # Charge les images selon mapping (row-major de placement)
        imgs = []
        for r in range(rows):
            for c in range(cols):
                p = mapping[(r,c)]
                im = Image.open(p)
                if im.mode not in ("RGB","RGBA"):
                    im = im.convert("RGBA" if im.mode=="LA" else "RGB")
                imgs.append(im)

        # Normalisation taille
        if target_w <= 0 or target_h <= 0:
            target_w = imgs[0].width if target_w <= 0 else target_w
            target_h = imgs[0].height if target_h <= 0 else target_h
        norm = []
        for im in imgs:
            if enforce_tile_size and (im.width != target_w or im.height != target_h):
                im = im.resize((target_w, target_h), Image.Resampling.LANCZOS)
            norm.append(im)

        C = 4 if any(im.mode=="RGBA" for im in norm) else 3
        rgba = (C==4)
        bg_rgb = _parse_hex_color(bg_color)
        Ht, Wt = target_h, target_w
        stride_x = max(1, Wt + gutter - overlap_x)
        stride_y = max(1, Ht + gutter - overlap_y)
        canvas_H = offset_y + rows*Ht + max(0, rows-1)*(gutter - overlap_y)
        canvas_W = offset_x + cols*Wt + max(0, cols-1)*(gutter - overlap_x)
        canvas_H = max(canvas_H, Ht + offset_y); canvas_W = max(canvas_W, Wt + offset_x)
        canvas = _make_canvas(canvas_W, canvas_H, rgba=rgba, bg_rgb=bg_rgb, bg_alpha=bg_alpha)

        # Placement
        for i, im in enumerate(norm):
            r, c = i // cols, i % cols  # on place selon row-major des images listées
            y = offset_y + r*stride_y; x = offset_x + c*stride_x
            src = np.array(im.convert("RGBA" if rgba else "RGB"), dtype=np.uint8)

            # crop si hors-champ via offset
            y0, x0 = max(0,y), max(0,x); dy, dx = y0-y, x0-x
            y1, x1 = min(canvas.shape[0], y+Ht), min(canvas.shape[1], x+Wt)
            if y1<=y0 or x1<=x0: continue
            src = src[dy:dy+(y1-y0), dx:dx+(x1-x0), :]
            _blend_place(canvas[y0:y1, x0:x1, :], src, 0, 0,
                         mode=overlap_blend, weighted_w=blend_weight, feather_px=feather_px)

        pil = Image.fromarray(canvas, mode=("RGBA" if rgba else "RGB"))
        save_path = ""
        if export:
            root_out = os.path.join("output","tiles"); ts = time.strftime("%Y%m%d-%H%M%S")
            folder_out = os.path.join(root_out, subfolder) if subfolder.strip() else root_out
            os.makedirs(folder_out, exist_ok=True)
            fname = f"{basename}_{rows}x{cols}_{canvas.shape[1]}x{canvas.shape[0]}_{ts}.{filetype}"
            save_path = os.path.join(folder_out, fname)
            _save_pil(pil, save_path, filetype=filetype, quality=quality)

        return (_numpy_to_tensor(np.array(pil)), save_path or "")
