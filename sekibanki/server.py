from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .store import list_traces, load_trace


INDEX_HTML = r'''<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>SekiBanki</title>
<style>
:root{color-scheme:dark;--bg:#111318;--panel:#1a1d24;--line:#303540;--text:#eef1f5;--muted:#9ba3b1;--accent:#7dd3fc;--red:#fb7185;--green:#86efac}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:14px/1.5 system-ui,-apple-system,Segoe UI,sans-serif}header{border-bottom:1px solid var(--line);padding:20px 28px;display:flex;align-items:end;justify-content:space-between}h1{font-size:24px;margin:0;letter-spacing:.02em}header p{color:var(--muted);margin:4px 0 0}.layout{display:grid;grid-template-columns:290px 1fr;min-height:calc(100vh - 85px)}aside{border-right:1px solid var(--line);padding:18px 14px}input{width:100%;background:#101217;border:1px solid var(--line);border-radius:6px;color:var(--text);padding:10px 11px;outline:none}input:focus{border-color:var(--accent)}.run{padding:13px 12px;border-bottom:1px solid var(--line);cursor:pointer}.run:hover,.run.active{background:#222731}.run strong{display:block;font-weight:600}.run small{color:var(--muted)}.badge{float:right;font-size:11px}.ok{color:var(--green)}.bad{color:var(--red)}main{padding:28px;max-width:1050px;width:100%}.empty{color:var(--muted);padding-top:40px}.summary{display:flex;gap:10px;flex-wrap:wrap;margin:18px 0 26px}.stat{background:var(--panel);border:1px solid var(--line);border-radius:7px;padding:12px 16px;min-width:140px}.stat span{display:block;color:var(--muted);font-size:12px}.stat b{font-size:18px}.timeline{border-left:2px solid #3a4351;padding-left:25px}.event{position:relative;background:var(--panel);border:1px solid var(--line);border-radius:7px;margin:0 0 12px;padding:14px 16px}.event:before{content:"";position:absolute;left:-33px;top:17px;width:12px;height:12px;border-radius:50%;background:var(--accent);box-shadow:0 0 0 4px var(--bg)}.event.failed:before{background:var(--red)}.event.child{margin-left:25px}.event-head{display:flex;justify-content:space-between;gap:12px}.event-name{font-weight:650}.kind{color:var(--accent);font-size:12px}.details{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:12px}.details pre{white-space:pre-wrap;overflow:auto;background:#111318;border-radius:5px;padding:10px;margin:4px 0 0;color:#cbd5e1;font:12px ui-monospace,SFMono-Regular,monospace}.label{color:var(--muted);font-size:12px}@media(max-width:720px){.layout{grid-template-columns:1fr}aside{border-right:0;border-bottom:1px solid var(--line)}.details{grid-template-columns:1fr}main{padding:20px}}
</style></head><body><header><div><h1>SekiBanki</h1><p>Replayable traces for AI agents</p></div><div id="count"></div></header><div class="layout"><aside><input id="search" placeholder="Filter runs..."/><div id="runs"></div></aside><main id="detail"><div class="empty">Select a run to inspect its timeline.</div></main></div>
<script>
const state={runs:[],selected:null};
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const pretty=v=>v===null||v===undefined?'':esc(JSON.stringify(v,null,2));
function renderRuns(){const q=document.querySelector('#search').value.toLowerCase();document.querySelector('#runs').innerHTML=state.runs.filter(r=>r.name.toLowerCase().includes(q)).map(r=>`<div class="run ${state.selected===r.id?'active':''}" onclick="selectRun('${r.id}')"><span class="badge ${r.status==='failed'?'bad':'ok'}">${r.status}</span><strong>${esc(r.name)}</strong><small>${esc(r.started_at)} · ${r.events.length} events</small></div>`).join('');document.querySelector('#count').textContent=`${state.runs.length} runs`}
function renderDetail(r){const events=r.events.map(e=>`<article class="event ${e.status==='failed'?'failed':''} ${e.parent_id?'child':''}"><div class="event-head"><div><span class="event-name">${esc(e.name)}</span> <span class="kind">${esc(e.kind)}</span></div><span class="${e.status==='failed'?'bad':'ok'}">${e.status} · ${e.duration_ms??0} ms</span></div>${e.input!==null||e.output!==null||e.error?`<div class="details"><div><span class="label">Input</span><pre>${pretty(e.input)}</pre></div><div><span class="label">Output${e.error?' / Error':''}</span><pre>${e.error?esc(e.error.message):pretty(e.output)}</pre></div></div>`:''}</article>`).join('');document.querySelector('#detail').innerHTML=`<h2>${esc(r.name)}</h2><div class="summary"><div class="stat"><span>Status</span><b class="${r.status==='failed'?'bad':'ok'}">${r.status}</b></div><div class="stat"><span>Duration</span><b>${r.duration_ms??0} ms</b></div><div class="stat"><span>Events</span><b>${r.events.length}</b></div></div><div class="timeline">${events||'<div class="empty">No events recorded.</div>'}</div>`}
async function selectRun(id){state.selected=id;renderRuns();const r=state.runs.find(x=>x.id===id);renderDetail(r)}
document.querySelector('#search').addEventListener('input',renderRuns);
fetch('/api/traces').then(x=>x.json()).then(x=>{state.runs=x;renderRuns();if(x[0])selectRun(x[0].id)});
</script></body></html>'''


def create_handler(directory: Path):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urlparse(self.path)
            if parsed.path == "/":
                self._send(200, INDEX_HTML.encode(), "text/html; charset=utf-8")
                return
            if parsed.path == "/api/traces":
                payload = [trace.to_dict() for trace in list_traces(directory)]
                self._send(200, json.dumps(payload, ensure_ascii=False).encode(), "application/json")
                return
            if parsed.path.startswith("/api/traces/"):
                trace_id = parsed.path.rsplit("/", 1)[-1]
                match = next((path for path in directory.glob(f"{trace_id}.json")), None)
                if match:
                    self._send(200, match.read_bytes(), "application/json")
                    return
            self._send(404, b"Not found", "text/plain")

        def _send(self, code: int, body: bytes, content_type: str):
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args):
            return

    return Handler


def serve(directory: str | Path = ".sekibanki", host: str = "127.0.0.1", port: int = 8765) -> None:
    data_dir = Path(directory)
    data_dir.mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer((host, port), create_handler(data_dir))
    print(f"SekiBanki is running at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()
