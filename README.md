# medroute

A triage API for health complaints. Send a complaint in plain words and get back how urgent it is and what to do next.

Built in March 2026.

## How it works

Five small agents run in order: intake, symptom extraction, triage, recommendation and audit. The triage agent asks a local model through Ollama and also runs a rule-based check. If the rules say emergency and the model does not, the answer becomes emergency. Every request is logged to SQLite.

Urgency levels: `emergency`, `urgent`, `semi_urgent`, `non_urgent`.

It is not a medical device and does not give medical advice.

## Run it

You need Python 3.11 or newer and Ollama with a model pulled. The default model is `medllama2:7b`. Set `OLLAMA_MODEL` to use another one.

```bash
./setup.sh
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs are then at `http://localhost:8000/docs`.

| Method | Path | What it does |
|---|---|---|
| POST | `/triage` | triage a complaint, body `{"query": "..."}` |
| GET | `/health` | health check |
| GET | `/stats` | counts from the log |
