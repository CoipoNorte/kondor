import os
import json
import subprocess
import tkinter as tk
from tkinter import messagebox


class ScriptsMenu:
    def __init__(self, root, project_var: tk.StringVar, log):
        self.root        = root
        self.project_var = project_var
        self.log         = log

    def show(self):
        p = self.project_var.get()
        if not p or not os.path.isdir(p):
            messagebox.showerror("Error", "Select DIR first")
            return

        pkg_path = os.path.join(p, "package.json")
        if not os.path.exists(pkg_path):
            messagebox.showerror("Error", "No package.json found")
            return

        try:
            with open(pkg_path, "r", encoding="utf-8") as f:
                pkg = json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"Error reading package.json:\n{e}")
            return

        scripts = pkg.get("scripts", {})
        if not scripts:
            messagebox.showinfo("Scripts", "No scripts found")
            return

        menu = tk.Menu(self.root, tearoff=0,
            bg="#1e293b", fg="#e2e8f0",
            activebackground="#7c3aed", activeforeground="#fff",
            font=("Consolas", 9), relief="flat", bd=0)

        menu.add_command(label="  ── scripts ──  ", state="disabled")

        for name, cmd in scripts.items():
            preview = cmd[:45] + "..." if len(cmd) > 45 else cmd
            menu.add_command(
                label=f"  {name:<12} {preview}",
                command=lambda n=name: self._run(n, p))

        menu.add_separator()
        menu.add_command(label="  Cancelar  ", command=menu.destroy)

        x = self.root.winfo_pointerx()
        y = self.root.winfo_pointery()
        try:
            menu.tk_popup(x, y)
        finally:
            menu.grab_release()

    def _run(self, script_name: str, p: str):
        cmd = f"npm run {script_name}"
        self.log(f"  [SCRIPT] {cmd}", "interactive")
        try:
            subprocess.Popen(
                f'start cmd /k "'
                                f'title KONDOR — {cmd} && '
                f'echo ======================================== && '
                f'echo  {cmd} && '
                f'echo ======================================== && echo. && '
                f'cd /d "{p}" && {cmd}"',
                shell=True, cwd=p)
        except Exception as e:
            self.log(f"  SCRIPT ERR: {e}", "err")
