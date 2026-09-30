"""
MiroFish Backend - Flask应用工厂
"""

import os
import warnings

# 抑制 multiprocessing resource_tracker 的警告（来自第三方库如 transformers）
# 需要在所有其他导入之前设置
warnings.filterwarnings("ignore", message=".*resource_tracker.*")

from flask import Flask, request
from flask_cors import CORS

from .config import Config
from .utils.logger import setup_logger, get_logger


def create_app(config_class=Config):
    """Flask应用工厂函数"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # 设置JSON编码：确保中文直接显示（而不是 \uXXXX 格式）
    # Flask >= 2.3 使用 app.json.ensure_ascii，旧版本使用 JSON_AS_ASCII 配置
    if hasattr(app, 'json') and hasattr(app.json, 'ensure_ascii'):
        app.json.ensure_ascii = False
    
    # 设置日志
    logger = setup_logger('mirofish')
    
    # 只在 reloader 子进程中打印启动信息（避免 debug 模式下打印两次）
    is_reloader_process = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
    debug_mode = app.config.get('DEBUG', False)
    should_log_startup = not debug_mode or is_reloader_process
    
    if should_log_startup:
        logger.info("=" * 50)
        logger.info("MiroFish Backend 启动中...")
        logger.info("=" * 50)
    
    # 启用CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # 注册模拟进程清理函数（确保服务器关闭时终止所有模拟进程）
    from .services.simulation_runner import SimulationRunner
    SimulationRunner.register_cleanup()
    if should_log_startup:
        logger.info("已注册模拟进程清理函数")
    
    # 请求日志中间件
    @app.before_request
    def log_request():
        logger = get_logger('mirofish.request')
        logger.debug(f"请求: {request.method} {request.path}")
        if request.content_type and 'json' in request.content_type:
            logger.debug(f"请求体: {request.get_json(silent=True)}")
    
    @app.after_request
    def log_response(response):
        logger = get_logger('mirofish.request')
        logger.debug(f"响应: {response.status_code}")
        return response
    
    # 注册蓝图
    from .api import graph_bp, simulation_bp, report_bp, research_bp
    app.register_blueprint(graph_bp, url_prefix='/api/graph')
    app.register_blueprint(simulation_bp, url_prefix='/api/simulation')
    app.register_blueprint(report_bp, url_prefix='/api/report')
    app.register_blueprint(research_bp)

    # Inisialisasi Database Relasional & Pemindaian Pemulihan Pasca-Crash
    from .models.db_session import init_db
    from .services.recovery import startup_recovery_scan
    db_uri = os.environ.get("DATABASE_URI", "sqlite:///mirofish.db")
    try:
        init_db(db_uri)
        recovered = startup_recovery_scan()
        if recovered:
            logger.info(f"[Crash Recovery] {len(recovered)} job otomatis dipulihkan")
    except Exception as e:
        logger.error(f"[DB Init Error] Gagal inisialisasi DB: {e}")

    # Endpoint Multi-Platform & Karakteristik
    from .services.platform_behaviors import PLATFORM_CHARACTERISTICS
    @app.route('/api/platforms', methods=['GET'])
    def list_platforms():
        return {
            'success': True,
            'data': PLATFORM_CHARACTERISTICS
        }

    # Endpoint Manajemen Job & Status Dashboard
    from .services.job_engine import JobEngine
    job_engine = JobEngine()

    @app.route('/api/jobs', methods=['GET'])
    def get_jobs_list():
        proj_id = request.args.get('project_id')
        jobs = job_engine.list_jobs(project_id=proj_id)
        return {'success': True, 'data': jobs}

    @app.route('/api/jobs/<job_id>/recover', methods=['POST'])
    def recover_job_endpoint(job_id):
        from .services.recovery import restore_checkpoint
        from .models.entities import CheckpointModel
        from .models.db_session import get_db_session
        with get_db_session() as s:
            latest_cp = s.query(CheckpointModel).filter_by(job_id=job_id).order_by(CheckpointModel.round_number.desc()).first()
            if not latest_cp:
                return {'success': False, 'error': {'code': 'NO_CHECKPOINT', 'message': 'Tidak ada checkpoint untuk job ini'}}, 404
            data = restore_checkpoint(job_id, latest_cp.round_number)
            job_engine.transition(job_id, 'running')
            return {'success': True, 'data': {'job_id': job_id, 'resumed_from_round': latest_cp.round_number}}

    # 健康检查
    @app.route('/health')
    @app.route('/api/health')
    def health():
        return {
            'status': 'healthy',
            'service': 'MiroFish Enterprise Backend (v3.1)',
            'database': 'sqlite',
            'multi_platform': True,
            'searxng': True
        }
    
    if should_log_startup:
        logger.info("MiroFish Backend 启动完成")
    
    return app

