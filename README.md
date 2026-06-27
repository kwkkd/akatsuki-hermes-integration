# AKATSUKI — Advanced APT Simulation Toolkit

**Penetration testing simulation. AI-native. Fully offline-capable.**

AKATSUKI is a modular red-team simulation framework with a built-in chat agent, multi-agent swarm orchestration, payload generation, reconnaissance engine, vulnerability mapping, and an optional HuggingFace training pipeline for fine-tuning LLMs.

```
pip install akatsuki
```

No external agent framework required. Everything runs out of the box.

---

## Quick Start

```bash
# Talk to an AI (auto-detects Ollama at localhost:11434)
akatsuki chat "Scan a web server for common vulnerabilities"

# Reconnaissance
akatsuki recon example.com

# Payload generation
akatsuki payload reverse_python 10.0.0.1 4444

# Vulnerability lookup
akatsuki vuln apache 2.4.49

# Organization chart
akatsuki org chart

# Multi-agent swarm operation
akatsuki swarm 10.0.0.0/24 "Full penetration test"

# Attack chain
akatsuki attack example.com

# Start REST API server
akatsuki api

# Show configuration
akatsuki config
```

---

## Installation

### Core (works immediately)

```bash
pip install akatsuki
```

The core toolkit requires only lightweight dependencies (FastAPI, httpx, pydantic, dnspython, python-whois). It includes the interactive chat, CLI, API server, and all simulation engines.

### Optional components

```bash
# All features (training, MCP, web UI, Telegram)
pip install akatsuki[all]

# Training pipeline (torch + transformers + PEFT + TRL)
pip install akatsuki[training]

# MCP server
pip install akatsuki[mcp]

# Web UI (Gradio)
pip install akatsuki[webui]

# Telegram bot
pip install akatsuki[telegram]

# Development
pip install akatsuki[dev]
```

### LLM Backend

Chat requires a running LLM backend. AKATSUKI auto-detects Ollama:

```bash
# Install Ollama: https://ollama.com
ollama pull dolphin-mistral:7b

# Chat works immediately -- no config needed
akatsuki chat "Hello"
```

Alternatively, start the API server and connect any OpenAI-compatible backend:

```bash
akatsuki api &
akatsuki chat "Hello"
```

---

## Commands

### Simulation

| Command | Description |
|---------|-------------|
| `akatsuki recon <target>` | Domain/IP/email/URL reconnaissance (DNS, WHOIS, subdomain enum, tech detection) |
| `akatsuki payload <type> <lhost> <lport>` | Generate reverse/bind shell payload (python, bash, php, powershell) |
| `akatsuki weapon <subcommand> [args]` | Weaponization: evasive code, AMSI bypass, compression, XOR obfuscation |
| `akatsuki vuln <service> [version]` | Look up known vulnerabilities from built-in database |
| `akatsuki cve <CVE-ID>` | Fetch CVE details from NVD |
| `akatsuki attack <target> [playbook]` | Execute a full attack chain |

### Organization

| Command | Description |
|---------|-------------|
| `akatsuki org chart` | Display the 13-agent organizational chart |
| `akatsuki org member <name>` | Show details of a specific agent |
| `akatsuki team <name>` | Show team structure and members |

### Operations

| Command | Description |
|---------|-------------|
| `akatsuki op <target> [objective]` | Multi-agent operation across all departments |
| `akatsuki swarm <target> <objective>` | 4-phase swarm orchestration (recon, analysis, exploit, report) |
| `akatsuki kb <query>` | Search the knowledge base (RAG over markdown documents) |
| `akatsuki config` | Show current configuration |

### Chat & API

| Command | Description |
|---------|-------------|
| `akatsuki chat [message]` | Interactive or single-message chat (auto-detects Ollama) |
| `akatsuki chat --model <name>` | Chat with a specific model |
| `akatsuki api` | Start the FastAPI REST server |
| `akatsuki gateway` | Show gateway status |
| `akatsuki model` | Show model configuration |

### Training

| Command | Description |
|---------|-------------|
| `akatsuki train` | SFT training with LoRA via TRL `SFTTrainer` |
| `akatsuki train-dpo` | DPO preference training via TRL `DPOTrainer` |
| `akatsuki train-pretrain` | Continued pretraining with causal LM |
| `akatsuki merge` | Merge LoRA weights into base model |

Training requires `pip install akatsuki[training]`.

---

## Architecture

```
src/akatsuki/
├── __init__.py          # Package root
├── __main__.py          # python -m akatsuki
├── _cli.py              # Unified CLI dispatcher
│
├── core/                # Simulation engines
│   ├── config.py        # GlobalConfig (pydantic, env-aware)
│   ├── recon.py         # ReconEngine -- DNS, WHOIS, HTTP, Shodan, Censys
│   ├── weapon.py        # PayloadFactory + EvasionKit
│   ├── vuln.py          # VulnMapper + NVD integration + vuln_db.json
│   ├── team.py          # 13 Naruto-themed agents, OrgManager, HackerTeam, AgentWorker
│   ├── swarm.py         # SwarmOrchestrator -- 4-phase async consensus
│   ├── chain.py         # ChainBuilder, ChainExecutor, C2Builder
│   ├── tool_runner.py   # Wraps nmap, sqlmap, nuclei, hydra, msfconsole
│   ├── inference.py     # Local model inference via transformers
│   ├── report_gen.py    # Markdown/PDF report generation
│   └── logger.py        # Centralized logging
│
├── api/                 # REST API
│   ├── server.py        # FastAPI -- Ollama proxy, auth, chat, team endpoints
│   ├── client.py        # AkatsukiAPIClient -- auto Ollama detection, retry
│   ├── mcp.py           # MCP server -- real tool execution
│   └── hackerai_mcp.py  # Alternative MCP server
│
├── chat/                # Built-in chat (no external deps)
│   ├── cli.py           # Interactive/single-message chat
│   ├── gateway.py       # Gateway status
│   └── tools.py         # 6 built-in AKATSUKI tools with OpenAI function-calling schema
│
├── training/            # HuggingFace training pipeline
│   ├── train.py         # SFTTrainer + LoRA + 4-bit
│   ├── dpo.py           # DPOTrainer
│   ├── pretrain.py      # Continued pretraining
│   └── merge.py         # LoRA weight merging
│
├── knowledge_base/      # RAG system
│   └── rag.py           # Keyword-based context retrieval over .md files
│
├── hermes/              # Hermes Agent compatibility layer
│   ├── tools.py         # External hermes-agent tool registration
│   └── adapter.py       # AkatsukiAgent -- works with or without hermes-agent
│
├── telegram/            # Telegram bot
├── webui/               # Gradio web interface
└── data/                # Dataset builders
```

---

## API Server

```bash
akatsuki api
```

Open `http://localhost:8000/docs` for interactive Swagger documentation.

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check with Ollama status |
| GET | `/v1/models` | List available models |
| POST | `/v1/chat/completions` | OpenAI-compatible chat completions (proxied to Ollama) |
| GET | `/v1/team/status` | Team status |
| GET | `/v1/team/info` | Organization chart |
| GET | `/v1/tools` | List registered AKATSUKI tools |
| POST | `/v1/dept/{name}` | Department-specific task execution |

### Authentication

Set `AKATSUKI_API_KEY` environment variable to enable Bearer token authentication for all non-public endpoints.

---

## Configuration

Configuration is managed through environment variables and `akatsuki.yaml`.

| Variable | Default | Description |
|----------|---------|-------------|
| `AKATSUKI_API_URL` | `http://localhost:8000/v1` | API server URL |
| `AKATSUKI_API_KEY` | `""` | API authentication key |
| `AKATSUKI_OLLAMA_DIRECT` | auto-detected | Direct Ollama URL |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `dolphin-mistral:7b` | Default model name |
| `TELEGRAM_BOT_TOKEN` | `""` | Telegram bot token |

---

## Hermes Agent Compatibility

AKATSUKI ships with a built-in chat agent, so no external framework is required. However, if you prefer using `hermes-agent`, install:

```bash
pip install akatsuki[hermes]
```

When Hermes Agent is installed, `akatsuki chat` uses it automatically. When absent, the built-in chat takes over -- same interface, same tools.

---

## License

MIT
