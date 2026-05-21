"""
Application configuration using pydantic-settings.
All environment variables are loaded from .env file.
"""

import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # NVIDIA NIM Configuration
    nvidia_api_key: str = ""
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
    nvidia_model: str = "meta/llama-3.3-70b-instruct"

    # LLM rate limiting (NVIDIA NIM free/low tiers are often ~40 RPM)
    llm_max_rpm: int = 35
    llm_max_parallel: int = 1
    llm_retry_max: int = 6
    # Per-request read timeout (seconds). Reasoning models often exceed 120s.
    llm_timeout_seconds: int = 300

    # Demo mode: use user prompts directly as GEPA seed (skip LLM seed generation)
    demo_mode: bool = False

    # Hiring Configuration
    hire_threshold: float = 3.0

    # GEPA Configuration
    gepa_max_metric_calls: int = 150
    gepa_seed: int = 42
    train_split_ratio: float = 0.70
    val_split_ratio: float = 0.15
    test_split_ratio: float = 0.15
    early_stop_patience: int = 10
    overfit_gap_threshold: float = 0.15
    min_resumes_for_split: int = 6

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/resume_gepa.db"

    # Upload directory
    upload_dir: str = "./data/uploads"

    @property
    def upload_path(self) -> Path:
        path = Path(self.upload_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def data_dir(self) -> Path:
        path = Path("./data")
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache
def get_settings() -> Settings:
    return Settings()
