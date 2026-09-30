"""
Router API Riset Web Langkah 0 (SearXNG)
Endpoint pencarian privat, ekstraksi fakta/entitas, scoring kredibilitas
"""
import asyncio
from flask import Blueprint, request, jsonify
from ..services.web_research_service import WebResearchService
from ..utils.logger import get_logger

logger = get_logger('mirofish.api.research')
research_bp = Blueprint('research', __name__, url_prefix='/api/research')

def run_async(coro):
    """Menjalankan coroutine async di dalam handler route sinkron Flask."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    if loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    return loop.run_until_complete(coro)

@research_bp.route('/searchxng', methods=['POST'])
def search_with_searchxng():
    data = request.get_json() or {}
    query = data.get('query', '').strip()
    research_type = data.get('research_type', 'general')
    max_results = int(data.get('max_results', 10))

    if not query:
        return jsonify({"success": False, "error": {"code": "INVALID_QUERY", "message": "Kueri riset tidak boleh kosong"}}), 400
    if len(query) > 400:
        return jsonify({"success": False, "error": {"code": "QUERY_TOO_LONG", "message": "Kueri melebihi batas 400 karakter"}}), 400

    try:
        service = WebResearchService()
        report = run_async(service.research(query=query, research_type=research_type, max_results=max_results))
        return jsonify({
            "success": True,
            "data": report.to_dict(),
            "privacy_note": "Pencarian privat melalui SearXNG (tanpa pelacakan, tanpa API key komersial)"
        })
    except Exception as e:
        logger.error(f"Pencarian SearXNG gagal: {e}")
        return jsonify({"success": False, "error": {"code": "RESEARCH_FAILED", "message": str(e)}}), 500

@research_bp.route('/health', methods=['GET'])
def check_searchxng_health():
    try:
        service = WebResearchService()
        report = run_async(service.searchxng.search("uji koneksi", max_results=1))
        status = "healthy" if report.results else "degraded"
        return jsonify({
            "success": True,
            "status": status,
            "searchxng_url": service.searchxng.searchxng_url,
            "enabled": service.searchxng.enabled,
            "engines_active": report.engines_used,
            "message": "Layanan SearXNG beroperasi secara privat"
        })
    except Exception as e:
        return jsonify({
            "success": True,
            "status": "unhealthy",
            "error": str(e),
            "message": "SearXNG tidak dapat dijangkau"
        })
