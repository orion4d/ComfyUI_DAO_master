// ComfyUI_DAO_master / web / dao_text_maker.js
// Combo dynamique pour choisir la police dans ./Fonts/

import { app } from "/scripts/app.js";

async function apiJSON(url) {
  try {
    const r = await fetch(url, { cache: "no-store" });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return await r.json();
  } catch (e) {
    console.error("[DAO][text-maker] fetch error:", e, url);
    return {};
  }
}

function replaceWithCombo(node, widgetName) {
  const idx = node.widgets.findIndex((w) => w.name === widgetName);
  const oldW = idx >= 0 ? node.widgets[idx] : null;
  if (oldW && oldW.type === "combo") return oldW;

  const startVal = oldW ? oldW.value : "";
  if (oldW) node.widgets.splice(idx, 1);

  const newW = node.addWidget(
    "combo",
    widgetName,
    startVal,
    (v) => { newW.value = v; },
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
  name: "DAO.TextMaker",
  async beforeRegisterNodeDef(nodeType, nodeData) {
    const isTarget =
      (nodeData?.name && /Text Maker/i.test(nodeData.name)) ||
      (nodeData?.category && /DAO_master\/Text/i.test(nodeData.category));
    if (!isTarget) return;

    const _onNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      _onNodeCreated?.apply(this, arguments);

      const wFont = replaceWithCombo(this, "font_file");

      const refreshFonts = async () => {
        const data = await apiJSON("/dao/text/fonts");
        const vals = Array.isArray(data.fonts) ? data.fonts : [];
        wFont.options = wFont.options || {};
        wFont.options.values = vals;
        if (!vals.includes(wFont.value)) {
          wFont.value = vals[0] || "";
        }
        this.setDirtyCanvas(true, true);
      };

      if (!this.widgets.find((w) => w.name === "↻")) {
        this.addWidget("button", "↻", null, async () => { await refreshFonts(); });
      }

      refreshFonts();
    };
  },
});
