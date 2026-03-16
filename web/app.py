"""
FastAPI Application — REST API for the JSON Agent.

Endpoints:
    POST /query          — Upload a JSON file + ask a question → get an answer.
    POST /query/path     — Point to a JSON file on disk + ask a question.
    GET  /health         — Health check.
"""

from __future__ import annotations

import logging
import os
import shutil
import uuid

import openai
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from web.agent import create_llm, run_query
from web.config import settings

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Lifespan — create the LLM client once at startup
# ------------------------------------------------------------------

_llm = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the shared LLM client on startup."""
    global _llm

    if not settings.openrouter_api_key:
        logger.warning(
            "OPENROUTER_API_KEY not set — /query endpoints will fail. "
            "Set it and restart."
        )
        yield
        return

    logger.info(
        "Initializing LLM client with model=%s", settings.openrouter_model
    )
    _llm = create_llm()
    os.makedirs(settings.upload_dir, exist_ok=True)
    logger.info("Agent ready. Upload dir: %s", settings.upload_dir)
    yield

    # Cleanup uploads on shutdown
    if os.path.isdir(settings.upload_dir):
        shutil.rmtree(settings.upload_dir, ignore_errors=True)


# ------------------------------------------------------------------
# FastAPI app
# ------------------------------------------------------------------

app = FastAPI(
    title="JSON Agent API",
    description=(
        "Upload a JSON file and ask natural-language questions. "
        "An LLM agent autonomously picks the right analysis tools "
        "and returns the answer."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------------------------
# Request / Response schemas
# ------------------------------------------------------------------


class QueryByPathRequest(BaseModel):
    """Request body for /query/path — reference a file already on disk."""

    file_path: str = Field(description="Absolute path to the JSON file.")
    question: str = Field(description="Natural-language question about the data.")


class QueryResponse(BaseModel):
    """Standard response for all query endpoints."""

    answer: str
    steps: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Intermediate tool calls the agent made.",
    )


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------


@app.get("/health")
async def health():
    """Health check — confirms the server is running."""
    return {
        "status": "ok",
        "model": settings.openrouter_model,
        "agent_ready": _llm is not None,
    }


@app.post("/query", response_model=QueryResponse)
async def query_upload(
    file: UploadFile = File(..., description="The JSON file to analyse."),
    question: str = Form(..., description="Natural-language question."),
):
    """
    Upload a JSON file and ask a question about it.

    The agent loads the file, explores its structure, and uses the
    appropriate tools to answer your question.
    """
    if _llm is None:
        raise HTTPException(
            status_code=503,
            detail="Agent not initialized — check OPENROUTER_API_KEY.",
        )

    # Save upload to a temp file
    file_id = uuid.uuid4().hex[:12]
    safe_name = os.path.basename(file.filename or "upload.json")
    save_path = os.path.join(settings.upload_dir, f"{file_id}_{safe_name}")

    with open(save_path, "wb") as f:
        content = await file.read()
        f.write(content)

    try:
        result = await run_query(_llm, question, save_path)
        return QueryResponse(**result)
    except openai.RateLimitError as exc:
        logger.warning("Rate-limited by upstream provider: %s", exc)
        raise HTTPException(status_code=429, detail=str(exc))
    except Exception as exc:
        logger.exception("Agent error")
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        # Clean up the uploaded file
        if os.path.exists(save_path):
            os.unlink(save_path)


@app.post("/query/path", response_model=QueryResponse)
async def query_by_path(req: QueryByPathRequest):
    """
    Ask a question about a JSON file already on disk.

    Provide the absolute file path — no upload needed.
    """
    if _llm is None:
        raise HTTPException(
            status_code=503,
            detail="Agent not initialized — check OPENROUTER_API_KEY.",
        )

    if not os.path.isfile(req.file_path):
        raise HTTPException(status_code=404, detail=f"File not found: {req.file_path}")

    try:
        result = await run_query(_llm, req.question, req.file_path)
        return QueryResponse(**result)
    except openai.RateLimitError as exc:
        logger.warning("Rate-limited by upstream provider: %s", exc)
        raise HTTPException(status_code=429, detail=str(exc))
    except Exception as exc:
        logger.exception("Agent error")
        raise HTTPException(status_code=500, detail=str(exc))
