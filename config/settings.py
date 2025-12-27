"""Configuration and settings for the Resume Builder AI system."""
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# API Keys
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_API_URL = os.getenv("GROQ_API_URL", "https://api.groq.ai")
GROQ_MODEL = os.getenv("GROQ_MODEL", "groq-1")
GROQ_TEMPERATURE = float(os.getenv("GROQ_TEMPERATURE", "0"))

# Groq Mock Mode (for offline testing)
GROQ_MOCK_MODE = os.getenv("GROQ_MOCK_MODE", "true").lower() == "true"

# Model Configuration
CONTENT_MODEL = "gemini-2.0-flash-exp"  # For content generation (free tier available)
VALIDATION_MODEL = "gemini-2.0-flash-exp"  # For validation tasks (free tier available)

# Quality Thresholds
MIN_ATS_SCORE = 0.90  # 90%
KEYWORD_MATCH_THRESHOLD = 0.80  # 80%
PDF_QUALITY_THRESHOLD = 85  # out of 100
LATEX_COMPILE_TIMEOUT = 30  # seconds

# Pass/Fail Policy
# Hybrid policy: allow automatic PASS when numeric thresholds met and
# at most HYBRID_ALLOWED_FAILURES non-blocking failures are present.
ENABLE_HYBRID_POLICY = True
HYBRID_ALLOWED_FAILURES = int(os.getenv("HYBRID_ALLOWED_FAILURES", "1"))

# Workflow Configuration
MAX_ITERATIONS = 2
ITERATION_TIMEOUT = 120  # seconds per iteration

# File Paths
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "outputs")
RESUME_OUTPUT_DIR = os.path.join(OUTPUT_DIR, "resumes")
LATEX_OUTPUT_DIR = os.path.join(OUTPUT_DIR, "latex")
PDF_OUTPUT_DIR = os.path.join(OUTPUT_DIR, "pdfs")

# Create output directories if they don't exist
for dir_path in [RESUME_OUTPUT_DIR, LATEX_OUTPUT_DIR, PDF_OUTPUT_DIR]:
    os.makedirs(dir_path, exist_ok=True)

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Temperature Settings for LLMs
CONTENT_GENERATION_TEMPERATURE = 0.7
VALIDATION_TEMPERATURE = 0.3
FEEDBACK_TEMPERATURE = 0.5

# System Prompts (imported separately for organization)
from .prompts import SYSTEM_PROMPTS

__all__ = [
    "GOOGLE_API_KEY",
    "GROQ_API_KEY",
    "GROQ_API_URL",
    "GROQ_MODEL",
    "GROQ_TEMPERATURE",
    "GROQ_MOCK_MODE",
    "CONTENT_MODEL",
    "VALIDATION_MODEL",
    "MIN_ATS_SCORE",
    "KEYWORD_MATCH_THRESHOLD",
    "PDF_QUALITY_THRESHOLD",
    "MAX_ITERATIONS",
    "OUTPUT_DIR",
    "RESUME_OUTPUT_DIR",
    "LATEX_OUTPUT_DIR",
    "PDF_OUTPUT_DIR",
    "SYSTEM_PROMPTS",
]
