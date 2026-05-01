import threading


class ProcessManager:
    def __init__(self):
        self._lock    = threading.Lock()
        self._process = None

    def set(self, proc):
        with self._lock:
            self._process = proc

    def kill(self):
        with self._lock:
            proc = self._process
            self._process = None
        if proc:
            try:
                proc.kill()
                proc.wait(timeout=3)
            except Exception:
                pass

    @property
    def active(self):
        with self._lock:
            return self._process is not None
