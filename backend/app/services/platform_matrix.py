"""
MiroFish Enterprise 7-Platform Calibration Matrix (Agent 12: Divisi D)
Matriks Pembobotan Algoritmik untuk 7 Platform Unik (Menyelesaikan Celah P1 Master Plan):
1. X (Twitter)
2. Reddit
3. TikTok
4. Instagram
5. YouTube
6. LinkedIn
7. Threads
Menerapkan distribusi partisipasi Pareto 90-9-1 (90% lurker, 9% kurator/komentator, 1% kreator).
"""

from typing import Dict, Any, List
from pydantic import BaseModel, Field

class PlatformWeights(BaseModel):
    platform_name: str
    virality_decay_rate: float
    lurker_ratio: float = 0.90
    contributor_ratio: float = 0.09
    creator_ratio: float = 0.01
    comment_depth_weight: float
    visual_affinity: float
    echo_chamber_vulnerability: float

PLATFORM_CALIBRATION_DB: Dict[str, PlatformWeights] = {
    "x": PlatformWeights(
        platform_name="X (Twitter)",
        virality_decay_rate=0.85,
        lurker_ratio=0.88,
        contributor_ratio=0.10,
        creator_ratio=0.02,
        comment_depth_weight=0.6,
        visual_affinity=0.4,
        echo_chamber_vulnerability=0.82
    ),
    "reddit": PlatformWeights(
        platform_name="Reddit",
        virality_decay_rate=0.50,
        lurker_ratio=0.85,
        contributor_ratio=0.13,
        creator_ratio=0.02,
        comment_depth_weight=0.95,
        visual_affinity=0.3,
        echo_chamber_vulnerability=0.78
    ),
    "tiktok": PlatformWeights(
        platform_name="TikTok",
        virality_decay_rate=0.92,
        lurker_ratio=0.93,
        contributor_ratio=0.06,
        creator_ratio=0.01,
        comment_depth_weight=0.4,
        visual_affinity=1.0,
        echo_chamber_vulnerability=0.88
    ),
    "instagram": PlatformWeights(
        platform_name="Instagram",
        virality_decay_rate=0.75,
        lurker_ratio=0.90,
        contributor_ratio=0.08,
        creator_ratio=0.02,
        comment_depth_weight=0.5,
        visual_affinity=0.95,
        echo_chamber_vulnerability=0.75
    ),
    "youtube": PlatformWeights(
        platform_name="YouTube",
        virality_decay_rate=0.40,
        lurker_ratio=0.92,
        contributor_ratio=0.07,
        creator_ratio=0.01,
        comment_depth_weight=0.7,
        visual_affinity=0.9,
        echo_chamber_vulnerability=0.70
    ),
    "linkedin": PlatformWeights(
        platform_name="LinkedIn",
        virality_decay_rate=0.60,
        lurker_ratio=0.87,
        contributor_ratio=0.11,
        creator_ratio=0.02,
        comment_depth_weight=0.8,
        visual_affinity=0.5,
        echo_chamber_vulnerability=0.65
    ),
    "threads": PlatformWeights(
        platform_name="Threads",
        virality_decay_rate=0.80,
        lurker_ratio=0.89,
        contributor_ratio=0.10,
        creator_ratio=0.01,
        comment_depth_weight=0.65,
        visual_affinity=0.6,
        echo_chamber_vulnerability=0.72
    ),
}

class PlatformMatrixService:
    """Provides calibrated weights for multi-platform social simulations."""

    def get_platform_weights(self, platform_key: str) -> PlatformWeights:
        k = platform_key.lower().strip()
        if k in PLATFORM_CALIBRATION_DB:
            return PLATFORM_CALIBRATION_DB[k]
        # Default fallback
        return PLATFORM_CALIBRATION_DB["x"]

    def list_supported_platforms(self) -> List[str]:
        return list(PLATFORM_CALIBRATION_DB.keys())
