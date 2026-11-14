"""Load and index all platforms/*.yaml PlatformSpecs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from mirofish.core.spec import PlatformSpec


class PlatformRegistry:
    """Registry of PlatformSpecs keyed by ``platform_id``.

    Invalid specs are not fatal at load time; their errors are surfaced via
    :meth:`validate_all` and :attr:`errors`.
    """

    def __init__(self, platforms_dir: str | Path) -> None:
        self.platforms_dir = Path(platforms_dir)
        self._specs: dict[str, PlatformSpec] = {}
        self._errors: dict[str, list[str]] = {}
        self._load()

    # -- loading ------------------------------------------------------------

    def _load(self) -> None:
        if not self.platforms_dir.is_dir():
            raise FileNotFoundError(f"platforms dir not found: {self.platforms_dir}")
        for path in sorted(self.platforms_dir.glob("*.yaml")):
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    data: Any = yaml.safe_load(fh)
                spec = PlatformSpec.from_dict(data)
            except (yaml.YAMLError, ValueError, ValidationError) as exc:
                self._errors[path.stem] = [str(exc)]
                continue
            self._specs[spec.platform_id] = spec

    # -- access -------------------------------------------------------------

    @property
    def errors(self) -> dict[str, list[str]]:
        """Load/validation errors keyed by file stem (for invalid specs)."""
        return dict(self._errors)

    def get(self, platform_id: str) -> PlatformSpec:
        """Return the spec for ``platform_id``; raises KeyError if absent/invalid."""
        if platform_id in self._errors:
            raise KeyError(f"platform spec '{platform_id}' failed validation: {self._errors[platform_id]}")
        try:
            return self._specs[platform_id]
        except KeyError:
            raise KeyError(f"unknown platform_id: {platform_id!r}") from None

    def list(self) -> list[PlatformSpec]:
        """All successfully loaded specs, sorted by platform_id."""
        return [self._specs[k] for k in sorted(self._specs)]

    def validate_all(self) -> dict[str, list[str]]:
        """Re-validate every YAML file; returns {platform_id_or_stem: [errors]}.

        Empty dict means every spec is valid.
        """
        results: dict[str, list[str]] = {}
        for path in sorted(self.platforms_dir.glob("*.yaml")):
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    data: Any = yaml.safe_load(fh)
                spec = PlatformSpec.from_dict(data)
            except (yaml.YAMLError, ValueError, ValidationError) as exc:
                results[path.stem] = [str(exc)]
                continue
            # Cross-file duplicate platform_id check
            dup = [p for p in self.platforms_dir.glob("*.yaml") if p != path]
            for other in dup:
                try:
                    with open(other, "r", encoding="utf-8") as fh:
                        odata = yaml.safe_load(fh)
                    if isinstance(odata, dict) and odata.get("platform_id") == spec.platform_id:
                        results.setdefault(path.stem, []).append(
                            f"duplicate platform_id {spec.platform_id!r} also in {other.name}"
                        )
                except Exception:
                    pass  # the other file's own errors are reported separately
        return results
