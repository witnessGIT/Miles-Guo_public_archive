import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import agent_entry


class AgentEntryTests(unittest.TestCase):
    def test_new_agent_id_is_unique_and_uses_worker_format(self):
        first = agent_entry.new_agent_id()
        second = agent_entry.new_agent_id()
        self.assertTrue(first.startswith("agent-"))
        self.assertNotEqual(first, second)

    def test_session_reuses_the_same_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            previous = agent_entry.SESSION
            try:
                agent_entry.SESSION = Path(tmp) / ".agent_session.json"
                first = agent_entry.load_or_create_agent_id(None)
                second = agent_entry.load_or_create_agent_id(None)
                saved = json.loads(agent_entry.SESSION.read_text(encoding="utf-8"))
            finally:
                agent_entry.SESSION = previous
        self.assertEqual(first, second)
        self.assertEqual(saved["agent_id"], first)


if __name__ == "__main__":
    unittest.main()
