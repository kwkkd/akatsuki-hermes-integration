import json
import logging
from pathlib import Path
from typing import Optional

from tools.registry import registry, tool_error, tool_result

logger = logging.getLogger(__name__)


AKATSUKI_WIDGETS_SCHEMA = {
    "name": "akatsuki_widgets",
    "description": "Dashboard Widget Engine — create, configure, and render custom widgets (MetricCard, VulnChart, Topology view).",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["configure", "render", "list", "delete"],
                "description": "configure: save widget config; render: get widget HTML; list: show widgets; delete: remove",
            },
            "widget_id": {
                "type": "string",
                "description": "Unique widget identifier",
            },
            "widget_type": {
                "type": "string",
                "enum": ["metric_card", "vuln_chart", "topology", "operations", "timeline", "recent_alerts"],
                "description": "Widget type",
            },
            "config_json": {
                "type": "string",
                "description": "JSON configuration object for the widget",
            },
        },
        "required": ["action"],
    },
}

_widgets_store: dict[str, dict] = {}
_STORE_PATH = Path(__file__).resolve().parent.parent / "data" / "widgets.json"


def _load():
    global _widgets_store
    if _STORE_PATH.exists():
        try:
            _widgets_store = json.loads(_STORE_PATH.read_text())
        except Exception:
            _widgets_store = {}


def _save():
    _STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _STORE_PATH.write_text(json.dumps(_widgets_store, indent=2))


_load()


def configure(widget_id: str, widget_type: str, config_json: str = "{}") -> dict:
    try:
        config = json.loads(config_json) if isinstance(config_json, str) else config_json
    except json.JSONDecodeError:
        return {"error": "Invalid config JSON"}
    _widgets_store[widget_id] = {
        "id": widget_id,
        "type": widget_type,
        "config": config,
    }
    _save()
    return {"widget_id": widget_id, "type": widget_type, "configured": True}


def render_widget(widget_id: str) -> str:
    widget = _widgets_store.get(widget_id)
    if not widget:
        return "<div class='widget-error'>Widget not found</div>"
    t = widget["type"]
    cfg = widget.get("config", {})
    if t == "metric_card":
        return _render_metric_card(cfg)
    if t == "vuln_chart":
        return _render_vuln_chart(cfg)
    if t == "topology":
        return _render_topology(cfg)
    if t == "operations":
        return _render_operations(cfg)
    if t == "timeline":
        return _render_timeline(cfg)
    if t == "recent_alerts":
        return _render_recent_alerts(cfg)
    return f"<div>Unknown widget type: {t}</div>"


def _render_metric_card(cfg: dict) -> str:
    label = cfg.get("label", "Metric")
    value = cfg.get("value", "0")
    icon = cfg.get("icon", "chart")
    color = cfg.get("color", "#4f46e5")
    return (
        f'<div class="widget metric-card" style="border-left:4px solid {color}">'
        f'  <div class="metric-icon">{icon}</div>'
        f'  <div class="metric-value">{value}</div>'
        f'  <div class="metric-label">{label}</div>'
        f'</div>'
    )


def _render_vuln_chart(cfg: dict) -> str:
    counts = cfg.get("counts", {"critical": 0, "high": 0, "medium": 0, "low": 0})
    colors = {"critical": "#ef4444", "high": "#f97316", "medium": "#eab308", "low": "#22c55e"}
    bars = "".join(
        f'<div class="vuln-bar-row">'
        f'  <span class="vuln-label">{sev.upper()}</span>'
        f'  <div class="vuln-bar-bg">'
        f'    <div class="vuln-bar" style="width:{cnt * 20}%;background:{colors.get(sev, "#888")}"></div>'
        f'  </div>'
        f'  <span class="vuln-count">{cnt}</span>'
        f'</div>'
        for sev, cnt in counts.items()
    )
    return f'<div class="widget vuln-chart"><h4>Vulnerabilities</h4>{bars}</div>'


def _render_topology(cfg: dict) -> str:
    nodes = cfg.get("nodes", [])
    edges = cfg.get("edges", [])
    if not nodes:
        return '<div class="widget topology"><h4>Network Topology</h4><p>No nodes configured</p></div>'
    items = "".join(
        f'<div class="topo-node" data-id="{n.get("id", "")}">'
        f'  <span class="topo-icon">{"🖥" if n.get("type") == "host" else "🌐"}</span>'
        f'  <span class="topo-label">{n.get("label", n.get("id", ""))}</span>'
        f'</div>'
        for n in nodes
    )
    return f'<div class="widget topology"><h4>Network Topology</h4><div class="topo-nodes">{items}</div></div>'


def _render_operations(cfg: dict) -> str:
    ops = cfg.get("operations", [])
    if not ops:
        return '<div class="widget operations"><h4>Active Operations</h4><p>None running</p></div>'
    items = "".join(
        f'<div class="op-item">'
        f'  <span class="op-status op-{o.get("status", "pending")}"></span>'
        f'  <span class="op-id">{o.get("id", "")}</span>'
        f'  <span class="op-phase">{o.get("phase", "")}</span>'
        f'</div>'
        for o in ops
    )
    return f'<div class="widget operations"><h4>Active Operations</h4>{items}</div>'


def _render_timeline(cfg: dict) -> str:
    events = cfg.get("events", [])
    if not events:
        return '<div class="widget timeline"><h4>Timeline</h4><p>No events</p></div>'
    items = "".join(
        f'<div class="tl-event">'
        f'  <span class="tl-time">{e.get("time", "")}</span>'
        f'  <span class="tl-desc">{e.get("description", "")}</span>'
        f'</div>'
        for e in events[-10:]
    )
    return f'<div class="widget timeline"><h4>Recent Events</h4>{items}</div>'


def _render_recent_alerts(cfg: dict) -> str:
    alerts = cfg.get("alerts", [])
    if not alerts:
        return '<div class="widget alerts"><h4>Alerts</h4><p>No alerts</p></div>'
    items = "".join(
        f'<div class="alert-item alert-{a.get("severity", "info")}">'
        f'  <span class="alert-title">{a.get("title", "")}</span>'
        f'</div>'
        for a in alerts[-5:]
    )
    return f'<div class="widget alerts"><h4>Recent Alerts</h4>{items}</div>'


def list_widgets() -> dict:
    return {"widgets": list(_widgets_store.values()), "count": len(_widgets_store)}


def delete_widget(widget_id: str) -> dict:
    if widget_id in _widgets_store:
        del _widgets_store[widget_id]
        _save()
        return {"widget_id": widget_id, "deleted": True}
    return {"error": f"Widget not found: {widget_id}"}


def akatsuki_widgets(action: str, widget_id: str = "", widget_type: str = "metric_card",
                      config_json: str = "{}") -> str:
    if action == "configure":
        if not widget_id:
            return tool_error("widget_id is required")
        return tool_result(configure(widget_id, widget_type, config_json))
    if action == "render":
        if not widget_id:
            return tool_error("widget_id is required")
        html = render_widget(widget_id)
        return tool_result({"widget_id": widget_id, "html": html})
    if action == "list":
        return tool_result(list_widgets())
    if action == "delete":
        if not widget_id:
            return tool_error("widget_id is required")
        return tool_result(delete_widget(widget_id))
    return tool_error(f"Unknown action: {action}")


def check_akatsuki_widgets_requirements() -> bool:
    return True


registry.register(
    name="akatsuki_widgets",
    toolset="akatsuki",
    schema=AKATSUKI_WIDGETS_SCHEMA,
    handler=lambda args, **kw: akatsuki_widgets(
        action=args["action"],
        widget_id=args.get("widget_id", ""),
        widget_type=args.get("widget_type", "metric_card"),
        config_json=args.get("config_json", "{}"),
    ),
    check_fn=check_akatsuki_widgets_requirements,
    emoji="📊",
)