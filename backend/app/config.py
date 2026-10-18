"""\n配置管理\n统一从项目根目录的 .env 文件加载配置\n"""

import os
from dotenv import load_dotenv

# 加载项目根目录的 .env 文件
# 路径: MiroFish/.env (相对于 backend/app/config.py)
project_root_env = os.path.join(os.path.dirname(__file__), '../../.env')

if os.path.exists(project_root_env):
    load_dotenv(project_root_env, override=True)
else:
    # 如果根目录没有 .env，尝试加载环境变量（用于生产环境）
    load_dotenv(override=True)


class Config:
    """Flask配置类"""
    
    # Flask配置
    SECRET_KEY = os.environ.get('SECRET_KEY', '')
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    DEVELOPMENT_MODE = os.environ.get('DEVELOPMENT_MODE', 'false').lower() == 'true'
    AUTH_REQUIRED = os.environ.get('AUTH_REQUIRED', 'false').lower() == 'true'
    PORT = int(os.environ.get('PORT', 8000))
    VAULT_MASTER_KEY = os.environ.get('VAULT_MASTER_KEY') or os.environ.get('MIROFISH_VAULT_KEY', '')

    # JWT Hardening Configuration (P1-4)
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or os.environ.get('SECRET_KEY', '')
    JWT_ALGORITHM = 'HS256'
    JWT_ISSUER = os.environ.get('JWT_ISSUER')
    JWT_AUDIENCE = os.environ.get('JWT_AUDIENCE')
    
    # CORS配置
    ALLOWED_CORS_ORIGINS = os.environ.get('ALLOWED_CORS_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000')

    # JSON配置 - 禁用ASCII转义，让中文直接显示
    JSON_AS_ASCII = False
    
    # LLM配置（统一使用OpenAI格式）
    LLM_API_KEY = os.environ.get('LLM_API_KEY')
    LLM_BASE_URL = os.environ.get('LLM_BASE_URL', 'https://api.openai.com/v1')
    LLM_MODEL_NAME = os.environ.get('LLM_MODEL_NAME', 'gpt-4o-mini')
    
    # Zep配置
    ZEP_API_KEY = os.environ.get('ZEP_API_KEY')
    
    # Graph Memory Backend (Graphiti Platform + FalkorDB + Neo4j)
    GRAPH_BACKEND = os.environ.get('GRAPH_BACKEND', 'graphiti').lower()
    GRAPHITI_CONTROL_PLANE_URL = os.environ.get('GRAPHITI_CONTROL_PLANE_URL', 'http://127.0.0.1:8080')
    GRAPHITI_CONTROL_PLANE_PORT = int(os.environ.get('GRAPHITI_CONTROL_PLANE_PORT', '8090'))
    FALKORDB_HOST = os.environ.get('FALKORDB_HOST', '127.0.0.1')
    FALKORDB_PORT = int(os.environ.get('FALKORDB_PORT', '6379'))
    NEO4J_URI = os.environ.get('NEO4J_URI', 'bolt://127.0.0.1:7687')
    NEO4J_USER = os.environ.get('NEO4J_USER', 'neo4j')
    NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD', '')
    REDIS_HOST = os.environ.get('REDIS_HOST', '127.0.0.1')
    REDIS_PORT = int(os.environ.get('REDIS_PORT', '6379'))
    REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', '')
    REDIS_DB = int(os.environ.get('REDIS_DB', '0'))
    GRAPHITI_GROUP_ID = os.environ.get('GRAPHITI_GROUP_ID', 'main')

    # Redis URL dengan penegakan requirepass (anti-anonymous login)
    _raw_redis_url = os.environ.get('REDIS_URL')
    if _raw_redis_url:
        if REDIS_PASSWORD and '@' not in _raw_redis_url:
            from urllib.parse import urlparse, quote
            _p = urlparse(_raw_redis_url)
            _db_str = _p.path.lstrip('/') if _p.path else str(REDIS_DB)
            REDIS_URL = f"{_p.scheme or 'redis'}://:{quote(REDIS_PASSWORD, safe='')}@{_p.hostname or REDIS_HOST}:{_p.port or REDIS_PORT}/{_db_str}"
        else:
            REDIS_URL = _raw_redis_url
    else:
        if REDIS_PASSWORD:
            from urllib.parse import quote
            REDIS_URL = f"redis://:{quote(REDIS_PASSWORD, safe='')}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
        else:
            REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

    # FalkorDB URI dengan dukungan autentikasi password
    _raw_falkordb_uri = os.environ.get('FALKORDB_URI')
    if _raw_falkordb_uri:
        if REDIS_PASSWORD and '@' not in _raw_falkordb_uri:
            from urllib.parse import urlparse, quote
            _p = urlparse(_raw_falkordb_uri)
            FALKORDB_URI = f"{_p.scheme or 'redis'}://:{quote(REDIS_PASSWORD, safe='')}@{_p.hostname or FALKORDB_HOST}:{_p.port or FALKORDB_PORT}"
        else:
            FALKORDB_URI = _raw_falkordb_uri
    else:
        if REDIS_PASSWORD:
            from urllib.parse import quote
            FALKORDB_URI = f"redis://:{quote(REDIS_PASSWORD, safe='')}@{FALKORDB_HOST}:{FALKORDB_PORT}"
        else:
            FALKORDB_URI = f"redis://{FALKORDB_HOST}:{FALKORDB_PORT}"

    # SearXNG Metasearch
    SEARXNG_ENABLED = os.environ.get('SEARXNG_ENABLED', 'true').lower() == 'true'
    SEARXNG_ENDPOINT = os.environ.get('SEARXNG_ENDPOINT') or os.environ.get('SEARXNG_URL') or os.environ.get('SEARCHXNG_URL', 'http://127.0.0.1:8088')
    SEARCHXNG_URL = SEARXNG_ENDPOINT
    
    # Database 配置 (Supabase PostgreSQL / Self-Hosted Supabase)
    DATABASE_URI = os.environ.get(
        'DATABASE_URI',
        'postgresql+psycopg://postgres.your-tenant-id:your_password@127.0.0.1:5432/postgres?options=-csearch_path%3Dmirofish,public'
    )
    
    # 文件上传配置
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '../uploads')
    ALLOWED_EXTENSIONS = {'pdf', 'md', 'txt', 'markdown'}
    
    # 文本处理配置
    DEFAULT_CHUNK_SIZE = 500  # 默认切块大小
    DEFAULT_CHUNK_OVERLAP = 50  # 默认重叠大小
    
    # OASIS模拟配置
    OASIS_DEFAULT_MAX_ROUNDS = int(os.environ.get('OASIS_DEFAULT_MAX_ROUNDS', '20'))
    OASIS_SIMULATION_DATA_DIR = os.path.join(os.path.dirname(__file__), '../uploads/simulations')

    # OASIS平台可用动作配置
    OASIS_TWITTER_ACTIONS = [
        'CREATE_POST', 'LIKE_POST', 'REPOST', 'FOLLOW', 'DO_NOTHING', 'QUOTE_POST'
    ]
    OASIS_REDDIT_ACTIONS = [
        'LIKE_POST', 'DISLIKE_POST', 'CREATE_POST', 'CREATE_COMMENT',
        'LIKE_COMMENT', 'DISLIKE_COMMENT', 'SEARCH_POSTS', 'SEARCH_USER',
        'TREND', 'REFRESH', 'DO_NOTHING', 'FOLLOW', 'MUTE'
    ]

    # Report Agent配置
    REPORT_AGENT_MAX_TOOL_CALLS = int(os.environ.get('REPORT_AGENT_MAX_TOOL_CALLS', '15'))
    REPORT_AGENT_MAX_REFLECTION_ROUNDS = int(os.environ.get('REPORT_AGENT_MAX_REFLECTION_ROUNDS', '2'))
    REPORT_AGENT_TEMPERATURE = float(os.environ.get('REPORT_AGENT_TEMPERATURE', '0.5'))

    @classmethod
    def build_redis_url(cls, host: str = None, port: int = None, password: str = None, db: int = None) -> str:
        """Membangun string koneksi Redis URL yang aman."""
        from .utils.redis_client import build_redis_url as _builder
        h = host or cls.REDIS_HOST
        p = port if port is not None else cls.REDIS_PORT
        pwd = password if password is not None else cls.REDIS_PASSWORD
        d = db if db is not None else cls.REDIS_DB
        return _builder(host=h, port=p, password=pwd, db=d)

    @classmethod
    def get_redis_url(cls, enforce_auth: bool = True) -> str:
        """Mengambil Redis URL yang diproteksi dari akses anonymous ketika REDIS_PASSWORD diset."""
        from .utils.redis_client import enforce_redis_credentials
        url = cls.REDIS_URL
        if enforce_auth and cls.REDIS_PASSWORD:
            return enforce_redis_credentials(url, required_password=cls.REDIS_PASSWORD)
        return url

    @classmethod
    def validate(cls) -> list[str]:
        """验证必要配置"""
        errors: list[str] = []
        graph_backend = os.environ.get("GRAPH_BACKEND", "zep").lower()
        if not cls.LLM_API_KEY:
            # Berikan peringatan untuk pengujian lokal jika belum dikonfigurasi
            if not os.environ.get("DEVELOPMENT_MODE", "false").lower() == "true":
                errors.append("LLM_API_KEY belum dikonfigurasi")
        if not cls.ZEP_API_KEY and graph_backend == "zep":
            if not os.environ.get("DEVELOPMENT_MODE", "false").lower() == "true":
                errors.append("ZEP_API_KEY belum dikonfigurasi (atau gunakan GRAPH_BACKEND=graphiti)")
        if os.environ.get("ZEP_API_URL"):
            errors.append("ZEP_API_URL 不受支持；MiroFish 仅连接 Zep Cloud")
        if cls.DEBUG:
            import warnings
            warnings.warn("Flask DEBUG mode is enabled. Do not use in production.", RuntimeWarning)
        return errors
