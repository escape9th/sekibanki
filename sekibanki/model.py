from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class TraceEvent:
    id: str
    name: str
    kind: str = "span"
    status: str = "running"
    started_at: str = field(default_factory=utc_now)
    finished_at: str | None = None
    duration_ms: float | None = None
    input: Any = None
    output: Any = None
    error: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    parent_id: str | None = None
    children: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "TraceEvent":
        return cls(**payload)


@dataclass
class Trace:
    id: str
    name: str
    status: str
    started_at: str
    finished_at: str | None
    duration_ms: float | None
    events: list[TraceEvent]
    metadata: dict[str, Any] = field(default_factory=dict)
    schema_version: int = 1

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["events"] = [event.to_dict() for event in self.events]
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Trace":
        data = dict(payload)
        data["events"] = [TraceEvent.from_dict(item) for item in data.get("events", [])]
        data.pop("schema_version", None)
        return cls(**data)
