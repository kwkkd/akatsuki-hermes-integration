import asyncio, json, websockets, uuid

async def test():
    async with websockets.connect("ws://127.0.0.1:18749") as ws:
        msg_id = str(uuid.uuid4())[:8]
        await ws.send(json.dumps({"jsonrpc": "2.0", "id": msg_id, "method": "note/delete", "params": {"path": "AKATSUKI/TEST-FINAL.md"}}))
        errors = 0
        while True:
            resp = json.loads(await ws.recv())
            rid = resp.get("id")
            print(f"GOT: id={rid}, method={resp.get('method','?')}, has_result={'result' in resp}, has_error={'error' in resp}")
            if rid == msg_id:
                print("MATCH!")
                print(json.dumps(resp, indent=2))
                return
            errors += 1
            if errors > 10:
                print("Too many non-matching messages, aborting")
                return

asyncio.run(test())
