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
from ..services.recsys_funnel import RecSysFunnel, FeedItem, UserProfile, PLATFORM_RECSYS_WEIGHTS
from ..services.platform_matrix import PlatformMatrixService
from ..services.cascade_dynamics import CascadeDynamicsEngine, HawkesEvent
from ..services.bsp_swarm_runner import BSPSwarmRunner, SQLiteWALCheckpointer
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
bsp_runner = BSPSwarmRunner()
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


@enterprise_bp.route('/decision/hierarchical-nested-logit', methods=['POST'])
def run_hierarchical_nested_logit():
    """Kenneth Train 3-Level Hierarchical Nested Logit (Active/Lurker -> Consume/Produce -> Actions)."""
    data = request.get_json(silent=True) or {}
    u_active = float(data.get('utility_active', 0.8))
    u_lurker = float(data.get('utility_lurker', 0.5))
    u_consume = data.get('utilities_consume', {'like': 0.8, 'retweet': 0.5, 'browse': 0.6})
    u_produce = data.get('utilities_produce', {'reply': 0.4, 'quote': 0.3, 'post': 0.2})
    mu_active = float(data['mu_active']) if 'mu_active' in data else None
    mu_consume = float(data['mu_consume']) if 'mu_consume' in data else None
    mu_produce = float(data['mu_produce']) if 'mu_produce' in data else None

    res = decision_engine.evaluate_hierarchical_nested_logit(
        utility_active=u_active,
        utility_lurker=u_lurker,
        utilities_consume=u_consume,
        utilities_produce=u_produce,
        mu_active=mu_active,
        mu_consume=mu_consume,
        mu_produce=mu_produce
    )
    return jsonify({'success': True, 'result': res.model_dump()})


@enterprise_bp.route('/decision/ddm-analytical', methods=['POST'])
def run_ddm_analytical():
    """Ratcliff Drift Diffusion Model (DDM) Closed-Form Solution."""
    data = request.get_json(silent=True) or {}
    drift = float(data.get('drift_rate', 0.3))
    threshold_a = float(data.get('threshold_a', 1.0))
    t_er = float(data.get('non_decision_time_ms', 300.0))
    p_up, mean_rt, var_rt = decision_engine.analytical_ddm(drift, threshold_a=threshold_a, non_decision_time_ms=t_er)
    return jsonify({
        'success': True,
        'p_upper': p_up,
        'mean_rt_ms': mean_rt,
        'var_rt_ms': var_rt
    })


@enterprise_bp.route('/decision/self-censorship', methods=['POST'])
def run_self_censorship():
    """Kahneman-Tversky Prospect Theory Self-Censorship Evaluation."""
    data = request.get_json(silent=True) or {}
    from app.services.decision_engine import DecisionContext
    ctx = DecisionContext(**data.get('context', {}))
    candidate = data.get('candidate_action', 'post')
    r_tol = float(data.get('risk_tolerance', 0.5))
    lam = float(data['lambda_loss']) if 'lambda_loss' in data else None

    res = decision_engine.evaluate_self_censorship(
        candidate_action=candidate,
        context=ctx,
        lambda_param=lam,
        risk_tolerance=r_tol
    )
    return jsonify({'success': True, 'result': res.model_dump()})


@enterprise_bp.route('/decision/simulate-swarm', methods=['POST'])
def run_swarm_decision_sim():
    """Swarm Predictive Sandbox Simulation (100 agents x N rounds)."""
    data = request.get_json(silent=True) or {}
    agents = int(data.get('agents_count', 100))
    rounds = int(data.get('rounds', 20))
    shock = int(data['shock_round']) if 'shock_round' in data else 10
    res = decision_engine.run_swarm_decision_simulation(
        agents_count=agents,
        rounds=rounds,
        controversy_shock_round=shock
    )
    return jsonify({'success': True, 'result': res.model_dump()})


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


@enterprise_bp.route('/recsys/funnel', methods=['POST'])
def run_recsys_funnel():
    """Menjalankan full 3-Stage RecSys Funnel dengan profil pengguna dan parameter platform."""
    data = request.get_json(silent=True) or {}
    items_raw = data.get('items', [])
    items = [FeedItem(**it) for it in items_raw]
    profile_raw = data.get('user_profile', {})
    profile = UserProfile(**profile_raw)
    platform = data.get('platform', 'x')
    limit = int(data.get('limit', 20))
    damping = float(data.get('damping_factor', 0.60))
    eps = float(data.get('epsilon', 0.05))

    local_funnel = RecSysFunnel(damping_factor=damping, epsilon=eps, platform=platform)
    result = local_funnel.run_funnel(items=items, user_profile=profile, platform=platform, limit=limit)
    return jsonify({'success': True, 'result': result.model_dump()})


@enterprise_bp.route('/recsys/simulate-swarm', methods=['POST'])
def run_swarm_recsys_sim():
    """Simulasi Sandbox Swarm RecSys (Multi-agent x N rounds)."""
    data = request.get_json(silent=True) or {}
    agents = int(data.get('agents_count', 50))
    corpus = int(data.get('corpus_size', 500))
    rounds = int(data.get('rounds', 15))
    damping = float(data.get('damping_factor', 0.75))
    eps = float(data.get('epsilon', 0.10))
    candidate_lim = int(data.get('candidate_limit', 60))
    platform = str(data.get('platform', 'x'))

    res = recsys.run_swarm_recsys_simulation(
        agents_count=agents,
        corpus_size=corpus,
        rounds=rounds,
        damping_factor=damping,
        epsilon=eps,
        candidate_limit=candidate_lim,
        platform=platform
    )
    return jsonify({'success': True, 'result': res.model_dump()})


@enterprise_bp.route('/recsys/diversity-metrics', methods=['POST'])
def calculate_recsys_metrics():
    """Kalkulasi metrik diversitas & Shannon entropy feed."""
    data = request.get_json(silent=True) or {}
    items_raw = data.get('items', [])
    items = [FeedItem(**it) for it in items_raw]
    user_stance = float(data.get('user_stance', 0.0))
    metrics = RecSysFunnel.calculate_stance_diversity_metrics(items, user_stance=user_stance)
    return jsonify({'success': True, 'metrics': metrics})


@enterprise_bp.route('/recsys/weights', methods=['GET'])
def get_recsys_weights():
    """Daftar bobot multi-task platform rekomendasi."""
    return jsonify({'success': True, 'weights': PLATFORM_RECSYS_WEIGHTS})


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

@enterprise_bp.route('/platforms/<platform_key>', methods=['GET'])
def get_platform_detail(platform_key: str):
    """Detail parameter pembobotan dan kalibrasi platform tertentu."""
    weights = platform_matrix.get_platform_weights(platform_key)
    pareto_metrics = platform_matrix.calculate_platform_pareto_metrics(platform_key)
    return jsonify({
        'success': True,
        'platform_key': platform_key,
        'weights': weights.__dict__ if hasattr(weights, '__dict__') else weights,
        'pareto_metrics': pareto_metrics.__dict__ if hasattr(pareto_metrics, '__dict__') else pareto_metrics,
    })


@enterprise_bp.route('/platforms/pareto-metrics', methods=['GET'])
def get_platforms_pareto_metrics():
    """Metrik analitik distribusi Pareto dan Gini untuk seluruh platform kanonikal."""
    platforms = platform_matrix.list_supported_platforms()
    metrics = {p: platform_matrix.calculate_platform_pareto_metrics(p).__dict__ for p in platforms}
    return jsonify({
        'success': True,
        'platforms': platforms,
        'pareto_metrics': metrics,
    })


@enterprise_bp.route('/platforms/simulate-pareto', methods=['POST'])
def simulate_platform_pareto():
    """Simulasi Sandbox Swarm Multi-Agen untuk validasi Pareto 90-9-1 dan atensi power-law."""
    data = request.get_json(silent=True) or {}
    platform_key = data.get('platform', 'x')
    n_agents = int(data.get('n_agents', 50))
    n_rounds = int(data.get('n_rounds', 15))
    seed = int(data.get('seed', 42))

    sim_result = platform_matrix.simulate_platform_sandbox(
        platform_key=platform_key,
        n_agents=n_agents,
        n_rounds=n_rounds,
        seed=seed,
    )
    return jsonify({
        'success': True,
        'simulation': sim_result.__dict__ if hasattr(sim_result, '__dict__') else sim_result,
    })


@enterprise_bp.route('/platforms/downstream-recommendations', methods=['GET'])
def get_platform_downstream_recommendations():
    """Parameter rekomendasi terkalibrasi untuk downstream (Agent 13 Hawkes & Agent 14 BSP)."""
    recommendations = platform_matrix.get_downstream_recommendations()
    return jsonify({
        'success': True,
        'recommendations': recommendations,
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
    platform = data.get('platform')
    if platform:
        intensity = cascade_engine.calculate_platform_intensity(curr_time, events, platform=platform)
    else:
        intensity = cascade_engine.calculate_hawkes_intensity(curr_time, events)
    return jsonify({'success': True, 'intensity': intensity})


@enterprise_bp.route('/cascade/rescorla-wagner', methods=['POST'])
def compute_rescorla_wagner():
    """Rescorla-Wagner Dopamine Learning & RPE Update."""
    data = request.get_json(silent=True) or {}
    curr_v = float(data.get('current_v', 0.30))
    alpha = float(data['alpha']) if 'alpha' in data and data['alpha'] is not None else None

    # Jika diberikan reward sequence, jalankan simulasi jadwal
    if 'reward_sequence' in data and isinstance(data['reward_sequence'], list):
        seq = [float(r) for r in data['reward_sequence']]
        res = cascade_engine.simulate_dopamine_schedule(initial_v=curr_v, reward_sequence=seq, alpha=alpha)
        return jsonify({'success': True, 'data': res})

    received_reward = float(data.get('received_reward', 1.0))
    new_v, error = cascade_engine.update_rescorla_wagner(curr_v, received_reward, alpha=alpha)
    return jsonify({
        'success': True,
        'current_v': curr_v,
        'received_reward': received_reward,
        'new_v': new_v,
        'prediction_error': error,
    })


@enterprise_bp.route('/cascade/granovetter', methods=['POST'])
def compute_granovetter():
    """Mark Granovetter (1978) Threshold Model of Collective Action."""
    data = request.get_json(silent=True) or {}

    # Jika request meminta simulasi jaringan
    if data.get('simulate', False):
        num_agents = int(data.get('num_agents', 50))
        platform = data.get('platform', 'x')
        seed_ratio = float(data.get('seed_ratio', 0.04))
        network_type = data.get('network_type', 'small_world')
        res = cascade_engine.simulate_granovetter_cascade(
            num_agents=num_agents,
            platform=platform,
            seed_ratio=seed_ratio,
            network_type=network_type
        )
        return jsonify({'success': True, 'data': res})

    threshold = float(data.get('threshold', 0.30))
    active_peer_ratio = float(data.get('active_peer_ratio', 0.0))
    is_active = cascade_engine.evaluate_granovetter_activation(threshold, active_peer_ratio)
    return jsonify({
        'success': True,
        'threshold': threshold,
        'active_peer_ratio': active_peer_ratio,
        'is_active': is_active
    })


@enterprise_bp.route('/cascade/hawkes/simulate', methods=['POST'])
def simulate_hawkes_point_process():
    """Simulasi Kaskade Titik Hawkes Ogata Thinning."""
    data = request.get_json(silent=True) or {}
    platform = data.get('platform', 'x')
    time_horizon = float(data.get('time_horizon', 24.0))
    max_events = int(data.get('max_events', 200))
    res = cascade_engine.simulate_hawkes_cascade(
        platform=platform,
        time_horizon=time_horizon,
        max_events=max_events
    )
    return jsonify({'success': True, 'data': res})


@enterprise_bp.route('/cascade/swarm/simulate', methods=['POST'])
def simulate_swarm_cascade():
    """Predictive Sandbox Swarm Simulator (50 Agen x 15 Ronde Multi-Platform)."""
    data = request.get_json(silent=True) or {}
    agents_count = int(data.get('agents_count', 50))
    rounds = int(data.get('rounds', 15))
    platforms = data.get('platforms')
    res = cascade_engine.run_swarm_cascade_simulation(
        agents_count=agents_count,
        rounds=rounds,
        platforms=platforms
    )
    res_data = res.model_dump() if hasattr(res, 'model_dump') else res.dict()
    return jsonify({'success': True, 'data': res_data})


@enterprise_bp.route('/cascade/platform-matrices', methods=['GET'])
def get_cascade_platform_matrices():
    """Matriks Kalibrasi Hawkes & Granovetter Per Platform."""
    matrices = {}
    for p in cascade_engine.platform_matrix.keys():
        params = cascade_engine.get_platform_hawkes_params(p)
        matrices[p] = params.model_dump() if hasattr(params, 'model_dump') else params.dict()
    return jsonify({'success': True, 'platforms': matrices})


@enterprise_bp.route('/cascade/downstream-recommendations', methods=['GET'])
def get_cascade_downstream_recommendations():
    """Handoff Parameter Terkalibrasi untuk Agent 14 (BSP Parallel Runner)."""
    recs = cascade_engine.get_downstream_recommendations_agent_14()
    return jsonify({'success': True, 'recommendations': recs})


@enterprise_bp.route('/bsp/simulate', methods=['POST'])
def run_bsp_simulation():
    """Jalankan simulasi paralel Bulk Synchronous Parallel (BSP) Swarm."""
    data = request.get_json(silent=True) or {}
    agents_per_platform = int(data.get('agents_per_platform', 50))
    rounds = int(data.get('rounds', 15))
    platforms = data.get('platforms', None)
    job_id = data.get('job_id', None)
    
    result = bsp_runner.run_swarm_simulation(
        agents_per_platform=agents_per_platform,
        rounds=rounds,
        platforms=platforms,
        job_id=job_id
    )
    return jsonify({
        'success': result.success,
        'simulation_id': result.simulation_id,
        'status': result.status,
        'metrics': result.metrics.model_dump(),
        'downstream_recommendations': result.downstream_recommendations
    })


@enterprise_bp.route('/bsp/checkpoint', methods=['POST'])
def save_bsp_checkpoint():
    """Simpan checkpoint transaksional SQLite WAL dengan SHA-256 state hashing."""
    import time
    data = request.get_json(silent=True) or {}
    job_id = data.get('job_id', f"bsp_manual_{int(time.time())}")
    round_num = int(data.get('round_num', 1))
    superstep_id = data.get('superstep_id', f"BSP_BARRIER_{round_num}")
    state_dict = data.get('state_dict', {})
    active_agents = int(data.get('active_agents', len(state_dict.get('agents', []))))
    events_generated = int(data.get('events_generated', 0))
    wal_freq = int(data.get('wal_checkpoint_frequency', 5))

    cp = bsp_runner.checkpointer.save_checkpoint(
        job_id=job_id,
        round_num=round_num,
        superstep_id=superstep_id,
        state_dict=state_dict,
        active_agents_count=active_agents,
        events_generated=events_generated,
        wal_checkpoint_frequency=wal_freq
    )
    return jsonify({
        'success': True,
        'checkpoint': cp.model_dump()
    })


@enterprise_bp.route('/bsp/recover', methods=['POST'])
def recover_bsp_simulation():
    """Pemulihan crash zero-loss dan auto-resume dari checkpoint SQLite WAL terakhir."""
    data = request.get_json(silent=True) or {}
    job_id = data.get('job_id')
    if not job_id:
        return jsonify({'success': False, 'error': 'job_id wajib disertakan'}), 400
    target_rounds = int(data.get('target_rounds', 15))
    platforms = data.get('platforms', None)

    try:
        res = bsp_runner.resume_simulation(job_id=job_id, target_rounds=target_rounds, platforms=platforms)
        return jsonify({
            'success': res.success,
            'simulation_id': res.simulation_id,
            'status': res.status,
            'metrics': res.metrics.model_dump(),
            'downstream_recommendations': res.downstream_recommendations
        })
    except Exception as ex:
        return jsonify({'success': False, 'error': str(ex)}), 500


@enterprise_bp.route('/bsp/status/<job_id>', methods=['GET'])
def get_bsp_status(job_id: str):
    """Ambil status checkpoint dan histori verifikasi SHA-256 sebuah job simulasi."""
    latest = bsp_runner.checkpointer.get_latest_checkpoint(job_id)
    history = bsp_runner.checkpointer.list_checkpoints(job_id)
    return jsonify({
        'success': True,
        'job_id': job_id,
        'has_checkpoints': latest is not None,
        'latest_checkpoint': latest.model_dump() if latest else None,
        'checkpoints_count': len(history),
        'checkpoints': [c.model_dump() for c in history]
    })


@enterprise_bp.route('/bsp/downstream-recommendations', methods=['GET'])
def get_bsp_downstream_recommendations():
    """Handoff parameter rekomendasi dan rantai sitasi graf untuk Agent 15 (ReACT ReportAgent)."""
    job_id = request.args.get('job_id', 'sim_bsp_default')
    recs = bsp_runner.get_downstream_recommendations_agent_15(job_id)
    return jsonify({'success': True, 'recommendations': recs})


@enterprise_bp.route('/report/generate', methods=['POST'])
def generate_strategic_report():
    """ReACT ReportAgent dengan Klausul Safe Abstention & Sitasi Simpul Graf."""
    data = request.get_json(silent=True) or {}
    topic = data.get('topic', 'Analisis Swarm Enterprise')
    verified_nodes = data.get('verified_nodes', [])
    unverified_queries = data.get('unverified_queries', [])
    upstream_bsp_handoff = data.get('upstream_bsp_handoff')
    hypotheses = data.get('hypotheses')

    # Integrasi otomatis rekomendasi BSP Runner jika tidak disediakan
    if not upstream_bsp_handoff:
        job_id = data.get('simulation_job_id', 'sim_bsp_slice14_verified')
        upstream_bsp_handoff = bsp_runner.get_downstream_recommendations_agent_15(job_id)

    report = report_agent.generate_strategic_report(
        topic=topic,
        verified_nodes=verified_nodes,
        unverified_queries=unverified_queries,
        upstream_bsp_handoff=upstream_bsp_handoff,
        hypotheses=hypotheses
    )
    return jsonify({
        'success': True,
        'report_id': report.report_id,
        'title': report.title,
        'executive_summary': report.executive_summary,
        'key_findings': report.key_findings,
        'citations': [c.model_dump() for c in report.citations],
        'abstained_questions': report.abstained_questions,
        'deduction_steps': [s.model_dump() for s in report.deduction_steps],
        'hypotheses_deductions': [h.model_dump() for h in report.hypotheses_deductions],
        'markdown_content': report.markdown_content,
        'provenance_summary': report.provenance_summary,
        'downstream_parameters': report.downstream_parameters
    })


@enterprise_bp.route('/report/deduce', methods=['POST'])
def deduce_hypothesis():
    """ReACT Multi-Turn Deduction Loop untuk Pengujian Hipotesis Spesifik."""
    data = request.get_json(silent=True) or {}
    hypothesis = data.get('hypothesis', '')
    if not hypothesis:
        return jsonify({'success': False, 'error': 'Parameter hypothesis wajib diisi'}), 400

    verified_nodes = data.get('verified_nodes', [])
    provenance_context = data.get('provenance_context')
    if not provenance_context:
        job_id = data.get('simulation_job_id', 'sim_bsp_slice14_verified')
        rec = bsp_runner.get_downstream_recommendations_agent_15(job_id)
        provenance_context = rec.get('provenance_chain_summary', {})

    deduction = report_agent.deduction_analyst.deduce_hypothesis(
        hypothesis=hypothesis,
        verified_nodes=verified_nodes,
        provenance_context=provenance_context
    )
    return jsonify({
        'success': True,
        'hypothesis': deduction.hypothesis,
        'status': deduction.status,
        'confidence': deduction.confidence,
        'citations': [c.model_dump() for c in deduction.citations],
        'deduction_narrative': deduction.deduction_narrative,
        'abstention_reason': deduction.abstention_reason,
        'steps': [s.model_dump() for s in deduction.steps]
    })


@enterprise_bp.route('/report/downstream-recommendations', methods=['GET'])
def get_report_downstream_recommendations():
    """Handoff parameter dan ringkasan eksekutif untuk Agent 16 (BettaFish Integrator)."""
    topic = request.args.get('topic', 'Analisis Swarm Enterprise')
    job_id = request.args.get('job_id', 'sim_bsp_slice14_verified')
    upstream_bsp = bsp_runner.get_downstream_recommendations_agent_15(job_id)

    report = report_agent.generate_strategic_report(
        topic=topic,
        verified_nodes=[],
        unverified_queries=None,
        upstream_bsp_handoff=upstream_bsp
    )
    recs = report_agent.deduction_analyst.get_downstream_recommendations_agent_16(report)
    return jsonify({'success': True, 'recommendations': recs})


@enterprise_bp.route('/bettafish/sentiment', methods=['POST'])
def analyze_bettafish():
    """BettaFish Sentiment & Analytics Integration."""
    data = request.get_json(silent=True) or {}
    text = data.get('text', '')
    res = bettafish.analyze_sentiment(text)
    return jsonify({'success': True, 'data': res.__dict__})


@enterprise_bp.route('/bettafish/executive-report', methods=['POST'])
def generate_bettafish_executive_report():
    """Pembuatan Laporan Eksekutif C-Level BettaFish ReportEngine."""
    data = request.get_json(silent=True) or {}
    topic = data.get('topic', 'Pemberdayaan Platform Enterprise & Ketahanan Sistem')
    upstream_handoff = data.get('upstream_handoff')
    simulation_events = data.get('simulation_events')
    custom_claims = data.get('custom_claims')

    report = bettafish.generate_c_level_report(
        topic=topic,
        upstream_handoff=upstream_handoff,
        simulation_events=simulation_events,
        custom_claims=custom_claims
    )
    return jsonify({
        'success': True,
        'report': report.model_dump()
    })


@enterprise_bp.route('/bettafish/risk-assessment', methods=['POST'])
def assess_bettafish_corporate_risk():
    """Penilaian Risiko Korporat & Peringatan Dini BettaFish InsightEngine."""
    data = request.get_json(silent=True) or {}
    text = data.get('text', '')
    claim_polarities = data.get('claim_polarities')
    virality_potential = float(data.get('virality_potential', 0.0))

    assessment = bettafish.assess_corporate_risk(
        text=text,
        claim_polarities=claim_polarities,
        virality_potential=virality_potential
    )
    return jsonify({
        'success': True,
        'risk_assessment': assessment.model_dump()
    })


@enterprise_bp.route('/bettafish/downstream-recommendations', methods=['GET'])
def get_bettafish_downstream_recommendations():
    """Parameter Handoff Terkalibrasi untuk Downstream Agent 17 & Agent 18."""
    topic = request.args.get('topic', 'Enterprise AI Governance')
    report = bettafish.generate_c_level_report(topic=topic)
    recs = bettafish.get_downstream_recommendations(report)
    return jsonify({
        'success': True,
        'recommendations': recs
    })


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
