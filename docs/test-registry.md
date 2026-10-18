# MiroFish Enterprise - Test Suite Registry

> **Single-Source-of-Truth**: Dokumen ini dihasilkan secara otomatis dari analisis AST pada `backend/tests/` via `scripts/gen_docs.py`.
> **Status Epistemik**: `[VERIFIED]` | **Terakhir Disinkronkan**: 2026-10-18 04:59:25 UTC
> **Test Framework**: `pytest` | **Environment**: Linux x86_64 / Python 3.12+

## Ringkasan Test Suite

- **Total Berkas Test**: `48` berkas
- **Total Kasus Test (Discovered Cases)**: `449` test cases

---

## Matriks Modul & Kategori

| No | Berkas Test | Kategori Domain | Jumlah Test | Fokus & Cakupan Pengujian |
|---|---|---|---|---|
| 1 | [`test_agent18_webhooks_and_openapi.py`](#test-agent18-webhooks-and-openapi-py) | **API & OpenAPI 3.1.0 Webhooks** | `18` | Unit & Integration Test Suite for Agent 18: |
| 2 | [`test_all_steps.py`](#test-all-steps-py) | **E2E Lifecycle Pipeline** | `0` | Pengujian fungsionalitas komponen |
| 3 | [`test_anti_injection.py`](#test-anti-injection-py) | **Step 0 - Prompt Injection Shield** | `20` | Test suite untuk MiroFish Enterprise CaMeL 3-Layer Prompt Shield & Content Sanitizer (Agent 03). |
| 4 | [`test_auth.py`](#test-auth-py) | **Security & Authentication** | `7` | Pengujian fungsionalitas komponen |
| 5 | [`test_bettafish_report_engine.py`](#test-bettafish-report-engine-py) | **Step 4 - BettaFish Report Engine** | `18` | Unit & Integration Test Suite for BettaFish Analytics & Sentiment Model Integrator |
| 6 | [`test_bsp_crash_recovery.py`](#test-bsp-crash-recovery-py) | **Step 3 - BSP Crash Recovery & Barrier** | `8` | Test Suite untuk Agent 14: BSP Swarm Runner & SQLite WAL Crash Recovery |
| 7 | [`test_cascade_dynamics.py`](#test-cascade-dynamics-py) | **Step 3 - Hawkes Cascade Dynamics** | `18` | MiroFish Enterprise - Test Suite untuk Agent 13 (Divisi D: SIM) |
| 8 | [`test_decision_engine.py`](#test-decision-engine-py) | **Step 2 - DDM Decision Engine** | `11` | Unit and Integration Tests for MiroFish Enterprise Decision Engine (Agent 10: Divisi C) |
| 9 | [`test_domain_credibility.py`](#test-domain-credibility-py) | **Step 0 - Domain Credibility** | `9` | Unit & Integration Tests for Agent 04: Domain Credibility Scorer & Epistemic Grounding Validator |
| 10 | [`test_dynamic_ontology_grounding.py`](#test-dynamic-ontology-grounding-py) | **Step 1 - Dynamic Ontology Grounding** | `10` | Unit & Integration Tests for Slice 05: Dynamic Ontology Generation & Schema Grounding. |
| 11 | [`test_embedding_service.py`](#test-embedding-service-py) | **Embedding Services** | `2` | Pengujian fungsionalitas komponen |
| 12 | [`test_fastmcp_server.py`](#test-fastmcp-server-py) | **Step 5 - FastMCP Server & OAuth 2.1** | `10` | Unit & Integration Tests for Agent 17: Canonical FastMCP Server |
| 13 | [`test_graphiti_control_plane.py`](#test-graphiti-control-plane-py) | **Step 1 - Graphiti Control Plane** | `10` | Unit Tests untuk Subagent 06: Graphiti & FalkorDB/Neo4j Control Plane |
| 14 | [`test_humanoid_needs.py`](#test-humanoid-needs-py) | **Step 2 - Humanoid ODE Needs** | `11` | Test Suite for Agent 09: Humanoid ODE Basic Needs & Ekman Engine (Divisi SIM) |
| 15 | [`test_jwt_hardening.py`](#test-jwt-hardening-py) | **Security & JWT Hardening** | `16` | Unit test untuk Hardening Autentikasi JWT (P1-4). |
| 16 | [`test_llm_json_responses.py`](#test-llm-json-responses-py) | **LLM Structured JSON Parsing** | `12` | Pengujian fungsionalitas komponen |
| 17 | [`test_mcp_truthful_fallbacks.py`](#test-mcp-truthful-fallbacks-py) | **MCP Fallbacks & Truthful Abstraction** | `3` | Pengujian fungsionalitas komponen |
| 18 | [`test_multi_platform_simulation.py`](#test-multi-platform-simulation-py) | **Step 3 - Multi-Platform Simulation** | `8` | Pengujian fungsionalitas komponen |
| 19 | [`test_ontology_api_errors.py`](#test-ontology-api-errors-py) | **Step 1 - Ontology & Graph Generation** | `2` | Pengujian fungsionalitas komponen |
| 20 | [`test_ontology_attributes.py`](#test-ontology-attributes-py) | **Step 1 - Ontology & Graph Generation** | `12` | Pengujian fungsionalitas komponen |
| 21 | [`test_ontology_generator.py`](#test-ontology-generator-py) | **Step 1 - Ontology & Graph Generation** | `4` | Pengujian fungsionalitas komponen |
| 22 | [`test_openai_chat_compat.py`](#test-openai-chat-compat-py) | **LLM Provider Compatibility** | `5` | Pengujian fungsionalitas komponen |
| 23 | [`test_pii_scrubber.py`](#test-pii-scrubber-py) | **General Tests** | `17` | Unit tests untuk Modul Sanitasi PII MiroFish Enterprise (backend/app/services/pii_scrubber.py). |
| 24 | [`test_platform_matrix.py`](#test-platform-matrix-py) | **Step 3 - Platform Matrix & RecSys** | `17` | Unit and Integration Tests for MiroFish Enterprise 7-Platform Calibration Matrix (Agent 12). |
| 25 | [`test_platform_profiles.py`](#test-platform-profiles-py) | **Step 3 - Platform Matrix & RecSys** | `6` | Pengujian fungsionalitas komponen |
| 26 | [`test_profile_field_normalization.py`](#test-profile-field-normalization-py) | **Step 2 - Agent Profile Normalization** | `4` | Pengujian fungsionalitas komponen |
| 27 | [`test_psychometrics.py`](#test-psychometrics-py) | **Step 2 - Whole Trait Psychometrics** | `11` | Unit tests for MiroFish Enterprise Psychometrics Service (Agent 08 - Divisi C) |
| 28 | [`test_react_report_agent.py`](#test-react-report-agent-py) | **Step 4 - ReACT Report Analyst** | `11` | Unit Tests untuk Agent 15: ReACT ReportAgent Multi-Turn Deduction Analyst |
| 29 | [`test_recsys_funnel.py`](#test-recsys-funnel-py) | **Step 3 - RecSys Funnel & Pareto** | `15` | Unit and Integration Tests for Agent 11: 3-Stage RecSys Funnel Engineer |
| 30 | [`test_redis_auth_hardening.py`](#test-redis-auth-hardening-py) | **General Tests** | `14` | Unit Test: Redis Requirepass Client Enforcement & Database WAL Integrity |
| 31 | [`test_report_tool_result_sanitizer.py`](#test-report-tool-result-sanitizer-py) | **Step 4 - Report Tool Result Sanitizer** | `2` | Pengujian fungsionalitas komponen |
| 32 | [`test_searxng_client.py`](#test-searxng-client-py) | **Step 0 - SearXNG Client Integration** | `5` | Test suite untuk SearXNGClient (Agent 02: SearXNG Private Search & Ingestion Specialist) |
| 33 | [`test_simulation_engine_v36.py`](#test-simulation-engine-v36-py) | **Step 3 - Simulation Runner Lifecycle** | `10` | Unit Tests Komprehensif untuk MiroFish Simulation Engine v3.6: |
| 34 | [`test_simulation_prepare_failure.py`](#test-simulation-prepare-failure-py) | **Step 3 - Simulation Runner Lifecycle** | `2` | Pengujian fungsionalitas komponen |
| 35 | [`test_startup_security_guard.py`](#test-startup-security-guard-py) | **Security & Startup Fail-Fast Guard** | `6` | Unit tests for Startup Security Fail-Fast Guard (P0-2 / P0-4) |
| 36 | [`test_token_cost_estimator.py`](#test-token-cost-estimator-py) | **Token Budget & Cost Estimator** | `17` | Unit & Integration Test Suite untuk Token Budget & Cost Estimator (Subagent F) |
| 37 | [`test_v31_core.py`](#test-v31-core-py) | **Architecture - Core v3.1 Engine** | `8` | MiroFish Backend Core v3.1 Test Suite |
| 38 | [`test_v32_enterprise.py`](#test-v32-enterprise-py) | **Architecture - Enterprise v3.2 Swarm** | `16` | MiroFish Enterprise Master Plan v3.2 Automated Test Suite |
| 39 | [`test_zep_adapter_barrier.py`](#test-zep-adapter-barrier-py) | **Step 1 - Zep Memory & Graph Adapter** | `11` | Unit & Integration Test Suite for ZepAdapter, NLI Verification Barrier, and Graph Readiness Barrier. |
| 40 | [`test_zep_cloud_contracts.py`](#test-zep-cloud-contracts-py) | **Step 1 - Zep Memory & Graph Adapter** | `15` | Pengujian fungsionalitas komponen |
| 41 | [`test_zep_cloud_validation_script.py`](#test-zep-cloud-validation-script-py) | **Step 1 - Zep Memory & Graph Adapter** | `3` | Pengujian fungsionalitas komponen |
| 42 | [`test_zep_edge_paging.py`](#test-zep-edge-paging-py) | **Step 1 - Zep Memory & Graph Adapter** | `4` | Pengujian fungsionalitas komponen |
| 43 | [`test_zep_entity_reader_edges.py`](#test-zep-entity-reader-edges-py) | **Step 1 - Zep Memory & Graph Adapter** | `2` | Pengujian fungsionalitas komponen |
| 44 | [`test_zep_graph_lifecycle.py`](#test-zep-graph-lifecycle-py) | **Step 1 - Zep Memory & Graph Adapter** | `10` | Pengujian fungsionalitas komponen |
| 45 | [`test_zep_graph_memory_updater.py`](#test-zep-graph-memory-updater-py) | **Step 1 - Zep Memory & Graph Adapter** | `9` | Pengujian fungsionalitas komponen |
| 46 | [`test_zep_report_barrier.py`](#test-zep-report-barrier-py) | **Step 1 - Zep Memory & Graph Adapter** | `4` | Pengujian fungsionalitas komponen |
| 47 | [`test_zep_retry_and_client.py`](#test-zep-retry-and-client-py) | **Step 1 - Zep Memory & Graph Adapter** | `6` | Pengujian fungsionalitas komponen |
| 48 | [`test_zep_simulation_barrier.py`](#test-zep-simulation-barrier-py) | **Step 1 - Zep Memory & Graph Adapter** | `10` | Pengujian fungsionalitas komponen |

---

## Rincian Berkas & Kasus Pengujian

### `test_agent18_webhooks_and_openapi.py`

- **Lokasi File**: `backend/tests/test_agent18_webhooks_and_openapi.py`
- **Kategori**: `API & OpenAPI 3.1.0 Webhooks`
- **Total Kasus Uji**: `18` test

**Deskripsi Modul**:
> Unit & Integration Test Suite for Agent 18: Enterprise OpenAPI 3.1.0, JSON Schema 2020-12 Dialect, and Distributed Webhook Delivery Engine with HMAC-SHA256, Anti-Replay, Jittered Backoff, and Dead-Letter Queue (DLQ) Re-Drive.

| Baris | Nama Test Identifier | Tipe | Penjelasan / Assert Inti |
|---|---|---|---|
| `L58` | `test_openapi_310_version_and_dialect` | `function` | OpenAPI version must be 3.1.0 and jsonSchemaDialect must be draft 2020-12. |
| `L69` | `test_openapi_top_level_webhooks_catalog` | `function` | Top-level webhooks object must declare required enterprise events. |
| `L88` | `test_openapi_components_schema_valid_draft202012` | `function` | All schemas under components.schemas must validate against JSON Schema 2020-12. |
| `L99` | `test_openapi_documentation_endpoints` | `function` | OpenAPI JSON, YAML, and Swagger UI routes must return HTTP 200. |
| `L122` | `test_json_schema_2020_12_validation_utility` | `function` | validate_json_schema_2020_12 must accurately detect valid and invalid schemas. |
| `L147` | `test_webhook_hmac_signature_generation_and_verification` | `function` | HMAC-SHA256 signature generation and strict match. |
| `L172` | `test_webhook_anti_replay_timestamp_protection` | `function` | Signatures with expired or skewed timestamps must be rejected. |
| `L197` | `test_webhook_verify_endpoint_api` | `function` | Test POST /api/enterprise/webhooks/verify API endpoint. |
| `L220` | `test_exponential_backoff_jitter_bounds` | `function` | Verify exponential backoff calculation remains strictly within jitter boundaries. |
| `L229` | `test_webhook_p95_latency_benchmark` | `function` | Benchmark webhook delivery in fast test mode: P95 latency must be strictly < 250ms. |
| `L260` | `test_webhook_dlq_capture_and_redrive` | `function` | Failed deliveries must be queued into DLQ and re-driven upon resolution. |
| `L296` | `test_dlq_api_endpoints` | `function` | Test /api/enterprise/webhooks/dlq endpoints for inspection, replay, and purge. |
| `L325` | `test_webhook_subscriptions_crud_lifecycle` | `function` | Test full CRUD lifecycle for webhook subscriptions. |
| `L364` | `test_mock_webhook_receiver_end_to_end` | `function` | Verify mock receiver receives and logs webhook headers and payloads. |
| `L394` | `test_fastmcp_rest_proxy_and_health` | `function` | Test FastMCP REST tools catalog and health check. |
| `L411` | `test_fastmcp_tool_invocation_and_webhook_dispatch` | `function` | Invoking tool via REST must succeed and trigger MCP_TOOL_INVOKED webhook. |
| `L432` | `test_bettafish_executive_report_webhook_broadcast` | `function` | Generating C-Level executive report must automatically broadcast webhook. |
| `L448` | `test_bettafish_critical_risk_alert_webhook` | `function` | High risk assessment must trigger BETTAFISH_CRITICAL_RISK_ALERT webhook. |

---

### `test_all_steps.py`

- **Lokasi File**: `backend/tests/test_all_steps.py`
- **Kategori**: `E2E Lifecycle Pipeline`
- **Total Kasus Uji**: `0` test

**Deskripsi Modul**:
> Tidak ada modul docstring.

*(Berkas test ini berupa script runner terpadu seperti E2E sequence tanpa decorator pytest test_)*

---

### `test_anti_injection.py`

- **Lokasi File**: `backend/tests/test_anti_injection.py`
- **Kategori**: `Step 0 - Prompt Injection Shield`
- **Total Kasus Uji**: `20` test

**Deskripsi Modul**:
> Test suite untuk MiroFish Enterprise CaMeL 3-Layer Prompt Shield & Content Sanitizer (Agent 03). Memverifikasi: - L1: Regex & HTML sanitasi (script payloads, inline CSS, zero-width chars, control tokens, jailbreak, directive override). - L2: XML Spotlighting (structured delimiting & pencegahan delimiter breaking / breakout). - L3: Deterministic Passive Extractor & CaMeL Capability Gate (capability isolation, block tool execution).

| Baris | Nama Test Identifier | Tipe | Penjelasan / Assert Inti |
|---|---|---|---|
| `L28` | `test_layer1_zero_width_character_obfuscation` | `function` | Pengujian unit standar |
| `L39` | `test_layer1_bidi_and_hidden_unicode_strip` | `function` | Pengujian unit standar |
| `L54` | `test_layer1_script_tags_removal` | `function` | Pengujian unit standar |
| `L63` | `test_layer1_active_embedded_tags` | `function` | Pengujian unit standar |
| `L72` | `test_layer1_html_event_handlers` | `function` | Pengujian unit standar |
| `L81` | `test_layer1_dangerous_uri_schemes` | `function` | Pengujian unit standar |
| `L96` | `test_layer1_style_tags_and_inline_css` | `function` | Pengujian unit standar |
| `L109` | `test_layer1_css_expression_and_import` | `function` | Pengujian unit standar |
| `L134` | `test_layer1_jailbreak_patterns` | `function` | Pengujian unit standar |
| `L151` | `test_layer1_directive_overrides` | `function` | Pengujian unit standar |
| `L162` | `test_layer1_special_tokens_injection` | `function` | Pengujian unit standar |
| `L172` | `test_layer1_model_delimiters` | `function` | Pengujian unit standar |
| `L181` | `test_layer1_template_injections` | `function` | Pengujian unit standar |
| `L188` | `test_layer1_markdown_data_exfiltration` | `function` | Pengujian unit standar |
| `L200` | `test_layer2_spotlight_structure` | `function` | Pengujian unit standar |
| `L223` | `test_layer2_delimiter_breaking_defense` | `function` | Pengujian unit standar |
| `L241` | `test_layer3_deterministic_extraction` | `function` | Pengujian unit standar |
| `L263` | `test_layer3_capability_gate_enforcement` | `function` | Pengujian unit standar |
| `L289` | `test_dual_boundary_prompt_builder` | `function` | Pengujian unit standar |
| `L306` | `test_global_sanitize_untrusted_content_helper` | `function` | Pengujian unit standar |

---

### `test_auth.py`

- **Lokasi File**: `backend/tests/test_auth.py`
- **Kategori**: `Security & Authentication`
- **Total Kasus Uji**: `7` test

**Deskripsi Modul**:
> Tidak ada modul docstring.

| Baris | Nama Test Identifier | Tipe | Penjelasan / Assert Inti |
|---|---|---|---|
| `L29` | `test_missing_auth_returns_401` | `function` | Pengujian unit standar |
| `L35` | `test_invalid_auth_format_returns_401` | `function` | Pengujian unit standar |
| `L41` | `test_empty_token_returns_401` | `function` | Pengujian unit standar |
| `L47` | `test_valid_auth_returns_200` | `function` | Pengujian unit standar |
| `L52` | `test_project_route_without_auth_returns_401` | `function` | Pengujian unit standar |
| `L56` | `test_project_route_with_auth_returns_200` | `function` | Pengujian unit standar |
| `L61` | `test_idor_prevention_forbidden_id_returns_403` | `function` | Pengujian unit standar |

---

### `test_bettafish_report_engine.py`

- **Lokasi File**: `backend/tests/test_bettafish_report_engine.py`
- **Kategori**: `Step 4 - BettaFish Report Engine`
- **Total Kasus Uji**: `18` test

**Deskripsi Modul**:
> Unit & Integration Test Suite for BettaFish Analytics & Sentiment Model Integrator (Agent 16: Divisi E)  Tests: 1. Polar Sentiment Analysis (Polarity score, Valence Modifiers, Subjectivity, 8 Emotions). 2. Multilingual Coverage (Indonesian, English, Chinese). 3. Corporate Risk Assessment, Polarization Index, and Early Warning Sentinel. 4. C-Level Executive Report Synthesis (CEO, CTO, CMO, CRO Directives, SWOT, SHA-256 Integrity). 5. Downstream Handoff Matrix to Agent 17 (FastMCP) and Agent 18 (OpenAPI/Webhooks). 6. Enterprise Flask API Endpoint Integrations.

| Baris | Nama Test Identifier | Tipe | Penjelasan / Assert Inti |
|---|---|---|---|
| `L49` | `TestPolarSentimentModel.test_positive_text_evaluation` | `method` | Pengujian unit standar |
| `L60` | `TestPolarSentimentModel.test_negative_text_evaluation` | `method` | Pengujian unit standar |
| `L70` | `TestPolarSentimentModel.test_neutral_text_evaluation` | `method` | Pengujian unit standar |
| `L77` | `TestPolarSentimentModel.test_valence_shifting_negation` | `method` | Pengujian unit standar |
| `L86` | `TestPolarSentimentModel.test_valence_shifting_intensifiers_and_dampeners` | `method` | Pengujian unit standar |
| `L96` | `TestPolarSentimentModel.test_multilingual_coverage` | `method` | Pengujian unit standar |
| `L108` | `TestPolarSentimentModel.test_batch_and_stream_analysis` | `method` | Pengujian unit standar |
| `L129` | `TestBettaFishInsightEngine.test_corporate_risk_low_risk_scenario` | `method` | Pengujian unit standar |
| `L144` | `TestBettaFishInsightEngine.test_corporate_risk_critical_scenario_and_early_warning` | `method` | Pengujian unit standar |
| `L160` | `TestBettaFishInsightEngine.test_polarization_index_calculation` | `method` | Pengujian unit standar |
| `L178` | `TestBettaFishReportEngine.test_c_level_report_synthesis_with_upstream_handoff` | `method` | Pengujian unit standar |
| `L215` | `TestBettaFishReportEngine.test_downstream_recommendations_matrix` | `method` | Pengujian unit standar |
| `L246` | `TestBettaFishAdapter.test_adapter_backward_compatibility` | `method` | Pengujian unit standar |
| `L266` | `TestBettaFishAdapter.test_adapter_advanced_methods` | `method` | Pengujian unit standar |
| `L282` | `TestBettaFishAPIEndpoints.test_api_bettafish_sentiment` | `method` | Pengujian unit standar |
| `L292` | `TestBettaFishAPIEndpoints.test_api_bettafish_executive_report` | `method` | Pengujian unit standar |
| `L309` | `TestBettaFishAPIEndpoints.test_api_bettafish_risk_assessment` | `method` | Pengujian unit standar |
| `L322` | `TestBettaFishAPIEndpoints.test_api_bettafish_downstream_recommendations` | `method` | Pengujian unit standar |

---

### `test_bsp_crash_recovery.py`

- **Lokasi File**: `backend/tests/test_bsp_crash_recovery.py`
- **Kategori**: `Step 3 - BSP Crash Recovery & Barrier`
- **Total Kasus Uji**: `8` test

**Deskripsi Modul**:
> Test Suite untuk Agent 14: BSP Swarm Runner & SQLite WAL Crash Recovery (Slice 14 / Master Plan v3.2 Divisi D)  Menguji: 1. Determinisme Kriptografi SHA-256 pada State Agen & Canonical JSON. 2. SQLite WAL Checkpointing: PRAGMA WAL, atomisitas simpan/pulih, deteksi korupsi. 3. Bulk Synchronous Parallel (BSP) Supersteps: Local Computation -> Communication -> Barrier Synchronization. 4. Zero-Loss Crash Recovery: Simulasi crash pada ronde K dan auto-resume hingga target ronde tanpa kehilangan data. 5. Skalabilitas Predictive Sandbox: 50 agen x 15 ronde x 8 platform (6.000 aksi evaluasi) tanpa deadlock. 6. Handoff Parameter Terkalibrasi untuk Agent 15 (ReACT ReportAgent). 7. Enterprise API Endpoints (/api/enterprise/bsp/*).

| Baris | Nama Test Identifier | Tipe | Penjelasan / Assert Inti |
|---|---|---|---|
| `L43` | `test_bsp_agent_state_canonical_hash` | `function` | Memastikan representasi canonical hash agen deterministik dan sensitif terhadap perubahan. |
| `L85` | `test_sqlite_wal_mode_and_checkpoint` | `function` | Memverifikasi inisialisasi WAL mode, penulisan checkpoint, dan eksekusi WAL pragma. |
| `L135` | `test_bsp_barrier_sync_and_supersteps` | `function` | Menguji eksekusi superstep BSP dengan sinkronisasi penghalang (Barrier) multi-platform. |
| `L175` | `test_zero_loss_crash_simulation_and_recovery` | `function` | Mensimulasikan crash server di tengah jalan (ronde 4 dari 8), |
| `L218` | `test_predictive_sandbox_6000_actions` | `function` | Verifikasi benchmark: 50 agen x 15 ronde x 8 platform = 6.000 aksi evaluasi. |
| `L273` | `test_api_bsp_simulate` | `function` | Uji API /api/enterprise/bsp/simulate. |
| `L288` | `test_api_bsp_checkpoint_and_status` | `function` | Uji API /api/enterprise/bsp/checkpoint dan /api/enterprise/bsp/status/<job_id>. |
| `L315` | `test_api_bsp_downstream_recommendations` | `function` | Uji API /api/enterprise/bsp/downstream-recommendations. |

---

### `test_cascade_dynamics.py`

- **Lokasi File**: `backend/tests/test_cascade_dynamics.py`
- **Kategori**: `Step 3 - Hawkes Cascade Dynamics`
- **Total Kasus Uji**: `18` test

**Deskripsi Modul**:
> MiroFish Enterprise - Test Suite untuk Agent 13 (Divisi D: SIM) Hawkes Process & Rescorla-Wagner Viral Cascade Modeler  Pengujian komprehensif: 1. Rescorla-Wagner Reward Prediction Error, dopamin, habituasi, dan burnout. 2. Marked Hawkes Self-Exciting Point Process, branching ratio eta, dan Ogata thinning. 3. Mark Granovetter (1978) Threshold Model, topologi jaringan, dan tipping point. 4. Swarm Predictive Sandbox Simulation (50 agen x 15 ronde x 8 platform = 6,000 aksi). 5. Downstream Parameter Handoff Matrix untuk Agent 14 (BSP Parallel Runner). 6. Enterprise REST API endpoints integrasi.

| Baris | Nama Test Identifier | Tipe | Penjelasan / Assert Inti |
|---|---|---|---|
| `L48` | `test_rescorla_wagner_acquisition` | `function` | Verifikasi peningkatan ekspektasi dopamin V saat reward positif diperoleh. |
| `L58` | `test_rescorla_wagner_extinction` | `function` | Verifikasi peluruhan eksponensial V menuju 0 saat reward dihentikan (R=0). |
| `L70` | `test_rescorla_wagner_stateful_agent_and_burnout` | `function` | Verifikasi pembaruan state agen dan pemicuan burnout akibat kekecewaan beruntun. |
| `L88` | `test_rescorla_wagner_post_frequency` | `function` | Verifikasi bahwa frekuensi posting meningkat dengan dopamin dan turun saat burnout. |
| `L104` | `test_hawkes_intensity_baseline_and_decay` | `function` | Verifikasi bahwa intensitas Hawkes meluruh kembali ke baseline mu seiring berjalannya waktu. |
| `L117` | `test_hawkes_influence_mark_weighting` | `function` | Verifikasi mark pengaruh pengguna yang lebih tinggi memicu lonjakan intensitas lebih besar. |
| `L128` | `test_hawkes_platform_matrices_and_criticality` | `function` | Verifikasi kalkulasi parameter Hawkes dan regim kritisitas pada seluruh 8 platform. |
| `L154` | `test_hawkes_continuous_simulation_ogata` | `function` | Verifikasi simulasi proses titik kontinu Ogata thinning. |
| `L172` | `test_granovetter_basic_activation` | `function` | Verifikasi kompatibilitas dasar aturan ambang batas Granovetter. |
| `L179` | `test_granovetter_dynamic_effective_threshold` | `function` | Verifikasi bahwa dopamin tinggi dan intensitas viral menurunkan resistensi ambang batas. |
| `L190` | `test_granovetter_cascade_simulation_small_world` | `function` | Verifikasi propagasi kaskade adopsi pada topologi Small-World. |
| `L211` | `test_swarm_cascade_sandbox_full_run` | `function` | Eksekusi simulasi swarm sandbox komprehensif 50 agen x 15 ronde pada seluruh 8 platform |
| `L256` | `test_api_cascade_hawkes_endpoint` | `function` | Verifikasi endpoint POST /api/enterprise/cascade/hawkes (backward compatible). |
| `L272` | `test_api_cascade_rescorla_wagner_endpoint` | `function` | Verifikasi endpoint POST /api/enterprise/cascade/rescorla-wagner. |
| `L297` | `test_api_cascade_granovetter_endpoint` | `function` | Verifikasi endpoint POST /api/enterprise/cascade/granovetter. |
| `L319` | `test_api_cascade_hawkes_simulate_endpoint` | `function` | Verifikasi endpoint POST /api/enterprise/cascade/hawkes/simulate. |
| `L333` | `test_api_cascade_swarm_simulate_endpoint` | `function` | Verifikasi endpoint POST /api/enterprise/cascade/swarm/simulate. |
| `L348` | `test_api_platform_matrices_and_downstream` | `function` | Verifikasi endpoint GET platform-matrices & downstream-recommendations. |

---

### `test_decision_engine.py`

- **Lokasi File**: `backend/tests/test_decision_engine.py`
- **Kategori**: `Step 2 - DDM Decision Engine`
- **Total Kasus Uji**: `11` test

**Deskripsi Modul**:
> Unit and Integration Tests for MiroFish Enterprise Decision Engine (Agent 10: Divisi C) Mencakup: 1. Kenneth Train Nested Logit (GEV model): Backward compatibility & 3-level hierarchy. 2. Relaksasi IIA (Independence of Irrelevant Alternatives) lintas nest. 3. Inclusive Value (Logsum) numerik stabil & skala mu. 4. Ratcliff Drift Diffusion Model (DDM): Solusi analitik closed-form vs simulasi stokastik. 5. Modulasi psikologis DDM (afek, drift rate, dwell time). 6. Kahneman-Tversky Cumulative Prospect Theory: Loss aversion (lambda = 2.25) & S-curve. 7. Pembobotan probabilitas non-linear (overweighting risiko backlash kecil). 8. Mekanisme Sensor-Diri (Self-Censorship / Chilling Effect) pada konten berisiko. 9. Integrasi End-to-End dengan Agent 08 (Psychometrics) & Agent 09 (Humanoid Needs ODE). 10. Swarm Predictive Sandbox: Validasi Pareto 90:10 lurker-to-contributor rule. 11. Deteksi Anomali (Chilling Effect Spiral, Impulsive Polarization) & Handoff ke Agent 11 RecSys Funnel.

| Baris | Nama Test Identifier | Tipe | Penjelasan / Assert Inti |
|---|---|---|---|
| `L34` | `test_nested_logit_backward_compatibility` | `function` | Pengujian unit standar |
| `L50` | `test_hierarchical_nested_logit_3_levels` | `function` | Pengujian unit standar |
| `L83` | `test_iia_relaxation_across_nests` | `function` | Pengujian unit standar |
| `L107` | `test_logsum_inclusive_values_monotonicity` | `function` | Pengujian unit standar |
| `L124` | `test_ratcliff_ddm_analytical_vs_simulation` | `function` | Pengujian unit standar |
| `L156` | `test_ddm_psychological_modulation` | `function` | Pengujian unit standar |
| `L169` | `test_prospect_theory_loss_aversion` | `function` | Pengujian unit standar |
| `L190` | `test_self_censorship_mechanism` | `function` | Pengujian unit standar |
| `L235` | `test_agent_08_09_end_to_end_orchestration` | `function` | Pengujian unit standar |
| `L268` | `test_swarm_simulation_pareto_and_shock` | `function` | Pengujian unit standar |
| `L297` | `test_anomaly_detection_and_recsys_handoff` | `function` | Pengujian unit standar |

---

### `test_domain_credibility.py`

- **Lokasi File**: `backend/tests/test_domain_credibility.py`
- **Kategori**: `Step 0 - Domain Credibility`
- **Total Kasus Uji**: `9` test

**Deskripsi Modul**:
> Unit & Integration Tests for Agent 04: Domain Credibility Scorer & Epistemic Grounding Validator (Divisi Riset / R2P)

| Baris | Nama Test Identifier | Tipe | Penjelasan / Assert Inti |
|---|---|---|---|
| `L29` | `TestDomainCredibilityScorer.test_extract_domain` | `method` | Pengujian unit standar |
| `L37` | `TestDomainCredibilityScorer.test_domain_authority_hierarchy` | `method` | Pengujian unit standar |
| `L77` | `TestDomainCredibilityScorer.test_recency_decay` | `method` | Pengujian unit standar |
| `L98` | `TestDomainCredibilityScorer.test_cross_source_consensus` | `method` | Pengujian unit standar |
| `L130` | `TestDomainCredibilityScorer.test_composite_credibility_calculation` | `method` | Pengujian unit standar |
| `L143` | `TestDomainCredibilityScorer.test_classify_epistemic_status` | `method` | Pengujian unit standar |
| `L159` | `TestEpistemicGroundingValidator.test_ground_fact_and_formatting` | `method` | Pengujian unit standar |
| `L182` | `TestEpistemicGroundingValidator.test_ground_corpus_sorting_and_labels` | `method` | Pengujian unit standar |
| `L217` | `TestEpistemicGroundingValidator.test_export_step0_contract` | `method` | Pengujian unit standar |

---

### `test_dynamic_ontology_grounding.py`

- **Lokasi File**: `backend/tests/test_dynamic_ontology_grounding.py`
- **Kategori**: `Step 1 - Dynamic Ontology Grounding`
- **Total Kasus Uji**: `10` test

**Deskripsi Modul**:
> Unit & Integration Tests for Slice 05: Dynamic Ontology Generation & Schema Grounding. Tests PascalCase entity names, SCREAMING_SNAKE relation types, Pydantic schema validation, adaptive semantic chunking, and Step 0 research grounding.

| Baris | Nama Test Identifier | Tipe | Penjelasan / Assert Inti |
|---|---|---|---|
| `L48` | `TestCasingConventions.test_to_pascal_case` | `method` | Pengujian unit standar |
| `L64` | `TestCasingConventions.test_to_screaming_snake_case` | `method` | Pengujian unit standar |
| `L74` | `TestPydanticOntologyModels.test_entity_definition_validation` | `method` | Pengujian unit standar |
| `L88` | `TestPydanticOntologyModels.test_relation_definition_validation` | `method` | Pengujian unit standar |
| `L101` | `TestPydanticOntologyModels.test_ontology_schema_validation` | `method` | Pengujian unit standar |
| `L121` | `TestPydanticOntologyModels.test_grounded_node_and_edge_reference_tracking` | `method` | Pengujian unit standar |
| `L154` | `TestAdaptiveSemanticChunker.test_structural_header_chunking` | `method` | Pengujian unit standar |
| `L182` | `TestAdaptiveSemanticChunker.test_text_processor_adaptive_integration` | `method` | Pengujian unit standar |
| `L203` | `TestStep0ResearchGrounding.test_ground_with_step0_research` | `method` | Pengujian unit standar |
| `L248` | `TestLocalGraphServiceEndToEnd.test_local_graph_extract_and_build` | `method` | Pengujian unit standar |

---

### `test_embedding_service.py`

- **Lokasi File**: `backend/tests/test_embedding_service.py`
- **Kategori**: `Embedding Services`
- **Total Kasus Uji**: `2` test

**Deskripsi Modul**:
> Tidak ada modul docstring.

| Baris | Nama Test Identifier | Tipe | Penjelasan / Assert Inti |
|---|---|---|---|
| `L20` | `EmbeddingServiceTest.test_batches_preserve_order_and_cache` | `method` | Pengujian unit standar |
| `L38` | `EmbeddingServiceTest.test_empty_input` | `method` | Pengujian unit standar |

---

### `test_fastmcp_server.py`

- **Lokasi File**: `backend/tests/test_fastmcp_server.py`
- **Kategori**: `Step 5 - FastMCP Server & OAuth 2.1`
- **Total Kasus Uji**: `10` test

**Deskripsi Modul**:
> Unit & Integration Tests for Agent 17: Canonical FastMCP Server Tests cover: 1. OAuth 2.1 RFC 7636 (PKCE S256) & RFC 7662 (Introspection) flows 2. FastMCP Streamable HTTP authentication gating (401 on missing/invalid token, 200 on valid) 3. Strict execution and Pydantic validation of all 11 Canonical Tools 4. BettaFish Downstream Analytics Tools (Agent 16) 5. ReAct Deduction Analyst tool dispatch integration 6. Legacy Stdio JSON-RPC 2.0 backward compatibility 7. Diagnostic health checks and port configuration

| Baris | Nama Test Identifier | Tipe | Penjelasan / Assert Inti |
|---|---|---|---|
| `L49` | `test_client` | `function` | Test client with FastMCP and OAuth 2.1 routes. |
| `L60` | `test_oauth_metadata_rfc8414` | `function` | Verifikasi metadata server otorisasi OAuth 2.1 sesuai RFC 8414. |
| `L73` | `test_oauth_pkce_authorization_code_flow` | `function` | Verifikasi alur Authorization Code dengan proteksi PKCE S256 (RFC 7636). |
| `L157` | `test_oauth_client_credentials_flow` | `function` | Verifikasi alur Client Credentials untuk client terdaftar. |
| `L186` | `test_fastmcp_streamable_http_auth_enforcement` | `function` | Verifikasi proteksi otentikasi FastMCP pada endpoint /mcp. |
| `L222` | `test_diagnostics_and_health_endpoint` | `function` | Verifikasi endpoint diagnostik sistem /health. |
| `L236` | `test_canonical_11_tools_execution` | `function` | Uji eksekusi langsung 11 Canonical Tools dengan Pydantic schemas. |
| `L313` | `test_bettafish_downstream_tools` | `function` | Uji perkakas analitik BettaFish downstream (Agent 16). |
| `L332` | `test_react_deduction_analyst_dispatch_canonical_tool` | `function` | Verifikasi integrasi ReACT Analyst memanggil FastMCP Canonical Tools. |
| `L369` | `test_legacy_stdio_backward_compatibility` | `function` | Uji kompatibilitas penuh MCPServer stdio JSON-RPC 2.0 untuk orkestrator legacy. |

---

### `test_graphiti_control_plane.py`

- **Lokasi File**: `backend/tests/test_graphiti_control_plane.py`
- **Kategori**: `Step 1 - Graphiti Control Plane`
- **Total Kasus Uji**: `10` test

**Deskripsi Modul**:
> Unit Tests untuk Subagent 06: Graphiti & FalkorDB/Neo4j Control Plane Memverifikasi: 1. Isolasi data graf multi-tenant per project_id 2. Operasi bi-temporal edge (valid_from, valid_to, point-in-time snapshot as_of) 3. Garansi latensi kueri subgraf < 100ms 4. K-hop neighborhood traversal 5. Kepatuhan implementasi GraphMemoryAdapter (create_graph, add_facts, search_temporal_facts, get_entity_context) 6. Klien FalkorDB RESP native dan fallback resiliensi 7. FastAPI Control Plane REST API endpoints (TestClient) 8. FastMCP Server tool definitions & execution 9. Integrasi GraphitiAdapter dengan GraphitiService

| Baris | Nama Test Identifier | Tipe | Penjelasan / Assert Inti |
|---|---|---|---|
| `L38` | `test_tenant_isolation` | `function` | Validasi isolasi multi-tenant: data project_A tidak bocor ke project_B. |
| `L73` | `test_bitemporal_edge_lifecycle_and_point_in_time` | `function` | Validasi siklus hidup edge bi-temporal dan snapshot point-in-time as_of. |
| `L129` | `test_subgraph_query_latency_sub_100ms` | `function` | Validasi SLA performa: latency read/write subgraf < 100ms. |
| `L160` | `test_k_hop_neighborhood_traversal` | `function` | Validasi traversal k-hop BFS di sekitar central node. |
| `L183` | `test_graph_memory_adapter_compliance` | `function` | Validasi kepatuhan terhadap GraphMemoryAdapter contract. |
| `L226` | `test_falkordb_native_resp_client_live_or_fallback` | `function` | Validasi koneksi socket RESP FalkorDB. |
| `L239` | `test_fastapi_control_plane_endpoints` | `function` | Validasi REST API FastAPI Control Plane menggunakan TestClient. |
| `L295` | `test_fastmcp_server_tools` | `function` | Validasi pendaftaran alat FastMCP. |
| `L303` | `test_graphiti_adapter_integration` | `function` | Validasi sinkronisasi penuh GraphitiAdapter ke GraphitiService. |
| `L331` | `test_graphiti_service_app_health` | `function` | Validasi ASGI app pada app.services.graphiti_service memiliki route /health. |

---

### `test_humanoid_needs.py`

- **Lokasi File**: `backend/tests/test_humanoid_needs.py`
- **Kategori**: `Step 2 - Humanoid ODE Needs`
- **Total Kasus Uji**: `11` test

**Deskripsi Modul**:
> Test Suite for Agent 09: Humanoid ODE Basic Needs & Ekman Engine (Divisi SIM) Validates: 1. Ekman 7 basic emotions and Russell Circumplex (PAD) mapping 2. System 1 Needs ODE analytical solutions, RK2 midpoint, and replenishment 3. Somatic coupling and emotional homeostatic decay 4. Bimodal 24-hour circadian clock and chronotype variation 5. Downstream parameter handoffs for Agent 10 (Nested Logit & DDM) 6. Swarm predictive sandbox simulation, acute shock response, and anomaly detection 7. Pydantic v2 legacy alias remapping and integration with Agent 08 recommendations

| Baris | Nama Test Identifier | Tipe | Penjelasan / Assert Inti |
|---|---|---|---|
| `L30` | `test_ekman_emotions_initialization_and_pad_mapping` | `function` | Memverifikasi inisialisasi default emosi Ekman dan pemetaan Circumplex Russell (PAD). |
| `L59` | `test_humanoid_needs_state_alias_remapping` | `function` | Memverifikasi Pydantic v2 model_validator remapping alias legacy (social -> social_drive, entertainment -> stimulation). |
| `L75` | `test_needs_ode_analytical_decay` | `function` | Memverifikasi solusi analitik peluruhan eksponensial ODE dN/dt = -lambda * N. |
| `L92` | `test_needs_ode_rk2_vs_analytical` | `function` | Membandingkan solusi analitik dengan solusi numerik Runge-Kutta Orde-2 (Midpoint). |
| `L107` | `test_needs_replenishment_and_clipping` | `function` | Memverifikasi pemulihan (replenishment) kebutuhan dan batas atas [0.01, 1.0]. |
| `L132` | `test_cognitive_appraisal_events` | `function` | Memverifikasi pengaruh evaluasi kognitif peristiwa terhadap pergeseran emosi Ekman. |
| `L160` | `test_somatic_coupling_and_fatigue_distress` | `function` | Memverifikasi bahwa defisit energi kritis (< 0.20) memicu distres somatis pada emosi. |
| `L177` | `test_bimodal_circadian_clock_and_chronotype` | `function` | Memverifikasi kurva sirkadian 24-jam bimodal dan pergeseran kronotipe. |
| `L199` | `test_downstream_decision_utilities_handoff` | `function` | Memverifikasi payload kalibrasi utilitas untuk Agent 10 (Nested Logit & DDM). |
| `L229` | `test_factory_from_agent_08_psychometrics` | `function` | Memverifikasi integrasi dari DownstreamRecommendation Agent 08 ke Agent 09. |
| `L246` | `test_swarm_predictive_sandbox_and_shock_recovery` | `function` | Memverifikasi simulasi sandbox prediktif swarm humanoid dengan injeksi shock dan deteksi pemulihan. |

---

### `test_jwt_hardening.py`

- **Lokasi File**: `backend/tests/test_jwt_hardening.py`
- **Kategori**: `Security & JWT Hardening`
- **Total Kasus Uji**: `16` test

**Deskripsi Modul**:
> Unit test untuk Hardening Autentikasi JWT (P1-4). Memverifikasi: 1. Token valid berhasil didekode dengan klaim user. 2. Token tanpa tanda tangan atau tanda tangan salah menghasilkan 401 ("Invalid token signature"). 3. Token kedaluwarsa (exp di masa lalu) menghasilkan 401 ("Token has expired"). 4. Token dengan manipulasi algoritma ("none", "HS384", "RS256") ditolak 401. 5. Token malformed menghasilkan 401 ("Invalid token format"). 6. Penegakan AUTH_REQUIRED memblokir rute terproteksi tanpa token valid. 7. Validasi klaim issuer (iss) dan audience (aud) saat dikonfigurasi. 8. Fungsi helper decode_token dan create_token.

| Baris | Nama Test Identifier | Tipe | Penjelasan / Assert Inti |
|---|---|---|---|
| `L64` | `test_valid_jwt_token_decodes_successfully` | `function` | Token valid dengan HS256 dan exp masa depan berhasil didekode dan mengembalikan 200. |
| `L81` | `test_valid_jwt_token_with_sub_claim` | `function` | Token valid dengan klaim standard 'sub' berhasil memetakan user id. |
| `L101` | `test_token_with_wrong_signature_returns_401` | `function` | Token yang ditandatangani dengan secret key lain wajib ditolak dengan 401 Invalid token signature. |
| `L118` | `test_token_stripped_signature_returns_401` | `function` | Token dengan signature dihilangkan (header.payload.) wajib ditolak dengan 401. |
| `L137` | `test_token_missing_signature_segment_returns_401` | `function` | Token yang hanya terdiri dari dua segmen (header.payload) wajib ditolak dengan 401 Invalid token format. |
| `L160` | `test_expired_jwt_token_returns_401` | `function` | Token dengan exp di masa lalu wajib ditolak dengan pesan 'Token has expired'. |
| `L182` | `test_manipulated_algorithm_none_rejected` | `function` | Token yang menggunakan algoritma 'none' wajib ditolak dengan 401. |
| `L199` | `test_disallowed_algorithm_hs384_rejected` | `function` | Token dengan algoritma selain HS256 (misal HS384/HS512) wajib ditolak karena pinning HS256. |
| `L219` | `test_malformed_token_returns_401` | `function` | Token dengan format acak atau korup wajib menghasilkan 401 Invalid token format. |
| `L240` | `test_auth_required_blocks_request_without_header` | `function` | Ketika AUTH_REQUIRED=True, request tanpa header Authorization diblokir dengan 401. |
| `L249` | `test_auth_required_blocks_invalid_header_format` | `function` | Header yang bukan format Bearer diblokir dengan 401. |
| `L257` | `test_auth_required_blocks_empty_token` | `function` | Header Bearer tanpa token diblokir dengan 401. |
| `L265` | `test_auth_required_false_allows_unauthenticated` | `function` | Ketika AUTH_REQUIRED=False dan tanpa header Authorization, request diizinkan (backward compat). |
| `L279` | `test_issuer_claim_validation` | `function` | Memverifikasi klaim issuer ketika JWT_ISSUER dikonfigurasi. |
| `L304` | `test_audience_claim_validation` | `function` | Memverifikasi klaim audience ketika JWT_AUDIENCE dikonfigurasi. |
| `L333` | `test_direct_decode_token_algorithm_pinning` | `function` | decode_token wajib hanya menerima algoritma yang dipin (HS256). |

---

### `test_llm_json_responses.py`

- **Lokasi File**: `backend/tests/test_llm_json_responses.py`
- **Kategori**: `LLM Structured JSON Parsing`
- **Total Kasus Uji**: `12` test

**Deskripsi Modul**:
> Tidak ada modul docstring.

| Baris | Nama Test Identifier | Tipe | Penjelasan / Assert Inti |
|---|---|---|---|
| `L49` | `test_chat_json_retries_truncated_completion_without_token_cap` | `function` | Pengujian unit standar |
| `L67` | `test_chat_json_omits_token_cap_when_requested` | `function` | Pengujian unit standar |
| `L78` | `test_chat_json_retries_empty_content_once` | `function` | Pengujian unit standar |
| `L94` | `test_chat_json_accepts_complete_object_before_trailing_text` | `function` | Pengujian unit standar |
| `L113` | `test_chat_json_rejects_a_second_json_document` | `function` | Pengujian unit standar |
| `L123` | `test_chat_json_rejects_top_level_array` | `function` | Pengujian unit standar |
| `L134` | `test_chat_json_error_does_not_echo_partial_model_output` | `function` | Pengujian unit standar |
| `L152` | `test_chat_json_falls_back_only_for_explicit_response_format_rejection` | `function` | Pengujian unit standar |
| `L176` | `test_response_format_fallback_keeps_content_retry_available` | `function` | Pengujian unit standar |
| `L206` | `test_chat_json_defaults_to_one_content_attempt` | `function` | Pengujian unit standar |
| `L222` | `test_chat_json_does_not_retry_unrelated_provider_errors` | `function` | Pengujian unit standar |
| `L246` | `test_chat_json_reports_missing_choices_without_retrying_forever` | `function` | Pengujian unit standar |

---

### `test_mcp_truthful_fallbacks.py`

- **Lokasi File**: `backend/tests/test_mcp_truthful_fallbacks.py`
- **Kategori**: `MCP Fallbacks & Truthful Abstraction`
- **Total Kasus Uji**: `3` test

**Deskripsi Modul**:
> Tidak ada modul docstring.

| Baris | Nama Test Identifier | Tipe | Penjelasan / Assert Inti |
|---|---|---|---|
| `L16` | `test_job_status_fallback_is_unavailable` | `function` | Pengujian unit standar |
| `L25` | `test_stop_fallback_does_not_claim_stop` | `function` | Pengujian unit standar |
| `L33` | `test_report_fallback_remains_unavailable` | `function` | Pengujian unit standar |

---

### `test_multi_platform_simulation.py`

- **Lokasi File**: `backend/tests/test_multi_platform_simulation.py`
- **Kategori**: `Step 3 - Multi-Platform Simulation`
- **Total Kasus Uji**: `8` test

**Deskripsi Modul**:
> Tidak ada modul docstring.

| Baris | Nama Test Identifier | Tipe | Penjelasan / Assert Inti |
|---|---|---|---|
| `L24` | `test_canonical_platforms_characteristics` | `function` | Pengujian unit standar |
| `L35` | `test_normalize_platforms` | `function` | Pengujian unit standar |
| `L55` | `test_simulation_state_lifecycle` | `function` | Pengujian unit standar |
| `L87` | `test_get_profiles_multi_platform` | `function` | Pengujian unit standar |
| `L127` | `test_simulation_parameters_multi_platform` | `function` | Pengujian unit standar |
| `L163` | `test_report_agent_persistence` | `function` | Pengujian unit standar |
| `L189` | `test_mcp_report_unavailable_fallback` | `function` | Pengujian unit standar |
| `L215` | `test_check_simulation_prepared_dynamic` | `function` | Pengujian unit standar |

---

### `test_ontology_api_errors.py`

- **Lokasi File**: `backend/tests/test_ontology_api_errors.py`
- **Kategori**: `Step 1 - Ontology & Graph Generation`
- **Total Kasus Uji**: `2` test

**Deskripsi Modul**:
> Tidak ada modul docstring.

| Baris | Nama Test Identifier | Tipe | Penjelasan / Assert Inti |
|---|---|---|---|
| `L20` | `test_ontology_api_returns_safe_truncation_error_and_failed_project` | `function` | Pengujian unit standar |
| `L49` | `test_ontology_api_does_not_expose_provider_error_body` | `function` | Pengujian unit standar |

---

### `test_ontology_attributes.py`

- **Lokasi File**: `backend/tests/test_ontology_attributes.py`
- **Kategori**: `Step 1 - Ontology & Graph Generation`
- **Total Kasus Uji**: `12` test

**Deskripsi Modul**:
> Tidak ada modul docstring.

| Baris | Nama Test Identifier | Tipe | Penjelasan / Assert Inti |
|---|---|---|---|
| `L15` | `test_normalize_string_attribute` | `function` | Pengujian unit standar |
| `L23` | `test_preserve_valid_dictionary_attribute` | `function` | Pengujian unit standar |
| `L29` | `test_reject_unusable_attribute_shapes` | `function` | Pengujian unit standar |
| `L34` | `test_attribute_list_is_non_empty_and_capped_for_zep` | `function` | Pengujian unit standar |
| `L50` | `test_generator_normalizes_entity_and_edge_attributes` | `function` | Pengujian unit standar |
| `L68` | `test_generator_adds_a_property_to_empty_custom_types` | `function` | Pengujian unit standar |
| `L78` | `test_graph_builder_safety_net_accepts_strings_and_skips_invalid_values` | `function` | Pengujian unit standar |
| `L102` | `test_graph_builder_emits_a_pinned_zep_sdk_compatible_schema` | `function` | Pengujian unit standar |
| `L150` | `test_graph_builder_passes_an_empty_entity_mapping_for_edge_only_ontology` | `function` | Pengujian unit standar |
| `L174` | `test_graph_builder_deduplicates_and_caps_edge_source_targets_for_zep` | `function` | Pengujian unit standar |
| `L209` | `test_generator_ignores_invalid_entries_and_normalizes_edge_names` | `function` | Pengujian unit standar |
| `L240` | `test_generator_caps_after_discarding_invalid_edge_endpoints` | `function` | Pengujian unit standar |

---

### `test_ontology_generator.py`

- **Lokasi File**: `backend/tests/test_ontology_generator.py`
- **Kategori**: `Step 1 - Ontology & Graph Generation`
- **Total Kasus Uji**: `4` test

**Deskripsi Modul**:
> Tidak ada modul docstring.

| Baris | Nama Test Identifier | Tipe | Penjelasan / Assert Inti |
|---|---|---|---|
| `L27` | `test_short_ontology_context_keeps_original_text` | `function` | Pengujian unit standar |
| `L36` | `test_long_ontology_context_samples_across_document` | `function` | Pengujian unit standar |
| `L52` | `test_very_long_ontology_context_selects_representative_chunks` | `function` | Pengujian unit standar |
| `L68` | `test_ontology_generation_does_not_cap_structured_output_tokens` | `function` | Pengujian unit standar |

---

### `test_openai_chat_compat.py`

- **Lokasi File**: `backend/tests/test_openai_chat_compat.py`
- **Kategori**: `LLM Provider Compatibility`
- **Total Kasus Uji**: `5` test

**Deskripsi Modul**:
> Tidak ada modul docstring.

| Baris | Nama Test Identifier | Tipe | Penjelasan / Assert Inti |
|---|---|---|---|
| `L29` | `test_gpt5_uses_completion_token_limit_without_temperature` | `function` | Pengujian unit standar |
| `L53` | `test_legacy_model_preserves_original_request_shape` | `function` | Pengujian unit standar |
| `L77` | `test_provider_error_is_propagated_without_guessing_or_retrying` | `function` | Pengujian unit standar |
| `L103` | `test_gpt5_family_detection` | `function` | Pengujian unit standar |
| `L107` | `test_extracts_text_from_supported_content_shapes` | `function` | Pengujian unit standar |

---

### `test_pii_scrubber.py`

- **Lokasi File**: `backend/tests/test_pii_scrubber.py`
- **Kategori**: `General Tests`
- **Total Kasus Uji**: `17` test

**Deskripsi Modul**:
> Unit tests untuk Modul Sanitasi PII MiroFish Enterprise (backend/app/services/pii_scrubber.py). Memverifikasi kepatuhan terhadap UU No. 27 Tahun 2022 (UU PDP): 1. Pembersihan NIK 16 digit. 2. Pembersihan nomor HP Indonesia (+62 dan 08xx). 3. Pembersihan email dan nomor kartu kredit / rekening finansial. 4. Idempotensi pembersihan teks.

| Baris | Nama Test Identifier | Tipe | Penjelasan / Assert Inti |
|---|---|---|---|
| `L32` | `test_scrub_nik_16_digit_raw` | `function` | Memastikan NIK 16 digit mentah disanitasi menjadi [REDACTED_NIK]. |
| `L39` | `test_scrub_nik_with_contextual_keywords` | `function` | Memastikan NIK dengan prefix seperti 'NIK:', 'No. KTP', 'Nomor KTP' disanitasi. |
| `L50` | `test_scrub_nik_with_separators` | `function` | Memastikan NIK dengan pemisah tanda hubung atau spasi disanitasi. |
| `L59` | `test_scrub_nik_embedded_in_narrative` | `function` | Memastikan NIK yang disematkan dalam narasi web/dokumen disanitasi. |
| `L74` | `test_scrub_phone_plus_62_formats` | `function` | Memastikan nomor telepon format internasional (+62 / 62) disanitasi. |
| `L89` | `test_scrub_phone_08xx_domestic_formats` | `function` | Memastikan nomor HP format domestik 08xx disanitasi. |
| `L105` | `test_scrub_phone_embedded_in_text` | `function` | Memastikan nomor HP dalam kalimat percakapan disanitasi. |
| `L118` | `test_scrub_email_formats` | `function` | Memastikan alamat email dengan berbagai format domain disanitasi. |
| `L132` | `test_scrub_credit_card_formatted` | `function` | Memastikan nomor kartu kredit dengan tanda hubung atau spasi disanitasi. |
| `L148` | `test_scrub_credit_card_unformatted_raw` | `function` | Memastikan nomor kartu kredit mentah 16 digit disanitasi. |
| `L155` | `test_scrub_bank_account_with_keywords` | `function` | Memastikan nomor rekening bank dengan kata kunci disanitasi. |
| `L171` | `test_scrub_pii_idempotency_single_string` | `function` | Idempotensi matematis: scrub_pii(scrub_pii(text)) == scrub_pii(text). |
| `L205` | `test_scrub_pii_tokens_invariance` | `function` | Memastikan token pengganti itu sendiri kebal terhadap scrubbing ulang. |
| `L219` | `test_scrub_personal_names` | `function` | Memastikan nama dengan sapaan/gelar resmi atau custom names disanitasi. |
| `L233` | `test_pii_detection_and_cleanliness` | `function` | Memastikan deteksi metrik PII dan pengecekan kebersihan teks berfungsi. |
| `L246` | `test_scrub_dict_nested` | `function` | Memastikan struktur dictionary bersarang dibersihkan secara rekursif. |
| `L272` | `test_non_pii_strings_preservation` | `function` | Memastikan data teknis non-PII (timestamp, UUID, metrik, skor) tidak rusak. |

---

### `test_platform_matrix.py`

- **Lokasi File**: `backend/tests/test_platform_matrix.py`
- **Kategori**: `Step 3 - Platform Matrix & RecSys`
- **Total Kasus Uji**: `17` test

**Deskripsi Modul**:
> Unit and Integration Tests for MiroFish Enterprise 7-Platform Calibration Matrix (Agent 12).

| Baris | Nama Test Identifier | Tipe | Penjelasan / Assert Inti |
|---|---|---|---|
| `L25` | `test_canonical_7_platforms_uniqueness` | `function` | Pengujian unit standar |
| `L34` | `test_platform_aliases` | `function` | Pengujian unit standar |
| `L49` | `test_extended_platforms` | `function` | Pengujian unit standar |
| `L58` | `test_pareto_90_9_1_ratios_sum_to_one` | `function` | Pengujian unit standar |
| `L68` | `test_sample_user_roles_population` | `function` | Pengujian unit standar |
| `L76` | `test_pareto_power_law_metrics_formula` | `function` | Pengujian unit standar |
| `L88` | `test_cross_platform_inequality_ranking` | `function` | Pengujian unit standar |
| `L96` | `test_sample_pareto_reach_convergence` | `function` | Pengujian unit standar |
| `L105` | `test_feed_scoring_visual_affinity` | `function` | Pengujian unit standar |
| `L117` | `test_feed_scoring_virality_decay` | `function` | Pengujian unit standar |
| `L127` | `test_swarm_simulation_all_7_platforms` | `function` | Pengujian unit standar |
| `L141` | `test_downstream_recommendations` | `function` | Pengujian unit standar |
| `L163` | `test_api_get_platforms` | `function` | Pengujian unit standar |
| `L173` | `test_api_get_platform_detail` | `function` | Pengujian unit standar |
| `L183` | `test_api_get_pareto_metrics` | `function` | Pengujian unit standar |
| `L191` | `test_api_simulate_pareto` | `function` | Pengujian unit standar |
| `L202` | `test_api_downstream_recommendations` | `function` | Pengujian unit standar |

---

### `test_platform_profiles.py`

- **Lokasi File**: `backend/tests/test_platform_profiles.py`
- **Kategori**: `Step 3 - Platform Matrix & RecSys`
- **Total Kasus Uji**: `6` test

**Deskripsi Modul**:
> Tidak ada modul docstring.

| Baris | Nama Test Identifier | Tipe | Penjelasan / Assert Inti |
|---|---|---|---|
| `L28` | `test_twitter_default_reads_generated_csv` | `function` | Pengujian unit standar |
| `L38` | `test_reddit_default_preserves_json_behavior` | `function` | Pengujian unit standar |
| `L46` | `test_explicit_platform_overrides_dual_platform_default` | `function` | Pengujian unit standar |
| `L56` | `test_invalid_platform_is_rejected` | `function` | Pengujian unit standar |
| `L63` | `test_migrate_prepared_simulation_clones_existing_profiles_without_resetting_state` | `function` | Pengujian unit standar |
| `L108` | `test_migrate_prepared_simulation_rejects_non_ready_state` | `function` | Pengujian unit standar |

---

### `test_profile_field_normalization.py`

- **Lokasi File**: `backend/tests/test_profile_field_normalization.py`
- **Kategori**: `Step 2 - Agent Profile Normalization`
- **Total Kasus Uji**: `4` test

**Deskripsi Modul**:
> Tidak ada modul docstring.

| Baris | Nama Test Identifier | Tipe | Penjelasan / Assert Inti |
|---|---|---|---|
| `L12` | `test_text_coercion_handles_none_nested_objects_and_lists` | `function` | Pengujian unit standar |
| `L19` | `test_list_coercion_flattens_nested_values_and_drops_missing_items` | `function` | Pengujian unit standar |
| `L26` | `test_profile_construction_is_the_single_normalization_boundary` | `function` | Pengujian unit standar |
| `L50` | `test_normalized_profile_serializes_to_twitter_and_reddit` | `function` | Pengujian unit standar |

---

### `test_psychometrics.py`

- **Lokasi File**: `backend/tests/test_psychometrics.py`
- **Kategori**: `Step 2 - Whole Trait Psychometrics`
- **Total Kasus Uji**: `11` test

**Deskripsi Modul**:
> Unit tests for MiroFish Enterprise Psychometrics Service (Agent 08 - Divisi C) Verifies: 1. Fleeson Whole Trait Theory density distribution (s = trait + noise) 2. Trait boundedness [0.0, 1.0] under extreme perturbation 3. DeYoung Cybernetic Big Five 10 aspects & functional drive mappings 4. Situational press modulation (threat, novelty, social, reward, structure) 5. Temporal state inertia (AR-1 autoregressive dynamic) 6. Intra-individual long-term convergence & identity retention 7. Multi-agent swarm population simulation 8. Cybernetic deadlock / freezing detection under extreme threat shock 9. Homeostasis recovery tracking 10. Calibrated downstream recommendations for Agent 09 (ODE) & Agent 10 (Decision)

| Baris | Nama Test Identifier | Tipe | Penjelasan / Assert Inti |
|---|---|---|---|
| `L30` | `test_big_five_trait_initialization` | `function` | Verify default and custom BigFiveTrait fields and constraints. |
| `L56` | `test_sample_state_fleeson_distribution` | `function` | Verify Fleeson Whole Trait sampling produces states within valid bounds. |
| `L81` | `test_deyoung_cybernetic_aspects_calculation` | `function` | Verify 10 DeYoung aspects are properly derived from momentary states. |
| `L117` | `test_situational_press_modulation` | `function` | Verify external situational press appropriately shifts personality states. |
| `L145` | `test_state_inertia_autoregressive` | `function` | Verify temporal AR(1) state inertia dampens erratic jumps between rounds. |
| `L174` | `test_density_distribution_stability` | `function` | Verify sample_distribution maintains expected mean and stability flag. |
| `L187` | `test_trajectory_core_identity_retention` | `function` | Verify Fleeson's core finding: across 50 rounds, momentary states fluctuate |
| `L211` | `test_swarm_population_simulation` | `function` | Verify multi-agent swarm simulation produces collective metrics and archetypes. |
| `L228` | `test_deadlock_detection_cybernetic_freezing` | `function` | Verify detection of cybernetic freezing when swarm faces overwhelming persistent threat. |
| `L243` | `test_homeostasis_recovery_after_shock` | `function` | Verify swarm recovers toward baseline homeostasis after an acute one-round shock. |
| `L261` | `test_downstream_recommendation` | `function` | Verify calibrated parameter generation for Agent 09 (ODE) & Agent 10 (Decision). |

---

### `test_react_report_agent.py`

- **Lokasi File**: `backend/tests/test_react_report_agent.py`
- **Kategori**: `Step 4 - ReACT Report Analyst`
- **Total Kasus Uji**: `11` test

**Deskripsi Modul**:
> Unit Tests untuk Agent 15: ReACT ReportAgent Multi-Turn Deduction Analyst Memverifikasi: 1. Siklus ReACT Multi-Turn Loop (Reasoning + Acting + Deduction) 2. Safe Abstention & Perlindungan Anti-Spekulasi (NLI Threshold >= 0.85) 3. Sitasi Wajib Simpul Graf [VERIFIED] 4. Integrasi Upstream Agent 14 (BSP Swarm Runner Provenance & SHA-256) 5. Handoff Matriks Downstream untuk Agent 16 (BettaFish Sentiment Integrator) 6. REST API Endpoints di /api/enterprise/report/*

| Baris | Nama Test Identifier | Tipe | Penjelasan / Assert Inti |
|---|---|---|---|
| `L85` | `test_react_deduction_steps_and_loop` | `function` | Memverifikasi siklus multi-turn loop ReACT menghasilkan langkah reasoning terstruktur. |
| `L110` | `test_safe_abstention_barrier_unverified_query` | `function` | Kueri tanpa simpul graf terverifikasi wajib diabstain (anti-spekulasi). |
| `L120` | `test_safe_abstention_barrier_speculative_financial` | `function` | Spekulasi finansial masa depan tanpa data empiris langsung ditolak. |
| `L131` | `test_safe_abstention_low_nli_rejection` | `function` | Simpul dengan NLI < 0.85 tidak boleh disitasi sebagai temuan terverifikasi. |
| `L149` | `test_mandatory_verified_citations` | `function` | Setiap temuan wajib menyertakan rujukan eksplisit simpul [VERIFIED]. |
| `L168` | `test_upstream_agent_14_provenance_ingestion` | `function` | Memverifikasi ingesti rantai provenance SHA-256 dan rekomendasi Agent 14. |
| `L186` | `test_downstream_agent_16_recommendations` | `function` | Memverifikasi pembentukan matriks handoff untuk Agent 16 (BettaFish). |
| `L205` | `test_hypothesis_deduction_confirmed_and_refuted` | `function` | Membuktikan deduksi membedakan hipotesis terdukung vs spekulatif. |
| `L221` | `test_enterprise_api_report_generate` | `function` | Integrasi endpoint POST /api/enterprise/report/generate. |
| `L241` | `test_enterprise_api_report_deduce` | `function` | Integrasi endpoint POST /api/enterprise/report/deduce. |
| `L257` | `test_enterprise_api_report_downstream_recommendations` | `function` | Integrasi endpoint GET /api/enterprise/report/downstream-recommendations. |

---

### `test_recsys_funnel.py`

- **Lokasi File**: `backend/tests/test_recsys_funnel.py`
- **Kategori**: `Step 3 - RecSys Funnel & Pareto`
- **Total Kasus Uji**: `15` test

**Deskripsi Modul**:
> Unit and Integration Tests for Agent 11: 3-Stage RecSys Funnel Engineer Validates: 1. Stage 1 Candidate Generation (Graph Homophily, Semantic Cosine Similarity, Stance Proximity) 2. Stage 2 Heavy Ranking (Multi-task engagement scoring across 7 platforms) 3. Stage 3 Re-Ranking with Echo Chamber Damping (0.40 - 0.80), Time Decay, Diversity Penalty & Epsilon-Greedy 4. Shannon Entropy and Stance Diversity Metrics 5. Swarm Predictive Sandbox Simulation & Downstream Calibration Handoffs (Agent 12 & 13) 6. Enterprise API Endpoint Integration

| Baris | Nama Test Identifier | Tipe | Penjelasan / Assert Inti |
|---|---|---|---|
| `L131` | `test_feed_item_instantiation_and_defaults` | `function` | Memastikan FeedItem kompatibel backward dan mendukung atribut extended. |
| `L144` | `test_cosine_similarity_and_sigmoid` | `function` | Validasi numerik kosinus embedding dan aktivasi sigmoid. |
| `L159` | `test_stage1_candidate_generation` | `function` | Tahap 1: Validasi candidate retrieval dengan homofili graf & cosine similarity. |
| `L177` | `test_stage2_heavy_ranking_multitask` | `function` | Tahap 2: Validasi multi-task scoring (like, share, reply, dwell) per platform. |
| `L200` | `test_stage2_platform_weight_calibration` | `function` | Tahap 2: Membandingkan ranking X (virality/share) vs Reddit (reply) vs TikTok (dwell). |
| `L218` | `test_stage3_echo_chamber_damping_range` | `function` | Tahap 3: Validasi peredaman ruang gema dalam rentang 0.40 - 0.80. |
| `L234` | `test_stage3_time_decay_and_topic_diversity` | `function` | Tahap 3: Validasi time decay eksponensial dan penalti diversitas topik. |
| `L247` | `test_stage3_epsilon_greedy_exploration` | `function` | Tahap 3: Epsilon-greedy serendipity exploration swapping. |
| `L260` | `test_shannon_entropy_and_diversity_metrics` | `function` | Validasi kalkulasi Shannon Entropy dan metrik stance diversity. |
| `L284` | `test_end_to_end_run_funnel` | `function` | End-to-End: Verifikasi corong 3 tahap penuh menghasilkan FunnelResult terstruktur. |
| `L302` | `test_swarm_recsys_simulation` | `function` | Swarm Sandbox: Simulasi multi-agen (50 agen x 5 ronde) membuktikan mitigasi echo-chamber. |
| `L332` | `test_upstream_agent_10_parameter_integration` | `function` | Memverifikasi parameter upstream dari Agent 10: limit=60, damping=0.75, eps=0.10. |
| `L351` | `test_edge_cases` | `function` | Penanganan edge case: korpus kosong, 1 item, nilai ekstrim. |
| `L374` | `test_api_recsys_rank_backward_compatible` | `function` | Verifikasi endpoint lama POST /api/enterprise/recsys/rank tetap berjalan 100%. |
| `L393` | `test_api_recsys_funnel_and_weights` | `function` | Verifikasi endpoint baru POST /api/enterprise/recsys/funnel dan GET /recsys/weights. |

---

### `test_redis_auth_hardening.py`

- **Lokasi File**: `backend/tests/test_redis_auth_hardening.py`
- **Kategori**: `General Tests`
- **Total Kasus Uji**: `14` test

**Deskripsi Modul**:
> Unit Test: Redis Requirepass Client Enforcement & Database WAL Integrity Memverifikasi: 1. URL parsing Redis dengan password terisi dan kosong. 2. Penolakan koneksi tanpa kredensial jika REDIS_PASSWORD diwajibkan (anonymous login prohibited). 3. Penerimaan koneksi saat kredensial valid dan pencocokan password. 4. Integrasi Config.get_redis_url() dan build_redis_url(). 5. Konsistensi SQLite WAL mode dan synchronous=NORMAL pada inisialisasi koneksi.

| Baris | Nama Test Identifier | Tipe | Penjelasan / Assert Inti |
|---|---|---|---|
| `L37` | `test_parse_redis_url_without_password` | `function` | Menguji parsing URL Redis standar tanpa autentikasi password. |
| `L50` | `test_parse_redis_url_with_password` | `function` | Menguji parsing URL Redis dengan kredensial requirepass. |
| `L63` | `test_parse_redis_url_with_username_and_ssl` | `function` | Menguji parsing URL Redis dengan username dan skema SSL (rediss://). |
| `L77` | `test_parse_redis_url_invalid_scheme` | `function` | Menguji penolakan skema URL selain redis:// atau rediss://. |
| `L87` | `test_build_redis_url` | `function` | Menguji pembuatan format URL Redis dengan dan tanpa password. |
| `L102` | `test_enforce_redis_credentials_rejection` | `function` | Memastikan penolakan keras (PermissionError) saat mencoba akses anonymous tanpa password. |
| `L112` | `test_enforce_redis_credentials_mismatch` | `function` | Memastikan penolakan saat password yang diberikan salah. |
| `L121` | `test_enforce_redis_credentials_acceptance` | `function` | Memastikan koneksi diterima saat password valid disertakan. |
| `L130` | `test_hardened_redis_client_enforcement` | `function` | Menguji HardenedRedisClient menolak anonymous login dan mengesahkan autentikasi. |
| `L170` | `test_get_hardened_redis_url_injection` | `function` | Menguji injeksi otomatis password wajib ke URL anonymous jika diminta. |
| `L183` | `test_config_redis_url_behavior` | `function` | Menguji Config.build_redis_url dan Config.get_redis_url sesuai environment. |
| `L207` | `test_sqlite_engine_wal_and_synchronous` | `function` | Memverifikasi inisialisasi koneksi SQLite langsung mengeksekusi PRAGMA WAL dan synchronous NORMAL. |
| `L227` | `test_sqlalchemy_sqlite_engine_wal_listener` | `function` | Memverifikasi hook configure_sqlite_engine mengonfigurasi koneksi SQLAlchemy ke SQLite. |
| `L243` | `test_local_graph_service_sqlite_connection` | `function` | Memverifikasi LocalGraphService.get_sqlite_connection() menerapkan PRAGMA WAL & synchronous NORMAL. |

---

### `test_report_tool_result_sanitizer.py`

- **Lokasi File**: `backend/tests/test_report_tool_result_sanitizer.py`
- **Kategori**: `Step 4 - Report Tool Result Sanitizer`
- **Total Kasus Uji**: `2` test

**Deskripsi Modul**:
> Tidak ada modul docstring.

| Baris | Nama Test Identifier | Tipe | Penjelasan / Assert Inti |
|---|---|---|---|
| `L21` | `test_strip_fake_tool_results` | `function` | Pengujian unit standar |
| `L25` | `test_preserves_legitimate_text_without_tool_result_tags` | `function` | Pengujian unit standar |

---

### `test_searxng_client.py`

- **Lokasi File**: `backend/tests/test_searxng_client.py`
- **Kategori**: `Step 0 - SearXNG Client Integration`
- **Total Kasus Uji**: `5` test

**Deskripsi Modul**:
> Test suite untuk SearXNGClient (Agent 02: SearXNG Private Search & Ingestion Specialist) Menguji: 1. Zero-tracking client header enforcement (tanpa kebocoran IP, DNT=1, Sec-GPC=1). 2. Rotasi User-Agent. 3. Multi-engine routing (Google, Bing, DuckDuckGo, Brave, arXiv). 4. Token bucket rate limiting. 5. In-memory caching dengan sub-millisecond retrieval. 6. Fallback query relaxation saat kueri awal kosong / gagal. 7. Latensi batch search < 1.2s per batch. 8. Kompatibilitas SearchXNGReport / to_dict / to_text.

| Baris | Nama Test Identifier | Tipe | Penjelasan / Assert Inti |
|---|---|---|---|
| `L34` | `test_user_agent_rotation` | `function` | Memastikan rotasi User-Agent mengembalikan string valid dari daftar modern. |
| `L44` | `test_zero_tracking_headers` | `function` | Memverifikasi kepatuhan privasi zero-tracking: |
| `L67` | `test_engine_routing_resolution` | `function` | Memverifikasi pemilihan engine berdasarkan kategori. |
| `L80` | `test_fallback_query_generation` | `function` | Memverifikasi relaksasi kueri untuk fallback saat kueri kompleks nihil hasil. |
| `L192` | `test_sync_execution_wrapper` | `function` | Memastikan metode search_sync bekerja tanpa kendala. |

---

### `test_simulation_engine_v36.py`

- **Lokasi File**: `backend/tests/test_simulation_engine_v36.py`
- **Kategori**: `Step 3 - Simulation Runner Lifecycle`
- **Total Kasus Uji**: `10` test

**Deskripsi Modul**:
> Unit Tests Komprehensif untuk MiroFish Simulation Engine v3.6: 1. Pipeline 6-Tahap (Source, Hydrator, Filter, Scorer, Selector, SideEffect) 2. Platform Profile Store (Versioned YAML & Fallback) 3. Persona Store (OCEAN, Demografi, Register Bahasa) 4. Intent Sampler (7-Kategori & Modulasi Multinomial) 5. Style Realizer (Few-Shot Retrieval & Prompt Construction) 6. Noise Layer (Singkatan Indonesia & Typo QWERTY Deterministic) 7. Opinion Dynamics & Hawkes Process (Bounded Confidence & Self-Exciting Cascade) 8. Calibration Harness (90-9-1 Rule, Heavy-Tail, Diurnal Cycle) 9. Evaluation Suite & N-Gram Leakage Checker 10. Ethics Guard (Sandbox Lock, Mandatory is_synthetic, Watermark, Audit Log)

| Baris | Nama Test Identifier | Tipe | Penjelasan / Assert Inti |
|---|---|---|---|
| `L47` | `test_feed_pipeline_six_stages` | `function` | Pengujian unit standar |
| `L101` | `test_platform_profile_store` | `function` | Pengujian unit standar |
| `L134` | `test_persona_store` | `function` | Pengujian unit standar |
| `L165` | `test_intent_sampler` | `function` | Pengujian unit standar |
| `L192` | `test_style_realizer` | `function` | Pengujian unit standar |
| `L216` | `test_noise_layer` | `function` | Pengujian unit standar |
| `L241` | `test_bounded_confidence_and_hawkes` | `function` | Pengujian unit standar |
| `L282` | `test_calibration_harness` | `function` | Pengujian unit standar |
| `L315` | `test_evaluation_suite_and_leakage` | `function` | Pengujian unit standar |
| `L348` | `test_ethics_guard` | `function` | Pengujian unit standar |

---

### `test_simulation_prepare_failure.py`

- **Lokasi File**: `backend/tests/test_simulation_prepare_failure.py`
- **Kategori**: `Step 3 - Simulation Runner Lifecycle`
- **Total Kasus Uji**: `2` test

**Deskripsi Modul**:
> Tidak ada modul docstring.

| Baris | Nama Test Identifier | Tipe | Penjelasan / Assert Inti |
|---|---|---|---|
| `L34` | `test_realtime_endpoints_expose_terminal_failure` | `function` | Pengujian unit standar |
| `L62` | `test_zero_entities_persists_failed_state_and_raises` | `function` | Pengujian unit standar |

---

### `test_startup_security_guard.py`

- **Lokasi File**: `backend/tests/test_startup_security_guard.py`
- **Kategori**: `Security & Startup Fail-Fast Guard`
- **Total Kasus Uji**: `6` test

**Deskripsi Modul**:
> Unit tests for Startup Security Fail-Fast Guard (P0-2 / P0-4) Validates that MiroFish rejects booting when SECRET_KEY is missing/dangerous or DEVELOPMENT_MODE is enabled during production execution (FLASK_DEBUG=false/0).

| Baris | Nama Test Identifier | Tipe | Penjelasan / Assert Inti |
|---|---|---|---|
| `L22` | `test_production_rejects_empty_secret_key` | `function` | Production mode must reject empty SECRET_KEY. |
| `L33` | `test_production_rejects_unset_secret_key` | `function` | Production mode with unset SECRET_KEY in environ must fail fast. |
| `L54` | `test_production_rejects_insecure_pattern_secret_keys` | `function` | Production mode must reject keys containing 'example', 'test', or 'mirofish-enterprise-secret-key-2026'. |
| `L66` | `test_production_rejects_development_mode_enabled` | `function` | Production mode must reject DEVELOPMENT_MODE=true or 1. |
| `L78` | `test_production_accepts_valid_configuration` | `function` | Production mode boots cleanly when SECRET_KEY is cryptographically secure and DEVELOPMENT_MODE=false. |
| `L92` | `test_development_mode_bypasses_guard` | `function` | When FLASK_DEBUG=true, development values and mock keys are permitted without raising RuntimeError. |

---

### `test_token_cost_estimator.py`

- **Lokasi File**: `backend/tests/test_token_cost_estimator.py`
- **Kategori**: `Token Budget & Cost Estimator`
- **Total Kasus Uji**: `17` test

**Deskripsi Modul**:
> Unit & Integration Test Suite untuk Token Budget & Cost Estimator (Subagent F) Memvalidasi kalkulasi baseline empiris OASIS (~335.6k token / 100 agen / 10 ronde), skala kecil (10 agen), alokasi 4 fase, pricing multi-model, dan deteksi over-budget.

| Baris | Nama Test Identifier | Tipe | Penjelasan / Assert Inti |
|---|---|---|---|
| `L28` | `TestTokenCostEstimatorBaseline.test_oasis_standard_scale_100_agents` | `method` | Verifikasi bahwa 100 agen, 10 ronde menghasilkan persis baseline empiris OASIS (335.6k token). |
| `L39` | `TestTokenCostEstimatorBaseline.test_small_scale_10_agents` | `method` | Verifikasi bahwa skala kecil (10 agen, 10 ronde) menghasilkan persis 10% dari baseline OASIS (33,560 token). |
| `L50` | `TestTokenCostEstimatorBaseline.test_functional_helper_estimate_tokens` | `method` | Verifikasi modul helper fungsional menghasilkan nilai yang identik. |
| `L58` | `TestTokenCostEstimatorBaseline.test_parameter_scaling` | `method` | Verifikasi sensitivitas terhadap ronde, platform, dan ukuran context window. |
| `L76` | `TestBudgetLimitAndWarnings.test_over_budget_warning_triggered` | `method` | Uji kondisi ketika estimasi token melebihi budget limit yang ditentukan. |
| `L96` | `TestBudgetLimitAndWarnings.test_within_budget_no_warning` | `method` | Uji kondisi ketika estimasi token berada di bawah atau sama dengan budget limit. |
| `L112` | `TestBudgetLimitAndWarnings.test_exact_budget_limit` | `method` | Uji batas persis pada budget limit. |
| `L118` | `TestBudgetLimitAndWarnings.test_functional_budget_warning_helper` | `method` | Uji helper check_simulation_budget_warning. |
| `L128` | `TestPhaseAllocations.test_phase_allocation_ratios` | `method` | Rekomendasi alokasi: |
| `L147` | `TestPhaseAllocations.test_small_scale_phase_allocations` | `method` | Uji alokasi fase pada skala kecil (33,560 token). |
| `L161` | `TestModelPricingAndCostEstimation.test_claude_35_sonnet_cost` | `method` | Uji estimasi biaya Claude 3.5 Sonnet ($6.00 blended rate per 1M). |
| `L171` | `TestModelPricingAndCostEstimation.test_gpt_4o_cost` | `method` | Uji estimasi biaya GPT-4o ($4.375 blended rate per 1M). |
| `L181` | `TestModelPricingAndCostEstimation.test_llama_3_local_cost` | `method` | Uji Llama 3 local / open-source ($0.00 / free compute). |
| `L190` | `TestModelPricingAndCostEstimation.test_model_aliases` | `method` | Verifikasi alias model teresolusi dengan benar. |
| `L202` | `TestModelPricingAndCostEstimation.test_custom_exchange_rate` | `method` | Uji penggunaan kurs kustom USD ke IDR. |
| `L212` | `TestComprehensiveReportAndValidation.test_generate_budget_report_full` | `method` | Uji pembentukan laporan terpadu lengkap. |
| `L237` | `TestComprehensiveReportAndValidation.test_invalid_arguments_raise_value_errors` | `method` | Uji penolakan input negatif atau nol. |

---

### `test_v31_core.py`

- **Lokasi File**: `backend/tests/test_v31_core.py`
- **Kategori**: `Architecture - Core v3.1 Engine`
- **Total Kasus Uji**: `8` test

**Deskripsi Modul**:
> MiroFish Backend Core v3.1 Test Suite Menguji komponen inti: Database, JobEngine, Recovery Checkpoints, Secrets AES-GCM, Platform Behaviors (7 Platform), MultiPlatformSimulator, SearXNG Web Research, dan MCP Server.

| Baris | Nama Test Identifier | Tipe | Penjelasan / Assert Inti |
|---|---|---|---|
| `L62` | `test_database_sqlite_init_and_relations` | `function` | 1. Uji inisialisasi SQLite dan relasi model (Project -> Task -> Job -> Checkpoint). |
| `L138` | `test_job_engine_state_transitions` | `function` | 2. Uji transisi status JobEngine (queued -> running -> checkpointing -> completed). |
| `L205` | `test_checkpoints_integrity_and_recovery` | `function` | 3. Uji pembuatan checkpoint, verifikasi hash integritas SHA-256, dan restore_checkpoint. |
| `L301` | `test_secrets_aes_gcm_encryption` | `function` | 4. Uji enkripsi & dekripsi rahasia menggunakan AES-GCM 256-bit. |
| `L348` | `test_seven_platform_behaviors_and_scoring` | `function` | 5. Uji 7 karakteristik platform & feed scoring (Twitter, X, Reddit, TikTok, Instagram, Facebook, Threads). |
| `L420` | `test_multi_platform_simulator_loop` | `function` | 6. Uji loop eksekusi MultiPlatformSimulator lintas platform dan pemulihannya. |
| `L484` | `test_searxng_and_web_research_offline_and_mock` | `function` | 7. Uji layanan riset web SearXNG (sanitasi, penanganan offline, dan mocking). |
| `L574` | `test_mcp_server_listing_and_calling` | `function` | 8. Uji MCP Server (tools/list, tools/call, initialize, dan error handling). |

---

### `test_v32_enterprise.py`

- **Lokasi File**: `backend/tests/test_v32_enterprise.py`
- **Kategori**: `Architecture - Enterprise v3.2 Swarm`
- **Total Kasus Uji**: `16` test

**Deskripsi Modul**:
> MiroFish Enterprise Master Plan v3.2 Automated Test Suite Phase-Gate Validation (V1 - V8) across all 6 Divisions & 20 Subagents.

| Baris | Nama Test Identifier | Tipe | Penjelasan / Assert Inti |
|---|---|---|---|
| `L25` | `test_v3_camel_shield_indirect_injection` | `function` | Pengujian unit standar |
| `L40` | `test_v2_graphiti_subgraph_and_latency` | `function` | Pengujian unit standar |
| `L50` | `test_v2_zep_nli_barrier` | `function` | Pengujian unit standar |
| `L66` | `test_v2_psychometrics_whole_trait_fleeson` | `function` | Pengujian unit standar |
| `L73` | `test_v2_humanoid_ode_decay` | `function` | Pengujian unit standar |
| `L80` | `test_v2_nested_logit_train` | `function` | Pengujian unit standar |
| `L89` | `test_v2_hierarchical_nested_logit_3_tier` | `function` | Pengujian unit standar |
| `L100` | `test_v2_ddm_analytical_and_prospect_value` | `function` | Pengujian unit standar |
| `L111` | `test_v2_recsys_damping_entropy` | `function` | Pengujian unit standar |
| `L124` | `test_v2_platform_matrix_7_unique` | `function` | Pengujian unit standar |
| `L134` | `test_v2_cascade_hawkes_and_rescorla` | `function` | Pengujian unit standar |
| `L147` | `test_v1_report_agent_safe_abstention` | `function` | Pengujian unit standar |
| `L157` | `test_v1_bettafish_sentiment_integration` | `function` | Pengujian unit standar |
| `L164` | `test_v3_vault_envelope_encryption` | `function` | Pengujian unit standar |
| `L172` | `test_v5_webhook_hmac_signature` | `function` | Pengujian unit standar |
| `L181` | `test_v2_orchestrator_watchdog` | `function` | Pengujian unit standar |

---

### `test_zep_adapter_barrier.py`

- **Lokasi File**: `backend/tests/test_zep_adapter_barrier.py`
- **Kategori**: `Step 1 - Zep Memory & Graph Adapter`
- **Total Kasus Uji**: `11` test

**Deskripsi Modul**:
> Unit & Integration Test Suite for ZepAdapter, NLI Verification Barrier, and Graph Readiness Barrier. Agent 07: Zep Cloud & NLI Verification Barrier Specialist (Divisi B)

| Baris | Nama Test Identifier | Tipe | Penjelasan / Assert Inti |
|---|---|---|---|
| `L31` | `test_nli_entailment_valid_threshold` | `function` | Pengujian entailment valid bahasa Indonesia & Inggris dengan skor >= 0.85. |
| `L51` | `test_nli_contradiction_and_fabrication_rejection` | `function` | Pengujian penolakan kontradiksi dan fabrikasi informasi. |
| `L78` | `test_nli_neutral_and_empty_inputs` | `function` | Pengujian penanganan input kosong dan topik tidak berkaitan (NEUTRAL). |
| `L99` | `test_batch_verify_facts_and_zero_fabrication` | `function` | Pengujian verifikasi batch dan eliminasi entitas yang difabrikasi. |
| `L137` | `test_graph_readiness_barrier_topology` | `function` | Pengujian Graph Readiness Barrier terhadap topologi simpul dan relasi. |
| `L179` | `test_graph_readiness_barrier_indexing_sync` | `function` | Pengujian Graph Readiness Barrier saat batch Zep Cloud masih dalam proses indexing. |
| `L194` | `test_verify_graph_readiness_barrier_with_graph_dict` | `function` | Pengujian verifikasi barrier menggunakan representasi dictionary graf lokal. |
| `L225` | `test_zep_batch_ingestion_validation` | `function` | Pengujian batasan validasi API batch episode sebelum transmisi. |
| `L244` | `test_zep_batch_ingestion_pipeline_and_tracking` | `function` | Pengujian pipeline batch ingestion, registry, dan polling status. |
| `L280` | `test_step1_contract_generation_and_validation` | `function` | Pengujian pembuatan kontrak Step 1 GraphRAG dan verifikasi SHA-256 kanonikal. |
| `L310` | `test_export_step1_contract_file` | `function` | Pengujian ekspor file kontrak ke filesystem dan verifikasi ulang. |

---

### `test_zep_cloud_contracts.py`

- **Lokasi File**: `backend/tests/test_zep_cloud_contracts.py`
- **Kategori**: `Step 1 - Zep Memory & Graph Adapter`
- **Total Kasus Uji**: `15` test

**Deskripsi Modul**:
> Tidak ada modul docstring.

| Baris | Nama Test Identifier | Tipe | Penjelasan / Assert Inti |
|---|---|---|---|
| `L16` | `test_report_search_caps_the_query_sent_to_zep` | `function` | Pengujian unit standar |
| `L34` | `test_profile_context_search_caps_both_queries_sent_to_zep` | `function` | Pengujian unit standar |
| `L59` | `test_entity_context_includes_incoming_edges_from_the_full_graph` | `function` | Pengujian unit standar |
| `L123` | `test_entity_reader_does_not_turn_auth_failure_into_missing_entity` | `function` | Pengujian unit standar |
| `L138` | `test_entity_reader_does_not_turn_edge_failure_into_empty_data` | `function` | Pengujian unit standar |
| `L155` | `test_report_tools_do_not_turn_zep_read_failures_into_empty_data` | `function` | Pengujian unit standar |
| `L174` | `test_episode_processing_timeout_fails_instead_of_reporting_success` | `function` | Pengujian unit standar |
| `L192` | `test_document_ingestion_uses_current_batch_api_and_persists_identity` | `function` | Pengujian unit standar |
| `L237` | `test_graph_create_persists_identity_before_post_and_reconciles_timeout` | `function` | Pengujian unit standar |
| `L266` | `test_batch_create_timeout_is_reconciled_by_operation_metadata` | `function` | Pengujian unit standar |
| `L312` | `test_batch_add_timeout_recovers_a_fully_accepted_group_without_replay` | `function` | Pengujian unit standar |
| `L352` | `test_batch_wait_validates_terminal_items_and_opaque_zero_cursor` | `function` | Pengujian unit standar |
| `L399` | `test_batch_non_success_terminal_states_fail` | `function` | Pengujian unit standar |
| `L418` | `test_batch_wait_times_out_while_status_remains_nonterminal` | `function` | Pengujian unit standar |
| `L436` | `test_installed_sdk_serializes_the_batch_325_contract` | `function` | Pengujian unit standar |

---

### `test_zep_cloud_validation_script.py`

- **Lokasi File**: `backend/tests/test_zep_cloud_validation_script.py`
- **Kategori**: `Step 1 - Zep Memory & Graph Adapter`
- **Total Kasus Uji**: `3` test

**Deskripsi Modul**:
> Tidak ada modul docstring.

| Baris | Nama Test Identifier | Tipe | Penjelasan / Assert Inti |
|---|---|---|---|
| `L9` | `test_validation_script_preserves_the_process_key_across_app_config_import` | `function` | Pengujian unit standar |
| `L48` | `test_validation_cleanup_retains_graph_when_updater_cannot_drain` | `function` | Pengujian unit standar |
| `L83` | `test_validation_cleanup_deletes_graph_after_confirmed_drain` | `function` | Pengujian unit standar |

---

### `test_zep_edge_paging.py`

- **Lokasi File**: `backend/tests/test_zep_edge_paging.py`
- **Kategori**: `Step 1 - Zep Memory & Graph Adapter`
- **Total Kasus Uji**: `4` test

**Deskripsi Modul**:
> Tidak ada modul docstring.

| Baris | Nama Test Identifier | Tipe | Penjelasan / Assert Inti |
|---|---|---|---|
| `L18` | `test_edge_cap_stops_pagination_at_requested_limit` | `function` | Pengujian unit standar |
| `L44` | `test_existing_positional_retry_arguments_keep_their_meaning` | `function` | Pengujian unit standar |
| `L60` | `test_pagination_uses_the_current_opaque_response_cursor` | `function` | Pengujian unit standar |
| `L95` | `test_pagination_fails_if_the_service_repeats_a_cursor` | `function` | Pengujian unit standar |

---

### `test_zep_entity_reader_edges.py`

- **Lokasi File**: `backend/tests/test_zep_entity_reader_edges.py`
- **Kategori**: `Step 1 - Zep Memory & Graph Adapter`
- **Total Kasus Uji**: `2` test

**Deskripsi Modul**:
> Tidak ada modul docstring.

| Baris | Nama Test Identifier | Tipe | Penjelasan / Assert Inti |
|---|---|---|---|
| `L7` | `test_pinned_zep_sdk_exposes_get_edges_not_get_entity_edges` | `function` | Pengujian unit standar |
| `L12` | `test_get_node_edges_uses_the_supported_sdk_method` | `function` | Pengujian unit standar |

---

### `test_zep_graph_lifecycle.py`

- **Lokasi File**: `backend/tests/test_zep_graph_lifecycle.py`
- **Kategori**: `Step 1 - Zep Memory & Graph Adapter`
- **Total Kasus Uji**: `10` test

**Deskripsi Modul**:
> Tidak ada modul docstring.

| Baris | Nama Test Identifier | Tipe | Penjelasan / Assert Inti |
|---|---|---|---|
| `L38` | `test_project_reset_deletes_the_cloud_graph_before_clearing_reference` | `function` | Pengujian unit standar |
| `L73` | `test_project_reset_refuses_a_graph_with_an_active_simulation` | `function` | Pengujian unit standar |
| `L95` | `test_graph_delete_cannot_discard_an_updater_during_finalization` | `function` | Pengujian unit standar |
| `L119` | `test_repeated_build_request_reuses_the_existing_task` | `function` | Pengujian unit standar |
| `L150` | `test_stale_build_after_restart_is_recoverable_instead_of_reused` | `function` | Pengujian unit standar |
| `L186` | `test_stale_build_resumes_a_persisted_processing_batch` | `function` | Pengujian unit standar |
| `L247` | `test_project_delete_removes_cloud_graph_before_local_files` | `function` | Pengujian unit standar |
| `L288` | `test_completed_build_request_is_idempotent_without_force` | `function` | Pengujian unit standar |
| `L310` | `test_force_must_be_a_json_boolean` | `function` | Pengujian unit standar |
| `L331` | `test_graph_reset_and_memory_start_cannot_cross_between_delete_and_clear` | `function` | Pengujian unit standar |

---

### `test_zep_graph_memory_updater.py`

- **Lokasi File**: `backend/tests/test_zep_graph_memory_updater.py`
- **Kategori**: `Step 1 - Zep Memory & Graph Adapter`
- **Total Kasus Uji**: `9` test

**Deskripsi Modul**:
> Tidak ada modul docstring.

| Baris | Nama Test Identifier | Tipe | Penjelasan / Assert Inti |
|---|---|---|---|
| `L50` | `test_stop_drains_an_immediately_queued_tail_activity` | `function` | Pengujian unit standar |
| `L66` | `test_network_write_happens_outside_the_buffer_lock` | `function` | Pengujian unit standar |
| `L86` | `test_activity_episode_has_provenance_time_and_a_safe_size` | `function` | Pengujian unit standar |
| `L109` | `test_failed_non_idempotent_write_is_reported_by_stop` | `function` | Pengujian unit standar |
| `L123` | `test_failed_simulation_action_is_not_ingested` | `function` | Pengujian unit standar |
| `L144` | `test_stop_cannot_finish_between_acceptance_check_and_enqueue` | `function` | Pengujian unit standar |
| `L180` | `test_pending_episode_wait_has_a_deadline` | `function` | Pengujian unit standar |
| `L198` | `test_explicit_graph_destruction_can_discard_a_stopped_failed_updater` | `function` | Pengujian unit standar |
| `L212` | `test_flush_deadline_keeps_unattempted_platform_for_a_safe_retry` | `function` | Pengujian unit standar |

---

### `test_zep_report_barrier.py`

- **Lokasi File**: `backend/tests/test_zep_report_barrier.py`
- **Kategori**: `Step 1 - Zep Memory & Graph Adapter`
- **Total Kasus Uji**: `4` test

**Deskripsi Modul**:
> Tidak ada modul docstring.

| Baris | Nama Test Identifier | Tipe | Penjelasan / Assert Inti |
|---|---|---|---|
| `L26` | `test_report_generation_waits_for_zep_ingestion` | `function` | Pengujian unit standar |
| `L67` | `test_active_rerun_does_not_return_a_stale_completed_report` | `function` | Pengujian unit standar |
| `L113` | `test_failed_ingestion_cannot_generate_a_report_after_restart` | `function` | Pengujian unit standar |
| `L149` | `test_report_reader_lease_blocks_graph_start_and_delete` | `function` | Pengujian unit standar |

---

### `test_zep_retry_and_client.py`

- **Lokasi File**: `backend/tests/test_zep_retry_and_client.py`
- **Kategori**: `Step 1 - Zep Memory & Graph Adapter`
- **Total Kasus Uji**: `6` test

**Deskripsi Modul**:
> Tidak ada modul docstring.

| Baris | Nama Test Identifier | Tipe | Penjelasan / Assert Inti |
|---|---|---|---|
| `L10` | `test_permanent_zep_errors_fail_without_retry` | `function` | Pengujian unit standar |
| `L27` | `test_rate_limit_retry_respects_retry_after` | `function` | Pengujian unit standar |
| `L52` | `test_zep_client_is_shared_and_uses_an_explicit_timeout` | `function` | Pengujian unit standar |
| `L75` | `test_zep_client_rejects_self_hosted_endpoint_override` | `function` | Pengujian unit standar |
| `L82` | `test_zep_client_uses_internal_timeout_and_ignores_env_overrides` | `function` | Pengujian unit standar |
| `L107` | `test_zep_timeout_policy_is_not_exposed_in_env_example` | `function` | Pengujian unit standar |

---

### `test_zep_simulation_barrier.py`

- **Lokasi File**: `backend/tests/test_zep_simulation_barrier.py`
- **Kategori**: `Step 1 - Zep Memory & Graph Adapter`
- **Total Kasus Uji**: `10` test

**Deskripsi Modul**:
> Tidak ada modul docstring.

| Baris | Nama Test Identifier | Tipe | Penjelasan / Assert Inti |
|---|---|---|---|
| `L18` | `test_manual_stop_surfaces_graph_ingestion_failure` | `function` | Pengujian unit standar |
| `L58` | `test_platform_completion_does_not_publish_terminal_success_before_barrier` | `function` | Pengujian unit standar |
| `L82` | `test_manual_stop_timeout_leaves_monitor_owned_state_stopping` | `function` | Pengujian unit standar |
| `L118` | `test_failed_ingestion_finalization_can_be_retried` | `function` | Pengujian unit standar |
| `L156` | `test_stop_api_keeps_pending_finalization_out_of_failed_state` | `function` | Pengujian unit standar |
| `L195` | `test_simulation_start_rejects_string_booleans` | `function` | Pengujian unit standar |
| `L208` | `test_force_restart_does_not_continue_while_old_ingestion_is_pending` | `function` | Pengujian unit standar |
| `L273` | `test_monitor_start_failure_terminates_the_spawned_process` | `function` | Pengujian unit standar |
| `L339` | `test_shutdown_terminates_producer_before_tail_read_and_updater_drain` | `function` | Pengujian unit standar |
| `L428` | `test_shutdown_drain_failure_remains_failed_and_retryable` | `function` | Pengujian unit standar |

---
