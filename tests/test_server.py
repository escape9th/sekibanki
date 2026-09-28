import json
import tempfile
import unittest
from pathlib import Path
from urllib.request import urlopen

from sekibanki import TraceRecorder
from sekibanki.server import create_handler
from http.server import ThreadingHTTPServer
from threading import Thread


class ServerTests(unittest.TestCase):
    def test_serves_trace_list_and_viewer(self):
        with tempfile.TemporaryDirectory() as directory:
            with TraceRecorder("api-check", output_dir=directory):
                pass
            server = ThreadingHTTPServer(("127.0.0.1", 0), create_handler(Path(directory)))
            thread = Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                base = f"http://127.0.0.1:{server.server_port}"
                with urlopen(base + "/") as response:
                    self.assertIn(b"SekiBanki", response.read())
                with urlopen(base + "/api/traces") as response:
                    payload = json.load(response)
                self.assertEqual(payload[0]["name"], "api-check")
            finally:
                server.shutdown()
                thread.join(timeout=2)
                server.server_close()


if __name__ == "__main__":
    unittest.main()
