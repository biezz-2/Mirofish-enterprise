"""
MiroFish Enterprise - Canonical MCP Models (Agent 17: Canonical FastMCP Server Architect)
Strictly-typed Pydantic schemas for 11 Canonical Tools, BettaFish Analytics, and OAuth 2.1 authentication.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# 11 Canonical Tools Input & Output Models
# ---------------------------------------------------------------------------

# Tool 1: create_simulation_project
class CreateSimulationProjectInput(BaseModel):
    project_id: str = Field(..., description="ID proyek unik untuk simulasi")
    name: str = Field(..., description="Nama atau judul proyek simulasi")
    description: str = Field("", description="Deskripsi singkat tujuan simulasi")
    target_platforms: List[str] = Field(
        default_factory=lambda: ["instagram", "linkedin", "reddit", "threads", "tiktok", "twitter", "youtube"],
        description="Daftar platform sosial target yang dimodelkan"
    )

class SimulationProjectResult(BaseModel):
    project_id: str
    name: str
    description: str
    status: str = "initialized"
    target_platforms: List[str]
    created_at: str


# Tool 2: trigger_web_research
class TriggerWebResearchInput(BaseModel):
    query: str = Field(..., description="Kueri pencarian riset web")
    project_id: str = Field("proj_default", description="ID proyek terkait")
    max_results: int = Field(10, ge=1, le=50, description="Maksimum jumlah hasil")
    search_type: str = Field("general", description="Tipe riset: general, academic, news")

class WebResearchResult(BaseModel):
    query: str
    project_id: str
    total_results: int
    credibility_score: float = Field(..., ge=0.0, le=1.0)
    epistemic_status: str = Field(..., description="Status epistemik [VERIFIED] atau [UNVERIFIED]")
    sanitized_facts: List[str]
    sources: List[Dict[str, Any]]


# Tool 3: build_knowledge_graph
class BuildKnowledgeGraphInput(BaseModel):
    project_id: str = Field(..., description="ID proyek pemilik ontologi graf")
    source_text: str = Field(..., description="Korpus teks fakta riset untuk diekstrak ke graf")
    group_id: Optional[str] = Field(None, description="Grup isolasi subgraf")
    extract_relations: bool = Field(True, description="Apakah mengekstrak relasi bitemporal antar entitas")

class KnowledgeGraphResult(BaseModel):
    project_id: str
    nodes_count: int
    edges_count: int
    status: str = "indexed"
    readiness_score: float = Field(..., ge=0.0, le=1.0)
    graph_digest_sha256: str


# Tool 4: generate_agent_profiles
class GenerateAgentProfilesInput(BaseModel):
    project_id: str = Field(..., description="ID proyek")
    count: int = Field(10, ge=1, le=1000, description="Jumlah profil agen yang dihasilkan")
    archetype: str = Field("balanced", description="Distribusi arketipe: balanced, polarized, viral")
    target_platforms: Optional[List[str]] = Field(None, description="Platform preferensi profil agen")

class AgentProfilesResult(BaseModel):
    project_id: str
    agents_generated: int
    archetype: str
    sample_profiles: List[Dict[str, Any]]
    ocean_summary: Dict[str, float]


# Tool 5: calibrate_platform_algorithms
class CalibratePlatformAlgorithmsInput(BaseModel):
    platform: str = Field(..., description="Nama platform (misal: instagram, linkedin, reddit, threads, tiktok, twitter, youtube)")
    outgroup_penalty: Optional[float] = Field(None, ge=0.0, le=2.0, description="Penalti interaksi outgroup")
    echo_damping: Optional[float] = Field(None, ge=0.0, le=1.0, description="Faktor peredam echo chamber")

class PlatformCalibrationResult(BaseModel):
    platform: str
    calibration_weights: Dict[str, float]
    is_calibrated: bool = True
    damping_factor: float
    algorithm_version: str = "v3.2-recsys"


# Tool 6: execute_parallel_simulation
class ExecuteParallelSimulationInput(BaseModel):
    project_id: str = Field(..., description="ID proyek")
    simulation_id: str = Field(..., description="ID sesi eksekusi simulasi")
    max_rounds: int = Field(10, ge=1, le=100, description="Jumlah superstep putaran BSP")
    platform: str = Field("parallel", description="Mode platform: parallel, multi-platform, isolated")
    run_bsp_barrier: bool = Field(True, description="Apakah menegakkan barrier sinkronisasi BSP")

class SimulationExecutionResult(BaseModel):
    simulation_id: str
    project_id: str
    rounds_completed: int
    runner_status: str = "completed"
    checkpoint_hash_sha256: str
    deadlock_detected: bool = False


# Tool 7: fetch_simulation_stream
class FetchSimulationStreamInput(BaseModel):
    simulation_id: str = Field(..., description="ID sesi simulasi")
    from_round: int = Field(0, ge=0, description="Mulai dari putaran ke-n")
    limit: int = Field(50, ge=1, le=500, description="Maksimum event yang diambil")

class SimulationStreamResult(BaseModel):
    simulation_id: str
    events_count: int
    events: List[Dict[str, Any]]
    current_round: int
    has_more: bool
    platform_breakdown: Optional[Dict[str, int]] = None
    runner_status: Optional[str] = None


# Tool 8: query_graph_insights
class QueryGraphInsightsInput(BaseModel):
    project_id: str = Field(..., description="ID proyek")
    query: str = Field(..., description="Kueri analitik simpul / relasi subgraf")
    limit: int = Field(10, ge=1, le=50, description="Batas hasil ekstraksi")
    as_of: Optional[str] = Field(None, description="Bitemporal timestamp (valid_at)")

class GraphInsightsResult(BaseModel):
    project_id: str
    query: str
    facts: List[str]
    total_found: int
    nli_confidence_avg: float


# Tool 9: generate_executive_report
class GenerateExecutiveReportInput(BaseModel):
    topic: str = Field(..., description="Topik evaluasi strategis")
    project_id: Optional[str] = Field(None, description="ID proyek")
    simulation_id: Optional[str] = Field(None, description="ID simulasi")
    verified_only: bool = Field(True, description="Hanya menyertakan klaim berstatus [VERIFIED]")

class ExecutiveReportResult(BaseModel):
    report_id: str
    title: str
    executive_summary: str
    c_level_directives: Dict[str, List[str]]
    swot_analysis: Dict[str, List[str]]
    sha256_digest: str
    abstained_questions: List[str]


# Tool 10: interview_simulation_agent
class InterviewSimulationAgentInput(BaseModel):
    simulation_id: str = Field(..., description="ID simulasi")
    agent_id: str = Field(..., description="ID agen persona")
    question: str = Field(..., description="Pertanyaan klarifikasi opini kepada agen")
    max_tokens: int = Field(256, ge=16, le=1024, description="Maksimum token jawaban")

class AgentInterviewResult(BaseModel):
    simulation_id: str
    agent_id: str
    question: str
    response_text: str
    emotional_state_ekman: Dict[str, float]
    stance_score: float = Field(..., ge=-1.0, le=1.0)


# Tool 11: audit_system_diagnostics
class AuditSystemDiagnosticsInput(BaseModel):
    include_vault: bool = Field(True, description="Apakah mengaudit integritas AES-256-GCM Vault")
    include_backends: bool = Field(True, description="Apakah mengecek kesiapan backend SearXNG, Graphiti, dan Redis")

class SystemDiagnosticsResult(BaseModel):
    status: str = "HEALTHY"
    fastmcp_port: int = 8080
    oauth_2_1: Dict[str, Any]
    backends: Dict[str, str]
    active_tools_count: int = 11
    integrity_check: str = "PASSED"


# ---------------------------------------------------------------------------
# BettaFish Downstream Analytics Tools Models (Agent 16 Alignment)
# ---------------------------------------------------------------------------

class PolarSentimentInput(BaseModel):
    text: str = Field(..., description="Teks dokumen atau klaim korporat untuk dianalisis")

class PolarSentimentResult(BaseModel):
    polarity_score: float = Field(..., ge=-1.0, le=1.0)
    sentiment_label: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    subjectivity: float = Field(..., ge=0.0, le=1.0)
    emotions: Dict[str, float]

class CorporateRiskInput(BaseModel):
    polarity_score: float = Field(..., ge=-1.0, le=1.0)
    virality_potential: float = Field(0.0, ge=0.0, le=1.0)

class CorporateRiskResult(BaseModel):
    risk_level: str
    polarization_index: float
    early_warning_triggered: bool
    containment_recommendation: str

class ExecutiveReportInput(BaseModel):
    topic: str = Field(..., description="Topik briefing eksekutif C-Level")
    claims: Optional[List[str]] = Field(None, description="Daftar klaim terverifikasi")

class ExecutiveSummaryCLevel(BaseModel):
    report_id: str
    title: str
    executive_summary: str
    swot_analysis: Dict[str, List[str]]
    c_level_directives: Dict[str, List[str]]
    report_digest_sha256: str


# ---------------------------------------------------------------------------
# OAuth 2.1 Models (RFC 6749, RFC 7636, RFC 7662, RFC 8414)
# ---------------------------------------------------------------------------

class OAuthTokenRequest(BaseModel):
    grant_type: str = Field(..., description="Tipe grant OAuth 2.1: 'authorization_code' atau 'client_credentials'")
    client_id: str = Field(..., description="ID Klien terdaftar")
    client_secret: Optional[str] = Field(None, description="Secret Klien (untuk client_credentials)")
    code: Optional[str] = Field(None, description="Kode otorisasi (untuk authorization_code)")
    redirect_uri: Optional[str] = Field(None, description="Redirect URI yang cocok")
    code_verifier: Optional[str] = Field(None, description="PKCE Code Verifier (RFC 7636)")
    scope: Optional[str] = Field(None, description="Scope izin yang diminta")

class OAuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600
    scope: str
    refresh_token: Optional[str] = None

class OAuthIntrospectionRequest(BaseModel):
    token: str = Field(..., description="Token bearer yang diintrospeksi")

class OAuthIntrospectionResponse(BaseModel):
    active: bool
    scope: Optional[str] = None
    client_id: Optional[str] = None
    sub: Optional[str] = None
    exp: Optional[int] = None
    iat: Optional[int] = None
    iss: Optional[str] = None

class OAuthAuthorizeRequest(BaseModel):
    response_type: str = Field(..., description="Wajib 'code'")
    client_id: str = Field(..., description="ID Klien terdaftar")
    redirect_uri: str = Field(..., description="Redirect URI terdaftar")
    code_challenge: str = Field(..., description="PKCE Code Challenge (RFC 7636)")
    code_challenge_method: str = Field("S256", description="Wajib 'S256' pada OAuth 2.1")
    scope: Optional[str] = Field("mcp:read", description="Scope yang diminta")
    state: Optional[str] = Field(None, description="State token CSRF")
