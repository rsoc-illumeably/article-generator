# article-generator

A personal, internal Python service that generates fact-checked articles using a two-agent LLM loop (Writer + Judge). Containerized with Docker and deployable to a Digital Ocean Droplet. Accessible via curl or a password-protected browser UI.

---

## Implementation Status

| Layer | Status |
|---|---|
| FastAPI app, config loader, Pydantic schemas | Done |
| X-API-Key authentication | Done |
| LLM abstraction (interface, Anthropic client, factory) | Done |
| Writer agent | Done |
| Judge agent (structured verdict via tool_use, web search) | Done |
| Writer→Judge loop | Done |
| `POST /api/generate` — submit job, returns `job_id` immediately | Done |
| `GET /api/status/{job_id}` — poll live progress and retrieve result | Done |
| Browser UI (session password gate, Tailwind UI, polling progress) | Done |

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
│   ├── check_api.py               # Live connectivity check: verifies API key + provider reachability
│   ├── check_writer.py            # Live Writer agent check: initial draft + feedback revision
│   └── check_judge.py             # Live Judge agent check: valid article + flawed article (expects fail)
│
├── tests/
│   ├── conftest.py                # Shared fixtures: TestClient, TEST_API_KEY, MockLLMClient
│   ├── test_auth.py               # X-API-Key authentication tests
│   ├── test_health.py             # GET /health endpoint tests
│   ├── test_writer.py             # WriterAgent unit tests (mocked LLM)
│   ├── test_judge.py              # JudgeAgent unit tests (mocked LLM, two-call flow)
│   └── test_loop.py               # Loop unit tests: termination, feedback threading, history flags
│
├── src/
│   ├── main.py                    # FastAPI app; routes, in-memory job store, thread pool
│   ├── config.py                  # Loads YAML configs and exposes typed dataclasses
│   │
│   ├── api/
│   │   └── auth.py                # FastAPI dependency: validates X-API-Key header
│   │
│   ├── frontend/
│   │   ├── routes.py              # GET / (login or UI), POST /session (password submit)
│   │   ├── session.py             # In-memory session store for browser auth
│   │   └── templates/
│   │       ├── login.html         # Password gate page
│   │       └── index.html         # Single-page Tailwind UI with polling progress
│   │
│   ├── agents/
│   │   ├── writer.py              # Writer agent: builds prompt, calls LLM, returns draft
│   │   ├── judge.py               # Judge agent: call 1 web search, call 2 forced tool verdict
│   │   └── loop.py                # Writer→Judge loop; writes live status to job dict
│   │
│   ├── llm/
│   │   ├── interface.py           # Abstract LLM base class: complete() + complete_structured()
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
   pytest tests/test_loop.py
   ```

**What the tests currently cover:**

| File | Tests | What is verified |
|---|---|---|
| `tests/test_auth.py` | 4 | Missing key → 401; wrong key → 401; correct key → 200 with `job_id` (executor patched); 401 body includes `detail` field |
| `tests/test_health.py` | 2 | Returns 200; response shape contains status, provider, model, max_iterations |
| `tests/test_writer.py` | 8 | Return value; single LLM call; topic in prompt; no leftover placeholder; feedback injection; feedback header absent without feedback; article rules in prompt; no tools passed |
| `tests/test_judge.py` | 7 | Web search tool on call 1; topic and article in prompt; verdict tool on call 2; research threaded into verdict call; pass verdict; fail verdict with annotations |
| `tests/test_loop.py` | 11 | Pass on iteration 1; pass on iteration 2; error after cap; first writer call has no feedback; annotations threaded to next writer call; feedback replaced each round; draft flows writer→judge; verbose=false omits history; verbose=true populates history; error always includes history; IterationRecord fields correct |

No test requires a real `.env` file or live API calls. `conftest.py` injects a dummy `API_KEY` via `monkeypatch`, provides `MockLLMClient` (which stubs both `complete` and `complete_structured`) for agent tests, and `test_loop.py` uses its own `MockWriterAgent` and `MockJudgeAgent`.

---

## Live Checks

Three scripts make real API calls to verify the service end-to-end. None of these are part of the `pytest` suite — run them manually from the project root with the virtual environment active.

**Prerequisites:** Virtual environment active, `.env` present with `ANTHROPIC_API_KEY` set.

---

### `check_api.py` — Provider connectivity

Verifies the API key is valid and the configured provider is reachable. Makes a single minimal completion request.

```bash
python scripts/check_api.py
```

**Expected output on success:**
```
Provider : anthropic
Model    : claude-sonnet-4-6

  Instantiating AnthropicClient...
  Sending minimal completion request...
  Response: 'OK'

[PASS] API call succeeded.
```

---

### `check_writer.py` — Writer agent

Verifies the Writer agent produces a non-empty draft and correctly incorporates Judge feedback on revision.

```bash
python scripts/check_writer.py
```

Two checks run in sequence:
1. **Initial draft** — calls `writer.write(topic=...)` with no feedback; asserts a non-empty response is returned and prints the full draft
2. **Feedback revision** — calls `writer.write(topic=..., feedback=[...])` with two specific annotations; asserts a non-empty revision is returned and prints it

---

### `check_judge.py` — Judge agent

Verifies the Judge agent returns a structurally valid verdict and correctly flags a factually flawed article. Uses web search — each check takes longer than the other scripts.

```bash
python scripts/check_judge.py
```

Two checks run in sequence:
1. **Factually sound article** — judges an accurate Apollo 11 article; asserts the verdict is `"pass"` or `"fail"` and annotations is a list (structural validation only)
2. **Factually flawed article** — judges an article falsely claiming Nikola Tesla invented the telephone; asserts the verdict is `"fail"` with at least one annotation (behavioral validation — the web search must catch the error)

---

**Common failure modes across all scripts:**

| Output | Cause | Fix |
|---|---|---|
| `[FAIL] Missing environment variable: 'ANTHROPIC_API_KEY'` | Key absent from `.env` | Add `ANTHROPIC_API_KEY` to `.env` |
| `[FAIL] No connectivity check implemented for provider '...'` | `config/app.yml` names an unsupported provider | Correct the provider name or implement a check for it |
| `[FAIL] <API error message>` | Key present but invalid, or provider unreachable | Verify the key is correct and the provider API is up |

---

## Making Requests with curl

Generation is now asynchronous. `POST /api/generate` returns a `job_id` immediately; `GET /api/status/{job_id}` is polled to track progress and retrieve the result.

**Step 1 — Submit a job:**

```bash
curl -X POST https://YOUR_DROPLET_IP/api/generate \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{"topic": "The history of the Roman Empire", "verbose": false}'
```

**Response:**
```json
{"job_id": "3f7a1c2e-..."}
```

**Step 2 — Poll for status:**

```bash
curl https://YOUR_DROPLET_IP/api/status/3f7a1c2e-... \
  -H "X-API-Key: your_api_key_here"
```

**While running:**
```json
{
  "status": "running",
  "iteration": 2,
  "max_iterations": 5,
  "phase": "judging",
  "last_verdict": "fail",
  "result": null,
  "error": null
}
```

**When done:**
```json
{
  "status": "done",
  "iteration": 2,
  "max_iterations": 5,
  "phase": "judging",
  "last_verdict": "pass",
  "result": {
    "success": true,
    "article": "<full article text>",
    "iterations": 2,
    "history": null
  },
  "error": null
}
```

**When error (iteration cap reached):**
```json
{
  "status": "error",
  "iteration": 5,
  "max_iterations": 5,
  "phase": "judging",
  "last_verdict": "fail",
  "result": {
    "success": false,
    "error": "Article did not pass after 5 iterations.",
    "iterations": 5,
    "history": [...]
  },
  "error": "Article did not pass after 5 iterations."
}
```

For local development, replace `https://YOUR_DROPLET_IP` with `http://localhost:8000`.

> **Note:** The self-signed cert will cause curl to fail with an SSL error.
> Add `-k` to skip cert verification for local testing against the prod stack:
> `curl -k https://YOUR_DROPLET_IP/api/status/...`

---

## Using the Browser UI

1. Navigate to `http://localhost:8000` (local) or `https://YOUR_DROPLET_IP` (prod).
2. Enter the session password set in `FRONTEND_SESSION_PASSWORD` in your `.env` to unlock the UI. The session persists until the container restarts — no timeout.
3. Type a topic in the text box, or upload a `.txt` file — the file's contents are loaded into the topic field.
4. Toggle **Verbose** to include the full iteration history below the article — each iteration shows its verdict (PASS/FAIL) and any Judge annotations.
5. Click **Generate**. A progress card appears immediately showing the current iteration, phase (Writer drafting / Judge reviewing), and elapsed time — updated every 2 seconds via polling.
7. When generation completes, the article appears below with iteration count and total time badges.

**How the UI handles long-running generation:**
The browser submits the job and receives a `job_id` in milliseconds. The loop runs entirely in a background thread on the server. The browser polls `GET /api/status/{job_id}` every 2 seconds — each poll is a short-lived request immune to connection timeouts. Generation can take many minutes with no risk of a "Failed to fetch" error.

---

## Judge Agent Design

The Judge uses a deliberate two-call flow to guarantee structured output without any text parsing.

**Call 1 — research:**
The Judge is given Anthropic's built-in `web_search` tool and told to verify every factual claim in the article. The model searches freely and returns a plain-text analysis of what it found. No verdict is produced yet.

**Call 2 — forced verdict:**
The research text from call 1 is appended to the conversation as an assistant message. The Judge is then called again with only the `submit_verdict` tool available and `tool_choice` set to force that specific tool. The Anthropic API guarantees the response conforms to the tool's schema before it reaches the application — `verdict` is always `"pass"` or `"fail"`, and `annotations` is always a list of strings. No YAML or JSON parsing occurs on our side.

```
call 1:  system_prompt + [user: "Review the article now."]
         tools = [web_search]
         → returns: text analysis

call 2:  system_prompt + [user: "Review...", assistant: <analysis>, user: "Submit verdict now."]
         tools = [submit_verdict]   tool_choice = {"type": "tool", "name": "submit_verdict"}
         → returns: {"verdict": "pass"|"fail", "annotations": [...]}
```

The `submit_verdict` tool is defined in `src/agents/judge.py` as `VERDICT_TOOL`. The `complete_structured()` method on `LLMInterface` (implemented in `anthropic_client.py`) handles the forced tool call and returns the tool input as a plain Python dict.

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

| Variable                    | Description                                                              |
| --------------------------- | ------------------------------------------------------------------------ |
| `ANTHROPIC_API_KEY`         | Anthropic API key for Claude                                             |
| `API_KEY`                   | Static key required in the `X-API-Key` header for all API requests       |
| `FRONTEND_SESSION_PASSWORD` | Password entered in the browser to unlock the UI; session persists until container restart |
