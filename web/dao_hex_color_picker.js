// ComfyUI_DAO_master / web / dao_hex_color_picker.js
// Rend "list_file" et "color" vraiment dynamiques (combos) même si Python déclare STRING

import { app } from "/scripts/app.js";

async function apiJSON(url) {
  try {
    const r = await fetch(url, { cache: "no-store" });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return await r.json();
  } catch (e) {
    console.error("[DAO][hex-picker] fetch error:", e, url);
    return {};
  }
}

/** Remplace un widget existant par un vrai combo, en gardant le même nom et sa position */
function replaceWithCombo(node, widgetName, initialValue, onChange) {
  // Trouve l'ancien widget
  const idx = node.widgets.findIndex((w) => w.name === widgetName);
  let oldW = idx >= 0 ? node.widgets[idx] : null;

  // Si c'est déjà un combo, on renvoie tel quel
  if (oldW && oldW.type === "combo") return oldW;

  // Valeur de départ
  const startVal = initialValue ?? (oldW ? oldW.value : "");

  // Supprime l'ancien si présent
  if (oldW) node.widgets.splice(idx, 1);

  // Crée le nouveau combo
  const newW = node.addWidget(
    "combo",
    widgetName,
    startVal,
    (v, w, n) => {
      newW.value = v;
      onChange?.(v);
    },
    { values: [] }
  );

  // Replace à l'ancienne position pour garder l’ordre visuel
  if (idx >= 0) {
    const last = node.widgets.length - 1;
    node.widgets.splice(idx, 0, newW);
    node.widgets.splice(last + 1, 1);
  }

  return newW;
}

app.registerExtension({
  name: "DAO.HexColorPicker",
  async beforeRegisterNodeDef(nodeType, nodeData) {
    // On cible ton node (nom et/ou catégorie)
    const isTarget =
      (nodeData?.name && /Hex Color Picker/i.test(nodeData.name)) ||
      (nodeData?.category && /DAO_master\/Color\/DAO/i.test(nodeData.category));

    if (!isTarget) return;

    const _onNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      _onNodeCreated?.apply(this, arguments);

      // Remplace "list_file" et "color" par de vrais combos
      const wList  = replaceWithCombo(this, "list_file");
      const wColor = replaceWithCombo(this, "color");

      const refreshColors = async () => {
        const file = encodeURIComponent(wList.value || "");
        const data = await apiJSON(`/dao/hex_picker/colors?file=${file}`);
        const vals = Array.isArray(data.colors) ? data.colors : [];
        wColor.options = wColor.options || {};
        wColor.options.values = vals;
        if (!vals.includes(wColor.value)) {
          wColor.value = vals[0] || "";
        }
        this.setDirtyCanvas(true, true);
      };

      const refreshFiles = async () => {
        const data = await apiJSON("/dao/hex_picker/files");
        const files = Array.isArray(data.files) ? data.files : [];
        wList.options = wList.options || {};
        wList.options.values = files;
        if (!files.includes(wList.value)) {
          wList.value = files[0] || "";
        }
        await refreshColors();
        this.setDirtyCanvas(true, true);
      };

      // Quand on change de fichier => recharge les couleurs
      wList.callback = refreshColors;

      // Bouton ↻ pour recharger la liste des fichiers + couleurs
      if (!this.widgets.find((w) => w.name === "↻")) {
        this.addWidget("button", "↻", null, async () => {
          await refreshFiles();
        });
      }

      // Premier remplissage
      refreshFiles();
    };
  },
});
