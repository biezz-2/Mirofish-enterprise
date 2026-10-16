"""
Unit & Integration Tests for Slice 05: Dynamic Ontology Generation & Schema Grounding.
Tests PascalCase entity names, SCREAMING_SNAKE relation types, Pydantic schema validation,
adaptive semantic chunking, and Step 0 research grounding.
"""

import os
import json
import re
import pytest
from typing import Dict, Any, List

from app.models.graphrag_ontology import (
    is_pascal_case,
    to_pascal_case,
    is_screaming_snake_case,
    to_screaming_snake_case,
    OntologyAttribute,
    EntityDefinition,
    RelationDefinition,
    SourceTargetPair,
    OntologySchema,
    SemanticChunk,
    GroundedNode,
    GroundedEdge,
    GroundedGraph,
)
from app.services.adaptive_chunker import AdaptiveSemanticChunker
from app.services.text_processor import TextProcessor
from app.services.ontology_generator import OntologyGeneratorService
from app.services.local_graph_service import LocalGraphService


class TestCasingConventions:
    """Test strict casing normalization and validation."""

    @pytest.mark.parametrize("raw,expected", [
        ("person", "Person"),
        ("media_organization", "MediaOrganization"),
        ("publicFigure", "PublicFigure"),
        ("political-party", "PoliticalParty"),
        ("ai_researcher", "AiResearcher"),
        ("123analyst", "Analyst"),
        ("___influencer___", "Influencer"),
        ("Social Media Platform", "SocialMediaPlatform"),
        ("", "Entity"),
    ])
    def test_to_pascal_case(self, raw: str, expected: str):
        result = to_pascal_case(raw)
        assert result == expected
        assert is_pascal_case(result)
        assert re.match(r'^[A-Z][a-zA-Z0-9]*$', result) is not None

    @pytest.mark.parametrize("raw,expected", [
        ("supports", "SUPPORTS"),
        ("affiliated_with", "AFFILIATED_WITH"),
        ("worksFor", "WORKS_FOR"),
        ("opposes-policy", "OPPOSES_POLICY"),
        ("funds and sponsors", "FUNDS_AND_SPONSORS"),
        ("123_connects", "REL_123_CONNECTS"),
        ("___mentions___", "MENTIONS"),
        ("", "RELATION"),
    ])
    def test_to_screaming_snake_case(self, raw: str, expected: str):
        result = to_screaming_snake_case(raw)
        assert result == expected
        assert is_screaming_snake_case(result)
        assert re.match(r'^[A-Z][A-Z0-9]*(_[A-Z0-9]+)*$', result) is not None


class TestPydanticOntologyModels:
    """Test Pydantic schema validation for Grounded GraphRAG."""

    def test_entity_definition_validation(self):
        entity = EntityDefinition(
            name="public_analyst",
            description="Expert analyst",
            attributes=[
                OntologyAttribute(name="Credibility_Score", type="float"),
                OntologyAttribute(name="affiliation", type="text"),
            ]
        )
        assert entity.name == "PublicAnalyst"
        assert is_pascal_case(entity.name)
        assert len(entity.attributes) == 2
        assert entity.attributes[0].name == "credibility_score"

    def test_relation_definition_validation(self):
        relation = RelationDefinition(
            name="publishes_opinion_on",
            description="Publishes an opinion piece",
            source_targets=[
                SourceTargetPair(source="media_org", target="hot_topic")
            ]
        )
        assert relation.name == "PUBLISHES_OPINION_ON"
        assert is_screaming_snake_case(relation.name)
        assert relation.source_targets[0].source == "MediaOrg"
        assert relation.source_targets[0].target == "HotTopic"

    def test_ontology_schema_validation(self):
        schema = OntologySchema(
            entity_types=[
                EntityDefinition(name="GovernmentAgency", description="Public policy maker"),
                EntityDefinition(name="KeyOpinionLeader", description="Social influencer"),
            ],
            relation_types=[
                RelationDefinition(
                    name="CRITICIZES_POLICY",
                    source_targets=[SourceTargetPair(source="KeyOpinionLeader", target="GovernmentAgency")]
                )
            ],
            domain_context="Public Health Policy Discourse",
            step0_grounding_verified=True,
        )
        assert len(schema.entity_types) == 2
        assert schema.entity_types[0].name == "GovernmentAgency"
        assert schema.relation_types[0].name == "CRITICIZES_POLICY"
        assert schema.step0_grounding_verified is True

    def test_grounded_node_and_edge_reference_tracking(self):
        node = GroundedNode(
            uuid="node_001",
            name="Ministry of Health",
            entity_type="gov_agency",
            labels=["GovAgency"],
            summary="National health authority",
            attributes={"stance": "pro-vaccine"},
            chunk_ids=["chunk_0001", "chunk_0003"]
        )
        assert node.entity_type == "GovAgency"
        assert "GovAgency" in node.labels
        assert "Entity" in node.labels
        assert "chunk_0001" in node.chunk_ids

        edge = GroundedEdge(
            uuid="edge_001",
            name="announces_mandate",
            source_node_uuid="node_001",
            target_node_uuid="node_002",
            source_node_name="Ministry of Health",
            target_node_name="Public Citizens",
            fact="Ministry of Health announces new vaccination requirements",
            chunk_ids=["chunk_0001"]
        )
        assert edge.name == "ANNOUNCES_MANDATE"
        assert edge.relation_type == "ANNOUNCES_MANDATE"
        assert edge.chunk_ids == ["chunk_0001"]


class TestAdaptiveSemanticChunker:
    """Test topic boundary preservation and cohesion scoring."""

    def test_structural_header_chunking(self):
        text = """# Executive Summary
MiroFish Enterprise provides multi-agent simulation for social opinion dynamics.
The system forecasts narrative cascades and viral misinformation trajectories.

# Technical Architecture
The core architecture integrates FalkorDB for GraphRAG operations.
Semantic chunking partitions documents while maintaining strict topic boundaries.

## Psychological Modeling
System 1 affective sentiment transitions govern agent emotional reactions.
Differential equations simulate affective decay over continuous time intervals.
"""
        chunker = AdaptiveSemanticChunker(target_chunk_size=300, min_chunk_size=100, max_chunk_size=600)
        chunks = chunker.chunk_document(text, source_doc="whitepaper.md")

        assert len(chunks) == 3
        assert chunks[0].section_header == "Executive Summary"
        assert chunks[1].section_header == "Technical Architecture"
        assert chunks[2].section_header == "Psychological Modeling"
        assert chunks[0].source_doc == "whitepaper.md"

        # Verify token counts and cohesion scores
        for c in chunks:
            assert c.token_count > 0
            assert 0.0 <= c.cohesion_score <= 1.0
            assert c.metadata.get("redundant_tokens") == 0

    def test_text_processor_adaptive_integration(self):
        text = """## Section Alpha
Paragraph one discusses geopolitical events and international relations between states.

## Section Beta
Paragraph two discusses computational graph neural networks and node embeddings.
"""
        chunks = TextProcessor.split_text_adaptive(text, target_chunk_size=200, min_chunk_size=50)
        assert len(chunks) == 2
        assert chunks[0].section_header == "Section Alpha"
        assert chunks[1].section_header == "Section Beta"

        plain_chunks = TextProcessor.split_text(text, chunk_size=200, overlap=50, adaptive=True)
        assert len(plain_chunks) == 2
        assert "geopolitical" in plain_chunks[0]
        assert "computational" in plain_chunks[1]


class TestStep0ResearchGrounding:
    """Test ontology grounding with Step 0 research contract."""

    def test_ground_with_step0_research(self, tmp_path):
        sample_contract = {
            "contract": "01-step0-research",
            "version": "1.0.0",
            "payload": {
                "min_credibility_score": 0.85,
                "verified_claims_count": 15,
                "sources": [
                    {"domain": "arxiv.org", "credibility": 0.95, "verified": True},
                    {"domain": "nature.com", "credibility": 0.98, "verified": True},
                ]
            }
        }
        contract_file = tmp_path / "01-step0-research.json"
        contract_file.write_text(json.dumps(sample_contract), encoding="utf-8")

        raw_ontology = {
            "entity_types": [
                {"name": "research_scientist", "description": "Academic author"},
                {"name": "peer_reviewed_paper", "description": "Published paper"}
            ],
            "edge_types": [
                {
                    "name": "authors_and_publishes",
                    "description": "Writes paper",
                    "source_targets": [{"source": "research_scientist", "target": "peer_reviewed_paper"}]
                }
            ]
        }

        grounded = OntologyGeneratorService.ground_with_step0_research(
            raw_ontology,
            research_contract_path=str(contract_file)
        )

        assert grounded["step0_grounding_verified"] is True
        assert grounded["schema_valid"] is True
        assert grounded["grounding_metadata"]["min_credibility_score"] == 0.85
        assert grounded["grounding_metadata"]["sources_count"] == 2
        assert "arxiv.org" in grounded["grounding_metadata"]["verified_sources"]


class TestLocalGraphServiceEndToEnd:
    """Test LocalGraphService end-to-end extraction and grounded graph building."""

    def test_local_graph_extract_and_build(self, monkeypatch, tmp_path):
        # Mock LLM Client to return simulated entities and relations
        class MockLLMClient:
            def chat_json(self, messages, temperature=0.2):
                return {
                    "entities": [
                        {
                            "name": "Satgas Covid",
                            "type": "government_taskforce",
                            "summary": "National emergency management committee",
                            "attributes": {"jurisdiction": "National"}
                        },
                        {
                            "name": "Komunitas Relawan",
                            "type": "community_group",
                            "summary": "Grassroots civic support network",
                            "attributes": {"focus": "aid"}
                        }
                    ],
                    "relations": [
                        {
                            "source": "Satgas Covid",
                            "target": "Komunitas Relawan",
                            "relation": "coordinates_with",
                            "fact": "Satgas Covid coordinates logistical distribution with Komunitas Relawan"
                        }
                    ]
                }

        from app.utils import llm_client as client_module
        monkeypatch.setattr(client_module, "LLMClient", lambda: MockLLMClient())

        test_text = """# Dokumen Penanganan Pandemi
Satgas Covid mengumumkan protokol penanganan darurat bersama Komunitas Relawan di seluruh daerah.
Koordinasi logistik dilakukan secara langsung melalui jalur komando terpadu.
"""
        graph = LocalGraphService.extract_and_build_graph(
            text=test_text,
            graph_id="test_graph_slice_05",
            graph_name="Pandemic Response Graph",
            entity_types_info=["- GovernmentTaskforce: Satuan tugas pemerintah", "- CommunityGroup: Komunitas masyarakat"],
            relation_types_info=["- COORDINATES_WITH: Berkoordinasi dalam logistik"],
        )

        assert graph["graph_id"] == "test_graph_slice_05"
        assert graph["node_count"] == 2
        assert graph["edge_count"] == 1
        assert "chunks" in graph
        assert len(graph["chunks"]) > 0

        # Check node casing and chunk tracking
        node_names = [n["name"] for n in graph["nodes"]]
        assert "Satgas Covid" in node_names
        assert "Komunitas Relawan" in node_names

        for node in graph["nodes"]:
            assert is_pascal_case(node["entity_type"])
            assert len(node["chunk_ids"]) > 0

        # Check edge casing and chunk tracking
        edge = graph["edges"][0]
        assert is_screaming_snake_case(edge["name"])
        assert edge["name"] == "COORDINATES_WITH"
        assert len(edge["chunk_ids"]) > 0
