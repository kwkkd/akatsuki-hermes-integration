#!/usr/bin/env python3
"""Install AKATSUKI Obsidian Bridge into Hermes Agent."""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERMES_PATHS = [
    Path.home() / ".local" / "share" / "hermes" / "hermes-agent",
    Path(os.environ.get("APPDATA", "")) / "hermes" / "hermes-agent",
]
HERMES_CLI = shutil.which("hermes") or ""


def find_hermes() -> Path:
    for p in HERMES_PATHS:
        if (p / "tools").exists():
            return p
    if HERMES_CLI:
        p = Path(HERMES_CLI).parent
        if (p / "tools").exists():
            return p
    raise FileNotFoundError("Hermes Agent not found. Install Hermes first.")


def install_bridge(hermes_dir: Path):
    src = Path(__file__).resolve().parent.parent
    bridge_dst = hermes_dir / "hermes_bridge"
    schemas_dst = hermes_dir / "schemas"

    print(f"Installing bridge to {bridge_dst}")
    if bridge_dst.exists():
        shutil.rmtree(bridge_dst)
    shutil.copytree(src / "hermes-bridge" / "src", bridge_dst)
    shutil.copytree(src / "schemas", schemas_dst)

    tool_src = bridge_dst / "commands" / "akatsuki_obsidian.py"
    tool_dst = hermes_dir / "tools" / "akatsuki_obsidian.py"
    shutil.copy2(tool_src, tool_dst)
    print(f"  Tool: {tool_dst}")

    print("  Bridge installed")


def install_skill(hermes_dir: Path):
    src = Path(__file__).resolve().parent.parent
    skill_src = src / "skills" / "akatsuki-obsidian"
    skill_dst = hermes_dir / "skills" / "security" / "akatsuki-obsidian"

    print(f"Installing skill to {skill_dst}")
    if skill_dst.exists():
        shutil.rmtree(skill_dst)
    shutil.copytree(skill_src, skill_dst)
    print("  Skill installed")


def patch_toolsets(hermes_dir: Path):
    toolsets_py = hermes_dir / "toolsets.py"
    if not toolsets_py.exists():
        print("  WARN: toolsets.py not found, skipping")
        return

    content = toolsets_py.read_text()
    if "akatsuki_obsidian" in content:
        print("  toolsets.py already patched")
        return

    print("  Patching toolsets.py...")
    content = content.replace(
        "from .tools.akatsuki_report import register_tools as register_akatsuki_report",
        "from .tools.akatsuki_report import register_tools as register_akatsuki_report\nfrom .tools.akatsuki_obsidian import register_tools as register_akatsuki_obsidian",
    )
    content = content.replace(
        "register_akatsuki_report(register_fn)",
        "register_akatsuki_report(register_fn)\n    register_akatsuki_obsidian(register_fn)",
    )
    toolsets_py.write_text(content)
    print("  toolsets.py patched")


def install_obsidian_plugin():
    plugin_src = Path(__file__).resolve().parent.parent / "obsidian-plugin"
    vaults = list(Path.home().glob("*"))
    vaults += list(Path.home().glob("Documents/*"))
    installed = False

    for v in vaults:
        plugin_dir = v / ".obsidian" / "plugins" / "akatsuki-obsidian"
        if plugin_dir.exists() or (v / ".obsidian").exists():
            plugin_dir.mkdir(parents=True, exist_ok=True)
            for f in ["manifest.json", "main.js", "styles.css"]:
                sf = plugin_src / f
                if sf.exists():
                    shutil.copy2(sf, plugin_dir / f)
            print(f"  Plugin installed: {plugin_dir}")
            installed = True

    if not installed:
        print("  No Obsidian vault found. Install plugin manually:")
        print(f"    Copy obsidian-plugin/ to <vault>/.obsidian/plugins/akatsuki-obsidian/")


def main():
    print("=== AKATSUKI Obsidian Bridge Installer ===\n")

    try:
        hermes_dir = find_hermes()
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    print(f"Hermes Agent: {hermes_dir}\n")
    install_bridge(hermes_dir)
    install_skill(hermes_dir)
    patch_toolsets(hermes_dir)
    install_obsidian_plugin()

    print("\nInstallation complete!")
    print("\nStart the bridge:")
    print(f"  python -m hermes_bridge /path/to/obsidian/vault")
    print("\nThen in Hermes:")
    print("  /obsidian list")
    print("  /obsidian read AKATSUKI/Missions/OP-001")
    print("  /obsidian write --path test.md --content 'Hello'")


if __name__ == "__main__":
    main()
