# backend/app/services/simulation/platform_spec_service.py
"""
PlatformSpec Service — jembatan antara spesifikasi platform deklaratif
(`backend/platforms/*.yaml`, paket `mirofish.core`) dan pipeline simulasi
enterprise yang sudah ada (PlatformProfileStore / FeedPipeline).

Kontrak:
- ``list_platforms()``      : semua platform_id yang tervalidasi schema.
- ``get_spec(platform_id)`` : PlatformSpec pydantic utuh.
- ``validate_all()``        : hasil validasi semantik per file YAML.
- ``to_pipeline_profile()`` : adaptasi PlatformSpec -> dict profil yang
  dipahami ``PlatformProfileStore``/``FeedPipeline`` (field yang tidak dapat
  dipetakan secara jujur dibiarkan fallback; data fidelitas tinggi tetap
  tersedia di bawah kunci ``platform_spec``).

Catatan kejujuran: ``FeedPipeline`` saat ini masih memakai bobot ``p_*``
internal; bobot ``signal_schema`` PlatformSpec adalah parameter kalibrasi
(dokumentasi/inferred/prior) dan belum menjadi scorer produksi.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from mirofish.core.registry import PlatformRegistry
from mirofish.core.spec import PlatformSpec

# backend/app/services/simulation/platform_spec_service.py -> backend/
BACKEND_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SPECS_DIR = BACKEND_ROOT / "platforms"


class PlatformSpecService:
    """Akses terpusat ke registry PlatformSpec enterprise."""

    def __init__(self, specs_dir: Optional[Path] = None):
        self.specs_dir = Path(specs_dir) if specs_dir else DEFAULT_SPECS_DIR
        self._registry = PlatformRegistry(self.specs_dir)

    # -- registry passthrough ----------------------------------------------

    @property
    def registry(self) -> PlatformRegistry:
        return self._registry

    def list_platforms(self) -> List[str]:
        return sorted(spec.platform_id for spec in self._registry.list())

    def get_spec(self, platform_id: str) -> PlatformSpec:
        return self._registry.get(platform_id)

    def validate_all(self) -> Dict[str, List[str]]:
        return self._registry.validate_all()

    # -- adaptation ---------------------------------------------------------

    def to_pipeline_profile(self, platform_id: str) -> Dict[str, Any]:
        """Adapt PlatformSpec menjadi dict profil untuk FeedPipeline.

        Hanya field yang pemetaannya jelas yang diisi; selebihnya pipeline
        memakai fallback internalnya sendiri. Seluruh spec tetap disertakan
        di ``platform_spec`` untuk konsumen yang butuh fidelitas penuh.
        """
        spec = self.get_spec(platform_id)
        profile: Dict[str, Any] = {
            "platform": spec.platform_id,
            "version": spec.spec_version,
            "display_name": spec.display_name,
            "archetype": spec.archetype,
            "privacy_tier": spec.privacy_tier,
            "delivery_mode": spec.delivery_mode,
            "spec_source": "platformspec",
        }

        # content constraints -> regimes.regular (dipakai scorer/filter)
        if spec.content_constraints is not None:
            max_chars = spec.content_constraints.max_length_chars
            if max_chars:
                profile["regimes"] = {"regular": {"max_chars": max_chars}}

        # feed signal schema -> metadata bobot (belum dipakai ScorerStage p_*)
        if spec.feed is not None and spec.feed.signal_schema:
            profile["signal_schema"] = [
                s.model_dump(exclude_none=True) for s in spec.feed.signal_schema
            ]
            profile["feed_kind"] = spec.feed.kind
            scorer = spec.feed.scorer
            if scorer is not None:
                plugin = scorer.get("plugin") if isinstance(scorer, dict) \
                    else getattr(scorer, "plugin", None)
                if plugin:
                    profile["scorer_plugin"] = plugin

        # delivery semantics untuk platform push/private
        if spec.delivery_mode == "push" or spec.privacy_tier == "private":
            profile["delivery"] = {"mode": spec.delivery_mode, "privacy_tier": spec.privacy_tier}

        # raw spec untuk konsumen lanjutan
        profile["platform_spec"] = spec.model_dump(exclude_none=True)
        return profile
