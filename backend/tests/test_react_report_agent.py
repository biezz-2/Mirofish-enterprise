"""
Unit Tests untuk Agent 15: ReACT ReportAgent Multi-Turn Deduction Analyst
Memverifikasi:
1. Siklus ReACT Multi-Turn Loop (Reasoning + Acting + Deduction)
2. Safe Abstention & Perlindungan Anti-Spekulasi (NLI Threshold >= 0.85)
3. Sitasi Wajib Simpul Graf [VERIFIED]
4. Integrasi Upstream Agent 14 (BSP Swarm Runner Provenance & SHA-256)
5. Handoff Matriks Downstream untuk Agent 16 (BettaFish Sentiment Integrator)
6. REST API Endpoints di /api/enterprise/report/*
"""

import json
import pytest
from flask import Flask

from backend.app.services.react_deduction_analyst import (
    ReACTDeductionAnalyst,
    ReACTStep,
    ClaimCitation,
    HypothesisDeduction,
    StrategicReport,
)
from backend.app.services.report_agent import ReportAgent
from backend.app.api.enterprise import enterprise_bp


@pytest.fixture
def sample_verified_nodes():
    return [
        {
            "node_id": "SIM-NODE-BSP-RUNNER-sim_bsp_slice14",
            "content": "BSP Parallel Swarm Superstep Verification: 15 ronde konvergen bebas deadlock.",
            "nli_score": 0.98,
            "status": "VERIFIED",
            "sha256": "24b6a34ec7727750853aa11fedcf3385a6ccd7c17c2952844e97add567324b08",
            "label": "BSP Parallel Swarm Superstep Verification",
        },
        {
            "node_id": "SIM-NODE-CRASH-RECOVERY-sim_bsp_crash",
            "content": "SQLite WAL Zero-Loss State Recovery: Checkpoint scanner memulihkan state konsisten.",
            "nli_score": 0.95,
            "status": "VERIFIED",
            "sha256": "fe078e3a38a30ae2a2ca0ec445b644de5764aacd3d54ac1b29548058c7835935",
            "label": "SQLite WAL Zero-Loss State Recovery",
        },
    ]


@pytest.fixture
def sample_upstream_bsp_handoff():
    return {
        "simulation_job_id": "sim_bsp_slice14_verified",
        "integrity_attestation": "SHA-256_CHAIN_VERIFIED",
        "provenance_chain_summary": {
            "latest_checkpoint_hash": "24b6a34ec7727750853aa11fedcf3385a6ccd7c17c2952844e97add567324b08",
            "total_verified_checkpoints": 15,
            "latest_round": 15,
        },
        "recommended_citation_nodes": [
            {
                "node_id": "SIM-NODE-BSP-RUNNER-sim_bsp_slice14",
                "label": "BSP Parallel Swarm Superstep Verification",
                "status": "VERIFIED",
                "sha256": "24b6a34ec7727750853aa11fedcf3385a6ccd7c17c2952844e97add567324b08",
            },
            {
                "node_id": "SIM-NODE-CRASH-RECOVERY-sim_bsp_crash",
                "label": "SQLite WAL Zero-Loss State Recovery",
                "status": "VERIFIED",
                "sha256": "fe078e3a38a30ae2a2ca0ec445b644de5764aacd3d54ac1b29548058c7835935",
            },
        ],
    }


@pytest.fixture
def client():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.register_blueprint(enterprise_bp, url_prefix="/api/enterprise")
    with app.test_client() as test_client:
        yield test_client


def test_react_deduction_steps_and_loop(sample_verified_nodes):
    """Memverifikasi siklus multi-turn loop ReACT menghasilkan langkah reasoning terstruktur."""
    analyst = ReACTDeductionAnalyst(nli_threshold=0.85)
    hypothesis = "Konvergensi BSP bebas deadlock pada simulasi swarm."

    deduction = analyst.deduce_hypothesis(hypothesis, sample_verified_nodes)

    assert deduction.status == "CONFIRMED"
    assert deduction.confidence >= 0.85
    assert len(deduction.steps) >= 2

    step1 = deduction.steps[0]
    assert step1.iteration == 1
    assert step1.action == "query_graph_node"
    assert step1.thought != ""
    assert step1.observation != ""
    assert step1.deduction != ""
    assert step1.reflection != ""

    step2 = deduction.steps[1]
    assert step2.iteration == 2
    assert step2.action == "verify_provenance_hash"
    assert "SHA-256" in step2.observation


def test_safe_abstention_barrier_unverified_query(sample_verified_nodes):
    """Kueri tanpa simpul graf terverifikasi wajib diabstain (anti-spekulasi)."""
    analyst = ReACTDeductionAnalyst(nli_threshold=0.85)
    unverified_query = "Apakah terjadi manipulasi data pemilu di platform X?"

    is_abstained, reason = analyst.evaluate_safe_abstention(unverified_query, sample_verified_nodes)
    assert is_abstained is True
    assert "diabstain" in reason.lower()


def test_safe_abstention_barrier_speculative_financial(sample_verified_nodes):
    """Spekulasi finansial masa depan tanpa data empiris langsung ditolak."""
    analyst = ReACTDeductionAnalyst(nli_threshold=0.85)
    query = "Berapa laba bersih kuartal depan?"

    is_abstained, reason = analyst.evaluate_safe_abstention(query, sample_verified_nodes)
    assert is_abstained is True
    assert "diabstain" in reason.lower()
    assert "safe abstention" in reason.lower() or "anti-spekulasi" in reason.lower() or "finansial" in reason.lower()


def test_safe_abstention_low_nli_rejection():
    """Simpul dengan NLI < 0.85 tidak boleh disitasi sebagai temuan terverifikasi."""
    analyst = ReACTDeductionAnalyst(nli_threshold=0.85)
    low_nli_nodes = [
        {
            "node_id": "node_weak_01",
            "content": "Klaim dugaan rumor tanpa verifikasi cukup.",
            "nli_score": 0.65,
            "status": "VERIFIED",
        }
    ]

    report = analyst.generate_strategic_report("Analisis Rumor", low_nli_nodes)
    assert len(report.citations) == 0
    assert len(report.abstained_questions) >= 1
    assert "diabstain" in report.abstained_questions[0].lower()


def test_mandatory_verified_citations(sample_verified_nodes):
    """Setiap temuan wajib menyertakan rujukan eksplisit simpul [VERIFIED]."""
    analyst = ReACTDeductionAnalyst(nli_threshold=0.85)
    report = analyst.generate_strategic_report("Audit Ketahanan", sample_verified_nodes)

    assert len(report.citations) >= 2
    for citation in report.citations:
        assert citation.is_verified is True
        assert citation.status == "VERIFIED"
        assert citation.nli_confidence >= 0.85
        assert citation.sha256 is not None

    for finding in report.key_findings:
        assert "[VERIFIED]" in finding
        assert "Ref: [" in finding

    assert "[VERIFIED]" in report.markdown_content


def test_upstream_agent_14_provenance_ingestion(sample_upstream_bsp_handoff):
    """Memverifikasi ingesti rantai provenance SHA-256 dan rekomendasi Agent 14."""
    agent = ReportAgent(nli_threshold=0.85)
    report = agent.generate_strategic_report(
        topic="Validasi Orkestrasi BSP",
        verified_nodes=[],
        upstream_bsp_handoff=sample_upstream_bsp_handoff,
    )

    assert report.provenance_summary.get("latest_checkpoint_hash") == (
        "24b6a34ec7727750853aa11fedcf3385a6ccd7c17c2952844e97add567324b08"
    )
    assert report.provenance_summary.get("total_verified_checkpoints") == 15
    assert len(report.citations) >= 2
    assert any("SIM-NODE-BSP-RUNNER" in c.graph_node_id for c in report.citations)
    assert any("SIM-NODE-CRASH-RECOVERY" in c.graph_node_id for c in report.citations)


def test_downstream_agent_16_recommendations(sample_verified_nodes, sample_upstream_bsp_handoff):
    """Memverifikasi pembentukan matriks handoff untuk Agent 16 (BettaFish)."""
    analyst = ReACTDeductionAnalyst(nli_threshold=0.85)
    report = analyst.generate_strategic_report(
        topic="Ringkasan C-Level Swarm",
        verified_nodes=sample_verified_nodes,
        upstream_bsp_handoff=sample_upstream_bsp_handoff,
    )

    handoff = analyst.get_downstream_recommendations_agent_16(report)
    assert handoff["target_subagent"] == "Agent 16: BettaFish Analytics & Sentiment Model Integrator"
    assert handoff["downstream_task_id"] == "t_b58486a8"
    assert handoff["provenance_chain_status"] == "SHA-256_CHAIN_VERIFIED"
    assert handoff["c_level_risk_assessment_required"] is True
    assert len(handoff["sentiment_target_claims"]) >= 2
    assert handoff["mean_nli_confidence"] >= 0.85
    assert "SentimentAnalysisModel_Polar" in handoff["recommended_sentiment_models"]


def test_hypothesis_deduction_confirmed_and_refuted(sample_verified_nodes):
    """Membuktikan deduksi membedakan hipotesis terdukung vs spekulatif."""
    analyst = ReACTDeductionAnalyst(nli_threshold=0.85)

    valid_hyp = "BSP Superstep konvergen dan bebas deadlock."
    res_valid = analyst.deduce_hypothesis(valid_hyp, sample_verified_nodes)
    assert res_valid.status == "CONFIRMED"
    assert len(res_valid.citations) > 0

    spec_hyp = "Perusahaan akan mengalami kebangkrutan bulan depan."
    res_spec = analyst.deduce_hypothesis(spec_hyp, sample_verified_nodes)
    assert res_spec.status == "ABSTAINED"
    assert res_spec.abstention_reason is not None
    assert "diabstain" in res_spec.abstention_reason.lower()


def test_enterprise_api_report_generate(client, sample_verified_nodes):
    """Integrasi endpoint POST /api/enterprise/report/generate."""
    payload = {
        "topic": "Evaluasi Platform Swarm",
        "verified_nodes": sample_verified_nodes,
        "unverified_queries": ["Apakah server akan padam besok?"],
    }
    response = client.post("/api/enterprise/report/generate", json=payload)
    assert response.status_code == 200
    data = response.get_json()

    assert data["success"] is True
    assert "report_id" in data
    assert len(data["citations"]) >= 2
    assert len(data["abstained_questions"]) >= 1
    assert "diabstain" in data["abstained_questions"][0].lower()
    assert len(data["deduction_steps"]) >= 2
    assert data["downstream_parameters"]["target_subagent"] == "Agent 16: BettaFish Analytics & Sentiment Model Integrator"


def test_enterprise_api_report_deduce(client, sample_verified_nodes):
    """Integrasi endpoint POST /api/enterprise/report/deduce."""
    payload = {
        "hypothesis": "SQLite WAL menjamin zero data loss pada recovery.",
        "verified_nodes": sample_verified_nodes,
    }
    response = client.post("/api/enterprise/report/deduce", json=payload)
    assert response.status_code == 200
    data = response.get_json()

    assert data["success"] is True
    assert data["status"] == "CONFIRMED"
    assert len(data["steps"]) >= 2
    assert len(data["citations"]) >= 1


def test_enterprise_api_report_downstream_recommendations(client):
    """Integrasi endpoint GET /api/enterprise/report/downstream-recommendations."""
    response = client.get("/api/enterprise/report/downstream-recommendations?topic=Audit+Swarm")
    assert response.status_code == 200
    data = response.get_json()

    assert data["success"] is True
    recs = data["recommendations"]
    assert recs["downstream_task_id"] == "t_b58486a8"
    assert recs["target_subagent"] == "Agent 16: BettaFish Analytics & Sentiment Model Integrator"
    assert recs["provenance_chain_status"] == "SHA-256_CHAIN_VERIFIED"
