import json
import tempfile
from pathlib import Path

from tools.akatsuki_widgets import (
    configure, render_widget, list_widgets, delete_widget,
    _widgets_store, _STORE_PATH, _save, _load,
)


class TestWidgets:
    def setup_method(self):
        _widgets_store.clear()

    def test_configure_metric_card(self):
        result = configure("cpu-metric", "metric_card", json.dumps({"label": "CPU", "value": "42%"}))
        assert result["configured"] is True
        assert result["widget_id"] == "cpu-metric"

    def test_configure_vuln_chart(self):
        cfg = {"counts": {"critical": 5, "high": 10, "medium": 20, "low": 15}}
        result = configure("vulns", "vuln_chart", json.dumps(cfg))
        assert result["configured"] is True

    def test_list_widgets(self):
        configure("w1", "metric_card", "{}")
        configure("w2", "topology", "{}")
        result = list_widgets()
        assert result["count"] == 2

    def test_delete_widget(self):
        configure("delete-me", "metric_card", "{}")
        result = delete_widget("delete-me")
        assert result["deleted"] is True
        assert "delete-me" not in _widgets_store

    def test_delete_nonexistent(self):
        result = delete_widget("does-not-exist")
        assert "error" in result

    def test_render_metric_card(self):
        configure("test", "metric_card", json.dumps({"label": "CPU", "value": "75%"}))
        html = render_widget("test")
        assert "metric-card" in html
        assert "75%" in html
        assert "CPU" in html

    def test_render_vuln_chart(self):
        configure("v", "vuln_chart", json.dumps({"counts": {"critical": 3, "high": 5, "medium": 7, "low": 9}}))
        html = render_widget("v")
        assert "vuln-chart" in html
        assert "CRITICAL" in html

    def test_render_topology(self):
        cfg = {"nodes": [{"id": "host1", "label": "Gateway", "type": "host"}, {"id": "net1", "label": "10.0.0.0/24", "type": "network"}]}
        configure("topo", "topology", json.dumps(cfg))
        html = render_widget("topo")
        assert "topology" in html
        assert "Gateway" in html

    def test_render_operations(self):
        cfg = {"operations": [{"id": "op-1", "status": "running", "phase": "Recon"}]}
        configure("ops", "operations", json.dumps(cfg))
        html = render_widget("ops")
        assert "op-running" in html

    def test_render_unknown_type(self):
        configure("bad", "nonexistent", "{}")
        html = render_widget("bad")
        assert "Unknown widget" in html

    def test_render_not_found(self):
        html = render_widget("ghost")
        assert "Widget not found" in html
