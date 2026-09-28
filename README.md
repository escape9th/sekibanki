# SekiBanki

**Replayable traces for AI agents.**

SekiBanki turns a black-box agent run into a local, searchable timeline. Add a few `with` blocks, run your agent as usual, then open the trace in a browser and see every model call, tool call, input, output, duration, and error.

- Local-first: traces stay as plain JSON on your machine.
- Zero runtime dependencies: Python standard library only.
- Framework-agnostic: works with any Python agent, SDK, or custom loop.
- Nested spans: model calls, tools, retrieval, planning, and custom steps.
- Shareable artifacts: one trace is one portable JSON file.

## Quick start

```bash
git clone https://github.com/escape9th/sekibanki.git
cd sekibanki
python -m pip install -e .
```

Record a run:

```python
from sekibanki import TraceRecorder

with TraceRecorder("support-agent") as trace:
    with trace.span("plan", input={"question": "Where is my order?"}) as plan:
        plan.set_output({"next": "lookup_order"})

    with trace.span("lookup_order", kind="tool", input={"order_id": "A-17"}) as tool:
        tool.set_output({"status": "shipped", "eta": "Friday"})

print(f"Saved to {trace.path}")
```

Open the local viewer:

```bash
sekibanki serve
```

Then visit <http://127.0.0.1:8765>. The viewer reads `.sekibanki/*.json` and updates each time you refresh the page.

## Capture model and tool calls

Use `span` around any operation. Inputs and outputs can be dictionaries, lists, strings, numbers, or any JSON-serializable value. Non-serializable values are represented by `repr()` so a debugging run does not fail just because an object is unusual.

```python
with TraceRecorder("research-agent", metadata={"environment": "local"}) as trace:
    with trace.span("call_model", kind="llm", input=messages) as model:
        response = client.responses.create(input=messages)
        model.set_output(response.output_text)
        model.set_metadata(model="gpt-4.1-mini")

    with trace.span("search", kind="tool", input={"query": response.output_text}) as search:
        search.set_output(search_docs(response.output_text))
```

For one-off events:

```python
trace.log("cache_hit", output={"key": "A-17"}, metadata={"layer": "redis"})
```

If a span raises, SekiBanki records the exception type, message, traceback, duration, and marks both the span and run as `failed`, then re-raises the original exception.

## CLI options

```text
sekibanki serve [--directory .sekibanki] [--host 127.0.0.1] [--port 8765]
```

The server is intentionally bound to `127.0.0.1` by default. Use `--host 0.0.0.0` only when you understand that the trace viewer may become reachable from your network.

## Why SekiBanki?

Agent frameworks are getting easier to build, but their failures are still hard to explain. Logs show lines; SekiBanki shows the run as a timeline. It is small enough to drop into an existing project, transparent enough to trust, and structured enough to become a useful artifact in a bug report.

The first release focuses on one job: **make one agent run understandable**. Future compatibility can be added without changing the portable trace format.

## Development

```bash
python -m unittest discover -s tests -v
```

The project intentionally uses the Python standard library for the first release, so there is no dependency installation required to run the tests.

## License

MIT. See [LICENSE](LICENSE).
