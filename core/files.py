import os
import shutil
import time


class FileManager:
    def __init__(self, temp_dir: str, backup_enabled_fn, undo_stack: list, log):
        self.temp_dir          = temp_dir
        self.backup_enabled_fn = backup_enabled_fn
        self.undo_stack        = undo_stack
        self.log               = log

    def backup(self, filepath: str):
        if not self.backup_enabled_fn() or not os.path.exists(filepath):
            return
        bdir = os.path.join(self.temp_dir, "backups")
        os.makedirs(bdir, exist_ok=True)
        ts  = int(time.time() * 1000)
        dst = os.path.join(bdir, f"{ts}_{os.path.basename(filepath)}")
        shutil.copy2(filepath, dst)
        self.undo_stack.append({"original": filepath, "backup": dst})
        if len(self.undo_stack) > 50:
            self.undo_stack.pop(0)

    def undo_last(self):
        if not self.undo_stack:
            self.log("UNDO: nothing to undo", "warn")
            return
        entry = self.undo_stack.pop()
        try:
            shutil.copy2(entry["backup"], entry["original"])
            self.log(f"UNDO: restored {os.path.basename(entry['original'])}", "undo")
        except Exception as e:
            self.log(f"UNDO ERROR: {e}", "err")

    def create(self, project: str, inst: dict):
        filepath = inst["filepath"]
        content  = inst["content"]
        full     = os.path.join(project, filepath.replace("/", os.sep))
        dir_path = os.path.dirname(full)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(content + "\n")
        n   = content.count("\n") + 1
        act = "NEW" if inst["action"] == "CREAR" else "MOD"
        self.log(f"  {act}: {filepath} ({n}L)", "ok")

    def delete(self, project: str, inst: dict):
        filepath = inst["filepath"]
        full     = os.path.join(project, filepath.replace("/", os.sep))
        if os.path.exists(full):
            os.remove(full)
            self.log(f"  DEL: {filepath}", "warn")
        else:
            self.log(f"  NOT FOUND: {filepath}", "warn")

    def replace(self, project: str, inst: dict):
        filepath = inst["filepath"]
        content  = inst["content"]
        full     = os.path.join(project, filepath.replace("/", os.sep))

        if not os.path.exists(full):
            self.log(f"  REPL ERR: not found → {filepath}", "err")
            return
        if ">>>" not in content:
            self.log("  REPL ERR: missing >>> separator", "err")
            return

        parts   = content.split(">>>", 1)
        search  = parts[0].rstrip("\n")
        replace = parts[1].lstrip("\n")

        if not search.strip():
            self.log("  REPL ERR: empty search text", "err")
            return

        with open(full, "r", encoding="utf-8") as f:
            fc = f.read()

        # 🐱 intento 1: exacto
        if search in fc:
            self._write(full, fc.replace(search, replace, 1), filepath, search, replace)
            return

        # 🐱 intento 2: normalizar tabs
        def norm(t): return t.replace("\t", "    ")
        nfc = norm(fc)
        nsr = norm(search)
        if nsr in nfc:
            self._write(full, nfc.replace(nsr, replace, 1), filepath, search, replace)
            return

        # 🐱 intento 3: línea por línea
        sl      = [l.strip() for l in search.split("\n") if l.strip()]
        fc_lines = fc.split("\n")
        if not sl:
            self.log("  REPL ERR: empty search", "err")
            return

        found = False
        for si in range(len(fc_lines)):
            if fc_lines[si].strip() != sl[0]:
                continue
            if len(sl) == 1:
                fc_lines = fc_lines[:si] + replace.split("\n") + fc_lines[si+1:]
                found = True
                break
            match = True
            fi = si
            for s in sl:
                while fi < len(fc_lines) and fc_lines[fi].strip() == "" and s != "":
                    fi += 1
                if fi >= len(fc_lines) or fc_lines[fi].strip() != s:
                    match = False
                    break
                fi += 1
            if match:
                fc_lines = fc_lines[:si] + replace.split("\n") + fc_lines[fi:]
                found = True
                break

        if found:
            self._write(full, "\n".join(fc_lines), filepath, search, replace)
            return

        # 🐱 intento 4: parcial una línea
        if len(sl) == 1:
            for idx, line in enumerate(fc_lines):
                ls = line.strip()
                if len(sl[0]) >= 5 and len(ls) >= 5 and (sl[0] in ls or ls in sl[0]):
                    fc_lines = fc_lines[:idx] + replace.split("\n") + fc_lines[idx+1:]
                    self._write(full, "\n".join(fc_lines), filepath, search, replace)
                    self.log("    (partial match)", "warn")
                    return

        self.log(f"  REPL ERR: not found in {filepath}", "err")
        self.log(f"    search: {search.split(chr(10))[0][:60]}...", "dim")

    def _write(self, full, content, filepath, search, replace):
        with open(full, "w", encoding="utf-8") as f:
            f.write(content)
        self.log(f"  REPL: {filepath}", "replace")
        self.log(f"    - {search.split(chr(10))[0][:50]}", "dim")
        self.log(f"    + {replace.split(chr(10))[0][:50]}", "ok")
