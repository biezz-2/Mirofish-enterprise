"""
Enterprise API Blueprint for MiroFish Enterprise (Master Plan v3.2)
Exposes endpoints for the 20 Subagents and 6 Divisions.
"""

import os
import json
import logging
from flask import Blueprint, request, jsonify
from pathlib import Path

from ..services.orchestrator import OrchestratorStateMachine
from ..services.anti_injection import CaMeLPromptShield
from ..services.searxng_client import SearXNGClient
from ..services.graphiti_service import GraphitiService
from ..services.zep_adapter import ZepAdapter
from ..services.psychometrics import PsychometricsEngine, BigFiveTrait
from ..services.humanoid_needs import HumanoidNeedsEngine, HumanoidNeedsState
from ..services.decision_engine import DecisionEngine
from ..services.recsys_funnel import RecSysFunnel, FeedItem
from ..services.platform_matrix import PlatformMatrixService
from ..services.cascade_dynamics import CascadeDynamicsEngine, HawkesEvent
from ..services.report_agent import ReportAgent
from ..services.bettafish_adapter import BettaFishAdapter
from ..services.webhook_service import WebhookDispatcher, WebhookEvent
from ..services.discord_reporter import DiscordReporter
from ..utils.vault import VaultManager

logger = logging.getLogger('mirofish.api.enterprise')

enterprise_bp = Blueprint('enterprise', __name__)

# Singletons / Services
orchestrator = OrchestratorStateMachine()
shield = CaMeLPromptShield()
searxng = SearXNGClient()
graphiti = GraphitiService()
zep = ZepAdapter()
psychometrics = PsychometricsEngine()
needs_engine = HumanoidNeedsEngine()
decision_engine = DecisionEngine()
recsys = RecSysFunnel()
platform_matrix = PlatformMatrixService()
cascade_engine = CascadeDynamicsEngine()
report_agent = ReportAgent()
bettafish = BettaFishAdapter()
webhook_dispatcher = WebhookDispatcher()
vault_manager = VaultManager()
discord_reporter = DiscordReporter()


@enterprise_bp.route('/status', methods=['GET'])
def get_enterprise_status():
    """Status menyeluruh Master Plan v3.2 (20 Subagent, 6 Divisi)."""
    return jsonify({
        'success': True,
        'master_plan_version': 'v3.2',
        'divisions': {
            'A': 'Divisi A: Riset Web & Keamanan (Agent 01-04)',
            'B': 'Divisi B: GraphRAG & Memory Plane (Agent 05-07)',
            'C': 'Divisi C: Psikometri & Simulasi Agen (Agent 08-10)',
            'D': 'Divisi D: RecSys Funnel & Dinamika Viral (Agent 11-14)',
            'E': 'Divisi E: Analitik & Pelaporan Strategis (Agent 15-16)',
            'F': 'Divisi F: Ekstensibilitas Universal & QA (Agent 17-20)'
        },
        'subagents_count': 20,
        'ports': {
            'searxng': 8888,
            'graphiti': 8090,
            'mcp_server': 8091,
            'backend_api': 5001,
            'frontend_vue': 3001
        },
        'orchestrator': {
            'current_step': orchestrator.current_step,
            'step_name': orchestrator.get_status().get('step_name'),
            'heartbeats_monitored': len(orchestrator.heartbeats)
        }
    })


@enterprise_bp.route('/orchestrator/step', methods=['POST'])
def step_orchestrator():
    """Maju ke step berikutnya dalam orkestrasi 6-step."""
    data = request.get_json(silent=True) or {}
    success = orchestrator.advance_step()
    status = orchestrator.get_status()
    
    # Broadcast status ke Discord queue jika aktif
    try:
        discord_reporter.emit_event(
            event_type='TRANSITION',
            agent_id='A01',
            division='Divisi A (Step 0)',
            status='IN_PROGRESS',
            title_suffix=f"Step {status['current_step']}: {status['step_name']}"
        )
    except Exception as e:
        logger.warning(f"Gagal emit event discord: {e}")
    
    return jsonify({'success': success, 'data': status})


@enterprise_bp.route('/orchestrator/watchdog', methods=['GET'])
def run_watchdog():
    """Scan agen yang melewati batas heartbeat (timeout 45 menit)."""
    timeout = float(request.args.get('timeout', 2700.0))
    dead_agents = orchestrator.scan_watchdog(timeout_seconds=timeout)
    return jsonify({'success': True, 'dead_agents': dead_agents})


@enterprise_bp.route('/shield/sanitize', methods=['POST'])
def sanitize_content():
    """CaMeL Prompt Shield 3-layer (Regex sanitize, XML Spotlighting, Passive Capability)."""
    data = request.get_json(silent=True) or {}
    text = data.get('text', '')
    res = shield.process(text)
    return jsonify({
        'success': True,
        'is_safe': res.is_safe,
        'detected_patterns': res.detected_patterns,
        'spotlight_xml': res.spotlight_xml,
        'sanitized_text': res.sanitized_text
    })


@enterprise_bp.route('/searxng/search', methods=['GET'])
def search_searxng():
    """Metasearch SearXNG zero-tracking format JSON (port 8888)."""
    q = request.args.get('q', '')
    categories = request.args.get('categories', 'general')
    res = searxng.search(query=q, categories=categories)
    return jsonify({'success': True, 'query': q, 'results': res})


@enterprise_bp.route('/graphiti/subgraph', methods=['GET'])
def query_graphiti():
    """Kueri subgraf Graphiti Control Plane (port 8090)."""
    project_id = request.args.get('project_id', 'proj_default')
    label = request.args.get('label')
    res = graphiti.query_subgraph(project_id=project_id, label_filter=label)
    return jsonify({
        'success': True,
        'total_nodes': res.total_nodes,
        'total_edges': res.total_edges,
        'nodes': res.nodes,
        'edges': res.edges,
        'query_time_ms': res.query_time_ms
    })


@enterprise_bp.route('/zep/verify-nli', methods=['POST'])
def verify_nli():
    """Evaluasi NLI Hallucination Barrier (threshold >= 0.85)."""
    data = request.get_json(silent=True) or {}
    premise = data.get('premise', '')
    hypothesis = data.get('hypothesis', '')
    res = zep.evaluate_nli_entailment(premise, hypothesis)
    return jsonify({
        'success': True,
        'is_verified': res.is_verified,
        'entailment_score': res.entailment_score,
        'latency_ms': res.latency_ms
    })


@enterprise_bp.route('/psychometrics/sample', methods=['POST'])
def sample_traits():
    """Sample Fleeson Whole Trait Theory & Cybernetic Big Five."""
    data = request.get_json(silent=True) or {}
    trait = BigFiveTrait(
        openness=float(data.get('openness', 0.5)),
        conscientiousness=float(data.get('conscientiousness', 0.5)),
        extraversion=float(data.get('extraversion', 0.5)),
        agreeableness=float(data.get('agreeableness', 0.5)),
        neuroticism=float(data.get('neuroticism', 0.5))
    )
    res = psychometrics.sample_distribution(trait, n_samples=int(data.get('samples', 100)))
    return jsonify({'success': True, 'data': res})


@enterprise_bp.route('/humanoid/decay', methods=['POST'])
def decay_humanoid_needs():
    """ODE Peluruhan Kebutuhan (dN/dt = -lambda * N)."""
    data = request.get_json(silent=True) or {}
    state = HumanoidNeedsState(
        energy=float(data.get('energy', 1.0)),
        social=float(data.get('social', 0.8)),
        entertainment=float(data.get('entertainment', 0.7)),
        achievement=float(data.get('achievement', 0.5))
    )
    dt = float(data.get('dt_hours', 1.0))
    new_state = needs_engine.step_ode_decay(state, dt_hours=dt)
    return jsonify({'success': True, 'new_state': new_state.__dict__})


@enterprise_bp.route('/decision/nested-logit', methods=['POST'])
def run_nested_logit():
    """Kenneth Train Nested Logit Discrete Choice."""
    data = request.get_json(silent=True) or {}
    u_active = float(data.get('utility_active', 1.0))
    u_lurker = float(data.get('utility_lurker', 0.5))
    actions = data.get('actions', {'like': 0.8, 'retweet': 0.5, 'reply': 0.3})
    probs = decision_engine.evaluate_nested_logit(u_active, u_lurker, actions)
    return jsonify({'success': True, 'probabilities': probs})


@enterprise_bp.route('/recsys/rank', methods=['POST'])
def rank_feed():
    """3-Stage Recommender Funnel (Candidate Gen, Heavy Rank, Echo Damping)."""
    data = request.get_json(silent=True) or {}
    items_raw = data.get('items', [])
    items = [
        FeedItem(
            item_id=it.get('id', str(i)),
            author_id=it.get('author_id', 'a1'),
            topic=it.get('topic', 'general'),
            stance=float(it.get('stance', 0.0))
        )
        for i, it in enumerate(items_raw)
    ]
    user_stance = float(data.get('user_stance', 0.0))
    ranked = recsys.stage2_heavy_rank(items)
    reranked = recsys.stage3_rerank(ranked, user_stance=user_stance)
    entropy = recsys.calculate_shannon_entropy(reranked)
    return jsonify({
        'success': True,
        'entropy': entropy,
        'items': [{'item_id': it.item_id, 'topic': it.topic, 'stance': it.stance} for it in reranked]
    })


@enterprise_bp.route('/platforms', methods=['GET'])
def get_platforms():
    """Matriks Kalibrasi Algoritma 7 Platform unik."""
    supported = platform_matrix.list_supported_platforms()
    matrix = {p: platform_matrix.get_platform_weights(p) for p in supported}
    return jsonify({
        'success': True,
        'platforms': supported,
        'matrix': {k: (v.__dict__ if hasattr(v, '__dict__') else v) for k, v in matrix.items()}
    })


@enterprise_bp.route('/cascade/hawkes', methods=['POST'])
def compute_hawkes():
    """Marked Hawkes Self-Exciting Point Process Viral Intensity."""
    data = request.get_json(silent=True) or {}
    curr_time = float(data.get('current_time', 10.0))
    events_raw = data.get('events', [])
    events = [
        HawkesEvent(timestamp=float(e.get('t', 0.0)), user_influence_mark=float(e.get('mark', 1.0)))
        for e in events_raw
    ]
    intensity = cascade_engine.calculate_hawkes_intensity(curr_time, events)
    return jsonify({'success': True, 'intensity': intensity})


@enterprise_bp.route('/report/generate', methods=['POST'])
def generate_strategic_report():
    """ReACT ReportAgent dengan Klausul Safe Abstention & Sitasi Simpul Graf."""
    data = request.get_json(silent=True) or {}
    topic = data.get('topic', 'Analisis Swarm Enterprise')
    verified_nodes = data.get('verified_nodes', [])
    unverified_queries = data.get('unverified_queries', [])
    report = report_agent.generate_report(topic, verified_nodes, unverified_queries)
    return jsonify({
        'success': True,
        'title': report.title,
        'executive_summary': report.executive_summary,
        'key_findings': report.key_findings,
        'citations': [c.dict() for c in report.citations],
        'abstained_questions': report.abstained_questions,
        'markdown_content': report.markdown_content
    })


@enterprise_bp.route('/bettafish/sentiment', methods=['POST'])
def analyze_bettafish():
    """BettaFish Sentiment & Analytics Integration."""
    data = request.get_json(silent=True) or {}
    text = data.get('text', '')
    res = bettafish.analyze_sentiment(text)
    return jsonify({'success': True, 'data': res.__dict__})


@enterprise_bp.route('/webhooks/dispatch', methods=['POST'])
def dispatch_webhook():
    """Kirim event webhook bertandatangan HMAC-SHA256."""
    data = request.get_json(silent=True) or {}
    url = data.get('url', 'http://127.0.0.1:5001/api/webhooks/mock')
    event_type = data.get('event_type', 'SIMULATION_ROUND_COMPLETED')
    payload = data.get('payload', {})
    event = WebhookEvent(event_type=event_type, payload=payload)
    res = webhook_dispatcher.dispatch(url, event)
    return jsonify({'success': res.is_success, 'delivery_id': res.delivery_id, 'error': res.error_message})


@enterprise_bp.route('/contracts', methods=['GET'])
def list_contracts():
    """Daftar kontrak hand-off terverifikasi SHA-256."""
    base_dir = Path(__file__).resolve().parent.parent.parent.parent / 'contracts'
    contracts = []
    if base_dir.exists():
        for f in sorted(base_dir.iterdir()):
            if f.is_file():
                contracts.append({
                    'filename': f.name,
                    'size_bytes': f.stat().st_size
                })
    return jsonify({'success': True, 'contracts': contracts})
