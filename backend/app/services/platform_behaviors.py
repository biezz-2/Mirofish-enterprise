# backend/app/services/platform_behaviors.py
"""
Karakteristik dan perilaku platform untuk simulasi multi-platform MiroFish.
Seluruh platform dimodelkan sebagai DATA, bukan fork kode.
Menerapkan spesifikasi matematis Notion:
- Normalized Feed Scoring: Score = lambda_rec * 2^(-dt/t_half) + beta_pop * min(1, ln(1+Eng)/ln(1+Eng_p99)) + gamma_echo * (1 + cos(e_i, e_j))/2
- Parameter spesifik per platform (TikTok t_half=1.8, Reddit t_half=6.0, dll)
- Aturan partisipasi Pareto 90-9-1 (90% lurker, 9% contributor, 1% creator)
"""
import math
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any

# ============ LANGKAH 1: KARAKTERISTIK PLATFORM ============
# Parameter empiris dan pembobotan konveks terkalibrasi sesuai Dokumen Notion #2 & #7
# Syarat konveks: lambda_rec + beta_pop + gamma_echo = 1.0
PLATFORM_CHARACTERISTICS: Dict[str, dict] = {
    "twitter": {
        "display_name": "Twitter",
        "recency_weight": 0.50,
        "popularity_weight": 0.35,
        "relevance_weight": 0.20,
        "echo_chamber_strength": 0.15,
        "half_life": 2.5,
        "half_life_rounds": 2.5,
        "eng_p99": 5000,
        "viral_threshold": 5000,
        "max_content_length": 280,
        "interaction_style": "ephemeral",
        "base_activity_multiplier": 1.0,
    },
    "x": {
        "display_name": "X",
        "recency_weight": 0.40,
        "popularity_weight": 0.30,
        "relevance_weight": 0.20,
        "echo_chamber_strength": 0.30,
        "half_life": 3.5,
        "half_life_rounds": 3.5,
        "eng_p99": 8000,
        "viral_threshold": 8000,
        "max_content_length": 25000,
        "interaction_style": "ephemeral_long",
        "base_activity_multiplier": 0.9,
    },
    "reddit": {
        "display_name": "Reddit",
        "recency_weight": 0.20,
        "popularity_weight": 0.40,
        "relevance_weight": 0.25,
        "echo_chamber_strength": 0.40,
        "half_life": 6.0,
        "half_life_rounds": 6.0,
        "eng_p99": 500,
        "viral_threshold": 300,
        "max_content_length": 40000,
        "interaction_style": "persistent_deep",
        "base_activity_multiplier": 0.8,
    },
    "tiktok": {
        "display_name": "TikTok",
        "recency_weight": 0.45,
        "popularity_weight": 0.45,
        "relevance_weight": 0.30,
        "echo_chamber_strength": 0.10,
        "half_life": 1.8,
        "half_life_rounds": 1.8,
        "eng_p99": 50000,
        "viral_threshold": 50000,
        "max_content_length": 150,
        "interaction_style": "algorithmic_viral",
        "base_activity_multiplier": 1.3,
    },
    "instagram": {
        "display_name": "Instagram",
        "recency_weight": 0.30,
        "popularity_weight": 0.45,
        "relevance_weight": 0.25,
        "echo_chamber_strength": 0.25,
        "half_life": 4.5,
        "half_life_rounds": 4.5,
        "eng_p99": 10000,
        "viral_threshold": 10000,
        "max_content_length": 2200,
        "interaction_style": "visual_follower",
        "base_activity_multiplier": 1.0,
    },
    "facebook": {
        "display_name": "Facebook",
        "recency_weight": 0.20,
        "popularity_weight": 0.35,
        "relevance_weight": 0.25,
        "echo_chamber_strength": 0.45,
        "half_life": 8.0,
        "half_life_rounds": 8.0,
        "eng_p99": 8000,
        "viral_threshold": 8000,
        "max_content_length": 63000,
        "interaction_style": "broad_network",
        "base_activity_multiplier": 0.7,
    },
    "threads": {
        "display_name": "Threads",
        "recency_weight": 0.50,
        "popularity_weight": 0.35,
        "relevance_weight": 0.20,
        "echo_chamber_strength": 0.15,
        "half_life": 3.0,
        "half_life_rounds": 3.0,
        "eng_p99": 5000,
        "viral_threshold": 5000,
        "max_content_length": 500,
        "interaction_style": "conversational",
        "base_activity_multiplier": 0.8,
    },
    "youtube": {
        "display_name": "YouTube",
        "recency_weight": 0.25,
        "popularity_weight": 0.55,
        "relevance_weight": 0.25,
        "echo_chamber_strength": 0.20,
        "half_life": 5.0,
        "half_life_rounds": 5.0,
        "eng_p99": 25000,
        "viral_threshold": 25000,
        "max_content_length": 5000,
        "interaction_style": "video_broadcast",
        "base_activity_multiplier": 0.9,
    },
    "linkedin": {
        "display_name": "LinkedIn",
        "recency_weight": 0.35,
        "popularity_weight": 0.50,
        "relevance_weight": 0.30,
        "echo_chamber_strength": 0.15,
        "half_life": 4.0,
        "half_life_rounds": 4.0,
        "eng_p99": 2000,
        "viral_threshold": 2000,
        "max_content_length": 3000,
        "interaction_style": "professional_networking",
        "base_activity_multiplier": 0.85,
    },
}

CANONICAL_PLATFORMS = (
    "instagram",
    "linkedin",
    "reddit",
    "threads",
    "tiktok",
    "twitter",
    "youtube",
)
DEFAULT_PLATFORMS = ["twitter", "reddit"]  # kompatibilitas mundur

def get_platform_characteristics(platform: str) -> dict:
    p = platform.lower().strip()
    if p not in PLATFORM_CHARACTERISTICS:
        raise ValueError(f"Platform tidak dikenal: {platform}")
    return PLATFORM_CHARACTERISTICS[p]

# ============ LANGKAH 2: ATURAN PARTISIPASI PARETO 90-9-1 ============
PARETO_DISTRIBUTION: Dict[str, float] = {
    "lurker": 0.90,       # 90% pasif (DO_NOTHING, SKIP, REFRESH)
    "contributor": 0.09,  # 9% bereaksi (LIKE, COMMENT, REPOST, SHARE, UPVOTE)
    "creator": 0.01,      # 1% pencipta konten asli (CREATE_POST, CREATE_SCRIPT)
}

PLATFORM_ACTION_SPACES: Dict[str, Dict[str, List[str]]] = {
    "twitter": {
        "creator": ["CREATE_POST"],
        "contributor": ["LIKE_POST", "REPOST", "QUOTE_POST", "FOLLOW"],
        "lurker": ["DO_NOTHING"],
    },
    "x": {
        "creator": ["CREATE_POST"],
        "contributor": ["LIKE_POST", "REPOST", "QUOTE_POST", "FOLLOW"],
        "lurker": ["DO_NOTHING"],
    },
    "reddit": {
        "creator": ["CREATE_POST"],
        "contributor": ["LIKE_POST", "CREATE_COMMENT", "LIKE_COMMENT", "DISLIKE_POST", "DISLIKE_COMMENT", "SEARCH_POSTS", "FOLLOW"],
        "lurker": ["REFRESH", "DO_NOTHING"],
    },
    "tiktok": {
        "creator": ["CREATE_SCRIPT"],
        "contributor": ["LIKE_VIDEO", "COMMENT", "SHARE_TO_FRIENDS", "DUET_REACT", "FOLLOW_CREATOR"],
        "lurker": ["SKIP", "DO_NOTHING"],
    },
    "instagram": {
        "creator": ["CREATE_POST"],
        "contributor": ["LIKE_POST", "CREATE_COMMENT", "SAVE_POST", "SHARE_STORY", "FOLLOW"],
        "lurker": ["DO_NOTHING"],
    },
    "threads": {
        "creator": ["CREATE_POST"],
        "contributor": ["LIKE_POST", "REPLY", "REPOST", "QUOTE_POST", "FOLLOW"],
        "lurker": ["DO_NOTHING"],
    },
    "youtube": {
        "creator": ["CREATE_POST"],
        "contributor": ["LIKE", "COMMENT", "SUBSCRIBE", "SHARE"],
        "lurker": ["DO_NOTHING"],
    },
    "linkedin": {
        "creator": ["CREATE_POST"],
        "contributor": ["LIKE", "COMMENT", "CONNECT", "REPOST"],
        "lurker": ["DO_NOTHING"],
    },
    "facebook": {
        "creator": ["CREATE_POST"],
        "contributor": ["LIKE", "COMMENT", "SHARE"],
        "lurker": ["DO_NOTHING"],
    },
}

def sample_agent_role(rng_val: Optional[float] = None) -> str:
    """
    Menentukan peran agen pada putaran berdasarkan distribusi Pareto 90-9-1:
    - 90% Lurker (val < 0.90)
    - 9% Contributor (0.90 <= val < 0.99)
    - 1% Creator (val >= 0.99)
    """
    val = random.random() if rng_val is None else float(rng_val)
    if val < 0.90:
        return "lurker"
    elif val < 0.99:
        return "contributor"
    return "creator"

def sample_platform_action(platform: str, role: str, rng_choice: Optional[str] = None) -> str:
    """Mengambil aksi spesifik platform berdasarkan peran Pareto (lurker, contributor, creator)."""
    p = platform.lower().strip()
    action_space = PLATFORM_ACTION_SPACES.get(p, PLATFORM_ACTION_SPACES.get("twitter"))
    candidates = action_space.get(role, ["DO_NOTHING"])
    if rng_choice and rng_choice in candidates:
        return rng_choice
    return random.choice(candidates)

# ============ LANGKAH 3: PERILAKU PLATFORM ============
@dataclass
class PlatformBehavior:
    """Turunan perilaku agen pada sebuah platform."""
    platform: str
    characteristics: dict
    agent_type_distribution: Dict[str, float] = field(default_factory=dict)
    action_probabilities: Dict[str, float] = field(default_factory=dict)
    content_style: str = ""
    demographic_bias: Dict[str, str] = field(default_factory=dict)
    peak_hours: List[int] = field(default_factory=list)

    def __post_init__(self):
        c = self.characteristics
        if self.platform in ("twitter", "x"):
            self.agent_type_distribution = {"individual": 0.6, "public_figure": 0.3, "institutional": 0.1}
            self.action_probabilities = {"post": 0.3, "repost": 0.3, "comment": 0.2, "like": 0.2}
            self.content_style = "singkat, tajam, sangat reaktif terhadap berita"
            self.peak_hours = [8, 12, 18, 21]
        elif self.platform == "reddit":
            self.agent_type_distribution = {"individual": 0.8, "public_figure": 0.1, "institutional": 0.1}
            self.action_probabilities = {"post": 0.2, "comment": 0.5, "upvote": 0.3}
            self.content_style = "panjang, argumentatif, berbasis komunitas topik"
            self.peak_hours = [10, 14, 20, 22]
        elif self.platform == "tiktok":
            self.agent_type_distribution = {"individual": 0.7, "public_figure": 0.25, "institutional": 0.05}
            self.action_probabilities = {"post": 0.15, "comment": 0.15, "like": 0.6, "share": 0.1}
            self.content_style = "sangat singkat, reaktif tren, emosional"
            self.demographic_bias = {"age": "16-30", "consumption": "pasif tinggi"}
            self.peak_hours = [12, 15, 19, 20, 21]
        elif self.platform == "facebook":
            self.agent_type_distribution = {"individual": 0.4, "public_figure": 0.2, "institutional": 0.4}
            self.action_probabilities = {"post": 0.2, "comment": 0.35, "like": 0.35, "share": 0.1}
            self.content_style = "naratif panjang, personal, keluarga/lokal"
            self.demographic_bias = {"age": "30-60", "network": "kenalan nyata"}
            self.peak_hours = [8, 13, 20]
        elif self.platform == "youtube":
            self.agent_type_distribution = {"individual": 0.65, "public_figure": 0.25, "institutional": 0.10}
            self.action_probabilities = {"post": 0.1, "comment": 0.4, "like": 0.4, "share": 0.1}
            self.content_style = "naratif deskriptif video, analitis, opini terperinci"
            self.demographic_bias = {"age": "18-50", "consumption": "video_broadcast"}
            self.peak_hours = [14, 18, 20, 22]
        elif self.platform == "linkedin":
            self.agent_type_distribution = {"individual": 0.50, "public_figure": 0.20, "institutional": 0.30}
            self.action_probabilities = {"post": 0.25, "comment": 0.35, "like": 0.30, "share": 0.10}
            self.content_style = "profesional, berorientasi karir/industri, formal"
            self.demographic_bias = {"age": "22-60", "network": "profesional_korporat"}
            self.peak_hours = [8, 9, 12, 17]
        else:  # instagram, threads — turunan parametrik
            self.agent_type_distribution = {"individual": 0.65, "public_figure": 0.25, "institutional": 0.1}
            self.action_probabilities = {"post": 0.25, "repost": 0.25, "comment": 0.25, "like": 0.25}
            self.content_style = "percakapan teks ringan"
            self.peak_hours = [9, 18, 21]

def get_platform_behavior(platform: str) -> PlatformBehavior:
    return PlatformBehavior(platform=platform, characteristics=get_platform_characteristics(platform))

# ============ LANGKAH 4: ALGORITMA REKOMENDASI PER PLATFORM (NOTION SPEC) ============
def _compute_cosine_similarity(e1: Any, e2: Any) -> float:
    """Menghitung cosine similarity antara dua embedding vektor atau nilai skalar opini."""
    if e1 is None or e2 is None:
        return 0.0
    if isinstance(e1, (list, tuple)) and isinstance(e2, (list, tuple)):
        if len(e1) != len(e2) or len(e1) == 0:
            return 0.0
        dot = sum(float(a) * float(b) for a, b in zip(e1, e2))
        norm1 = math.sqrt(sum(float(a) ** 2 for a in e1))
        norm2 = math.sqrt(sum(float(b) ** 2 for b in e2))
        if norm1 > 1e-9 and norm2 > 1e-9:
            return max(-1.0, min(1.0, dot / (norm1 * norm2)))
        return 0.0
    try:
        # Skalar opini: rentang [-1.0, 1.0] atau [0.0, 1.0]
        # Jarak diff = |v1 - v2|. Jika sama persis, cos = 1.0; jika berlawanan, cos <= -0.5
        v1 = float(e1)
        v2 = float(e2)
        diff = abs(v1 - v2)
        return max(-1.0, min(1.0, 1.0 - diff))
    except (TypeError, ValueError):
        return 0.0

def compute_feed_score(
    platform: str,
    post: dict,
    agent: dict,
    current_hour: int = 0,
    delta_t: Optional[float] = None,
) -> float:
    """
    Normalized Feed Scoring sesuai spesifikasi matematis Notion:
    Score = lambda_rec * 2^(-dt / t_half)
          + beta_pop * min(1, ln(1 + Eng) / ln(1 + Eng_p99))
          + gamma_echo * (1 + cos(e_i, e_j)) / 2
          + (opsional: relevance_weight * topic_overlap jika ada)
    """
    c = get_platform_characteristics(platform)
    lambda_rec = float(c.get("recency_weight", 0.45))
    beta_pop = float(c.get("popularity_weight", 0.30))
    gamma_echo = float(c.get("echo_chamber_strength", 0.15))
    relevance_weight = float(c.get("relevance_weight", 0.0))

    # 1. Recency term: lambda_rec * 2^(-dt / t_half)
    if delta_t is not None:
        dt = float(delta_t)
    elif "age_rounds" in post:
        dt = float(post["age_rounds"])
    else:
        dt = float(post.get("age_hours", 0.0))
    dt = max(0.0, dt)
    t_half = float(c.get("half_life", c.get("half_life_rounds", 3.0)))
    recency_term = 2.0 ** (-dt / max(t_half, 0.1))

    # 2. Popularity term: beta_pop * min(1, ln(1 + Eng) / ln(1 + Eng_p99))
    # Atenuasi popularitas 50% jika konten merupakan spillover lintas platform (Notion Dokumen #2 Rekomendasi 4)
    # untuk mencegah pelipatgandaan viralitas artifisial (runaway cascade) di platform penerima
    effective_beta_pop = beta_pop * 0.5 if post.get("is_spillover", False) else beta_pop

    eng = post.get("engagement")
    if eng is None:
        likes = float(post.get("likes", post.get("like_count", 0)))
        shares = float(post.get("shares", post.get("share_count", post.get("repost_count", 0))))
        comments = float(post.get("comments", post.get("comment_count", 0)))
        eng = likes + 2.0 * shares + 1.5 * comments
    else:
        eng = float(eng)
    eng = max(0.0, eng)
    eng_p99 = max(1.0, float(c.get("eng_p99", c.get("viral_threshold", 5000))))
    pop_ratio = math.log(1.0 + eng) / math.log(1.0 + eng_p99)
    pop_term = min(1.0, max(0.0, pop_ratio))

    # 3. Echo chamber term: gamma_echo * (1 + cos(e_i, e_j)) / 2
    agent_embed = agent.get("embedding")
    post_embed = post.get("embedding")
    if agent_embed is not None and post_embed is not None:
        cos_sim = _compute_cosine_similarity(agent_embed, post_embed)
    elif "alignment" in post:
        cos_sim = float(post.get("alignment", 0.0))
    elif "opinion_score" in agent and ("mean_opinion" in post or "opinion_score" in post):
        post_op = post.get("mean_opinion", post.get("opinion_score", 0.0))
        agent_op = agent.get("opinion_score", 0.0)
        cos_sim = _compute_cosine_similarity(agent_op, post_op)
    else:
        cos_sim = 0.0  # Netral
    echo_term = (1.0 + max(-1.0, min(1.0, cos_sim))) / 2.0

    score = (lambda_rec * recency_term) + (effective_beta_pop * pop_term) + (gamma_echo * echo_term)

    # 4. Efek relevansi topik (opsional bila agent menyediakan topic_overlap)
    if "topic_overlap" in agent or "relevance" in post:
        rel = float(agent.get("topic_overlap", post.get("relevance", 0.5)))
        score += relevance_weight * rel

    return float(score)

def is_viral(platform: str, post: dict) -> bool:
    return post.get("engagement", 0) >= get_platform_characteristics(platform)["viral_threshold"]


# ============ LANGKAH 5: ALGORITMA PERINGKAT REDDIT & TWITTER (NOTION DOKUMEN #7) ============
def compute_wilson_score(upvotes: int, downvotes: int, z: float = 1.28155) -> float:
    """
    Menghitung lower bound interval Wilson Score (80% confidence interval, z=1.28155)
    untuk penentuan Best Comment Reddit sesuai Dokumen Notion #7.
    W(u, d, z) = (p_hat + z^2/(2n) - z*sqrt((p_hat*(1-p_hat)/n) + z^2/(4n^2))) / (1 + z^2/n)
    """
    n = int(upvotes) + int(downvotes)
    if n <= 0:
        return 0.0
    p_hat = float(upvotes) / float(n)
    z2 = float(z) * float(z)
    denominator = 1.0 + (z2 / float(n))
    center = p_hat + (z2 / (2.0 * float(n)))
    variance_term = (p_hat * (1.0 - p_hat) / float(n)) + (z2 / (4.0 * float(n) * float(n)))
    spread = float(z) * math.sqrt(max(0.0, variance_term))
    score = (center - spread) / denominator
    return float(max(0.0, min(1.0, score)))


def compute_reddit_hot_score(
    upvotes: int,
    downvotes: int,
    post_time_epoch: float,
    epoch_start: float = 1134028003.0
) -> float:
    """
    Reddit Hot Ranking Algorithm sesuai Dokumen Notion #7:
    Score_hot = sign(U - D) * log10(max(|U - D|, 1)) + (t - t0) / 45000
    """
    u = int(upvotes)
    d = int(downvotes)
    s = u - d
    order = math.log10(max(abs(s), 1))
    sign = 1 if s > 0 else (-1 if s < 0 else 0)
    seconds = float(post_time_epoch) - float(epoch_start)
    return float(round(sign * order + (seconds / 45000.0), 7))

