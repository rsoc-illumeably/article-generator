# article-generator

A personal, internal Python service that generates fact-checked articles using a two-agent LLM loop (Writer + Judge). Containerized with Docker and deployable to a Digital Ocean Droplet. Accessible via curl or a browser UI.

---

## Implementation Status

| Layer | Status |
|---|---|
| FastAPI app, config loader, Pydantic schemas | Done |
| X-API-Key authentication | Done |
| LLM abstraction (interface, Anthropic client, factory) | Done |
| Writer agent | Done |
| Judge agent (YAML verdict, web search) | Done |
| Writer→Judge loop | Done |
| `POST /api/generate` (fully wired) | Done |
| Browser UI (session auth, frontend routes, Tailwind UI) | Not yet implemented |

---

## Repository Structure

```
article-generator/
├── Dockerfile                     # Python image; runs uvicorn
├── docker-compose.yml             # Local dev — FastAPI only, port 8000, no SSL
├── docker-compose.prod.yml        # Production — nginx + self-signed SSL, port 443
├── .env.example                   # Required env var template; copy to .env
├── .gitignore                     # Excludes .env, certs/, __pycache__, etc.
├── requirements.txt               # Python dependencies
├── requirements-dev.txt           # Test dependencies (pytest, httpx)
├── pytest.ini                     # Pytest config — sets project root on sys.path
├── setup_ssl.sh                   # Generates self-signed SSL cert into certs/
├── README.md                      # This file
│
├── scripts/
│   └── check_api.py               # Live connectivity check: verifies API key + provider reachability
│
├── tests/
│   ├── conftest.py                # Shared fixtures: TestClient, TEST_API_KEY, MockLLMClient
│   ├── test_auth.py               # X-API-Key authentication tests
│   ├── test_health.py             # GET /health endpoint tests
│   ├── test_writer.py             # WriterAgent unit tests (mocked LLM)
│   └── test_judge.py              # JudgeAgent unit tests + _parse_verdict error cases (mocked LLM)
│
├── src/
│   ├── main.py                    # FastAPI app factory; all routes defined here
│   ├── config.py                  # Loads YAML configs and exposes typed dataclasses
│   │
│   ├── api/
│   │   └── auth.py                # FastAPI dependency: validates X-API-Key header
│   │
│   ├── frontend/                  # NOT YET IMPLEMENTED — stubs only
│   │   ├── routes.py              # GET / (UI or login), POST /session (password submit)
│   │   ├── session.py             # In-memory session store for browser auth
│   │   └── templates/
│   │       └── index.html         # Single-page Tailwind UI
│   │
│   ├── agents/
│   │   ├── writer.py              # Writer agent: builds prompt, calls LLM, returns draft
│   │   ├── judge.py               # Judge agent: fact-checks via web search, parses YAML verdict
│   │   └── loop.py                # Writer→Judge iteration loop; returns GenerateResponse or ErrorResponse
│   │
│   ├── llm/
│   │   ├── interface.py           # Abstract LLM base class (provider-agnostic)
│   │   ├── factory.py             # Instantiates the configured LLM client from config/app.yml
│   │   └── anthropic_client.py    # Concrete Anthropic/Claude implementation
│   │
│   └── models/
│       └── schemas.py             # Pydantic request/response models
│
├── config/
│   ├── app.yml                    # LLM provider, model name, max iteration cap
│   ├── writer_prompt.yml          # Writer system prompt + article structure rules
│   └── judge_prompt.yml           # Judge system prompt + acceptance criteria
│
├── nginx/
│   └── nginx.conf                 # SSL termination → proxy_pass to FastAPI
│
└── certs/
    └── .gitkeep                   # Directory tracked; cert files are gitignored
```

---

## Local Setup

**Prerequisites:** Docker and Docker Compose installed.

1. Clone the repo:

   ```bash
   git clone <repo-url>
   cd article-generator
   ```

2. Create your `.env` from the example:

   ```bash
   cp .env.example .env
   # Open .env and fill in your API keys and passwords.
   ```

3. Start the service and run detached:

   ```bash
   docker compose up --build -d
   ```

4. Confirm the service is running:

   ```bash
   curl http://localhost:8000/health
   ```

5. To stop the service:

   ```bash
   docker compose down
   ```

**Note:** Changes to `.env` are picked up when the container is recreated (`docker compose up`), not just restarted (`docker compose restart`). Rebuilding (`--build`) is only needed when `requirements.txt` or the `Dockerfile` changes.

---

## Droplet Deployment

1. SSH into your Droplet and clone the repo:

   ```bash
   git clone <repo-url>
   cd article-generator
   ```

2. Create your `.env`:

   ```bash
   cp .env.example .env
   nano .env  # fill in your secrets
   ```

3. Generate the self-signed SSL certificate (run once):

   ```bash
   chmod +x setup_ssl.sh
   ./setup_ssl.sh
   ```

4. Start the production stack and run detached:

   ```bash
   docker compose -f docker-compose.prod.yml up -d --build
   ```

5. Access at `https://YOUR_DROPLET_IP`.
   Your browser will warn about the self-signed certificate — this is expected. Proceed past the warning.

---

## Running Tests

Tests run locally against the FastAPI app directly — no Docker required.

**Prerequisites:** Python 3.12+ with a virtual environment.

1. Create and activate a virtual environment (first time only):
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

2. Install all dependencies:
   ```bash
   pip install -r requirements.txt -r requirements-dev.txt
   ```

3. Run the full test suite:
   ```bash
   pytest
   ```

4. Run with verbose output to see each test name:
   ```bash
   pytest -v
   ```

5. Run a single test file:
   ```bash
   pytest tests/test_auth.py
   pytest tests/test_health.py
   pytest tests/test_writer.py
   pytest tests/test_judge.py
   ```

**What the tests currently cover:**

| File | Tests | What is verified |
|---|---|---|
| `tests/test_auth.py` | 4 | Missing key → 401; wrong key → 401; correct key → 200; 401 body includes `detail` field |
| `tests/test_health.py` | 2 | Returns 200; response shape contains status, provider, model, max_iterations |
| `tests/test_writer.py` | 8 | Return value; single LLM call; topic in prompt; no leftover placeholder; feedback injection; feedback header absent without feedback; article rules in prompt; no tools passed |
| `tests/test_judge.py` | 9 | Web search tool passed; topic and article in prompt; YAML pass verdict; YAML fail verdict with annotations; raises on malformed YAML; raises on non-mapping; raises on missing verdict field; raises on invalid verdict value; raises on non-list annotations |

**Note on `test_auth.py`:** `test_correct_key_returns_200` sends a real request to `POST /api/generate`, which now calls the full agent loop. This test will fail without `ANTHROPIC_API_KEY` set in the test environment. This test needs to be updated now that the route is wired — it is a known pending fix.

Agent tests (`test_writer.py`, `test_judge.py`) do not require a real `.env` file — they use `MockLLMClient` from `conftest.py`. Auth and health tests inject a dummy `API_KEY` via `monkeypatch`.

---

## Checking API Connectivity

Before deploying, verify that your API key is valid and the configured provider is reachable.

**Prerequisites:** Virtual environment active with dependencies installed.

1. Activate the virtual environment:
   ```bash
   source .venv/bin/activate
   ```

2. Run the script from the project root:
   ```bash
   python scripts/check_api.py
   ```

The script reads the active provider and model from `config/app.yml`, auto-loads credentials from `.env`, instantiates the configured LLM client, sends a single minimal completion request, and reports pass or fail.

**Expected output on success:**
```
Provider : anthropic
Model    : claude-sonnet-4-6

  Instantiating AnthropicClient...
  Sending minimal completion request...
  Response: 'OK'

[PASS] API call succeeded.
```

**Failure modes:**

| Output | Cause | Fix |
|---|---|---|
| `[FAIL] Missing environment variable: 'ANTHROPIC_API_KEY'` | Key absent from `.env` | Add `ANTHROPIC_API_KEY` to `.env` |
| `[FAIL] No connectivity check implemented for provider '...'` | `config/app.yml` names an unsupported provider | Correct the provider name or implement a check for it |
| `[FAIL] <API error message>` | Key present but invalid, or provider unreachable | Verify the key is correct and the provider API is up |

---

## Making Requests with curl

The `POST /api/generate` endpoint is fully implemented. It runs the Writer→Judge loop and returns either a success response (article passed fact-checking) or an error response (iteration cap reached without passing).

**Generate an article (concise response):**

```bash
curl -X POST https://YOUR_DROPLET_IP/api/generate \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{"topic": "The history of the Roman Empire", "verbose": false}'
```

**Generate with full verbose output (iteration history included):**

```bash
curl -X POST https://YOUR_DROPLET_IP/api/generate \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{"topic": "The history of the Roman Empire", "verbose": true}'
```

**With dev mode enabled (includes per-iteration agent trace):**

```bash
curl -X POST https://YOUR_DROPLET_IP/api/generate \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{"topic": "The history of the Roman Empire", "verbose": true, "dev_mode": true}'
```

For local development, replace `https://YOUR_DROPLET_IP` with `http://localhost:8000`.

> **Note:** The self-signed cert will cause curl to fail with an SSL error.
> Add `-k` to skip cert verification for local testing against the prod stack:
> `curl -k -X POST https://YOUR_DROPLET_IP/api/generate ...`

**Success response shape (`verbose: false`):**
```json
{
  "success": true,
  "article": "<full article text>",
  "iterations": 2,
  "history": null
}
```

**Success response shape (`verbose: true`):**
```json
{
  "success": true,
  "article": "<full article text>",
  "iterations": 2,
  "history": [
    {
      "iteration": 1,
      "writer_output": "<first draft>",
      "judge_verdict": "fail",
      "judge_annotations": ["Claim X is unverified.", "Missing conclusion."]
    },
    {
      "iteration": 2,
      "writer_output": "<revised draft>",
      "judge_verdict": "pass",
      "judge_annotations": []
    }
  ]
}
```

**Error response (iteration cap reached):**
```json
{
  "success": false,
  "error": "Article did not pass after 5 iterations.",
  "iterations": 5,
  "history": [...]
}
```

---

## Using the Browser UI

> **Not yet implemented.** The frontend layer (`src/frontend/`) is scaffolded but not built. Access the service via curl until the browser UI is complete.

When implemented, the browser UI will work as follows:

1. Navigate to `http://localhost:8000` (local) or `https://YOUR_DROPLET_IP` (prod).
2. Enter the session password set in your `.env` to unlock the UI.
3. Type a topic in the text box, or upload a `.txt` file — the file's contents are loaded into the topic field and treated identically to typed input.
4. Toggle **Verbose** to include the full iteration history in the response.
5. Toggle **Dev Panel** to see the turn-by-turn agent interaction rendered after the article loads.
6. Click **Generate** and wait. Results appear in the output area below.

---

## Updating Prompts and Article Rules

All prompts and structural rules live in `config/`. Editing these files never requires a code change.

| What you want to change                                   | File to edit                                      |
| --------------------------------------------------------- | ------------------------------------------------- |
| Writer's system prompt                                    | `config/writer_prompt.yml` → `system_prompt`      |
| Article max word/paragraph count, required sections, tone | `config/writer_prompt.yml` → `article_rules`      |
| Judge's system prompt                                     | `config/judge_prompt.yml` → `system_prompt`       |
| Judge's acceptance criteria                               | `config/judge_prompt.yml` → `acceptance_criteria` |
| LLM provider or model                                     | `config/app.yml` → `llm`                          |
| Max Writer→Judge iterations before error                  | `config/app.yml` → `agent.max_iterations`         |

After editing any config file, restart the service:

```bash
# Local
docker compose up --build

# Production
docker compose -f docker-compose.prod.yml up -d --build
```

---

## Secrets Reference

All secrets live in `.env` (never committed). See `.env.example` for the full list.

| Variable                    | Description                                                    |
| --------------------------- | -------------------------------------------------------------- |
| `ANTHROPIC_API_KEY`         | Anthropic API key for Claude                                   |
| `API_KEY`                   | Static key required in the `X-API-Key` header for API requests |
| `FRONTEND_SESSION_PASSWORD` | Password entered in the browser to unlock the UI (not yet active) |
