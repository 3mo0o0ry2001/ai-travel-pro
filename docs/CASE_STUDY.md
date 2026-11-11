# Waypoint: from prototype to an operable flight discovery application

## Context

Personal engineering project. The starting application combined a Streamlit UI, an LLM tool-calling function, a flight-search API and SQLite. Weather was hardcoded, price monitoring saved rows without running checks, all users shared `user_1`, and error responses could be mistaken for empty flight results.

## Engineering decisions

1. **Keep the model out of authoritative decisions.** Optional structured extraction proposes validated form fields. Dates, budget, airline and nonstop requirements are enforced by application code; prices come from the flight provider.
2. **Make identity explicit.** Separate accounts, hashed passwords/session tokens, verified email, scoped alert access, password reset and account deletion replace shared preferences.
3. **Separate scheduled work from web requests.** A leased worker and durable outbox persist alert checks and email retries across restarts.
4. **Treat usage as a resource.** Persistent per-user/IP limits, a global flight-request budget and a 10-minute cache constrain paid API calls. Alert cadence is published instead of promising continuous monitoring.
5. **Make release claims measurable.** Real-database integration tests, network-boundary mocks, dependency audit, HTTP load smoke, health endpoints and backup checks provide evidence. Live-provider and deployment checks remain explicit release gates.
6. **Match the operating model to the scope.** A single-host SQLite deployment is simple and recoverable for a portfolio release. Horizontal deployment would require a different shared datastore and coordinated queue; it is not claimed here.

## Demonstration walkthrough

- Show English and Arabic layouts and the persistent demo banner.
- Register two accounts and demonstrate that their alerts are isolated.
- Search DXB → CAI, sort by duration, and apply a total-budget/nonstop filter.
- Show that provider failure is a service error, not “no flights”.
- Verify email using a development outbox, create an alert and run one worker cycle.
- Demonstrate token reuse rejection, account deletion and a verified DB backup.
- Present [release evidence](RELEASE.md), including the difference between offline tests and live service validation.

## Scope boundaries

No payment collection, ticket issuance/refunds, confirmed commercial partner integration, live weather or calendar access. The onward link opens an external route search. Demo prices are labelled and forbidden in production configuration. A deployed release must use real API/SMTP credentials and pass the deployment guide's gates.
