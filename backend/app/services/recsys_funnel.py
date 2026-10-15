"""
MiroFish Enterprise 3-Stage RecSys Funnel Service (Agent 11: Divisi D)
Implementasi Funnel Rekomendasi 3-Tahap:
- Stage 1: Candidate Generation (Graf Homofili & Cosine Similarity)
- Stage 2: Heavy Ranking (Multi-task engagement scoring: Like, RT, Reply)
- Stage 3: Re-Ranking dengan Echo Chamber Damping (0.40 - 0.80) dan Epsilon-Greedy (eps=0.05).
"""

import math
import random
from typing import Dict, Any, List
from pydantic import BaseModel, Field

class FeedItem(BaseModel):
    item_id: str
    author_id: str
    topic: str
    stance: float = 0.0  # -1.0 s.d. +1.0
    base_score: float = 0.5
    final_score: float = 0.0

class RecSysFunnel:
    """3-Stage Enterprise Recommender System."""

    def __init__(self, damping_factor: float = 0.60, epsilon: float = 0.05):
        self.damping_factor = max(0.40, min(0.80, damping_factor))
        self.epsilon = epsilon

    # Stage 1: Candidate Generation
    def stage1_candidates(self, items: List[FeedItem], user_stance: float, limit: int = 50) -> List[FeedItem]:
        scored = []
        for it in items:
            # Homofili: kedekatan pandangan
            stance_diff = abs(it.stance - user_stance)
            homophily = 1.0 - (stance_diff / 2.0)
            scored.append((it, homophily))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [it for it, _ in scored[:limit]]

    # Stage 2: Heavy Ranking (Multi-task scoring)
    def stage2_heavy_rank(self, candidates: List[FeedItem]) -> List[FeedItem]:
        for it in candidates:
            # Skor keterlibatan gabungan
            it.final_score = round(it.base_score * 0.7 + random.uniform(0.1, 0.3), 3)
        candidates.sort(key=lambda x: x.final_score, reverse=True)
        return candidates

    # Stage 3: Re-Ranking with Echo Chamber Damping
    def stage3_rerank(self, ranked_items: List[FeedItem], user_stance: float) -> List[FeedItem]:
        result = []
        for it in ranked_items:
            # Cek kesesuaian sudut pandang
            stance_diff = abs(it.stance - user_stance)
            # Jika pandangan terlalu identik (risiko echo chamber), terapkan damping
            if stance_diff < 0.2:
                it.final_score *= (1.0 - (self.damping_factor * 0.5))
            else:
                # Beri bonus eksplorasi untuk konten kontras moderat
                it.final_score *= 1.15
            result.append(it)

        # Epsilon-greedy injection: acak item non-top
        if random.random() < self.epsilon and len(result) > 3:
            rand_idx = random.randint(2, len(result) - 1)
            result[0], result[rand_idx] = result[rand_idx], result[0]

        result.sort(key=lambda x: x.final_score, reverse=True)
        return result

    @staticmethod
    def calculate_shannon_entropy(items: List[FeedItem]) -> float:
        """Menghitung Shannon Entropy dari persebaran topik/stance pada feed."""
        if not items:
            return 0.0
        counts: Dict[str, int] = {}
        for it in items:
            counts[it.topic] = counts.get(it.topic, 0) + 1
        entropy = 0.0
        total = len(items)
        for c in counts.values():
            p = c / total
            entropy -= p * math.log2(p)
        return round(entropy, 3)
