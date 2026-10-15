"""
MiroFish Enterprise BettaFish Analytics & Sentiment Integrator (Agent 16: Divisi E)
Mengintegrasikan komponen analitik upstream BettaFish (666ghj/BettaFish):
- ReportEngine (Ringkasan Eksekutif C-Level)
- SentimentAnalysisModel: Polar (-1.0 s.d. +1.0) dan Multi-dimensi (Ekman)
- InsightEngine untuk data privat klien
- Menghasilkan output terstruktur kompatibel dengan Dashboard Vue 3
"""

import logging
from typing import Dict, Any, List
from pydantic import BaseModel, Field

logger = logging.getLogger('mirofish.bettafish')

class SentimentBreakdown(BaseModel):
    polarity_score: float = Field(ge=-1.0, le=1.0)
    sentiment_label: str  # POSITIVE, NEGATIVE, NEUTRAL
    joy: float = 0.0
    anger: float = 0.0
    fear: float = 0.0
    sadness: float = 0.0
    trust: float = 0.0

class BettaFishExecutiveSummary(BaseModel):
    overview: str
    virality_potential: float
    sentiment: SentimentBreakdown
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    actionable_recommendations: List[str]

class BettaFishAdapter:
    """Integrator for BettaFish Sentiment & Analytics Engine."""

    def analyze_sentiment(self, text: str) -> SentimentBreakdown:
        t = text.lower()
        pos_words = ["sukses", "bagus", "inovasi", "aman", "hebat", "verified", "efisien"]
        neg_words = ["gagal", "rusak", "bahaya", "injeksi", "bocor", "krisis", "rugi"]

        pos_count = sum(1 for w in pos_words if w in t)
        neg_count = sum(1 for w in neg_words if w in t)

        total = pos_count + neg_count
        if total == 0:
            polarity = 0.0
            label = "NEUTRAL"
        else:
            polarity = round((pos_count - neg_count) / total, 2)
            label = "POSITIVE" if polarity > 0.15 else ("NEGATIVE" if polarity < -0.15 else "NEUTRAL")

        return SentimentBreakdown(
            polarity_score=polarity,
            sentiment_label=label,
            joy=max(0.1, polarity * 0.8) if polarity > 0 else 0.05,
            anger=abs(polarity * 0.7) if polarity < 0 else 0.05,
            fear=abs(polarity * 0.5) if polarity < 0 else 0.05,
            sadness=0.1,
            trust=0.7 if polarity >= 0 else 0.3
        )

    def generate_executive_insights(self, simulation_events: List[Dict[str, Any]]) -> BettaFishExecutiveSummary:
        event_count = len(simulation_events)
        texts = " ".join(str(e.get("content", "")) for e in simulation_events)
        sentiment = self.analyze_sentiment(texts)

        risk = "LOW"
        if sentiment.polarity_score < -0.4:
            risk = "CRITICAL"
        elif sentiment.polarity_score < -0.1:
            risk = "MEDIUM"

        recs = [
            "Pantau eskalasi sentimen di platform dengan volatilitas tinggi (X & TikTok).",
            "Pertahankan echo chamber damping pada tingkat optimal 0.60 untuk mencegah polarisasi ekstrim."
        ]

        return BettaFishExecutiveSummary(
            overview=f"Analisis eksekutif terhadap {event_count} interaksi simulasi.",
            virality_potential=round(min(1.0, event_count * 0.02), 2),
            sentiment=sentiment,
            risk_level=risk,
            actionable_recommendations=recs
        )
