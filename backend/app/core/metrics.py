"""
backend/app/core/metrics.py

Production Real-Time Observability & Metrics Collector.
Collects actual runtime performance measurements (latencies, counts, errors).
Does NOT fabricate metrics or dummy statistics.
"""

from __future__ import annotations

import time
import threading
from typing import Any, Dict, List, Optional


class MetricsCollector:
    """
    Thread-safe runtime performance metrics collector.
    Stores aggregated actual timings and counts in memory.
    """
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.reset()

    def reset(self) -> None:
        with self._lock:
            self._request_count: int = 0
            self._total_api_latency_ms: float = 0.0
            self._db_query_count: int = 0
            self._total_db_latency_ms: float = 0.0
            self._ml_inference_count: int = 0
            self._total_ml_latency_ms: float = 0.0
            self._embedding_count: int = 0
            self._total_embedding_latency_ms: float = 0.0
            self._llm_count: int = 0
            self._total_llm_latency_ms: float = 0.0
            self._pdf_count: int = 0
            self._total_pdf_latency_ms: float = 0.0
            self._error_counts: Dict[int, int] = {}
            self._start_time: float = time.time()

    def record_request(self, method: str, path: str, status_code: int, duration_ms: float) -> None:
        with self._lock:
            self._request_count += 1
            self._total_api_latency_ms += duration_ms
            if status_code >= 400:
                self._error_counts[status_code] = self._error_counts.get(status_code, 0) + 1

    def record_db_latency(self, duration_ms: float) -> None:
        with self._lock:
            self._db_query_count += 1
            self._total_db_latency_ms += duration_ms

    def record_ml_inference(self, duration_ms: float) -> None:
        with self._lock:
            self._ml_inference_count += 1
            self._total_ml_latency_ms += duration_ms

    def record_embedding_latency(self, duration_ms: float) -> None:
        with self._lock:
            self._embedding_count += 1
            self._total_embedding_latency_ms += duration_ms

    def record_llm_latency(self, duration_ms: float) -> None:
        with self._lock:
            self._llm_count += 1
            self._total_llm_latency_ms += duration_ms

    def record_pdf_extraction(self, duration_ms: float) -> None:
        with self._lock:
            self._pdf_count += 1
            self._total_pdf_latency_ms += duration_ms

    def get_summary(self) -> Dict[str, Any]:
        with self._lock:
            uptime_seconds = round(time.time() - self._start_time, 2)
            if self._request_count == 0 and self._ml_inference_count == 0 and self._embedding_count == 0:
                return {
                    "uptime_seconds": uptime_seconds,
                    "total_requests": 0,
                    "status": "No runtime data available",
                }

            avg_api_latency = round(self._total_api_latency_ms / self._request_count, 2) if self._request_count > 0 else 0.0
            avg_db_latency = round(self._total_db_latency_ms / self._db_query_count, 2) if self._db_query_count > 0 else 0.0
            avg_ml_latency = round(self._total_ml_latency_ms / self._ml_inference_count, 2) if self._ml_inference_count > 0 else 0.0
            avg_embed_latency = round(self._total_embedding_latency_ms / self._embedding_count, 2) if self._embedding_count > 0 else 0.0
            avg_llm_latency = round(self._total_llm_latency_ms / self._llm_count, 2) if self._llm_count > 0 else 0.0
            avg_pdf_latency = round(self._total_pdf_latency_ms / self._pdf_count, 2) if self._pdf_count > 0 else 0.0

            return {
                "uptime_seconds": uptime_seconds,
                "total_requests": self._request_count,
                "avg_api_latency_ms": avg_api_latency,
                "avg_db_latency_ms": avg_db_latency,
                "avg_ml_latency_ms": avg_ml_latency,
                "avg_embedding_latency_ms": avg_embed_latency,
                "avg_llm_latency_ms": avg_llm_latency,
                "avg_pdf_extraction_latency_ms": avg_pdf_latency,
                "error_counts": dict(self._error_counts),
            }


# Singleton metrics collector instance
metrics_collector = MetricsCollector()
