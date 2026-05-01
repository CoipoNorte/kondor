import os
import re
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox, ttk
import time
import json
import shutil
import winsound
import ctypes

try:
    import pystray
    from PIL import Image
    HAS_TRAY = True
except ImportError:
    HAS_TRAY = False

try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    HAS_DND = True
except ImportError:
    HAS_DND = False

from core.config   import APP_VERSION, CONFIG_FILE, find_file, load_txt, validate_path
from core.process  import ProcessManager
from core.files    import FileManager
from core.parser   import extract_instructions
from core.executor import Executor
from ui.styles     import apply_styles, apply_log_tags
from ui.toolbar    import Toolbar
from ui.sidebar    import Sidebar
from ui.statusbar  import StatusBar
from ui.editor     import InstructionEditor
from ui.scripts    import ScriptsMenu


PROMPT_TEXT = load_txt("prompt.txt")
MINIP_TEXT  = load_txt("minip.txt")


class AutoBuilder:
    def __init__(self):
        self.root = TkinterDnD.Tk() if HAS_DND else tk.Tk()
        self.root.title(f"KONDOR v{APP_VERSION}")
        self.root.configure(bg="#0d1117")
        self.root.resizable(True, True)

        self.config = self._load_config()
        self.root.geometry(self.config.get("geometry", "1100x650"))

        self.project_path   = tk.StringVar(value=self.config.get("last_dir", ""))
        self.md_path        = tk.StringVar(value="")
        self.is_running     = False
        self.skip_current   = False
        self.stop_all       = False
        self.instructions   = []
        self.cmd_sep_var    = tk.BooleanVar(value=True)
        self.dry_run        = tk.BooleanVar(value=False)
        self.auto_run       = tk.BooleanVar(value=False)
        self.backup_enabled = tk.BooleanVar(value=True)
        self.undo_stack     = []

        self.pm = ProcessManager()
        self.fm = FileManager(
            temp_dir=os.path.join(os.path.dirname(CONFIG_FILE), "_kondor_tmp"),
            backup_enabled_fn=self.backup_enabled.get,
            undo_stack=self.undo_stack,
            log=self.log_msg,
        )
        os.makedirs(self.fm.temp_dir, exist_ok=True)

        self.tray_icon    = None
        self.tray_running = False

        self.spinner_chars   = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        self.spinner_idx     = 0
        self.spinner_running = False
        self.spinner_text    = ""

        self.icon_path = find_file("condor.ico")
        if self.icon_path:
            try:
                self.root.iconbitmap(self.icon_path)
            except Exception:
                pass

        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("kondor.v6")
        except Exception:
            pass

        self._check_node()

        self.style = ttk.Style()
        apply_styles(self.style)

        self._build_ui()
        self._setup_keybindings()
        self._setup_drag_drop()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        if self.project_path.get() and os.path.isdir(self.project_path.get()):
            self.root.after(200, self.sidebar.refresh)

    def _load_config(self) -> dict:
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return {
            "recent_dirs": [],
            "recent_mds": [],
            "geometry": "1100x650",
            "last_dir": "",
        }

    def _save_config(self):
        try:
            self.config["geometry"] = self.root.geometry()
            self.config["last_dir"] = self.project_path.get()
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2)
        except Exception:
            pass

    def _add_recent(self, key, path):
        lst = self.config.setdefault(key, [])
        if path in lst:
            lst.remove(path)
        lst.insert(0, path)
        self.config[key] = lst[:10]
        self._save_config()

    def _check_node(self):
        def run(cmd):
            try:
                r = subprocess.run(cmd, shell=True, capture_output=True,
                                   text=True, timeout=5)
                return r.stdout.strip() if r.returncode == 0 else None
            except Exception:
                return None

        node_v = run("node --version")
        npm_v  = run("npm --version")
        self.node_status = f"node {node_v}" if node_v else "node: NOT FOUND"
        self.npm_status  = f"npm {npm_v}" if npm_v else "npm: NOT FOUND"

    def _build_ui(self):
        Toolbar(self.root, self)

        self.progress_bar = tk.Canvas(
            self.root, height=3, bg="#161b22", highlightthickness=0
        )
        self.progress_bar.pack(fill="x")

        main = tk.Frame(self.root, bg="#0d1117")
        main.pack(fill="both", expand=True)

        self.sidebar = Sidebar(main, self.project_path, self.log_msg, self.root)

        self.log = scrolledtext.ScrolledText(
            main,
            font=("Consolas", 9),
            bg="#0d1117",
            fg="#e2e8f0",
            insertbackground="#7c3aed",
            relief="flat",
            bd=0,
            wrap="word",
            state="disabled",
            padx=8,
            pady=4,
        )
        self.log.pack(side="left", fill="both", expand=True)
        apply_log_tags(self.log)

        self.scripts_menu = ScriptsMenu(self.root, self.project_path, self.log_msg)

        self.statusbar = StatusBar(
            self.root,
            self.node_status,
            self.npm_status,
            self._copy_minip,
        )

    def _setup_keybindings(self):
        b = self.root.bind
        b("<Control-v>", lambda e: self.paste_from_clipboard())
        b("<Control-r>", lambda e: self.run_all())
        b("<Control-s>", lambda e: self.parse_md())
        b("<Control-z>", lambda e: self.undo_last())
        b("<Control-o>", lambda e: self.open_explorer())
        b("<Escape>", lambda e: self.stop_execution())

    def _setup_drag_drop(self):
        if not HAS_DND:
            return
        try:
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind("<<Drop>>", self._on_drop)
            self.log_msg("Drag & Drop enabled", "ok")
        except Exception as e:
            self.log_msg(f"DnD not available: {e}", "dim")

    def _on_drop(self, event):
        raw = event.data.strip()

        paths = []
        for match in re.findall(r'\{[^}]+\}|[^\s]+', raw):
            clean = match.strip("{}\"'")
            if clean:
                paths.append(os.path.normpath(clean))

        if not paths:
            self.log_msg("DROP: empty payload", "warn")
            return

        path = None
        for candidate in paths:
            if os.path.exists(candidate):
                path = candidate
                break

        if not path:
            self.log_msg(f"DROP: path not found → {raw}", "err")
            return

        if os.path.isdir(path):
            if not validate_path(path):
                messagebox.showerror("Error", "Dangerous path!")
                return
            self.project_path.set(path)
            self._add_recent("recent_dirs", path)
            self.log_msg(f"DROP DIR: {path}", "path")
            self.sidebar.refresh()
            return

        if os.path.isfile(path):
            ext = path.lower().rsplit(".", 1)[-1] if "." in path else ""
            if ext in ("md", "txt"):
                self.md_path.set(path)
                self._add_recent("recent_mds", path)
                self.log_msg(f"DROP FILE: {path}", "path")
                self.parse_md()
            else:
                self.log_msg(f"DROP: unsupported file type → {path}", "warn")
            return

        self.log_msg(f"DROP: unsupported → {path}", "warn")

    def _on_close(self):
        self._save_config()

        menu = tk.Menu(
            self.root,
            tearoff=0,
            bg="#1e293b",
            fg="#e2e8f0",
            activebackground="#7c3aed",
            activeforeground="#fff",
            font=("Consolas", 9),
            relief="flat",
            bd=0,
        )

        if HAS_TRAY:
            menu.add_command(
                label="  Minimizar a bandeja  ",
                command=self._hide_to_tray,
            )

        menu.add_command(label="  Cerrar KONDOR  ", command=self._quit_app)
        menu.add_separator()
        menu.add_command(label="  Cancelar  ", command=menu.destroy)

        x = self.root.winfo_x() + self.root.winfo_width() - 180
        y = self.root.winfo_y() + 30

        try:
            menu.tk_popup(x, y)
        finally:
            menu.grab_release()

    def _load_pil_image(self):
        if self.icon_path and HAS_TRAY:
            try:
                return Image.open(self.icon_path).convert("RGBA").resize((64, 64))
            except Exception:
                pass
        if HAS_TRAY:
            return Image.new("RGBA", (64, 64), (124, 58, 237, 255))
        return None

    def _hide_to_tray(self):
        self.root.withdraw()
        if self.tray_running:
            return

        image = self._load_pil_image()
        menu = pystray.Menu(
            pystray.MenuItem("Abrir KONDOR", self._cb_show, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Cerrar KONDOR", self._cb_exit),
        )
        self.tray_icon = pystray.Icon("kondor", image, f"KONDOR v{APP_VERSION}", menu)
        self.tray_running = True
        threading.Thread(target=self._tray_loop, daemon=True).start()

    def _tray_loop(self):
        try:
            self.tray_icon.run()
        finally:
            self.tray_running = False

    def _cb_show(self, icon, item):
        self.root.after(0, self._restore)

    def _restore(self):
        self._stop_tray()
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def _cb_exit(self, icon, item):
        self.root.after(0, self._quit_app)

    def _stop_tray(self):
        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
            self.tray_icon = None
            self.tray_running = False

    def _quit_app(self):
        self._save_config()
        self.stop_all = True
        self.skip_current = True
        self.pm.kill()
        self._stop_tray()
        shutil.rmtree(self.fm.temp_dir, ignore_errors=True)
        self.root.destroy()

    def log_msg(self, msg: str, tag: str = "white"):
        self.log.configure(state="normal")
        lines = int(self.log.index("end-1c").split(".")[0])
        if lines > 600:
            self.log.delete("1.0", f"{lines - 500}.0")
        self.log.insert("end", msg + "\n", tag)
        self.log.see("end")
        self.log.configure(state="disabled")

    def clear_log(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")
        self.stats_label.config(text="")
        self._reset_progress()

    def _update_progress(self, current, total, action=""):
        self.progress_bar.delete("all")
        if total <= 0:
            return
        w = self.progress_bar.winfo_width()
        fw = int((current / total) * w)
        self.progress_bar.create_rectangle(0, 0, fw, 3, fill="#7c3aed", outline="")
        self.spinner_text = f"[{current}/{total}] {action}"

    def _reset_progress(self):
        self.progress_bar.delete("all")

    def _start_spinner(self, text="Processing"):
        self.spinner_running = True
        self.spinner_text = text
        self._tick_spinner()

    def _tick_spinner(self):
        if not self.spinner_running:
            return
        c = self.spinner_chars[self.spinner_idx % len(self.spinner_chars)]
        self.spinner_idx += 1
        self.statusbar.set_text(f"{c} {self.spinner_text}")
        self.root.after(100, self._tick_spinner)

    def _stop_spinner(self):
        self.spinner_running = False
        self.statusbar.set_text("Ready")

    def _beep(self, success=True):
        try:
            winsound.MessageBeep(
                winsound.MB_OK if success else winsound.MB_ICONHAND
            )
        except Exception:
            pass

    def _notify(self, title, msg):
        if HAS_TRAY and self.tray_icon and self.tray_running:
            try:
                self.tray_icon.notify(title, msg)
            except Exception:
                pass

    def select_folder(self):
        path = filedialog.askdirectory(title="Project root folder")
        if not path:
            return
        if not validate_path(path):
            messagebox.showerror("Error", "Dangerous path!")
            return
        self.project_path.set(path)
        self._add_recent("recent_dirs", path)
        self.log_msg(f"DIR: {path}", "path")
        self.sidebar.refresh()

    def select_md(self):
        path = filedialog.askopenfilename(
            title=".md file",
            filetypes=[("Markdown", "*.md"), ("All", "*.*")],
        )
        if not path:
            return
        self.md_path.set(path)
        self._add_recent("recent_mds", path)
        self.log_msg(f".MD: {path}", "path")

    def open_cmd(self):
        p = self.project_path.get()
        if not p or not os.path.isdir(p):
            messagebox.showerror("Error", "Select a valid project folder first")
            return
        subprocess.Popen(f'start cmd /k "cd /d {p}"', shell=True)
        self.log_msg(f"CMD: {p}", "ok")

    def open_explorer(self):
        p = self.project_path.get()
        if not p or not os.path.isdir(p):
            messagebox.showerror("Error", "Select a valid project folder first")
            return
        os.startfile(p)
        self.log_msg(f"OPEN: {p}", "ok")

    def copy_prompt(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(PROMPT_TEXT)
        self.root.update()
        self.log_msg("PROMPT copied!", "ok")

    def _copy_minip(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(MINIP_TEXT)
        self.root.update()
        self.log_msg("Mini prompt copied!", "ok")

    def show_scripts_menu(self):
        self.scripts_menu.show()

    def undo_last(self):
        self.fm.undo_last()

    def skip_instruction(self):
        if not self.is_running:
            return
        self.skip_current = True
        self.log_msg(">> SKIPPING...", "warn")
        self.pm.kill()

    def stop_execution(self):
        if not self.is_running:
            return
        self.stop_all = True
        self.skip_current = True
        self.log_msg(">> STOPPING...", "err")
        self.pm.kill()

    def paste_from_clipboard(self):
        try:
            clipboard = self.root.clipboard_get()
        except tk.TclError:
            messagebox.showerror("Error", "Clipboard is empty")
            return
        if not clipboard.strip():
            return
        p = self.project_path.get()
        if not p or not os.path.isdir(p):
            messagebox.showerror("Error", "Select DIR first")
            return

        tmp = os.path.join(self.fm.temp_dir, f"paste_{int(time.time())}.md")
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(clipboard)

        self.md_path.set(tmp)
        self.log_msg(f"PASTE: {len(clipboard)} chars", "ok")
        self.parse_md()

    def parse_md(self):
        md_file = self.md_path.get()
        if not md_file or not os.path.exists(md_file):
            messagebox.showerror("Error", "Select a valid .md file")
            return

        project = self.project_path.get()
        if not project or not os.path.isdir(project):
            messagebox.showerror("Error", "Select a valid folder")
            return

        if not validate_path(project):
            messagebox.showerror("Error", "Dangerous path!")
            return

        try:
            with open(md_file, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            self.log_msg(f"Error reading file: {e}", "err")
            return

        self.instructions = extract_instructions(content, self.log_msg)
        self._display_instructions()
        self.log.bind("<Double-Button-1>", self._on_log_double_click)

        if self.auto_run.get() and self.instructions:
            self.run_all()

    def _display_instructions(self):
        self.clear_log()
        self.log_msg("=" * 50, "dim")
        self.log_msg("INSTRUCTIONS — double-click to edit", "head")
        self.log_msg("=" * 50, "dim")

        if not self.instructions:
            self.log_msg("No instructions", "warn")
            self.run_btn.state(["disabled"])
            return

        counts = {}
        for inst in self.instructions:
            counts[inst["action"]] = counts.get(inst["action"], 0) + 1

        self.log_msg(f"Found: {len(self.instructions)} instructions", "info")
        for a, c in counts.items():
            self.log_msg(f"  {a}: {c}", "info")
        self.log_msg("")

        for i, inst in enumerate(self.instructions):
            a = inst["action"]
            if a == "EJECUTAR":
                preview = inst["content"].replace("\n", " | ")[:60]
                self.log_msg(f"  {i+1:02d}. EXEC  {preview}...", "cmd")
            elif a == "ELIMINAR":
                self.log_msg(f"  {i+1:02d}. DEL   {inst['filepath']}", "warn")
            elif a == "REEMPLAZAR":
                self.log_msg(f"  {i+1:02d}. REPL  {inst['filepath']}", "replace")
            else:
                n = inst["content"].count("\n") + 1
                act = "NEW" if a == "CREAR" else "MOD"
                self.log_msg(f"  {i+1:02d}. {act}   {inst['filepath']} ({n}L)", "cmd")

        self.log_msg("")
        self.log_msg("Double-click to edit. Press RUN to execute.", "ok")
        self.stats_label.config(
            text=" | ".join(f"{a}:{c}" for a, c in counts.items())
        )
        self.run_btn.state(["!disabled"])

    def _on_log_double_click(self, event):
        if self.is_running or not self.instructions:
            return

        index = self.log.index(f"@{event.x},{event.y}")
        line_num = int(index.split(".")[0])

        self.log.configure(state="normal")
        line_text = self.log.get(f"{line_num}.0", f"{line_num}.end").strip()
        self.log.configure(state="disabled")

        m = re.match(r'^\s*(\d+)\.', line_text)
        if m:
            idx = int(m.group(1)) - 1
            if 0 <= idx < len(self.instructions):
                InstructionEditor.open(
                    self.root,
                    self.instructions,
                    idx,
                    self.log_msg,
                    self._display_instructions,
                )

    def run_all(self):
        if self.is_running or not self.instructions:
            return

        mode = "DRY-RUN" if self.dry_run.get() else "EXECUTE"
        if not messagebox.askyesno(
            "Confirm",
            f"{mode}: {len(self.instructions)} instructions\n"
            f"Project: {self.project_path.get()}\n\nContinue?"
        ):
            return

        self.is_running   = True
        self.stop_all     = False
        self.skip_current = False
        self.run_btn.state(["disabled"])
        self.skip_btn.state(["!disabled"])
        self.stop_btn.state(["!disabled"])
        self._start_spinner("Executing")

        executor = Executor(
            fm=self.fm,
            pm=self.pm,
            log=self.log_msg,
            cmd_sep_fn=self.cmd_sep_var.get,
            stop_fn=lambda: self.stop_all,
            skip_fn=lambda: self.skip_current,
        )

        def run_thread():
            executor.run(
                project=self.project_path.get(),
                instructions=self.instructions,
                dry_run=self.dry_run.get(),
                on_progress=lambda c, t, a: self.root.after(
                    0, lambda: self._update_progress(c, t, a)
                ),
                on_done=lambda ok, err, skip, stopped: self.root.after(
                    0, lambda: self._on_done(ok, err, skip, stopped)
                ),
            )

        threading.Thread(target=run_thread, daemon=True).start()

    def _on_done(self, ok, err, skip, stopped):
        if err == 0 and not stopped:
            self.log_msg("Done!", "ok")
            self._beep(True)
            self._notify("KONDOR", "Execution completed!")
        elif stopped:
            self.log_msg("Stopped by user", "warn")
        else:
            self.log_msg(f"Done with {err} errors", "warn")
            self._beep(False)
            self._notify("KONDOR", f"Completed with {err} errors")

        self.sidebar.refresh()
        self._finish()

    def _finish(self):
        self.is_running   = False
        self.stop_all     = False
        self.skip_current = False
        self._stop_spinner()
        self.run_btn.state(["!disabled"])
        self.skip_btn.state(["disabled"])
        self.stop_btn.state(["disabled"])

    def run(self):
        self.log_msg(f"KONDOR v{APP_VERSION}", "head")
        self.log_msg(f"{self.node_status} | {self.npm_status}", "info")
        self.log_msg(
            "Ctrl+V=paste  Ctrl+R=run  Ctrl+S=scan  "
            "Ctrl+Z=undo  Ctrl+O=open  Esc=stop", "dim")
        self.log_msg(
            "ETIQUETA → INICIO_BLOQUE → contenido → FIN_BLOQUE", "block")
        if PROMPT_TEXT.startswith("Error:"):
            self.log_msg(PROMPT_TEXT, "err")
        self.log_msg("")
        self.root.mainloop()
