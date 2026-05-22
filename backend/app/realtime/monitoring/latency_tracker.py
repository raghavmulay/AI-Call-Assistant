"""
latency_tracker.py — Per-session WebSocket transport latency recorder.
"""
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, Deque


@dataclass
class LatencyStats:
    samples: Deque[float] = field(default_factory=lambda: deque(maxlen=100))

    def record(self, ms: float):
        self.samples.append(ms)

    @property
    def avg(self) -> float:
        return sum(self.samples) / len(self.samples) if self.samples else 0.0

    @property
    def min(self) -> float:
        return min(self.samples) if self.samples else 0.0

    @property
    def max(self) -> float:
        return max(self.samples) if self.samples else 0.0

    def summary(self) -> dict:
        return {"avg_ms": round(self.avg, 2), "min_ms": round(self.min, 2), "max_ms": round(self.max, 2), "samples": len(self.samples)}


class LatencyTracker:
    def __init__(self):
        self._stats: Dict[str, LatencyStats] = defaultdict(LatencyStats)

    def record(self, session_id: str, latency_ms: float):
        self._stats[session_id].record(latency_ms)

    def get_stats(self, session_id: str) -> dict:
        return self._stats[session_id].summary()

    def remove(self, session_id: str):
        self._stats.pop(session_id, None)


latency_tracker = LatencyTracker()
