import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sekibanki import TraceRecorder


def fake_order_lookup(order_id: str) -> dict[str, str]:
    return {"order_id": order_id, "status": "shipped", "eta": "Friday"}


with TraceRecorder("support-agent", metadata={"example": True}) as trace:
    with trace.span("plan", input={"question": "Where is my order A-17?"}) as plan:
        plan.set_output({"action": "lookup_order", "order_id": "A-17"})

    with trace.span("lookup_order", kind="tool", input={"order_id": "A-17"}) as tool:
        tool.set_output(fake_order_lookup("A-17"))

    trace.log("answer", output="Your order A-17 has shipped and should arrive Friday.")

print(f"Trace saved to {trace.path}")
