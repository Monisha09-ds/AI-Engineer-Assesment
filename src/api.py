import os
import shutil
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Use mock LLM by default for local demo if MODEL_PROVIDER is not set.
if os.getenv("MODEL_PROVIDER") is None:
    os.environ["MODEL_PROVIDER"] = "mock"

from processor import DocProcessor
from vector_store import VectorStoreManager
from drafter import Drafter
from feedback import FeedbackLoop

BASE_DIR = Path(__file__).resolve().parent.parent
SAMPLE_DOCUMENTS_DIR = BASE_DIR / "data" / "sample_documents"
MEMORY_PATH = BASE_DIR / "data" / "memory.json"
INDEX_PATH = BASE_DIR / "faiss_index"

app = FastAPI(
    title="Legal AI Workflow API",
    description="API for the Pearson Specter Litt legal AI workflow.",
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")

processor = DocProcessor()
vector_store = VectorStoreManager(index_path=str(INDEX_PATH))
feedback_loop = FeedbackLoop(memory_path=str(MEMORY_PATH))
drafter = Drafter(vector_store, feedback_loop)


def list_documents() -> List[str]:
    SAMPLE_DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
    return [item.name for item in sorted(SAMPLE_DOCUMENTS_DIR.iterdir()) if item.is_file()]


def generate_sample_documents() -> List[str]:
    from mock_generator import generate_messy_pdf, generate_handwritten_style_txt

    SAMPLE_DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
    existing = list_documents()
    if existing:
        return existing

    title_review_text = """
    PRELIMINARY TITLE REPORT
    Order No: 9988-AX-2026
    Date: May 10, 2026

    Property Address: 789 Harvey Specter Lane, New York, NY
    Current Owner: Mike Ross (as per deed dated 01/15/2020)

    Exceptions:
    1. Taxes for the fiscal year 2025-2026 are a lien, not yet payable.
    2. An easement for public utilities over the eastern 10 feet of the land.
    3. [ILLEGIBLE] ... regarding the north boundary ... [SMUDGE]

    Notes: The owner reported a minor dispute with the neighbor (Louis Litt)
    regarding the fence location.
    """

    case_facts = """
    MEMORANDUM OF CASE FACTS
    Subject: Pearson vs. Hardman

    On the night of April 12, the defendant was seen entering the premises
    at approx 11:45 PM. Witness A (Donna Paulsen) states she heard
    loud voices coming from the library.

    Key Evidence:
    - CCTV footage from the lobby (Timestamp: 23:46)
    - Signed contract dated Feb 3, 2024.
    - [HANDWRITTEN NOTE]: \"Don't let them see the blue file.\"
    """

    generate_messy_pdf(str(SAMPLE_DOCUMENTS_DIR / "title_report.pdf"), title_review_text, "Preliminary Title Report")
    generate_handwritten_style_txt(str(SAMPLE_DOCUMENTS_DIR / "case_facts.txt"), case_facts)
    return list_documents()


def rebuild_index(directory: Optional[Path] = None) -> int:
    global vector_store, drafter
    if directory is None:
        directory = SAMPLE_DOCUMENTS_DIR

    if not directory.exists():
        raise FileNotFoundError(f"Document directory not found: {directory}")

    if not any(directory.iterdir()):
        generate_sample_documents()

    docs = processor.process_directory(str(directory))
    if not docs:
        raise ValueError("No documents were processed. Make sure the source directory contains supported files.")

    if INDEX_PATH.exists():
        shutil.rmtree(INDEX_PATH)
    vector_store = VectorStoreManager(index_path=str(INDEX_PATH))
    vector_store.add_documents(docs)
    drafter = Drafter(vector_store, feedback_loop)
    return len(docs)


def ensure_vector_store_ready() -> None:
    if vector_store.vector_store is not None:
        return
    if vector_store.load_index():
        return
    if not list_documents():
        generate_sample_documents()
    rebuild_index()


class ProcessRequest(BaseModel):
    directory: Optional[str] = None
    rebuild: bool = False


class DraftRequest(BaseModel):
    query: str
    draft_type: str = "summary"


class FeedbackRequest(BaseModel):
    original: str
    edited: str
    query: str


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/api/status")
def api_status():
    documents = list_documents()
    is_loaded = vector_store.vector_store is not None or vector_store.load_index()
    return {
        "status": "ok",
        "documents": documents,
        "vector_store_ready": is_loaded,
        "insights_count": len(feedback_loop.memory),
    }


@app.get("/api/documents")
def api_list_documents():
    return {"documents": list_documents()}


@app.post("/api/process")
def api_process(request: ProcessRequest):
    directory = SAMPLE_DOCUMENTS_DIR
    if request.directory:
        candidate = Path(request.directory)
        if not candidate.is_absolute():
            candidate = BASE_DIR / candidate
        directory = candidate

    if request.rebuild and INDEX_PATH.exists():
        shutil.rmtree(INDEX_PATH)

    if not list_documents():
        generate_sample_documents()

    try:
        count = rebuild_index(directory)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return {
        "status": "ok",
        "processed_documents": count,
        "documents": list_documents(),
    }


@app.post("/api/draft")
def api_draft(request: DraftRequest):
    ensure_vector_store_ready()
    try:
        draft = drafter.generate_draft(request.query, request.draft_type)
        return {"status": "ok", "query": request.query, "draft": draft}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/feedback")
def api_feedback(request: FeedbackRequest):
    try:
        feedback_loop.learn_from_edit(request.original, request.edited, request.query)
        return {
            "status": "ok",
            "insights_count": len(feedback_loop.memory),
            "insights": feedback_loop.memory,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/insights")
def api_insights():
    return {"status": "ok", "insights": feedback_loop.memory}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
