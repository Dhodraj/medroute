# Healthcare Triage Backend

FastAPI-based healthcare triage system that processes free-text health complaints through an agent chain and returns structured triage recommendations.

## Features

- Agent-based architecture with 5 specialized agents
- Llama 3 8B integration via Ollama
- Rule-based fallbacks for reliability
- SQLite logging for audit trails
- Extensible model interface for future integrations

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install and start Ollama:
```bash
# Install Ollama (if not already installed)
curl -fsSL https://ollama.ai/install.sh | sh

# Pull default model (or use model management utility)
python3 manage_model.py change medllama2:7b
```

3. Run the application:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Usage

Send a POST request to `/triage`:

```bash
curl -X POST "http://localhost:8000/triage" \
     -H "Content-Type: application/json" \
     -d '{"query": "I have chest pain for 2 hours"}'
```

## Architecture

- **Intake Agent**: Validates and cleans input
- **Symptom Extraction Agent**: Extracts structured symptoms
- **Triage Agent**: Applies rule-based and LLM-based triage
- **Recommendation Agent**: Generates recommendations with disclaimers
- **Audit Agent**: Logs all interactions for compliance

## Configuration

### Model Management
Change the LLM model easily using the model management utility:

```bash
# Show current model
python3 manage_model.py current

# List available models
python3 manage_model.py list

# Change model (automatically pulls if needed)
python3 manage_model.py change medllama2:7b

# Pull a specific model
python3 manage_model.py pull llama3:8b
```

### Environment Variables
Set in `.env` file or environment:
- `MODEL_BACKEND`: "ollama" (default) or "openai"
- `OLLAMA_MODEL`: "medllama2:7b" (default) - **Change this in one place to update everywhere**
- `DATABASE_URL`: SQLite database path
