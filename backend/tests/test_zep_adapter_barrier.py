"""
Unit & Integration Test Suite for ZepAdapter, NLI Verification Barrier, and Graph Readiness Barrier.
Agent 07: Zep Cloud & NLI Verification Barrier Specialist (Divisi B)
"""

import os
import json
import tempfile
import pytest

from app.services.zep_adapter import (
    ZepAdapter,
    NLIEvaluationResult,
    NLIVerificationReport,
    GraphReadinessStatus,
    ZepEpisodePayload,
    ZepBatchSubmission,
    Step1ContractPayload
)


@pytest.fixture
def adapter():
    return ZepAdapter(nli_threshold=0.85)


# ==========================================
# 1. NLI Entailment & Contradiction Tests
# ==========================================

def test_nli_entailment_valid_threshold(adapter):
    """Pengujian entailment valid bahasa Indonesia & Inggris dengan skor >= 0.85."""
    # Indonesian paraphrase entailment
    p_id = "Pemerintah menerbitkan regulasi tata kelola kecerdasan buatan nasional."
    h_id = "Regulasi tata kelola kecerdasan buatan resmi diterbitkan pemerintah."
    r_id = adapter.evaluate_nli_entailment(p_id, h_id)
    assert r_id.is_verified is True
    assert r_id.entailment_score >= 0.85
    assert r_id.label == "ENTAILMENT"
    assert "overlap" in r_id.details

    # English valid entailment
    p_en = "Quantum computing requires ultra-low temperatures near absolute zero to operate."
    h_en = "Near absolute zero ultra-low temperatures are needed for quantum computing."
    r_en = adapter.evaluate_nli_entailment(p_en, h_en)
    assert r_en.is_verified is True
    assert r_en.entailment_score >= 0.85
    assert r_en.label == "ENTAILMENT"


def test_nli_contradiction_and_fabrication_rejection(adapter):
    """Pengujian penolakan kontradiksi dan fabrikasi informasi."""
    # Indonesian explicit contradiction marker
    p1 = "Sistem komputasi awan dijamin aman dari insiden kebocoran data sensitif."
    h1 = "Sistem komputasi awan tidak pernah aman dari kebocoran data sensitif."
    r1 = adapter.evaluate_nli_entailment(p1, h1)
    assert r1.is_verified is False
    assert r1.entailment_score <= 0.20
    assert r1.label == "CONTRADICTION"

    # Fabrication marker ("palsu", "rekayasa")
    p2 = "Hasil uji laboratorium menunjukkan efikasi obat mencapai 95 persen."
    h2 = "Hasil uji laboratorium menunjukkan efikasi obat palsu dan rekayasa."
    r2 = adapter.evaluate_nli_entailment(p2, h2)
    assert r2.is_verified is False
    assert r2.entailment_score <= 0.20
    assert r2.label == "CONTRADICTION"

    # English contradiction marker ("never", "fabricated")
    p3 = "The satellite was successfully launched into geostationary orbit."
    h3 = "The satellite was never launched into orbit and claims are fabricated."
    r3 = adapter.evaluate_nli_entailment(p3, h3)
    assert r3.is_verified is False
    assert r3.entailment_score <= 0.20
    assert r3.label == "CONTRADICTION"


def test_nli_neutral_and_empty_inputs(adapter):
    """Pengujian penanganan input kosong dan topik tidak berkaitan (NEUTRAL)."""
    # Empty inputs
    r_empty = adapter.evaluate_nli_entailment("", "Klaim hipotesis")
    assert r_empty.is_verified is False
    assert r_empty.entailment_score == 0.0
    assert r_empty.label == "CONTRADICTION"

    r_empty2 = adapter.evaluate_nli_entailment("Premis ada.", "")
    assert r_empty2.is_verified is False
    assert r_empty2.entailment_score == 0.0

    # Low overlap / unrelated topics
    p_unrelated = "Pembangunan infrastruktur jalan tol di Jawa Timur terus berlanjut."
    h_unrelated = "Studi biologi kelautan menemukan spesies ubur-ubur baru di Samudra Pasifik."
    r_unrelated = adapter.evaluate_nli_entailment(p_unrelated, h_unrelated)
    assert r_unrelated.is_verified is False
    assert r_unrelated.entailment_score < 0.50
    assert r_unrelated.label in ["NEUTRAL", "CONTRADICTION"]


def test_batch_verify_facts_and_zero_fabrication(adapter):
    """Pengujian verifikasi batch dan eliminasi entitas yang difabrikasi."""
    premises = [
        "Bank Sentral menaikkan suku bunga acuan sebesar 25 basis poin untuk menekan laju inflasi.",
        "Kementerian ESDM meresmikan pembangkit listrik tenaga surya terapung terbesar di Asia Tenggara."
    ]

    claims = [
        {"entity": "BankSentral", "claim": "Bank Sentral menaikkan suku bunga acuan 25 basis poin inflasi."},
        {"entity": "KementerianESDM", "claim": "Kementerian ESDM meresmikan pembangkit listrik tenaga surya terapung."},
        {"entity": "EntitasFiktif", "claim": "Organisasi fiktif menguasai seluruh cadangan uranium tanpa izin."},
        {"entity": "KlaimPalsu", "claim": "Bank Sentral tidak pernah menaikkan suku bunga acuan dan kabar itu bohong."}
    ]

    report = adapter.batch_verify_facts(premises=premises, hypotheses=claims)
    assert isinstance(report, NLIVerificationReport)
    assert report.total_evaluated == 4
    assert report.verified_count == 2
    assert report.rejected_count == 2
    assert "BankSentral" in report.verified_entities
    assert "KementerianESDM" in report.verified_entities
    assert "EntitasFiktif" in report.rejected_entities
    assert "KlaimPalsu" in report.rejected_entities

    # Entity filtering guarantee
    entities = [
        {"name": "BankSentral", "entity_type": "Institution", "description": "Bank Sentral menaikkan suku bunga acuan."},
        {"name": "KlaimPalsu", "entity_type": "Organization", "description": "Bank Sentral tidak pernah menaikkan suku bunga."},
    ]
    filtered, f_report = adapter.verify_entities_and_claims(entities, source_premises=premises)
    assert len(filtered) == 1
    assert filtered[0]["name"] == "BankSentral"


# ==========================================
# 2. Graph Readiness Barrier Tests
# ==========================================

def test_graph_readiness_barrier_topology(adapter):
    """Pengujian Graph Readiness Barrier terhadap topologi simpul dan relasi."""
    # Failing node count
    status_nodes = adapter.check_graph_readiness_barrier(node_count=3, edge_count=10, min_nodes=5, min_edges=3)
    assert status_nodes.is_ready is False
    assert any("Jumlah simpul" in r for r in status_nodes.blocked_reasons)
    assert status_nodes.readiness_percentage < 100.0

    # Failing edge count
    status_edges = adapter.check_graph_readiness_barrier(node_count=10, edge_count=2, min_nodes=5, min_edges=3)
    assert status_edges.is_ready is False
    assert any("Jumlah relasi/edge" in r for r in status_edges.blocked_reasons)

    # Failing isolated nodes ratio
    status_isolated = adapter.check_graph_readiness_barrier(
        node_count=10,
        edge_count=10,
        min_nodes=5,
        min_edges=3,
        isolated_count=5,  # 50% isolated > 30% tolerance
        max_isolated_ratio=0.3
    )
    assert status_isolated.is_ready is False
    assert any("simpul terisolasi" in r for r in status_isolated.blocked_reasons)

    # Successful readiness
    status_ready = adapter.check_graph_readiness_barrier(
        node_count=20,
        edge_count=35,
        min_nodes=5,
        min_edges=3,
        isolated_count=1,
        subgraphs=["sg_policy_01", "sg_tech_02"],
        batch_ids=["batch_zep_101"]
    )
    assert status_ready.is_ready is True
    assert status_ready.readiness_percentage == 100.0
    assert status_ready.sync_status == "SYNCHRONIZED"
    assert status_ready.density > 0.0
    assert len(status_ready.blocked_reasons) == 0


def test_graph_readiness_barrier_indexing_sync(adapter):
    """Pengujian Graph Readiness Barrier saat batch Zep Cloud masih dalam proses indexing."""
    status_indexing = adapter.check_graph_readiness_barrier(
        node_count=20,
        edge_count=30,
        min_nodes=5,
        min_edges=3,
        pending_batches_count=2
    )
    assert status_indexing.is_ready is False
    assert status_indexing.sync_status == "INDEXING"
    assert any("indexing belum sinkron" in r for r in status_indexing.blocked_reasons)
    assert status_indexing.readiness_percentage < 100.0


def test_verify_graph_readiness_barrier_with_graph_dict(adapter):
    """Pengujian verifikasi barrier menggunakan representasi dictionary graf lokal."""
    graph_dict = {
        "nodes": [
            {"uuid": "n1", "name": "Node 1"},
            {"uuid": "n2", "name": "Node 2"},
            {"uuid": "n3", "name": "Node 3"},
            {"uuid": "n4", "name": "Node 4"},
            {"uuid": "n5", "name": "Node 5"},
            {"uuid": "n6", "name": "Isolated Node"}
        ],
        "edges": [
            {"source": "n1", "target": "n2"},
            {"source": "n2", "target": "n3"},
            {"source": "n3", "target": "n4"},
            {"source": "n4", "target": "n5"}
        ]
    }

    res = adapter.verify_graph_readiness_barrier("graph_test_01", local_graph=graph_dict, min_nodes=5, min_edges=3)
    assert res.is_ready is True
    assert res.indexed_node_count == 6
    assert res.indexed_edge_count == 4
    assert res.isolated_nodes_count == 1
    assert res.sync_status == "SYNCHRONIZED"


# ==========================================
# 3. Zep Episode Batch Ingestion Tests
# ==========================================

def test_zep_batch_ingestion_validation(adapter):
    """Pengujian batasan validasi API batch episode sebelum transmisi."""
    # Empty episodes
    with pytest.raises(ValueError, match="At least one episode is required"):
        adapter.validate_batch_episodes([])

    # Invalid batch_size
    with pytest.raises(ValueError, match="batch_size must be between 1 and 350"):
        adapter.validate_batch_episodes(["episode 1"], batch_size=0)

    with pytest.raises(ValueError, match="batch_size must be between 1 and 350"):
        adapter.validate_batch_episodes(["episode 1"], batch_size=400)

    # Oversized item
    oversized = "a" * 10001
    with pytest.raises(ValueError, match="exceeds 10,000 characters"):
        adapter.validate_batch_episodes([oversized])


def test_zep_batch_ingestion_pipeline_and_tracking(adapter):
    """Pengujian pipeline batch ingestion, registry, dan polling status."""
    episodes = [
        {"content": "Dokumen kebijakan regulasi AI 2026", "role": "user", "metadata": {"source": "gov"}},
        {"content": "Laporan pengujian sistem keamanan informasi", "role": "user", "metadata": {"source": "lab"}},
        "Pengumuman suku bunga bank sentral"
    ]

    submission = adapter.ingest_episodes_batch(
        graph_id="graph_sample_99",
        episodes=episodes,
        wait_for_completion=True
    )

    assert isinstance(submission, ZepBatchSubmission)
    assert submission.graph_id == "graph_sample_99"
    assert submission.item_count == 3
    assert len(submission.episode_uuids) == 3
    assert submission.status == "completed"
    assert submission.batch_id.startswith("batch_zep_")

    # Query registry
    status = adapter.get_batch_status(submission.batch_id)
    assert status.batch_id == submission.batch_id
    assert status.status == "completed"

    # List batches for graph
    graph_batches = adapter.list_batches(graph_id="graph_sample_99")
    assert len(graph_batches) >= 1
    assert any(b.batch_id == submission.batch_id for b in graph_batches)


# ==========================================
# 4. Step 1 GraphRAG Contract Tests
# ==========================================

def test_step1_contract_generation_and_validation(adapter):
    """Pengujian pembuatan kontrak Step 1 GraphRAG dan verifikasi SHA-256 kanonikal."""
    contract = adapter.generate_step1_contract(
        entities_verified_count=48,
        subgraph_ids=["sg_policy_01", "sg_tech_02"],
        zep_batch_ids=["batch_zep_101"],
        previous_contract_path="contracts/01-step0-research.json"
    )

    assert contract["contract"] == "02-step1-graphrag"
    assert contract["version"] == "1.0.0"
    assert contract["producer"] == "A07-Zep-NLI-Barrier"
    assert "C-division-agents" in contract["consumers"]
    assert contract["payload"]["graph_status"] == "READY"
    assert contract["payload"]["nli_min_score"] == 0.85
    assert contract["payload"]["entities_verified_count"] == 48

    # Validate integrity
    is_valid, errors = adapter.validate_step1_contract(contract)
    assert is_valid is True
    assert len(errors) == 0

    # Test tampering detection
    tampered_contract = json.loads(json.dumps(contract))
    tampered_contract["payload"]["entities_verified_count"] = 999
    is_valid_t, errors_t = adapter.validate_step1_contract(tampered_contract)
    assert is_valid_t is False
    assert any("integrity mismatch" in err for err in errors_t)


def test_export_step1_contract_file(adapter):
    """Pengujian ekspor file kontrak ke filesystem dan verifikasi ulang."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        target_path = os.path.join(tmp_dir, "02-step1-graphrag.json")
        adapter.export_step1_contract_file(
            filepath=target_path,
            entities_verified_count=48,
            subgraph_ids=["sg_policy_01", "sg_tech_02"],
            zep_batch_ids=["batch_zep_101"]
        )

        assert os.path.exists(target_path)
        with open(target_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        is_valid, errors = adapter.validate_step1_contract(data)
        assert is_valid is True
        assert len(errors) == 0
