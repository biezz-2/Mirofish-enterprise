import os
import tempfile
import time
import unittest
from unittest.mock import MagicMock, patch
from urllib import error

from app.services.embedding_service import (
    EmbeddingConfig,
    EmbeddingService,
    configured_embedding_service,
)


class EmbeddingServiceTest(unittest.TestCase):
    def make_service(self, with_fallback: bool = False):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".sqlite3")
        return EmbeddingService(EmbeddingConfig(
            base_url="https://9router.biezz.my.id",
            api_key="test-primary-key",
            model="bge-m3/bge-m3",
            dimensions=1024,
            batch_size=2,
            concurrency=2,
            timeout_seconds=5.0,
            max_retries=1,
            cache_path=self.tmp.name,
            fallback_base_url="http://192.168.101.19:20128" if with_fallback else None,
            fallback_api_key="test-fallback-key" if with_fallback else None,
            fallback_model="bge-m3/bge-m3" if with_fallback else None,
            fallback_dimensions=1024 if with_fallback else None,
            fallback_timeout_seconds=5.0,
            cooldown_seconds=10.0,
        ))

    def test_batches_preserve_order_and_cache(self):
        service = self.make_service()
        calls = []

        def fake_batch(texts):
            calls.append(list(texts))
            return [[float(len(text))] for text in texts], "bge-m3/bge-m3"

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

    def test_primary_tpu_priority_and_dimensions(self):
        service = self.make_service(with_fallback=True)

        with patch.object(service, "_execute_http_batch") as mock_http:
            mock_http.return_value = [[0.1] * 1024, [0.2] * 1024]
            vectors, model = service._request_batch(["alpha", "beta"])

            self.assertEqual(len(vectors), 2)
            self.assertEqual(len(vectors[0]), 1024)
            self.assertEqual(model, "bge-m3/bge-m3")
            mock_http.assert_called_once_with(
                base_url="https://9router.biezz.my.id",
                api_key="test-primary-key",
                model="bge-m3/bge-m3",
                dimensions=1024,
                timeout_seconds=5.0,
                texts=["alpha", "beta"],
            )
            self.assertTrue(service.is_primary_healthy())

    def test_failover_to_fallback_when_primary_502_offline(self):
        service = self.make_service(with_fallback=True)

        def side_effect(base_url, api_key, model, dimensions, timeout_seconds, texts):
            if "9router" in base_url:
                raise error.HTTPError(
                    url="https://9router.biezz.my.id/v1/embeddings",
                    code=502,
                    msg="Bad Gateway",
                    hdrs=MagicMock(),
                    fp=None,
                )
            # Fallback succeeds
            return [[0.9] * 1024 for _ in texts]

        with patch.object(service, "_execute_http_batch", side_effect=side_effect) as mock_http:
            vectors, used_model = service._request_batch(["hello", "world"])

            self.assertEqual(len(vectors), 2)
            self.assertEqual(used_model, "bge-m3/bge-m3")
            # Verify primary was tried and then fallback was called
            self.assertFalse(service.is_primary_healthy())
            self.assertEqual(mock_http.call_count, 3)  # primary try + retry, then fallback

    def test_circuit_breaker_cooldown_routes_direct_to_fallback(self):
        service = self.make_service(with_fallback=True)
        service.mark_primary_unhealthy(duration=60.0)
        self.assertFalse(service.is_primary_healthy())

        with patch.object(service, "_execute_http_batch") as mock_http:
            mock_http.return_value = [[0.5] * 1024]
            vectors, used_model = service._request_batch(["test text"])

            self.assertEqual(vectors, [[0.5] * 1024])
            self.assertEqual(used_model, "bge-m3/bge-m3")
            # Primary was NOT called because it is in cooldown
            mock_http.assert_called_once_with(
                base_url="http://192.168.101.19:20128",
                api_key="test-fallback-key",
                model="bge-m3/bge-m3",
                dimensions=1024,
                timeout_seconds=5.0,
                texts=["test text"],
            )

    def test_both_endpoints_fail_raises_runtime_error(self):
        service = self.make_service(with_fallback=True)

        with patch.object(service, "_execute_http_batch", side_effect=TimeoutError("Connection timed out")):
            with self.assertRaises(RuntimeError) as ctx:
                service._request_batch(["fail test"])
            self.assertIn("Both primary", str(ctx.exception))

    def test_configured_embedding_service_environment_priority(self):
        env_vars = {
            "EMBEDDING_PRIMARY_API_KEY": "sk-primary-tpu-test",
            "EMBEDDING_PRIMARY_BASE_URL": "https://9router.biezz.my.id",
            "EMBEDDING_PRIMARY_MODEL": "bge-m3/bge-m3",
            "EMBEDDING_PRIMARY_DIMENSIONS": "1024",
            "EMBEDDING_FALLBACK_BASE_URL": "http://192.168.101.19:20128",
            "EMBEDDING_FALLBACK_API_KEY": "sk-fallback-test",
            "EMBEDDING_FALLBACK_MODEL": "bge-m3/bge-m3",
            "EMBEDDING_FALLBACK_DIMENSIONS": "1024",
        }
        with patch.dict(os.environ, env_vars, clear=False):
            svc = configured_embedding_service()
            self.assertIsNotNone(svc)
            self.assertEqual(svc.config.base_url, "https://9router.biezz.my.id")
            self.assertEqual(svc.config.api_key, "sk-primary-tpu-test")
            self.assertEqual(svc.config.model, "bge-m3/bge-m3")
            self.assertEqual(svc.config.dimensions, 1024)
            self.assertEqual(svc.config.fallback_base_url, "http://192.168.101.19:20128")
            self.assertEqual(svc.config.fallback_api_key, "sk-fallback-test")
            self.assertEqual(svc.config.fallback_dimensions, 1024)


if __name__ == "__main__":
    unittest.main()
