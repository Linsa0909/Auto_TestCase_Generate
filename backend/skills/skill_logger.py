"""
Skill activity logger — each skill writes to its own log file under /log/skills/
"""
import os
import logging
from datetime import datetime
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent.parent / "log" / "skills"
LOG_DIR.mkdir(parents=True, exist_ok=True)


def get_skill_logger(skill_name: str) -> logging.Logger:
    """Get a logger that writes to log/skills/{skill_name}_{timestamp}.log"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"{skill_name}_{timestamp}.log"

    logger = logging.getLogger(f"skill.{skill_name}")
    logger.setLevel(logging.INFO)
    logger.propagate = False  # don't duplicate to root logger

    # File handler
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter(
        "[%(asctime)s] %(levelname)s %(message)s",
        datefmt="%H:%M:%S"
    ))
    logger.addHandler(fh)

    # Also log to console for dev visibility
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter(
        "[%(asctime)s] %(levelname)s %(message)s",
        datefmt="%H:%M:%S"
    ))
    logger.addHandler(ch)

    return logger
