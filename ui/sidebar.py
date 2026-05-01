import os
import tkinter as tk
from tkinter import ttk
from core.config import IGNORE_DIRS, IGNORE_FILES
from ui.styles  import make_tip


FILE_ICONS = {
    "js": "📜", "jsx": "⚛️",  "ts":   "📘", "tsx": "⚛️",
    "css": "🎨", "html": "🌐", "json": "📋", "md":  "📝",
    "py": "🐍",  "svg": "🖼️",  "png":  "🖼️", "jpg": "🖼️",
    "ico": "🖼️", "txt": "📄",  "env":  "🔒", "yml": "⚙️",
    "yaml": "⚙️","toml": "⚙️", "lock": "🔒", "sh":  "🐚",
    "bat": "🐚", "cmd": "🐚",  "sql":  "🗄️", "db":  "🗄️",
}

HIDDEN_ALLOWED = {".env", ".gitignore", ".env.local"}


def file_icon(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return FILE_ICONS.get(ext, "📄")


def _filter(entries, path):
    result = []
    for e in entries:
        full = os.path.join(path, e)
        if os.path.isdir(full) and e in IGNORE_DIRS:
            continue
        if e in IGNORE_FILES:
            continue
        if e.startswith(".") and e not in HIDDEN_ALLOWED:
            continue
        result.append(e)
    return result


class Sidebar:
    def __init__(self, parent, project_var: tk.StringVar, log, root):
        self.project_var = project_var
        self.log         = log
        self.root        = root

        frame = tk.Frame(parent, bg="#0d1117", width=220)
        frame.pack(side="left", fill="y")
        frame.pack_propagate(False)

        # 🐱 header
        header = tk.Frame(frame, bg="#161b22")
        header.pack(fill="x")

        tk.Label(header, text="FILES", font=("Consolas", 7, "bold"),
            fg="#64748b", bg="#161b22", padx=6, pady=3).pack(side="left")

        refresh_lbl = tk.Label(header, text="↻",
            font=("Consolas", 10), fg="#64748b", bg="#161b22",
            cursor="hand2", padx=4, pady=2)
        refresh_lbl.pack(side="right")
        refresh_lbl.bind("<Button-1>", lambda e: self.refresh())
        refresh_lbl.bind("<Enter>", lambda e: refresh_lbl.config(fg="#7c3aed"))
        refresh_lbl.bind("<Leave>", lambda e: refresh_lbl.config(fg="#64748b"))
        make_tip(refresh_lbl, "Refrescar árbol")

        copy_lbl = tk.Label(header, text="📋",
            font=("Consolas", 9), fg="#64748b", bg="#161b22",
            cursor="hand2", padx=4, pady=2)
        copy_lbl.pack(side="right")
        copy_lbl.bind("<Button-1>", lambda e: self.copy_tree())
        copy_lbl.bind("<Enter>", lambda e: copy_lbl.config(fg="#7c3aed"))
        copy_lbl.bind("<Leave>", lambda e: copy_lbl.config(fg="#64748b"))
        make_tip(copy_lbl, "Copiar estructura al portapapeles")

        # 🐱 árbol
        tree_frame = tk.Frame(frame, bg="#0d1117")
        tree_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(tree_frame, show="tree", selectmode="browse")
        scroll    = ttk.Scrollbar(tree_frame, orient="vertical",
                        command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)

        # 🐱 separador
        tk.Frame(parent, bg="#21262d", width=1).pack(side="left", fill="y")

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        p = self.project_var.get()
        if not p or not os.path.isdir(p):
            return
        root_name = os.path.basename(p) or p
        node = self.tree.insert("", "end", text=f"📁 {root_name}", open=True)
        self._populate(node, p)

    def _populate(self, parent, path):
        try:
            entries = sorted(os.listdir(path),
                key=lambda x: (not os.path.isdir(os.path.join(path, x)), x.lower()))
        except PermissionError:
            return

        for e in _filter(entries, path):
            full = os.path.join(path, e)
            if os.path.isdir(full):
                node = self.tree.insert(parent, "end", text=f"📁 {e}")
                self._populate(node, full)
            else:
                self.tree.insert(parent, "end", text=f"{file_icon(e)} {e}")

    def copy_tree(self):
        p = self.project_var.get()
        if not p or not os.path.isdir(p):
            return
        lines = [f"📁 {os.path.basename(p)}/"]
        self._build_text(p, "", lines)
        self.root.clipboard_clear()
        self.root.clipboard_append("\n".join(lines))
        self.root.update()
        self.log(f"Tree copied! ({len(lines)} lines)", "ok")

    def _build_text(self, path, prefix, lines):
        try:
            entries = sorted(os.listdir(path),
                key=lambda x: (not os.path.isdir(os.path.join(path, x)), x.lower()))
        except PermissionError:
            return

        filtered = _filter(entries, path)
        for idx, e in enumerate(filtered):
            full      = os.path.join(path, e)
            is_last   = idx == len(filtered) - 1
            connector = "└── " if is_last else "├── "
            ext_str   = "    " if is_last else "│   "
            if os.path.isdir(full):
                lines.append(f"{prefix}{connector}📁 {e}/")
                self._build_text(full, prefix + ext_str, lines)
            else:
                lines.append(f"{prefix}{connector}{file_icon(e)} {e}")
