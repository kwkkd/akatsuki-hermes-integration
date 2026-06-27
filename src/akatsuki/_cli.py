"""AKATSUKI Unified CLI"""
import sys
import json
import asyncio
from typing import List
from .core.config import CONFIG


def print_help():
    print("AKATSUKI - Advanced APT Simulation Toolkit")
    print("=" * 60)
    print("Usage: akatsuki <command> [args]")
    print()
    print("Commands:")
    print("  recon <target>         Reconnaissance (domain/IP/email/URL)")
    print("  payload <type> <lh> <lp>  Payload generation")
    print("  weapon [sub] [args]    Weaponization (evasive, amsi, compress, sandbox)")
    print("  vuln <service> [ver]   Vulnerability lookup")
    print("  cve <id>               CVE details from NVD")
    print("  org chart              Organization chart")
    print("  org member <name>      Agent details")
    print("  team <name>            Team details")
    print("  api                    Start API server")
    print("  mcp                    Start MCP server")
    print("  op <target> [obj]      Multi-agent operation")
    print("  swarm <target> <obj>   Swarm orchestration")
    print("  attack <target> [pb]   Run attack chain")
    print("  kb <query>             Search knowledge base")
    print("  config                 Show configuration")
    print("  chat [message]         Interactive chat (built-in)")
    print("  gateway [status|start] Gateway/API server")
    print("  model                  Show model config")
    print()
    print("Training Commands:")
    print("  train                  SFT training")
    print("  train-dpo              DPO training")
    print("  train-pretrain         Continued pretraining")
    print("  merge                  Merge LoRA weights")
    print()
    print("Payload types: reverse_python, reverse_bash, reverse_php,")
    print("               reverse_ps, bind_python")


def handle_recon(args: List[str]):
    if not args: print("Usage: akatsuki recon <target>"); return
    from .core.recon import ReconEngine
    re = ReconEngine()
    result = re.full_recon(args[0])
    print(json.dumps(result, indent=2, ensure_ascii=False))


def handle_payload(args: List[str]):
    if len(args) < 3: print("Usage: akatsuki payload <type> <lhost> <lport>"); return
    from .core.weapon import PayloadFactory
    code, ext = PayloadFactory().generate(args[0], args[1], int(args[2]))
    fname = f"payload_{args[0]}{ext}"
    with open(fname, "w") as f: f.write(code)
    print(f"[+] Payload generated: {fname} ({len(code)} bytes)")


def handle_weapon(args: List[str]):
    if not args: print("Usage: akatsuki weapon <sub> [args]"); return
    from .core.weapon import EvasionKit
    ek = EvasionKit()
    cmd = args[0]
    if cmd == "amsi":
        lang = args[1] if len(args) > 1 else "powershell"
        print(ek.amsi_bypass(lang).get("code", ""))
    elif cmd == "evasive":
        lang = args[1] if len(args) > 1 else "powershell"
        print(ek.evade_sandbox("echo payload", lang))
    elif cmd == "compress":
        p = args[1] if len(args) > 1 else "echo test"
        print(ek.compress_payload(p))
    elif cmd == "xor":
        p = args[1] if len(args) > 1 else "test"
        k = int(args[2]) if len(args) > 2 else 0x42
        print(ek.xor_obfuscate(p, k))
    else:
        print(f"Unknown weapon command: {cmd}")


def handle_vuln(args: List[str]):
    if not args: print("Usage: akatsuki vuln <service> [version]"); return
    from .core.vuln import VulnMapper
    vulns = VulnMapper().classify(args[0], args[1] if len(args) > 1 else "")
    if vulns:
        for v in vulns:
            print(f"  {v.cve_id} ({v.severity}, CVSS {v.cvss_score}) - {v.affected_software}")
    else:
        print(f"No known vulnerabilities for '{args[0]}'")


def handle_cve(args: List[str]):
    if not args: print("Usage: akatsuki cve <CVE-ID>"); return
    from .core.vuln import VulnMapper
    result = asyncio.run(VulnMapper().fetch_nvd_cve(args[0]))
    if result:
        print(f"  {result['cve_id']}")
        print(f"  Score: {result['cvss_score']} ({result['severity']})")
        print(f"  Published: {result['published']}")
        print(f"  Description: {result['description'][:200]}")
    else:
        print(f"CVE '{args[0]}' not found")


def handle_org(args: List[str]):
    from .core.team import get_org_manager
    mgr = get_org_manager()
    if not args or args[0] == "chart":
        print(mgr.get_org_chart())
    elif args[0] == "member":
        name = args[1] if len(args) > 1 else ""
        m = mgr.get_member(name)
        if m:
            print(f"  {m.codename} ({m.name})")
            print(f"  {'=' * 30}")
            print(f"  Title:     {m.title}")
            print(f"  Dept:      {m.department}")
            print(f"  Team:      {m.team}")
            print(f"  Reports:   {m.report_to}")
            print(f"  Expertise: {', '.join(m.expertise)}")
        else:
            print(f"Agent '{name}' not found")


def handle_team(args: List[str]):
    from .core.team import get_org_manager
    name = args[0] if args else ""
    team = get_org_manager().get_team(name)
    if team:
        print(f"  Team: {team.name} ({team.department})")
        print(f"  {'=' * 30}")
        print(f"  Leader: {team.leader.codename} ({team.leader.name})")
        print(f"  Members ({len(team.members)}):")
        for m in team.members:
            print(f"    - {m.codename} ({m.name}){' [Root]' if m.is_root else ''}")
    else:
        print(f"Team '{name}' not found")


def handle_op(args: List[str]):
    target = args[0] if args else "unknown"
    objective = args[1] if len(args) > 1 else "Full penetration test"
    from .core.team import HackerTeam
    result = asyncio.run(HackerTeam().run_operation(target, objective))
    print(f"Duration: {result.completed_at - result.started_at:.1f}s")
    print(result.final_report[:3000])


def handle_swarm(args: List[str]):
    if len(args) < 2: print("Usage: akatsuki swarm <target> <objective>"); return
    from .core.swarm import SwarmOrchestrator
    result = asyncio.run(SwarmOrchestrator().execute_swarm(f"Target: {args[0]}\nObjective: {args[1]}"))
    print(json.dumps(result, indent=2, ensure_ascii=False)[:3000])


def handle_attack(args: List[str]):
    target = args[0] if args else "unknown"
    from .core.chain import ChainBuilder, ChainExecutor
    chain = ChainBuilder().build(target, "Full attack chain")
    result = ChainExecutor().execute(chain)
    print(json.dumps(result, indent=2, ensure_ascii=False)[:3000])


def handle_kb(args: List[str]):
    if not args: print("Usage: akatsuki kb <query>"); return
    from .knowledge_base.rag import KnowledgeBase
    context = KnowledgeBase().get_context(" ".join(args), max_chars=2000)
    if context: print(f"Knowledge Base Results:\n{context}")
    else: print("No relevant knowledge found")


def handle_chat(args: List[str]):
    from .chat.cli import main
    main(args)


def handle_gateway(args: List[str]):
    from .chat.gateway import main
    main()


def handle_model(args: List[str]):
    print(f"Default model: {CONFIG.api.ollama_model}")
    print(f"Max tokens:    {CONFIG.api.max_tokens}")
    print(f"Temperature:   {CONFIG.api.temperature}")
    print(f"API server:    http://{CONFIG.api.host}:{CONFIG.api.port}")


def handle_api():
    from .api.server import main
    main()


def handle_mcp():
    from .api.mcp import main
    main()


def handle_config():
    print(json.dumps({k: str(v) for k, v in CONFIG.__dict__.items()}, indent=2, default=str))


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help", "?"):
        print_help(); return
    cmd = sys.argv[1]
    args = sys.argv[2:]
    commands = {
        "recon": handle_recon, "payload": handle_payload, "weapon": handle_weapon,
        "vuln": handle_vuln, "cve": handle_cve, "org": handle_org, "team": handle_team,
        "op": handle_op, "operation": handle_op, "swarm": handle_swarm, "attack": handle_attack,
        "kb": handle_kb, "chat": lambda _: handle_chat(_), "gateway": lambda _: handle_gateway(_),
        "model": lambda _: handle_model(_), "api": lambda _: handle_api(), "serve": lambda _: handle_api(),
        "mcp": lambda _: handle_mcp(), "config": lambda _: handle_config(),
        "train": lambda _: __import__("akatsuki.training.train", fromlist=["main"]).main(),
        "train-dpo": lambda _: __import__("akatsuki.training.dpo", fromlist=["main"]).main(),
        "train-pretrain": lambda _: __import__("akatsuki.training.pretrain", fromlist=["main"]).main(),
        "merge": lambda _: __import__("akatsuki.training.merge", fromlist=["main"]).main(),
    }
    if cmd in commands:
        commands[cmd](args)
    else:
        print(f"Unknown command: {cmd}")
        print("Run 'akatsuki help' for usage.")
        sys.exit(1)
