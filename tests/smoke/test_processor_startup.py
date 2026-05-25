import unittest

from processor import DocProcessor


class TestProcessorStartup(unittest.TestCase):
    def test_processor_can_initialize_converter(self):
        processor = DocProcessor()

        self.assertIsNotNone(processor.converter)


if __name__ == "__main__":
    unittest.main()
