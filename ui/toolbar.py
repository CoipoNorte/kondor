import os
import json
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from core.config import validate_path
from ui.styles   import make_tip


class Toolbar:
    def __init__(self, parent, app):
        self.app = app
        top = tk.Frame(parent, bg="#161b22", padx=6, pady=4)
        top.pack(fill="x")
        self._build_paths(top)
        self._build_buttons(top)
        self._build_opts(top)

    def _build_paths(self, top):
        paths = tk.Frame(top, bg="#161b22")
        paths.pack(fill="x", pady=1)

        tk.Label(paths, text="DIR", font=("Consolas", 8, "bold"),
            fg="#7c3aed", bg="#161b22", width=3).pack(side="left")
        self.folder_entry = tk.Entry(paths,
            textvariable=self.app.project_path,
            font=("Consolas", 8), bg="#0d1117", fg="#e2e8f0",
            insertbackground="#7c3aed", relief="flat", bd=0)
        self.folder_entry.pack(side="left", fill="x", expand=True, ipady=2, ipadx=3)
        make_tip(self.folder_entry, "Carpeta raíz del proyecto")
        ttk.Button(paths, text="..", style="P.TButton", width=2,
            command=self.app.select_folder).pack(side="left", padx=1)

        tk.Label(paths, text="MD", font=("Consolas", 8, "bold"),
            fg="#3b82f6", bg="#161b22", width=2).pack(side="left", padx=(4, 0))
        self.md_entry = tk.Entry(paths,
            textvariable=self.app.md_path,
            font=("Consolas", 8), bg="#0d1117", fg="#e2e8f0",
            insertbackground="#3b82f6", relief="flat", bd=0)
        self.md_entry.pack(side="left", fill="x", expand=True, ipady=2, ipadx=3)
        make_tip(self.md_entry, "Archivo .md con instrucciones")
        ttk.Button(paths, text="..", style="C.TButton", width=2,
            command=self.app.select_md).pack(side="left", padx=1)

    def _build_buttons(self, top):
        btns = tk.Frame(top, bg="#161b22")
        btns.pack(fill="x", pady=2)

        left = tk.Frame(btns, bg="#161b22")
        left.pack(side="left")

        def lb(text, style, cmd, tip, attr=None):
            b = ttk.Button(left, text=text, style=style, command=cmd)
            b.pack(side="left", padx=1)
            make_tip(b, tip)
            if attr:
                setattr(self.app, attr, b)

        lb("▶ RUN",     "G.TButton", self.app.run_all,              "Ejecutar todo (Ctrl+R)",    "run_btn")
        lb("📋 PASTE",  "T.TButton", self.app.paste_from_clipboard, "Pegar .md (Ctrl+V)")
        lb("🧹 CLR",    "P.TButton", self.app.clear_log,            "Limpiar log")
        lb("📜 SCRIPTS","O.TButton", self.app.show_scripts_menu,    "Scripts del package.json")
        lb("⌨ CMD",     "C.TButton", self.app.open_cmd,             "Abrir terminal CMD")
        lb("💬 PROMPT", "W.TButton", self.app.copy_prompt,          "Copiar instrucciones para IA")

        tk.Frame(left, bg="#30363d", width=1, height=16).pack(side="left", padx=4)

        lb("⏭ SKIP",   "Y.TButton", self.app.skip_instruction,     "Saltar instrucción actual", "skip_btn")
        lb("⏹ STOP",   "R.TButton", self.app.stop_execution,       "Detener todo (Esc)",        "stop_btn")
        lb("🔍 SCAN",  "P.TButton", self.app.parse_md,             "Analizar .md (Ctrl+S)")
        lb("↩ UNDO",   "O.TButton", self.app.undo_last,            "Deshacer (Ctrl+Z)")
        lb("📂 OPEN",  "C.TButton", self.app.open_explorer,        "Abrir en Explorer (Ctrl+O)")

        self.app.run_btn.state(["disabled"])
        self.app.skip_btn.state(["disabled"])
        self.app.stop_btn.state(["disabled"])

    def _build_opts(self, top):
        opts = tk.Frame(top, bg="#161b22")
        opts.pack(fill="x", pady=1)

        for text, var in [
            ("Auto-run", self.app.auto_run),
            ("Dry-run",  self.app.dry_run),
            ("Backup",   self.app.backup_enabled),
            ("CMD SEP",  self.app.cmd_sep_var),
        ]:
            ttk.Checkbutton(opts, text=text, variable=var,
                style="Dark.TCheckbutton").pack(side="left", padx=4)

        self.app.stats_label = tk.Label(opts, text="",
            font=("Consolas", 7), fg="#64748b", bg="#161b22")
        self.app.stats_label.pack(side="right", padx=4)
