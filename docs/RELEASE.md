# Release evidence — 2026-10-17

Status: local release candidate, not a live production deployment.

## Verified locally

- 50 automated tests passed without warnings on Windows / Python 3.13.1 after dependency updates. Measured coverage across application modules: 89.21% (667 statements; report under ignored `data/coverage.json`).
- Tests include two-account isolation, CSRF/origin rejection, credential redaction, password reset/session invalidation, token expiry/reuse, nonstop regression, filter correctness, provider failures/timeouts, cache/budget enforcement, worker alerts/retries/lease, structured AI extraction/refusal, and backup data integrity.
- Runtime dependency scan of the complete pinned `requirements.lock`: no known vulnerabilities reported by pip-audit on the verification date. This does not replace application security review or container image scanning.
- Public HTTP smoke: 200 requests, concurrency 10, zero failures; p50 68.13 ms, p95 127.87 ms, elapsed 1.55 s on the local preview. Only `/` and `/api/session` were measured. These are local observations, not a production SLA or flight-search/5,000-user benchmark.
- Ruff lint and formatting checks, JavaScript syntax check with Node, and Compose configuration validation passed.
- Browser review confirmed English/Arabic rendering, demo disclosure, local account sign-in, three flight cards, budget filtering to one matching fare, and verification gating before alert creation. Screenshots are in `docs/images/`. Phone-viewport verification remains a deployment gate.

## Not yet verified

- Docker build/runtime: Docker CLI is installed, but the Linux daemon was unavailable during inspection. A background Desktop startup was attempted; no successful image build/runtime is claimed. CI is configured to build the image; no successful CI run is claimed.
- Live SerpApi search, provider usage rights, live OpenAI extraction and actual SMTP inbox delivery.
- Public DNS, HTTPS certificate issuance, deployed-host restore drill, external monitoring, realistic traffic/load and independent security review.
- Commercial affiliate/booking partnership. The application opens an external route search only.

## Production release condition

Complete the [deployment gates](DEPLOYMENT.md#release-gates-on-the-deployed-host), record the actual host/domain and dated results, and attach a public URL before changing this status to deployed. Source-code readiness and local tests alone cannot prove a live production service.

## Account flow fix — 2026-10-17

- Full regression suite: 56 tests passed (six added password-boundary scenarios); Ruff lint/format and JavaScript syntax passed. The coverage percentage above belongs to the earlier measured 50-test run.
- Browser checks: Arabic short-password feedback and live character count, confirmation mismatch, registration-to-login transition with retained email, localized invalid-login feedback, successful sign-in and sign-out. A fictitious local account was used; no real email was sent.
- Registration keeps a generic response for both new and existing email addresses. Passwords remain 12–128 characters; verification is still required for email alerts. The UI explains development outbox delivery and does not promise an inbox email when SMTP is absent.
- Screenshot: [registration feedback](images/auth-registration-fixed.png).

Account feedback follow-up: registration delivery information is shown in registration only. The login form no longer retains registration feedback; editing auth fields clears previous messages. Browser checks confirmed registration-to-login transition, login-only credential errors, and error removal on input. Screenshot: images/auth-feedback-separated.png.
