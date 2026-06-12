# Security Policy

Murmura handles user-provided scenario text, model provider credentials, simulation output, and local database state. Please report security issues privately before opening a public issue.

## Supported Versions

The `main` branch and the latest published release are supported for security reports.

## Reporting a Vulnerability

Please email the maintainer or open a private GitHub security advisory if available.

Include:

- affected version or commit
- reproduction steps
- expected and actual behavior
- impact assessment
- suggested fix, if known

Do not include real API keys, production data, or private user data in a report.

## Security Scope

Relevant issues include:

- prompt injection or unsafe prompt construction
- secret leakage through logs, reports, WebSocket events, or API responses
- SSRF, unsafe model provider base URLs, or insecure connector behavior
- authentication or authorization bypasses
- unsafe file handling, path traversal, or local database exposure
- dependency vulnerabilities with a practical exploit path

## Maintainer Response

The maintainer aims to acknowledge valid reports within 7 days, provide an initial assessment within 14 days, and coordinate a fix or mitigation before public disclosure.

