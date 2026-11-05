# PKG-03 — Secure configuration

Scope: issue #14; backend, official Android (`mobile/vytal-app/`), web and CI.
No deployment, migration, credential rotation or production configuration change is included.

## Audit and controls

| Area | Observed behavior before PKG-03 | Required behavior now |
| --- | --- | --- |
| Backend environment | Missing environment selected local; dotenv loaded implicitly | Process must explicitly select a supported environment; unknown/missing names fail. Only explicit local/dev/development loads dotenv; managed Cloud Run cannot select local/test. |
| Signing and OAuth secrets | Shared development signing defaults; plain settings representations | Production/staging require explicit non-placeholder secrets; signing keys have no static default. Secret settings are masked. Local/test omission generates independent random ephemeral keys. |
| OAuth/CORS | Local callback and wildcard CORS available by fallback | Production requires explicit HTTPS OAuth callback and rejects local/credential-bearing URLs; CORS defaults to deny and accepts explicit HTTPS origins. |
| Persistence selection | Missing YAML silently selected local storage | Production requires explicit CONFIG_PATH, existing YAML and provider. Explicit local provider remains supported; no infrastructure migration is implied. |
| Demo authentication | Anonymous seed could use a shared embedded password | Disabled by default; explicit local/test opt-in and private configured password required. Production/staging reject seed configuration and route access before persistence. No credentials prefilled in web login; demo controls appear only in development. |
| Android transport | Embedded production/private LAN fallback | Public endpoint configured explicitly for release; non-local HTTPS required. Local fallback only in development. Same pure validator used by Expo configuration and runtime. |
| Web transport | Production rewrite silently targeted localhost | Server-only VYTAL_BACKEND_URL required for production build/start; explicit non-local HTTPS origin. Local fallback retained for development/test. |
| Public frontend environment | No guard against credential-shaped public variables | EXPO_PUBLIC_/NEXT_PUBLIC_ secret/token/password/private-key/credential names fail configuration without printing values. This complements review; it cannot identify arbitrarily named secrets. |
| Logging | Provider error body and discarded pipeline payload could be logged | Provider status and pipeline stage/exception type only; no response body, rejected event, identifier or exception text. JWT failure detail is generic. |
| CI | Existing auth regressions and builds | Configuration negative tests included in backend/Android/web suites; builds use synthetic HTTPS endpoints, no production credentials. Push checks cover codex branches so automatic PR creation does not skip CI. |

## Local setup and compatibility

Copy the component `.env.example` to a private `.env` if needed. Backend launch must explicitly set `ENVIRONMENT=local` in the process (dotenv cannot choose it), with local OAuth configuration. Tests use `ENVIRONMENT=test` and synthetic OAuth values; they do not read dotenv. Existing v1 schemas/authentication and account/session authorization stay unchanged. Do not log settings via `get_secret_value()`.

Omitting local signing keys intentionally invalidates existing local tokens on restart. Supply private stable keys through the local environment when persistence across restarts is required. Do not copy those keys into templates. Demo seed requires explicit `ALLOW_DEV_SEED=true`, private `DEMO_PASSWORD` (existing minimum 8 characters), optionally `DEMO_EMAIL`; otherwise use normal registration. Do not expose development servers to shared environments.

Android development uses Expo's development mode; configure `EXPO_PUBLIC_API_URL` for the host/emulator (Android emulator normally `http://10.0.2.2:8000/api/v1`). Release exports require `NODE_ENV=production` and an explicit HTTPS API URL. Web `npm run dev` uses localhost:8003 unless a server-only rewrite origin is configured; production `npm run build` and `npm start` require an explicit HTTPS `VYTAL_BACKEND_URL`. These endpoint values are configuration, not credentials.

Production/staging backend startup requires process ENVIRONMENT, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, SECRET_KEY, JWT_SECRET_KEY, GOOGLE_REDIRECT_URI and CONFIG_PATH. Configure CORS_ORIGINS as a JSON array only when browser cross-origin access is needed. Existing HS256 and token lifetimes remain, with invalid/nonpositive lifetime values rejected. Provision/verify configuration before rollout; this PR does not authorize rollout or mutate deployed secrets. Existing deployment definitions are audited but unchanged; they must supply all required settings or startup fails closed.

## Validation and limitations

Regression coverage includes missing/unknown environment, copied dotenv, managed-runtime local mode, unsafe production secrets, redirects/CORS, unsupported JWT algorithm, invalid lifetimes, seed access before DB, masked representations/errors, provider response and dead-letter payload logging, frontend production URL/credential rejection, and legitimate local/HTTPS configurations. Existing auth/account isolation and refresh regressions remain enabled. OpenAPI comparison guards public v1 schemas.

No actual secrets are printed, rotated or added to CI. No live production/GCP calls or native device release signing are required to validate this policy. Secret-name checks and known-placeholder rejection cannot prove arbitrary credential strength or detect secrets under unrelated names; use the existing secret management process and code review. No claim is made that deployment settings or real credentials have been verified. Android validation exports a Hermes bundle, not a signed APK. Production approval remains separate.

## Local evidence before publication

- Backend: 311 tests passed; 78.62% application coverage (existing threshold 30%). Includes isolated BigQuery SDK, API account-isolation/refresh and 58 configuration/logging tests.
- Official Android: 32 authentication/session tests plus 20 configuration tests passed; real Android client/FastAPI/JWT/SQLite integration passed; scoped ESLint and TypeScript passed; release Hermes bundle exported with a synthetic HTTPS endpoint.
- Web: 21 authentication/session tests plus 21 configuration tests passed; clean `npm ci`, TypeScript and production Next build passed with Node 22/npm 10 and a synthetic HTTPS upstream.
- Public OpenAPI comparison against master passed. Scoped backend Ruff and pipeline syntax/import lint passed; intentional pipeline import bootstrap uses E402 exclusion. `pip check` passed.
- Tracked source/workflow credential-pattern scan (private-key headers, GitHub tokens, Google API keys, AWS access keys) found no matches; excludes generated web build artifacts and does not claim exhaustive credential detection.
- Remote checks are authoritative for the pushed SHA and are reported separately; no production calls, signed native build, merge or deployment performed.
