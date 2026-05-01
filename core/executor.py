import os
from core.cmd   import is_interactive, normalize_create_cmd, run_cmd_sep, run_cmd_inline
from core.files import FileManager


class Executor:
    def __init__(self, fm: FileManager, pm, log, cmd_sep_fn, stop_fn, skip_fn):
        self.fm         = fm
        self.pm         = pm
        self.log        = log
        self.cmd_sep_fn = cmd_sep_fn
        self.stop_fn    = stop_fn
        self.skip_fn    = skip_fn

    def run(self, project: str, instructions: list,
            dry_run: bool, on_progress, on_done):
        total  = len(instructions)
        ok = err = skip = 0

        self.log("")
        self.log("=" * 50, "dim")
        self.log("DRY-RUN" if dry_run else "EXECUTING", "head")
        self.log("=" * 50, "dim")

        for i, inst in enumerate(instructions, 1):
            if self.stop_fn():
                self.log(f"STOPPED at [{i}/{total}]", "err")
                break

            action = inst["action"]
            on_progress(i, total, action)
            self.log(f"--- [{i}/{total}] {action} ---", "dim")

            try:
                if dry_run:
                    if action == "EJECUTAR":
                        self.log(
                            f"  [DRY] Would execute: "
                            f"{inst['content'].replace(chr(10), ' | ')[:60]}...", "dry")
                    else:
                        self.log(f"  [DRY] Would {action}: {inst['filepath']}", "dry")
                    ok += 1
                    continue

                if action == "EJECUTAR":
                    self._exec(project, inst["content"])
                elif action in ("CREAR", "MODIFICAR"):
                    self.fm.backup(os.path.join(
                        project, inst["filepath"].replace("/", os.sep)))
                    self.fm.create(project, inst)
                elif action == "ELIMINAR":
                    self.fm.backup(os.path.join(
                        project, inst["filepath"].replace("/", os.sep)))
                    self.fm.delete(project, inst)
                elif action == "REEMPLAZAR":
                    self.fm.backup(os.path.join(
                        project, inst["filepath"].replace("/", os.sep)))
                    self.fm.replace(project, inst)
                else:
                    self.log(f"  Unknown action: {action}", "warn")
                    continue

                if self.skip_fn():
                    skip += 1
                else:
                    ok += 1

            except Exception as e:
                err += 1
                self.log(f"  ERROR: {e}", "err")

        self.log("")
        self.log("=" * 50, "dim")
        self.log(f"OK:{ok} ERR:{err} SKIP:{skip} TOTAL:{total}", "head")
        self.log("=" * 50, "dim")

        on_done(ok, err, skip, self.stop_fn())

    def _exec(self, project: str, commands: str):
        lines = [l.strip() for l in commands.strip().split("\n")
                 if l.strip() and not l.strip().startswith("#")]

        for cmd in lines:
            if self.stop_fn():
                self.log(f"  STOP: {cmd}", "err")
                break
            if self.skip_fn():
                self.log(f"  SKIP: {cmd}", "warn")
                continue

            cmd = normalize_create_cmd(cmd)

            if self.cmd_sep_fn() and is_interactive(cmd):
                run_cmd_sep(cmd, project, self.pm, self.log,
                            self.stop_fn, self.skip_fn)
            else:
                run_cmd_inline(cmd, project, self.pm, self.log,
                               self.stop_fn, self.skip_fn)
