"""File watcher that monitors .env files for changes and re-audits automatically."""

import time
import os
from pathlib import Path
from typing import Callable, Optional

from envguard.loader import load_env_file
from envguard.auditor import AuditReport
from envguard.schema import EnvSchema
from envguard.auditor import audit


class EnvFileWatcher:
    """Watches a .env file for modifications and triggers re-audit on change."""

    def __init__(
        self,
        env_path: str,
        schema: EnvSchema,
        on_change: Optional[Callable[[AuditReport], None]] = None,
        poll_interval: float = 1.0,
    ):
        self.env_path = Path(env_path)
        self.schema = schema
        self.on_change = on_change or self._default_handler
        self.poll_interval = poll_interval
        self._last_mtime: Optional[float] = None
        self._running = False

    def _default_handler(self, report: AuditReport) -> None:
        status = "PASSED" if report.passed else "FAILED"
        print(f"[envguard] Re-audit {status}: {len(report.errors())} error(s), {len(report.warnings())} warning(s)")

    def _get_mtime(self) -> Optional[float]:
        try:
            return os.path.getmtime(self.env_path)
        except FileNotFoundError:
            return None

    def _check_and_audit(self) -> bool:
        """Returns True if a change was detected and audit was triggered."""
        mtime = self._get_mtime()
        if mtime != self._last_mtime:
            self._last_mtime = mtime
            if mtime is not None:
                env_vars = load_env_file(str(self.env_path))
                report = audit(env_vars, self.schema)
                self.on_change(report)
            return True
        return False

    def start(self, max_iterations: Optional[int] = None) -> None:
        """Start polling loop. If max_iterations is set, stop after N checks (for testing)."""
        self._running = True
        self._last_mtime = None
        iterations = 0
        try:
            while self._running:
                self._check_and_audit()
                iterations += 1
                if max_iterations is not None and iterations >= max_iterations:
                    break
                time.sleep(self.poll_interval)
        except KeyboardInterrupt:
            pass
        finally:
            self._running = False

    def stop(self) -> None:
        self._running = False
