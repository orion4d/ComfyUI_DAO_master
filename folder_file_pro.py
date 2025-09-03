# -*- coding: utf-8 -*-
# DAO_master - Folder File Pro (v4.1)

import os
import io
import re
import sys
import json
import random
import subprocess
import datetime
from dataclasses import dataclass
from typing import List, Dict, Any

# --------------------------------------------------------------------------------------
# Optional modules
HAVE_SERVER = False
try:
    from aiohttp import web  # type: ignore
    from server import PromptServer  # type: ignore
    HAVE_SERVER = True
except Exception:
    HAVE_SERVER = False

HAVE_PIL = False
try:
    from PIL import Image  # type: ignore
    HAVE_PIL = True
except Exception:
    HAVE_PIL = False

HAVE_CV2 = False
try:
    import cv2  # type: ignore
    HAVE_CV2 = True
except Exception:
    HAVE_CV2 = False

# --------------------------------------------------------------------------------------
SUPPORTED_IMAGE_EXT = [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".svg"]
SUPPORTED_VIDEO_EXT = [".mp4", ".webm", ".mov", ".mkv", ".avi"]
SUPPORTED_AUDIO_EXT = [".mp3", ".wav", ".ogg", ".flac"]

def classify_type(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".svg":
        return "svg"
    if ext in SUPPORTED_IMAGE_EXT:
        return "image"
    if ext in SUPPORTED_VIDEO_EXT:
        return "video"
    if ext in SUPPORTED_AUDIO_EXT:
        return "audio"
    return "other"

NODE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(NODE_DIR, "folder_file_pro.config.json")

def _load_cfg() -> Dict[str, Any]:
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def _save_cfg(data: Dict[str, Any]) -> None:
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

@dataclass
class FInfo:
    name: str
    path: str
    size: int
    mtime: float

# --------------------------------------------------------------------------------------
# Helpers

def _norm_exts(exts: str) -> List[str]:
    if not exts:
        return []
    raw = exts.replace(";", ",").split(",")
    out: List[str] = []
    for r in raw:
        r = r.strip().lower()
        if not r:
            continue
        if not r.startswith("."):
            r = "." + r
        out.append(r)
    seen = set()
    dedup: List[str] = []
    for e in out:
        if e not in seen:
            seen.add(e)
            dedup.append(e)
    return dedup

def _list_files_current_dir(directory: str, extensions: List[str]) -> List[FInfo]:
    directory = os.path.expanduser(str(directory)).strip().strip('"')
    if not os.path.isdir(directory):
        return []
    results: List[FInfo] = []
    try:
        for fn in os.listdir(directory):
            full = os.path.join(directory, fn)
            if not os.path.isfile(full):
                continue
            if fn.startswith("."):
                continue
            if extensions and (os.path.splitext(fn)[1].lower() not in extensions):
                continue
            try:
                st = os.stat(full)
                results.append(FInfo(fn, os.path.abspath(full), int(st.st_size), float(st.st_mtime)))
            except Exception:
                continue
    except Exception:
        return []
    return results

def _apply_regex(files: List[FInfo], pattern: str, mode: str, ignore_case: bool) -> List[FInfo]:
    pat = (pattern or "").strip()
    if not pat:
        return files
    flags = re.IGNORECASE if ignore_case else 0
    try:
        rx = re.compile(pat, flags)
    except re.error:
        return files
    include = (mode or "include").lower() != "exclude"
    if include:
        return [f for f in files if rx.search(f.name)]
    return [f for f in files if not rx.search(f.name)]

def _sort_files(files: List[FInfo], sort_by: str, descending: bool) -> List[FInfo]:
    sb = (sort_by or "name").lower()
    def k_name(f: FInfo):
        return (f.name.lower(), f.path)
    def k_mtime(f: FInfo):
        return (f.mtime, f.name.lower(), f.path)
    def k_size(f: FInfo):
        return (f.size, f.name.lower(), f.path)
    key = k_name if sb == "name" else (k_mtime if sb == "mtime" else k_size)
    return sorted(files, key=key, reverse=bool(descending))

def _iso(ts: float) -> str:
    try:
        return datetime.datetime.fromtimestamp(ts).isoformat(timespec="seconds")
    except Exception:
        return ""

def _get_file_info(path: str) -> Dict[str, Any]:
    info: Dict[str, Any] = {"name": os.path.basename(path), "path": os.path.abspath(path)}
    try:
        st = os.stat(path)
        info["size_bytes"] = int(st.st_size)
        info["created"] = st.st_ctime
        info["modified"] = st.st_mtime
        info["created_iso"] = _iso(st.st_ctime)
        info["modified_iso"] = _iso(st.st_mtime)
    except Exception:
        info["size_bytes"] = -1
        info["created"] = None
        info["modified"] = None
        info["created_iso"] = ""
        info["modified_iso"] = ""
    info["type"] = classify_type(path)
    info["width"] = None
    info["height"] = None
    if info["type"] == "image" and path.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp")) and HAVE_PIL:
        try:
            im = Image.open(path)
            info["width"], info["height"] = im.size
        except Exception:
            pass
    elif info["type"] == "video" and HAVE_CV2:
        try:
            cap = cv2.VideoCapture(path)
            w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            cap.release()
            if w and h:
                info["width"] = int(w)
                info["height"] = int(h)
        except Exception:
            pass
    return info

def _open_in_explorer(target: str) -> None:
    if os.name == "nt":
        if os.path.isfile(target):
            try:
                subprocess.Popen(["explorer", "/select,", target], close_fds=True)
                return
            except Exception:
                pass
        os.startfile(target)  # type: ignore
    elif sys.platform == "darwin":
        subprocess.Popen(["open", target], close_fds=True)
    else:
        subprocess.Popen(["xdg-open", target], close_fds=True)

# --------------------------------------------------------------------------------------
# HTTP endpoints
if HAVE_SERVER:

    @PromptServer.instance.routes.get("/folder_file_pro/list")
    async def http_list(request: "web.Request"):
        q = request.rel_url.query
        directory  = q.get("directory", "")
        exts_q     = q.get("exts", "")
        sort_by    = q.get("sort_by", "name")
        descending = q.get("descending", "false").lower() in ("1", "true", "yes", "on")
        regex      = q.get("regex", "")
        regex_mode = q.get("regex_mode", "include")
        regex_ic   = q.get("regex_ic", "true").lower() in ("1", "true", "yes", "on")

        directory_abs = os.path.abspath(os.path.expanduser(directory)) if directory else ""
        if not os.path.isdir(directory_abs):
            return web.json_response({"error": "Directory not found.", "current_directory": directory_abs}, status=404)

        cfg = _load_cfg()
        cfg["last_path"] = directory_abs
        _save_cfg(cfg)

        # Dossiers
        dirs = []
        try:
            for name in os.listdir(directory_abs):
                p = os.path.join(directory_abs, name)
                if os.path.isdir(p):
                    dirs.append({"name": name, "path": p})
            dirs.sort(key=lambda d: (d["name"].lower(), d["path"]), reverse=descending)
        except Exception:
            dirs = []

        # Fichiers
        extensions = _norm_exts(exts_q)
        files = _list_files_current_dir(directory_abs, extensions)
        files = _apply_regex(files, regex, regex_mode, regex_ic)
        files = _sort_files(files, sort_by, descending)

        visible = []
        for f in files:
            ext = os.path.splitext(f.path)[1].lower()
            visible.append({"name": f.name, "path": f.path, "type": classify_type(f.path), "ext": ext})

        parent = os.path.dirname(directory_abs) if directory_abs else None
        if parent == directory_abs:
            parent = None

        return web.json_response({
            "current_directory": directory_abs,
            "parent_directory": parent,
            "dirs": dirs,
            "files": visible,
            "total_count": len(files),
        })

    @PromptServer.instance.routes.get("/folder_file_pro/resolve_index")
    async def http_resolve_index(request: "web.Request"):
        q = request.rel_url.query
        directory  = q.get("directory", "")
        exts_q     = q.get("exts", "")
        sort_by    = q.get("sort_by", "name")
        descending = q.get("descending", "false").lower() in ("1", "true", "yes", "on")
        regex      = q.get("regex", "")
        regex_mode = q.get("regex_mode", "include")
        regex_ic   = q.get("regex_ic", "true").lower() in ("1", "true", "yes", "on")
        target     = q.get("path", "")

        extensions = _norm_exts(exts_q)
        files = _list_files_current_dir(directory, extensions)
        files = _apply_regex(files, regex, regex_mode, regex_ic)
        files = _sort_files(files, sort_by, descending)

        idx = -1
        tgt = os.path.abspath(target)
        for i, f in enumerate(files):
            if os.path.abspath(f.path) == tgt:
                idx = i
                break
        return web.json_response({"index": idx, "count": len(files)})

    @PromptServer.instance.routes.get("/folder_file_pro/get_last_path")
    async def http_get_last_path(request: "web.Request"):
        return web.json_response({"last_path": _load_cfg().get("last_path", "")})

    @PromptServer.instance.routes.get("/folder_file_pro/thumbnail")
    async def http_thumbnail(request: "web.Request"):
        if not HAVE_PIL:
            return web.Response(status=501, text="Pillow not installed.")
        filepath = request.query.get("filepath", "")
        if not filepath or ".." in filepath:
            return web.Response(status=400)
        if not os.path.exists(filepath):
            return web.Response(status=404)
        try:
            img = Image.open(filepath)
            # alpha -> PNG, sinon JPEG
            has_alpha = (img.mode == "RGBA") or (img.mode == "P" and "transparency" in img.info)
            img = img.convert("RGBA") if has_alpha else img.convert("RGB")
            img.thumbnail([320, 320], Image.LANCZOS)
            buf = io.BytesIO()
            if has_alpha:
                img.save(buf, format="PNG")
                ctype = "image/png"
            else:
                img.save(buf, format="JPEG", quality=90)
                ctype = "image/jpeg"
            buf.seek(0)
            return web.Response(body=buf.read(), content_type=ctype)
        except Exception:
            return web.Response(status=500)

    @PromptServer.instance.routes.get("/folder_file_pro/view")
    async def http_view(request: "web.Request"):
        filepath = request.query.get("filepath", "")
        if not filepath or ".." in filepath:
            return web.Response(status=400)
        if not os.path.exists(filepath):
            return web.Response(status=404)
        try:
            return web.FileResponse(filepath)
        except Exception:
            return web.Response(status=500)

    @PromptServer.instance.routes.post("/folder_file_pro/open_explorer")
    async def http_open_explorer(request: "web.Request"):
        try:
            data = await request.json()
        except Exception:
            data = {}
        target = str(data.get("path", "")).strip()
        if not target:
            return web.json_response({"ok": False, "error": "missing path"}, status=400)
        target = os.path.abspath(os.path.expanduser(target))
        if not os.path.exists(target):
            return web.json_response({"ok": False, "error": "not found"}, status=404)
        try:
            _open_in_explorer(target)
            return web.json_response({"ok": True})
        except Exception as e:
            return web.json_response({"ok": False, "error": str(e)}, status=500)

# --------------------------------------------------------------------------------------
# ComfyUI node

class FolderFilePro:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "directory": ("STRING", {"default": "input"}),
                "extensions": ("STRING", {"default": ""}),
                "name_regex": ("STRING", {"default": ""}),
                "regex_mode": (["include", "exclude"], {"default": "include"}),
                "regex_ignore_case": ("BOOLEAN", {"default": True}),
                "sort_by": (["name", "mtime", "size"], {"default": "name"}),
                "descending": ("BOOLEAN", {"default": False}),
                # Sélection
                "seed_mode": (["manual", "fixed", "increment", "decrement", "randomize"], {"default": "manual"}),
                "seed": ("INT", {"default": 0, "min": -2147483648, "max": 2147483647}),
                "index": ("INT", {"default": 0, "min": 0, "max": 1_000_000_000}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("file_path", "filename", "dir_used", "files_json", "file_info")
    FUNCTION = "pick"
    CATEGORY = "DAO_master"

    def pick(self, directory: str, extensions: str,
             name_regex: str, regex_mode: str, regex_ignore_case: bool,
             sort_by: str, descending: bool,
             seed_mode: str, seed: int, index: int):

        exts = _norm_exts(extensions)
        files = _list_files_current_dir(directory, exts)
        files = _apply_regex(files, name_regex, regex_mode, regex_ignore_case)
        files = _sort_files(files, sort_by, descending)

        dir_used = os.path.abspath(os.path.expanduser(str(directory))).strip('"')
        if not files:
            return ("", "", dir_used, json.dumps([], ensure_ascii=False), json.dumps({}, ensure_ascii=False))

        n = len(files)

        sm = (seed_mode or "manual").lower()
        if sm == "manual":
            sel = max(0, min(int(index), n - 1))
        elif sm == "randomize":
            sel = random.Random(int(seed) & 0xFFFFFFFF).randrange(n)
        elif sm == "decrement":
            sel = (int(seed) - 1) % n
        else:
            # fixed / increment → même base (Comfy ne fournit pas de hook post-run ici)
            sel = int(seed) % n

        chosen = files[sel]

        files_json = json.dumps(
            [{"name": f.name, "path": f.path, "size": f.size, "mtime": f.mtime} for f in files],
            ensure_ascii=False
        )
        info = _get_file_info(chosen.path)

        return (chosen.path, chosen.name, dir_used, files_json, json.dumps(info, ensure_ascii=False))

# --------------------------------------------------------------------------------------
NODE_CLASS_MAPPINGS = {"Folder File Pro": FolderFilePro}
NODE_DISPLAY_NAME_MAPPINGS = {"Folder File Pro": "Folder File Pro (dir -> file_path)"}
