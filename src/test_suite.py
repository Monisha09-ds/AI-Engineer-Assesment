import unittest
from processor import DocProcessor
from vector_store import VectorStoreManager
from feedback import FeedbackLoop

class TestLegalAI(unittest.TestCase):
    def test_processor_mock(self):
        # This test checks if the processor class can be initialized
        # (Running full process() requires heavy dependencies)
        processor = DocProcessor()
        self.assertIsNotNone(processor.converter)

    def test_vector_store_logic(self):
        manager = VectorStoreManager(index_path="test_faiss_index")
        class MockDoc:
            content = "This is a test document."
            metadata = {"source": "test.txt"}
            file_path = "test.txt"
            
        manager.add_documents([MockDoc()])
        results = manager.search("test")
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0].metadata["source"], "test.txt")

    def test_feedback_learning(self):
        # We need a mock LLM for this or just test memory logic
        loop = FeedbackLoop(memory_path="data/test_memory.json")
        loop.memory = [{"type": "fact", "insight": "The date is 2026", "source_query": "date"}]
        insights = loop.get_relevant_insights("What is the date?")
        self.assertIn("2026", insights)

if __name__ == "__main__":
    unittest.main()
