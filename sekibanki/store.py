from __future__ import annotations

import json
from pathlib import Path

from .model import Trace


def load_trace(path: str | Path) -> Trace:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return Trace.from_dict(payload)


def list_traces(directory: str | Path = ".sekibanki") -> list[Trace]:
    traces = [load_trace(path) for path in Path(directory).glob("*.json")]
    return sorted(traces, key=lambda trace: trace.started_at, reverse=True)
