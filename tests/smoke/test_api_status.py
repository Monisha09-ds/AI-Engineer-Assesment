import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from langchain_core.embeddings import Embeddings

os.environ["MODEL_PROVIDER"] = "mock"


class StubEmbeddings(Embeddings):
    def embed_documents(self, texts):
        return [[0.0] for _ in texts]

    def embed_query(self, text):
        return [0.0]


with patch("vector_store.HuggingFaceEmbeddings", return_value=StubEmbeddings()):
    from api import app, vector_store


class TestApiStatus(unittest.TestCase):
    def test_status_endpoint_is_reachable(self):
        client = TestClient(app)

        with patch.object(vector_store, "load_index", return_value=False):
            response = client.get("/api/status")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("status"), "ok")


if __name__ == "__main__":
    unittest.main()
