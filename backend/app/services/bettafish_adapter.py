"""
MiroFish Enterprise BettaFish Analytics & Sentiment Integrator (Agent 16: Divisi E)
Mengintegrasikan komponen analitik upstream BettaFish (666ghj/BettaFish):
- ReportEngine (Ringkasan Eksekutif C-Level)
- SentimentAnalysisModel: Polar (-1.0 s.d. +1.0) dan Multi-dimensi (Plutchik/Ekman)
- InsightEngine untuk data privat klien & corporate risk assessment
- Menghasilkan output terstruktur kompatibel dengan Dashboard Vue 3
- Handoff terkalibrasi untuk downstream Agent 17 (FastMCP) & Agent 18 (OpenAPI/Webhooks)
"""

import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from .bettafish_report_engine import (
    SentimentAnalysisModel_Polar,
    BettaFishInsightEngine,
    BettaFishReportEngine,
    SentimentLabel,
    RiskLevel,
    EmotionVector,
    PolarSentimentResult,
    ClaimSentimentAnalysis,
    CLevelDirectives,
    SWOTAnalysis,
    CorporateRiskAssessment,
    ExecutiveSummaryCLevel,
)

logger = logging.getLogger('mirofish.bettafish')


class SentimentBreakdown(BaseModel):
    polarity_score: float = Field(ge=-1.0, le=1.0)
    sentiment_label: str  # POSITIVE, NEGATIVE, NEUTRAL
    joy: float = 0.0
    anger: float = 0.0
    fear: float = 0.0
    sadness: float = 0.0
    trust: float = 0.0
    granular_label: Optional[str] = None
    subjectivity_score: float = 0.0
    matched_positive_words: List[str] = Field(default_factory=list)
    matched_negative_words: List[str] = Field(default_factory=list)
    valence_modifiers: List[str] = Field(default_factory=list)


class BettaFishExecutiveSummary(BaseModel):
    overview: str
    virality_potential: float
    sentiment: SentimentBreakdown
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    actionable_recommendations: List[str]
    c_level_directives: Optional[Dict[str, List[str]]] = None
    report_digest_sha256: Optional[str] = None


class BettaFishAdapter:
    """Integrator for BettaFish Sentiment & Analytics Engine."""

    def __init__(self):
        self.polar_model = SentimentAnalysisModel_Polar()
        self.insight_engine = BettaFishInsightEngine()
        self.report_engine = BettaFishReportEngine()

    def analyze_sentiment(self, text: str) -> SentimentBreakdown:
        """
        Analisis sentimen teks tunggal berbasis SentimentAnalysisModel_Polar.
        Mempertahankan kompatibilitas antarmuka legacy SentimentBreakdown.
        """
        res = self.polar_model.analyze(text)
        return SentimentBreakdown(
            polarity_score=res.polarity_score,
            sentiment_label=res.sentiment_label,
            joy=res.joy,
            anger=res.anger,
            fear=res.fear,
            sadness=res.sadness,
            trust=res.trust,
            granular_label=res.granular_label.value,
            subjectivity_score=res.subjectivity_score,
            matched_positive_words=res.matched_positive_words,
            matched_negative_words=res.matched_negative_words,
            valence_modifiers=res.valence_modifiers
        )

    def analyze_polar_sentiment(self, text: str) -> PolarSentimentResult:
        """Analisis polaritas mendalam dengan representasi model kontinu penuh."""
        return self.polar_model.analyze(text)

    def generate_executive_insights(self, simulation_events: List[Dict[str, Any]]) -> BettaFishExecutiveSummary:
        """
        Menghasilkan ringkasan wawasan eksekutif dari daftar peristiwa simulasi.
        """
        event_count = len(simulation_events)
        texts = " ".join(str(e.get("content", "")) for e in simulation_events)
        sentiment_breakdown = self.analyze_sentiment(texts)

        # Hitung risiko melalui insight engine
        polar_res = self.polar_model.analyze(texts)
        virality_potential = round(min(1.0, event_count * 0.02 + (sentiment_breakdown.subjectivity_score * 0.2)), 2)
        risk_assessment = self.insight_engine.assess_corporate_risk(
            sentiment=polar_res,
            claim_polarities=[polar_res.polarity_score],
            virality_potential=virality_potential
        )

        recs = [
            "Pantau eskalasi sentimen di platform dengan volatilitas tinggi (X & TikTok).",
            "Pertahankan echo chamber damping pada tingkat optimal 0.60 untuk mencegah polarisasi ekstrim."
        ]
        if risk_assessment.early_warning_escalation:
            recs.insert(0, "Peringatan Dini: Potensi kaskade viral negatif terdeteksi.")

        return BettaFishExecutiveSummary(
            overview=f"Analisis eksekutif terhadap {event_count} interaksi simulasi.",
            virality_potential=virality_potential,
            sentiment=sentiment_breakdown,
            risk_level=risk_assessment.overall_risk_level.value,
            actionable_recommendations=recs,
            c_level_directives={
                "ceo": ["Jaga konsistensi komunikasi korporat."],
                "cto": ["Pastikan verifikasi hash simpul graf SHA-256."],
                "cmo": ["Stabilkan persepsi publik di platform media sosial."],
                "cro": ["Tegakkan Safe Abstention pada kueri berisiko."]
            }
        )

    def generate_c_level_report(
        self,
        topic: str,
        upstream_handoff: Optional[Dict[str, Any]] = None,
        simulation_events: Optional[List[Dict[str, Any]]] = None,
        custom_claims: Optional[List[str]] = None
    ) -> ExecutiveSummaryCLevel:
        """Menghasilkan laporan analitik C-Level komprehensif melalui ReportEngine."""
        return self.report_engine.generate_executive_report(
            topic=topic,
            upstream_handoff=upstream_handoff,
            simulation_events=simulation_events,
            custom_claims=custom_claims
        )

    def assess_corporate_risk(
        self,
        text: str,
        claim_polarities: Optional[Any] = None,
        virality_potential: float = 0.0
    ) -> CorporateRiskAssessment:
        """Menilai risiko korporat dan mendeteksi kondisi peringatan dini."""
        polar_res = self.polar_model.analyze(text)
        
        # Ekstraksi dan normalisasi polaritas klaim (bisa float atau dict {'claim': ..., 'polarity': ...})
        normalized_polarities: List[float] = []
        if claim_polarities:
            for item in claim_polarities:
                if isinstance(item, (int, float)):
                    normalized_polarities.append(float(item))
                elif isinstance(item, dict) and 'polarity' in item:
                    normalized_polarities.append(float(item['polarity']))
        
        if not normalized_polarities:
            normalized_polarities = [polar_res.polarity_score]
        else:
            # Jika teks bebas netral namun klaim memiliki polaritas kuat, selaraskan polaritas
            avg_claim_polarity = sum(normalized_polarities) / len(normalized_polarities)
            if polar_res.polarity_score == 0.0 or abs(avg_claim_polarity) > abs(polar_res.polarity_score):
                polar_res.polarity_score = avg_claim_polarity
                if avg_claim_polarity < -0.2:
                    polar_res.emotions.anger = max(polar_res.emotions.anger, 0.75)
                    polar_res.emotions.fear = max(polar_res.emotions.fear, 0.75)

        return self.insight_engine.assess_corporate_risk(
            sentiment=polar_res,
            claim_polarities=normalized_polarities,
            virality_potential=virality_potential
        )

    def get_downstream_recommendations(
        self,
        report: ExecutiveSummaryCLevel
    ) -> Dict[str, Any]:
        """Mengambil matriks rekomendasi handoff untuk downstream Agent 17 & 18."""
        return self.report_engine.get_downstream_recommendations_agent_17_18(report)
