import unittest
import tempfile
import json
import sys
from pathlib import Path

# Add akatsuki-obsidian to path for hermes_bridge imports
_obsidian_path = Path(__file__).resolve().parent.parent / "akatsuki-obsidian"
if str(_obsidian_path) not in sys.path:
    sys.path.insert(0, str(_obsidian_path))


class TestSyncManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.vault_path = Path(self.temp_dir.name)
        (self.vault_path / ".obsidian").mkdir(parents=True, exist_ok=True)
        from hermes_bridge.sync.sync_manager import SyncManager
        self.sync = SyncManager(str(self.vault_path))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_init_generates_node_id(self):
        state = self.sync.get_state()
        self.assertIn("node_id", state)
        self.assertEqual(len(state["node_id"]), 12)

    def test_mark_changed(self):
        test_file = self.vault_path / "test.md"
        test_file.write_text("hello", encoding="utf-8")
        self.sync.mark_changed("test.md", "hello")
        state = self.sync.get_state()
        self.assertIn("test.md", state["checksums"])

    def test_get_changed_new_file(self):
        test_file = self.vault_path / "new_note.md"
        test_file.write_text("content", encoding="utf-8")
        changed = self.sync.get_changed()
        self.assertGreaterEqual(len(changed), 1)

    def test_get_changed_no_change(self):
        test_file = self.vault_path / "stable.md"
        test_file.write_text("stable content", encoding="utf-8")
        changed = self.sync.get_changed()
        self.sync.record_sync({rel: cs for rel, cs in changed})
        changed_again = self.sync.get_changed()
        self.assertEqual(len(changed_again), 0)

    def test_record_sync(self):
        self.sync.record_sync({"note1.md": "abc123"})
        state = self.sync.get_state()
        self.assertEqual(state["checksums"]["note1.md"], "abc123")
        self.assertGreater(state["last_sync"], 0)

    def test_create_op(self):
        op = self.sync.create_op("INSERT", "test.md", "hello")
        self.assertEqual(op.op_type, "INSERT")
        self.assertEqual(op.path, "test.md")
        self.assertGreater(op.lamport, 0)

    def test_merge_ops(self):
        op1 = self.sync.create_op("INSERT", "a.md", "content_a")
        remote_ops = [
            {
                "op_id": "remote_node:1",
                "op_type": "INSERT",
                "node_id": "remote_node",
                "seq": 1,
                "lamport": 100,
                "path": "b.md",
                "value": "content_b",
                "deps": [],
            }
        ]
        new_ops = self.sync.merge_ops(remote_ops)
        self.assertEqual(len(new_ops), 1)
        self.assertEqual(new_ops[0].node_id, "remote_node")

    def test_merge_ops_deduplication(self):
        op = self.sync.create_op("UPDATE", "c.md", "data")
        remote_ops = [
            {
                "op_id": op.op_id,
                "op_type": "UPDATE",
                "node_id": op.node_id,
                "seq": op.seq,
                "lamport": op.lamport,
                "path": "c.md",
                "value": "data",
                "deps": [],
            }
        ]
        new_ops = self.sync.merge_ops(remote_ops)
        self.assertEqual(len(new_ops), 0)

    def test_resolve_conflict_local_wins(self):
        from hermes_bridge.sync.sync_manager import CrdtOperation
        local_op = CrdtOperation("local:1", "UPDATE", "node_a", 1, 200, "f.md", "local_val")
        remote_op = CrdtOperation("remote:1", "UPDATE", "node_b", 1, 100, "f.md", "remote_val")
        winner = self.sync.resolve_conflict(local_op, remote_op)
        self.assertEqual(winner.node_id, "node_a")

    def test_resolve_conflict_remote_wins(self):
        from hermes_bridge.sync.sync_manager import CrdtOperation
        local_op = CrdtOperation("local:1", "UPDATE", "node_a", 1, 100, "f.md", "local_val")
        remote_op = CrdtOperation("remote:1", "UPDATE", "node_b", 1, 200, "f.md", "remote_val")
        winner = self.sync.resolve_conflict(local_op, remote_op)
        self.assertEqual(winner.node_id, "node_b")

    def test_resolve_conflict_same_lamport(self):
        from hermes_bridge.sync.sync_manager import CrdtOperation
        local_op = CrdtOperation("local:1", "UPDATE", "node_b", 1, 100, "f.md", "val")
        remote_op = CrdtOperation("remote:1", "UPDATE", "node_a", 1, 100, "f.md", "val")
        winner = self.sync.resolve_conflict(local_op, remote_op)
        self.assertEqual(winner.node_id, "node_b")

    def test_state_persistence(self):
        self.sync.record_sync({"persist.md": "xyz789"})
        from hermes_bridge.sync.sync_manager import SyncManager
        sync2 = SyncManager(str(self.vault_path))
        state2 = sync2.get_state()
        self.assertEqual(state2["checksums"].get("persist.md"), "xyz789")


if __name__ == "__main__":
    unittest.main()