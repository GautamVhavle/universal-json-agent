"""
Configuration — settings loaded from environment variables.

Set OPENROUTER_API_KEY in your environment or a .env file.
Optionally override the model with OPENROUTER_MODEL.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()  # reads .env from project root


@dataclass(frozen=True)
class Settings:
    """Immutable application settings."""

    openrouter_api_key: str = field(
        default_factory=lambda: os.environ.get("OPENROUTER_API_KEY", "")
    )
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = field(
        default_factory=lambda: os.environ.get(
            "OPENROUTER_MODEL", "openai/gpt-4o-mini"
        )
    )
    max_iterations: int = 25       # max agent tool-call loops
    upload_dir: str = "/tmp/json_agent_uploads"


settings = Settings()
