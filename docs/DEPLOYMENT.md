# Operating Waypoint

## Supported deployment

Python 3.13, Linux Docker host, one web container, one worker and Caddy. Both application processes share a named local Docker volume. SQLite runs in WAL mode with foreign keys and a 10-second busy timeout. Do not run this volume on NFS or across hosts. No claim of 5,000 simultaneous users is made.

The old Streamlit startup command is replaced by `uvicorn app:create_app --factory`. Keep the historical database separately; it contains no reliable per-person ownership to migrate automatically.

## Required configuration

Copy `.env.production.example` to a private `.env.production`; fill it before starting. The example values are not credentials. The application refuses production demo mode, missing flight/mail configuration, HTTP base URLs, and a missing/short/example secret.

| Variable | Meaning |
|---|---|
| `DOMAIN` | Public DNS hostname used by Caddy; must match `BASE_URL` |
| `APP_ENV` | `production` for public deployment |
| `FLIGHT_PROVIDER` | `live` in production; `demo` permitted only locally |
| `BASE_URL` | Public HTTPS origin, used in private email links and origin validation |
| `DATABASE_PATH` | `/app/data/travel.db` in Compose |
| `APP_SECRET` | Random secret of 32+ characters; generate using `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `SERP_API_KEY` | Flight provider credential; confirm commercial/data usage rights with your provider |
| `OPENAI_API_KEY` | Optional; enables natural-language extraction |
| `OPENAI_MODEL` | Structured-output-capable model; default `gpt-4o-mini` |
| `DAILY_PROVIDER_LIMIT` | Shared UTC-day flight request ceiling; default 500; each attempt consumes budget |
| `ALERT_INTERVAL_SECONDS` | Route check interval; default 43200; minimum 3600 |
| `SMTP_HOST`, `SMTP_PORT` | Submission server supporting STARTTLS; default port 587; implicit TLS/465 is not supported |
| `SMTP_USERNAME`, `SMTP_PASSWORD` | SMTP authentication if the configured server requires it |
| `MAIL_FROM` | Authorized sending email address; configure SPF/DKIM/DMARC at your mail provider |

## Start

Point your DNS record at the host and allow inbound 80/443. Install Docker Engine with Compose. The application port is intentionally not published; only Caddy accepts external requests.

```sh
docker compose --env-file .env.production config --quiet
docker compose --env-file .env.production up --build -d
docker compose --env-file .env.production ps
```

Caddy obtains HTTPS certificates when DNS and connectivity allow it. The web process trusts forwarding headers because it is reachable only on the private Compose network. Do not publish port 8000 or use `--forwarded-allow-ips '*'` on an exposed server. Configure separate host firewall and monitoring controls for your environment.

The image runs as UID/GID 10001, drops capabilities and uses a read-only root filesystem. Data and temporary directories remain writable. Python dependencies are pinned in `requirements.lock`. Container base/proxy images must be scanned and updated during maintenance; a Python dependency audit is not a container audit.

## Release gates on the deployed host

1. Production configuration validation succeeds; demo mode does not start.
2. `/health/live` returns 200. `/health/ready` returns 200 after the worker starts. Readiness checks configuration, DB access and recent worker heartbeat, **not live provider connectivity or SMTP deliverability**.
3. Register an account, receive a real verification email and verify it. Test sign-in, logout and password reset, including expiry and session revocation.
4. Perform real searches for nonstop and connecting routes, airline and total budget filters. Confirm prices, passenger totals and dates against provider output; confirm the external link is a route search.
5. Create an alert with a matching target; verify its real search and actual email delivery, then delete it. Test a provider failure and SMTP retry.
6. Test Arabic, English and phone layouts, keyboard navigation, empty and error states.
7. Run workload tests appropriate to your actual traffic and provider budget. Three watches × 5,000 users × two daily checks can imply 30,000 daily checks before deduplication; default 500/day is a cost guard, not capacity for that workload.
8. Complete a backup and restore drill, and connect an external uptime monitor to readiness. Review provider terms, privacy/support contact details and the licensing requirements applicable to your public service.

Do not promote the release to a public audience until these checks pass. Registration count is not a capacity benchmark.

## Scheduling, quotas and failure semantics

The worker polls every 15 seconds, handles up to 50 due alerts and 20 emails in a batch, and renews a 120-second SQLite lease before individual tasks. Run only one worker. A second worker is rejected while a valid lease exists; a crashed worker can be replaced after lease expiry.

Each account can have three active alerts. Email must be verified before creation. First matching fare or a lower matching fare after a later check queues an email. Trips that become invalid/past are deactivated. Search errors preserve the last successful price and retry after one hour. Search cache lasts 10 minutes; matching requests may reuse it. There is no exact-time notification guarantee under quota exhaustion or provider downtime.

Mail uses a durable outbox with up to five attempts and exponential backoff (60s, 120s, 240s, 480s, 960s). Exhausted messages remain visible to the operator in `outbox`. Delivery is **at least once**: a crash after SMTP acceptance and before DB commit can duplicate a message; deterministic Message-ID helps downstream deduplication but does not guarantee it. SMTP errors are logged by type without recipient, body, passwords or secret links.

Search limit: 30/account/hour and 60/IP/15 minutes. Login: 10/IP and 10/email/15 minutes. Registration: 5/IP/15 minutes. AI: 5/account/24h, 20/IP/15min and 100 globally/24h. Quotas persist across restart. Monitor false positives behind shared networks and tune code intentionally with tests.

## Logs and alerts

`logging.json` disables URL-level HTTP client/access logging so API keys and verification query strings do not enter normal application logs. Application request logs contain only generated request ID, method, path, status and elapsed milliseconds. Protect infrastructure access logs with the same rule. Configure log rotation and retention on the host.

Monitor readiness, HTTP error rate, provider failures/quota consumption, last successful alert checks, worker restarts, pending/exhausted outbox, disk space and backup age. Health endpoints do not expose credentials or user data. Sent outbox messages are removed after seven days by the worker; expired sessions, tokens, counters and cache are cleaned every cycle. Pending/failed mail requires operator review.

## Backups and restoration

Use the SQLite backup API, not a plain copy of the WAL-backed live `.db` file:

```sh
docker compose --env-file .env.production exec web python scripts/backup.py --source /app/data/travel.db --output /app/data/backups/travel-2026-10-17.db
```

Choose a fresh filename each time; the utility refuses overwrites and runs `PRAGMA integrity_check`. Schedule daily backups using your host scheduler, copy them encrypted off-host, and retain seven daily backups as an initial policy. The repository provides the backup utility, not an already-configured host scheduler or remote backup service. Restrict all volume/backup access: the DB contains emails and queued private links.

For a restore: stop web and worker, preserve the existing DB and its WAL/SHM files as a matched rollback set, restore a verified backup under `DATABASE_PATH`, ensure UID 10001 owns it, and restart both processes. Do not leave an old WAL/SHM file beside a restored database. Recheck account access, alerts, integrity and readiness. Restore first into a separate staging volume when possible. Account deletion removes active stored account data; backup deletion follows the documented retention policy.

## Updating and rollback

Back up before deployment, run CI checks, rebuild the images, and apply Compose. Schema version 1 initializes idempotently; an unknown future schema version refuses startup. Future schema changes require explicit versioned migrations and rollback testing. Keep previous image tags and compatible backups. The current repository does not automatically upgrade an old shared-user schema.
