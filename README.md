# killBill

> An agentic Jac app that audits a year of bank-statement charges, flags the forgotten and overpriced subscriptions, and drafts your cancellation emails.

**Track:** Fintech · **Built for:** JacHacks Spring · **Stack:** [Jac](https://docs.jaseci.org/) + byLLM

---

## What it does

Drop a 12-month CSV bank statement. The app:

1. **Detects recurring charges** deterministically — clusters by normalized merchant name + similar amount + ~monthly cadence (plain Python, no LLM tokens burned).
2. **Hands each charge to an agent** that decides which tools to call:
   - `enrich_merchant` — clean name, category, market-typical price
   - `judge_value` — KEEP / DOWNGRADE / CANCEL with a reason that references your *other* subs
   - `find_cheaper_alternative` — concrete tier-downgrade or substitute
   - `draft_cancellation_email` — subject, body, send-to channel
3. **Persists the audit graph** under Jac's `root` (Statement → Subscription → Recommendation → Email nodes survive across runs).
4. **Reports the headline number** — total monthly + annual savings.

The agentic part is in `audit.jac` — see `analyze_one_subscription` on line ~129. That one `by llm(tools=[...])` call lets the LLM plan and dispatch tools per subscription. The model picks the order. That's the "real agent" bar JacHacks judges asked for, not an API-wrapper.

---

## Install

```bash
cd subscription-killer
python3 -m venv .venv && source .venv/bin/activate
pip install jaseci          # installs jac, byllm, litellm, jac-cloud
cp .env.example .env
# edit .env and set ONE of: FEATHERLESS_API_KEY (recommended), ANTHROPIC_API_KEY,
# OPENAI_API_KEY, or GEMINI_API_KEY
```

`jac --version` should report 0.15+.

### Which LLM backend?

`audit.jac::_pick_model()` chooses the first key it sees in this order:

| env var | model used | notes |
|---|---|---|
| `FEATHERLESS_API_KEY` | `Qwen/Qwen2.5-72B-Instruct` via Featherless (OpenAI-compatible) | **Recommended** — free tier, solid tool calling. |
| `ANTHROPIC_API_KEY`   | `claude-sonnet-4-20250514` | Best quality, costs money. |
| `OPENAI_API_KEY`      | `gpt-4o-mini` | Cheap, good. |
| `GEMINI_API_KEY`      | `gemini/gemini-2.5-flash` | Free tier; rate-limit sensitive. |

If you use Featherless, `run_demo.sh` also exports `OPENAI_API_KEY=$FEATHERLESS_API_KEY` and `OPENAI_API_BASE=https://api.featherless.ai/v1` so LiteLLM routes through the right endpoint.

> **No keys are hardcoded.** `.env` is gitignored.

---

## Run the demo

```bash
./run_demo.sh
```

Or directly:

```bash
source .venv/bin/activate
set -a && source .env && set +a    # load API keys
jac run main.jac
```

The output prints a per-subscription verdict + the headline `$X saved per year` number.

### As a REST API

```bash
jac start audit.jac --port 8000 --no_client
```

jac-cloud requires bearer auth on walker endpoints by default — register a user and grab a token:

```bash
curl -sX POST http://127.0.0.1:8000/user/register -H 'Content-Type: application/json' \
  -d '{"identities":[{"type":"email","value":"demo@example.com"}],"credential":{"type":"password","password":"Demo1234aA!"}}'

TOK=$(curl -sX POST http://127.0.0.1:8000/user/login -H 'Content-Type: application/json' \
  -d '{"identity":{"type":"email","value":"demo@example.com"},"credential":{"type":"password","password":"Demo1234aA!"}}' \
  | python3 -c 'import json,sys;print(json.load(sys.stdin)["data"]["token"])')

curl -X POST http://127.0.0.1:8000/walker/AuditStatement \
  -H "Content-Type: application/json" -H "Authorization: Bearer $TOK" \
  -d '{"csv_path":"samples/statement_001.csv","persist":false}'
```

The audit lives in `data.reports[0]`.

### As a web UI

```bash
./run_web.sh
# then open http://127.0.0.1:5173
```

This starts both the API server (port 8000) and the static web app (port 5173). The frontend auto-registers a throwaway demo user on first load. Drop a CSV; the headline number animates up.

If the agent isn't reachable, the UI falls back to `web/demo_report.json` (a pre-recorded result against `samples/statement_001.csv`) so you can still see the dashboard.

---

## Project layout

```
subscription-killer/
  audit.jac             # agentic pipeline + walker + graph nodes
  main.jac              # CLI demo entry that pretty-prints the report
  recurrence.py         # deterministic CSV clustering (Python)
  smoke_test.jac        # one-sub smoke test for the agent
  jac.toml              # byllm default model config
  samples/
    statement_001.csv   # 331 rows / 12 months / 13 recurring charges
  scripts/
    generate_sample.py  # regenerates the demo CSV
  web/
    index.html          # minimal drag-and-drop dashboard (no build step)
  run_demo.sh           # CLI runner that loads .env and runs main.jac
  .env.example
```

---

## Sample input → sample output

The bundled `samples/statement_001.csv` is a 12-month statement with 13 monthly recurring charges totaling **$418.28/mo** ($5,019/yr). The agent identifies:

- **Hulu** ($17.99/mo) — DOWNGRADE: "you already pay for Netflix Premium, content overlap is high"
- **Adobe Creative Cloud** ($54.99/mo) — DOWNGRADE: "Canva Pro at $12.99/mo overlaps with most of this"
- **Planet Fitness** ($24.99/mo) — CANCEL: "8 months, no adjacent fitness-related spend"
- **Audible** ($14.95/mo) — CANCEL: "no companion Amazon book/audiobook activity"
- **NYTimes** ($17.00/mo) — DOWNGRADE: "basic digital is $4/mo"

…plus a drafted cancellation email for each CANCEL.

---

## What's "agentic" about this

- **Planning** — `analyze_one_subscription` decomposes "audit this charge" into 4 sub-decisions and the LLM picks the order.
- **Tool use** — 4 typed tool functions (`enrich_merchant`, `judge_value`, `find_cheaper_alternative`, `draft_cancellation_email`); the agent decides which fire and skips e.g. the email step for KEEP/DOWNGRADE verdicts.
- **Memory** — `BankStatement`, `Subscription`, `KillRecommendation`, `CancellationEmail` nodes connect to `root` and persist across `jac run` invocations (Jac OSP).
- **Multi-step reasoning** — verdict explanations reference the user's *other* subscriptions ("you already pay for X"), which requires the model to hold the full sub-portfolio in context.

## Jac features used

- `node Foo { has field: type; }` for the persistent graph
- `def fn(...) -> str by llm()` for typed LLM functions
- `def fn(...) -> str by llm(tools=[t1, t2, ...])` for agentic tool use
- `sem fn = "..."` for instruction-grade prompt hints
- `walker AuditStatement { can run with ` root` entry { ... } }` for the REST endpoint
- `root ++> stmt` for auto-persisted graph storage

---

## Limitations / known issues

- Featherless 72B model is slow (~30s per per-sub agent call). The full 13-sub audit takes ~6-10 min wall-clock. Use Anthropic/OpenAI keys for a faster demo.
- The cluster-detector treats anything monthly + ≥3 charges as recurring; a few real-world ambiguities (e.g. a coincidental quarterly Target charge) get filtered when cadence isn't monthly.
- `jac serve` walker endpoints inherit Jac's `jac-cloud` defaults; for a public demo you'd want auth + rate limiting.

## License

MIT — built for JacHacks Spring 2026, fictional data only.
