"use strict";
// DAO_master — Folder File Pro UI (v4.0)
// - Folder icon from web/ico_dossier.png (non déformée)
// - Grid/List, scroll fiable, double-clic, type-to-select, Explorer

import { app } from "/scripts/app.js";
import { api } from "/scripts/api.js";

/* ---------- Lightbox (image/vidéo/audio) ---------- */
function ensureLightbox() {
  let el = document.getElementById("ffp-lightbox");
  if (el) return;
  el = document.createElement("div");
  el.id = "ffp-lightbox";
  el.style.cssText =
    "position:fixed;inset:0;background:rgba(0,0,0,.85);display:none;align-items:center;justify-content:center;z-index:10000;";
  el.innerHTML =
    '<button class="ffp-close" style="position:absolute;top:15px;right:20px;width:36px;height:36px;border:2px solid #fff;border-radius:50%;background:rgba(0,0,0,.5);color:#fff;font-size:22px;cursor:pointer">x</button>' +
    '<img style="max-width:95%;max-height:95%;display:none"/>' +
    '<video controls autoplay style="max-width:95%;max-height:95%;display:none"></video>' +
    '<audio controls autoplay style="width:80%;max-width:640px;display:none"></audio>';
  document.body.appendChild(el);
  const close = () => {
    const i = el.querySelector("img"),
      v = el.querySelector("video"),
      a = el.querySelector("audio");
    if (i) i.src = "";
    if (v) {
      v.pause();
      v.src = "";
    }
    if (a) {
      a.pause();
      a.src = "";
    }
    el.style.display = "none";
  };
  el.querySelector(".ffp-close").onclick = close;
  el.addEventListener("click", (e) => {
    if (e.target === el) close();
  });
}

/* ---------- Icône dossier PNG depuis /web ---------- */
const FFP_FOLDER_URL = new URL("./ico_dossier.png", import.meta.url).href;

/* ---------- Badge d'extension pour non-images ---------- */
function extBadge(ext) {
  if (!ext) ext = ".file";
  if (ext[0] !== ".") ext = "." + ext;
  return '<div class="ffp-ext">[File' + ext + "]</div>";
}

app.registerExtension({
  name: "DAO_master.FolderFilePro.UI.v4_0",
  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (!nodeData || nodeData.name !== "Folder File Pro") return;

    const onCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      if (onCreated) onCreated.apply(this, arguments);
      ensureLightbox();

      /* --------- Widgets Comfy --------- */
      const wDir = this.widgets.find((w) => w.name === "directory");
      const wExt = this.widgets.find((w) => w.name === "extensions");
      const wRe = this.widgets.find((w) => w.name === "name_regex");
      const wReM = this.widgets.find((w) => w.name === "regex_mode");
      const wReIC = this.widgets.find((w) => w.name === "regex_ignore_case");
      const wSort = this.widgets.find((w) => w.name === "sort_by");
      const wDesc = this.widgets.find((w) => w.name === "descending");
      const wIdx = this.widgets.find((w) => w.name === "index");
      if (wIdx) wIdx.hidden = true;

      /* --------- UI DOM --------- */
      const root = document.createElement("div");
      const css = `
<style>
  .ffp-root{height:100%;width:100%;box-sizing:border-box;display:flex;flex-direction:column;padding:6px 6px 8px 6px;font-family:Arial,Helvetica,sans-serif;color:#ddd}
  .ffp-row{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-bottom:6px}
  .ffp-input,.ffp-btn,.ffp-select{background:#333;color:#ccc;border:1px solid #555;border-radius:6px;padding:6px 8px;font-size:12px}
  .ffp-input{flex:1 1 auto;min-width:240px}

  /* conteneur résultats → occupe tout l'espace disponible; min-height:0 pour activer le scroll */
  .ffp-grid{flex:1 1 auto;min-height:0;overflow-y:auto;background:#222;border-radius:10px;padding:10px;
           display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:10px}
  .ffp-grid.ffp-list{display:block}

  .ffp-card{display:flex;flex-direction:column;background:#2a2a2a;border-radius:12px;border:2px solid transparent;user-select:none;outline:none}
  .ffp-card:hover{border-color:#666}
  .ffp-card.selected{border-color:#00ffc9}

  .ffp-media{display:flex;align-items:center;justify-content:center;height:150px;border-radius:10px 10px 0 0;background:#1b1b1b;overflow:hidden;color:#bbb;font-size:22px}
  .ffp-media img{max-width:100%;max-height:100%;object-fit:contain;image-rendering:auto}

  /* taille conforme Local_Image_Gallery (Grid ~72px haut) */
  .ffp-media .ffp-folder-img{max-height:72px;max-width:96px;width:auto;height:auto}

  .ffp-info{padding:8px 10px;font-size:12px;word-break:break-all;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}

  /* List mode */
  .ffp-grid.ffp-list .ffp-card{flex-direction:row;align-items:center;padding:6px 8px;margin-bottom:6px}
  .ffp-grid.ffp-list .ffp-media{width:52px;height:52px;border-radius:8px;margin-right:10px}
  .ffp-grid.ffp-list .ffp-media .ffp-folder-img{max-height:40px;max-width:56px}
  .ffp-grid.ffp-list .ffp-info{padding:0;-webkit-line-clamp:1}

  .ffp-ext{display:inline-block;font-size:12px;border:1px solid #777;border-radius:6px;padding:4px 6px;background:#1e1e1e;color:#ddd}
</style>`;
      root.innerHTML = `
        ${css}
        <div class="ffp-root">
          <div class="ffp-row">
            <button class="ffp-btn ffp-up">Up</button>
            <input class="ffp-input ffp-path" placeholder="Chemin complet..."/>
            <select class="ffp-select ffp-view"><option value="grid">Grid</option><option value="list">List</option></select>
            <button class="ffp-btn ffp-go">Refresh</button>
            <button class="ffp-btn ffp-explore">Explorer</button>
            <span class="ffp-count" style="margin-left:auto;font-size:12px;opacity:.8"></span>
          </div>
          <div class="ffp-grid" tabindex="0"><p style="padding:8px">Saisir un dossier puis Refresh.</p></div>
        </div>`;
      this.addDOMWidget("folder_file_pro", "div", root, {});
      this.size = [860, 660];

      /* --------- Refs DOM --------- */
      const grid = root.querySelector(".ffp-grid");
      const pathInput = root.querySelector(".ffp-path");
      const upBtn = root.querySelector(".ffp-up");
      const goBtn = root.querySelector(".ffp-go");
      const exploreBtn = root.querySelector(".ffp-explore");
      const viewSel = root.querySelector(".ffp-view");
      const countLbl = root.querySelector(".ffp-count");

      /* --------- État --------- */
      let parentDir = null;
      let isLoading = false;
      let selectedPath = null;
      let lastDir = "";
      let lastView = "grid";
      let forceResetScroll = false;

      let typeBuffer = "";
      let typeTimer = null;
      const TYPE_TIMEOUT = 800;

      /* --------- Helpers --------- */
      function cardsArray() {
        return Array.from(grid.querySelectorAll(".ffp-card"));
      }
      function getNameFromCard(card) {
        const info = card.querySelector(".ffp-info");
        return (info ? info.textContent : "").trim();
      }
      function selectCard(card, { scroll = true, updateIndex = true } = {}) {
        if (!card) return;
        cardsArray().forEach((c) => c.classList.remove("selected"));
        card.classList.add("selected");
        selectedPath = card.dataset.path || null;
        if (scroll) card.scrollIntoView({ block: "nearest" });
        if (updateIndex && card.dataset.type === "file")
          resolveAndSelect.call(this, selectedPath);
      }
      function selectByIndex(idx) {
        const list = cardsArray();
        if (!list.length) return;
        if (idx < 0) idx = 0;
        if (idx >= list.length) idx = list.length - 1;
        selectCard.call(this, list[idx]);
      }
      function currentIndex() {
        const list = cardsArray();
        const cur = grid.querySelector(".ffp-card.selected");
        return Math.max(0, list.indexOf(cur || list[0] || null));
      }

      function folderHTML(d) {
        return (
          '<div class="ffp-media"><img class="ffp-folder-img" loading="lazy" src="' +
          FFP_FOLDER_URL +
          '" alt="folder"/></div>' +
          '<div class="ffp-info" title="' +
          d.name +
          '">' +
          d.name +
          "</div>"
        );
      }
      function fileHTML(f) {
        if (f.type === "image") {
          const src =
            "/folder_file_pro/thumbnail?filepath=" +
            encodeURIComponent(f.path);
          return (
            '<div class="ffp-media"><img loading="lazy" src="' +
            src +
            '" /></div><div class="ffp-info" title="' +
            f.name +
            '">' +
            f.name +
            "</div>"
          );
        } else if (f.type === "svg") {
          const src =
            "/folder_file_pro/view?filepath=" +
            encodeURIComponent(f.path);
          return (
            '<div class="ffp-media"><img loading="lazy" src="' +
            src +
            '" /></div><div class="ffp-info" title="' +
            f.name +
            '">' +
            f.name +
            "</div>"
          );
        } else {
          return (
            '<div class="ffp-media">' +
            extBadge(f.ext || ".file") +
            '</div><div class="ffp-info" title="' +
            f.name +
            '">' +
            f.name +
            "</div>"
          );
        }
      }

      /* --------- Récupération liste --------- */
      async function fetchList() {
        if (isLoading) return;
        isLoading = true;

        const prevScroll = grid.scrollTop;
        const prevDir = lastDir;
        const prevView = lastView;

        grid.style.opacity = "0.6";
        grid.innerHTML = "";
        selectedPath = null;

        try {
          const params = new URLSearchParams({
            directory: String(wDir ? wDir.value : ""),
            exts: String(wExt ? wExt.value : ""),
            sort_by: String(wSort ? wSort.value : "name"),
            descending: String(!!(wDesc && wDesc.value)),
            regex: String(wRe ? wRe.value : ""),
            regex_mode: String(wReM ? wReM.value : "include"),
            regex_ic: String(!!(wReIC && wReIC.value)),
          }).toString();
          const res = await api.fetchApi("/folder_file_pro/list?" + params);
          if (!res.ok) throw new Error("HTTP " + res.status);
          const data = await res.json();

          const curDir = data.current_directory || "";
          const curView = viewSel.value;

          pathInput.value = curDir;
          parentDir = data.parent_directory || null;
          upBtn.disabled = !parentDir;
          countLbl.textContent = data.total_count
            ? String(data.total_count) + " fichier(s)"
            : "";

          grid.classList.toggle("ffp-list", curView === "list");

          (data.dirs || []).forEach((d) => {
            const card = document.createElement("div");
            card.className = "ffp-card";
            card.dataset.type = "dir";
            card.dataset.path = d.path;
            card.innerHTML = folderHTML(d);
            grid.appendChild(card);
          });
          (data.files || []).forEach((f) => {
            const card = document.createElement("div");
            card.className = "ffp-card";
            card.dataset.type = "file";
            card.dataset.path = f.path;
            card.innerHTML = fileHTML(f);
            grid.appendChild(card);
          });

          requestAnimationFrame(() => {
            const sameDir = curDir === prevDir;
            const sameView = curView === prevView;
            if (!sameDir || !sameView || forceResetScroll) grid.scrollTop = 0;
            else {
              const maxScroll = Math.max(
                0,
                grid.scrollHeight - grid.clientHeight
              );
              grid.scrollTop = Math.min(prevScroll, maxScroll);
            }
            lastDir = curDir;
            lastView = curView;
            forceResetScroll = false;
            grid.focus();
          });
        } catch (e) {
          grid.innerHTML =
            '<p style="color:#ff7777;padding:8px">' +
            (e.message || String(e)) +
            "</p>";
          lastDir = String(wDir ? wDir.value : "");
          lastView = viewSel.value;
          forceResetScroll = false;
        } finally {
          isLoading = false;
          grid.style.opacity = "1";
        }
      }

      /* --------- Résolution index pour sortie --------- */
      async function resolveAndSelect(targetPath) {
        if (!targetPath) return;
        try {
          const params = new URLSearchParams({
            directory: String(wDir ? wDir.value : ""),
            exts: String(wExt ? wExt.value : ""),
            sort_by: String(wSort ? wSort.value : "name"),
            descending: String(!!(wDesc && wDesc.value)),
            regex: String(wRe ? wRe.value : ""),
            regex_mode: String(wReM ? wReM.value : "include"),
            regex_ic: String(!!(wReIC && wReIC.value)),
            path: String(targetPath),
          }).toString();
          const res = await api.fetchApi(
            "/folder_file_pro/resolve_index?" + params
          );
          const data = await res.json();
          const idxW = this.widgets.find((w) => w.name === "index");
          if (idxW && data.index >= 0) {
            idxW.value = data.index;
            this.setDirtyCanvas(true, true);
          }
        } catch (e) {
          console.warn("[FolderFilePro] resolve_index error", e);
        }
      }

      /* --------- Interactions --------- */
      grid.addEventListener("click", (e) => {
        const card = e.target.closest(".ffp-card");
        if (!card) return;
        selectCard.call(this, card, { scroll: false });
        grid.focus();
      });

      grid.addEventListener("dblclick", (e) => {
        const card = e.target.closest(".ffp-card");
        if (!card) return;
        const p = card.dataset.path;
        if (card.dataset.type === "dir") {
          if (wDir) {
            wDir.value = p;
            forceResetScroll = true;
            fetchList();
          }
          return;
        }
        const isImg = /\.(png|jpg|jpeg|bmp|gif|webp|svg)$/i.test(p);
        const lb = document.getElementById("ffp-lightbox");
        const i = lb.querySelector("img"),
          v = lb.querySelector("video"),
          a = lb.querySelector("audio");
        i.style.display = v.style.display = a.style.display = "none";
        v.pause();
        a.pause();
        if (isImg) {
          i.src =
            "/folder_file_pro/view?filepath=" + encodeURIComponent(p);
          i.style.display = "block";
          lb.style.display = "flex";
        } else {
          window.open(
            "/folder_file_pro/view?filepath=" + encodeURIComponent(p),
            "_blank"
          );
        }
      });

      // tape-pour-sélectionner
      function handleType(char) {
        if (!char) return;
        typeBuffer += char.toLowerCase();
        if (typeTimer) clearTimeout(typeTimer);
        typeTimer = setTimeout(() => (typeBuffer = ""), TYPE_TIMEOUT);

        const list = cardsArray();
        if (!list.length) return;
        let start = currentIndex.call(this) + 1;
        const N = list.length;
        for (let k = 0; k < N; k++) {
          const idx = (start + k) % N;
          const nm = getNameFromCard(list[idx]).toLowerCase();
          if (nm.startsWith(typeBuffer)) {
            selectByIndex.call(this, idx);
            return;
          }
        }
      }
      grid.addEventListener("keydown", (e) => {
        const tag =
          (document.activeElement && document.activeElement.tagName) || "";
        if (tag === "INPUT" || tag === "SELECT" || tag === "TEXTAREA") return;
        if (e.key.length === 1 && !e.ctrlKey && !e.metaKey && !e.altKey) {
          handleType.call(this, e.key);
          e.preventDefault();
          return;
        }
        if (e.key === "Backspace") {
          typeBuffer = typeBuffer.slice(0, -1);
          e.preventDefault();
          return;
        }
        if (e.key === "Escape") {
          typeBuffer = "";
          return;
        }
      });

      // relier widgets aux refresh
      function rewire(w) {
        if (!w) return;
        const prev = w.callback;
        w.callback = function () {
          if (prev) prev.apply(w, arguments);
          fetchList();
        };
      }
      [wDir, wExt, wRe, wReM, wReIC, wSort, wDesc].forEach(rewire);

      // barre d’actions
      upBtn.onclick = () => {
        if (parentDir && wDir) {
          wDir.value = parentDir;
          forceResetScroll = true;
          fetchList();
        }
      };
      goBtn.onclick = () => {
        if (wDir) {
          wDir.value = pathInput.value;
          forceResetScroll = true;
          fetchList();
        }
      };
      viewSel.onchange = () => {
        forceResetScroll = true;
        fetchList();
      };
      exploreBtn.onclick = async () => {
        const toOpen =
          (selectedPath || (wDir ? wDir.value : "") || "").toString();
        if (!toOpen) return;
        try {
          await api.fetchApi("/folder_file_pro/open_explorer", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ path: toOpen }),
          });
        } catch (e) {
          console.warn("open_explorer failed", e);
        }
      };

      // init
      (async () => {
        try {
          const r = await api.fetchApi("/folder_file_pro/get_last_path");
          const d = await r.json();
          const last = d.last_path || (wDir ? wDir.value : "");
          if (last) {
            if (wDir) wDir.value = last;
            pathInput.value = last;
          }
          lastDir = last || "";
          lastView = viewSel.value;
        } catch (e) { /* ignore */ }
        forceResetScroll = true;
        fetchList();
      })();
    };
  },
});

console.log("[DAO_master] Folder File Pro UI v4.0 loaded");
