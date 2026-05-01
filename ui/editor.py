import tkinter as tk
from tkinter import ttk, scrolledtext


class InstructionEditor:
    @staticmethod
    def open(root, instructions: list, index: int, log, on_done):
        if index < 0 or index >= len(instructions):
            return

        inst = instructions[index]
        win  = tk.Toplevel(root)
        win.title(f"Edit [{index+1}] {inst['action']} — {inst['filepath']}")
        win.geometry("600x400")
        win.configure(bg="#0d1117")
        win.transient(root)
        win.grab_set()

        top = tk.Frame(win, bg="#161b22", padx=8, pady=6)
        top.pack(fill="x")

        tk.Label(top, text=f"{inst['action']}  →  {inst['filepath']}",
            font=("Consolas", 9, "bold"),
            fg="#7c3aed", bg="#161b22").pack(side="left")

        def save():
            instructions[index]["content"] = editor.get("1.0", "end-1c").strip()
            log(f"  EDITED [{index+1}] {inst['filepath']}", "undo")
            win.destroy()
            on_done()

        def cancel():
            win.destroy()

        def delete():
            instructions.pop(index)
            log(f"  REMOVED [{index+1}] {inst['filepath']}", "warn")
            win.destroy()
            on_done()

        ttk.Button(top, text="ELIMINAR", style="R.TButton",
            command=delete).pack(side="right", padx=2)
        ttk.Button(top, text="CANCELAR", style="W.TButton",
            command=cancel).pack(side="right", padx=2)
        ttk.Button(top, text="GUARDAR", style="G.TButton",
            command=save).pack(side="right", padx=2)

        editor = scrolledtext.ScrolledText(win,
            font=("Consolas", 10), bg="#161b22", fg="#e2e8f0",
            insertbackground="#7c3aed", relief="flat", bd=0,
            wrap="none", padx=8, pady=8)
        editor.pack(fill="both", expand=True, padx=6, pady=(0, 6))
        editor.insert("1.0", inst["content"])
        editor.focus_set()
