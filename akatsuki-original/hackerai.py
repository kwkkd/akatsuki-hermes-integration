"""
AKATSUKI — Universal CLI Tool
=============================
Usage:
  python hackerai.py dept <name> <objective> [context]
  python hackerai.py op <target> [objective]
  python hackerai.py list
  python hackerai.py chat <message>
  python hackerai.py attack <target> [playbook]
  python hackerai.py recon <domain>
  python hackerai.py payload <type> <lhost> <lport>
  python hackerai.py scan <target>
"""
import json, sys, httpx, os
sys.path.insert(0, os.path.dirname(__file__))
from akatsuki_config import CONFIG
from logger import logger

API = f"http://{CONFIG.api.host}:{CONFIG.api.port}/v1"

def main():
    if len(sys.argv) < 2:
        logger.info(__doc__)
        return
    cmd = sys.argv[1]

    if cmd == "list":
        r = httpx.get(f"{API}/tools", timeout=10)
        tools = r.json()
        logger.info(f"AKATSUKI — {len(tools)} departments/tools available\n")
        for t in tools:
            fn = t["function"]
            logger.info(f"  {fn['name']}")
            logger.info(f"    {fn['description'][:100]}")
            props = fn["parameters"].get("properties", {})
            required = fn["parameters"].get("required", [])
            for pn, pv in props.items():
                req = " *" if pn in required else ""
                logger.info(f"    - {pn}{req}: {pv.get('description','')[:80]}")
            logger.info("")

    elif cmd == "dept":
        if len(sys.argv) < 4:
            logger.error("Usage: python hackerai.py dept <name> <objective> [context]")
            return
        name = sys.argv[2]
        objective = sys.argv[3]
        context = sys.argv[4] if len(sys.argv) > 4 else ""
        logger.info(f"[{name}] {objective[:60]}...")
        r = httpx.post(f"{API}/dept/{name}", json={"objective": objective, "context": context}, timeout=180)
        data = r.json()
        if "result" in data:
            logger.info(f"\n{data['result'][:3000]}")
        else:
            logger.info(json.dumps(data, indent=2, ensure_ascii=False))

    elif cmd == "op":
        target = sys.argv[2] if len(sys.argv) > 2 else "unknown"
        objective = sys.argv[3] if len(sys.argv) > 3 else "Full penetration test"
        logger.info(f"[OPERATION] {target} — {objective[:60]}...")
        r = httpx.post(f"{API}/team/operation", json={"target": target, "objective": objective}, timeout=600)
        data = r.json()
        if "final_report" in data:
            logger.info(f"\nDuration: {data.get('duration_seconds',0)}s")
            logger.info(f"\n{data['final_report'][:4000]}")
        else:
            logger.info(json.dumps(data, indent=2, ensure_ascii=False))

    elif cmd == "chat":
        msg = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "Hello"
        r = httpx.post(f"{API}/chat/tool-completions", json={
            "model": "hacker-ai", "messages": [{"role": "user", "content": msg}],
            "temperature": 0.3, "max_tokens": 1024
        }, timeout=180)
        logger.info(r.json()["choices"][0]["message"]["content"])

    elif cmd == "attack":
        target = sys.argv[2] if len(sys.argv) > 2 else "unknown"
        playbook = sys.argv[3] if len(sys.argv) > 3 else "web_full_chain"
        logger.info(f"[ATTACK] {target} — playbook: {playbook}")
        try:
            from chain_builder import ChainBuilder
            from chain_executor import ChainExecutor
            builder = ChainBuilder()
            chain = builder.load_playbook(f"playbooks/{playbook}.yaml", target) if playbook else builder.build(target, "Full penetration test")
            executor = ChainExecutor()
            result = executor.execute(chain)
            logger.info(json.dumps(result, indent=2, ensure_ascii=False)[:3000])
        except Exception as e:
            logger.error(f"[Error] {e}")

    elif cmd == "recon":
        domain = sys.argv[2] if len(sys.argv) > 2 else "example.com"
        logger.info(f"[RECON] {domain}")
        try:
            from recon_engine import ReconEngine
            re = ReconEngine()
            result = re.full_recon(domain)
            logger.info(json.dumps(result, indent=2, ensure_ascii=False))
        except Exception as e:
            logger.error(f"[Error] {e}")

    elif cmd == "payload":
        if len(sys.argv) < 5:
            logger.error("Usage: python hackerai.py payload <type> <lhost> <lport>")
            logger.error("Types: reverse_python, reverse_ps, reverse_bash, reverse_php, bind_python")
            return
        ptype, lhost, lport = sys.argv[2], sys.argv[3], int(sys.argv[4])
        try:
            from payload_factory import PayloadFactory
            pf = PayloadFactory()
            code, ext = pf.generate(ptype, lhost, lport)
            fname = f"payload_{ptype}{ext}"
            with open(fname, "w") as f:
                f.write(code)
            logger.info(f"[+] Payload saved: {fname}")
        except Exception as e:
            logger.error(f"[Error] {e}")

    elif cmd == "scan":
        target = sys.argv[2] if len(sys.argv) > 2 else "127.0.0.1"
        logger.info(f"[SCAN] {target}")
        try:
            from tool_runner import ToolRunner
            tr = ToolRunner()
            logger.info(f"Available tools: {{k for k,v in tr.tools.items() if v}}")
            result = tr.run_scan(target)
            logger.info(json.dumps(result, indent=2, ensure_ascii=False)[:2000])
        except Exception as e:
            logger.error(f"[Error] {e}")

    else:
        logger.error(f"Unknown command: {cmd}")
        logger.error(__doc__)

if __name__ == "__main__":
    main()
