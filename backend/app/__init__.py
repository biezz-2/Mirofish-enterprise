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
    cors_origins = [origin.strip() for origin in app.config.get('ALLOWED_CORS_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000').split(',')]
    CORS(app, resources={r"/api/*": {"origins": cors_origins}})
    
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

        # Security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; connect-src 'self' *"
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        return response
    
    # 注册蓝图
    from .api import graph_bp, simulation_bp, report_bp, research_bp, enterprise_bp
    app.register_blueprint(graph_bp, url_prefix='/api/graph')
    app.register_blueprint(simulation_bp, url_prefix='/api/simulation')
    app.register_blueprint(report_bp, url_prefix='/api/report')
    app.register_blueprint(enterprise_bp, url_prefix='/api/enterprise')
    app.register_blueprint(research_bp)

    # Inisialisasi Database Relasional & Pemindaian Pemulihan Pasca-Crash
    from .models.db_session import init_db, get_engine
    from .services.recovery import startup_recovery_scan
    db_uri = os.environ.get("DATABASE_URI", Config.DATABASE_URI)
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
        engine = get_engine()
        db_type = engine.dialect.name if engine else 'uninitialized'
        db_label = f"supabase ({db_type})" if "postgresql" in db_type else db_type
        return {
            'status': 'healthy',
            'service': 'MiroFish Enterprise Backend (v3.2)',
            'version': '3.2.0',
            'subagents_count': 20,
            'divisions_count': 6,
            'database': db_label,
            'multi_platform': True,
            'searxng': True,
            'ports': {
                'searxng': 8888,
                'graphiti': 8090,
                'mcp_server': 8091,
                'backend_api': 5001,
                'frontend_vue': 3001
            }
        }

    # OpenAPI 3.1.0 & Swagger UI documentation endpoints (Agent 18)
    from .services.openapi_engine import get_openapi_spec, get_swagger_ui_html

    @app.route('/openapi.json')
    @app.route('/api/openapi.json')
    def app_openapi_json():
        from flask import jsonify
        return jsonify(get_openapi_spec("dict"))

    @app.route('/openapi.yaml')
    @app.route('/api/openapi.yaml')
    def app_openapi_yaml():
        from flask import make_response
        resp = make_response(get_openapi_spec("yaml"))
        resp.headers["Content-Type"] = "application/x-yaml"
        return resp

    @app.route('/docs')
    @app.route('/api/docs')
    def app_api_docs():
        return get_swagger_ui_html(spec_url="/api/openapi.json")

    # FastMCP REST Proxy routes (Agent 17 -> Agent 18)
    @app.route('/api/mcp/tools', methods=['GET'])
    @app.route('/api/v1/mcp/tools', methods=['GET'])
    def app_mcp_tools():
        from mcp_server.tools import register_mcp_tools
        tools = register_mcp_tools()
        return {'success': True, 'tools': tools, 'count': len(tools)}

    @app.route('/api/mcp/health', methods=['GET'])
    @app.route('/api/v1/mcp/health', methods=['GET'])
    def app_mcp_health():
        from mcp_server.tools import register_mcp_tools
        return {'status': 'healthy', 'service': 'FastMCP Server Proxy', 'tools_count': len(register_mcp_tools())}
    
    if should_log_startup:
        logger.info("MiroFish Backend 启动完成")
    
    return app

