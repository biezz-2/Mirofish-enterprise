"""
MiroFish Enterprise Lead Orchestrator & Swarm Dispatcher (Agent 01: Divisi A)
State Machine Alur 6-Langkah & Swarm Coordinator:
- Step 0: Web Research & Security (Divisi A: Agent 01-04)
- Step 1: Knowledge Engineering & GraphRAG (Divisi B: Agent 05-07)
- Step 2: Psychometrics & Agent Behaviors (Divisi C: Agent 08-10)
- Step 3: RecSys Funnel & Viral Dynamics (Divisi D: Agent 11-14)
- Step 4: Predictive Analytics & Reporting (Divisi E: Agent 15-16)
- Step 5: Universal Extensibility & Dashboard (Divisi F: Agent 17-20)
- Watchdog Heartbeat: Memantau 20 subagent, mendeteksi agen senyap > 45 menit,
  dan memancarkan event ke Discord Reporter.
"""

import os
import time
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from .discord_reporter import get_reporter

logger = logging.getLogger('mirofish.orchestrator')

STEP_DEFINITIONS = [
    {"step": 0, "name": "Web Research & CaMeL Shield", "division": "A", "agents": ["A01", "A02", "A03", "A04"]},
    {"step": 1, "name": "GraphRAG & Zep NLI Barrier", "division": "B", "agents": ["A05", "A06", "A07"]},
    {"step": 2, "name": "Psychometrics & Humanoid ODE", "division": "C", "agents": ["A08", "A09", "A10"]},
    {"step": 3, "name": "RecSys Funnel & BSP Simulation", "division": "D", "agents": ["A11", "A12", "A13", "A14"]},
    {"step": 4, "name": "ReACT ReportAgent & BettaFish", "division": "E", "agents": ["A15", "A16"]},
    {"step": 5, "name": "FastMCP & Enterprise Dashboard", "division": "F", "agents": ["A17", "A18", "A19", "A20"]},
]

class AgentHeartbeat(BaseModel):
    agent_id: str
    division: str
    last_seen: float  # Unix timestamp
    status: str = "ACTIVE"
    current_task: str = "idle"

class OrchestratorStateMachine:
    """Lead Orchestrator managing 6-step lifecycle and 20-agent watchdog."""

    def __init__(self, board_id: str = "project-mirofish-enterprise-notion"):
        self.board_id = board_id
        self.current_step = 0
        self.heartbeats: Dict[str, AgentHeartbeat] = {}
        self.reporter = get_reporter()
        self._init_agents()

    def _init_agents(self):
        for s in STEP_DEFINITIONS:
            div = s["division"]
            for a_id in s["agents"]:
                self.heartbeats[a_id] = AgentHeartbeat(
                    agent_id=a_id,
                    division=div,
                    last_seen=time.time(),
                    status="ACTIVE",
                    current_task="initialized"
                )

    def record_heartbeat(self, agent_id: str, task: str = "running") -> None:
        if agent_id in self.heartbeats:
            self.heartbeats[agent_id].last_seen = time.time()
            self.heartbeats[agent_id].current_task = task
            self.heartbeats[agent_id].status = "ACTIVE"

    def scan_watchdog(self, timeout_seconds: float = 2700.0) -> List[str]:
        """
        Watchdog: Memeriksa apakah ada agen yang senyap lebih dari 45 menit (2700 detik).
        Jika ada, trigger WATCHDOG_ALERT.
        """
        now = time.time()
        dead_agents = []

        for a_id, hb in self.heartbeats.items():
            silence_duration = now - hb.last_seen
            if silence_duration > timeout_seconds:
                dead_agents.append(a_id)
                hb.status = "DEAD_OR_SILENT"
                logger.error(f"Watchdog ALERT: Agen {a_id} tidak aktif selama {silence_duration:.1f} detik!")
                self.reporter.emit_event(
                    event_type="WATCHDOG_ALERT",
                    agent_id=a_id,
                    division=hb.division,
                    status="CRITICAL_TIMEOUT",
                    title_suffix=f"Agen senyap > {int(timeout_seconds/60)} menit",
                    next_action="Perlu intervensi human on-call / trigger restart"
                )
        return dead_agents

    def advance_step(self) -> Dict[str, Any]:
        """Transisi deterministik alur langkah 0 s.d. 5."""
        if self.current_step < 5:
            self.current_step += 1
            step_meta = STEP_DEFINITIONS[self.current_step]
            self.reporter.emit_event(
                event_type="PHASE_GATE",
                agent_id="A01-Orchestrator",
                division=step_meta["division"],
                status="IN_PROGRESS",
                title_suffix=f"Transisi ke Step {self.current_step}: {step_meta['name']}",
                next_action=f"Aktivasi subagent divisi {step_meta['division']}"
            )
            return {"success": True, "current_step": self.current_step, "step_info": step_meta}
        return {"success": False, "message": "Seluruh alur 6 langkah telah selesai (Step 5 reached)."}
