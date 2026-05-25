import os
import unittest
from unittest.mock import patch

from vector_store import VectorStoreManager


class TestVectorStoreConfiguration(unittest.TestCase):
    @patch("vector_store.HuggingFaceEmbeddings")
    def test_passes_hf_token_to_embedding_model_when_configured(self, embeddings):
        with patch.dict(os.environ, {"HF_TOKEN": "hf_test_token"}, clear=False):
            VectorStoreManager(index_path="unused")

        embeddings.assert_called_once_with(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={"token": "hf_test_token"},
        )


if __name__ == "__main__":
    unittest.main()
