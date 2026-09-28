import json
import tempfile
import unittest
from pathlib import Path

from sekibanki import TraceRecorder, load_trace


class TraceRecorderTests(unittest.TestCase):
    def test_records_nested_spans_with_timing_and_status(self):
        with tempfile.TemporaryDirectory() as directory:
            with TraceRecorder("checkout-agent", output_dir=directory) as trace:
                with trace.span("plan", input={"question": "refund"}) as plan:
                    plan.set_output({"action": "lookup_order"})
                    with trace.span("lookup_order", kind="tool") as lookup:
                        lookup.set_output({"order_id": "A-17"})

            saved = load_trace(trace.path)

            self.assertEqual(saved.name, "checkout-agent")
            self.assertEqual(saved.status, "completed")
            self.assertEqual([event.name for event in saved.events], ["plan", "lookup_order"])
            self.assertEqual(saved.events[0].children, [saved.events[1].id])
            self.assertEqual(saved.events[1].kind, "tool")
            self.assertEqual(saved.events[1].output, {"order_id": "A-17"})
            self.assertIsNotNone(saved.events[1].duration_ms)

    def test_marks_failed_span_and_run_when_code_raises(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(RuntimeError, "provider unavailable"):
                with TraceRecorder("broken-agent", output_dir=directory) as trace:
                    with trace.span("call-model"):
                        raise RuntimeError("provider unavailable")

            saved = load_trace(trace.path)

            self.assertEqual(saved.status, "failed")
            self.assertEqual(saved.events[0].status, "failed")
            self.assertEqual(saved.events[0].error["type"], "RuntimeError")
            self.assertEqual(saved.events[0].error["message"], "provider unavailable")

    def test_serialized_file_is_portable_json(self):
        with tempfile.TemporaryDirectory() as directory:
            with TraceRecorder("portable", output_dir=directory) as trace:
                trace.log("answer", output="42", metadata={"model": "local"})

            payload = json.loads(Path(trace.path).read_text(encoding="utf-8"))

            self.assertEqual(payload["schema_version"], 1)
            self.assertEqual(payload["events"][0]["name"], "answer")
            self.assertEqual(payload["events"][0]["metadata"]["model"], "local")


if __name__ == "__main__":
    unittest.main()
