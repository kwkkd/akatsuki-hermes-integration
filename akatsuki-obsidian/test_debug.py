import asyncio, json, websockets, uuid

async def test():
    async with websockets.connect("ws://127.0.0.1:18749") as ws:
        # Call with unique ID, print all messages
        msg_id = str(uuid.uuid4())[:8]
        await ws.send(json.dumps({
            "jsonrpc": "2.0", "id": msg_id,
            "method": "note/list",
            "params": {"prefix": "AKATSUKI/Missions"}
        }))
        await asyncio.sleep(3)  # give time for response + any events
        # Drain all available messages
        import sys
        while True:
            try:
                resp = json.loads(await asyncio.wait_for(ws.recv(), timeout=1.0))
                print(f"RECV [id={resp.get('id', 'N/A')}]: method={resp.get('method', 'N/A')}")
                if resp.get('result'):
                    notes = resp['result'].get('notes', [])
                    print(f"  -> {len(notes)} notes")
                    for n in notes:
                        print(f"     - {n['path']}")
                elif resp.get('error'):
                    print(f"  -> ERROR: {resp['error']}")
            except asyncio.TimeoutError:
                print("(no more messages)")
                break

asyncio.run(test())
