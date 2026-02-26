# Striper

Analyze prompts for over-engineering using the **Stripe method**: strip components one at a time and compare model outputs. If removing a component barely changes the output, it's redundant. If it changes a lot, it's essential.

## Quick start

```bash
# Clone and enter
cd /root/striper

# Create venv and install
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt

# Set API key
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Run
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000 in your browser.

## How it works

1. **Parse** – Your prompt is split into components (sentences/clauses).
2. **Baseline** – The model produces a sample response using the full prompt.
3. **Strip** – Each component is removed one at a time; the model responds again.
4. **Compare** – Outputs are compared via embeddings. Similar output → component is redundant.
5. **Score** – Over-engineered score = proportion of redundant components (0–1).
6. **Improve** – The improved prompt keeps only essential components.

## API

- `POST /analyze` – Body: `{"prompt": "...", "input": "...", "api_key": "sk-..."}` (input and api_key optional) → Returns score, improved prompt, component breakdown
- `GET /health` – Health check

## UI

Paste a prompt, optionally add sample input text the prompt will process, optionally enter an OpenAI API key (uses server config if blank), click **Analyze**, and view the over-engineered score, improved prompt, and component breakdown (kept vs removed). Use the **Copy** button next to the improved prompt to copy it to the clipboard. From **History**, click **Use** on any past analysis to load that prompt into the form for re-analysis or editing.

## Project structure

```
striper/
├── app/
│   ├── main.py       # FastAPI app
│   ├── stripe.py     # Stripe method logic
│   ├── openai_client.py
│   └── models.py
├── static/
│   └── index.html    # Frontend
├── PLAN.md           # Detailed plan
└── requirements.txt
```

## License

See [LICENSE](LICENSE).
