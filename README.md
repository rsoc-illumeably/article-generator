# article-generator

A personal, internal Python service that generates fact-checked articles using a two-agent LLM loop (Writer + Judge). Containerized with Docker and deployable to a Digital Ocean Droplet. Accessible via a browser UI or curl.

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
├── setup_ssl.sh                   # Generates self-signed SSL cert into certs/
├── README.md                      # This file
│
├── src/
│   ├── main.py                    # FastAPI app factory; registers all routers
│   ├── config.py                  # Loads YAML configs and exposes typed dataclasses
│   │
│   ├── api/
│   │   ├── auth.py                # FastAPI dependency: validates X-API-Key header
│   │   └── routes.py              # POST /api/generate
│   │
│   ├── frontend/
│   │   ├── routes.py              # GET / (UI or login), POST /session (password submit)
│   │   ├── session.py             # In-memory session store for browser auth
│   │   └── templates/
│   │       └── index.html         # Single-page Tailwind UI
│   │
│   ├── agents/
│   │   ├── writer.py              # Writer agent: produces article drafts
│   │   ├── judge.py               # Judge agent: fact-checks via web search
│   │   └── loop.py                # Orchestrates the Writer→Judge loop
│   │
│   ├── llm/
│   │   ├── interface.py           # Abstract LLM base class (provider-agnostic)
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

3. Start the service:
   ```bash
   docker compose up --build
   ```

4. Open `http://localhost:8000` in your browser.

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

4. Start the production stack:
   ```bash
   docker compose -f docker-compose.prod.yml up -d --build
   ```

5. Access at `https://YOUR_DROPLET_IP`.
   Your browser will warn about the self-signed certificate — this is expected. Proceed past the warning.

---

## Making Requests with curl

**Generate an article (concise response):**
```bash
curl -X POST https://YOUR_DROPLET_IP/api/generate \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{"topic": "The history of the Roman Empire", "verbose": false}'
```

**Generate with full verbose output (iteration history + reasoning):**
```bash
curl -X POST https://YOUR_DROPLET_IP/api/generate \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{"topic": "The history of the Roman Empire", "verbose": true}'
```

**With dev mode enabled:**
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

---

## Using the Browser UI

1. Navigate to `http://localhost:8000` (local) or `https://YOUR_DROPLET_IP` (prod).
2. Enter the session password set in your `.env` to unlock the UI.
3. Type a topic in the text box, or upload a `.txt` file — the file's contents are loaded into the topic field and treated identically to typed input.
4. Toggle **Verbose** to include the full iteration history and per-agent reasoning in the response.
5. Toggle **Dev Panel** to see the turn-by-turn agent interaction rendered after the article loads (agent name, output or flags, iteration number).
6. Click **Generate** and wait. Results appear in the output area below.

---

## Updating Prompts and Article Rules

All prompts and structural rules live in `config/`. Editing these files never requires a code change.

| What you want to change | File to edit |
|---|---|
| Writer's system prompt | `config/writer_prompt.yml` → `system_prompt` |
| Article max word/paragraph count, required sections, tone | `config/writer_prompt.yml` → `article_rules` |
| Judge's system prompt | `config/judge_prompt.yml` → `system_prompt` |
| Judge's acceptance criteria | `config/judge_prompt.yml` → `acceptance_criteria` |
| LLM provider or model | `config/app.yml` → `llm` |
| Max Writer→Judge iterations before error | `config/app.yml` → `agent.max_iterations` |

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

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude |
| `API_KEY` | Static key required in the `X-API-Key` header for API requests |
| `FRONTEND_SESSION_PASSWORD` | Password entered in the browser to unlock the UI |
