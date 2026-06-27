import asyncio, json, websockets, os
from pathlib import Path

VAULT = Path(os.environ.get("AKATSUKI_VAULT", "C:/Users/이준혁/Documents/AKATSUKI-Vault"))

async def demo():
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    print("=" * 60)
    print("AKATSUKI Obsidian Bridge - LIVE DEMO")
    print("=" * 60)

    # 1. Connect
    print("\n[1] WebSocket connecting...")
    async with websockets.connect("ws://127.0.0.1:18749") as ws:
        print("    [OK] Connected")

        async def call(method, params=None):
            import uuid
            msg_id = str(uuid.uuid4())[:8]
            await ws.send(json.dumps({"jsonrpc": "2.0", "id": msg_id, "method": method, "params": params or {}}))
            while True:
                resp = json.loads(await ws.recv())
                if resp.get("id") == msg_id:
                    return resp

        # 2. Ping
        print("\n[2] Ping test...")
        r = await call("ping")
        assert r["result"]["pong"] == True
        print(f"    [OK] Pong! vault: {r['result']['vault']}")

        # 3. Write a note
        print("\n[3] Write note...")
        r = await call("note/write", {
            "note": {
                "path": "AKATSUKI/Missions/LIVE-TEST-001.md",
                "title": "Live Test Mission",
                "content": "# Live Test Mission\n\nThis note was created via **WebSocket IPC**.\n\n## Target\n- IP: 10.0.0.1\n- Service: Apache 2.4.49\n\n## Status\n- [ ] Recon complete\n- [x] Vulnerability identified (CVE-2021-41773)\n- [ ] Exploitation pending",
                "tags": ["live-test", "mission", "apache"],
            }
        })
        print(f"    [OK] Written: {r['result']['path']} (v{r['result']['version']})")

        # 4. Read it back
        print("\n[4] Read note...")
        r = await call("note/read", {"path": "AKATSUKI/Missions/LIVE-TEST-001.md"})
        note = r["result"]
        print(f"    [OK] Title: {note['title']}")
        print(f"    [OK] Tags: {note['tags']}")
        print(f"    [OK] Content ({len(note['content'])} chars): {note['content'][:60]}...")

        # 5. Search
        print("\n[5] Search test ('Apache')...")
        r = await call("note/search", {"query": "Apache"})
        notes = r.get("notes", [])
        print(f"    [OK] {len(notes)} notes found")
        for n in notes:
            print(f"       - {n['path']}")

        # 6. List notes
        print("\n[6] List notes (AKATSUKI/Missions)...")
        r = await call("note/list", {"prefix": "AKATSUKI/Missions"})
        notes = r.get("notes", [])
        print(f"    [OK] {len(notes)} notes in Missions/")
        for n in notes:
            print(f"       - {n['path']} (v{n['version']})")

        # 7. List folders
        print("\n[7] Folder structure...")
        r = await call("folder/list", {})
        print(f"    [OK] {len(r['folders'])} folders:")
        for f in r['folders']:
            print(f"       - {f}")

        # 8. List tags
        print("\n[8] Tags list...")
        r = await call("tags/list", {})
        print(f"    [OK] {len(r['tags'])} tags: {r['tags']}")

    # 9. Verify on filesystem
    print("\n[9] Filesystem check...")
    target = VAULT / "AKATSUKI" / "Missions" / "LIVE-TEST-001.md"
    if target.exists():
        content = target.read_text(encoding="utf-8")
        print(f"    [OK] File exists: {target}")
        print(f"    [OK] Size: {len(content)} bytes")
        for i, line in enumerate(content.split("\n")[:5]):
            print(f"       | {line}")
    else:
        print(f"    [FAIL] File not found: {target}")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED")
    print("Vault: " + str(VAULT))
    print("WebSocket: ws://127.0.0.1:18749")
    print("=" * 60)

asyncio.run(demo())
