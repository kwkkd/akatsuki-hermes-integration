import asyncio, json, websockets, uuid

async def test():
    async with websockets.connect("ws://127.0.0.1:18749") as ws:
        msg_id = str(uuid.uuid4())[:8]
        await ws.send(json.dumps({"jsonrpc": "2.0", "id": msg_id, "method": "note/read", "params": {"path": "AKATSUKI/INTEL-001.md"}}))
        while True:
            resp = json.loads(await ws.recv())
            if resp.get("id") == msg_id:
                print(json.dumps(resp, indent=2, ensure_ascii=False))
                return

asyncio.run(test())
