import json
import tempfile
from pathlib import Path

from tools.akatsuki_replay import (
    record, list_operations, step_forward, step_backward,
    current, export_operation,
    _replays, _cursors, _STORE_PATH, _load, _save,
)


class TestReplay:
    def setup_method(self):
        _replays.clear()
        _cursors.clear()

    def test_record(self):
        result = record("op-1", "recon", json.dumps({"target": "10.0.0.1", "ports": [80, 443]}))
        assert result["recorded"] is True
        assert result["operation_id"] == "op-1"
        assert result["step"] == 0

    def test_record_multiple_steps(self):
        record("op-1", "recon", '{"step": 1}')
        record("op-1", "weaponize", '{"step": 2}')
        result = record("op-1", "delivery", '{"step": 3}')
        assert result["step"] == 2
        assert len(_replays["op-1"]) == 3

    def test_list_empty(self):
        result = list_operations()
        assert result["count"] == 0

    def test_list_with_ops(self):
        record("op-1", "recon", "{}")
        record("op-2", "exploit", "{}")
        result = list_operations()
        assert result["count"] == 2
        assert "op-1" in result["operations"]
        assert "op-2" in result["operations"]

    def test_step_forward(self):
        record("op-1", "recon", '{"step": "a"}')
        record("op-1", "weaponize", '{"step": "b"}')
        result = step_forward("op-1")
        assert result["step"] == 1
        assert result["current"]["phase"] == "weaponize"
        assert result["progress"] == "2/2"

    def test_step_forward_at_end(self):
        record("op-1", "recon", "{}")
        result = step_forward("op-1")
        assert result["step"] == 0

    def test_step_backward(self):
        record("op-1", "recon", "{}")
        record("op-1", "weaponize", "{}")
        step_forward("op-1")
        result = step_backward("op-1")
        assert result["step"] == 0

    def test_step_backward_at_start(self):
        record("op-1", "recon", "{}")
        result = step_backward("op-1")
        assert result["step"] == 0

    def test_current(self):
        record("op-1", "recon", '{"step": 1}')
        result = current("op-1")
        assert result["step"] == 0
        assert result["current"]["phase"] == "recon"

    def test_current_no_ops(self):
        result = current("empty")
        assert "error" in result

    def test_export_operation(self):
        record("op-1", "recon", '{"target": "x"}')
        record("op-1", "exploit", '{"vuln": "y"}')
        result = export_operation("op-1")
        assert result["total_steps"] == 2
        assert len(result["steps"]) == 2

    def test_export_nonexistent(self):
        result = export_operation("ghost")
        assert "error" in result

    def test_record_invalid_json(self):
        result = record("op-1", "recon", "not valid json")
        assert "error" in result
