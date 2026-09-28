import tempfile
import unittest

from sekibanki import TraceRecorder
from sekibanki.store import list_traces


class TraceStoreTests(unittest.TestCase):
    def test_lists_saved_traces_newest_first(self):
        with tempfile.TemporaryDirectory() as directory:
            with TraceRecorder("older", output_dir=directory):
                pass
            with TraceRecorder("newer", output_dir=directory):
                pass

            traces = list_traces(directory)

            self.assertEqual([item.name for item in traces], ["newer", "older"])


if __name__ == "__main__":
    unittest.main()
