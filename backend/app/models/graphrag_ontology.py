"""
GraphRAG Grounded Ontology Models & Pydantic Schemas.
Enforces strict PascalCase for Node entity types and SCREAMING_SNAKE for Relation edge types.
Supports chunk reference tracking and Step 0 research grounding.
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


def is_pascal_case(name: str) -> bool:
    """Return True if name is strict PascalCase (e.g. 'Person', 'MediaOrganization')."""
    if not isinstance(name, str) or not name:
        return False
    return bool(re.match(r'^[A-Z][a-zA-Z0-9]*$', name))


def to_pascal_case(name: str) -> str:
    """
    Convert arbitrary string (snake_case, camelCase, kebab-case, spaced) to strict PascalCase.
    Guarantees output matches ^[A-Z][a-zA-Z0-9]*$.
    """
    if not isinstance(name, str) or not name.strip():
        return "Entity"

    raw = name.strip()
    # Strip leading non-alphabetic chars so it starts with a letter
    raw = re.sub(r'^[^a-zA-Z]+', '', raw)
    if not raw:
        return "Entity"

    # Split on non-alphanumeric characters
    parts = re.split(r'[^a-zA-Z0-9]+', raw)
    words: List[str] = []
    for part in parts:
        # Separate camelCase boundaries: 'mediaOrg' -> 'media_Org'
        expanded = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', part)
        for w in expanded.split('_'):
            if w:
                words.append(w.capitalize())

    result = "".join(words)
    if not result:
        return "Entity"
    if not result[0].isalpha() or not result[0].isupper():
        result = "Entity" + result
    return result


def is_screaming_snake_case(name: str) -> bool:
    """Return True if name is strict SCREAMING_SNAKE_CASE (e.g. 'SUPPORTS', 'AFFILIATED_WITH')."""
    if not isinstance(name, str) or not name:
        return False
    return bool(re.match(r'^[A-Z][A-Z0-9]*(_[A-Z0-9]+)*$', name))


def to_screaming_snake_case(name: str) -> str:
    """
    Convert arbitrary string to strict SCREAMING_SNAKE_CASE.
    Guarantees output matches ^[A-Z][A-Z0-9]*(_[A-Z0-9]+)*$.
    """
    if not isinstance(name, str) or not name.strip():
        return "RELATION"

    raw = name.strip()
    # Expand camelCase / PascalCase boundaries
    separated = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', raw)
    # Replace any non-alphanumeric chars with underscore
    normalized = re.sub(r'[^a-zA-Z0-9]+', '_', separated).strip('_').upper()
    # Collapse multiple consecutive underscores
    normalized = re.sub(r'_+', '_', normalized)

    if not normalized:
        return "RELATION"
    if normalized[0].isdigit():
        normalized = f"REL_{normalized}"
    return normalized


class OntologyAttribute(BaseModel):
    """Attribute definition for an entity or relation type."""
    name: str
    type: str = "text"
    description: str = ""

    @field_validator("name")
    def validate_name(cls, v: str) -> str:
        s = v.strip().lower()
        cleaned = re.sub(r'[^a-z0-9_]+', '_', s).strip('_')
        return cleaned or "attribute"


class SourceTargetPair(BaseModel):
    """Allowed source and target entity types for a relation."""
    source: str = "Entity"
    target: str = "Entity"

    @field_validator("source", "target")
    def validate_pascal(cls, v: str) -> str:
        return to_pascal_case(v)


class EntityDefinition(BaseModel):
    """Entity schema definition enforced to PascalCase."""
    name: str
    description: str = ""
    attributes: List[OntologyAttribute] = Field(default_factory=list)
    grounded_in_corpus: bool = True

    @field_validator("name")
    def validate_entity_name(cls, v: str) -> str:
        return to_pascal_case(v)


class RelationDefinition(BaseModel):
    """Relation schema definition enforced to SCREAMING_SNAKE."""
    name: str
    description: str = ""
    source_targets: List[SourceTargetPair] = Field(default_factory=list)
    attributes: List[OntologyAttribute] = Field(default_factory=list)

    @field_validator("name")
    def validate_relation_name(cls, v: str) -> str:
        return to_screaming_snake_case(v)


class OntologySchema(BaseModel):
    """Strict GraphRAG ontology schema with grounded types."""
    entity_types: List[EntityDefinition] = Field(default_factory=list)
    relation_types: List[RelationDefinition] = Field(default_factory=list)
    domain_context: Optional[str] = None
    step0_grounding_verified: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def ensure_valid_names(self):
        # Validate that all entity names are unique and in PascalCase
        seen_entities = set()
        for et in self.entity_types:
            if not is_pascal_case(et.name):
                et.name = to_pascal_case(et.name)
            seen_entities.add(et.name)

        # Validate that all relation names are in SCREAMING_SNAKE
        for rt in self.relation_types:
            if not is_screaming_snake_case(rt.name):
                rt.name = to_screaming_snake_case(rt.name)

        return self


class SemanticChunk(BaseModel):
    """Structured text chunk produced by AdaptiveSemanticChunker."""
    chunk_id: str
    text: str
    start_char: int
    end_char: int
    token_count: int
    section_header: Optional[str] = None
    cohesion_score: float = 1.0
    source_doc: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GroundedNode(BaseModel):
    """Knowledge Graph node linked to origin semantic chunk references."""
    uuid: str
    name: str
    entity_type: str
    labels: List[str] = Field(default_factory=list)
    summary: str = ""
    attributes: Dict[str, Any] = Field(default_factory=dict)
    chunk_ids: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())

    @field_validator("entity_type")
    def validate_type(cls, v: str) -> str:
        return to_pascal_case(v)

    @field_validator("labels")
    def validate_labels(cls, v: List[str], info) -> List[str]:
        cleaned = [to_pascal_case(label) for label in v if label]
        if "Entity" not in cleaned:
            cleaned.append("Entity")
        return cleaned


class GroundedEdge(BaseModel):
    """Knowledge Graph edge linked to origin semantic chunk references."""
    uuid: str
    name: str
    relation_type: Optional[str] = None
    source_node_uuid: str
    target_node_uuid: str
    source_node_name: str
    target_node_name: str
    fact: str
    attributes: Dict[str, Any] = Field(default_factory=dict)
    chunk_ids: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())

    @field_validator("name")
    def validate_relation(cls, v: str) -> str:
        return to_screaming_snake_case(v)

    @model_validator(mode="after")
    def sync_relation_type(self):
        if not self.relation_type:
            self.relation_type = self.name
        else:
            self.relation_type = to_screaming_snake_case(self.relation_type)
        return self


class GroundedGraph(BaseModel):
    """Complete grounded knowledge graph representation."""
    graph_id: str
    name: str = "MiroFish Grounded Graph"
    nodes: List[GroundedNode] = Field(default_factory=list)
    edges: List[GroundedEdge] = Field(default_factory=list)
    chunks: List[SemanticChunk] = Field(default_factory=list)
    node_count: int = 0
    edge_count: int = 0
    entity_types: List[str] = Field(default_factory=list)
    backend: str = "grounded_graphrag"

    @model_validator(mode="after")
    def update_counts(self):
        self.node_count = len(self.nodes)
        self.edge_count = len(self.edges)
        types = set()
        for n in self.nodes:
            types.add(n.entity_type)
        self.entity_types = sorted(list(types))
        return self
