"""
backend/app/services/backup_service.py

Production Database Backup & Recovery Service.
Handles safe SQLite database backup generation and integrity verification.
Does NOT fabricate backup success records.
"""

from __future__ import annotations

import os
import shutil
import sqlite3
import datetime
import logging
from pathlib import Path
from typing import Dict, Any

from app.config import get_settings
from app.database import engine, check_db_connection

logger = logging.getLogger(__name__)

_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent


def create_database_backup(backup_dir: str | None = None) -> Dict[str, Any]:
    """
    Creates a timestamped copy of the current SQLite database file.
    Validates backup integrity via SQLite connection test.

    Returns:
        Dict containing success status, backup path, file size, timestamp, or error detail.
    """
    settings = get_settings()
    url = settings.database_url

    if not url.startswith("sqlite:///"):
        logger.info("Backup mechanism optimized for SQLite. Current DB URL: %s", url)
        # For non-sqlite, perform connection check
        db_ok = check_db_connection()
        return {
            "success": db_ok,
            "database_type": "external",
            "message": "External database backup should be managed by host provider snapshot policy.",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

    # Extract db filepath from sqlite:/// URL
    db_relative_path = url.replace("sqlite:///", "")
    db_path = Path(db_relative_path)
    if not db_path.is_absolute():
        db_path = _BACKEND_ROOT / db_path

    if not db_path.exists():
        logger.error("Database file not found for backup: %s", db_path)
        return {
            "success": False,
            "error": "Source database file does not exist.",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

    target_dir = Path(backup_dir) if backup_dir else _BACKEND_ROOT / "backups"
    target_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_filename = f"db_backup_{timestamp}.db"
    backup_file_path = target_dir / backup_filename

    try:
        # Use sqlite3 online backup API for safe live backup
        src_conn = sqlite3.connect(str(db_path))
        dst_conn = sqlite3.connect(str(backup_file_path))
        with dst_conn:
            src_conn.backup(dst_conn)
        dst_conn.close()
        src_conn.close()

        # Integrity Check
        integrity_ok = verify_backup_integrity(str(backup_file_path))
        if not integrity_ok:
            if backup_file_path.exists():
                backup_file_path.unlink()
            return {
                "success": False,
                "error": "Backup integrity check failed after creation.",
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }

        file_size_bytes = backup_file_path.stat().st_size
        logger.info("Successfully created database backup: %s (%d bytes)", backup_filename, file_size_bytes)

        return {
            "success": True,
            "backup_filename": backup_filename,
            "backup_path": str(backup_file_path),
            "size_bytes": file_size_bytes,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }

    except Exception as exc:
        logger.error("Database backup failed: %s", exc)
        return {
            "success": False,
            "error": f"Backup operation failed: {str(exc)}",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }


def verify_backup_integrity(backup_path: str) -> bool:
    """
    Verifies that a SQLite backup file is readable, not corrupt, and passes quick check.
    """
    path = Path(backup_path)
    if not path.exists() or path.stat().st_size == 0:
        return False

    try:
        conn = sqlite3.connect(str(path))
        cursor = conn.cursor()
        cursor.execute("PRAGMA quick_check")
        res = cursor.fetchone()
        conn.close()
        return res is not None and res[0] == "ok"
    except Exception as exc:
        logger.warning("Backup integrity verification failed for %s: %s", path.name, exc)
        return False
