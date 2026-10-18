import tempfile
import unittest
from unittest.mock import patch

from app.services.embedding_service import EmbeddingConfig, EmbeddingService


class EmbeddingServiceTest(unittest.TestCase):
    def make_service(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".sqlite3")
        return EmbeddingService(EmbeddingConfig(
            base_url="https://example.invalid",
            api_key="test-only",
            model="test-model",
            batch_size=2,
            concurrency=2,
            cache_path=self.tmp.name,
        ))

    def test_batches_preserve_order_and_cache(self):
        service = self.make_service()
        calls = []

        def fake_batch(texts):
            calls.append(list(texts))
            return [[float(len(text))] for text in texts]

        with patch.object(service, "_request_batch", side_effect=fake_batch):
            vectors, requests = service.embed(["a", "bb", "ccc"])
            cached_vectors, cached_requests = service.embed(["a", "bb", "ccc"])

        self.assertEqual(vectors, [[1.0], [2.0], [3.0]])
        self.assertEqual(cached_vectors, vectors)
        self.assertEqual(requests, 2)
        self.assertEqual(cached_requests, 0)
        self.assertEqual(len(calls), 2)

    def test_empty_input(self):
        service = self.make_service()
        self.assertEqual(service.embed([]), ([], 0))


if __name__ == "__main__":
    unittest.main()
