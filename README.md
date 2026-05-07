# Murmura

<div align="center">

**Universal Prediction Engine · 通用預測引擎**

Turn any seed text into an inspectable multi-agent forecast of collective behaviour.  
將任何種子文本轉成可檢查的多智能體集體反應預測。

[![License](https://img.shields.io/badge/license-Prosperity%20Public%202.0-orange)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11-blue)](https://www.python.org/)
[![Vue](https://img.shields.io/badge/vue-3.x-brightgreen)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-async-009688)](https://fastapi.tiangolo.com/)

</div>

---

## What Murmura Does

Murmura is a universal prediction workbench. Paste a news brief, market shock, policy proposal, company memo, fictional world, or historical fragment, and the engine automatically builds a simulation world:

1. Extracts entities, causal relations, and hidden stakeholders.
2. Builds a knowledge graph and agent population.
3. Runs an OASIS multi-agent simulation with memory, belief updates, factions, moderation events, shocks, and macro feedback.
4. Generates a traceable ReACT report with explainable-analysis tools.
5. Lets you interview agents and test what-if branches.

Murmura 不是單純叫 LLM 猜答案。它會把文本轉成一個可運行的世界，讓不同代理人帶著記憶、偏好、信念同資訊差互相影響，再觀察群體趨勢如何湧現。

---

## Quick Start

### Local Development

Requirements: Python 3.10 or 3.11, Node.js 18+, Git.

```bash
git clone https://github.com/destinyfrancis/Murmura.git
cd Murmura
make quickstart
```

Daily commands:

```bash
make start        # backend :5001 + frontend :5173
make stop         # stop uvicorn and OASIS processes
make backend      # backend only
make frontend     # frontend only
```

### Docker

```bash
cp .env.example .env
docker compose up -d
```

Demo mode without API keys:

```bash
docker compose --profile demo up -d
```

Observability with Jaeger:

```bash
docker compose --profile observability up -d
```

---

## Product Workflow

```text
Seed Text
  |
  v
Step 1  Graph Build      Entity extraction -> KG -> hidden actors -> memory seeds
Step 2  Env Setup        Agent profiles -> platform identities -> scenario config
Step 3  Simulation       OASIS rounds -> beliefs -> factions -> macro feedback
Step 4  Report           ReACT report -> XAI tools -> PDF/share token
Step 5  Interaction      Agent interviews -> what-if shocks -> branch comparison
```

The current UI is a compact prediction workbench: black/white/gray/orange, low-radius panels, visible five-step state, left canvas/right control surfaces, and an updated Learn page that acts as an operator manual rather than a marketing page.

---

## Core Capabilities

| Capability | What it means |
|---|---|
| Zero-config universal mode | Drop in any seed text; Murmura infers agents, decisions, metrics, and shocks. |
| Four-stage actor discovery | Explicit KG nodes, implicit stakeholders, scenario-implied actors, and background agents. |
| Knowledge firewall | LLM prompts reason from the seed text and avoid post-seed future knowledge. |
| Cognitive agents | Big Five, attachment style, cognitive fingerprint, goals, memories, and trust relations. |
| Bayesian belief dynamics | Belief updates use Bayesian revision and embedding propagation, not simple averaging. |
| Structured simulation hooks | Memories, trust, emotions, decisions, debate, propagation, factions, virality, and macro updates. |
| Multi-platform identity | Agents can carry platform-specific identities and activity vectors. |
| Swarm ensemble and forks | Divergence-triggered branches, lite replicas, Wilson intervals, and probability clouds. |
| ReACT reporting | Reports use dedicated XAI tools over timeline, factions, metrics, beliefs, and evidence. |
| Runtime settings | API keys, LLM models, per-step overrides, and presets update without server restart. |

---

## Simulation Presets

| Preset | Agents | Rounds | Emergence | Typical use |
|---|---:|---:|---|---|
| FAST | 100 | 15 | Off | Demo and quick validation |
| STANDARD | 300 | 20 | On | General scenario analysis |
| DEEP | 500 | 30 | On | Research and deeper branching |
| LARGE | 1,000 | 25 | On | Large-scale stress runs |
| MASSIVE | 3,000 | 20 | On | High-load simulations |
| custom | up to 50,000 | up to 100 | On | Advanced experiments |

Python compatibility note: the OASIS engine requires Python 3.10 or 3.11. If the app runs on Python 3.12+, the UI degrades gracefully and disables the Simulation step.

---

## Architecture

```text
frontend/
  src/views/         Home, Process, Workspace, Settings, Learn, Report, GodViewTerminal
  src/components/    graph, report, settings, simulation, lessons, charts
  src/api/           graph.js, simulation.js, report.js, settings.js
  src/i18n/          zh-TW.js, en-US.js

backend/
  app/api/           FastAPI routers: graph, simulation, report, settings, auth, ws
  app/services/      business logic: KG, agents, simulation, report, analytics, settings
  app/models/        frozen Pydantic models and dataclasses
  app/utils/         db.py, llm_client.py, runtime_settings.py, prompt_security.py
  database/          schema.sql with 60+ tables
  tests/             pytest unit and integration tests

data/
  murmuroscope.db    SQLite WAL database
  benchmarks/        fixtures and benchmark outputs
```

Main data systems:

| System | Role |
|---|---|
| SQLite WAL | Session, agents, KG, actions, beliefs, reports, settings, auth. |
| LanceDB | 384-dimensional memory and world-context embeddings. |
| DuckDB | Read-only analytics over SQLite data. |
| OASIS | Subprocess multi-agent simulation engine over JSONL IPC. |

---

## LLM Configuration

Set defaults in `.env`, then override live from `/settings`.

| Scope | Key examples | Purpose |
|---|---|---|
| Agents | `AGENT_LLM_PROVIDER`, `AGENT_LLM_MODEL`, `AGENT_LLM_MODEL_LITE` | Agent thinking, decisions, background agents. |
| Reports | `LLM_PROVIDER`, `GOOGLE_REPORT_MODEL` | Long-form report generation and analysis. |
| Step overrides | `step1_llm_provider`, `step1_llm_model`, through `step5_*` | Per-workflow model routing. |
| Cost controls | `SESSION_COST_BUDGET_USD`, `SESSION_COST_HARD_CAP_USD` | Warning and pause thresholds. |

Settings are stored in the `app_settings` table and loaded into `RuntimeSettingsStore`. A `PUT /api/settings` write updates both SQLite and in-memory overrides, so the next LLM call uses the new model or provider.

API keys are masked in responses and should never be committed.

---

## API Overview

| Area | Endpoint |
|---|---|
| Auth | `POST /auth/register`, `POST /auth/login`, `GET /auth/me` |
| Graph | `POST /graph/build`, `GET /graph/{id}`, `GET /graph/{id}/temporal?round=N` |
| Simulation | `POST /simulation/quick-start`, `POST /simulation/create`, `POST /simulation/start`, `GET /simulation/{id}/status` |
| Admin queue | `GET /simulation/admin/queue`, `POST /simulation/admin/jobs/{id}/cancel` |
| Report | `POST /report/{id}/generate`, `GET /report/{id}/pdf`, `POST /report/{id}/share` |
| Settings | `GET /api/settings`, `PUT /api/settings`, `POST /api/settings/test-key` |
| Cognitive theater | `GET /simulation/{id}/factions`, `GET /simulation/{id}/tipping-points`, `GET /simulation/{id}/multi-run` |
| Swarm | `POST /simulation/{id}/swarm-ensemble`, `GET /simulation/{id}/auto-forks` |
| Domain packs | `GET /api/domain-packs`, `POST /api/domain-packs/generate`, `POST /api/domain-packs/save` |

All user-provided scenario text should pass through `sanitize_seed_text()` or `sanitize_scenario_description()`.

---

## Testing

```bash
make test                      # unit tests
make test-int                  # integration tests
make test-all                  # full suite
make test-cov                  # unit + HTML coverage
make test-file F=test_zero_config
make test-changed
```

Notes:

- Unit tests are pure logic and fast.
- Integration tests use DB fixtures.
- Embedding tests should patch `EmbeddingProvider.embed_single` with a fixed 384-dim vector.
- Endpoint tests that mock SlowAPI-decorated routes must pass a mocked Starlette `Request`.

---

## Development Notes

- Backend handlers are async; DB access goes through `backend.app.utils.db.get_db()`.
- Models should be immutable: frozen dataclasses or `ConfigDict(frozen=True)`.
- FastAPI static routes must be declared before parameterized routes.
- `SimulationSubprocessManager` should be used through `launch()`, `stop()`, `cleanup()`, and `is_running()`.
- Frontend UI strings should use `vue-i18n`; avoid hardcoded Chinese or English in UI components.
- Vue timers and WebSocket reconnection timers must be cleared on unmount.
- The UI brand is `Murmura`; do not use legacy names in visible copy.

---

## Use Cases

| Use case | Seed example | Output |
|---|---|---|
| Geopolitical risk | Escalation brief, sanctions note, trade-war scenario | Coalition shifts, escalation risks, tipping points. |
| Markets and macro | Rate shock, supply-chain disruption, asset panic | Sentiment paths, macro feedback, probability bands. |
| Policy planning | Housing policy, migration policy, subsidy reform | Stakeholder reactions, opposition formation, what-if branches. |
| Company strategy | Competitor launch, B2B supply-chain change | Customer and supplier responses, faction dynamics. |
| Narrative worlds | Novel excerpt, fictional conflict, historical fragment | Character incentives, alliances, branch outcomes. |

---

## Limits

Murmura is a research and scenario-exploration tool. It is useful for stress-testing assumptions, comparing possible futures, and surfacing hidden stakeholders. It is not a substitute for expert judgment in finance, law, medicine, security, or other high-stakes domains.

Good outputs require good seeds. Include context, time horizon, actors, uncertainty, and the question you actually want to answer.

---

## License

Prosperity Public License 2.0.0.

Non-commercial personal, academic, and non-profit use is permitted. Commercial or revenue-generating use requires a separate commercial license.

Copyright © 2026 destinyfrancis. All rights reserved.
