"""FastAPI backend for the Personalized Networking Assistant."""
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend import database
from backend.models import (
    FactCheckRequest,
    FactCheckResponse,
    FeedbackRequest,
    GenerateStartersRequest,
    GenerateStartersResponse,
    HistoryItem,
    StarterItem,
)
from backend.services.fact_checker import FactChecker
from backend.services.starter_generator import StarterGenerator
from backend.services.theme_extractor import ThemeExtractor

app = FastAPI(
    title="Personalized Networking Assistant API",
    description="Generates tailored conversation starters and quick fact checks for networking events.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

theme_extractor = ThemeExtractor()
starter_generator = StarterGenerator()
fact_checker = FactChecker()


@app.on_event("startup")
def on_startup() -> None:
    database.init_db()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/generate-starters", response_model=GenerateStartersResponse)
def generate_starters(payload: GenerateStartersRequest) -> GenerateStartersResponse:
    themes = theme_extractor.extract_themes(
        payload.event_description, extra_labels=payload.interests
    )
    starters = starter_generator.generate_starters(
        themes, payload.interests, num_starters=payload.num_starters
    )
    if not starters:
        raise HTTPException(status_code=500, detail="Could not generate conversation starters.")

    items: List[StarterItem] = []
    for starter in starters:
        history_id = database.add_history_entry(
            payload.event_description, payload.interests, themes, starter
        )
        items.append(StarterItem(id=history_id, starter=starter))

    return GenerateStartersResponse(themes=themes, starters=items)


@app.post("/api/fact-check", response_model=FactCheckResponse)
def fact_check(payload: FactCheckRequest) -> FactCheckResponse:
    result = fact_checker.check(payload.query)
    return FactCheckResponse(**result)


@app.post("/api/feedback")
def feedback(payload: FeedbackRequest) -> dict:
    updated = database.update_feedback(payload.history_id, payload.useful)
    if not updated:
        raise HTTPException(status_code=404, detail="History entry not found.")
    return {"status": "updated"}


@app.get("/api/history", response_model=List[HistoryItem])
def history(limit: int = 50) -> List[HistoryItem]:
    rows = database.get_history(limit=limit)
    return [
        HistoryItem(
            id=row["id"],
            event_description=row["event_description"],
            interests=row["interests"] or "",
            themes=row["themes"] or "",
            starter=row["starter"],
            useful=(bool(row["useful"]) if row["useful"] is not None else None),
            created_at=row["created_at"],
        )
        for row in rows
    ]
