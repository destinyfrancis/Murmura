# Murmura

<div align="center">

**Turn any text into a simulated world of people, incentives, reactions, and possible futures.**

Murmura is a universal prediction engine for exploring how groups may react to events, shocks, policies, stories, and market changes.

[![License](https://img.shields.io/badge/license-Prosperity%20Public%202.0-orange)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11-blue)](https://www.python.org/)
[![Vue](https://img.shields.io/badge/vue-3-brightgreen)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-async-009688)](https://fastapi.tiangolo.com/)

</div>

---

## What Is Murmura?

Murmura lets you paste a piece of text and turn it into a living simulation.

That text can be:

- a news article
- a market shock
- a policy proposal
- a company memo
- a conflict scenario
- a fictional world
- a historical fragment
- a question you want to stress-test

Murmura then builds a world from it: who matters, who is affected, what they believe, how they influence one another, what could change, and which outcomes look more or less likely.

In plain language: **Murmura helps you explore “what might happen next?” without manually building a simulation from scratch.**

---

## What Can You Do With It?

| You want to know... | Murmura helps by... |
|---|---|
| How different groups may react to an event | Creating agents with different roles, incentives, beliefs, and memories |
| Which hidden stakeholders are being missed | Finding actors who are affected even if they are not named in the text |
| How a shock could spread through a system | Simulating rounds of reaction, belief change, faction formation, and feedback |
| Whether a result is stable or fragile | Running branches, what-if scenarios, and probability bands |
| Why the forecast says what it says | Producing traceable reports with evidence, timelines, and agent reasoning |
| What a specific actor might say or do | Letting you interview simulated agents after the run |

Example inputs:

```text
A new competitor enters a B2B supply chain market with aggressive pricing.
```

```text
A central bank unexpectedly raises interest rates by 200 basis points.
```

```text
In a fictional kingdom, two factions compete for control after the monarch disappears.
```

---

## How It Works

Murmura uses a five-step workflow:

```text
1. Build the world
   Your text becomes a knowledge graph of people, organizations, events, places, and relationships.

2. Create the agents
   The system creates simulated actors with goals, memories, personalities, beliefs, and platform identities.

3. Run the simulation
   Agents react over multiple rounds. They make decisions, influence each other, form factions, and respond to shocks.

4. Generate the report
   Murmura explains what happened, what changed, what outcomes emerged, and where the uncertainty is.

5. Ask follow-up questions
   You can interview agents, test what-if shocks, and compare alternative timelines.
```

You do not need to configure agents, decisions, metrics, or shocks by hand. Murmura infers them from the seed text.

---

## Quick Start

### Option 1: Local Development

Requirements:

- Python 3.10 or 3.11
- Node.js 18+
- Git

```bash
git clone https://github.com/destinyfrancis/Murmura.git
cd Murmura
make quickstart
```

Daily development:

```bash
make start      # start backend :5001 and frontend :5173
make stop       # stop local services
make backend    # backend only
make frontend   # frontend only
```

Open the app at:

```text
http://localhost:5173
```

### Option 2: Docker

```bash
cp .env.example .env
docker compose up -d
```

Demo mode without live API keys:

```bash
docker compose --profile demo up -d
```

With observability:

```bash
docker compose --profile observability up -d
```

---

## API Keys And Models

Murmura can run in demo mode, but live LLM-powered runs need model provider keys.

The easiest path:

1. Copy `.env.example` to `.env`.
2. Add your provider keys.
3. Start the app.
4. Open **Settings** in the UI to test keys and change models.

Common settings:

| Setting | What it controls |
|---|---|
| `OPENROUTER_API_KEY` | Agent generation and agent decisions |
| `GOOGLE_API_KEY` | Report generation, if using Google models |
| `AGENT_LLM_PROVIDER` | Default provider for agents |
| `AGENT_LLM_MODEL` | Main agent model |
| `AGENT_LLM_MODEL_LITE` | Cheaper model for background agents |
| `LLM_PROVIDER` | Default provider for reports |
| `AUTH_SECRET_KEY` | JWT signing key for auth |

You can also set different models for each workflow step from the Settings page.

---

## Main Features

- **Universal input**: paste almost any scenario, article, memo, or story.
- **Automatic actor discovery**: finds visible and hidden stakeholders.
- **Knowledge graph**: shows entities and relationships behind the simulation.
- **Agent-based simulation**: runs many agents with different incentives and memories.
- **Belief and faction dynamics**: tracks how views spread, harden, or split.
- **Shock testing**: inject policy, market, social, or narrative shocks.
- **What-if branches**: compare alternative timelines.
- **Probability bands**: read uncertainty instead of a single fake-certainty answer.
- **Explainable reports**: generate reports that show reasoning and evidence.
- **Agent interviews**: ask simulated agents why they acted or changed beliefs.
- **Runtime settings**: change API keys, models, and presets without restarting.

---

## Example Use Cases

| Area | Example |
|---|---|
| Policy | “What groups may support or oppose this housing policy?” |
| Markets | “How could a sudden rate hike affect investor sentiment?” |
| Companies | “How may customers, suppliers, and competitors react to a new entrant?” |
| Geopolitics | “Which actors may escalate, de-escalate, or hedge after this event?” |
| Public narrative | “How might a message spread across communities?” |
| Fiction and worldbuilding | “How would factions in this story respond to a major shock?” |
| Research | “Which assumptions matter most in this scenario?” |

---

## Simulation Presets

| Preset | Agents | Rounds | Best for |
|---|---:|---:|---|
| FAST | 100 | 15 | Quick demos and smoke tests |
| STANDARD | 300 | 20 | General analysis |
| DEEP | 500 | 30 | More detailed research runs |
| LARGE | 1,000 | 25 | Larger stress tests |
| MASSIVE | 3,000 | 20 | Heavy simulations |
| custom | up to 50,000 | up to 100 | Advanced experiments |

Note: the OASIS simulation engine currently requires Python 3.10 or 3.11. On Python 3.12+, the UI will gracefully disable the Simulation step instead of crashing.

---

## Project Structure

```text
backend/
  app/api/          FastAPI routes
  app/services/     simulation, graph, report, settings, and analytics logic
  app/models/       Pydantic request and response models
  app/utils/        database, LLM, logging, and security helpers
  database/         SQLite schema
  tests/            pytest tests

frontend/
  src/views/        main pages
  src/components/   reusable UI components
  src/api/          frontend API clients
  src/i18n/         Traditional Chinese and English copy

data/
  benchmarks/       benchmark fixtures
```

---

## Useful Commands

```bash
make test          # unit tests
make test-int      # integration tests
make test-all      # full test suite
make test-cov      # coverage report
make test-changed  # tests related to changed files
```

Frontend:

```bash
cd frontend
npm run build
npm run dev
```

---

## Release Status

This repository is close to a public source release, but it is not currently an npm/PyPI package.

Current distribution path:

- clone the repository
- run locally with `make quickstart`
- or run with Docker Compose

Package publishing would need a separate packaging pass, including package entrypoints, published artifacts, versioning rules, and registry metadata.

---

## Important Limits

Murmura is for exploration, research, and scenario stress-testing. It is not a replacement for professional judgment.

Do not use it as the only basis for:

- financial trading
- legal advice
- medical decisions
- safety-critical decisions
- regulatory or actuarial reporting

Good simulations need good input. Include context, time horizon, actors, uncertainty, and the question you actually care about.

---

## License

Prosperity Public License 2.0.0.

Non-commercial personal, academic, and non-profit use is permitted. Commercial or revenue-generating use requires a separate commercial license.

Copyright © 2026 destinyfrancis. All rights reserved.
