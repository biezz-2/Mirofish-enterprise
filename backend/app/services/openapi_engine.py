"""
MiroFish Enterprise - OpenAPI 3.1.0 & JSON Schema 2020-12 Engine (Agent 18: Divisi F)
Membangun spesifikasi RESTful API OpenAPI 3.1.0 terikat dialek JSON Schema 2020-12:
- Definisi Webhooks tingkat atas (Top-Level Webhooks Object)
- Registri Skema Terverifikasi JSON Schema 2020-12 (Draft202012Validator)
- Dekorator validasi payload request Flask terstandarisasi (HTTP 422 Unprocessable Entity)
- Export spesifikasi OpenAPI 3.1.0 dalam format JSON dan YAML
"""

import json
import functools
from typing import Dict, Any, List, Optional, Tuple, Callable
import yaml
from flask import request, jsonify, make_response
from jsonschema import Draft202012Validator, ValidationError

# ---------------------------------------------------------------------------
# Definisi Skema JSON Schema 2020-12 untuk Komponen
# ---------------------------------------------------------------------------

JSON_SCHEMA_DIALECT_2020_12 = "https://json-schema.org/draft/2020-12/schema"

SIMULATION_PROJECT_SCHEMA: Dict[str, Any] = {
    "$schema": JSON_SCHEMA_DIALECT_2020_12,
    "type": "object",
    "properties": {
        "title": {"type": "string", "minLength": 3},
        "target_audience": {"type": "string"},
        "initial_agents_count": {"type": "integer", "minimum": 1, "default": 20},
        "platforms": {
            "type": "array",
            "items": {"type": "string"},
            "default": ["twitter_x"]
        }
    },
    "required": ["title"]
}

WEBHOOK_SUBSCRIPTION_SCHEMA: Dict[str, Any] = {
    "$schema": JSON_SCHEMA_DIALECT_2020_12,
    "type": "object",
    "properties": {
        "target_url": {"type": "string"},
        "secret_key": {"type": "string", "minLength": 8},
        "subscribed_events": {
            "type": "array",
            "items": {"type": "string"},
            "default": ["*"]
        },
        "description": {"type": "string", "default": ""},
        "headers": {
            "type": "object",
            "additionalProperties": {"type": "string"},
            "default": {}
        }
    },
    "required": ["target_url"]
}

COMPONENT_SCHEMAS: Dict[str, Dict[str, Any]] = {
    "SimulationProjectRequest": SIMULATION_PROJECT_SCHEMA,
    "WebhookSubscriptionRequest": WEBHOOK_SUBSCRIPTION_SCHEMA,
    "ErrorResponse": {
        "$schema": JSON_SCHEMA_DIALECT_2020_12,
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "const": False},
            "error": {
                "type": "object",
                "properties": {
                    "code": {"type": "string"},
                    "message": {"type": "string"},
                    "details": {
                        "type": ["array", "null"],
                        "items": {"type": "object"}
                    }
                },
                "required": ["code", "message"]
            }
        },
        "required": ["success", "error"]
    },
    "HealthResponse": {
        "$schema": JSON_SCHEMA_DIALECT_2020_12,
        "type": "object",
        "properties": {
            "status": {"type": "string", "enum": ["healthy", "degraded", "down"]},
            "version": {"type": "string"},
            "timestamp": {"type": "string"},
            "services": {
                "type": "object",
                "additionalProperties": {"type": "string"}
            }
        },
        "required": ["status", "version"]
    },
    "BettaFishSentimentRequest": {
        "$schema": JSON_SCHEMA_DIALECT_2020_12,
        "type": "object",
        "properties": {
            "text": {"type": "string", "minLength": 1},
            "domain": {"type": "string", "default": "general"}
        },
        "required": ["text"]
    },
    "BettaFishSentimentResponse": {
        "$schema": JSON_SCHEMA_DIALECT_2020_12,
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "sentiment": {
                "type": "object",
                "properties": {
                    "score": {"type": "number", "minimum": -1.0, "maximum": 1.0},
                    "label": {"type": "string", "enum": ["POSITIVE", "NEUTRAL", "NEGATIVE", "EXTREME_NEGATIVE", "EXTREME_POSITIVE"]},
                    "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                    "emotion_vector": {
                        "type": "object",
                        "properties": {
                            "joy": {"type": "number"},
                            "anger": {"type": "number"},
                            "fear": {"type": "number"},
                            "sadness": {"type": "number"},
                            "surprise": {"type": "number"}
                        }
                    }
                },
                "required": ["score", "label", "confidence"]
            }
        },
        "required": ["success", "sentiment"]
    },
    "BettaFishExecutiveReportRequest": {
        "$schema": JSON_SCHEMA_DIALECT_2020_12,
        "type": "object",
        "properties": {
            "topic": {"type": "string", "minLength": 1},
            "claims": {
                "type": "array",
                "items": {"type": "string"},
                "default": []
            },
            "broadcast_webhook": {"type": "boolean", "default": True}
        },
        "required": ["topic"]
    },
    "BettaFishExecutiveReportResponse": {
        "$schema": JSON_SCHEMA_DIALECT_2020_12,
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "report": {
                "type": "object",
                "properties": {
                    "report_id": {"type": "string"},
                    "topic": {"type": "string"},
                    "key_takeaways": {"type": "array", "items": {"type": "string"}},
                    "strategic_recommendations": {"type": "array", "items": {"type": "string"}},
                    "overall_sentiment_score": {"type": "number"},
                    "swot_analysis": {"type": "object"},
                    "c_level_directives": {"type": "object"}
                },
                "required": ["report_id", "topic", "strategic_recommendations"]
            },
            "webhook_dispatched": {"type": "boolean"}
        },
        "required": ["success", "report"]
    },
    "BettaFishRiskAssessmentRequest": {
        "$schema": JSON_SCHEMA_DIALECT_2020_12,
        "type": "object",
        "properties": {
            "polarity_score": {"type": "number", "minimum": -1.0, "maximum": 1.0},
            "virality_potential": {"type": "number", "minimum": 0.0, "maximum": 1.0, "default": 0.0},
            "topic": {"type": "string", "default": "general"},
            "broadcast_webhook": {"type": "boolean", "default": True}
        },
        "required": ["polarity_score"]
    },
    "BettaFishRiskAssessmentResponse": {
        "$schema": JSON_SCHEMA_DIALECT_2020_12,
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "risk_assessment": {
                "type": "object",
                "properties": {
                    "risk_level": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]},
                    "early_warning_active": {"type": "boolean"},
                    "mitigation_playbook": {"type": "array", "items": {"type": "string"}},
                    "composite_risk_score": {"type": "number"}
                },
                "required": ["risk_level", "early_warning_active", "mitigation_playbook"]
            },
            "alert_dispatched": {"type": "boolean"}
        },
        "required": ["success", "risk_assessment"]
    },
    "WebhookSubscriptionRequest": {
        "$schema": JSON_SCHEMA_DIALECT_2020_12,
        "type": "object",
        "properties": {
            "target_url": {"type": "string", "format": "uri"},
            "secret_key": {"type": "string", "minLength": 8},
            "subscribed_events": {
                "type": "array",
                "items": {"type": "string"},
                "default": ["*"]
            },
            "description": {"type": "string", "default": ""},
            "headers": {
                "type": "object",
                "additionalProperties": {"type": "string"},
                "default": {}
            }
        },
        "required": ["target_url"]
    },
    "WebhookSubscriptionResponse": {
        "$schema": JSON_SCHEMA_DIALECT_2020_12,
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "subscription": {
                "type": "object",
                "properties": {
                    "subscription_id": {"type": "string"},
                    "target_url": {"type": "string"},
                    "subscribed_events": {"type": "array", "items": {"type": "string"}},
                    "is_active": {"type": "boolean"},
                    "created_at": {"type": "string"}
                },
                "required": ["subscription_id", "target_url", "subscribed_events", "is_active"]
            }
        },
        "required": ["success", "subscription"]
    },
    "WebhookDispatchRequest": {
        "$schema": JSON_SCHEMA_DIALECT_2020_12,
        "type": "object",
        "properties": {
            "event_type": {"type": "string", "minLength": 1},
            "payload": {"type": "object"},
            "target_url": {"type": ["string", "null"], "format": "uri"},
            "secret_key": {"type": ["string", "null"]}
        },
        "required": ["event_type", "payload"]
    },
    "WebhookDispatchResponse": {
        "$schema": JSON_SCHEMA_DIALECT_2020_12,
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "delivery_id": {"type": "string"},
            "status_code": {"type": ["integer", "null"]},
            "attempts": {"type": "integer"},
            "duration_ms": {"type": "number"},
            "error": {"type": ["string", "null"]}
        },
        "required": ["success", "delivery_id"]
    },
    "WebhookVerifyRequest": {
        "$schema": JSON_SCHEMA_DIALECT_2020_12,
        "type": "object",
        "properties": {
            "payload": {"type": "object"},
            "secret_key": {"type": "string"},
            "signature": {"type": "string"},
            "timestamp": {"type": ["string", "null"]},
            "tolerance_seconds": {"type": "integer", "default": 300}
        },
        "required": ["payload", "secret_key", "signature"]
    },
    "MCPToolInvokeRequest": {
        "$schema": JSON_SCHEMA_DIALECT_2020_12,
        "type": "object",
        "properties": {
            "tool_name": {"type": "string", "minLength": 1},
            "parameters": {"type": "object", "default": {}},
            "broadcast_webhook": {"type": "boolean", "default": True}
        },
        "required": ["tool_name"]
    },
    "MCPToolInvokeResponse": {
        "$schema": JSON_SCHEMA_DIALECT_2020_12,
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "tool_name": {"type": "string"},
            "result": {"type": "object"},
            "webhook_dispatched": {"type": "boolean"}
        },
        "required": ["success", "tool_name", "result"]
    }
}

# ---------------------------------------------------------------------------
# Definisi Webhooks OpenAPI 3.1.0 Tingkat Atas (Top-Level Webhooks Map)
# ---------------------------------------------------------------------------

OPENAPI_310_WEBHOOKS: Dict[str, Any] = {
    "BETTAFISH_EXECUTIVE_REPORT_GENERATED": {
        "post": {
            "summary": "Dipancarkan saat Laporan Eksekutif C-Level BettaFish selesai di-generate",
            "description": "Payload membawa ringkasan eksekutif SWOT, skor sentimen polar, dan direktif strategis.",
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "$schema": JSON_SCHEMA_DIALECT_2020_12,
                            "type": "object",
                            "properties": {
                                "event_id": {"type": "string"},
                                "event_type": {"type": "string", "const": "BETTAFISH_EXECUTIVE_REPORT_GENERATED"},
                                "timestamp": {"type": "string"},
                                "payload": {"$ref": "#/components/schemas/BettaFishExecutiveReportResponse"}
                            },
                            "required": ["event_id", "event_type", "payload"]
                        }
                    }
                }
            },
            "responses": {
                "200": {"description": "Webhook diterima dengan sukses oleh subscriber"}
            }
        }
    },
    "BETTAFISH_CRITICAL_RISK_ALERT": {
        "post": {
            "summary": "Dipancarkan saat skor risiko polar korporat mencapai level HIGH atau CRITICAL",
            "description": "Memicu protokol peringatan dini dan mitigasi eskalasi krisis pada downstream.",
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "$schema": JSON_SCHEMA_DIALECT_2020_12,
                            "type": "object",
                            "properties": {
                                "event_id": {"type": "string"},
                                "event_type": {"type": "string", "const": "BETTAFISH_CRITICAL_RISK_ALERT"},
                                "timestamp": {"type": "string"},
                                "payload": {"$ref": "#/components/schemas/BettaFishRiskAssessmentResponse"}
                            },
                            "required": ["event_id", "event_type", "payload"]
                        }
                    }
                }
            },
            "responses": {
                "200": {"description": "Peringatan risiko diterima"}
            }
        }
    },
    "MCP_TOOL_INVOKED": {
        "post": {
            "summary": "Dipancarkan saat perkakas FastMCP dieksekusi melalui REST atau protokol MCP",
            "description": "Membawa jejak audit nama perkakas, parameter, dan status eksekusi.",
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "$schema": JSON_SCHEMA_DIALECT_2020_12,
                            "type": "object",
                            "properties": {
                                "event_id": {"type": "string"},
                                "event_type": {"type": "string", "const": "MCP_TOOL_INVOKED"},
                                "payload": {"$ref": "#/components/schemas/MCPToolInvokeResponse"}
                            },
                            "required": ["event_id", "event_type", "payload"]
                        }
                    }
                }
            },
            "responses": {
                "200": {"description": "Event eksekusi MCP tercatat"}
            }
        }
    },
    "MCP_SIMULATION_STATE_CHANGED": {
        "post": {
            "summary": "Dipancarkan saat kondisi simulasi OASIS / BSP berubah via MCP",
            "description": "Memberikan pembaruan status transisi simulasi (running, paused, completed).",
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "$schema": JSON_SCHEMA_DIALECT_2020_12,
                            "type": "object",
                            "properties": {
                                "event_id": {"type": "string"},
                                "event_type": {"type": "string", "const": "MCP_SIMULATION_STATE_CHANGED"},
                                "payload": {"type": "object"}
                            },
                            "required": ["event_id", "event_type", "payload"]
                        }
                    }
                }
            },
            "responses": {
                "200": {"description": "Event perubahan status diterima"}
            }
        }
    },
    "SIMULATION_ROUND_COMPLETED": {
        "post": {
            "summary": "Dipancarkan saat satu ronde simulasi swarm BSP selesai diproses",
            "description": "Membawa ringkasan metrik ronde, konsensus agen, dan status barrier sinkronisasi.",
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "$schema": JSON_SCHEMA_DIALECT_2020_12,
                            "type": "object",
                            "properties": {
                                "event_id": {"type": "string"},
                                "event_type": {"type": "string", "const": "SIMULATION_ROUND_COMPLETED"},
                                "payload": {"type": "object"}
                            },
                            "required": ["event_id", "event_type", "payload"]
                        }
                    }
                }
            },
            "responses": {
                "200": {"description": "Ringkasan ronde diterima"}
            }
        }
    },
    "SIMULATION_COMPLETED": {
        "post": {
            "summary": "Dipancarkan ketika seluruh siklus simulasi multi-platform selesai dieksekusi",
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "$schema": JSON_SCHEMA_DIALECT_2020_12,
                            "type": "object",
                            "properties": {
                                "event_id": {"type": "string"},
                                "event_type": {"type": "string", "const": "SIMULATION_COMPLETED"},
                                "payload": {"type": "object"}
                            },
                            "required": ["event_id", "event_type", "payload"]
                        }
                    }
                }
            },
            "responses": {
                "200": {"description": "Siklus selesai dikonfirmasi"}
            }
        }
    },
    "SYSTEM_ALERT": {
        "post": {
            "summary": "Peringatan anomali sistem runtime, watchdog checkpoint, atau failover",
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "$schema": JSON_SCHEMA_DIALECT_2020_12,
                            "type": "object",
                            "properties": {
                                "event_id": {"type": "string"},
                                "event_type": {"type": "string", "const": "SYSTEM_ALERT"},
                                "payload": {"type": "object"}
                            },
                            "required": ["event_id", "event_type", "payload"]
                        }
                    }
                }
            },
            "responses": {
                "200": {"description": "Alert sistem diterima"}
            }
        }
    }
}

# Alias huruf kecil untuk fleksibilitas konsumsi OpenAPI 3.1.0 tooling
for _wh_k, _wh_v in list(OPENAPI_310_WEBHOOKS.items()):
    OPENAPI_310_WEBHOOKS[_wh_k.lower()] = _wh_v

# ---------------------------------------------------------------------------
# Spesifikasi Lengkap OpenAPI 3.1.0
# ---------------------------------------------------------------------------

OPENAPI_310_SPEC: Dict[str, Any] = {
    "openapi": "3.1.0",
    "jsonSchemaDialect": JSON_SCHEMA_DIALECT_2020_12,
    "info": {
        "title": "MiroFish Enterprise RESTful API",
        "version": "3.2.0",
        "description": (
            "Enterprise Multi-Agent Social Simulation Platform RESTful API conforming to "
            "OpenAPI 3.1.0 and JSON Schema Draft 2020-12. Features 6 engineering divisions, "
            "20 subagents, ReACT Strategic Report engine, BettaFish sentiment & risk analytics, "
            "FastMCP canonical tool integration, and distributed HMAC-SHA256 webhooks with DLQ."
        ),
        "contact": {
            "name": "MiroFish Enterprise Core Engineering",
            "url": "https://github.com/666ghj/MiroFish"
        },
        "license": {
            "name": "Apache-2.0",
            "url": "https://www.apache.org/licenses/LICENSE-2.0.html"
        }
    },
    "servers": [
        {"url": "http://127.0.0.1:8000", "description": "Local Development Server"},
        {"url": "http://localhost:8000", "description": "Localhost Mirror"}
    ],
    "tags": [
        {"name": "System & Health", "description": "Status kesehatan peladen dan diagnosis"},
        {"name": "BettaFish Analytics", "description": "Analisis Sentimen Polar & Penilaian Risiko Korporat C-Level"},
        {"name": "Webhooks Engine", "description": "Dispatcher Webhook Terdistribusi HMAC-SHA256, Langganan & DLQ"},
        {"name": "FastMCP REST Proxy", "description": "Proxy RESTful ke 11 Perkakas Kanonikal FastMCP"},
        {"name": "Enterprise Swarm", "description": "BSP Swarm Runner, RecSys 7 Platform, dan ReACT Strategic Report"},
        {"name": "Memory & Foundations", "description": "Graphiti Knowledge Graph, Zep Adapter, dan CaMeL Prompt Shield"}
    ],
    "paths": {
        "/health": {
            "get": {
                "tags": ["System & Health"],
                "summary": "Pemeriksaan kesehatan sistem MiroFish",
                "responses": {
                    "200": {
                        "description": "Sistem beroperasi normal",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/HealthResponse"}
                            }
                        }
                    }
                }
            }
        },
        "/api/enterprise/status": {
            "get": {
                "tags": ["System & Health"],
                "summary": "Status lengkap divisi dan modul enterprise MiroFish",
                "responses": {
                    "200": {
                        "description": "Metadata modul enterprise",
                        "content": {
                            "application/json": {
                                "schema": {"type": "object"}
                            }
                        }
                    }
                }
            }
        },
        "/api/enterprise/bettafish/sentiment": {
            "post": {
                "tags": ["BettaFish Analytics"],
                "summary": "Analisis sentimen polar teks dengan vektor emosi 5-dimensi",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/BettaFishSentimentRequest"}
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Hasil analisis sentimen polar",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/BettaFishSentimentResponse"}
                            }
                        }
                    },
                    "422": {
                        "description": "Payload tidak sesuai skema JSON Schema 2020-12",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    }
                }
            }
        },
        "/api/enterprise/bettafish/executive-report": {
            "post": {
                "tags": ["BettaFish Analytics"],
                "summary": "Menghasilkan laporan eksekutif C-Level BettaFish & memancarkan webhook",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/BettaFishExecutiveReportRequest"}
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Laporan eksekutif berhasil di-generate",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/BettaFishExecutiveReportResponse"}
                            }
                        }
                    },
                    "422": {
                        "description": "Payload tidak valid",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    }
                }
            }
        },
        "/api/enterprise/bettafish/risk-assessment": {
            "post": {
                "tags": ["BettaFish Analytics"],
                "summary": "Penilaian risiko korporat polar dan peringatan dini krisis",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/BettaFishRiskAssessmentRequest"}
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Hasil evaluasi risiko korporat",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/BettaFishRiskAssessmentResponse"}
                            }
                        }
                    },
                    "422": {
                        "description": "Validasi JSON Schema gagal",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    }
                }
            }
        },
        "/api/enterprise/bettafish/downstream-recommendations": {
            "get": {
                "tags": ["BettaFish Analytics"],
                "summary": "Ambil target downstream rekomendasi Agent 16 ke Agent 17-20",
                "responses": {
                    "200": {
                        "description": "Rekomendasi downstream aktif",
                        "content": {
                            "application/json": {
                                "schema": {"type": "object"}
                            }
                        }
                    }
                }
            }
        },
        "/api/enterprise/webhooks/subscriptions": {
            "post": {
                "tags": ["Webhooks Engine"],
                "summary": "Daftarkan langganan webhook baru",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/WebhookSubscriptionRequest"}
                        }
                    }
                },
                "responses": {
                    "201": {
                        "description": "Langganan webhook berhasil dibuat",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/WebhookSubscriptionResponse"}
                            }
                        }
                    },
                    "422": {
                        "description": "Format URL atau payload salah",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    }
                }
            },
            "get": {
                "tags": ["Webhooks Engine"],
                "summary": "Daftar seluruh langganan webhook aktif",
                "responses": {
                    "200": {
                        "description": "List langganan webhook",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "success": {"type": "boolean"},
                                        "subscriptions": {
                                            "type": "array",
                                            "items": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "/api/enterprise/webhooks/subscriptions/{subscription_id}": {
            "get": {
                "tags": ["Webhooks Engine"],
                "summary": "Ambil detail langganan webhook berdasarkan ID",
                "parameters": [
                    {
                        "name": "subscription_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"}
                    }
                ],
                "responses": {
                    "200": {"description": "Detail langganan"},
                    "404": {"description": "Langganan tidak ditemukan"}
                }
            },
            "delete": {
                "tags": ["Webhooks Engine"],
                "summary": "Hapus pendaftaran langganan webhook",
                "parameters": [
                    {
                        "name": "subscription_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"}
                    }
                ],
                "responses": {
                    "200": {"description": "Langganan berhasil dihapus"},
                    "404": {"description": "Langganan tidak ditemukan"}
                }
            }
        },
        "/api/enterprise/webhooks/dispatch": {
            "post": {
                "tags": ["Webhooks Engine"],
                "summary": "Kirim event webhook langsung ke target URL atau broadcast",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/WebhookDispatchRequest"}
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Pengiriman webhook berhasil atau queued",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/WebhookDispatchResponse"}
                            }
                        }
                    },
                    "422": {"description": "Payload tidak sesuai skema"}
                }
            }
        },
        "/api/enterprise/webhooks/dlq": {
            "get": {
                "tags": ["Webhooks Engine"],
                "summary": "Inspeksi daftar Dead-Letter Queue (DLQ) event yang gagal terkirim",
                "parameters": [
                    {"name": "limit", "in": "query", "schema": {"type": "integer", "default": 50}},
                    {"name": "offset", "in": "query", "schema": {"type": "integer", "default": 0}},
                    {"name": "event_type", "in": "query", "schema": {"type": "string"}}
                ],
                "responses": {
                    "200": {
                        "description": "Daftar event di DLQ",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "success": {"type": "boolean"},
                                        "count": {"type": "integer"},
                                        "dlq": {"type": "array", "items": {"type": "object"}}
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "delete": {
                "tags": ["Webhooks Engine"],
                "summary": "Bersihkan seluruh isi Dead-Letter Queue (DLQ)",
                "responses": {
                    "200": {"description": "DLQ berhasil dibersihkan"}
                }
            }
        },
        "/api/enterprise/webhooks/dlq/replay": {
            "post": {
                "tags": ["Webhooks Engine"],
                "summary": "Kirim ulang (re-drive) event dari Dead-Letter Queue",
                "requestBody": {
                    "required": False,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "event_id": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {"description": "Hasil replay pengiriman DLQ"}
                }
            }
        },
        "/api/enterprise/webhooks/verify": {
            "post": {
                "tags": ["Webhooks Engine"],
                "summary": "Verifikasi tanda tangan HMAC-SHA256 & proteksi anti-replay",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/WebhookVerifyRequest"}
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Hasil verifikasi signature",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "is_valid": {"type": "boolean"},
                                        "error": {"type": ["string", "null"]}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "/api/enterprise/webhooks/stats": {
            "get": {
                "tags": ["Webhooks Engine"],
                "summary": "Ambil statistik metrik performa webhook & latensi P95",
                "responses": {
                    "200": {
                        "description": "Statistik performa dispatcher",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "total_dispatched": {"type": "integer"},
                                        "total_delivered": {"type": "integer"},
                                        "total_failed": {"type": "integer"},
                                        "dlq_count": {"type": "integer"},
                                        "p95_latency_ms": {"type": "number"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "/api/mcp/tools": {
            "get": {
                "tags": ["FastMCP REST Proxy"],
                "summary": "Daftar 11 perkakas kanonikal FastMCP + perkakas BettaFish",
                "responses": {
                    "200": {
                        "description": "Katalog metadata perkakas kanonikal MCP",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "tools": {"type": "array", "items": {"type": "object"}},
                                        "count": {"type": "integer"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "/api/mcp/health": {
            "get": {
                "tags": ["FastMCP REST Proxy"],
                "summary": "Pemeriksaan kesehatan peladen FastMCP",
                "responses": {
                    "200": {"description": "FastMCP operasional"}
                }
            }
        },
        "/api/mcp/invoke": {
            "post": {
                "tags": ["FastMCP REST Proxy"],
                "summary": "Eksekusi perkakas MCP via HTTP REST dan pancarkan webhook MCP_TOOL_INVOKED",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/MCPToolInvokeRequest"}
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Hasil eksekusi perkakas MCP",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/MCPToolInvokeResponse"}
                            }
                        }
                    },
                    "422": {"description": "Format input perkakas tidak valid"}
                }
            }
        },
        "/api/openapi.json": {
            "get": {
                "tags": ["System & Health"],
                "summary": "Dokumen spesifikasi OpenAPI 3.1.0 lengkap format JSON",
                "responses": {
                    "200": {"description": "OpenAPI 3.1.0 JSON Specification"}
                }
            }
        },
        "/api/openapi.yaml": {
            "get": {
                "tags": ["System & Health"],
                "summary": "Dokumen spesifikasi OpenAPI 3.1.0 lengkap format YAML",
                "responses": {
                    "200": {"description": "OpenAPI 3.1.0 YAML Specification"}
                }
            }
        },
        "/api/docs": {
            "get": {
                "tags": ["System & Health"],
                "summary": "Dokumentasi interaktif OpenAPI 3.1.0 (Swagger UI)",
                "responses": {
                    "200": {"description": "HTML Interactive API Docs"}
                }
            }
        }
    },
    "webhooks": OPENAPI_310_WEBHOOKS,
    "components": {
        "schemas": COMPONENT_SCHEMAS,
        "securitySchemes": {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "Standard OAuth2 / JWT Bearer token authentication"
            },
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
                "description": "Enterprise API Key"
            },
            "HmacSignature": {
                "type": "apiKey",
                "in": "header",
                "name": "X-Mirofish-Signature",
                "description": "HMAC-SHA256 signature for webhook transmission integrity"
            }
        }
    }
}

# ---------------------------------------------------------------------------
# Validasi JSON Schema 2020-12
# ---------------------------------------------------------------------------

def validate_json_schema_2020_12(
    instance: Any,
    schema: Dict[str, Any]
) -> Tuple[bool, Optional[List[Dict[str, Any]]]]:
    """
    Validasi data menggunakan dialek resmi JSON Schema Draft 2020-12.
    Returns: (is_valid, errors_list)
    """
    try:
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
        errors = list(validator.iter_errors(instance))
        if not errors:
            return True, None
        
        formatted_errors = [
            {
                "path": list(err.path),
                "message": err.message,
                "validator": err.validator,
                "schema_path": list(err.schema_path)
            }
            for err in errors
        ]
        return False, formatted_errors
    except Exception as e:
        return False, [{"path": [], "message": str(e), "validator": "schema_error"}]


def validate_request_schema(schema_or_name: Any):
    """
    Dekorator Flask untuk memvalidasi request body dengan JSON Schema 2020-12.
    Jika tidak valid, otomatis mengembalikan respons HTTP 422 Unprocessable Entity.
    """
    def decorator(fn: Callable):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            schema = schema_or_name
            if isinstance(schema_or_name, str):
                schema = COMPONENT_SCHEMAS.get(schema_or_name)
                if not schema:
                    return jsonify({
                        "success": False,
                        "error": {
                            "code": "SCHEMA_NOT_FOUND",
                            "message": f"Schema '{schema_or_name}' not defined in COMPONENT_SCHEMAS"
                        }
                    }), 500

            data = request.get_json(silent=True)
            if data is None:
                data = {}

            is_valid, errors = validate_json_schema_2020_12(data, schema)
            if not is_valid:
                return jsonify({
                    "success": False,
                    "error": {
                        "code": "UNPROCESSABLE_ENTITY",
                        "message": "Payload does not conform to JSON Schema Draft 2020-12 specification",
                        "details": errors
                    }
                }), 422

            return fn(*args, **kwargs)
        return wrapper
    return decorator


def get_openapi_spec(format_type: str = "dict") -> Any:
    """
    Mengambil dokumen spesifikasi OpenAPI 3.1.0 dalam format dict, json, atau yaml.
    """
    if format_type.lower() == "json":
        return json.dumps(OPENAPI_310_SPEC, indent=2)
    elif format_type.lower() in ("yaml", "yml"):
        return yaml.dump(OPENAPI_310_SPEC, sort_keys=False, allow_unicode=True)
    return OPENAPI_310_SPEC


def get_swagger_ui_html(spec_url: str = "/api/openapi.json", title: str = "MiroFish Enterprise OpenAPI 3.1.0 Docs") -> str:
    """
    Menghasilkan HTML viewer mandiri untuk dokumentasi interaktif Swagger UI.
    """
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{title}</title>
  <link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.11.0/swagger-ui.css" />
  <style>
    html {{ box-sizing: border-box; overflow: -moz-scrollbars-vertical; overflow-y: scroll; }}
    *, *:before, *:after {{ box-sizing: inherit; }}
    body {{ margin: 0; background: #fafafa; font-family: sans-serif; }}
    .topbar {{ display: none; }}
  </style>
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.11.0/swagger-ui-bundle.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.11.0/swagger-ui-standalone-preset.js"></script>
  <script>
    window.onload = function() {{
      window.ui = SwaggerUIBundle({{
        url: "{spec_url}",
        dom_id: '#swagger-ui',
        deepLinking: true,
        presets: [
          SwaggerUIBundle.presets.apis,
          SwaggerUIStandalonePreset
        ],
        layout: "BaseLayout"
      }});
    }};
  </script>
</body>
</html>"""


__all__ = [
    "JSON_SCHEMA_DIALECT_2020_12",
    "OPENAPI_310_SPEC",
    "COMPONENT_SCHEMAS",
    "SIMULATION_PROJECT_SCHEMA",
    "WEBHOOK_SUBSCRIPTION_SCHEMA",
    "validate_json_schema_2020_12",
    "validate_request_schema",
    "get_openapi_spec",
    "get_swagger_ui_html",
]
