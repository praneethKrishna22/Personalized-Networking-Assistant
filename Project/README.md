# 🤝 Personalized Networking Assistant

An AI-powered assistant that generates personalized, context-aware conversation starters for networking events — plus quick fact-checking and a history of past suggestions with feedback tracking.

Given an event description and a user's interests, the app extracts the event's key themes, blends them with the user's stated interests, and produces natural conversation openers tailored to that intersection — so you walk into a room with something better to say than "so, what do you do?"

---

## ✨ Features

- **Generate Starters** — enter an event description and your interests, get 1–5 tailored conversation starters aligned to detected themes.
- **Fact Check** — quickly verify a claim or look up background on a topic via Wikipedia before bringing it up in conversation.
- **History & Feedback** — every generated starter is logged; mark it 👍 / 👎 to track what actually worked.

---

## 🏗️ Architecture

```
┌─────────────────────┐        HTTP (REST/JSON)        ┌──────────────────────┐
│   Streamlit Frontend │ ──────────────────────────────▶│   FastAPI Backend     │
│   (frontend/app.py)  │◀────────────────────────────── │   (backend/main.py)  │
└─────────────────────┘                                 └──────────┬───────────┘
                                                                    │
                                        ┌───────────────────────────┼───────────────────────────┐
                                        ▼                           ▼                           ▼
                            ThemeExtractor              StarterGenerator              FactChecker
                          (DistilBERT zero-shot          (GPT-2 conditioned            (Wikipedia API)
                           classification)                on themes/interests)
                                        │
                                        ▼
                                 SQLite (data/app.db)
                              conversation history + feedback
```

The frontend and backend are fully decoupled and communicate only over HTTP, so either layer can be swapped or scaled independently.

---

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| Backend API | [FastAPI](https://fastapi.tiangolo.com/) + [Uvicorn](https://www.uvicorn.org/) |
| Frontend | [Streamlit](https://streamlit.io/) |
| Theme extraction | DistilBERT (`typeform/distilbert-base-uncased-mnli`), zero-shot classification via 🤗 `transformers` |
| Starter generation | GPT-2, prompt-conditioned text generation via 🤗 `transformers` |
| Fact checking | Wikipedia REST API (`wikipedia` package) |
| Persistence | SQLite (no ORM — kept dependency-light) |
| Testing | `pytest`, with mocked-model fast tests and an opt-in slow suite against real models |
| Validation | Pydantic v2 schemas |

---

## 📁 Project Structure

```
personalized-networking-assistant/
├── backend/
│   ├── main.py                     # FastAPI app, routes, CORS, startup hook
│   ├── models.py                   # Pydantic request/response schemas
│   ├── database.py                 # SQLite persistence (history + feedback)
│   └── services/
│       ├── theme_extractor.py      # DistilBERT zero-shot theme extraction
│       ├── starter_generator.py    # GPT-2 conversation starter generation
│       └── fact_checker.py         # Wikipedia-backed fact checking
├── frontend/
│   └── app.py                      # Streamlit UI (3 tabs)
├── tests/
│   ├── test_api.py
│   ├── test_theme_extractor.py
│   ├── test_starter_generator.py
│   └── test_fact_checker.py
├── data/
│   └── app.db                      # SQLite database (created at runtime)
├── pytest.ini
├── requirements.txt
└── Personalized_Networking_Assistant_Colab.ipynb   # One-click Colab setup + demo
```

---

## 🚀 Getting Started

### Option A — Google Colab (fastest, no local setup)

1. Open `Personalized_Networking_Assistant_Colab.ipynb` in Google Colab.
2. Run every cell top to bottom.
3. Get a free ngrok authtoken and paste it into the designated cell: https://dashboard.ngrok.com/get-started/your-authtoken
4. The final cell prints a public `https://*.ngrok-free.app` URL — open that to use the app.

### Option B — Local setup

**Requirements:** Python 3.10+

```bash
git clone <repo-url>
cd personalized-networking-assistant
pip install -r requirements.txt
```

**Run the backend:**
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

**Run the frontend** (in a separate terminal):
```bash
streamlit run frontend/app.py
```

By default the frontend talks to `http://localhost:8000`. To point it elsewhere, set:
```bash
export BACKEND_URL="http://your-backend-host:8000"
```

---

## 🔌 API Reference

Base URL: `http://<host>:8000`

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check — returns `{"status": "ok"}` |
| `POST` | `/api/generate-starters` | Extract themes and generate conversation starters |
| `POST` | `/api/fact-check` | Look up a topic/claim via Wikipedia |
| `POST` | `/api/feedback` | Mark a history entry as useful (👍) or not (👎) |
| `GET` | `/api/history?limit=50` | Retrieve past starters and their feedback |

Interactive OpenAPI docs are also auto-generated by FastAPI at `/docs`.

#### `POST /api/generate-starters`

Request:
```json
{
  "event_description": "AI for Sustainable Cities",
  "interests": ["climate change", "urban planning"],
  "num_starters": 3
}
```

Response:
```json
{
  "themes": ["sustainability", "urban planning", "artificial intelligence"],
  "starters": [
    { "id": 1, "starter": "..." },
    { "id": 2, "starter": "..." }
  ]
}
```

#### `POST /api/fact-check`

Request:
```json
{ "query": "blockchain in healthcare" }
```

Response:
```json
{
  "query": "blockchain in healthcare",
  "found": true,
  "summary": "...",
  "url": "https://en.wikipedia.org/wiki/...",
  "options": []
}
```
If the query is ambiguous, `found` is `false` and `options` lists possible Wikipedia disambiguation matches instead.

#### `POST /api/feedback`

Request:
```json
{ "history_id": 1, "useful": true }
```

#### `GET /api/history`

Returns a list of past entries: event description, interests, detected themes, the starter text, feedback (`true`/`false`/`null`), and a timestamp.

---

## 🧠 How It Works

1. **Theme extraction** — `ThemeExtractor` runs the event description through a DistilBERT model in zero-shot classification mode against a bank of ~20 networking/industry candidate labels (AI, sustainability, healthcare, finance, etc.), plus the user's own interests merged in as extra candidate labels. The top-scoring labels above a confidence threshold become the detected themes.
2. **Starter generation** — `StarterGenerator` conditions GPT-2 on a templated prompt built from the detected themes and interests, sampling several continuations and filtering for sentence-shaped output. Since base GPT-2 isn't instruction-tuned, hand-written template starters (personalized with the themes/interests) fill in if the model doesn't produce enough usable candidates — this keeps output reliable for a demo setting.
3. **Fact checking** — `FactChecker` queries the Wikipedia API for the given topic, returning a summary and link, or a list of disambiguation options if the query is ambiguous.
4. **Persistence** — every generated starter is written to a local SQLite database (`data/app.db`) along with the event description, interests, and themes, so it shows up in the History tab and can later be marked useful or not.

---

## 🧪 Testing

```bash
python -m pytest -q
```

By default, the ML-backed services are mocked so the suite runs in seconds. To also exercise the real DistilBERT model:

```bash
python -m pytest -q -m slow
```

---

## ⚠️ Known Limitations

- GPT-2 (base) is not instruction-tuned, so raw generations can be noisy; the app compensates with template fallbacks rather than fully solving this at the model level.
- SQLite is used for simplicity and is not intended for concurrent multi-user production use.
- The Colab-hosted setup (via ngrok) is meant for demos, not persistent deployment — the backend and database reset when the Colab runtime ends.

## 🔭 Possible Future Improvements

- Swap GPT-2 for an instruction-tuned model for more coherent, reliably on-topic starters.
- Add user accounts so history/feedback is scoped per person rather than shared globally.
- Deploy backend and frontend as persistent hosted services instead of a Colab + ngrok demo flow.
- Use feedback (👍/👎) to fine-tune or re-rank future starter generations.
