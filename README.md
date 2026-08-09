# HR AI Agents

A full-stack hackathon project that combines three specialized AI agents into a single candidate-analysis workflow. It enriches a candidate profile with public web context, analyzes an uploaded interview recording, and produces a structured summary for a human HR reviewer.

This is decision-support software, not an autonomous hiring system. Its output should be reviewed by a person and should never be the sole basis for an employment decision.

[Live demo](https://hr-ai-agents.onrender.com)

Originally built in April 2026. Security controls, automated tests, CI, and portfolio documentation were added in August 2026.

## Workflow

```text
Candidate details
      |
      +---- Agent 1: Tavily web research + Gemini profile analysis
      |
Audio interview
      |
      +---- Agent 2: audio analysis
                    |
                    v
          Agent 3: consolidated HR assessment
                    |
                    v
        Validated dashboard-ready JSON
```

The web and audio agents run concurrently. A final agent combines their outputs, and a deterministic validator checks status values, score ranges, and all required graph fields before the response is shown.

## Stack

- FastAPI, Python 3.12, Pydantic, HTTPX
- Gemini, Tavily, and Groq integrations
- React 19, TypeScript, Vite, Material UI, and Recharts
- Docker and Render deployment configuration
- Optional n8n webhook and email notifications

## Privacy and security

- Candidate storage is disabled by default with `STORE_CANDIDATES=false`.
- When enabled, the in-memory store is capped at 100 records and is cleared whenever the process restarts.
- `/candidates` always requires an `X-Admin-Key` header and a configured `CANDIDATES_ADMIN_KEY`.
- Analysis endpoints support an optional `X-Analysis-Key` when `ANALYSIS_ACCESS_KEY` is configured.
- CORS is restricted through `ALLOWED_ORIGINS`; it is not open to every origin.
- Audio uploads are restricted to supported media types and 10 MB.
- API failures return generic messages instead of raw provider exceptions.
- The SPA fallback prevents paths from escaping the `static` directory.

Do not submit real candidate information to a demo deployment without consent and an approved data-handling policy.

## Run locally

1. Copy `.env.example` to `.env` and add your own development credentials.
2. Install the locked Python dependencies and start the API:

```powershell
pip install uv
uv sync --frozen
uv run uvicorn main:app --reload --port 8080
```

3. In another terminal, start the frontend:

```powershell
cd frontend
npm ci
npm run dev
```

The Vite development server proxies API requests to `http://localhost:8080` by default.

## Configuration

Required for the complete three-agent flow:

- `GEMINI_API_KEY_3`, `GEMINI_API_KEY_4`, `GEMINI_API_KEY_5`
- `TAVILY_API_KEY`

Optional controls and integrations:

- `ANALYSIS_ACCESS_KEY`
- `CANDIDATES_ADMIN_KEY`
- `STORE_CANDIDATES`
- `ALLOWED_ORIGINS`
- `N8N_WEBHOOK_URL`
- `EMAIL_FROM`, `EMAIL_PASSWORD`, `EMAIL_TO`

No real credentials belong in Git. `.env.example` documents names only.

## Quality checks

```powershell
uv run python -m unittest discover -s tests -v
cd frontend
npm run check
```

GitHub Actions runs Python syntax checks, backend unit tests, frontend lint, and a production frontend build on every push and pull request.
