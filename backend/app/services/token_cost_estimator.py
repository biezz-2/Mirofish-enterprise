"""
MiroFish Enterprise - Token Budget & Cost Estimator (Subagent F)
Mengestimasi kebutuhan token simulasi multi-agent dan biaya komputasi
berdasarkan baseline empiris OASIS (~335.6k token per 100 agen / 10 ronde),
alokasi 4 fase, dan model pricing multi-provider (Claude 3.5 Sonnet, GPT-4o, Llama 3).
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional

# Baseline Empiris OASIS: 100 agen, 10 ronde interaksi, 1 platform, 4096 context
OASIS_BASELINE_TOKENS: int = 335_600
OASIS_BASELINE_AGENTS: int = 100
OASIS_BASELINE_ROUNDS: int = 10
OASIS_BASELINE_PLATFORMS: int = 1
OASIS_BASELINE_CONTEXT_WINDOW: int = 4096

# Nilai Tukar Default USD -> IDR
DEFAULT_USD_TO_IDR: float = 16_000.0

# Alokasi Token Rekomendasi per Fase (Total 100%)
PHASE_ALLOCATION_PERCENTAGES: Dict[str, float] = {
    "step_0_research": 0.15,
    "step_1_graph": 0.20,
    "step_2_simulation": 0.50,
    "step_3_report": 0.15,
}

# Model Pricing per 1 Juta Token (Input / Output / Blended 75% Input & 25% Output)
MODEL_PRICING: Dict[str, Dict[str, Any]] = {
    "claude-3-5-sonnet": {
        "name": "Claude 3.5 Sonnet",
        "input_per_m": 3.00,
        "output_per_m": 15.00,
        "blended_per_m": 6.00,
        "provider": "Anthropic",
    },
    "gpt-4o": {
        "name": "GPT-4o",
        "input_per_m": 2.50,
        "output_per_m": 10.00,
        "blended_per_m": 4.375,
        "provider": "OpenAI",
    },
    "llama-3-local": {
        "name": "Llama 3 (Local / Open-Source)",
        "input_per_m": 0.00,
        "output_per_m": 0.00,
        "blended_per_m": 0.00,
        "provider": "Local/Self-Hosted",
    },
}

MODEL_ALIASES: Dict[str, str] = {
    "claude": "claude-3-5-sonnet",
    "claude-3-5-sonnet": "claude-3-5-sonnet",
    "claude-3.5-sonnet": "claude-3-5-sonnet",
    "sonnet": "claude-3-5-sonnet",
    "gpt-4o": "gpt-4o",
    "gpt4o": "gpt-4o",
    "openai": "gpt-4o",
    "llama": "llama-3-local",
    "llama-3": "llama-3-local",
    "llama3": "llama-3-local",
    "llama-3-local": "llama-3-local",
    "local": "llama-3-local",
    "open-source": "llama-3-local",
}


@dataclass
class CostEstimateResult:
    """Hasil kalkulasi estimasi biaya untuk model tertentu."""
    model_key: str
    model_name: str
    tokens: int
    cost_usd: float
    cost_idr: float
    usd_to_idr_rate: float
    blended_rate_per_m: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TokenBudgetReport:
    """Laporan terpadu kalkulasi token budget, alokasi fase, biaya, dan status batas limit."""
    num_agents: int
    rounds: int
    platform_count: int
    context_window_size: int
    estimated_tokens: int
    phase_allocations: Dict[str, int]
    cost_usd: float
    cost_idr: float
    model_key: str
    model_name: str
    budget_limit: Optional[int] = None
    is_over_budget: bool = False
    warning: Optional[str] = None
    epistemic_status: str = "[VERIFIED]"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TokenCostEstimator:
    """
    Engine estimasi token dan biaya komputasi MiroFish Enterprise.
    ponytail: linear parameter scaling without non-linear interaction terms; upgrade to empirical polynomial fit if OASIS logs provide variance data.
    """

    def __init__(self, default_usd_to_idr: float = DEFAULT_USD_TO_IDR):
        self.usd_to_idr = default_usd_to_idr

    @staticmethod
    def normalize_model_key(model: str) -> str:
        """Menormalisasi nama model atau alias ke kunci canonical."""
        key = model.strip().lower()
        if key in MODEL_ALIASES:
            return MODEL_ALIASES[key]
        if key in MODEL_PRICING:
            return key
        raise ValueError(f"Model '{model}' tidak dikenal. Pilihan: {list(MODEL_PRICING.keys())}")

    @classmethod
    def estimate_tokens(
        cls,
        num_agents: int = 100,
        rounds: int = 10,
        platform_count: int = 1,
        context_window_size: int = 4096
    ) -> int:
        """
        Menghitung estimasi token berdasarkan parameter simulasi dan baseline empiris OASIS.
        Baseline: 100 agen x 10 ronde x 1 platform x 4096 context = ~335.6k token.
        """
        if num_agents <= 0:
            raise ValueError(f"num_agents harus > 0 (diberikan: {num_agents})")
        if rounds <= 0:
            raise ValueError(f"rounds harus > 0 (diberikan: {rounds})")
        if platform_count <= 0:
            raise ValueError(f"platform_count harus > 0 (diberikan: {platform_count})")
        if context_window_size <= 0:
            raise ValueError(f"context_window_size harus > 0 (diberikan: {context_window_size})")

        agent_ratio = num_agents / OASIS_BASELINE_AGENTS
        round_ratio = rounds / OASIS_BASELINE_ROUNDS
        platform_ratio = platform_count / OASIS_BASELINE_PLATFORMS
        context_ratio = context_window_size / OASIS_BASELINE_CONTEXT_WINDOW

        raw_estimate = (
            OASIS_BASELINE_TOKENS
            * agent_ratio
            * round_ratio
            * platform_ratio
            * context_ratio
        )
        return int(round(raw_estimate))

    def estimate_cost(
        self,
        tokens: int,
        model: str = "claude-3-5-sonnet",
        usd_to_idr: Optional[float] = None
    ) -> CostEstimateResult:
        """
        Menghitung estimasi biaya USD dan IDR berdasarkan model pricing.
        """
        if tokens < 0:
            raise ValueError(f"tokens tidak boleh negatif (diberikan: {tokens})")

        m_key = self.normalize_model_key(model)
        pricing = MODEL_PRICING[m_key]
        rate_m = pricing["blended_per_m"]
        rate_idr = usd_to_idr if usd_to_idr is not None else self.usd_to_idr

        cost_usd = round((tokens / 1_000_000.0) * rate_m, 4)
        cost_idr = round(cost_usd * rate_idr, 2)

        return CostEstimateResult(
            model_key=m_key,
            model_name=pricing["name"],
            tokens=tokens,
            cost_usd=cost_usd,
            cost_idr=cost_idr,
            usd_to_idr_rate=rate_idr,
            blended_rate_per_m=rate_m
        )

    @staticmethod
    def allocate_phase_tokens(total_tokens: int) -> Dict[str, int]:
        """
        Merekomendasikan alokasi token per fase:
        - Step 0 Research: 15%
        - Step 1 Graph: 20%
        - Step 2 Simulation: 50%
        - Step 3 Report: 15%
        """
        if total_tokens < 0:
            raise ValueError(f"total_tokens tidak boleh negatif (diberikan: {total_tokens})")

        allocations: Dict[str, int] = {}
        allocated_sum = 0
        for phase, pct in PHASE_ALLOCATION_PERCENTAGES.items():
            amount = int(round(total_tokens * pct))
            allocations[phase] = amount
            allocated_sum += amount

        # Koreksi pembulatan integer agar total sama persis dengan total_tokens
        diff = total_tokens - allocated_sum
        if diff != 0:
            allocations["step_2_simulation"] += diff

        return allocations

    @staticmethod
    def check_budget_limit(estimated_tokens: int, budget_limit: int) -> Dict[str, Any]:
        """
        Mengecek batas maksimum budget dan menghasilkan over-budget warning jika terlampaui.
        """
        if not isinstance(estimated_tokens, (int, float)):
            raise TypeError(f"estimated_tokens harus berupa int atau float (diberikan: {type(estimated_tokens).__name__})")
        if not isinstance(budget_limit, (int, float)):
            raise TypeError(f"budget_limit harus berupa int atau float (diberikan: {type(budget_limit).__name__})")
        if budget_limit <= 0:
            raise ValueError(f"budget_limit harus > 0 (diberikan: {budget_limit})")

        is_over = estimated_tokens > budget_limit
        excess_tokens = max(0, estimated_tokens - budget_limit)
        excess_pct = round((excess_tokens / budget_limit) * 100.0, 2)

        warning: Optional[str] = None
        if is_over:
            warning = (
                f"[WARNING] Over-budget terdeteksi! Estimasi token ({estimated_tokens:,}) "
                f"melebihi batas alokasi ({budget_limit:,}) sebesar {excess_tokens:,} token "
                f"(+{excess_pct}%)."
            )

        return {
            "is_over_budget": is_over,
            "status": "OVER_BUDGET" if is_over else "WITHIN_BUDGET",
            "estimated_tokens": estimated_tokens,
            "budget_limit": budget_limit,
            "excess_tokens": excess_tokens,
            "excess_percentage": excess_pct,
            "warning": warning,
        }

    def generate_budget_report(
        self,
        num_agents: int = 100,
        rounds: int = 10,
        platform_count: int = 1,
        context_window_size: int = 4096,
        model: str = "claude-3-5-sonnet",
        budget_limit: Optional[int] = None,
        usd_to_idr: Optional[float] = None
    ) -> TokenBudgetReport:
        """
        Menghasilkan laporan lengkap: estimasi token, alokasi per fase, biaya, dan validasi budget.
        """
        tokens = self.estimate_tokens(
            num_agents=num_agents,
            rounds=rounds,
            platform_count=platform_count,
            context_window_size=context_window_size
        )
        cost_res = self.estimate_cost(tokens=tokens, model=model, usd_to_idr=usd_to_idr)
        allocations = self.allocate_phase_tokens(tokens)

        is_over = False
        warning: Optional[str] = None
        if budget_limit is not None:
            budget_check = self.check_budget_limit(tokens, budget_limit)
            is_over = budget_check["is_over_budget"]
            warning = budget_check["warning"]

        return TokenBudgetReport(
            num_agents=num_agents,
            rounds=rounds,
            platform_count=platform_count,
            context_window_size=context_window_size,
            estimated_tokens=tokens,
            phase_allocations=allocations,
            cost_usd=cost_res.cost_usd,
            cost_idr=cost_res.cost_idr,
            model_key=cost_res.model_key,
            model_name=cost_res.model_name,
            budget_limit=budget_limit,
            is_over_budget=is_over,
            warning=warning,
            epistemic_status="[VERIFIED]"
        )


# Modul helper fungsi instan untuk kompatibilitas fungsional
def estimate_simulation_tokens(
    num_agents: int = 100,
    rounds: int = 10,
    platform_count: int = 1,
    context_window_size: int = 4096
) -> int:
    return TokenCostEstimator.estimate_tokens(
        num_agents=num_agents,
        rounds=rounds,
        platform_count=platform_count,
        context_window_size=context_window_size
    )


def estimate_simulation_cost(
    tokens: int,
    model: str = "claude-3-5-sonnet",
    usd_to_idr: float = DEFAULT_USD_TO_IDR
) -> CostEstimateResult:
    estimator = TokenCostEstimator(default_usd_to_idr=usd_to_idr)
    return estimator.estimate_cost(tokens=tokens, model=model)


def allocate_simulation_phase_tokens(total_tokens: int) -> Dict[str, int]:
    return TokenCostEstimator.allocate_phase_tokens(total_tokens)


def check_simulation_budget_warning(
    estimated_tokens: int,
    budget_limit: int
) -> Dict[str, Any]:
    return TokenCostEstimator.check_budget_limit(estimated_tokens, budget_limit)
