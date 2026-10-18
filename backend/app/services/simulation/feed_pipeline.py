# backend/app/services/simulation/feed_pipeline.py
"""
Home-Mixer 6-Stage Feed Recommendation Pipeline:
1. Source: Pemilahan kandidat in-network dan out-network.
2. Hydrator: Penambahan metrik profil akun & engagement fitur.
3. Filter: Deduplikasi, blokir akun, safety filtering, batasan frekuensi.
4. Scorer: Perhitungan p_like, p_retweet, p_reply dengan pembobotan platform.
5. Selector: Diversifikasi slate, batasan domain, interleaving.
6. SideEffect: Pencatatan impresi dan pembaruan counter.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
import math

from app.services.simulation.platform_profile_store import PlatformProfileStore


@dataclass
class CandidateItem:
    """Representasi kandidat konten dalam feed pipeline."""
    id: str
    author_id: str
    text: str = ""
    created_at_hours_ago: float = 0.0
    in_network: bool = False
    topic: str = "general"
    domain: str = "default"
    toxic_score: float = 0.0
    features: Dict[str, Any] = field(default_factory=dict)
    predicted_scores: Dict[str, float] = field(default_factory=dict)
    final_score: float = 0.0
    filtered_reason: Optional[str] = None


@dataclass
class PipelineContext:
    """Konteks eksekusi pipeline rekomendasi per pengguna."""
    platform: str = "x"
    user_id: str = "user_0"
    user_network: Set[str] = field(default_factory=set)
    blocked_authors: Set[str] = field(default_factory=set)
    seen_ids: Set[str] = field(default_factory=set)
    author_frequency: Dict[str, int] = field(default_factory=dict)
    topic_frequency: Dict[str, int] = field(default_factory=dict)
    impressions: List[str] = field(default_factory=list)
    slate_size: int = 10
    platform_profile: Dict[str, Any] = field(default_factory=dict)


class SourceStage:
    """Stage 1: Menandai dan mengelompokkan kandidat in-network vs out-network."""

    def process(self, candidates: List[CandidateItem], ctx: PipelineContext) -> List[CandidateItem]:
        for item in candidates:
            item.in_network = item.author_id in ctx.user_network
        return candidates


class HydratorStage:
    """Stage 2: Menarik fitur engagement & profil akun."""

    def process(self, candidates: List[CandidateItem], ctx: PipelineContext) -> List[CandidateItem]:
        for item in candidates:
            # Default fitur engagement jika belum terisi
            f = item.features
            f.setdefault("likes_count", 0)
            f.setdefault("retweets_count", 0)
            f.setdefault("replies_count", 0)
            f.setdefault("author_authority", 0.5)
            f.setdefault("quality_score", 0.7)
            f.setdefault("arousal_score", 0.5)
        return candidates


class FilterStage:
    """Stage 3: Deduplikasi, filter blokir, safety filter, dan batasan frekuensi."""

    def process(self, candidates: List[CandidateItem], ctx: PipelineContext) -> List[CandidateItem]:
        safety_cfg = ctx.platform_profile.get("safety", {})
        toxic_limit = safety_cfg.get("toxic_threshold", 0.70)
        author_cap = safety_cfg.get("frequency_cap_author_per_slate", 3)

        passed: List[CandidateItem] = []
        author_counts: Dict[str, int] = {}
        seen_batch: Set[str] = set()

        for item in candidates:
            # 1. Deduplikasi
            if item.id in ctx.seen_ids or item.id in seen_batch:
                item.filtered_reason = "dedup"
                continue

            # 2. Blokir akun
            if item.author_id in ctx.blocked_authors:
                item.filtered_reason = "blocked_author"
                continue

            # 3. Safety filter
            if item.toxic_score >= toxic_limit:
                item.filtered_reason = "toxic_safety"
                continue

            # 4. Batasan frekuensi author
            count = author_counts.get(item.author_id, 0)
            if count >= author_cap:
                item.filtered_reason = "author_frequency_cap"
                continue

            seen_batch.add(item.id)
            author_counts[item.author_id] = count + 1
            passed.append(item)

        return passed


class ScorerStage:
    """Stage 4: Perhitungan p_like, p_retweet, p_reply dengan pembobotan platform."""

    def process(self, candidates: List[CandidateItem], ctx: PipelineContext) -> List[CandidateItem]:
        weights = ctx.platform_profile.get("weights", {
            "p_like": 0.25, "p_retweet": 0.35, "p_reply": 0.25, "p_dwell": 0.15
        })
        w_like = weights.get("p_like", 0.25)
        w_retweet = weights.get("p_retweet", 0.35)
        w_reply = weights.get("p_reply", 0.25)
        w_dwell = weights.get("p_dwell", 0.15)

        for item in candidates:
            f = item.features
            likes = f.get("likes_count", 0)
            rts = f.get("retweets_count", 0)
            replies = f.get("replies_count", 0)
            auth = f.get("author_authority", 0.5)
            quality = f.get("quality_score", 0.7)

            recency_decay = 1.0 / (1.0 + 0.1 * item.created_at_hours_ago)
            network_boost = 1.25 if item.in_network else 1.0

            # Prediksi probabilitas
            p_like = min(1.0, (math.log1p(likes) / 10.0 + 0.2 * quality) * recency_decay * network_boost)
            p_retweet = min(1.0, (math.log1p(rts) / 10.0 + 0.2 * auth) * recency_decay * network_boost)
            p_reply = min(1.0, (math.log1p(replies) / 10.0 + 0.15 * f.get("arousal_score", 0.5)) * recency_decay)
            p_dwell = min(1.0, (0.5 * quality + 0.5 * auth) * recency_decay)

            item.predicted_scores = {
                "p_like": p_like,
                "p_retweet": p_retweet,
                "p_reply": p_reply,
                "p_dwell": p_dwell,
            }

            item.final_score = (
                w_like * p_like +
                w_retweet * p_retweet +
                w_reply * p_reply +
                w_dwell * p_dwell
            )
        return candidates


class SelectorStage:
    """Stage 5: Diversifikasi slate, batasan domain, dan interleaving in/out network."""

    def process(self, candidates: List[CandidateItem], ctx: PipelineContext) -> List[CandidateItem]:
        # Sort descending berdasarkan final_score
        sorted_candidates = sorted(candidates, key=lambda x: x.final_score, reverse=True)

        in_net = [c for c in sorted_candidates if c.in_network]
        out_net = [c for c in sorted_candidates if not c.in_network]

        selected: List[CandidateItem] = []
        domain_counts: Dict[str, int] = {}
        max_per_domain = 3

        # Interleaving: 1 in-network, 1 out-network
        idx_in = 0
        idx_out = 0

        while len(selected) < ctx.slate_size and (idx_in < len(in_net) or idx_out < len(out_net)):
            candidate: Optional[CandidateItem] = None

            # Prioritaskan interleaved balance
            if (len(selected) % 2 == 0 and idx_in < len(in_net)) or idx_out >= len(out_net):
                candidate = in_net[idx_in]
                idx_in += 1
            elif idx_out < len(out_net):
                candidate = out_net[idx_out]
                idx_out += 1

            if candidate:
                d_count = domain_counts.get(candidate.domain, 0)
                if d_count < max_per_domain:
                    domain_counts[candidate.domain] = d_count + 1
                    selected.append(candidate)

        return selected


class SideEffectStage:
    """Stage 6: Pencatatan impresi dan pembaruan counter frekuensi."""

    def process(self, candidates: List[CandidateItem], ctx: PipelineContext) -> List[CandidateItem]:
        for item in candidates:
            ctx.impressions.append(item.id)
            ctx.seen_ids.add(item.id)
            ctx.author_frequency[item.author_id] = ctx.author_frequency.get(item.author_id, 0) + 1
            ctx.topic_frequency[item.topic] = ctx.topic_frequency.get(item.topic, 0) + 1
        return candidates


class FeedPipeline:
    """Home-Mixer 6-stage Pipeline Runner."""

    def __init__(self, profile_store: Optional[PlatformProfileStore] = None):
        self.profile_store = profile_store or PlatformProfileStore()
        self.stage1_source = SourceStage()
        self.stage2_hydrator = HydratorStage()
        self.stage3_filter = FilterStage()
        self.stage4_scorer = ScorerStage()
        self.stage5_selector = SelectorStage()
        self.stage6_side_effect = SideEffectStage()

    def run(self, candidates: List[CandidateItem], ctx: PipelineContext) -> List[CandidateItem]:
        """Jalankan seluruh 6 tahap pipeline."""
        if not ctx.platform_profile:
            ctx.platform_profile = self.profile_store.get_profile(ctx.platform)

        items = self.stage1_source.process(candidates, ctx)
        items = self.stage2_hydrator.process(items, ctx)
        items = self.stage3_filter.process(items, ctx)
        items = self.stage4_scorer.process(items, ctx)
        items = self.stage5_selector.process(items, ctx)
        items = self.stage6_side_effect.process(items, ctx)
        return items
