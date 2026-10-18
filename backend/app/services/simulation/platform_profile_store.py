# backend/app/services/simulation/platform_profile_store.py
"""
Platform Profile Store dengan dukungan versioned YAML dan fallback terstruktur.
Memuat profil platform dari YAML di folder profiles/, atau fallback data statis.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml

DEFAULT_PROFILES_DIR = Path(__file__).parent / "profiles"

# Fallback terstruktur jika YAML tidak ada di disk
STRUCTURED_FALLBACKS: Dict[str, Dict[str, Any]] = {
    "x": {
        "platform": "x",
        "version": "2026-10",
        "unified_brand": "X (formerly Twitter)",
        "aliases": ["twitter", "x_twitter"],
        "regimes": {
            "regular": {"max_chars": 280, "media_limit": 4},
            "premium": {"max_chars": 25000, "media_limit": 10},
        },
        "timelines": {
            "for_you": {
                "in_network_ratio": 0.50,
                "out_network_ratio": 0.50,
                "recency_weight": 0.70,
                "popularity_weight": 0.50,
                "relevance_weight": 0.40,
                "echo_chamber_strength": 0.50,
            },
            "following": {
                "in_network_ratio": 1.00,
                "out_network_ratio": 0.00,
                "recency_weight": 0.95,
                "popularity_weight": 0.05,
                "relevance_weight": 0.10,
                "echo_chamber_strength": 0.60,
            },
        },
        "weights": {"p_like": 0.25, "p_retweet": 0.35, "p_reply": 0.25, "p_dwell": 0.15},
        "safety": {"toxic_threshold": 0.75, "frequency_cap_author_per_slate": 2},
    },
    "reddit": {
        "platform": "reddit",
        "version": "2026-10",
        "karma_threshold": 50,
        "upvote_downvote_ratio_damping": 0.85,
        "subreddit_hierarchy": {"enabled": True, "depth_limit": 8, "min_account_age_days": 7},
        "weights": {"p_like": 0.15, "p_retweet": 0.05, "p_reply": 0.55, "p_dwell": 0.25},
        "regimes": {"regular": {"max_chars": 40000, "comment_max_chars": 10000}},
        "safety": {"toxic_threshold": 0.65, "frequency_cap_author_per_slate": 3},
    },
    "tiktok": {
        "platform": "tiktok",
        "version": "2026-10",
        "watch_time_duration_weight": 0.50,
        "completion_rate_weight": 0.35,
        "algorithmic_viral": {"threshold_views": 10000, "retention_gate": 0.70, "viral_multiplier": 1.50},
        "weights": {"p_like": 0.20, "p_retweet": 0.20, "p_reply": 0.10, "p_dwell": 0.50},
        "regimes": {"regular": {"max_chars": 2200, "comment_max_chars": 150}},
        "safety": {"toxic_threshold": 0.70, "frequency_cap_author_per_slate": 1},
    },
    "meta": {
        "platform": "meta",
        "version": "2026-10",
        "sub_platforms": ["instagram", "facebook", "threads"],
        "close_network_weight": 0.65,
        "reel_distribution_ratio": 0.45,
        "weights": {"p_like": 0.35, "p_retweet": 0.20, "p_reply": 0.30, "p_dwell": 0.15},
        "regimes": {"instagram": {"max_chars": 2200}, "facebook": {"max_chars": 63206}, "threads": {"max_chars": 500}},
        "safety": {"toxic_threshold": 0.70, "frequency_cap_author_per_slate": 2},
    },
}

ALIAS_MAP: Dict[str, str] = {
    "twitter": "x",
    "x_twitter": "x",
    "instagram": "meta",
    "facebook": "meta",
    "threads": "meta",
}


class PlatformProfileStore:
    """Store untuk profil platform berbasis file YAML dan fallback otomatis."""

    def __init__(self, profiles_dir: Optional[Path] = None):
        self.profiles_dir = profiles_dir or DEFAULT_PROFILES_DIR
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _resolve_platform_key(self, platform: str) -> str:
        p_lower = platform.lower().strip()
        return ALIAS_MAP.get(p_lower, p_lower)

    def get_profile(self, platform: str, version: str = "2026-10") -> Dict[str, Any]:
        """Ambil spesifikasi profil platform versioned."""
        key = self._resolve_platform_key(platform)
        cache_id = f"{key}@{version}"

        if cache_id in self._cache:
            return self._cache[cache_id]

        file_path = self.profiles_dir / f"{key}@{version}.yaml"
        if file_path.exists() and file_path.is_file():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if isinstance(data, dict):
                        self._cache[cache_id] = data
                        return data
            except Exception:
                pass  # ponytail: fallback ke static dictionary saat YAML parse gagal

        # Fallback terstruktur
        if key in STRUCTURED_FALLBACKS:
            fallback = STRUCTURED_FALLBACKS[key].copy()
            self._cache[cache_id] = fallback
            return fallback

        # Default generic fallback
        generic = {
            "platform": key,
            "version": version,
            "weights": {"p_like": 0.3, "p_retweet": 0.3, "p_reply": 0.3, "p_dwell": 0.1},
            "regimes": {"regular": {"max_chars": 1000}},
            "safety": {"toxic_threshold": 0.70, "frequency_cap_author_per_slate": 3},
        }
        self._cache[cache_id] = generic
        return generic

    def list_profiles(self) -> List[str]:
        """Daftar platform dan versi yang tersedia."""
        found = set(STRUCTURED_FALLBACKS.keys())
        if self.profiles_dir.exists():
            for p in self.profiles_dir.glob("*@*.yaml"):
                found.add(p.stem)
        return sorted(list(found))
