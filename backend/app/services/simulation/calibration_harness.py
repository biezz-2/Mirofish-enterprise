# backend/app/services/simulation/calibration_harness.py
"""
Calibration Harness: Stylized Facts Validator
Memvalidasi apakah pola dinamika simulasi merefleksikan hukum empiris media sosial:
1. Aturan 90-9-1 (90% Lurker pasif, 9% Kurator/Liker, 1% Kreator aktif)
2. Distribusi Cascade Heavy-Tailed (Pareto / Power-Law alpha ~ 1.2 - 3.0)
3. Siklus Diurnal (Puncak jam makan siang 12-13 & malam 19-22, palung dini hari 01-05).
"""
from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any, Dict, List, Optional


@dataclass
class CalibrationReport:
    """Hasil evaluasi stylized facts simulasi."""
    passed_all: bool
    rule_90_9_1_passed: bool
    heavy_tail_passed: bool
    diurnal_cycle_passed: bool
    metrics: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)


class StylizedFactsValidator:
    """Validator stylized facts makro sosiologis."""

    def __init__(
        self,
        lurker_range: tuple = (0.80, 0.96),
        curator_range: tuple = (0.04, 0.18),
        creator_range: tuple = (0.005, 0.06),
    ):
        self.lurker_range = lurker_range
        self.curator_range = curator_range
        self.creator_range = creator_range

    def validate_90_9_1_rule(self, agent_action_counts: Dict[str, Dict[str, int]]) -> Dict[str, Any]:
        """Klasifikasikan agen ke dalam: Lurker (0 aksi aktif), Kurator (hanya like/repost), Kreator (post/komentar)."""
        total_agents = len(agent_action_counts)
        if total_agents == 0:
            return {"passed": False, "reason": "No agents found"}

        lurkers = 0
        curators = 0
        creators = 0

        for _, acts in agent_action_counts.items():
            creates = acts.get("post", 0) + acts.get("comment", 0)
            curates = acts.get("like", 0) + acts.get("repost", 0) + acts.get("upvote", 0)

            if creates > 0:
                creators += 1
            elif curates > 0:
                curators += 1
            else:
                lurkers += 1

        r_lurker = lurkers / total_agents
        r_curator = curators / total_agents
        r_creator = creators / total_agents

        passed = (
            self.lurker_range[0] <= r_lurker <= self.lurker_range[1] and
            self.curator_range[0] <= r_curator <= self.curator_range[1] and
            self.creator_range[0] <= r_creator <= self.creator_range[1]
        )

        return {
            "passed": passed,
            "ratios": {
                "lurker": round(r_lurker, 4),
                "curator": round(r_curator, 4),
                "creator": round(r_creator, 4),
            },
            "counts": {"lurkers": lurkers, "curators": curators, "creators": creators, "total": total_agents},
        }

    def validate_heavy_tail(self, cascade_sizes: List[int]) -> Dict[str, Any]:
        """Uji apakah distribusi ukuran cascade memiliki heavy tail menggunakan MLE estimasi eksponen Pareto."""
        valid_sizes = [s for s in cascade_sizes if s >= 1]
        n = len(valid_sizes)
        if n < 10:
            return {"passed": False, "reason": "Sampel cascade terlalu sedikit (butuh >= 10)", "alpha": None}

        x_min = min(valid_sizes)
        # MLE estimator untuk eksponen Pareto: 1 + n / sum(ln(x_i / x_min))
        log_sum = sum(math.log(x / x_min) for x in valid_sizes if x > x_min)

        if log_sum <= 0:
            return {"passed": False, "reason": "Tidak ada variasi ukuran cascade", "alpha": None}

        # Pareto alpha
        alpha = 1.0 + (n / log_sum)

        # Nilai tipikal media sosial berkisar antara 1.2 hingga 3.5
        passed = 1.1 <= alpha <= 3.8

        return {
            "passed": passed,
            "alpha": round(alpha, 3),
            "sample_size": n,
            "max_cascade": max(valid_sizes),
        }

    def validate_diurnal_cycle(self, event_hours: List[int]) -> Dict[str, Any]:
        """Uji apakah terdapat pola diurnal: puncak siang (11-14) / malam (18-22) dan penurunan dini hari (01-05)."""
        if len(event_hours) < 20:
            return {"passed": False, "reason": "Data jam event terlalu sedikit"}

        hour_counts = [0] * 24
        for h in event_hours:
            if 0 <= h < 24:
                hour_counts[h] += 1

        total = len(event_hours)
        rates = [c / total for c in hour_counts]

        # Rata-rata jam malam puncak (19-22) dan siang (12-13)
        peak_night = sum(rates[19:23]) / 4.0
        peak_lunch = sum(rates[12:14]) / 2.0
        valley_night = sum(rates[1:6]) / 5.0

        # Puncak harus lebih tinggi dibanding palung dini hari
        has_night_peak = peak_night > valley_night * 1.3
        has_lunch_peak = peak_lunch > valley_night * 1.1
        passed = has_night_peak and has_lunch_peak

        return {
            "passed": passed,
            "peak_night_avg": round(peak_night, 4),
            "peak_lunch_avg": round(peak_lunch, 4),
            "valley_night_avg": round(valley_night, 4),
        }

    def validate_simulation_run(
        self,
        agent_actions: Dict[str, Dict[str, int]],
        cascade_sizes: List[int],
        event_hours: List[int],
    ) -> CalibrationReport:
        """Evaluasi gabungan seluruh stylized facts."""
        r_90_9_1 = self.validate_90_9_1_rule(agent_actions)
        r_cascade = self.validate_heavy_tail(cascade_sizes)
        r_diurnal = self.validate_diurnal_cycle(event_hours)

        passed_all = (
            bool(r_90_9_1.get("passed")) and
            bool(r_cascade.get("passed")) and
            bool(r_diurnal.get("passed"))
        )

        warnings = []
        if not r_90_9_1.get("passed"):
            warnings.append(f"Aturan 90-9-1 gagal: {r_90_9_1}")
        if not r_cascade.get("passed"):
            warnings.append(f"Heavy-tail cascade gagal: {r_cascade}")
        if not r_diurnal.get("passed"):
            warnings.append(f"Siklus diurnal gagal: {r_diurnal}")

        return CalibrationReport(
            passed_all=passed_all,
            rule_90_9_1_passed=bool(r_90_9_1.get("passed")),
            heavy_tail_passed=bool(r_cascade.get("passed")),
            diurnal_cycle_passed=bool(r_diurnal.get("passed")),
            metrics={
                "rule_90_9_1": r_90_9_1,
                "cascade": r_cascade,
                "diurnal": r_diurnal,
            },
            warnings=warnings,
        )
