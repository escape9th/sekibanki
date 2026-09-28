from __future__ import annotations

import json
import time
import traceback
import uuid
from pathlib import Path
from typing import Any

from .model import Trace, TraceEvent, utc_now


def _json_safe(value: Any) -> Any:
    try:
        json.dumps(value)
        return value
    except (TypeError, ValueError):
        return repr(value)


class Span:
    def __init__(self, recorder: "TraceRecorder", event: TraceEvent):
        self.recorder = recorder
        self.event = event
        self._started = time.perf_counter()

    def __enter__(self) -> "Span":
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback) -> bool:
        if exc_value is not None:
            self.event.status = "failed"
            self.event.error = {
                "type": type(exc_value).__name__,
                "message": str(exc_value),
                "traceback": "".join(traceback.format_exception(exc_type, exc_value, exc_traceback)),
            }
            self.recorder._failed = True
        else:
            self.event.status = "completed"
        self.event.finished_at = utc_now()
        self.event.duration_ms = round((time.perf_counter() - self._started) * 1000, 3)
        self.recorder._stack.pop()
        return False

    def set_output(self, output: Any) -> None:
        self.event.output = _json_safe(output)

    def set_input(self, value: Any) -> None:
        self.event.input = _json_safe(value)

    def set_metadata(self, **metadata: Any) -> None:
        self.event.metadata.update({key: _json_safe(value) for key, value in metadata.items()})


class TraceRecorder:
    def __init__(self, name: str, output_dir: str | Path = ".sekibanki", metadata: dict[str, Any] | None = None):
        self.name = name
        self.output_dir = Path(output_dir)
        self.metadata = metadata or {}
        self.id = uuid.uuid4().hex[:12]
        self.path: Path = self.output_dir / f"{self.id}.json"
        self.events: list[TraceEvent] = []
        self._stack: list[TraceEvent] = []
        self._started = time.perf_counter()
        self._started_at = utc_now()
        self._failed = False

    def __enter__(self) -> "TraceRecorder":
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback) -> bool:
        if exc_value is not None:
            self._failed = True
            if self._stack:
                event = self._stack[-1]
                event.status = "failed"
                event.error = {
                    "type": type(exc_value).__name__,
                    "message": str(exc_value),
                    "traceback": "".join(traceback.format_exception(exc_type, exc_value, exc_traceback)),
                }
                event.finished_at = utc_now()
                event.duration_ms = round((time.perf_counter() - event._started) * 1000, 3) if hasattr(event, "_started") else None
                self._stack.clear()
        trace = Trace(
            id=self.id,
            name=self.name,
            status="failed" if self._failed else "completed",
            started_at=self._started_at,
            finished_at=utc_now(),
            duration_ms=round((time.perf_counter() - self._started) * 1000, 3),
            events=self.events,
            metadata={key: _json_safe(value) for key, value in self.metadata.items()},
        )
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.output_dir / f"{self.id}.json"
        self.path.write_text(json.dumps(trace.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return False

    def span(self, name: str, *, kind: str = "span", input: Any = None, metadata: dict[str, Any] | None = None) -> Span:
        parent = self._stack[-1] if self._stack else None
        event = TraceEvent(
            id=uuid.uuid4().hex[:12],
            name=name,
            kind=kind,
            input=_json_safe(input),
            metadata={key: _json_safe(value) for key, value in (metadata or {}).items()},
            parent_id=parent.id if parent else None,
        )
        self.events.append(event)
        if parent:
            parent.children.append(event.id)
        event._started = time.perf_counter()
        self._stack.append(event)
        return Span(self, event)

    def log(self, name: str, *, output: Any = None, input: Any = None, kind: str = "log", metadata: dict[str, Any] | None = None) -> TraceEvent:
        with self.span(name, kind=kind, input=input, metadata=metadata) as event:
            event.set_output(output)
            return event.event
