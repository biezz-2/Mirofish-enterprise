"""
Unit & Integration Test Suite untuk Token Budget & Cost Estimator (Subagent F)
Memvalidasi kalkulasi baseline empiris OASIS (~335.6k token / 100 agen / 10 ronde),
skala kecil (10 agen), alokasi 4 fase, pricing multi-model, dan deteksi over-budget.
"""

import pytest
from backend.app.services.token_cost_estimator import (
    TokenCostEstimator,
    TokenBudgetReport,
    CostEstimateResult,
    OASIS_BASELINE_TOKENS,
    OASIS_BASELINE_AGENTS,
    OASIS_BASELINE_ROUNDS,
    OASIS_BASELINE_PLATFORMS,
    OASIS_BASELINE_CONTEXT_WINDOW,
    DEFAULT_USD_TO_IDR,
    estimate_simulation_tokens,
    estimate_simulation_cost,
    allocate_simulation_phase_tokens,
    check_simulation_budget_warning,
)


class TestTokenCostEstimatorBaseline:
    """Uji kalkulasi estimasi token untuk skala OASIS standar dan skala kecil."""

    def test_oasis_standard_scale_100_agents(self):
        """Verifikasi bahwa 100 agen, 10 ronde menghasilkan persis baseline empiris OASIS (335.6k token)."""
        tokens = TokenCostEstimator.estimate_tokens(
            num_agents=100,
            rounds=10,
            platform_count=1,
            context_window_size=4096
        )
        assert tokens == OASIS_BASELINE_TOKENS
        assert tokens == 335_600

    def test_small_scale_10_agents(self):
        """Verifikasi bahwa skala kecil (10 agen, 10 ronde) menghasilkan persis 10% dari baseline OASIS (33,560 token)."""
        tokens = TokenCostEstimator.estimate_tokens(
            num_agents=10,
            rounds=10,
            platform_count=1,
            context_window_size=4096
        )
        assert tokens == 33_560
        assert tokens == int(OASIS_BASELINE_TOKENS * 0.1)

    def test_functional_helper_estimate_tokens(self):
        """Verifikasi modul helper fungsional menghasilkan nilai yang identik."""
        t_std = estimate_simulation_tokens(num_agents=100, rounds=10)
        assert t_std == 335_600

        t_small = estimate_simulation_tokens(num_agents=10, rounds=10)
        assert t_small == 33_560

    def test_parameter_scaling(self):
        """Verifikasi sensitivitas terhadap ronde, platform, dan ukuran context window."""
        # 20 ronde (2x baseline) -> 671,200 token
        t_20_rounds = TokenCostEstimator.estimate_tokens(num_agents=100, rounds=20)
        assert t_20_rounds == 335_600 * 2

        # 2 platform (2x baseline) -> 671,200 token
        t_2_platforms = TokenCostEstimator.estimate_tokens(num_agents=100, rounds=10, platform_count=2)
        assert t_2_platforms == 335_600 * 2

        # 8192 context window (2x baseline) -> 671,200 token
        t_8k_context = TokenCostEstimator.estimate_tokens(num_agents=100, rounds=10, context_window_size=8192)
        assert t_8k_context == 335_600 * 2


class TestBudgetLimitAndWarnings:
    """Uji deteksi batas maksimum budget dan over-budget warnings."""

    def test_over_budget_warning_triggered(self):
        """Uji kondisi ketika estimasi token melebihi budget limit yang ditentukan."""
        estimated = 335_600
        budget_limit = 250_000

        res = TokenCostEstimator.check_budget_limit(
            estimated_tokens=estimated,
            budget_limit=budget_limit
        )

        assert res["is_over_budget"] is True
        assert res["status"] == "OVER_BUDGET"
        assert res["excess_tokens"] == 85_600
        assert res["excess_percentage"] == 34.24
        assert res["warning"] is not None
        assert "[WARNING]" in res["warning"]
        assert "Over-budget terdeteksi" in res["warning"]
        assert "335,600" in res["warning"]
        assert "250,000" in res["warning"]

    def test_within_budget_no_warning(self):
        """Uji kondisi ketika estimasi token berada di bawah atau sama dengan budget limit."""
        estimated = 33_560
        budget_limit = 50_000

        res = TokenCostEstimator.check_budget_limit(
            estimated_tokens=estimated,
            budget_limit=budget_limit
        )

        assert res["is_over_budget"] is False
        assert res["status"] == "WITHIN_BUDGET"
        assert res["excess_tokens"] == 0
        assert res["excess_percentage"] == 0.0
        assert res["warning"] is None

    def test_exact_budget_limit(self):
        """Uji batas persis pada budget limit."""
        res = TokenCostEstimator.check_budget_limit(estimated_tokens=100_000, budget_limit=100_000)
        assert res["is_over_budget"] is False
        assert res["warning"] is None

    def test_functional_budget_warning_helper(self):
        """Uji helper check_simulation_budget_warning."""
        res = check_simulation_budget_warning(estimated_tokens=500_000, budget_limit=300_000)
        assert res["is_over_budget"] is True
        assert res["excess_tokens"] == 200_000


class TestPhaseAllocations:
    """Uji rekomendasi alokasi token per fase sesuai arsitektur MiroFish."""

    def test_phase_allocation_ratios(self):
        """
        Rekomendasi alokasi:
        - Step 0 Research: 15%
        - Step 1 Graph: 20%
        - Step 2 Simulation: 50%
        - Step 3 Report: 15%
        """
        total = 335_600
        allocations = TokenCostEstimator.allocate_phase_tokens(total)

        assert allocations["step_0_research"] == int(round(total * 0.15))
        assert allocations["step_1_graph"] == int(round(total * 0.20))
        assert allocations["step_2_simulation"] == int(round(total * 0.50))
        assert allocations["step_3_report"] == int(round(total * 0.15))

        # Jumlah alokasi wajib persis sama dengan total token
        assert sum(allocations.values()) == total

    def test_small_scale_phase_allocations(self):
        """Uji alokasi fase pada skala kecil (33,560 token)."""
        total = 33_560
        allocations = allocate_simulation_phase_tokens(total)
        assert sum(allocations.values()) == total
        assert allocations["step_0_research"] == 5034
        assert allocations["step_1_graph"] == 6712
        assert allocations["step_2_simulation"] == 16780
        assert allocations["step_3_report"] == 5034


class TestModelPricingAndCostEstimation:
    """Uji perhitungan biaya USD dan IDR lintas model."""

    def test_claude_35_sonnet_cost(self):
        """Uji estimasi biaya Claude 3.5 Sonnet ($6.00 blended rate per 1M)."""
        estimator = TokenCostEstimator()
        tokens = 1_000_000
        cost = estimator.estimate_cost(tokens=tokens, model="claude-3-5-sonnet")

        assert cost.model_key == "claude-3-5-sonnet"
        assert cost.cost_usd == 6.00
        assert cost.cost_idr == 6.00 * DEFAULT_USD_TO_IDR

    def test_gpt_4o_cost(self):
        """Uji estimasi biaya GPT-4o ($4.375 blended rate per 1M)."""
        estimator = TokenCostEstimator()
        tokens = 1_000_000
        cost = estimator.estimate_cost(tokens=tokens, model="gpt-4o")

        assert cost.model_key == "gpt-4o"
        assert cost.cost_usd == 4.375
        assert cost.cost_idr == 4.375 * DEFAULT_USD_TO_IDR

    def test_llama_3_local_cost(self):
        """Uji Llama 3 local / open-source ($0.00 / free compute)."""
        estimator = TokenCostEstimator()
        cost = estimator.estimate_cost(tokens=500_000, model="llama-3-local")

        assert cost.model_key == "llama-3-local"
        assert cost.cost_usd == 0.0
        assert cost.cost_idr == 0.0

    def test_model_aliases(self):
        """Verifikasi alias model teresolusi dengan benar."""
        estimator = TokenCostEstimator()
        c1 = estimator.estimate_cost(tokens=100_000, model="sonnet")
        assert c1.model_key == "claude-3-5-sonnet"

        c2 = estimator.estimate_cost(tokens=100_000, model="openai")
        assert c2.model_key == "gpt-4o"

        c3 = estimator.estimate_cost(tokens=100_000, model="local")
        assert c3.model_key == "llama-3-local"

    def test_custom_exchange_rate(self):
        """Uji penggunaan kurs kustom USD ke IDR."""
        estimator = TokenCostEstimator(default_usd_to_idr=15_000.0)
        cost = estimator.estimate_cost(tokens=1_000_000, model="claude-3-5-sonnet")
        assert cost.cost_idr == 6.00 * 15_000.0


class TestComprehensiveReportAndValidation:
    """Uji laporan terpadu dan validasi batas input."""

    def test_generate_budget_report_full(self):
        """Uji pembentukan laporan terpadu lengkap."""
        estimator = TokenCostEstimator()
        report = estimator.generate_budget_report(
            num_agents=100,
            rounds=10,
            platform_count=1,
            context_window_size=4096,
            model="claude-3-5-sonnet",
            budget_limit=300_000
        )

        assert isinstance(report, TokenBudgetReport)
        assert report.estimated_tokens == 335_600
        assert report.is_over_budget is True
        assert report.warning is not None
        assert report.epistemic_status == "[VERIFIED]"
        assert report.cost_usd > 0
        assert report.cost_idr > 0
        assert sum(report.phase_allocations.values()) == 335_600

        data = report.to_dict()
        assert isinstance(data, dict)
        assert data["estimated_tokens"] == 335_600

    def test_invalid_arguments_raise_value_errors(self):
        """Uji penolakan input negatif atau nol."""
        with pytest.raises(ValueError, match="num_agents"):
            TokenCostEstimator.estimate_tokens(num_agents=0)

        with pytest.raises(ValueError, match="rounds"):
            TokenCostEstimator.estimate_tokens(rounds=-1)

        with pytest.raises(ValueError, match="platform_count"):
            TokenCostEstimator.estimate_tokens(platform_count=0)

        with pytest.raises(ValueError, match="context_window_size"):
            TokenCostEstimator.estimate_tokens(context_window_size=0)

        with pytest.raises(ValueError, match="budget_limit"):
            TokenCostEstimator.check_budget_limit(estimated_tokens=1000, budget_limit=0)

        with pytest.raises(ValueError, match="tidak dikenal"):
            TokenCostEstimator.normalize_model_key("model-tidak-ada")
