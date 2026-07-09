from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from vibespec_gate.core.risk_model import Finding, ProjectProfile


class ToolAdapter:
    name = "tool"
    executable = ""

    def is_available(self) -> bool:
        return bool(shutil.which(self.executable))

    def scan(self, root: Path, profile: ProjectProfile) -> list[Finding]:
        return []

    def run_json(self, args: list[str], timeout: int = 120) -> Any:
        completed = subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
        if not completed.stdout.strip():
            return None
        return json.loads(completed.stdout)
