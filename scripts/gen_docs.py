#!/usr/bin/env python3
"""
MiroFish Enterprise - Single-Source-of-Truth Docs Generator (Subagent F)
Mengekstrak definisi MCP Tools dari backend/mcp_server/tools.py ke docs/mcp-catalog.md
dan daftar test dari backend/tests/ ke docs/test-registry.md secara deterministik.
"""

import os
import sys
import ast
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple, Optional


REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
MCP_TOOLS_FILE = BACKEND_DIR / "mcp_server" / "tools.py"
TESTS_DIR = BACKEND_DIR / "tests"
DOCS_DIR = REPO_ROOT / "docs"

DOC_MCP_CATALOG = DOCS_DIR / "mcp-catalog.md"
DOC_TEST_REGISTRY = DOCS_DIR / "test-registry.md"

# Pemetaan kategori canonical tools berdasarkan arsitektur 6-Step MiroFish
TOOL_LIFECYCLE_MAPPING: Dict[str, Tuple[str, str]] = {
    "create_simulation_project": ("Step 0", "Project Initialization & Workspace Setup"),
    "trigger_web_research": ("Step 0", "Private Web Research & CaMeL Shield"),
    "build_knowledge_graph": ("Step 1", "GraphRAG & Dynamic Ontology Construction"),
    "generate_agent_profiles": ("Step 2", "Whole Trait Theory & System 1 ODE Personas"),
    "calibrate_platform_algorithms": ("Step 3", "7-Platform Matrix RecSys Calibration"),
    "execute_parallel_simulation": ("Step 3", "BSP Swarm Parallel Runner & WAL Checkpointing"),
    "fetch_simulation_stream": ("Step 3", "Hawkes Cascade & Action Event Streaming"),
    "query_graph_insights": ("Step 4", "BiTemporal Graph & NLI Fact Extraction"),
    "generate_executive_report": ("Step 4", "C-Level ReACT Strategic Report Synthesis"),
    "interview_simulation_agent": ("Step 4", "Agent Opinion IPC Qualitative Interview"),
    "audit_system_diagnostics": ("Step 5", "FastMCP, Vault & Transport Diagnostics"),
    "bettafish_analyze_polar_sentiment": ("Downstream", "BettaFish Polar Sentiment & Plutchik Emotion"),
    "bettafish_generate_c_level_report": ("Downstream", "BettaFish Executive SWOT & C-Level Directives"),
    "bettafish_assess_corporate_risk": ("Downstream", "BettaFish Polarization Index & Sentinel Risk"),
    "list_projects": ("Legacy", "Backward-Compatible Project Listing"),
    "get_job_status": ("Legacy", "Backward-Compatible Job Progress Polling"),
    "get_simulation_report": ("Legacy", "Backward-Compatible Simulation Report Fetching"),
    "search_knowledge_graph": ("Legacy", "Backward-Compatible Knowledge Graph Search"),
    "run_web_research": ("Legacy", "Backward-Compatible Web Search"),
    "create_simulation_job": ("Legacy", "Backward-Compatible Job Config Creation"),
    "start_simulation": ("Legacy", "Backward-Compatible Simulation Trigger"),
    "stop_simulation": ("Legacy", "Backward-Compatible Simulation Termination"),
}

# Pemetaan kategori test module
TEST_CATEGORY_MAPPING: Dict[str, str] = {
    "test_agent18": "API & OpenAPI 3.1.0 Webhooks",
    "test_all_steps": "E2E Lifecycle Pipeline",
    "test_anti_injection": "Step 0 - Prompt Injection Shield",
    "test_auth": "Security & Authentication",
    "test_bettafish": "Step 4 - BettaFish Report Engine",
    "test_bsp": "Step 3 - BSP Crash Recovery & Barrier",
    "test_cascade": "Step 3 - Hawkes Cascade Dynamics",
    "test_decision": "Step 2 - DDM Decision Engine",
    "test_domain_credibility": "Step 0 - Domain Credibility",
    "test_dynamic_ontology": "Step 1 - Dynamic Ontology Grounding",
    "test_embedding": "Embedding Services",
    "test_fastmcp": "Step 5 - FastMCP Server & OAuth 2.1",
    "test_graphiti": "Step 1 - Graphiti Control Plane",
    "test_humanoid": "Step 2 - Humanoid ODE Needs",
    "test_jwt": "Security & JWT Hardening",
    "test_llm_json": "LLM Structured JSON Parsing",
    "test_mcp_truthful": "MCP Fallbacks & Truthful Abstraction",
    "test_multi_platform": "Step 3 - Multi-Platform Simulation",
    "test_ontology": "Step 1 - Ontology & Graph Generation",
    "test_openai": "LLM Provider Compatibility",
    "test_platform": "Step 3 - Platform Matrix & RecSys",
    "test_profile": "Step 2 - Agent Profile Normalization",
    "test_psychometrics": "Step 2 - Whole Trait Psychometrics",
    "test_react": "Step 4 - ReACT Report Analyst",
    "test_recsys": "Step 3 - RecSys Funnel & Pareto",
    "test_report": "Step 4 - Report Tool Result Sanitizer",
    "test_searxng": "Step 0 - SearXNG Client Integration",
    "test_simulation": "Step 3 - Simulation Runner Lifecycle",
    "test_startup": "Security & Startup Fail-Fast Guard",
    "test_token_cost": "Token Budget & Cost Estimator",
    "test_v31_core": "Architecture - Core v3.1 Engine",
    "test_v32_enterprise": "Architecture - Enterprise v3.2 Swarm",
    "test_zep": "Step 1 - Zep Memory & Graph Adapter",
}


def extract_mcp_tools(file_path: Path) -> List[Dict[str, Any]]:
    """Mengekstrak definisi MCP tools dari file tools.py menggunakan AST."""
    if not file_path.exists():
        raise FileNotFoundError(f"File tools.py tidak ditemukan di: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    tree = ast.parse(content)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "register_mcp_tools":
            for sub in node.body:
                if isinstance(sub, ast.Assign) and len(sub.targets) == 1 and getattr(sub.targets[0], "id", "") == "tools":
                    raw_tools = ast.literal_eval(sub.value)
                    return raw_tools

    raise ValueError(f"Gagal menemukan variabel 'tools' di dalam register_mcp_tools() pada {file_path}")


def generate_mcp_catalog_markdown(tools: List[Dict[str, Any]]) -> str:
    """Menghasilkan dokumentasi Markdown terstruktur untuk seluruh MCP tools."""
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # Klasifikasikan tools
    canonical_tools = []
    bettafish_tools = []
    legacy_tools = []

    for t in tools:
        name = t["name"]
        cat, _ = TOOL_LIFECYCLE_MAPPING.get(name, ("Unknown", "Uncategorized"))
        if cat.startswith("Step"):
            canonical_tools.append(t)
        elif cat == "Downstream":
            bettafish_tools.append(t)
        else:
            legacy_tools.append(t)

    lines = [
        "# MiroFish Enterprise - MCP Tools Catalog",
        "",
        "> **Single-Source-of-Truth**: Dokumen ini dihasilkan secara otomatis dari `backend/mcp_server/tools.py` via `scripts/gen_docs.py`.",
        f"> **Status Epistemik**: `[VERIFIED]` | **Terakhir Disinkronkan**: {now_utc}",
        "> **Protokol Transport**: FastMCP Streamable HTTP (`:8080/mcp`), SSE, dan stdio fallback.",
        "> **Autentikasi**: OAuth 2.1 (RFC 7636 PKCE S256 & RFC 7662 Introspection).",
        "",
        "## Ringkasan Katalog",
        "",
        f"- **Total MCP Tools Terdaftar**: `{len(tools)}`",
        f"- **Canonical Lifecycle Tools (Step 0 - Step 5)**: `{len(canonical_tools)}`",
        f"- **BettaFish Downstream Analytics Tools**: `{len(bettafish_tools)}`",
        f"- **Legacy Backward-Compatible Tools**: `{len(legacy_tools)}`",
        "",
        "---",
        "",
        "## Daftar Isi",
        "",
        "1. [Canonical Enterprise Tools (11 Tools)](#1-canonical-enterprise-tools)",
        "2. [BettaFish Sentiment & Risk Analytics (3 Tools)](#2-bettafish-sentiment--risk-analytics)",
        "3. [Legacy Backward-Compatible Tools (8 Tools)](#3-legacy-backward-compatible-tools)",
        "4. [Detail Spesifikasi Parameter & Schema](#4-detail-spesifikasi-parameter--schema)",
        "",
        "---",
        "",
        "## 1. Canonical Enterprise Tools",
        "",
        "Tools utama yang menopang seluruh 6 fase siklus simulasi MiroFish Enterprise:",
        "",
        "| No | Tool Name | Lifecycle Step | Deskripsi | Parameter Wajib |",
        "|---|---|---|---|---|",
    ]

    for idx, t in enumerate(canonical_tools, 1):
        name = t["name"]
        step, _ = TOOL_LIFECYCLE_MAPPING.get(name, ("-", "-"))
        desc = t.get("description", "").replace("\n", " ").strip()
        schema = t.get("inputSchema", {})
        req = ", ".join(f"`{r}`" for r in schema.get("required", [])) or "*(tidak ada)*"
        lines.append(f"| {idx} | [`{name}`](#{name.replace('_', '-')}) | **{step}** | {desc} | {req} |")

    lines.extend([
        "",
        "## 2. BettaFish Sentiment & Risk Analytics",
        "",
        "Tools analitik hilir (Agent 16) untuk evaluasi polaritas, perumusan direktif C-Level, dan mitigasi krisis:",
        "",
        "| No | Tool Name | Domain Analitik | Deskripsi | Parameter Wajib |",
        "|---|---|---|---|---|",
    ])

    for idx, t in enumerate(bettafish_tools, 1):
        name = t["name"]
        desc = t.get("description", "").replace("\n", " ").strip()
        schema = t.get("inputSchema", {})
        req = ", ".join(f"`{r}`" for r in schema.get("required", [])) or "*(tidak ada)*"
        lines.append(f"| {idx} | [`{name}`](#{name.replace('_', '-')}) | BettaFish Analytics | {desc} | {req} |")

    lines.extend([
        "",
        "## 3. Legacy Backward-Compatible Tools",
        "",
        "Tools kompatibilitas backward untuk menjaga interoperabilitas penuh dengan klien legacy:",
        "",
        "| No | Tool Name | Scope Legacy | Deskripsi | Parameter Wajib |",
        "|---|---|---|---|---|",
    ])

    for idx, t in enumerate(legacy_tools, 1):
        name = t["name"]
        desc = t.get("description", "").replace("\n", " ").strip()
        schema = t.get("inputSchema", {})
        req = ", ".join(f"`{r}`" for r in schema.get("required", [])) or "*(tidak ada)*"
        lines.append(f"| {idx} | [`{name}`](#{name.replace('_', '-')}) | Backward Compatibility | {desc} | {req} |")

    lines.extend([
        "",
        "---",
        "",
        "## 4. Detail Spesifikasi Parameter & Schema",
        "",
    ])

    for idx, t in enumerate(tools, 1):
        name = t["name"]
        desc = t.get("description", "").strip()
        step, scope_desc = TOOL_LIFECYCLE_MAPPING.get(name, ("Custom", "Custom Tool"))
        schema = t.get("inputSchema", {})
        props = schema.get("properties", {})
        required_fields = set(schema.get("required", []))

        lines.extend([
            f"### `{name}`",
            "",
            f"- **Kategori**: `{step}` ({scope_desc})",
            f"- **Fungsi**: {desc}",
            "",
            "#### Parameter Masukan (`inputSchema`):",
            "",
        ])

        if props:
            lines.extend([
                "| Nama Field | Tipe | Wajib | Default | Deskripsi |",
                "|---|---|---|---|---|",
            ])
            for p_name, p_info in props.items():
                p_type = p_info.get("type", "any")
                is_req = "**Ya**" if p_name in required_fields else "Tidak"
                p_def = p_info.get("default", "-")
                if p_def is not None and p_def != "-":
                    p_def = f"`{p_def}`"
                else:
                    p_def = "`-`"
                p_desc = p_info.get("description", "-")
                lines.append(f"| `{p_name}` | `{p_type}` | {is_req} | {p_def} | {p_desc} |")
        else:
            lines.append("*(Tool ini tidak memerlukan parameter input)*")

        lines.extend([
            "",
            "#### JSON Schema:",
            "```json",
            json.dumps(schema, indent=2, ensure_ascii=False),
            "```",
            "",
            "---",
            ""
        ])

    return "\n".join(lines).strip() + "\n"


def extract_test_registry(tests_dir: Path) -> List[Dict[str, Any]]:
    """Mengekstrak seluruh test file, docstrings, dan test functions dari backend/tests/ via AST."""
    if not tests_dir.exists():
        raise FileNotFoundError(f"Direktori test tidak ditemukan di: {tests_dir}")

    test_files = sorted([f for f in tests_dir.glob("test_*.py") if f.is_file()])
    registry = []

    for fpath in test_files:
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()

        try:
            tree = ast.parse(content)
        except Exception as e:
            continue

        module_doc = (ast.get_docstring(tree) or "").strip()
        tests_in_file = []

        # Fungsi level modul
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                fdoc = (ast.get_docstring(node) or "").strip()
                fdoc_first = fdoc.split("\n")[0] if fdoc else ""
                tests_in_file.append({
                    "name": node.name,
                    "type": "function",
                    "lineno": node.lineno,
                    "docstring": fdoc_first
                })
            elif isinstance(node, ast.ClassDef):
                cdoc = (ast.get_docstring(node) or "").strip()
                for member in node.body:
                    if isinstance(member, ast.FunctionDef) and member.name.startswith("test_"):
                        mdoc = (ast.get_docstring(member) or "").strip()
                        mdoc_first = mdoc.split("\n")[0] if mdoc else ""
                        tests_in_file.append({
                            "name": f"{node.name}.{member.name}",
                            "type": "method",
                            "class_name": node.name,
                            "lineno": member.lineno,
                            "docstring": mdoc_first
                        })

        # Cari kategori berdasarkan prefix nama file
        category = "General Tests"
        for prefix, cat_name in TEST_CATEGORY_MAPPING.items():
            if fpath.name.startswith(prefix):
                category = cat_name
                break

        registry.append({
            "filename": fpath.name,
            "rel_path": f"backend/tests/{fpath.name}",
            "docstring": module_doc,
            "category": category,
            "test_count": len(tests_in_file),
            "tests": tests_in_file
        })

    return registry


def generate_test_registry_markdown(registry: List[Dict[str, Any]]) -> str:
    """Menghasilkan dokumentasi Markdown registri test suite MiroFish Enterprise."""
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    total_files = len(registry)
    total_cases = sum(item["test_count"] for item in registry)

    lines = [
        "# MiroFish Enterprise - Test Suite Registry",
        "",
        "> **Single-Source-of-Truth**: Dokumen ini dihasilkan secara otomatis dari analisis AST pada `backend/tests/` via `scripts/gen_docs.py`.",
        f"> **Status Epistemik**: `[VERIFIED]` | **Terakhir Disinkronkan**: {now_utc}",
        "> **Test Framework**: `pytest` | **Environment**: Linux x86_64 / Python 3.12+",
        "",
        "## Ringkasan Test Suite",
        "",
        f"- **Total Berkas Test**: `{total_files}` berkas",
        f"- **Total Kasus Test (Discovered Cases)**: `{total_cases}` test cases",
        "",
        "---",
        "",
        "## Matriks Modul & Kategori",
        "",
        "| No | Berkas Test | Kategori Domain | Jumlah Test | Fokus & Cakupan Pengujian |",
        "|---|---|---|---|---|",
    ]

    for idx, item in enumerate(registry, 1):
        fname = item["filename"]
        cat = item["category"]
        count = item["test_count"]
        doc = item["docstring"].split("\n")[0] if item["docstring"] else "Pengujian fungsionalitas komponen"
        anchor = fname.replace("_", "-").replace(".", "-")
        lines.append(f"| {idx} | [`{fname}`](#{anchor}) | **{cat}** | `{count}` | {doc} |")

    lines.extend([
        "",
        "---",
        "",
        "## Rincian Berkas & Kasus Pengujian",
        "",
    ])

    for item in registry:
        fname = item["filename"]
        rel_path = item["rel_path"]
        cat = item["category"]
        count = item["test_count"]
        doc = item["docstring"] or "Tidak ada modul docstring."
        anchor = fname.replace("_", "-").replace(".", "-")

        lines.extend([
            f"### `{fname}`",
            "",
            f"- **Lokasi File**: `{rel_path}`",
            f"- **Kategori**: `{cat}`",
            f"- **Total Kasus Uji**: `{count}` test",
            "",
            "**Deskripsi Modul**:",
            f"> {doc.replace(chr(10), ' ')}",
            "",
        ])

        if item["tests"]:
            lines.extend([
                "| Baris | Nama Test Identifier | Tipe | Penjelasan / Assert Inti |",
                "|---|---|---|---|",
            ])
            for t in item["tests"]:
                tname = t["name"]
                tline = t["lineno"]
                ttype = t["type"]
                tdoc = t["docstring"] or "Pengujian unit standar"
                lines.append(f"| `L{tline}` | `{tname}` | `{ttype}` | {tdoc} |")
        else:
            lines.append("*(Berkas test ini berupa script runner terpadu seperti E2E sequence tanpa decorator pytest test_)*")

        lines.extend([
            "",
            "---",
            ""
        ])

    return "\n".join(lines).strip() + "\n"


def sync_docs(check_only: bool = False) -> bool:
    """
    Eksekusi regenerasi dokumen dan verifikasi integritas.
    Jika check_only=True, return False jika terjadi drift, True jika sinkron.
    """
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Ekstrak & Generate MCP Tools Catalog
    tools = extract_mcp_tools(MCP_TOOLS_FILE)
    new_mcp_doc = generate_mcp_catalog_markdown(tools)

    # 2. Ekstrak & Generate Test Registry
    test_reg = extract_test_registry(TESTS_DIR)
    new_test_doc = generate_test_registry_markdown(test_reg)

    if check_only:
        mcp_in_sync = False
        test_in_sync = False

        if DOC_MCP_CATALOG.exists():
            # Bandingkan konten tanpa baris timestamp
            old_mcp = [l for l in DOC_MCP_CATALOG.read_text(encoding="utf-8").splitlines() if "Terakhir Disinkronkan" not in l]
            cur_mcp = [l for l in new_mcp_doc.splitlines() if "Terakhir Disinkronkan" not in l]
            mcp_in_sync = (old_mcp == cur_mcp)

        if DOC_TEST_REGISTRY.exists():
            old_test = [l for l in DOC_TEST_REGISTRY.read_text(encoding="utf-8").splitlines() if "Terakhir Disinkronkan" not in l]
            cur_test = [l for l in new_test_doc.splitlines() if "Terakhir Disinkronkan" not in l]
            test_in_sync = (old_test == cur_test)

        if mcp_in_sync and test_in_sync:
            print("[VERIFIED] Dokumentasi sinkron penuh dengan basis kode (zero drift).")
            return True
        else:
            print("[UNVERIFIED] Terdeteksi perbedaan/drift antara kode dan dokumentasi.")
            if not mcp_in_sync:
                print(f"  - Drift pada: {DOC_MCP_CATALOG}")
            if not test_in_sync:
                print(f"  - Drift pada: {DOC_TEST_REGISTRY}")
            return False

    # Tulis file dokumentasi ke disk
    DOC_MCP_CATALOG.write_text(new_mcp_doc, encoding="utf-8")
    DOC_TEST_REGISTRY.write_text(new_test_doc, encoding="utf-8")

    print("[VERIFIED_SUCCESS] Dokumentasi MiroFish Enterprise berhasil diperbarui:")
    print(f"  1. MCP Tools Catalog: {DOC_MCP_CATALOG} ({len(tools)} tools)")
    print(f"  2. Test Suite Registry: {DOC_TEST_REGISTRY} ({len(test_reg)} files, {sum(x['test_count'] for x in test_reg)} tests)")
    return True


def main():
    parser = argparse.ArgumentParser(description="MiroFish Enterprise Single-Source-of-Truth Docs Generator")
    parser.add_argument("--check", action="store_true", help="Cek apakah dokumentasi saat ini sinkron tanpa mengubah file")
    args = parser.parse_args()

    success = sync_docs(check_only=args.check)
    if not success and args.check:
        sys.exit(1)


if __name__ == "__main__":
    main()
