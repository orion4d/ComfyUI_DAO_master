// DAO_master — UI pour "Folder File Picker" (combo dynamique + refresh)
import { app } from "/scripts/app.js";
import { api } from "/scripts/api.js";

function asCombo(node, name, start = "", onChange = null) {
  const idx = node.widgets.findIndex(w => w.name === name);
  const old = idx >= 0 ? node.widgets[idx] : null;
  if (old && old.type === "combo") return old;

  const val = old ? old.value : start;
  if (old) node.widgets.splice(idx, 1);

  const w = node.addWidget("combo", name, val, (v) => {
    w.value = v;
    onChange?.(v);
  }, { values: [] });

  if (idx >= 0) {
    const last = node.widgets.length - 1;
    node.widgets.splice(idx, 0, w);
    node.widgets.splice(last + 1, 1);
  }
  return w;
}

app.registerExtension({
  name: "DAO_master.FolderFilePicker.UI",

  async beforeRegisterNodeDef(nodeType, nodeData) {
    if (nodeData?.name !== "Folder File Picker") return;

    const _onCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      _onCreated?.apply(this, arguments);
      console.log("[FolderFilePicker] UI hook attached");

      const wDir  = this.widgets.find(w => w.name === "directory");
      const wExt  = this.widgets.find(w => w.name === "extensions");

      const wRe   = this.widgets.find(w => w.name === "name_regex");
      const wReM  = this.widgets.find(w => w.name === "regex_mode");
      const wReIC = this.widgets.find(w => w.name === "regex_ignore_case");

      const wRec  = this.widgets.find(w => w.name === "recursive");
      const wSort = this.widgets.find(w => w.name === "sort_by");
      const wDesc = this.widgets.find(w => w.name === "descending");
      const wIdx  = this.widgets.find(w => w.name === "index");
      if (wIdx) wIdx.hidden = true;

      const wFile = asCombo(this, "file", "", (val) => {
        const list = this._fileList || [];
        const i = list.indexOf(val);
        if (wIdx && i >= 0) wIdx.value = i;
        this.setDirtyCanvas(true, true);
      });

      if (!this.widgets.find(w => w.name === "↻")) {
        this.addWidget("button", "↻", null, async () => { await refresh(); });
      }

      const rewire = (w) => {
        if (!w) return;
        const prev = w.callback;
        w.callback = (...args) => { prev?.apply(w, args); refresh(); };
      };
      [wDir, wExt, wRe, wReM, wReIC, wRec, wSort, wDesc].forEach(rewire);

      const refresh = async () => {
        try {
          const qs = new URLSearchParams({
            dir: (wDir?.value || "").toString(),
            exts: (wExt?.value || "").toString(),
            recursive: String(!!(wRec?.value)),
            sort_by: (wSort?.value || "name").toString(),
            descending: String(!!(wDesc?.value)),

            regex: (wRe?.value || "").toString(),
            regex_mode: (wReM?.value || "include").toString(),
            regex_ic: String(!!(wReIC?.value)),
          }).toString();

          const res = await api.fetchApi(`/dao_master/list_dir?${qs}`);
          if (!res?.ok) throw new Error("HTTP " + res.status);
          const data = await res.json();

          const names = (data.files || []).map(f => f.name);
          this._fileList = names;

          wFile.options.values.length = 0;
          wFile.options.values.push(...names);

          const idx = Math.max(0, Math.min((wIdx?.value ?? 0), names.length - 1));
          wFile.value = names[idx] || "";
          if (wIdx) wIdx.value = idx;

          this.setDirtyCanvas(true, true);
          console.log("[FolderFilePicker] files:", names.length);
        } catch (e) {
          console.warn("[FolderFilePicker] refresh error", e);
          this._fileList = [];
          wFile.options.values.length = 0;
          wFile.value = "";
          if (wIdx) wIdx.value = 0;
          this.setDirtyCanvas(true, true);
        }
      };

      refresh();
    };
  },
});
