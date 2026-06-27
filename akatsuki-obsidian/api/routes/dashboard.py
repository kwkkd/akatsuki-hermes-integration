import json
import logging
from pathlib import Path
from typing import Optional

try:
    from fastapi import APIRouter, Depends, HTTPException, Query
    from pydantic import BaseModel
except ImportError:
    APIRouter = None

from hermes_bridge.bridge.agent_bridge import AgentBridge
from hermes_bridge.notifications.manager import get_manager as get_notification_manager

if APIRouter is None:
    router = None
else:
    router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

logger = logging.getLogger("akatsuki.api.dashboard")


if router is not None:
    class DashboardWidget(BaseModel):
        id: str = ""
        type: str = "metric_card"
        title: str = ""
        config: dict = {}
        position: int = 0

    class DashboardLayout(BaseModel):
        widgets: list[DashboardWidget] = []


    @router.get("/stats")
    async def get_dashboard_stats(bridge: AgentBridge = None):
        if bridge is None:
            return {"error": "bridge not available"}
        stats = {
            "notes_total": 0,
            "tools_total": 0,
            "operations_active": 0,
            "peers_connected": 0,
        }
        try:
            result = bridge.vault.list_notes() if bridge.vault else []
            stats["notes_total"] = len(result) if isinstance(result, list) else 0
        except Exception:
            pass
        try:
            from hermes_bridge.sync.server import SyncServer
            for server in getattr(bridge, "_sync_servers", []):
                stats["peers_connected"] += len(server._peers)
        except Exception:
            pass
        try:
            from tools.registry import registry
            stats["tools_total"] = len(registry.list_tools())
        except Exception:
            pass
        return stats


    @router.get("/layout")
    async def get_layout():
        layout_path = Path("data") / "dashboard_layout.json"
        if layout_path.exists():
            try:
                return json.loads(layout_path.read_text())
            except Exception:
                pass
        return {"widgets": []}


    @router.post("/layout")
    async def save_layout(layout: DashboardLayout):
        layout_path = Path("data") / "dashboard_layout.json"
        layout_path.parent.mkdir(parents=True, exist_ok=True)
        layout_path.write_text(layout.model_dump_json(indent=2))
        return {"saved": True, "widgets": len(layout.widgets)}


    @router.get("/widgets/available")
    async def list_available_widgets():
        return {"widgets": [
            {"id": "metric_card", "name": "Metric Card", "description": "Key metrics display"},
            {"id": "vuln_chart", "name": "Vulnerability Chart", "description": "Severity breakdown"},
            {"id": "topology", "name": "Network Topology", "description": "Target network map"},
            {"id": "operations", "name": "Active Operations", "description": "Running ops list"},
            {"id": "timeline", "name": "Operation Timeline", "description": "Gantt timeline view"},
            {"id": "recent_alerts", "name": "Recent Alerts", "description": "Latest notifications"},
        ]}


    @router.get("/notifications/test")
    async def test_notification(title: str = "AKATSUKI Test",
                                 message: str = "Dashboard integration test"):
        mgr = get_notification_manager()
        result = mgr.broadcast(title, message)
        return result