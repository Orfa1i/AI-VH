"""
Runnable doctor-review API server for AI-VH (STEP 38 / P6.3).

Serves the STEP 37 review API over HTTP for the Clinical AI OS shell and the
Playwright end-to-end suite. Demo seeding (`FEEDBACK_DEMO_SEED=1`) wipes and
reseeds a throwaway database: dev/test use only, never production data.
"""

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from vh.feedback.api import create_app
from vh.feedback.seed import seed_demo

DB_PATH = os.environ.get("FEEDBACK_DB_PATH", "data/feedback-review.db")
OVERLAP_FRACTION = float(os.environ.get("FEEDBACK_OVERLAP_FRACTION", "0.15"))
CORS_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        "FEEDBACK_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    if origin.strip()
]

if os.environ.get("FEEDBACK_DEMO_SEED") == "1":
    Path(DB_PATH).unlink(missing_ok=True)
    seed_demo(
        DB_PATH,
        token=os.environ.get("FEEDBACK_DEMO_TOKEN", "e2e-demo-token-001"),
    )

app: FastAPI = create_app(db_path=DB_PATH, overlap_fraction=OVERLAP_FRACTION)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Reviewer-Token"],
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("vh.feedback.server:app", host="127.0.0.1", port=8100)
