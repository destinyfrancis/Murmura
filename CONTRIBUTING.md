# Contributing to Murmura

Thanks for helping improve Murmura. This project is a universal prediction workbench built with FastAPI, Vue, SQLite, and an OASIS-based agentic simulation engine.

## Ways to Contribute

- Fix bugs in graph building, simulation orchestration, report generation, settings, or the frontend workbench.
- Add or improve tests for backend services, API routes, domain packs, and frontend build behavior.
- Improve documentation, setup instructions, demo scenarios, and examples.
- Add domain packs, benchmark fixtures, or evaluation cases that make scenario simulation more reliable.
- Improve provider compatibility, cost controls, observability, and security hardening.

## Before You Start

Use Python 3.10 or 3.11. The OASIS simulation dependency is not compatible with Python 3.12+.

```bash
git clone https://github.com/destinyfrancis/Murmura.git
cd Murmura
make quickstart
```

For daily development:

```bash
make start
make stop
```

## Development Checks

Run the focused check for your change when possible:

```bash
make test
make test-int
make test-all
make test-changed
```

Frontend:

```bash
cd frontend
npm ci
npm run build
```

## Pull Request Guidelines

- Keep pull requests focused on one behavior or one documentation improvement.
- Include tests for backend behavior changes and meaningful regression fixes.
- Keep UI copy in `frontend/src/i18n/zh-TW.js` and `frontend/src/i18n/en-US.js`; do not hardcode visible strings.
- Do not commit `.env`, API keys, local databases, generated reports, logs, build output, coverage output, or vector stores.
- Explain the user-facing impact, verification commands, and any known limits in the pull request description.

## Code Style

- Backend code should use async handlers and `aiosqlite` for database access.
- Prefer frozen dataclasses and frozen Pydantic models for domain data.
- Sanitize user-provided scenario text with the helpers in `backend/app/utils/prompt_security.py`.
- Never expose raw exception strings in API responses.
- Frontend timers and WebSocket reconnect loops must clean up on unmount.

## Security

Please report vulnerabilities privately using the process in [SECURITY.md](SECURITY.md).

