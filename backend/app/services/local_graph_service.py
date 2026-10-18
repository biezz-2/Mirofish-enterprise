"""
Layanan Ekstraksi & Penyimpanan Graf Mandiri (Local LLM GraphRAG)
Menyediakan penyimpanan dan ekstraksi graf tanpa ketergantungan pada Zep Cloud.
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from ..config import Config
from ..utils.logger import get_logger
from ..utils import llm_client as llm_client_module
from ..utils.file_parser import split_text_into_chunks
from ..models.graphrag_ontology import (
    to_pascal_case,
    to_screaming_snake_case,
    GroundedNode,
    GroundedEdge,
    GroundedGraph,
    SemanticChunk,
)
from .adaptive_chunker import AdaptiveSemanticChunker
from .embedding_service import configured_embedding_service

logger = get_logger("mirofish.local_graph")

class LocalGraphService:
    """Layanan Penyimpanan & Ekstraksi Graf Pengetahuan Mandiri."""

    @classmethod
    def get_graphs_dir(cls) -> str:
        upload_folder = getattr(Config, "UPLOAD_FOLDER", os.path.join(os.path.dirname(__file__), "../uploads"))
        graphs_dir = os.path.join(upload_folder, "graphs")
        os.makedirs(graphs_dir, exist_ok=True)
        return graphs_dir

    @classmethod
    def get_sqlite_connection(cls, db_path: Optional[str] = None):
        """Koneksi SQLite terstandar dengan penegakan PRAGMA journal_mode=WAL dan PRAGMA synchronous=NORMAL."""
        from ..utils.sqlite_engine import get_sqlite_connection
        if db_path is None:
            db_path = os.path.join(cls.get_graphs_dir(), "local_graphs.sqlite3")
        return get_sqlite_connection(db_path)

    @classmethod
    def get_graph_file_path(cls, graph_id: str) -> str:
        return os.path.join(cls.get_graphs_dir(), f"{graph_id}.json")

    @classmethod
    def has_local_graph(cls, graph_id: str) -> bool:
        if not graph_id:
            return False
        # Cek file langsung di uploads/graphs/<graph_id>.json
        if os.path.exists(cls.get_graph_file_path(graph_id)):
            return True
        # Cek fallback di uploads/projects/<project_id>/graph_data.json
        upload_folder = getattr(Config, "UPLOAD_FOLDER", "")
        projects_dir = os.path.join(upload_folder, "projects")
        if os.path.exists(projects_dir):
            for pid in os.listdir(projects_dir):
                proj_json = os.path.join(projects_dir, pid, "project.json")
                if os.path.exists(proj_json):
                    try:
                        with open(proj_json, "r", encoding="utf-8") as f:
                            pdata = json.load(f)
                            if pdata.get("graph_id") == graph_id:
                                gdata_file = os.path.join(projects_dir, pid, "graph_data.json")
                                if os.path.exists(gdata_file):
                                    return True
                    except Exception:
                        pass
        return False

    @classmethod
    def get_local_graph(cls, graph_id: str) -> Optional[Dict[str, Any]]:
        path = cls.get_graph_file_path(graph_id)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)

        # Cek folder project
        upload_folder = getattr(Config, "UPLOAD_FOLDER", "")
        projects_dir = os.path.join(upload_folder, "projects")
        if os.path.exists(projects_dir):
            for pid in os.listdir(projects_dir):
                proj_json = os.path.join(projects_dir, pid, "project.json")
                if os.path.exists(proj_json):
                    try:
                        with open(proj_json, "r", encoding="utf-8") as f:
                            pdata = json.load(f)
                            if pdata.get("graph_id") == graph_id:
                                gdata_file = os.path.join(projects_dir, pid, "graph_data.json")
                                if os.path.exists(gdata_file):
                                    with open(gdata_file, "r", encoding="utf-8") as gf:
                                        data = json.load(gf)
                                        cls.save_graph(graph_id, data)
                                        return data
                    except Exception:
                        pass
        return None

    @classmethod
    def save_graph(cls, graph_id: str, data: Dict[str, Any], project_id: Optional[str] = None) -> None:
        path = cls.get_graph_file_path(graph_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        if project_id:
            upload_folder = getattr(Config, "UPLOAD_FOLDER", "")
            p_graph_path = os.path.join(upload_folder, "projects", project_id, "graph_data.json")
            os.makedirs(os.path.dirname(p_graph_path), exist_ok=True)
            with open(p_graph_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    @classmethod
    def delete_local_graph(cls, graph_id: str) -> bool:
        path = cls.get_graph_file_path(graph_id)
        if os.path.exists(path):
            try:
                os.remove(path)
                return True
            except OSError:
                return False
        return False

    @classmethod
    def extract_graph_with_llm(
        cls,
        text: str,
        ontology: Dict[str, Any],
        graph_name: str = "MiroFish Graph",
        graph_id: Optional[str] = None,
        project_id: Optional[str] = None,
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ) -> Dict[str, Any]:
        """
        Mengekstrak entitas dan relasi dari teks berdasarkan ontologi menggunakan model LLM lokal.
        """
        graph_id = graph_id or f"mirofish_{uuid.uuid4().hex[:16]}"
        logger.info(f"Memulai ekstraksi graf lokal untuk {graph_id}...")

        # Sanitasi PII (UU PDP No. 27/2022) sebelum ekstraksi graf lokal
        from .pii_scrubber import PIIScrubber
        text = PIIScrubber.scrub(text)

        if progress_callback:
            progress_callback("Menyiapkan dokumen dan skema ontologi...", 0.1)

        llm_client = llm_client_module.LLMClient()

        # Ekstrak ringkasan tipe entitas dan relasi dari ontologi
        entity_types_info = []
        raw_entity_types = ontology.get("entity_types", [])
        if isinstance(raw_entity_types, list):
            for et in raw_entity_types:
                if isinstance(et, dict):
                    name = et.get("name", "")
                    desc = et.get("description", "")
                    entity_types_info.append(f"- {name}: {desc}")
                elif isinstance(et, str):
                    entity_types_info.append(f"- {et}")
        elif isinstance(raw_entity_types, dict):
            for k, v in raw_entity_types.items():
                desc = v.get("description", "") if isinstance(v, dict) else str(v)
                entity_types_info.append(f"- {k}: {desc}")

        relation_types_info = []
        raw_relations = ontology.get("relation_types", []) or ontology.get("relations", [])
        if isinstance(raw_relations, list):
            for rt in raw_relations:
                if isinstance(rt, dict):
                    name = rt.get("name", "")
                    desc = rt.get("description", "")
                    relation_types_info.append(f"- {name}: {desc}")
                elif isinstance(rt, str):
                    relation_types_info.append(f"- {rt}")
        elif isinstance(raw_relations, dict):
            for k, v in raw_relations.items():
                desc = v.get("description", "") if isinstance(v, dict) else str(v)
                relation_types_info.append(f"- {k}: {desc}")

        entity_spec = "\n".join(entity_types_info) if entity_types_info else "- Person: Individu\n- Organization: Lembaga / Komunitas"
        relation_spec = "\n".join(relation_types_info) if relation_types_info else "- DISCUSSES: Membahas topik\n- SUPPORTS: Mendukung"

        # Segmentasi adaptif semantik untuk menjaga batas topik dan referensi chunk
        chunker = AdaptiveSemanticChunker(target_chunk_size=1200, max_chunk_size=2000)
        semantic_chunks = chunker.chunk_document(text)
        if not semantic_chunks:
            plain_chunks = split_text_into_chunks(text, chunk_size=2500, overlap=200)
            semantic_chunks = [
                SemanticChunk(
                    chunk_id=f"chunk_{i+1:04d}",
                    text=c,
                    start_char=0,
                    end_char=len(c),
                    token_count=len(c) // 4,
                )
                for i, c in enumerate(plain_chunks)
            ]

        logger.info(f"Teks dibagi menjadi {len(semantic_chunks)} potongan adaptif untuk ekstraksi graf.")

        # Optional semantic pre-embedding: bounded, resumable, and disabled
        # unless an embedding credential is explicitly configured. The LLM
        # extraction contract remains unchanged; vectors are cached for later
        # retrieval/graph enrichment and make progress visible in logs.
        embedding_service = None
        if os.environ.get("ENABLE_GRAPH_PREEMBEDDING", "false").lower() in {"1", "true", "yes"}:
            embedding_service = configured_embedding_service(Config)
        if embedding_service:
            def embedding_progress(completed: int, total: int, cached: int) -> None:
                ratio = completed / total if total else 1.0
                if progress_callback:
                    progress_callback(
                        f"Embedding {completed}/{total} (cache {cached})...",
                        0.10 + ratio * 0.05,
                    )

            embedding_service.embed(
                [chunk_obj.text for chunk_obj in semantic_chunks],
                progress=embedding_progress,
            )
            logger.info("Pre-embedding completed for %d chunks", len(semantic_chunks))
        else:
            logger.info("Pre-embedding skipped: EMBEDDING_API_KEY/NINEROUTER_KEY is not configured")

        all_raw_entities: List[Dict[str, Any]] = []
        all_raw_relations: List[Dict[str, Any]] = []

        total_chunks = len(semantic_chunks)
        for idx, chunk_obj in enumerate(semantic_chunks):
            chunk_id = chunk_obj.chunk_id
            chunk_text = chunk_obj.text
            if progress_callback:
                ratio = 0.15 + (idx / total_chunks) * 0.55  # 15% - 70%
                progress_callback(f"Mengekstrak entitas & relasi dari segmen {idx+1}/{total_chunks} ({chunk_id})...", ratio)

            system_prompt = f"""Kamu adalah mesin ekstraksi Knowledge Graph untuk simulasi media sosial.
Tugasmu adalah menganalisis teks dan mengekstrak entitas serta relasi sesuai dengan skema ontologi berikut:

### Tipe Entitas yang Diizinkan (harus PascalCase):
{entity_spec}

### Tipe Relasi yang Diizinkan (harus SCREAMING_SNAKE_CASE):
{relation_spec}

Aturan Ekstraksi:
1. Ekstrak entitas nyata yang relevan untuk simulasi sosial (tokoh, analis, influencer, media, komunitas, topik penting).
2. Setiap entitas HARUS memiliki:
   - "name": Nama entitas (jelas dan konsisten)
   - "type": Salah satu dari tipe entitas di atas (dalam PascalCase)
   - "summary": 1-2 kalimat deskripsi ringkas tentang entitas ini berdasarkan teks
   - "attributes": Dictionary berisi atribut pendukung (misal: platform, role, stance)
3. Setiap relasi HARUS menghubungkan dua entitas yang diekstrak:
   - "source": Nama entitas sumber
   - "target": Nama entitas target
   - "relation": Tipe relasi (dalam SCREAMING_SNAKE_CASE)
   - "fact": 1 kalimat fakta relasi yang terjadi antara kedua entitas
4. Output HARUS dalam format JSON valid dengan key "entities" dan "relations"."""

            user_prompt = f"""Ekstrak entitas dan relasi dari teks berikut ke dalam format JSON:

{chunk_text}"""

            try:
                resp = llm_client.chat_json([
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ], temperature=0.2)

                extracted_ents = resp.get("entities", [])
                extracted_rels = resp.get("relations", [])
                if isinstance(extracted_ents, list):
                    for ent in extracted_ents:
                        if isinstance(ent, dict):
                            ent["_source_chunk_id"] = chunk_id
                            all_raw_entities.append(ent)
                if isinstance(extracted_rels, list):
                    for rel in extracted_rels:
                        if isinstance(rel, dict):
                            rel["_source_chunk_id"] = chunk_id
                            all_raw_relations.append(rel)
            except Exception as e:
                logger.warning(f"Ekstraksi chunk {idx+1} ({chunk_id}) gagal/parsial: {e}")

        if progress_callback:
            progress_callback("Menyintesis dan memvalidasi struktur graf pengetahuan...", 0.75)

        # Normalisasi dan deduplikasi entitas dengan penegakan PascalCase & pelacakan chunk_id
        nodes_dict: Dict[str, Dict[str, Any]] = {}
        for ent in all_raw_entities:
            if not isinstance(ent, dict):
                continue
            name = (ent.get("name") or "").strip()
            if not name or len(name) < 2:
                continue
            raw_type = ent.get("type") or ent.get("entity_type") or "Entity"
            ent_type = to_pascal_case(raw_type)
            summary = ent.get("summary") or ""
            attributes = ent.get("attributes") or {}
            if not isinstance(attributes, dict):
                attributes = {}
            source_chunk_id = ent.get("_source_chunk_id")
            chunk_ids = [source_chunk_id] if source_chunk_id else []

            if name not in nodes_dict:
                node_uuid = f"node_{uuid.uuid4().hex[:12]}"
                labels = [ent_type, "Entity"] if ent_type != "Entity" else ["Entity"]
                nodes_dict[name] = {
                    "uuid": node_uuid,
                    "name": name,
                    "entity_type": ent_type,
                    "labels": labels,
                    "summary": summary,
                    "attributes": attributes,
                    "chunk_ids": chunk_ids,
                    "created_at": datetime.now().isoformat(),
                }
            else:
                if source_chunk_id and source_chunk_id not in nodes_dict[name]["chunk_ids"]:
                    nodes_dict[name]["chunk_ids"].append(source_chunk_id)
                # Perbarui summary jika lebih lengkap
                if len(summary) > len(nodes_dict[name]["summary"]):
                    nodes_dict[name]["summary"] = summary
                nodes_dict[name]["attributes"].update(attributes)

        # Normalisasi dan filter relasi dengan penegakan SCREAMING_SNAKE & pelacakan chunk_id
        edges_data: List[Dict[str, Any]] = []
        seen_edges = set()

        for rel in all_raw_relations:
            if not isinstance(rel, dict):
                continue
            src_name = (rel.get("source") or "").strip()
            tgt_name = (rel.get("target") or "").strip()
            raw_rel_type = (rel.get("relation") or rel.get("type") or "RELATION").strip()
            rel_type = to_screaming_snake_case(raw_rel_type)
            fact = (rel.get("fact") or f"{src_name} {rel_type} {tgt_name}").strip()
            source_chunk_id = rel.get("_source_chunk_id")
            chunk_ids = [source_chunk_id] if source_chunk_id else []

            if not src_name or not tgt_name or src_name == tgt_name:
                continue

            # Buat node jika belum ada
            if src_name not in nodes_dict:
                src_uuid = f"node_{uuid.uuid4().hex[:12]}"
                nodes_dict[src_name] = {
                    "uuid": src_uuid,
                    "name": src_name,
                    "entity_type": "Entity",
                    "labels": ["Entity"],
                    "summary": f"Entitas sumber: {src_name}",
                    "attributes": {},
                    "chunk_ids": chunk_ids,
                    "created_at": datetime.now().isoformat()
                }
            elif source_chunk_id and source_chunk_id not in nodes_dict[src_name]["chunk_ids"]:
                nodes_dict[src_name]["chunk_ids"].append(source_chunk_id)

            src_uuid = nodes_dict[src_name]["uuid"]

            if tgt_name not in nodes_dict:
                tgt_uuid = f"node_{uuid.uuid4().hex[:12]}"
                nodes_dict[tgt_name] = {
                    "uuid": tgt_uuid,
                    "name": tgt_name,
                    "entity_type": "Entity",
                    "labels": ["Entity"],
                    "summary": f"Entitas target: {tgt_name}",
                    "attributes": {},
                    "chunk_ids": chunk_ids,
                    "created_at": datetime.now().isoformat()
                }
            elif source_chunk_id and source_chunk_id not in nodes_dict[tgt_name]["chunk_ids"]:
                nodes_dict[tgt_name]["chunk_ids"].append(source_chunk_id)

            tgt_uuid = nodes_dict[tgt_name]["uuid"]

            edge_key = (src_uuid, tgt_uuid, rel_type)
            if edge_key in seen_edges:
                continue
            seen_edges.add(edge_key)

            edge_uuid = f"edge_{uuid.uuid4().hex[:12]}"
            edges_data.append({
                "uuid": edge_uuid,
                "name": rel_type,
                "relation_type": rel_type,
                "fact": fact,
                "fact_type": rel_type,
                "source_node_uuid": src_uuid,
                "target_node_uuid": tgt_uuid,
                "source_node_name": src_name,
                "target_node_name": tgt_name,
                "attributes": {},
                "chunk_ids": chunk_ids,
                "created_at": datetime.now().isoformat(),
                "valid_at": None,
                "invalid_at": None,
                "expired_at": None,
                "episodes": [],
            })

        nodes_data = list(nodes_dict.values())
        entity_types = set()
        for n in nodes_data:
            for l in n.get("labels", []):
                if l not in ["Entity", "Node"]:
                    entity_types.add(l)

        final_graph = {
            "graph_id": graph_id,
            "name": graph_name,
            "nodes": nodes_data,
            "edges": edges_data,
            "chunks": [c.model_dump() for c in semantic_chunks],
            "node_count": len(nodes_data),
            "edge_count": len(edges_data),
            "entity_types": list(entity_types),
            "backend": "local_llm_graphrag"
        }

        cls.save_graph(graph_id, final_graph, project_id=project_id)
        logger.info(f"Graf lokal berhasil disimpan: {graph_id} ({len(nodes_data)} node, {len(edges_data)} edge)")

        if progress_callback:
            progress_callback(f"Graf berhasil disusun: {len(nodes_data)} entitas, {len(edges_data)} relasi.", 1.0)

        return final_graph

    @classmethod
    def extract_and_build_graph(
        cls,
        text: str,
        ontology: Optional[Dict[str, Any]] = None,
        graph_name: str = "MiroFish Graph",
        graph_id: Optional[str] = None,
        project_id: Optional[str] = None,
        entity_types_info: Optional[List[str]] = None,
        relation_types_info: Optional[List[str]] = None,
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ) -> Dict[str, Any]:
        """
        Wrapper convenience method for extracting and building grounded graph.
        Supports passing either ontology dict or direct entity_types_info / relation_types_info.
        """
        if ontology is None:
            ontology = {
                "entity_types": [{"name": e.split(":")[0].replace("-", "").strip()} for e in (entity_types_info or [])],
                "relation_types": [{"name": r.split(":")[0].replace("-", "").strip()} for r in (relation_types_info or [])]
            }
        return cls.extract_graph_with_llm(
            text=text,
            ontology=ontology,
            graph_name=graph_name,
            graph_id=graph_id,
            project_id=project_id,
            progress_callback=progress_callback
        )