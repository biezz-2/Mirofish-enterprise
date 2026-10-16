"""
Unit & Integration Test Suite for BettaFish Analytics & Sentiment Model Integrator
(Agent 16: Divisi E)

Tests:
1. Polar Sentiment Analysis (Polarity score, Valence Modifiers, Subjectivity, 8 Emotions).
2. Multilingual Coverage (Indonesian, English, Chinese).
3. Corporate Risk Assessment, Polarization Index, and Early Warning Sentinel.
4. C-Level Executive Report Synthesis (CEO, CTO, CMO, CRO Directives, SWOT, SHA-256 Integrity).
5. Downstream Handoff Matrix to Agent 17 (FastMCP) and Agent 18 (OpenAPI/Webhooks).
6. Enterprise Flask API Endpoint Integrations.
"""

import hashlib
import json
import pytest
from app import create_app
from app.services.bettafish_report_engine import (
    SentimentAnalysisModel_Polar,
    BettaFishInsightEngine,
    BettaFishReportEngine,
    SentimentLabel,
    RiskLevel,
    EmotionVector,
    PolarSentimentResult,
    ExecutiveSummaryCLevel,
)
from app.services.bettafish_adapter import (
    BettaFishAdapter,
    SentimentBreakdown,
    BettaFishExecutiveSummary,
)


@pytest.fixture
def app():
    app = create_app()
    return app


@pytest.fixture
def client(app):
    return app.test_client()


class TestPolarSentimentModel:
    """Pengujian Unit SentimentAnalysisModel_Polar."""

    def test_positive_text_evaluation(self):
        model = SentimentAnalysisModel_Polar()
        res = model.analyze("Sistem orkestrasi berhasil beroperasi secara optimal, efisien, aman, dan stabil.")
        assert res.polarity_score > 0.3
        assert res.sentiment_label == "POSITIVE"
        assert res.granular_label in (SentimentLabel.POSITIVE, SentimentLabel.STRONGLY_POSITIVE)
        assert res.emotions.trust > 0.4
        assert res.emotions.joy > 0.2
        assert len(res.matched_positive_words) > 0
        assert res.confidence == 0.95

    def test_negative_text_evaluation(self):
        model = SentimentAnalysisModel_Polar()
        res = model.analyze("Terjadi kegagalan fatal pada server, sistem kolaps dan rentan terhadap serangan krisis.")
        assert res.polarity_score < -0.3
        assert res.sentiment_label == "NEGATIVE"
        assert res.granular_label in (SentimentLabel.NEGATIVE, SentimentLabel.STRONGLY_NEGATIVE)
        assert res.emotions.anger > 0.1
        assert res.emotions.fear > 0.1
        assert len(res.matched_negative_words) > 0

    def test_neutral_text_evaluation(self):
        model = SentimentAnalysisModel_Polar()
        res = model.analyze("Proses batch berjalan sesuai jadwal reguler pada jam 12:00.")
        assert abs(res.polarity_score) <= 0.15
        assert res.sentiment_label == "NEUTRAL"
        assert res.granular_label == SentimentLabel.NEUTRAL

    def test_valence_shifting_negation(self):
        model = SentimentAnalysisModel_Polar()
        # "aman" is positive; "tidak aman" must be negative
        res_pos = model.analyze("Arsitektur jaringan aman dan terpercaya.")
        res_neg = model.analyze("Arsitektur jaringan tidak aman dan tidak terpercaya.")
        assert res_pos.polarity_score > 0.2
        assert res_neg.polarity_score < 0.0
        assert any("negator" in mod for mod in res_neg.valence_modifiers)

    def test_valence_shifting_intensifiers_and_dampeners(self):
        model = SentimentAnalysisModel_Polar()
        res_base = model.analyze("Platform efisien.")
        res_intense = model.analyze("Platform sangat amat efisien.")
        res_damp = model.analyze("Platform agak efisien.")

        assert res_intense.polarity_score >= res_base.polarity_score
        assert any("intensifier" in mod for mod in res_intense.valence_modifiers)
        assert any("dampener" in mod for mod in res_damp.valence_modifiers)

    def test_multilingual_coverage(self):
        model = SentimentAnalysisModel_Polar()
        # English
        res_en = model.analyze("The breakthrough security update was successful and highly resilient.")
        assert res_en.polarity_score > 0.3
        assert res_en.sentiment_label == "POSITIVE"

        # Chinese
        res_zh = model.analyze("系统在创新与高效方面取得了巨大成功，表现卓越可靠。")
        assert res_zh.polarity_score > 0.3
        assert res_zh.sentiment_label == "POSITIVE"

    def test_batch_and_stream_analysis(self):
        model = SentimentAnalysisModel_Polar()
        texts = [
            "Layanan aman dan teruji.",
            "Krisis finansial dan kerugian fatal.",
            "Statistik harian tercatat."
        ]
        batch_results = model.analyze_batch(texts)
        assert len(batch_results) == 3
        assert batch_results[0].sentiment_label == "POSITIVE"
        assert batch_results[1].sentiment_label == "NEGATIVE"
        assert batch_results[2].sentiment_label == "NEUTRAL"

        events = [{"content": "Inovasi unggul."}, {"content": "Kinerja stabil."}]
        stream_res = model.analyze_stream(events)
        assert stream_res.polarity_score > 0.2


class TestBettaFishInsightEngine:
    """Pengujian Unit Penilaian Risiko Korporat dan Early Warning."""

    def test_corporate_risk_low_risk_scenario(self):
        engine = BettaFishInsightEngine()
        model = SentimentAnalysisModel_Polar()
        sentiment = model.analyze("Platform sangat aman, stabil, dan profit meningkat konsisten.")
        claim_polarities = [0.8, 0.75, 0.85]

        risk = engine.assess_corporate_risk(
            sentiment=sentiment,
            claim_polarities=claim_polarities,
            virality_potential=0.1
        )
        assert risk.overall_risk_level == RiskLevel.LOW
        assert risk.risk_score < 0.25
        assert risk.early_warning_escalation is False

    def test_corporate_risk_critical_scenario_and_early_warning(self):
        engine = BettaFishInsightEngine()
        model = SentimentAnalysisModel_Polar()
        sentiment = model.analyze("Krisis fatal, sistem kolaps rusak parah akibat kebocoran data dan korupsi fatal.")
        claim_polarities = [-0.9, -0.85, -0.7]

        risk = engine.assess_corporate_risk(
            sentiment=sentiment,
            claim_polarities=claim_polarities,
            virality_potential=0.85
        )
        assert risk.overall_risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)
        assert risk.early_warning_escalation is True
        assert len(risk.escalation_triggers) > 0
        assert any("Peringatan Dini" in r or "SEGERA" in r for r in risk.containment_recommendations)

    def test_polarization_index_calculation(self):
        engine = BettaFishInsightEngine()
        model = SentimentAnalysisModel_Polar()
        sentiment = model.analyze("Opini publik terpecah.")
        # Dispersed polarities (-0.9 vs +0.9)
        claim_polarities = [-0.9, 0.9, -0.85, 0.88]

        risk = engine.assess_corporate_risk(
            sentiment=sentiment,
            claim_polarities=claim_polarities,
            virality_potential=0.5
        )
        assert risk.polarization_index > 0.5


class TestBettaFishReportEngine:
    """Pengujian Unit BettaFishReportEngine dan C-Level Executive Synthesis."""

    def test_c_level_report_synthesis_with_upstream_handoff(self):
        engine = BettaFishReportEngine()
        upstream_handoff = {
            "strategic_report_id": "rep_strat_test_001",
            "topic": "Skalabilitas & Ketahanan Swarm BSP",
            "sentiment_target_claims": [
                {
                    "claim_text": "BSP checkpoint SQLite WAL terbukti konsisten dan pulih dalam < 500ms.",
                    "graph_node_id": "NODE-001",
                    "nli_score": 0.96,
                    "status": "VERIFIED"
                },
                {
                    "claim_text": "Platform terverifikasi aman dari deadlock dan kebocoran memori.",
                    "graph_node_id": "NODE-002",
                    "nli_score": 0.94,
                    "status": "VERIFIED"
                }
            ]
        }

        report = engine.generate_executive_report(
            topic="Skalabilitas & Ketahanan Swarm BSP",
            upstream_handoff=upstream_handoff
        )

        assert report.report_id.startswith("exec_rep_")
        assert len(report.claim_sentiments) == 2
        assert report.provenance_chain_status == "SHA-256_CHAIN_VERIFIED"
        assert len(report.report_digest_sha256) == 64
        assert len(report.directives.ceo_directives) > 0
        assert len(report.directives.cto_directives) > 0
        assert len(report.directives.cmo_directives) > 0
        assert len(report.directives.cro_directives) > 0
        assert len(report.swot_analysis.strengths) > 0
        assert "Laporan Eksekutif C-Level" in report.markdown_briefing

    def test_downstream_recommendations_matrix(self):
        engine = BettaFishReportEngine()
        report = engine.generate_executive_report(topic="Enterprise AI Multi-Agent")
        recs = engine.get_downstream_recommendations_agent_17_18(report)

        assert recs["source_subagent"] == "Agent 16: BettaFish Analytics & Sentiment Model Integrator"
        assert recs["provenance_chain_status"] == "SHA-256_CHAIN_VERIFIED"
        assert recs["executive_report_id"] == report.report_id
        assert "agent_17" in recs["downstream_targets"]
        assert "agent_18" in recs["downstream_targets"]

        # Verify Agent 17 spec
        ag17 = recs["downstream_targets"]["agent_17"]
        assert ag17["task_id"] == "t_fe0a76e7"
        assert len(ag17["mcp_tools_spec"]) == 3
        tool_names = [t["name"] for t in ag17["mcp_tools_spec"]]
        assert "bettafish_analyze_polar_sentiment" in tool_names
        assert "bettafish_generate_c_level_report" in tool_names
        assert "bettafish_assess_corporate_risk" in tool_names

        # Verify Agent 18 spec
        ag18 = recs["downstream_targets"]["agent_18"]
        assert ag18["task_id"] == "t_a0bb3682"
        assert ag18["openapi_version"] == "3.1.0"
        assert "BETTAFISH_EXECUTIVE_REPORT_GENERATED" in ag18["webhook_events"]
        assert ag18["hmac_sha256_required"] is True


class TestBettaFishAdapter:
    """Pengujian Unit Kompatibilitas BettaFishAdapter."""

    def test_adapter_backward_compatibility(self):
        adapter = BettaFishAdapter()
        # Legacy analyze_sentiment test
        res = adapter.analyze_sentiment("Sistem sukses berjalan dengan aman dan verified.")
        assert isinstance(res, SentimentBreakdown)
        assert res.sentiment_label == "POSITIVE"
        assert res.polarity_score > 0.0
        assert res.trust >= 0.5

        # Legacy generate_executive_insights test
        sim_events = [
            {"content": "Pengujian benchmark sukses besar."},
            {"content": "Latensi jaringan rendah dan aman."}
        ]
        exec_insights = adapter.generate_executive_insights(sim_events)
        assert isinstance(exec_insights, BettaFishExecutiveSummary)
        assert exec_insights.sentiment.sentiment_label == "POSITIVE"
        assert exec_insights.risk_level in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
        assert len(exec_insights.actionable_recommendations) > 0

    def test_adapter_advanced_methods(self):
        adapter = BettaFishAdapter()
        report = adapter.generate_c_level_report(topic="Ketahanan Infrastruktur Cloud")
        assert isinstance(report, ExecutiveSummaryCLevel)
        assert report.provenance_chain_status == "SHA-256_CHAIN_VERIFIED"

        risk = adapter.assess_corporate_risk("Sistem beroperasi aman tanpa gangguan.")
        assert risk.overall_risk_level == RiskLevel.LOW

        recs = adapter.get_downstream_recommendations(report)
        assert recs["downstream_targets"]["agent_17"]["task_id"] == "t_fe0a76e7"


class TestBettaFishAPIEndpoints:
    """Pengujian Integrasi REST Endpoints Flask Enterprise."""

    def test_api_bettafish_sentiment(self, client):
        resp = client.post('/api/enterprise/bettafish/sentiment', json={
            "text": "Inovasi platform enterprise terbukti sukses, cepat, dan aman."
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["data"]["sentiment_label"] == "POSITIVE"
        assert data["data"]["polarity_score"] > 0.0

    def test_api_bettafish_executive_report(self, client):
        payload = {
            "topic": "Audit Keamanan Siber Kriptografis",
            "custom_claims": [
                "Verifikasi SHA-256 valid 100% pada semua transaksi.",
                "Tidak ditemukan celah injeksi kode atau buffer overflow."
            ]
        }
        resp = client.post('/api/enterprise/bettafish/executive-report', json=payload)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "report" in data
        assert data["report"]["provenance_chain_status"] == "SHA-256_CHAIN_VERIFIED"
        assert len(data["report"]["report_digest_sha256"]) == 64
        assert len(data["report"]["directives"]["ceo_directives"]) > 0

    def test_api_bettafish_risk_assessment(self, client):
        payload = {
            "text": "Ancaman kegagalan server dan krisis fatal akibat serangan berbahaya.",
            "claim_polarities": [-0.8, -0.6],
            "virality_potential": 0.75
        }
        resp = client.post('/api/enterprise/bettafish/risk-assessment', json=payload)
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert data["risk_assessment"]["overall_risk_level"] in ("HIGH", "CRITICAL")
        assert data["risk_assessment"]["early_warning_escalation"] is True

    def test_api_bettafish_downstream_recommendations(self, client):
        resp = client.get('/api/enterprise/bettafish/downstream-recommendations?topic=Distributed+BSP')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["success"] is True
        assert "recommendations" in data
        assert data["recommendations"]["provenance_chain_status"] == "SHA-256_CHAIN_VERIFIED"
        assert data["recommendations"]["downstream_targets"]["agent_17"]["task_id"] == "t_fe0a76e7"
        assert data["recommendations"]["downstream_targets"]["agent_18"]["task_id"] == "t_a0bb3682"
