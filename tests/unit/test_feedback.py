import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("MODEL_PROVIDER", "mock")

from feedback import FeedbackLoop


class TestFeedbackLoop(unittest.TestCase):
    def test_relevant_insights_returns_matching_memory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            memory_path = Path(temp_dir) / "memory.json"
            loop = FeedbackLoop(memory_path=str(memory_path))
            loop.memory = [
                {"type": "fact", "insight": "The date is 2026", "source_query": "date"}
            ]

            insights = loop.get_relevant_insights("What is the date?")

        self.assertIn("2026", insights)


if __name__ == "__main__":
    unittest.main()
