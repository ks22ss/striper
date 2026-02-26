# Striper – Plan

## Overview

**Striper** is a FastAPI application that analyzes prompts for over-engineering using the **Stripe method**: strip components one at a time and compare model outputs. If removing a component barely changes the output, that component is redundant (over-engineered). If it changes a lot, the component is essential (optimal).

## Architecture

```
┌─────────────────┐     POST /analyze      ┌─────────────────────┐
│   Frontend UI   │ ───────────────────►  │   FastAPI Backend   │
│   (HTML/JS)     │                       │                     │
│   - Text area   │ ◄───────────────────  │   - Stripe logic    │
│   - Results     │     JSON response     │   - OpenAI client   │
└─────────────────┘                       └──────────┬──────────┘
                                                      │
                                                      ▼
                                             ┌─────────────────┐
                                             │   OpenAI API    │
                                             │   (gpt-4o-mini) │
                                             └─────────────────┘
```

## Stripe Method Algorithm

1. **Parse prompt into components**  
   Split by sentences/clauses (e.g., newlines, periods, numbered items). Each segment is a "component."

2. **Baseline**  
   Call the model with the full prompt and a simple execution task (e.g., "Respond to this prompt as if you were the assistant"). Store baseline output.

3. **Strip & compare**  
   For each component:
   - Build prompt without that component
   - Call model with same task
   - Compare output to baseline (similarity score: embedding cosine or simple diff)

4. **Score**  
   - **Over-engineered score** = proportion of components that, when removed, produce output similar to baseline (similarity > threshold)
   - Higher score = more redundant components = more over-engineered

5. **Improved prompt**  
   Keep only components whose removal significantly changed the output (i.e., essential components).

## Project Structure

```
striper/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app, routes
│   ├── stripe.py        # Stripe method logic
│   ├── openai_client.py # OpenAI API wrapper
│   └── models.py        # Pydantic schemas
├── static/
│   └── index.html       # Frontend UI
├── requirements.txt
├── .env.example
├── PLAN.md
└── README.md
```

## API Design

### `POST /analyze`

**Request:**
```json
{
  "prompt": "You are a helpful assistant. Always be concise. Use bullet points. Respond in JSON."
}
```

**Response:**
```json
{
  "over_engineered_score": 0.67,
  "improved_prompt": "You are a helpful assistant. Respond in JSON.",
  "components_removed": ["Always be concise.", "Use bullet points."],
  "components_kept": ["You are a helpful assistant.", "Respond in JSON."]
}
```

## Tech Stack

- **Backend:** FastAPI
- **LLM:** OpenAI API (gpt-4o-mini for speed/cost)
- **Similarity:** OpenAI embeddings or simple text diff
- **Frontend:** Vanilla HTML/CSS/JS (no build step)

## Environment

- `OPENAI_API_KEY` – required for analysis

## Implementation Order

1. Create `app/` structure, `main.py`, `models.py`
2. Implement `openai_client.py` – call model, get embeddings
3. Implement `stripe.py` – parse components, strip, compare, score
4. Wire `/analyze` endpoint
5. Build `static/index.html` UI
6. Add `requirements.txt`, `.env.example`, README
