import tkinter as tk
from ui.styles import make_tip

HAS_TRAY = False
try:
    import pystray
    HAS_TRAY = True
except ImportError:
    pass


class StatusBar:
    def __init__(self, parent, node_status: str, npm_status: str,
                 copy_minip_fn):
        frame = tk.Frame(parent, bg="#161b22", height=18)
        frame.pack(fill="x", side="bottom")

        self.status_label = tk.Label(frame, text="Ready",
            font=("Consolas", 7), fg="#10b981", bg="#161b22")
        self.status_label.pack(side="left", padx=4)

        # 🐱 botón P
        p_frame = tk.Frame(frame, bg="#7c3aed", cursor="hand2")
        p_frame.pack(side="left", padx=(4, 0))
        p_label = tk.Label(p_frame, text="P",
            font=("Consolas", 7, "bold"),
            fg="#fff", bg="#7c3aed", padx=4, pady=1)
        p_label.pack()
        for w in (p_frame, p_label):
            w.bind("<Button-1>", lambda e: copy_minip_fn())
            w.bind("<Enter>", lambda e: [
                p_frame.config(bg="#6d28d9"), p_label.config(bg="#6d28d9")])
            w.bind("<Leave>", lambda e: [
                p_frame.config(bg="#7c3aed"), p_label.config(bg="#7c3aed")])
        make_tip(p_frame, "Mini prompt compacto")

        tk.Label(frame, text=f"{node_status} | {npm_status}",
            font=("Consolas", 7), fg="#30363d", bg="#161b22").pack(side="right", padx=4)

        hint = "[X]=menu" if HAS_TRAY else ""
        tk.Label(frame,
            text=f"Ctrl+V=paste  Ctrl+R=run  Esc=stop  {hint}",
            font=("Consolas", 7), fg="#21262d", bg="#161b22").pack(side="right", padx=8)

    def set_text(self, text: str):
        self.status_label.config(text=text)
