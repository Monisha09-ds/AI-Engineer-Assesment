import tempfile
import unittest
from pathlib import Path

from vector_store import VectorStoreManager


class MockDocument:
    content = "This is a test document."
    metadata = {"source": "test.txt"}
    file_path = "test.txt"


class TestVectorStoreIntegration(unittest.TestCase):
    def test_document_can_be_indexed_and_retrieved(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            index_path = Path(temp_dir) / "faiss_index"
            manager = VectorStoreManager(index_path=str(index_path))

            manager.add_documents([MockDocument()])
            results = manager.search("test")

        self.assertGreater(len(results), 0)
        self.assertEqual(results[0].metadata["source"], "test.txt")


if __name__ == "__main__":
    unittest.main()
