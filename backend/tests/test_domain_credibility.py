"""
Unit & Integration Tests for Agent 04: Domain Credibility Scorer & Epistemic Grounding Validator
(Divisi Riset / R2P)
"""

import math
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from app.services.domain_credibility import (
    DomainCredibilityScorer,
    EpistemicGroundingValidator,
    GroundedFact,
    EpistemicStatus,
    SourceCredibility,
    DOMAIN_AUTHORITY_TIERS
)
from app.services.searchxng_service import SearchXNGResult, SearchXNGReport
from app.services.web_research_service import WebResearchService, ResearchReport


class TestDomainCredibilityScorer:
    """Pengujian mesin penilaian kredibilitas domain matematis."""

    def setup_method(self):
        self.scorer = DomainCredibilityScorer()

    def test_extract_domain(self):
        assert self.scorer.extract_domain("https://www.reuters.com/world/article") == "reuters.com"
        assert self.scorer.extract_domain("http://arxiv.org/abs/2503.18813") == "arxiv.org"
        assert self.scorer.extract_domain("https://sub.kemkominfo.go.id/path") == "sub.kemkominfo.go.id"
        assert self.scorer.extract_domain("https://reddit.com/r/ai") == "reddit.com"
        assert self.scorer.extract_domain("kaskus.co.id") == "kaskus.co.id"
        assert self.scorer.extract_domain("") == "unknown"

    def test_domain_authority_hierarchy(self):
        # 1. Akademik & Riset (>= 0.7, 1.0)
        assert self.scorer.get_domain_authority("arxiv.org") == 1.0
        assert self.scorer.get_domain_authority("https://nature.com/articles/123") == 1.0
        assert self.scorer.get_domain_authority("https://stanford.edu") == 1.0
        assert self.scorer.get_domain_authority("https://cs.ui.ac.id/research") == 1.0

        # 2. Pemerintah & Regulator (0.95 >= 0.7)
        assert self.scorer.get_domain_authority("who.int") == 0.95
        assert self.scorer.get_domain_authority("https://kemkominfo.go.id/news") == 0.95
        assert self.scorer.get_domain_authority("https://fda.gov") == 0.95
        assert self.scorer.get_domain_authority("https://bi.go.id") == 0.95
        assert self.scorer.get_domain_authority("spec.openapis.org") == 0.95

        # 3. Media Berita Kredibel (0.85 >= 0.7)
        assert self.scorer.get_domain_authority("reuters.com") == 0.85
        assert self.scorer.get_domain_authority("bloomberg.com") == 0.85
        assert self.scorer.get_domain_authority("apnews.com") == 0.85
        assert self.scorer.get_domain_authority("kompas.com") == 0.85
        assert self.scorer.get_domain_authority("tempo.co") == 0.85
        assert self.scorer.get_domain_authority("bisnis.com") == 0.85

        # 4. Portal Mainstream & Ensiklopedia (0.60)
        assert self.scorer.get_domain_authority("wikipedia.org") == 0.60
        assert self.scorer.get_domain_authority("techcrunch.com") == 0.60
        assert self.scorer.get_domain_authority("detik.com") == 0.60

        # 5. Media Sosial & Forum Anonim (< 0.50, misal: 0.30)
        assert self.scorer.get_domain_authority("reddit.com") == 0.30
        assert self.scorer.get_domain_authority("kaskus.co.id") == 0.30
        assert self.scorer.get_domain_authority("twitter.com") == 0.30
        assert self.scorer.get_domain_authority("x.com") == 0.30
        assert self.scorer.get_domain_authority("4chan.org") == 0.15
        assert self.scorer.get_domain_authority("reddit.com") < 0.50

        # 6. Domain Tak Dikenal (0.20)
        assert self.scorer.get_domain_authority("unknown-random-blog-12345.xyz") == 0.20
        # Jika kategori news tapi domain tak terdaftar, fallback ke 0.50
        assert self.scorer.get_domain_authority("unknown-local-paper.net", category="news") == 0.50

    def test_recency_decay(self):
        ref_date = datetime(2026, 10, 16, 12, 0, 0, tzinfo=timezone.utc)

        # Tanpa tanggal -> R = 1.0
        assert self.scorer.compute_recency_decay(None, reference_date=ref_date) == 1.0

        # Hari ini -> R = exp(0) = 1.0
        today_str = "2026-10-16"
        assert math.isclose(self.scorer.compute_recency_decay(today_str, reference_date=ref_date), 1.0, rel_tol=1e-2)

        # 10 hari lalu -> R = exp(-0.05 * 10) = exp(-0.5) ~ 0.6065
        past_str = "2026-10-06"
        decay_10d = self.scorer.compute_recency_decay(past_str, reference_date=ref_date)
        expected = math.exp(-0.05 * 10.0)
        assert math.isclose(decay_10d, expected, rel_tol=1e-2)

        # 30 hari lalu -> R = exp(-0.05 * 30) = exp(-1.5) ~ 0.2231
        past_30d = "2026-09-16"
        decay_30d = self.scorer.compute_recency_decay(past_30d, reference_date=ref_date)
        assert decay_30d < decay_10d

    def test_cross_source_consensus(self):
        r1 = SearchXNGResult(
            title="Adopsi AI Meningkatkan Efisiensi Sektor Perbankan",
            url="https://reuters.com/article/ai-banking",
            content="Bank sentral melaporkan efisiensi operasional perbankan naik 20 persen berkat adopsi AI."
        )
        r2 = SearchXNGResult(
            title="Laporan Efisiensi Perbankan Nasional dengan AI",
            url="https://bloomberg.com/news/banking-ai",
            content="Studi mencatat perbankan memanfaatkan kecerdasan artifisial untuk efisiensi operasional."
        )
        r3 = SearchXNGResult(
            title="Perbankan Nasional dan Transformasi AI",
            url="https://bisnis.com/keuangan/ai-bank",
            content="Efisiensi industri perbankan melonjak signifikan berkat implementasi teknologi AI."
        )
        r4_unrelated = SearchXNGResult(
            title="Resep Masakan Tradisional Rendang Daging",
            url="https://kuliner.com/resep-rendang",
            content="Bahan bumbu rempah kelapa untuk rendang daging sapi empuk khas Padang."
        )

        all_results = [r1, r2, r3, r4_unrelated]

        # r1 dikonfirmasi oleh r2 (bloomberg) dan r3 (bisnis.com) -> minimal 2 domain independen
        consensus_r1 = self.scorer.compute_cross_source_consensus(r1, all_results)
        assert consensus_r1 >= 0.80

        # r4 tidak dikonfirmasi oleh domain lain -> skor rendah
        consensus_r4 = self.scorer.compute_cross_source_consensus(r4_unrelated, all_results)
        assert consensus_r4 <= 0.40

    def test_composite_credibility_calculation(self):
        # S_cred = 0.45 * D_auth + 0.35 * C_consensus + 0.20 * R_recency
        # Case 1: Reuters (D_auth = 0.85), Consensus = 0.85, Recency = 1.0 (recent)
        # Expected = 0.45 * 0.85 + 0.35 * 0.85 + 0.20 * 1.0 = 0.3825 + 0.2975 + 0.20 = 0.8800
        score_high = self.scorer.calculate_composite_score(0.85, 0.85, 1.0)
        assert math.isclose(score_high, 0.88, abs_tol=0.01)
        assert score_high >= 0.70

        # Case 2: Reddit forum (D_auth = 0.30), Consensus = 0.35, Recency = 0.50
        # Expected = 0.45 * 0.30 + 0.35 * 0.35 + 0.20 * 0.50 = 0.135 + 0.1225 + 0.10 = 0.3575
        score_low = self.scorer.calculate_composite_score(0.30, 0.35, 0.50)
        assert score_low < 0.40

    def test_classify_epistemic_status(self):
        assert self.scorer.classify_epistemic_status(0.88, domain_authority=0.85) == EpistemicStatus.VERIFIED
        assert self.scorer.classify_epistemic_status(0.70, domain_authority=0.70) == EpistemicStatus.VERIFIED
        assert self.scorer.classify_epistemic_status(0.55, domain_authority=0.60) == EpistemicStatus.UNVERIFIED
        assert self.scorer.classify_epistemic_status(0.35, domain_authority=0.30) == EpistemicStatus.ASSUMED

        # Edge case: Domain anonim/sosmed dengan composite tinggi murni karena recency tidak boleh VERIFIED
        assert self.scorer.classify_epistemic_status(0.72, domain_authority=0.25) == EpistemicStatus.UNVERIFIED


class TestEpistemicGroundingValidator:
    """Pengujian ekstraksi fakta ber-grounding dan kepatuhan kontrak Step 0."""

    def setup_method(self):
        self.validator = EpistemicGroundingValidator()

    def test_ground_fact_and_formatting(self):
        res = SearchXNGResult(
            title="CaMeL Defense for Prompt Injection",
            url="https://arxiv.org/abs/2503.18813",
            content="CaMeL Defense provides provable non-interference security guarantees for untrusted web corpora.",
            engine="searxng",
            publish_date="2026-03-24",
            category="science"
        )
        fact = self.validator.ground_result(res)

        assert fact.domain == "arxiv.org"
        assert fact.epistemic_status == EpistemicStatus.VERIFIED
        assert fact.credibility_score >= 0.70
        assert fact.domain_authority == 1.0

        formatted = fact.to_formatted_string()
        # Harus memuat status epistemik, skor numerik, dan sitasi domain asli
        assert "[VERIFIED]" in formatted
        assert "Domain: arxiv.org" in formatted
        assert "Score:" in formatted
        assert "CaMeL Defense" in formatted

    def test_ground_corpus_sorting_and_labels(self):
        r_gov = SearchXNGResult(
            title="Regulasi AI Nasional 2026",
            url="https://kemkominfo.go.id/berita/regulasi-ai",
            content="Pemerintah resmi menerbitkan regulasi tata kelola kecerdasan artifisial nasional tahun 2026.",
            engine="google"
        )
        r_forum = SearchXNGResult(
            title="Rumor Bocoran AI Model Baru",
            url="https://reddit.com/r/localllama/comments/rumor",
            content="Ada rumor anonim di forum bahwa model baru akan segera dirilis minggu depan.",
            engine="bing"
        )
        r_news = SearchXNGResult(
            title="Investasi AI Melonjak di Asia Tenggara",
            url="https://reuters.com/tech/sea-ai-investment",
            content="Laporan Reuters menunjukkan aliran modal investasi ke startup kecerdasan artifisial naik pesat.",
            engine="duckduckgo"
        )

        facts = self.validator.ground_corpus([r_gov, r_forum, r_news])
        assert len(facts) == 3
        # Terurut dari skor kredibilitas tertinggi
        assert facts[0].credibility_score >= facts[1].credibility_score >= facts[2].credibility_score

        # Domain gov dan reuters harus terverifikasi
        gov_fact = next(f for f in facts if f.domain == "kemkominfo.go.id")
        assert gov_fact.epistemic_status == EpistemicStatus.VERIFIED
        assert gov_fact.credibility_score >= 0.70

        # Reddit harus UNVERIFIED atau ASSUMED
        reddit_fact = next(f for f in facts if f.domain == "reddit.com")
        assert reddit_fact.epistemic_status in (EpistemicStatus.UNVERIFIED, EpistemicStatus.ASSUMED)
        assert reddit_fact.credibility_score < 0.70

    def test_export_step0_contract(self):
        f1 = GroundedFact(
            claim="CaMeL Defense architecture implements XML spotlighting.",
            epistemic_status=EpistemicStatus.VERIFIED,
            credibility_score=0.95,
            domain="arxiv.org",
            source_url="https://arxiv.org/abs/2503.18813",
            domain_authority=1.0,
            consensus_score=0.85,
            recency_score=1.0,
            title="CaMeL Defense"
        )
        f2 = GroundedFact(
            claim="OpenAPI 3.1.0 standardizes schema modeling.",
            epistemic_status=EpistemicStatus.VERIFIED,
            credibility_score=0.95,
            domain="spec.openapis.org",
            source_url="https://spec.openapis.org/oas/v3.1.0",
            domain_authority=0.95,
            consensus_score=0.90,
            recency_score=1.0,
            title="OpenAPI 3.1.0"
        )

        contract = self.validator.export_step0_contract(
            query="arsitektur keamanan ai",
            facts=[f1, f2],
            overall_credibility=0.95
        )

        assert contract["contract"] == "01-step0-research"
        assert contract["producer"] == "A04-Domain-Credibility-Scorer"
        assert "B-division-agents" in contract["consumers"]
        assert contract["payload"]["min_credibility_score"] == 0.70
        assert contract["payload"]["verified_claims_count"] == 2
        assert len(contract["payload"]["sources"]) == 2
        assert contract["integrity"]["sha256"] is not None


class TestWebResearchServiceIntegration:
    """Pengujian integrasi end-to-end WebResearchService dengan DomainCredibilityScorer."""

    @pytest.mark.asyncio
    async def test_research_generates_grounded_facts_and_credibility(self):
        mock_raw_results = [
            SearchXNGResult(
                title="Pemerintah Luncurkan Panduan Etika Kecerdasan Artifisial",
                url="https://kemkominfo.go.id/berita/ai-ethics",
                content="Kementerian Kominfo merilis surat edaran panduan etika kecerdasan artifisial nasional untuk seluruh sektor.",
                engine="google",
                publish_date="2026-08-15",
                category="news",
                relevance_score=0.85,
            ),
            SearchXNGResult(
                title="Dampak Ekonomi AI Terhadap Pasar Tenaga Kerja",
                url="https://ekonomi.bisnis.com/ai-impact",
                content="Laporan riset mencatat produktivitas industri meningkat 18 persen dengan adopsi kecerdasan artifisial.",
                engine="duckduckgo",
                publish_date="2026-09-01",
                category="news",
                relevance_score=0.80,
            ),
        ]
        mock_report = SearchXNGReport(
            query="etika kecerdasan artifisial",
            category="news",
            results=mock_raw_results,
            total_results=2,
            engines_used=["google", "duckduckgo"],
        )

        research_svc = WebResearchService()
        with patch.object(research_svc.searchxng, "search_news", return_value=mock_report):
            report = await research_svc.research("etika kecerdasan artifisial", research_type="news")

        assert report.query == "etika kecerdasan artifisial"
        assert len(report.web_results) == 2
        assert len(report.summarized_facts) > 0
        assert len(report.grounded_facts) > 0

        # Validasi skor kredibilitas agregat
        assert report.credibility_score >= 0.70
        assert report.verified_claims_count >= 1

        # Cek format setiap fakta
        for fact_str in report.summarized_facts:
            assert any(tag in fact_str for tag in ["[VERIFIED]", "[UNVERIFIED]", "[ASSUMED]"])
            assert "Score:" in fact_str
            assert "Domain:" in fact_str

        # Validasi export kontrak Step 0
        step0_contract = report.export_step0_contract()
        assert step0_contract["producer"] == "A04-Domain-Credibility-Scorer"
        assert step0_contract["payload"]["verified_claims_count"] >= 1

        # Validasi to_dict dan to_text
        d = report.to_dict()
        assert "grounded_facts" in d
        assert "min_credibility_score" in d
        assert d["min_credibility_score"] == 0.70

        t = report.to_text()
        assert "Laporan Riset Internet (SearXNG)" in t
        assert "Skor kredibilitas:" in t
        assert "Klaim terverifikasi:" in t
