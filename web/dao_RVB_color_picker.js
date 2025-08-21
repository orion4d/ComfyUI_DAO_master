// ComfyUI_DAO_master / web / dao_RVB_color_picker.js
// Menus dynamiques (list_file + color) pour le node RVB

import { app } from "/scripts/app.js";

async function apiJSON(url) {
  try {
    const r = await fetch(url, { cache: "no-store" });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return await r.json();
  } catch (e) {
    console.error("[DAO][rvb-picker] fetch error:", e, url);
    return {};
  }
}

function replaceWithCombo(node, widgetName, initialValue, onChange) {
  const idx = node.widgets.findIndex((w) => w.name === widgetName);
  const oldW = idx >= 0 ? node.widgets[idx] : null;
  if (oldW && oldW.type === "combo") return oldW;

  const startVal = initialValue ?? (oldW ? oldW.value : "");
  if (oldW) node.widgets.splice(idx, 1);

  const newW = node.addWidget(
    "combo",
    widgetName,
    startVal,
    (v) => { newW.value = v; onChange?.(v); },
    { values: [] }
  );

  if (idx >= 0) {
    const last = node.widgets.length - 1;
    node.widgets.splice(idx, 0, newW);
    node.widgets.splice(last + 1, 1);
  }
  return newW;
}

app.registerExtension({
  name: "DAO.RVBColorPicker",
  async beforeRegisterNodeDef(nodeType, nodeData) {
    // On cible par nom et/ou catégorie
    const isTarget =
      (nodeData?.name && /RVB Color Picker/i.test(nodeData.name)) ||
      (nodeData?.category && /DAO_master\/Color/i.test(nodeData.category));
    if (!isTarget) return;

    const _onNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      _onNodeCreated?.apply(this, arguments);

      const wList  = replaceWithCombo(this, "list_file");
      const wColor = replaceWithCombo(this, "color");

      const refreshColors = async () => {
        const file = encodeURIComponent(wList.value || "");
        const data = await apiJSON(`/dao/rvb_picker/colors?file=${file}`);
        const vals = Array.isArray(data.colors) ? data.colors : [];
        wColor.options = wColor.options || {};
        wColor.options.values = vals;
        if (!vals.includes(wColor.value)) {
          wColor.value = vals[0] || "";
        }
        this.setDirtyCanvas(true, true);
      };

      const refreshFiles = async () => {
        const data = await apiJSON("/dao/rvb_picker/files");
        const files = Array.isArray(data.files) ? data.files : [];
        wList.options = wList.options || {};
        wList.options.values = files;
        if (!files.includes(wList.value)) {
          wList.value = files[0] || "";
        }
        await refreshColors();
        this.setDirtyCanvas(true, true);
      };

      // Recharger couleurs lors du changement de fichier
      wList.callback = refreshColors;

      // Bouton ↻
      if (!this.widgets.find((w) => w.name === "↻")) {
        this.addWidget("button", "↻", null, async () => { await refreshFiles(); });
      }

      refreshFiles();
    };
  },
});
