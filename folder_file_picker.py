# -*- coding: utf-8 -*-
# DAO_master — Folder File Picker (seed + regex + UI route)
#
# Node "Folder File Picker"
# - Parcourt un répertoire (option récursive)
# - Filtre par extensions ET/OU par RegEx sur le nom
# - Trie par nom / date / taille
# - Sélection par combo (index), OU via un "seed" optionnel :
#     seed_mode = manual | fixed | increment | decrement | randomize
# - Sorties : file_path, filename, dir_used, files_json
#
# Route aiohttp "/dao_master/list_dir" pour la combo côté web
#
import os, json, re, random
from dataclasses import dataclass
from typing import List

# ---- ComfyUI server (aiohttp) ----
HAVE_SERVER = False
try:
    from aiohttp import web
    from server import PromptServer
    HAVE_SERVER = True
except Exception:
    HAVE_SERVER = False


@dataclass
class FInfo:
    name: str
    path: str
    size: int
    mtime: float


def _norm_exts(exts: str) -> List[str]:
    """'.svg,.png;jpg' -> ['.svg','.png','.jpg'] (ordre conservé, uniques)."""
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
    return list(dict.fromkeys(out))


def _list_files(directory: str, extensions: List[str], recursive: bool) -> List[FInfo]:
    """Liste les fichiers (filtre extensions si fourni)."""
    directory = os.path.expanduser(str(directory)).strip('"').strip()
    if not os.path.isdir(directory):
        return []

    results: List[FInfo] = []
    if recursive:
        for root, _, files in os.walk(directory):
            for fn in files:
                if fn.startswith("."):
                    continue
                full = os.path.join(root, fn)
                if extensions and (os.path.splitext(fn)[1].lower() not in extensions):
                    continue
                try:
                    st = os.stat(full)
                    results.append(FInfo(fn, os.path.abspath(full), st.st_size, st.st_mtime))
                except Exception:
                    continue
    else:
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
                    results.append(FInfo(fn, os.path.abspath(full), st.st_size, st.st_mtime))
                except Exception:
                    continue
        except Exception:
            return []
    return results


def _apply_regex(files: List[FInfo], pattern: str, mode: str, ignore_case: bool) -> List[FInfo]:
    """Filtre RegEx sur le nom (mode 'include' ou 'exclude')."""
    pat = (pattern or "").strip()
    if not pat:
        return files
    flags = re.IGNORECASE if ignore_case else 0
    try:
        rx = re.compile(pat, flags)
    except Exception:
        # regex invalide → on n’applique rien
        return files

    if mode == "exclude":
        return [f for f in files if not rx.search(f.name)]
    # include (par défaut)
    return [f for f in files if rx.search(f.name)]


def _sort_files(files: List[FInfo], sort_by: str, descending: bool) -> List[FInfo]:
    key = (lambda f: f.name.lower())
    if sort_by == "mtime":
        key = (lambda f: f.mtime)
    elif sort_by == "size":
        key = (lambda f: f.size)
    return sorted(files, key=key, reverse=bool(descending))


# ----------------------- Route aiohttp (UI) -----------------------
if HAVE_SERVER:
    @PromptServer.instance.routes.get("/dao_master/list_dir")
    async def list_dir(request: web.Request):
        """
        GET /api/dao_master/list_dir?dir=...&exts=.svg,.png&recursive=false
            &sort_by=name&descending=false
            &regex=...&regex_mode=include|exclude&regex_ic=true|false
        """
        q = request.rel_url.query

        directory  = q.get("dir", "")
        exts_q     = q.get("exts", "")
        recursive  = q.get("recursive", "false").lower() in ("1", "true", "yes", "on")
        sort_by    = q.get("sort_by", "name")
        descending = q.get("descending", "false").lower() in ("1", "true", "yes", "on")

        regex      = q.get("regex", "")
        regex_mode = q.get("regex_mode", "include")
        regex_ic   = q.get("regex_ic", "true").lower() in ("1", "true", "yes", "on")

        extensions = _norm_exts(exts_q)

        files = _list_files(directory, extensions, recursive)
        files = _apply_regex(files, regex, regex_mode, regex_ic)
        files = _sort_files(files, sort_by, descending)

        payload = {
            "dir": os.path.abspath(os.path.expanduser(directory)) if directory else "",
            "count": len(files),
            "files": [
                {"name": f.name, "path": f.path, "size": f.size, "mtime": f.mtime}
                for f in files
            ],
        }
        return web.json_response(payload)


# ------------------------------ Node ------------------------------
class FolderFilePicker:
    # compteur global pour seed_mode increment/decrement
    _GLOBAL_COUNTER = 0

    @classmethod
    def _bump_counter(cls) -> int:
        cls._GLOBAL_COUNTER += 1
        return cls._GLOBAL_COUNTER

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "directory": ("STRING", {"default": "input", "multiline": False}),
            "extensions": ("STRING", {"default": ".svg,.png,.jpg,.jpeg,.dxf"}),

            "name_regex": ("STRING", {"default": ""}),
            "regex_mode": (["include", "exclude"], {"default": "include"}),
            "regex_ignore_case": ("BOOLEAN", {"default": True}),

            "recursive": ("BOOLEAN", {"default": False}),
            "sort_by": (["name", "mtime", "size"], {"default": "name"}),
            "descending": ("BOOLEAN", {"default": False}),

            # contrôlé par la combo côté JS (mais reste utilisable à la main)
            "index": ("INT", {"default": 0, "min": 0, "max": 999999}),

            # sélection pilotée par seed (optionnelle)
            "seed_mode": (["manual", "fixed", "increment", "decrement", "randomize"], {"default": "manual"}),
            "seed": ("INT", {"default": 0, "min": -1000000000, "max": 1000000000}),
        }}

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("file_path", "filename", "dir_used", "files_json")
    FUNCTION = "pick"
    CATEGORY = "DAO_master/IO"

    def pick(self, directory: str, extensions: str,
             name_regex: str, regex_mode: str, regex_ignore_case: bool,
             recursive: bool, sort_by: str, descending: bool,
             index: int, seed_mode: str, seed: int):

        exts = _norm_exts(extensions)
        files = _list_files(directory, exts, recursive)
        files = _apply_regex(files, name_regex, regex_mode, regex_ignore_case)
        files = _sort_files(files, sort_by, descending)

        dir_used = os.path.abspath(os.path.expanduser(str(directory))).strip('"')

        if not files:
            return ("", "", dir_used, json.dumps([], ensure_ascii=False))

        # --- choix de l'index ---
        N = len(files)
        idx = max(0, min(int(index), N - 1))

        if seed_mode != "manual":
            if seed_mode == "fixed":
                idx = int(seed) % N
            elif seed_mode == "randomize":
                rng = random.Random(int(seed))
                idx = rng.randrange(N)
            elif seed_mode == "increment":
                idx = (int(seed) + self._bump_counter()) % N
            elif seed_mode == "decrement":
                idx = (int(seed) - self._bump_counter()) % N

        chosen = files[idx]
        as_json = json.dumps(
            [{"name": f.name, "path": f.path, "size": f.size, "mtime": f.mtime} for f in files],
            ensure_ascii=False
        )

        return (chosen.path, chosen.name, dir_used, as_json)


NODE_CLASS_MAPPINGS = {"Folder File Picker": FolderFilePicker}
NODE_DISPLAY_NAME_MAPPINGS = {"Folder File Picker": "Folder File Picker (dir → file_path)"}
