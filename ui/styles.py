from tkinter import ttk


TAGS = [
    ("ok",          "#10b981", False),
    ("err",         "#ef4444", False),
    ("warn",        "#f59e0b", False),
    ("info",        "#3b82f6", False),
    ("cmd",         "#7c3aed", False),
    ("path",        "#06b6d4", False),
    ("head",        "#7c3aed", True),
    ("dim",         "#30363d", False),
    ("white",       "#e2e8f0", False),
    ("interactive", "#f59e0b", True),
    ("replace",     "#06b6d4", True),
    ("dry",         "#f59e0b", True),
    ("undo",        "#f97316", True),
    ("block",       "#a78bfa", True),
]

BUTTONS = [
    ("P", "#7c3aed", "#6d28d9", "white"),
    ("G", "#10b981", "#059669", "white"),
    ("R", "#ef4444", "#dc2626", "white"),
    ("Y", "#f59e0b", "#d97706", "black"),
    ("C", "#3b82f6", "#2563eb", "white"),
    ("W", "#64748b", "#475569", "white"),
    ("T", "#06b6d4", "#0891b2", "white"),
    ("O", "#f97316", "#ea580c", "white"),
]


def apply_styles(style: ttk.Style):
    style.theme_use("clam")

    for prefix, bg, active, fg in BUTTONS:
        style.configure(f"{prefix}.TButton",
            background=bg, foreground=fg,
            font=("Consolas", 8), padding=(6, 2))
        style.map(f"{prefix}.TButton",
            background=[("active", active), ("disabled", "#333")])

    style.configure("Dark.TCheckbutton",
        background="#161b22", foreground="#8b949e",
        font=("Consolas", 8))

    style.configure("Treeview",
        background="#0d1117", foreground="#e2e8f0",
        fieldbackground="#0d1117", borderwidth=0,
        font=("Consolas", 8), rowheight=20)
    style.map("Treeview",
        background=[("selected", "#1e293b")],
        foreground=[("selected", "#7c3aed")])


def apply_log_tags(log_widget):
    for tag, color, bold in TAGS:
        font = ("Consolas", 9, "bold") if bold else ("Consolas", 9)
        log_widget.tag_configure(tag, foreground=color, font=font)


def make_tip(widget, text: str):
    tip = None
    def enter(e):
        nonlocal tip
        x = widget.winfo_rootx() + 20
        y = widget.winfo_rooty() + widget.winfo_height() + 2
        import tkinter as tk
        tip = tk.Toplevel(widget)
        tip.wm_overrideredirect(True)
        tip.wm_geometry(f"+{x}+{y}")
        tk.Label(tip, text=text, font=("Consolas", 8),
            bg="#1f2937", fg="#e2e8f0", padx=6, pady=2).pack()
    def leave(e):
        nonlocal tip
        if tip:
            tip.destroy()
            tip = None
    widget.bind("<Enter>", enter)
    widget.bind("<Leave>", leave)
