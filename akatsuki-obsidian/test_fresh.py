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

        r = await call("note/write", {"note": {"path": "AKATSUKI/FRESH.md", "title": "Fresh Report", "content": "Fresh content here", "tags": ["fresh"]}})
        print("write:", r["path"])

        r = await call("note/read", {"path": "AKATSUKI/FRESH.md"})
        print(f"title: '{r['title']}' (expected: 'FRESH' or 'Fresh Report')")
        print(f"frontmatter title: '{r['frontmatter'].get('title')}'")
        print(f"tags: {r['tags']}")

asyncio.run(test())
