import subprocess
import time
from core.process import ProcessManager


INTERACTIVE_PREFIXES = ("npm ", "npx ", "python", "py ", "node ")


def is_interactive(cmd: str) -> bool:
    c = cmd.lower().strip()
    return any(c.startswith(p) for p in INTERACTIVE_PREFIXES)


def normalize_create_cmd(cmd: str) -> str:
    c = cmd.lower().strip()
    if any(x in c for x in [
        "npm init vite", "npm create vite",
        "npx create-vite", "npx init vite",
    ]):
        template = "react"
        if "--template" in c:
            idx  = c.index("--template")
            rest = cmd[idx + len("--template"):].strip()
            template = rest.split()[0] if rest.split() else "react"
        return f"npx create-vite@latest . --template {template} --yes"

    if "create-next-app" in c:
        if "--yes" not in c and "-y" not in c:
            return cmd + " --yes"

    return cmd


def run_cmd_sep(cmd: str, project: str, pm: ProcessManager,
                log, stop_flag, skip_flag):
    log(f"  [CMD SEP] {cmd}", "interactive")
    try:
        proc = subprocess.Popen(
            f'start /wait cmd /k "'
        f'title KONDOR: {cmd} && '
        f'echo ======================================== && '
        f'echo  KONDOR ejecutando: && '
            f'echo  {cmd} && '
            f'echo ======================================== && echo. && '
            f'cd /d "{project}" && {cmd} && echo. && '
            f'echo ======================================== && '
            f'echo  LISTO - puedes cerrar esta ventana && '
            f'echo ========================================"',
            shell=True, cwd=project)

        pm.set(proc)
        while proc.poll() is None:
            if stop_flag() or skip_flag():
                pm.kill()
                log("  Process killed.", "warn")
                return
            time.sleep(0.2)
        pm.set(None)
        log("  Window closed. Continuing...", "ok")

    except Exception as e:
        log(f"  Error: {e}", "err")
        pm.set(None)


def run_cmd_inline(cmd: str, project: str, pm: ProcessManager,
                   log, stop_flag, skip_flag):
    log(f"  > {cmd}", "cmd")
    try:
        proc = subprocess.Popen(
            cmd, shell=True, cwd=project,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, bufsize=1)

        pm.set(proc)
        out_count = 0

        while True:
            if stop_flag() or skip_flag():
                pm.kill()
                log("    Process killed.", "warn")
                break
            line = proc.stdout.readline()
            if line:
                clean = line.rstrip()
                if clean and out_count < 8:
                    log(f"    {clean}", "info")
                    out_count += 1
            elif proc.poll() is not None:
                break
            else:
                time.sleep(0.05)

        if not skip_flag() and not stop_flag():
            try:
                stderr = proc.stderr.read()
            except Exception:
                stderr = ""
            rc = proc.returncode if proc.returncode is not None else -1
            if rc != 0 and stderr and stderr.strip():
                tag = "warn" if ("warn" in stderr.lower()
                                 or "notice" in stderr.lower()) else "err"
                for ln in stderr.strip().split("\n")[:4]:
                    log(f"    {ln[:100]}", tag)
            log(f"    {'OK' if rc == 0 else f'exit:{rc}'}",
                "ok" if rc == 0 else "warn")

        pm.set(None)

    except Exception as e:
        log(f"    Error: {e}", "err")
        pm.set(None)
