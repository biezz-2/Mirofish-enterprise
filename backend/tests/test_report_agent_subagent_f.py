"""
Unit and Integration Tests for Subagent F: ReportAgent & Analytic Reasoning Engineer
Verifies:
1. ReACT Tool `cross_platform_synthesis` across all 7 canonical platforms:
   - Twitter / X, Reddit, TikTok, Instagram, LinkedIn, Threads, YouTube.
2. Cross-platform sentiment polarity scores (-1.0 to +1.0) and percentage distribution (% Pos / % Neu / % Neg).
3. Qualitative contrasting discourse profiles:
   - TikTok: viral hooks & short video dynamics.
   - Reddit: deep argumentation & community fact-checking.
   - LinkedIn: professional governance, industry impact & compliance.
4. Epistemic Protocol enforcement:
   - Status contract: VERIFIED_SUCCESS.
   - Epistemic label [VERIFIED] in citations and findings.
5. Report persistence:
   - `Report.to_dict()` and `ReportManager.get_report()` preserving `epistemic_status` & `cross_platform_sentiment`.
6. SSE Endpoint & Auth:
   - GET /api/report/<report_id>/agent-log/events streaming `text/event-stream`.
   - Query param `token` authentication in `require_auth`.
"""

import os
import json
import pytest
from unittest.mock import MagicMock, patch
from flask import Flask

from backend.app.services.report_agent import (
    ReportAgent,
    Report,
    ReportOutline,
    ReportSection,
    ReportStatus,
    ReportManager,
)
from backend.app.api.report import report_bp
from backend.app.utils.auth import create_token


@pytest.fixture
def test_app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["JWT_SECRET_KEY"] = "test-secret-report-key-1234567890-32bytes"
    app.config["AUTH_REQUIRED"] = True
    app.register_blueprint(report_bp, url_prefix="/api/report")
    return app


@pytest.fixture
def auth_token(test_app):
    with test_app.app_context():
        token = create_token(
            payload={"user_id": "analyst_f", "roles": ["user"]},
            secret_key="test-secret-report-key-1234567890-32bytes",
            expires_in=3600,
        )
    return token


class TestReportAgentCrossPlatformSynthesis:
    """Verifikasi logika analisis ReACT 7-platform dan sintesis opini publik."""

    def test_cross_platform_synthesis_tool_structure(self):
        agent = ReportAgent(
            graph_id="test_graph_123",
            simulation_id="sim_test_7platforms",
            simulation_requirement="Analisis sentimen peluncuran teknologi kecerdasan buatan"
        )

        # Pastikan perkakas terdaftar dalam tools
        assert "cross_platform_synthesis" in agent.tools

        # Eksekusi perkakas cross_platform_synthesis
        result_text = agent._execute_cross_platform_synthesis({
            "focus_topic": "Dampak AI generatif terhadap dunia kerja"
        })

        assert isinstance(result_text, str)
        # Verifikasi label epistemik
        assert "[VERIFIED]" in result_text
        assert "Matriks Sintesis Opini Publik 7-Platform" in result_text

        # Verifikasi semua 7 platform kanonikal hadir
        canonical_platforms = [
            "Twitter / X",
            "Reddit",
            "TikTok",
            "Instagram",
            "LinkedIn",
            "Threads",
            "YouTube"
        ]
        for platform in canonical_platforms:
            assert platform in result_text, f"Platform {platform} harus ada dalam sintesis"

        # Verifikasi profil diskursus kontras
        assert "TikTok vs Reddit" in result_text
        assert "LinkedIn vs Twitter/X" in result_text
        assert "video hook" in result_text
        assert "diskursus panjang" in result_text
        assert "kepatuhan" in result_text

        # Verifikasi data metrik tersimpan dalam state agent
        sentiments = agent.current_report_cross_platform_sentiment
        assert len(sentiments) == 7
        for key in ["twitter", "reddit", "tiktok", "instagram", "linkedin", "threads", "youtube"]:
            assert key in sentiments
            data = sentiments[key]
            # Polaritas rentang -1.0 s.d +1.0
            assert -1.0 <= data["net_polarity"] <= 1.0
            assert 0 <= data["positive_pct"] <= 100
            assert 0 <= data["neutral_pct"] <= 100
            assert 0 <= data["negative_pct"] <= 100
            assert data["positive_pct"] + data["neutral_pct"] + data["negative_pct"] == 100
            assert "discourse_profile" in data

    def test_report_dataclass_and_serialization(self, tmp_path):
        """Verifikasi kontrak epistemic_status dan persistensi Report."""
        outline = ReportOutline(
            title="Laporan Analisis Opini Publik Multidimensi",
            summary="Ringkasan simulasi 7 platform kanonikal",
            sections=[
                ReportSection(title="Ringkasan Eksekutif", content="[VERIFIED] Hasil observasi awal."),
                ReportSection(title="Dinamika Cross-Platform", content="[VERIFIED] Perbandingan sentimen.")
            ]
        )

        cross_sentiment = {
            "twitter": {"net_polarity": 0.15, "positive_pct": 38, "neutral_pct": 39, "negative_pct": 23, "discourse_profile": "Rapid dissemination"},
            "tiktok": {"net_polarity": 0.42, "positive_pct": 52, "neutral_pct": 38, "negative_pct": 10, "discourse_profile": "Viral hooks"},
            "reddit": {"net_polarity": -0.08, "positive_pct": 31, "neutral_pct": 40, "negative_pct": 29, "discourse_profile": "In-depth argumentation"},
            "linkedin": {"net_polarity": 0.35, "positive_pct": 49, "neutral_pct": 42, "negative_pct": 9, "discourse_profile": "Professional compliance"},
            "instagram": {"net_polarity": 0.28, "positive_pct": 45, "neutral_pct": 43, "negative_pct": 12, "discourse_profile": "Lifestyle empathy"},
            "threads": {"net_polarity": 0.05, "positive_pct": 33, "neutral_pct": 49, "negative_pct": 18, "discourse_profile": "Conversational banter"},
            "youtube": {"net_polarity": 0.22, "positive_pct": 41, "neutral_pct": 45, "negative_pct": 14, "discourse_profile": "Long-form commentary"}
        }

        report = Report(
            report_id="rep_test_verified_123",
            simulation_id="sim_test_7platforms",
            graph_id="graph_test_123",
            simulation_requirement="Evaluasi regulasi data privasi",
            status=ReportStatus.COMPLETED,
            outline=outline,
            markdown_content="# Laporan Lengkap\n\nIsi laporan...",
            epistemic_status="VERIFIED_SUCCESS",
            cross_platform_sentiment=cross_sentiment
        )

        data_dict = report.to_dict()
        assert data_dict["epistemic_status"] == "VERIFIED_SUCCESS"
        assert len(data_dict["cross_platform_sentiment"]) == 7
        assert data_dict["cross_platform_sentiment"]["tiktok"]["net_polarity"] == 0.42

        # Test persistensi & pemuatan kembali via ReportManager
        with patch.object(ReportManager, "REPORTS_DIR", str(tmp_path)):
            ReportManager.save_report(report)
            loaded = ReportManager.get_report("rep_test_verified_123")

            assert loaded is not None
            assert loaded.epistemic_status == "VERIFIED_SUCCESS"
            assert loaded.cross_platform_sentiment["reddit"]["net_polarity"] == -0.08
            assert loaded.cross_platform_sentiment["linkedin"]["discourse_profile"] == "Professional compliance"


class TestReportAgentSSEEndpoint:
    """Verifikasi Server-Sent Events (SSE) streaming endpoint."""

    def test_sse_endpoint_requires_auth(self, test_app):
        client = test_app.test_client()
        response = client.get("/api/report/rep_test_sse/agent-log/events")
        assert response.status_code == 401

    def test_sse_endpoint_with_query_param_token(self, test_app, auth_token, tmp_path):
        """Verifikasi bahwa token query parameter diterima untuk koneksi EventSource."""
        client = test_app.test_client()

        # Buat dummy report & log data di folder sementara
        with patch.object(ReportManager, "REPORTS_DIR", str(tmp_path)):
            report = Report(
                report_id="rep_test_sse",
                simulation_id="sim_test_sse",
                graph_id="graph_test_sse",
                simulation_requirement="Pengujian streaming SSE",
                status=ReportStatus.COMPLETED,
                epistemic_status="VERIFIED_SUCCESS"
            )
            ReportManager.save_report(report)

            # Tambah 1 line agent log
            log_entry = {
                "timestamp": "2026-10-18T10:00:00Z",
                "action": "cross_platform_synthesis",
                "stage": "generating",
                "section_title": "Analisis Multi-Platform",
                "section_index": 1,
                "details": {"platforms": 7, "epistemic_status": "VERIFIED_SUCCESS"}
            }
            log_path = ReportManager._get_agent_log_path("rep_test_sse")
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")

            with patch("backend.app.api.report.ReportManager.REPORTS_DIR", str(tmp_path)):
                # Mock require_resource_ownership agar lolos untuk test endpoint
                with patch("backend.app.utils.auth.get_db_session"):
                    response = client.get(
                        f"/api/report/rep_test_sse/agent-log/events?token={auth_token}&timeout=2.0"
                    )
                    assert response.status_code == 200
                    assert response.mimetype == "text/event-stream"
                    assert "no-cache" in response.headers.get("Cache-Control", "")

                    # Parse stream chunks
                    content = response.get_data(as_text=True)
                    assert "event: connected" in content
                    assert "event: log" in content
                    assert "cross_platform_synthesis" in content
                    assert "event: done" in content
