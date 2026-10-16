"""
MiroFish Enterprise Domain Credibility Scorer & Epistemic Grounding Validator
(Agent 04: Divisi Riset / R2P)

Implementasi Dokumen 8 & Master Plan MiroFish Enterprise v3.1 / v3.2:
- Penilaian kredibilitas domain multi-tier berbasis formula matematis:
    S_cred(k) = w1 * D_auth(k) + w2 * C_consensus(k) + w3 * exp(-alpha * Delta_t_k)
  dengan:
    w1 = 0.45 (Domain Authority)
    w2 = 0.35 (Cross-source Consensus)
    w3 = 0.20 (Recency Decay)
    alpha = 0.05 / hari
- Tingkat otoritas domain D_auth:
    >= 0.70 untuk media kredibel, jurnal akademik, institusi riset, lembaga pemerintah
    < 0.50 untuk media sosial, forum diskusi terbuka / anonim
- Pelabelan status epistemik 3-tingkat:
    [VERIFIED]   : S_cred >= 0.70 (didukung domain kredibel dan/atau konsensus multi-sumber)
    [UNVERIFIED] : 0.40 <= S_cred < 0.70 (otoritas moderat / minim konsensus)
    [ASSUMED]    : S_cred < 0.40 (sumber anonim, media sosial, atau klaim tanpa verifikasi)
- Setiap fakta memiliki skor kredibilitas numerik dan sitasi domain asli.
- Kompatibel dengan pipeline kontrak Step 0 (contracts/01-step0-research.json).
"""

import math
import re
import urllib.parse
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Set, Tuple


class EpistemicStatus:
    """Konstanta status epistemik 3-tingkat."""
    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    ASSUMED = "ASSUMED"


# Bobot otoritas domain bawaan (Dokumen 8)
DOMAIN_AUTHORITY_TIERS: Dict[str, float] = {
    # 1. Akademik & Riset (1.00)
    "arxiv.org": 1.00,
    "biorxiv.org": 1.00,
    "medrxiv.org": 1.00,
    "nature.com": 1.00,
    "sciencedirect.com": 1.00,
    "springer.com": 1.00,
    "ieee.org": 1.00,
    "acm.org": 1.00,
    "scholar.google.com": 1.00,
    "nih.gov": 1.00,
    "ncbi.nlm.nih.gov": 1.00,
    "jstor.org": 1.00,

    # 2. Lembaga Pemerintah, Regulator, & Standar Resmi (0.95)
    "who.int": 0.95,
    "un.org": 0.95,
    "bis.org": 0.95,
    "imf.org": 0.95,
    "worldbank.org": 0.95,
    "oecd.org": 0.95,
    "spec.openapis.org": 0.95,
    "w3.org": 0.95,
    "ietf.org": 0.95,
    "iso.org": 0.95,
    "kemkominfo.go.id": 0.95,
    "kominfo.go.id": 0.95,
    "bi.go.id": 0.95,
    "ojk.go.id": 0.95,
    "kemenkeu.go.id": 0.95,
    "bps.go.id": 0.95,

    # 3. Kantor Berita & Media Pers Terverifikasi (0.85) - >= 0.70
    "reuters.com": 0.85,
    "apnews.com": 0.85,
    "bloomberg.com": 0.85,
    "bbc.com": 0.85,
    "bbc.co.uk": 0.85,
    "afp.com": 0.85,
    "ft.com": 0.85,
    "wsj.com": 0.85,
    "nytimes.com": 0.85,
    "theguardian.com": 0.85,
    "cnn.com": 0.85,
    "cnbc.com": 0.85,
    "antara.co.id": 0.85,
    "antaranews.com": 0.85,
    "kompas.com": 0.85,
    "tempo.co": 0.85,
    "kontan.co.id": 0.85,
    "bisnis.com": 0.85,
    "thejakartapost.com": 0.85,

    # 4. Portal Mainstream, Ensiklopedia & Media Teknologi (0.60)
    "wikipedia.org": 0.60,
    "techcrunch.com": 0.60,
    "theverge.com": 0.60,
    "wired.com": 0.60,
    "arstechnica.com": 0.60,
    "forbes.com": 0.60,
    "detik.com": 0.60,
    "liputan6.com": 0.60,
    "tribunnews.com": 0.60,
    "kumparan.com": 0.60,
    "idntimes.com": 0.60,
    "medium.com": 0.55,
    "substack.com": 0.55,

    # 5. Media Sosial, Forum Publik & Diskusi Anonim (0.30) - < 0.50
    "reddit.com": 0.30,
    "twitter.com": 0.30,
    "x.com": 0.30,
    "facebook.com": 0.30,
    "instagram.com": 0.30,
    "tiktok.com": 0.30,
    "kaskus.co.id": 0.30,
    "quora.com": 0.35,
    "4chan.org": 0.15,
    "discord.com": 0.25,
    "threads.net": 0.30,
    "telegram.org": 0.25,
}

# Pola TLD Otoritatif
TLD_ACADEMIC_PATTERNS = (r"\.edu$", r"\.ac\.[a-z]{2,3}$", r"\.edu\.[a-z]{2,3}$")
TLD_GOV_PATTERNS = (r"\.gov$", r"\.go\.[a-z]{2,3}$", r"\.gov\.[a-z]{2,3}$", r"\.mil$")


@dataclass
class SourceCredibility:
    """Evaluasi kredibilitas komprehensif untuk satu sumber web."""
    domain: str
    url: str
    domain_authority: float
    consensus_score: float
    recency_score: float
    composite_score: float
    epistemic_status: str
    is_verified: bool
    title: str = ""
    engine: str = "unknown"
    publish_date: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain,
            "url": self.url,
            "domain_authority": round(self.domain_authority, 4),
            "consensus_score": round(self.consensus_score, 4),
            "recency_score": round(self.recency_score, 4),
            "composite_score": round(self.composite_score, 4),
            "epistemic_status": self.epistemic_status,
            "is_verified": self.is_verified,
            "title": self.title,
            "engine": self.engine,
            "publish_date": self.publish_date,
        }


@dataclass
class GroundedFact:
    """Fakta ber-grounding dengan skor numerik dan sitasi domain asli."""
    claim: str
    epistemic_status: str           # "VERIFIED", "UNVERIFIED", "ASSUMED"
    credibility_score: float        # S_cred (0.0 to 1.0)
    domain: str                     # sitasi domain asli (e.g. "reuters.com")
    source_url: str
    domain_authority: float
    consensus_score: float
    recency_score: float
    title: str = ""
    engine: str = "unknown"
    publish_date: Optional[str] = None

    def to_formatted_string(self) -> str:
        """Format standar: [STATUS] [Score: 0.85 | Domain: domain.com] Snippet fakta..."""
        return f"[{self.epistemic_status}] [Score: {self.credibility_score:.2f} | Domain: {self.domain}] {self.claim}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim": self.claim,
            "epistemic_status": self.epistemic_status,
            "credibility_score": round(self.credibility_score, 4),
            "domain": self.domain,
            "source_url": self.source_url,
            "domain_authority": round(self.domain_authority, 4),
            "consensus_score": round(self.consensus_score, 4),
            "recency_score": round(self.recency_score, 4),
            "title": self.title,
            "engine": self.engine,
            "publish_date": self.publish_date,
            "formatted": self.to_formatted_string()
        }


class DomainCredibilityScorer:
    """
    Mesin Penilai Kredibilitas Domain berdasarkan Formula Komposit Dokumen 8:
    S_cred(k) = w1 * D_auth(k) + w2 * C_consensus(k) + w3 * exp(-alpha * Delta_t_k)
    """

    def __init__(
        self,
        w1: float = 0.45,
        w2: float = 0.35,
        w3: float = 0.20,
        alpha: float = 0.05,
        min_verified_threshold: float = 0.70,
        unverified_threshold: float = 0.40,
        custom_domain_tiers: Optional[Dict[str, float]] = None
    ):
        self.w1 = w1
        self.w2 = w2
        self.w3 = w3
        self.alpha = alpha
        self.min_verified_threshold = min_verified_threshold
        self.unverified_threshold = unverified_threshold
        self.domain_tiers = dict(DOMAIN_AUTHORITY_TIERS)
        if custom_domain_tiers:
            self.domain_tiers.update(custom_domain_tiers)

    @staticmethod
    def extract_domain(url: str) -> str:
        """Ekstraksi nama domain ter-normalisasi dari URL."""
        if not url:
            return "unknown"
        try:
            parsed = urllib.parse.urlparse(url)
            netloc = parsed.netloc or parsed.path.split('/')[0]
            netloc = netloc.split(':')[0].lower().strip()
            if netloc.startswith("www."):
                netloc = netloc[4:]
            return netloc or "unknown"
        except Exception:
            return "unknown"

    def get_domain_authority(self, domain_or_url: str, category: str = "general") -> float:
        """
        Menentukan Otoritas Domain D_auth(k) in [0.10, 1.00].
        - >= 0.70 untuk media kredibel / jurnal / regulator
        - < 0.50 untuk forum anonim / media sosial
        """
        domain = self.extract_domain(domain_or_url) if "://" in domain_or_url or "/" in domain_or_url else domain_or_url.lower().strip()
        if domain.startswith("www."):
            domain = domain[4:]

        # 1. Cek kecocokan langsung pada kamus otoritas domain
        if domain in self.domain_tiers:
            return self.domain_tiers[domain]

        # 2. Cek subdomain (misal: news.bbc.co.uk -> bbc.co.uk, cs.ui.ac.id -> ui.ac.id)
        parts = domain.split(".")
        if len(parts) > 2:
            root_domain = ".".join(parts[-2:])
            if root_domain in self.domain_tiers:
                return self.domain_tiers[root_domain]
            if len(parts) > 3:
                root_3 = ".".join(parts[-3:])
                if root_3 in self.domain_tiers:
                    return self.domain_tiers[root_3]

        # 3. Cek TLD Otoritatif (Akademik & Riset: 1.00)
        for pattern in TLD_ACADEMIC_PATTERNS:
            if re.search(pattern, domain):
                return 1.00

        # 4. Cek TLD Pemerintah & Standar (0.95)
        for pattern in TLD_GOV_PATTERNS:
            if re.search(pattern, domain):
                return 0.95

        # 5. Kategori berita tanpa domain terdaftar (0.50)
        if category == "news":
            return 0.50

        # 6. Domain tak dikenal bawaan (0.20)
        return 0.20

    def compute_recency_decay(
        self,
        publish_date: Optional[str],
        reference_date: Optional[datetime] = None,
        category: str = "general",
        domain: str = ""
    ) -> float:
        """
        Menghitung Recency Decay: R_k = exp(-alpha * Delta_t_k).
        Untuk literatur ilmiah, riset akademis, dan standar resmi, pengetahuan bersifat kumulatif (tanpa decay agresif).
        """
        # Literatur sains, akademik, dan standar resmi tidak mengalami decay harian berita
        if category in ("science", "research", "standards") or domain in (
            "arxiv.org", "biorxiv.org", "medrxiv.org", "nature.com", "spec.openapis.org", "w3.org"
        ):
            return 1.0

        if not publish_date:
            return 1.0

        ref = reference_date or datetime.now(timezone.utc)
        parsed_dt = None

        formats = [
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y/%m/%d",
            "%d-%m-%Y",
            "%B %d, %Y",
        ]

        clean_date = publish_date.strip()
        for fmt in formats:
            try:
                dt = datetime.strptime(clean_date[:19], fmt[:19])
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                parsed_dt = dt
                break
            except Exception:
                continue

        if not parsed_dt:
            return 1.0

        if parsed_dt.hour == 0 and parsed_dt.minute == 0 and parsed_dt.second == 0:
            delta_days = float(max(0, (ref.date() - parsed_dt.date()).days))
        else:
            delta_days = max(0.0, (ref - parsed_dt).total_seconds() / 86400.0)

        if delta_days < 1.0:
            return 1.0

        decay = math.exp(-self.alpha * delta_days)
        # Batas bawah recency agar dokumen historis kredibel tetap mempertahankan nilai bukti
        return max(0.20, min(1.0, decay))

    @staticmethod
    def _extract_tokens(text: str) -> Set[str]:
        """Ekstraksi token kata bermakna untuk evaluasi konsensus antar-sumber."""
        if not text:
            return set()
        words = re.findall(r"\b[a-zA-Z0-9_\u0080-\uffff]{4,}\b", text.lower())
        stopwords = {
            "yang", "untuk", "pada", "adalah", "dalam", "dengan", "akan", "dari", "atau",
            "this", "that", "with", "from", "have", "more", "about", "which", "their", "were"
        }
        return {w for w in words if w not in stopwords}

    def compute_cross_source_consensus(
        self,
        target_result: Any,
        all_results: List[Any]
    ) -> float:
        """
        Menghitung skor konsensus lintas-sumber C_consensus(k) in [0.0, 1.0].
        Mengukur jumlah domain unik independen lain yang mengonfirmasi topik/klaim yang sama.
        """
        if not all_results or len(all_results) <= 1:
            return 0.60

        target_url = getattr(target_result, "url", "")
        target_domain = self.extract_domain(target_url)
        target_text = f"{getattr(target_result, 'title', '')} {getattr(target_result, 'content', '')}"
        target_tokens = self._extract_tokens(target_text)

        if not target_tokens:
            return 0.50

        corroborating_domains: Set[str] = set()

        for other in all_results:
            other_url = getattr(other, "url", "")
            other_domain = self.extract_domain(other_url)
            if other_domain == target_domain:
                continue

            other_text = f"{getattr(other, 'title', '')} {getattr(other, 'content', '')}"
            other_tokens = self._extract_tokens(other_text)
            if not other_tokens:
                continue

            intersection = target_tokens.intersection(other_tokens)
            overlap_ratio = len(intersection) / max(1, min(len(target_tokens), len(other_tokens)))

            if overlap_ratio >= 0.10 or len(intersection) >= 2:
                corroborating_domains.add(other_domain)

        domain_count = len(corroborating_domains)
        if domain_count == 0:
            # Tidak ada domain lain yang mengonfirmasi klaim
            return 0.35
        elif domain_count == 1:
            return 0.70
        elif domain_count == 2:
            return 0.85
        else:
            return 1.00

    def calculate_composite_score(
        self,
        d_auth: float,
        c_consensus: float,
        r_recency: float
    ) -> float:
        """
        Hitung Indeks Komposit Kredibilitas:
        S_cred = w1 * D_auth + w2 * C_consensus + w3 * R_recency
        """
        composite = (self.w1 * d_auth) + (self.w2 * c_consensus) + (self.w3 * r_recency)
        return round(max(0.0, min(1.0, composite)), 4)

    def classify_epistemic_status(
        self,
        composite_score: float,
        domain_authority: float = 0.0
    ) -> str:
        """
        Klasifikasi status epistemik 3-tingkat:
        - [VERIFIED]   : composite_score >= 0.70
        - [UNVERIFIED] : 0.40 <= composite_score < 0.70
        - [ASSUMED]    : composite_score < 0.40 (atau domain anonim tanpa verifikasi)
        """
        if composite_score >= self.min_verified_threshold:
            if domain_authority > 0 and domain_authority < 0.35:
                return EpistemicStatus.UNVERIFIED
            return EpistemicStatus.VERIFIED
        elif composite_score >= self.unverified_threshold:
            return EpistemicStatus.UNVERIFIED
        else:
            return EpistemicStatus.ASSUMED

    def score_result(
        self,
        result: Any,
        all_results: Optional[List[Any]] = None
    ) -> SourceCredibility:
        """Evaluasi kredibilitas lengkap untuk satu hasil pencarian."""
        url = getattr(result, "url", "")
        title = getattr(result, "title", "")
        category = getattr(result, "category", "general")
        publish_date = getattr(result, "publish_date", None)
        engine = getattr(result, "engine", "unknown")

        domain = self.extract_domain(url)
        d_auth = self.get_domain_authority(domain, category=category)
        r_recency = self.compute_recency_decay(publish_date, category=category, domain=domain)
        c_consensus = self.compute_cross_source_consensus(result, all_results or [result])

        composite = self.calculate_composite_score(d_auth, c_consensus, r_recency)

        # Enforce contract boundary:
        # 1. Media kredibel / jurnal / regulator (D_auth >= 0.80) dijamin S_cred >= 0.70
        if d_auth >= 0.80 and composite < self.min_verified_threshold:
            composite = self.min_verified_threshold

        # 2. Forum anonim / media sosial (D_auth < 0.50) dibatasi S_cred < 0.50
        if d_auth < 0.50 and composite >= 0.50:
            composite = 0.45

        composite = round(composite, 4)
        epistemic_status = self.classify_epistemic_status(composite, domain_authority=d_auth)
        is_verified = (epistemic_status == EpistemicStatus.VERIFIED)

        return SourceCredibility(
            domain=domain,
            url=url,
            domain_authority=d_auth,
            consensus_score=c_consensus,
            recency_score=r_recency,
            composite_score=composite,
            epistemic_status=epistemic_status,
            is_verified=is_verified,
            title=title,
            engine=engine,
            publish_date=publish_date
        )

    def score_batch(self, results: List[Any]) -> List[SourceCredibility]:
        """Evaluasi kredibilitas untuk sekumpulan hasil pencarian."""
        if not results:
            return []
        return [self.score_result(r, all_results=results) for r in results]


class EpistemicGroundingValidator:
    """
    Validator Grounding Epistemik untuk Ekstraksi Fakta dan Entitas Korpus Web.
    Memastikan setiap fakta memiliki skor numerik dan sitasi domain asli.
    """

    def __init__(self, scorer: Optional[DomainCredibilityScorer] = None):
        self.scorer = scorer or DomainCredibilityScorer()

    def ground_result(
        self,
        result: Any,
        all_results: Optional[List[Any]] = None
    ) -> GroundedFact:
        """Grounding satu hasil pencarian menjadi fakta berlabel dengan skor dan domain."""
        cred = self.scorer.score_result(result, all_results=all_results)
        content = getattr(result, "content", "")
        snippet = content[:200].strip() if content else getattr(result, "title", "Klaim tanpa cuplikan")

        return GroundedFact(
            claim=snippet,
            epistemic_status=cred.epistemic_status,
            credibility_score=cred.composite_score,
            domain=cred.domain,
            source_url=cred.url,
            domain_authority=cred.domain_authority,
            consensus_score=cred.consensus_score,
            recency_score=cred.recency_score,
            title=cred.title,
            engine=cred.engine,
            publish_date=cred.publish_date
        )

    def ground_corpus(
        self,
        results: List[Any],
        max_facts: int = 10
    ) -> List[GroundedFact]:
        """
        Grounding seluruh korpus web hasil pencarian.
        Fakta diurutkan berdasarkan skor kredibilitas tertinggi.
        """
        if not results:
            return []

        facts: List[GroundedFact] = []
        for r in results:
            content = getattr(r, "content", "")
            if len(content) > 20:
                gf = self.ground_result(r, all_results=results)
                facts.append(gf)

        facts.sort(key=lambda f: f.credibility_score, reverse=True)
        return facts[:max_facts]

    def export_step0_contract(
        self,
        query: str,
        facts: List[GroundedFact],
        overall_credibility: float,
        status: str = "COMPLETED"
    ) -> Dict[str, Any]:
        """
        Menghasilkan payload kontrak Step 0 sesuai schema contracts/01-step0-research.json.
        """
        import hashlib

        verified_facts = [f for f in facts if f.epistemic_status == EpistemicStatus.VERIFIED]
        
        sources_map: Dict[str, Dict[str, Any]] = {}
        for f in facts:
            if f.domain not in sources_map or f.credibility_score > sources_map[f.domain]["credibility"]:
                sources_map[f.domain] = {
                    "domain": f.domain,
                    "credibility": round(f.credibility_score, 2),
                    "verified": f.epistemic_status == EpistemicStatus.VERIFIED,
                    "title": f.title or f.domain
                }

        payload = {
            "research_status": status,
            "query": query,
            "min_credibility_score": self.scorer.min_verified_threshold,
            "overall_credibility_score": round(overall_credibility, 2),
            "verified_claims_count": len(verified_facts),
            "total_facts_count": len(facts),
            "sources": list(sources_map.values())
        }

        serialized = str(sorted(payload.items())).encode("utf-8")
        payload_hash = hashlib.sha256(serialized).hexdigest()

        return {
            "contract": "01-step0-research",
            "version": "1.0.0",
            "producer": "A04-Domain-Credibility-Scorer",
            "consumers": [
                "B-division-agents",
                "A05-GraphRAG-Chunker"
            ],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "schema_version": "mirofish-contract/1.0",
            "payload": payload,
            "integrity": {
                "sha256": payload_hash,
                "previous_contract": None
            }
        }
