import asyncio, json, websockets, uuid

async def test():
    async with websockets.connect("ws://127.0.0.1:18749") as ws:
        async def call(method, params=None):
            msg_id = str(uuid.uuid4())[:8]
            await ws.send(json.dumps({"jsonrpc": "2.0", "id": msg_id, "method": method, "params": params or {}}))
            while True:
                resp = json.loads(await ws.recv())
                if resp.get("id") == msg_id:
                    return resp.get("result")

        r = await call("ping")
        assert r["pong"] == True
        print("PASS: ping")

        r = await call("note/write", {"note": {"path": "AKATSUKI/TEST-FINAL.md", "title": "Final Test", "content": "Final validation", "tags": ["final", "validation"]}})
        assert r["path"] == "AKATSUKI/TEST-FINAL.md"
        print("PASS: write")

        r = await call("note/read", {"path": "AKATSUKI/TEST-FINAL.md"})
        assert r["title"] == "Final Test"
        assert "Final validation" in r["content"]
        assert "final" in r["tags"]
        assert "validation" in r["tags"]
        print("PASS: read (title, content, tags)")

        r = await call("note/search", {"query": "Final"})
        assert len(r["notes"]) >= 1
        print("PASS: search")

        r = await call("note/list", {"prefix": "AKATSUKI"})
        assert len(r["notes"]) >= 3
        print(f"PASS: list ({len(r['notes'])} notes)")

        r = await call("folder/list", {})
        assert len(r["folders"]) >= 1
        print(f"PASS: folders {r['folders']}")

        r = await call("tags/list", {})
        assert "final" in r["tags"]
        print(f"PASS: tags ({len(r['tags'])} total, including 'final')")

        r = await call("note/delete", {"path": "AKATSUKI/TEST-FINAL.md"})
        assert r["deleted"] == True
        print("PASS: delete")

        print("\n=== ALL 8 TESTS PASSED ===")

asyncio.run(test())
