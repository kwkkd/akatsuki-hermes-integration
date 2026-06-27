import asyncio, json, websockets, uuid

async def test():
    async with websockets.connect("ws://127.0.0.1:18749") as ws:
        async def call(method, params=None):
            msg_id = str(uuid.uuid4())[:8]
            await ws.send(json.dumps({"jsonrpc": "2.0", "id": msg_id, "method": method, "params": params or {}}))
            while True:
                resp = json.loads(await ws.recv())
                rid = resp.get("id")
                if rid == msg_id:
                    return resp
                print(f"  [skip event: method={resp.get('method','?')}]")

        r = await call("ping")
        print(f"[1] ping: {r['result']['pong']}")

        r = await call("note/write", {"note": {"path": "AKATSUKI/Missions/DEBUG.md", "title": "Debug", "content": "test body", "tags": ["debug"]}})
        print(f"[2] write: {r['result']['path']}")

        r = await call("note/list", {"prefix": "AKATSUKI/Missions"})
        notes = r.get("result", {}).get("notes", [])
        print(f"[3] list: {len(notes)} notes")
        for n in notes:
            print(f"    - {n['path']}")

        r = await call("folder/list", {})
        print(f"[4] folders: {r}")

asyncio.run(test())
