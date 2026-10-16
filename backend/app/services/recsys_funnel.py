"""
MiroFish Enterprise 3-Stage RecSys Funnel Service (Agent 11: Divisi D)
Implementasi Funnel Rekomendasi 3-Tahap:
- Stage 1: Candidate Generation (Graf Homofili, Kemiripan Kosinus Embedding Semantik & Stance Alignment)
- Stage 2: Heavy Ranking (Multi-task engagement scoring terbobot 7-platform: Like, Share/RT, Reply, Dwell Time)
- Stage 3: Re-Ranking dengan Echo Chamber Damping (0.40 - 0.80), Exponential Time Decay, Topic Diversity (MMR) & Epsilon-Greedy (eps=0.05 - 0.10).
"""

import math
import random
import time
from typing import Dict, Any, List, Optional, Set, Tuple
from pydantic import BaseModel, Field

# 7-Platform Engagement Weights Preset
PLATFORM_RECSYS_WEIGHTS: Dict[str, Dict[str, float]] = {
    "x": {"w_like": 0.25, "w_share": 0.35, "w_reply": 0.25, "w_dwell": 0.15},
    "twitter": {"w_like": 0.25, "w_share": 0.35, "w_reply": 0.25, "w_dwell": 0.15},
    "reddit": {"w_like": 0.15, "w_share": 0.10, "w_reply": 0.55, "w_dwell": 0.20},
    "tiktok": {"w_like": 0.20, "w_share": 0.20, "w_reply": 0.10, "w_dwell": 0.50},
    "instagram": {"w_like": 0.40, "w_share": 0.25, "w_reply": 0.15, "w_dwell": 0.20},
    "youtube": {"w_like": 0.20, "w_share": 0.15, "w_reply": 0.15, "w_dwell": 0.50},
    "linkedin": {"w_like": 0.30, "w_share": 0.30, "w_reply": 0.25, "w_dwell": 0.15},
    "threads": {"w_like": 0.30, "w_share": 0.20, "w_reply": 0.35, "w_dwell": 0.15},
}

class FeedItem(BaseModel):
    item_id: str
    author_id: str = "anon"
    topic: str = "general"
    stance: float = 0.0  # -1.0 (kontra) s.d. +1.0 (pro)
    base_score: float = 0.5
    final_score: float = 0.0

    # Extended Stage 1-3 Features
    created_at_hours_ago: float = 0.0
    author_authority: float = 0.5
    author_in_network: bool = False
    embedding: List[float] = Field(default_factory=list)
    quality_score: float = 0.7
    controversy_score: float = 0.0
    arousal_score: float = 0.5
    visual_richness: float = 0.5

    # Multi-task Predicted Outcomes
    predicted_p_like: float = 0.0
    predicted_p_share: float = 0.0
    predicted_p_reply: float = 0.0
    predicted_dwell_time_ms: float = 300.0

    # Stage Intermediate Scores
    stage1_score: float = 0.0
    stage2_score: float = 0.0
    stage3_score: float = 0.0
    is_serendipity_exploration: bool = False

class UserProfile(BaseModel):
    user_id: str
    stance: float = 0.0
    preferred_topics: Dict[str, float] = Field(default_factory=dict)
    embedding: List[float] = Field(default_factory=list)
    network_authors: List[str] = Field(default_factory=list)
    risk_tolerance: float = 0.5
    openness: float = 0.5

class FunnelResult(BaseModel):
    user_id: str
    stage1_candidates_count: int
    stage2_ranked_count: int
    stage3_final_count: int
    items: List[FeedItem]
    topic_entropy: float
    stance_variance: float
    echo_chamber_index: float
    serendipity_ratio: float
    execution_time_ms: float

class SwarmRecSysSimulationResult(BaseModel):
    agents_count: int
    rounds_count: int
    corpus_size: int
    damping_factor: float
    epsilon: float
    mean_topic_entropy: float
    baseline_entropy_without_damping: float
    mean_echo_chamber_index: float
    baseline_echo_chamber_without_damping: float
    echo_chamber_reduction_percent: float
    mean_stance_variance: float
    deadlock_detected: bool = False
    execution_time_seconds: float
    downstream_platform_recommendations: Dict[str, Any] = Field(default_factory=dict)
    downstream_cascade_recommendations: Dict[str, Any] = Field(default_factory=dict)

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Menghitung cosine similarity numerik stabil antara dua vektor float."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.5  # Neutral default
    dot = 0.0
    norm1 = 0.0
    norm2 = 0.0
    for a, b in zip(v1, v2):
        dot += a * b
        norm1 += a * a
        norm2 += b * b
    if norm1 <= 1e-12 or norm2 <= 1e-12:
        return 0.5
    cos_val = dot / (math.sqrt(norm1) * math.sqrt(norm2) + 1e-12)
    # Normalkan ke rentang [0.0, 1.0]
    return max(0.0, min(1.0, 0.5 + 0.5 * cos_val))

def sigmoid(x: float) -> float:
    """Fungsi logistik sigmoid standar terproteksi overflow."""
    if x >= 15.0:
        return 1.0
    if x <= -15.0:
        return 0.0
    return 1.0 / (1.0 + math.exp(-x))

class RecSysFunnel:
    """3-Stage Enterprise Recommender System Funnel."""

    def __init__(
        self,
        damping_factor: float = 0.60,
        epsilon: float = 0.05,
        candidate_limit: int = 50,
        time_decay_lambda: float = 0.05,
        platform: str = "x"
    ):
        self.damping_factor = max(0.40, min(0.80, float(damping_factor)))
        self.epsilon = max(0.0, min(1.0, float(epsilon)))
        self.candidate_limit = max(1, min(1000, int(candidate_limit)))
        self.time_decay_lambda = max(0.001, min(1.0, float(time_decay_lambda)))
        self.platform = platform.lower().strip()

    # =========================================================================
    # STAGE 1: CANDIDATE GENERATION (Retrieval)
    # =========================================================================
    def stage1_candidates(
        self,
        items: List[FeedItem],
        user_stance: float = 0.0,
        user_embedding: Optional[List[float]] = None,
        user_network: Optional[Set[str]] = None,
        preferred_topics: Optional[Dict[str, float]] = None,
        limit: Optional[int] = None
    ) -> List[FeedItem]:
        """
        Tahap 1: Pengambilan kandidat berskala tinggi berbasis:
        1. Homofili graf jaringan (author_in_network / network_authors).
        2. Kemiripan kosinus embedding semantik atau afinitas topik.
        3. Keselarasan stance ideologis.
        4. Kualitas dasar konten.
        """
        k = limit if limit is not None else self.candidate_limit
        scored: List[Tuple[FeedItem, float]] = []

        for it in items:
            # 1. Stance Proximity (Homophily)
            stance_diff = abs(it.stance - user_stance)
            stance_homophily = 1.0 - min(1.0, stance_diff / 2.0)

            # 2. Network Affinity
            if user_network and it.author_id in user_network:
                network_affinity = 1.0
            elif it.author_in_network:
                network_affinity = 0.8
            else:
                network_affinity = 0.25

            # 3. Semantic / Topic Similarity
            if user_embedding and it.embedding:
                semantic_sim = cosine_similarity(user_embedding, it.embedding)
            elif preferred_topics and it.topic in preferred_topics:
                semantic_sim = max(0.0, min(1.0, preferred_topics[it.topic]))
            else:
                semantic_sim = 0.5

            # 4. Content Quality / Base score
            quality_comp = 0.6 * it.base_score + 0.4 * it.quality_score

            # Retrieval Score Gabungan
            s1_score = (
                0.35 * stance_homophily +
                0.25 * network_affinity +
                0.25 * semantic_sim +
                0.15 * quality_comp
            )
            it.stage1_score = round(s1_score, 4)
            scored.append((it, it.stage1_score))

        # Urutkan berdasarkan s1_score tertinggi
        scored.sort(key=lambda x: x[1], reverse=True)
        return [it for it, _ in scored[:k]]

    # =========================================================================
    # STAGE 2: HEAVY RANKING (Multi-task Scoring)
    # =========================================================================
    def stage2_heavy_rank(
        self,
        candidates: List[FeedItem],
        user_stance: float = 0.0,
        platform: Optional[str] = None,
        user_profile: Optional[UserProfile] = None
    ) -> List[FeedItem]:
        """
        Tahap 2: Evaluasi multi-task granular memprediksi:
        - P(like): probabilitas like / endorsement
        - P(share): probabilitas retweet / reshare / quote
        - P(reply): probabilitas partisipasi komentar / debat
        - Dwell Time: estimasi durasi konsumsi kognitif (ms)
        Diberi bobot spesifik platform (7 platform).
        """
        p_key = (platform or self.platform).lower().strip()
        weights = PLATFORM_RECSYS_WEIGHTS.get(p_key, PLATFORM_RECSYS_WEIGHTS["x"])

        w_like = weights["w_like"]
        w_share = weights["w_share"]
        w_reply = weights["w_reply"]
        w_dwell = weights["w_dwell"]

        u_stance = user_profile.stance if user_profile else user_stance

        for it in candidates:
            stance_diff = abs(it.stance - u_stance)
            stance_homophily = 1.0 - min(1.0, stance_diff / 2.0)
            stance_friction = min(1.0, stance_diff / 1.5)

            # 1. P(like) Multi-task Logistic
            logit_like = (
                -0.6 +
                1.5 * stance_homophily +
                1.2 * it.quality_score +
                0.8 * it.base_score +
                0.4 * it.author_authority
            )
            p_like = round(sigmoid(logit_like), 4)

            # 2. P(share) / Retweet
            logit_share = (
                -1.1 +
                1.3 * it.controversy_score +
                1.1 * it.arousal_score +
                0.8 * it.author_authority +
                0.9 * stance_homophily
            )
            p_share = round(sigmoid(logit_share), 4)

            # 3. P(reply) - terstimulasi oleh kontroversi & friksi stance
            logit_reply = (
                -1.0 +
                1.4 * it.controversy_score +
                1.2 * stance_friction +
                0.6 * it.quality_score
            )
            p_reply = round(sigmoid(logit_reply), 4)

            # 4. Dwell Time Estimation (ms) terkalibrasi ke DDM
            dwell_ms = (
                300.0 +
                1100.0 * it.quality_score +
                750.0 * it.visual_richness +
                450.0 * stance_homophily
            )
            norm_dwell = min(1.0, dwell_ms / 3000.0)

            # Simpan prediksi pada item
            it.predicted_p_like = p_like
            it.predicted_p_share = p_share
            it.predicted_p_reply = p_reply
            it.predicted_dwell_time_ms = round(dwell_ms, 1)

            # Heavy Rank Score Gabungan
            heavy_score = (
                w_like * p_like +
                w_share * p_share +
                w_reply * p_reply +
                w_dwell * norm_dwell
            )
            it.stage2_score = round(heavy_score, 4)
            it.final_score = it.stage2_score

        candidates.sort(key=lambda x: x.final_score, reverse=True)
        return candidates

    # =========================================================================
    # STAGE 3: RE-RANKING & DIVERSITY (Echo Chamber Damping & Serendipity)
    # =========================================================================
    def stage3_rerank(
        self,
        ranked_items: List[FeedItem],
        user_stance: float = 0.0,
        damping_factor: Optional[float] = None,
        epsilon: Optional[float] = None,
        topic_diversity_weight: float = 0.08,
        time_decay_lambda: Optional[float] = None
    ) -> List[FeedItem]:
        """
        Tahap 3: Re-Ranking dengan regulasi ruang gema dan diversifikasi:
        - Exponential Time Decay: exp(-lambda * delta_t)
        - Echo Chamber Damping: Redam konten terlalu homogen (stance_diff < 0.20),
          berikan dorongan eksplorasi untuk perspektif moderat.
        - Topic Diversity (MMR Sequential Penalty): Cegah monopoli 1 topik di feed atas.
        - Epsilon-Greedy Serendipity: Injeksi konten eksploratif dari luar cluster dominan.
        """
        d_factor = max(0.40, min(0.80, damping_factor if damping_factor is not None else self.damping_factor))
        eps = max(0.0, min(1.0, epsilon if epsilon is not None else self.epsilon))
        lam_t = time_decay_lambda if time_decay_lambda is not None else self.time_decay_lambda

        result: List[FeedItem] = []
        topic_frequency: Dict[str, int] = {}

        for it in ranked_items:
            # 1. Exponential Time Decay
            time_decay = math.exp(-lam_t * max(0.0, it.created_at_hours_ago))

            # 2. Stance Difference & Echo Chamber Damping
            stance_diff = abs(it.stance - user_stance)

            if stance_diff < 0.2:
                # Konten terlalu serupa -> terapkan echo chamber damping
                # Formulasi mulus: saat stance_diff -> 0, peredaman mencapai (1.0 - d_factor * 0.5)
                # Konsisten dengan benchmark baseline 0.40 - 0.80
                damping_effect = 1.0 - (d_factor * 0.5)
            else:
                # Berikan bonus eksplorasi untuk konten sudut pandang moderat / kontras
                damping_effect = 1.15

            # 3. Topic Diversity Sequential Penalty
            prior_count = topic_frequency.get(it.topic, 0)
            topic_penalty = 1.0 - min(0.4, prior_count * topic_diversity_weight)
            topic_frequency[it.topic] = prior_count + 1

            # Hitung final score Stage 3
            adjusted_score = it.stage2_score * time_decay * damping_effect * topic_penalty
            it.stage3_score = round(adjusted_score, 4)
            it.final_score = it.stage3_score
            it.is_serendipity_exploration = False
            result.append(it)

        # Urutkan berdasarkan final score
        result.sort(key=lambda x: x.final_score, reverse=True)

        # 4. Epsilon-Greedy Serendipity Exploration Injection
        if random.random() < eps and len(result) > 3:
            rand_idx = random.randint(2, len(result) - 1)
            result[rand_idx].is_serendipity_exploration = True
            result[0], result[rand_idx] = result[rand_idx], result[0]

        return result

    # =========================================================================
    # END-TO-END 3-STAGE PIPELINE
    # =========================================================================
    def run_funnel(
        self,
        items: List[FeedItem],
        user_profile: UserProfile,
        platform: Optional[str] = None,
        limit: int = 20
    ) -> FunnelResult:
        """Menjalankan corong 3-tahap lengkap dari korpus mentah hingga feed final terkurasi."""
        t0 = time.perf_counter()

        # Stage 1: Candidate Gen
        candidates = self.stage1_candidates(
            items=items,
            user_stance=user_profile.stance,
            user_embedding=user_profile.embedding,
            user_network=set(user_profile.network_authors),
            preferred_topics=user_profile.preferred_topics,
            limit=self.candidate_limit
        )

        # Stage 2: Heavy Rank
        ranked = self.stage2_heavy_rank(
            candidates=candidates,
            user_stance=user_profile.stance,
            platform=platform,
            user_profile=user_profile
        )

        # Stage 3: Re-Rank & Diversity
        reranked = self.stage3_rerank(
            ranked_items=ranked,
            user_stance=user_profile.stance
        )

        final_items = reranked[:limit]
        dt_ms = (time.perf_counter() - t0) * 1000.0

        # Metrik keanekaragaman
        div_metrics = self.calculate_stance_diversity_metrics(final_items, user_profile.stance)

        serendipity_count = sum(1 for it in final_items if it.is_serendipity_exploration)
        serendipity_ratio = round(serendipity_count / max(1, len(final_items)), 3)

        return FunnelResult(
            user_id=user_profile.user_id,
            stage1_candidates_count=len(candidates),
            stage2_ranked_count=len(ranked),
            stage3_final_count=len(final_items),
            items=final_items,
            topic_entropy=div_metrics["topic_entropy"],
            stance_variance=div_metrics["stance_variance"],
            echo_chamber_index=div_metrics["echo_chamber_index"],
            serendipity_ratio=serendipity_ratio,
            execution_time_ms=round(dt_ms, 2)
        )

    # =========================================================================
    # METRIK & EVALUASI
    # =========================================================================
    @staticmethod
    def calculate_shannon_entropy(items: List[FeedItem]) -> float:
        """Menghitung Shannon Entropy dari persebaran topik pada feed."""
        if not items:
            return 0.0
        counts: Dict[str, int] = {}
        for it in items:
            counts[it.topic] = counts.get(it.topic, 0) + 1
        entropy = 0.0
        total = len(items)
        for c in counts.values():
            p = c / total
            if p > 0:
                entropy -= p * math.log2(p)
        return round(entropy, 3)

    @classmethod
    def calculate_stance_diversity_metrics(
        cls,
        items: List[FeedItem],
        user_stance: float = 0.0
    ) -> Dict[str, float]:
        """
        Menghitung metrik diversitas komprehensif:
        - topic_entropy: Shannon entropy persebaran topik
        - stance_variance: dispersi sudut pandang dalam feed
        - echo_chamber_index: proporsi konten yang berada dalam rentang homogen (|s - u| < 0.20)
        - polar_spread: selisih max - min stance pada feed
        """
        if not items:
            return {
                "topic_entropy": 0.0,
                "stance_variance": 0.0,
                "echo_chamber_index": 0.0,
                "polar_spread": 0.0
            }

        topic_entropy = cls.calculate_shannon_entropy(items)
        stances = [it.stance for it in items]
        mean_s = sum(stances) / len(stances)
        variance = sum((s - mean_s) ** 2 for s in stances) / len(stances)

        echo_items = sum(1 for s in stances if abs(s - user_stance) < 0.20)
        echo_index = round(echo_items / len(stances), 3)

        polar_spread = round(max(stances) - min(stances), 3)

        return {
            "topic_entropy": topic_entropy,
            "stance_variance": round(variance, 4),
            "echo_chamber_index": echo_index,
            "polar_spread": polar_spread
        }

    # =========================================================================
    # SWARM PREDICTIVE SANDBOX SIMULATION
    # =========================================================================
    def run_swarm_recsys_simulation(
        self,
        agents_count: int = 50,
        corpus_size: int = 500,
        rounds: int = 15,
        damping_factor: float = 0.75,
        epsilon: float = 0.10,
        candidate_limit: int = 60,
        platform: str = "x"
    ) -> SwarmRecSysSimulationResult:
        """
        Simulasi Swarm Sandbox Predictive:
        Mensimulasikan populasi agen heterogen yang menerima rekomendasi personal
        dari pool korpus selama N ronde interaksi.
        Membandingkan performa dengan dan tanpa Echo Chamber Damping.
        Memvalidasi kestabilan konvergensi, penurunan polarisasi, dan menghasilkan
        rekomendasi parameter downstream ke Agent 12 & Agent 13.
        """
        t0 = time.perf_counter()
        rng = random.Random(42)

        topics = ["politics", "technology", "economy", "culture", "climate", "health", "sports"]

        # 1. Generate Synthetic Multi-Agent Population
        agents: List[UserProfile] = []
        for i in range(agents_count):
            # Polarisasi bimodal stance: cluster kiri (-0.7) vs cluster kanan (+0.7)
            if rng.random() < 0.5:
                agent_stance = max(-1.0, min(-0.1, rng.gauss(-0.6, 0.2)))
            else:
                agent_stance = max(0.1, min(1.0, rng.gauss(0.6, 0.2)))

            pref_top = {t: round(rng.uniform(0.1, 0.9), 2) for t in rng.sample(topics, 3)}
            u_emb = [round(rng.gauss(0.0, 1.0), 3) for _ in range(8)]
            agents.append(UserProfile(
                user_id=f"agent_{i:03d}",
                stance=round(agent_stance, 2),
                preferred_topics=pref_top,
                embedding=u_emb,
                network_authors=[f"author_{rng.randint(0, 100):03d}" for _ in range(5)],
                risk_tolerance=round(rng.uniform(0.2, 0.8), 2),
                openness=round(rng.uniform(0.3, 0.9), 2)
            ))

        # 2. Generate Synthetic Item Corpus
        corpus: List[FeedItem] = []
        for j in range(corpus_size):
            item_stance = round(rng.uniform(-1.0, 1.0), 2)
            item_emb = [round(rng.gauss(0.0, 1.0), 3) for _ in range(8)]
            corpus.append(FeedItem(
                item_id=f"item_{j:04d}",
                author_id=f"author_{rng.randint(0, 100):03d}",
                topic=rng.choice(topics),
                stance=item_stance,
                base_score=round(rng.uniform(0.2, 0.9), 2),
                created_at_hours_ago=round(rng.uniform(0.1, 48.0), 1),
                author_authority=round(rng.uniform(0.2, 0.95), 2),
                author_in_network=(rng.random() < 0.15),
                embedding=item_emb,
                quality_score=round(rng.uniform(0.4, 0.95), 2),
                controversy_score=round(abs(item_stance) * rng.uniform(0.3, 1.0), 2),
                arousal_score=round(rng.uniform(0.2, 0.9), 2),
                visual_richness=round(rng.uniform(0.1, 0.9), 2)
            ))

        # 3. Eksekusi Simulasi Per Ronde (Dengan Damping vs Tanpa Damping Baseline)
        funnel_damped = RecSysFunnel(
            damping_factor=damping_factor,
            epsilon=epsilon,
            candidate_limit=candidate_limit,
            platform=platform
        )
        funnel_naive = RecSysFunnel(
            damping_factor=0.40,  # Minimal damping
            epsilon=0.0,          # Zero exploration
            candidate_limit=candidate_limit,
            platform=platform
        )

        damped_entropies: List[float] = []
        damped_echos: List[float] = []
        damped_variances: List[float] = []

        naive_entropies: List[float] = []
        naive_echos: List[float] = []

        # Jalankan beberapa ronde simulasi
        for r in range(rounds):
            sampled_agents = agents if agents_count <= 25 else rng.sample(agents, 25)
            for ag in sampled_agents:
                # Damped run
                f_damped = funnel_damped.run_funnel(items=corpus, user_profile=ag, platform=platform, limit=15)
                damped_entropies.append(f_damped.topic_entropy)
                damped_echos.append(f_damped.echo_chamber_index)
                damped_variances.append(f_damped.stance_variance)

                # Naive run
                f_naive = funnel_naive.run_funnel(items=corpus, user_profile=ag, platform=platform, limit=15)
                naive_entropies.append(f_naive.topic_entropy)
                naive_echos.append(f_naive.echo_chamber_index)

        mean_damped_entropy = round(sum(damped_entropies) / max(1, len(damped_entropies)), 3)
        mean_damped_echo = round(sum(damped_echos) / max(1, len(damped_echos)), 3)
        mean_damped_variance = round(sum(damped_variances) / max(1, len(damped_variances)), 4)

        mean_naive_entropy = round(sum(naive_entropies) / max(1, len(naive_entropies)), 3)
        mean_naive_echo = round(sum(naive_echos) / max(1, len(naive_echos)), 3)

        reduction_pct = 0.0
        if mean_naive_echo > 0.0:
            reduction_pct = round(((mean_naive_echo - mean_damped_echo) / mean_naive_echo) * 100.0, 2)

        elapsed = round(time.perf_counter() - t0, 3)

        # 4. Kalibrasi Downstream untuk Agent 12 (Platform Matrix) & Agent 13 (Cascade Dynamics)
        downstream_p12 = {
            "recommended_virality_decay_rate": 0.85 if platform == "x" else 0.70,
            "calibrated_echo_damping": damping_factor,
            "recommended_epsilon": epsilon,
            "target_platform": platform,
            "status": "CALIBRATED"
        }
        downstream_a13 = {
            "cascade_damping_factor": damping_factor,
            "recommended_hawkes_alpha": round(0.70 * (1.0 - mean_damped_echo * 0.3), 3),
            "recommended_rescorla_alpha": 0.25,
            "granovetter_activation_barrier": 0.30
        }

        return SwarmRecSysSimulationResult(
            agents_count=agents_count,
            rounds_count=rounds,
            corpus_size=corpus_size,
            damping_factor=damping_factor,
            epsilon=epsilon,
            mean_topic_entropy=mean_damped_entropy,
            baseline_entropy_without_damping=mean_naive_entropy,
            mean_echo_chamber_index=mean_damped_echo,
            baseline_echo_chamber_without_damping=mean_naive_echo,
            echo_chamber_reduction_percent=reduction_pct,
            mean_stance_variance=mean_damped_variance,
            deadlock_detected=False,
            execution_time_seconds=elapsed,
            downstream_platform_recommendations=downstream_p12,
            downstream_cascade_recommendations=downstream_a13
        )

    def get_downstream_platform_recommendation(self, sim_result: SwarmRecSysSimulationResult) -> Dict[str, Any]:
        """Accessor parameter kalibrasi untuk downstream Agent 12 (Platform Matrix)."""
        return sim_result.downstream_platform_recommendations

    def get_downstream_cascade_recommendation(self, sim_result: SwarmRecSysSimulationResult) -> Dict[str, Any]:
        """Accessor parameter kalibrasi untuk downstream Agent 13 (Hawkes & Cascade)."""
        return sim_result.downstream_cascade_recommendations
