# backend/app/services/platform_behaviors.py
"""
Karakteristik dan perilaku platform untuk simulasi multi-platform MiroFish.
Seluruh platform dimodelkan sebagai DATA, bukan fork kode.
"""
from dataclasses import dataclass, field
from typing import Dict, List

# ============ LANGKAH 1: KARAKTERISTIK PLATFORM ============
PLATFORM_CHARACTERISTICS: Dict[str, dict] = {
    "twitter": {
        "display_name": "Twitter", "recency_weight": 0.8, "popularity_weight": 0.5,
        "relevance_weight": 0.4, "echo_chamber_strength": 0.5,
        "viral_threshold": 5000, "max_content_length": 280,
        "interaction_style": "ephemeral", "base_activity_multiplier": 1.0,
    },
    "x": {
        "display_name": "X", "recency_weight": 0.8, "popularity_weight": 0.5,
        "relevance_weight": 0.4, "echo_chamber_strength": 0.5,
        "viral_threshold": 8000, "max_content_length": 25000,
        "interaction_style": "ephemeral_long", "base_activity_multiplier": 0.9,
    },
    "reddit": {
        "display_name": "Reddit", "recency_weight": 0.4, "popularity_weight": 0.8,
        "relevance_weight": 0.5, "echo_chamber_strength": 0.7,
        "viral_threshold": 300, "max_content_length": 40000,
        "interaction_style": "persistent_deep", "base_activity_multiplier": 0.8,
    },
    "tiktok": {
        "display_name": "TikTok", "recency_weight": 0.6, "popularity_weight": 0.9,
        "relevance_weight": 0.7, "echo_chamber_strength": 0.4,
        "viral_threshold": 50000, "max_content_length": 150,
        "interaction_style": "algorithmic_viral", "base_activity_multiplier": 1.3,
    },
    "instagram": {
        "display_name": "Instagram", "recency_weight": 0.5, "popularity_weight": 0.7,
        "relevance_weight": 0.6, "echo_chamber_strength": 0.5,
        "viral_threshold": 10000, "max_content_length": 2200,
        "interaction_style": "visual_follower", "base_activity_multiplier": 1.0,
    },
    "facebook": {
        "display_name": "Facebook", "recency_weight": 0.4, "popularity_weight": 0.6,
        "relevance_weight": 0.5, "echo_chamber_strength": 0.8,
        "viral_threshold": 8000, "max_content_length": 63000,
        "interaction_style": "broad_network", "base_activity_multiplier": 0.7,
    },
    "threads": {
        "display_name": "Threads", "recency_weight": 0.7, "popularity_weight": 0.5,
        "relevance_weight": 0.4, "echo_chamber_strength": 0.5,
        "viral_threshold": 5000, "max_content_length": 500,
        "interaction_style": "conversational", "base_activity_multiplier": 0.8,
    },
}

DEFAULT_PLATFORMS = ["twitter", "reddit"]  # kompatibilitas mundur

def get_platform_characteristics(platform: str) -> dict:
    if platform not in PLATFORM_CHARACTERISTICS:
        raise ValueError(f"Platform tidak dikenal: {platform}")
    return PLATFORM_CHARACTERISTICS[platform]

# ============ LANGKAH 4: PERILAKU PLATFORM ============
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
        if self.platform == "twitter":
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
        else:  # x, instagram, threads — turunan parametrik
            self.agent_type_distribution = {"individual": 0.65, "public_figure": 0.25, "institutional": 0.1}
            self.action_probabilities = {"post": 0.25, "repost": 0.25, "comment": 0.25, "like": 0.25}
            self.content_style = "percakapan teks ringan"
            self.peak_hours = [9, 18, 21]

def get_platform_behavior(platform: str) -> PlatformBehavior:
    return PlatformBehavior(platform=platform, characteristics=get_platform_characteristics(platform))

# ============ ALGORITMA REKOMENDASI PER PLATFORM ============
def compute_feed_score(platform: str, post: dict, agent: dict, current_hour: int) -> float:
    """Skor rekomendasi konten untuk agen pada platform tertentu."""
    c = get_platform_characteristics(platform)
    recency = 1.0 / (1.0 + post.get("age_hours", 0) ** c["recency_weight"])
    popularity = 1.0 + (post.get("engagement", 0) / max(c["viral_threshold"], 1)) ** 0.5
    relevance = agent.get("topic_overlap", 0.5)
    score = (c["recency_weight"] * recency
             + c["popularity_weight"] * popularity
             + c["relevance_weight"] * relevance)
    # efek echo chamber: bonus bila opini agen searah dengan mayoritas interaksi postingan
    if abs(agent.get("opinion_score", 0) - post.get("mean_opinion", 0)) < 0.3:
        score *= (1.0 + c["echo_chamber_strength"] * 0.5)
    return score

def is_viral(platform: str, post: dict) -> bool:
    return post.get("engagement", 0) >= get_platform_characteristics(platform)["viral_threshold"]
