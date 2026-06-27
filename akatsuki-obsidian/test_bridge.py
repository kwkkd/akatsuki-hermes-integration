import asyncio
import json
import websockets


async def test():
    async with websockets.connect("ws://127.0.0.1:18749") as ws:
        await ws.send(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "ping", "params": {}}))
        resp = json.loads(await ws.recv())
        print("Ping:", json.dumps(resp, indent=2))

        await ws.send(json.dumps({
            "jsonrpc": "2.0", "id": 2, "method": "note/write",
            "params": {"note": {"path": "AKATSUKI/test.md", "title": "Test",
                                "content": "Hello from bridge!", "tags": ["test"]}}
        }))
        resp = json.loads(await ws.recv())
        print("Write:", json.dumps(resp, indent=2))

        await ws.send(json.dumps({"jsonrpc": "2.0", "id": 3, "method": "note/list", "params": {"prefix": "AKATSUKI"}}))
        resp = json.loads(await ws.recv())
        print("List:", json.dumps(resp, indent=2))

asyncio.run(test())
