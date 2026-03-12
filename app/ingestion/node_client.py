from __future__ import annotations

import json
import os
import shutil
import subprocess
from datetime import date
from pathlib import Path

import pandas as pd

from app.config import get_settings
from app.ingestion.clients import BaseGarminClient, FetchResult


class GarminNodeClient(BaseGarminClient):
    def __init__(self, command: str | None = None) -> None:
        self.settings = get_settings()
        self.command = command or self.settings.garmin_node_command
        self.bridge_script = self.settings.root_dir / "scripts" / "node" / "garmin_bridge.cjs"

    def fetch(self, start_date: date, end_date: date, save_raw: bool = True) -> FetchResult:
        del save_raw
        executable = self._resolve_node_command()
        command = [
            executable,
            str(self.bridge_script),
            "--start",
            start_date.isoformat(),
            "--end",
            end_date.isoformat(),
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            message = result.stderr.strip() or result.stdout.strip() or "unknown node bridge error"
            raise RuntimeError(f"Node bridge failed: {message}")

        stdout = result.stdout.strip()
        if not stdout:
            message = result.stderr.strip() or "Node bridge returned empty stdout."
            raise RuntimeError(f"Node bridge produced no JSON output: {message}")

        payload = self._parse_json_output(stdout, result.stderr.strip())
        data = {name: pd.DataFrame(rows) for name, rows in payload["data"].items()}
        return FetchResult(data=data, raw_payload_paths={}, source="garmin_node")

    def _resolve_node_command(self) -> str:
        candidates = [self.command]

        which_match = shutil.which(self.command)
        if which_match:
            candidates.append(which_match)

        program_files = os.environ.get("ProgramFiles")
        local_app_data = os.environ.get("LOCALAPPDATA")
        if program_files:
            candidates.append(str(Path(program_files) / "nodejs" / "node.exe"))
        if local_app_data:
            candidates.append(str(Path(local_app_data) / "Programs" / "nodejs" / "node.exe"))

        for candidate in candidates:
            if candidate and Path(candidate).exists():
                return str(Path(candidate))

        if shutil.which(self.command):
            return str(shutil.which(self.command))

        raise RuntimeError(
            "No se encontro node.exe. Configura GARMIN_NODE_COMMAND con la ruta completa, por ejemplo C:/Program Files/nodejs/node.exe."
        )

    @staticmethod
    def _parse_json_output(stdout: str, stderr: str) -> dict:
        try:
            return json.loads(stdout)
        except json.JSONDecodeError:
            lines = [line.strip() for line in stdout.splitlines() if line.strip()]
            for line in reversed(lines):
                if line.startswith("{") and line.endswith("}"):
                    try:
                        return json.loads(line)
                    except json.JSONDecodeError:
                        continue
            detail = stderr or stdout[:1000]
            raise RuntimeError(f"Node bridge returned non-JSON output: {detail}")
