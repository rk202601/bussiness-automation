"""
config.py — Loads and validates configuration from .env
"""

import os
import sys
from dotenv import load_dotenv


class Config:
    """Loads all configuration from .env and validates required fields."""

    def __init__(self, env_path: str = ".env"):
        load_dotenv(env_path)

        # ── Required fields ──────────────────────────────────
        self.TARGET_STATE = self._require("TARGET_STATE")
        self.TARGET_CITIES = self._require_list("TARGET_CITIES")
        self.SEARCH_KEYWORDS = self._require_list("SEARCH_KEYWORDS")
        self.FIREBASE_CREDENTIALS_FILE = self._require("FIREBASE_CREDENTIALS_FILE")

        # ── Optional fields with defaults ────────────────────
        # Collection name: leads_<state> e.g. leads_haryana, leads_punjab
        # Auto-derived from TARGET_STATE. Can be overridden via FIRESTORE_COLLECTION in .env
        default_collection = "leads_" + self.TARGET_STATE.strip().lower().replace(" ", "_")
        self.FIRESTORE_COLLECTION = os.getenv("FIRESTORE_COLLECTION", default_collection).strip()
        self.HEADLESS = os.getenv("HEADLESS", "true").strip().lower() == "true"
        self.SCROLL_PAUSE_SEC = float(os.getenv("SCROLL_PAUSE_SEC", "1.5"))
        self.ACTION_DELAY_SEC = float(os.getenv("ACTION_DELAY_SEC", "2.0"))

        # ── Validate credentials file exists ─────────────────
        if not os.path.isfile(self.FIREBASE_CREDENTIALS_FILE):
            print(
                f"[CONFIG ERROR] Firebase credentials file not found: "
                f"'{self.FIREBASE_CREDENTIALS_FILE}'\n"
                f"  → Download it from Firebase Console → Project Settings → Service Accounts\n"
                f"  → Then update FIREBASE_CREDENTIALS_FILE in .env"
            )
            sys.exit(1)

    # ── Helpers ──────────────────────────────────────────────

    @staticmethod
    def _require(key: str) -> str:
        """Return an env var or exit with a clear message."""
        value = os.getenv(key, "").strip()
        if not value:
            print(
                f"[CONFIG ERROR] Required variable '{key}' is missing or empty in .env"
            )
            sys.exit(1)
        return value

    @staticmethod
    def _require_list(key: str) -> list[str]:
        """Return a comma-separated env var as a list, or exit."""
        raw = os.getenv(key, "").strip()
        if not raw:
            print(
                f"[CONFIG ERROR] Required variable '{key}' is missing or empty in .env"
            )
            sys.exit(1)
        return [item.strip() for item in raw.split(",") if item.strip()]

    def summary(self) -> str:
        """Return a human-readable summary of the current configuration."""
        return (
            f"  State:       {self.TARGET_STATE}\n"
            f"  Cities:      {', '.join(self.TARGET_CITIES)}\n"
            f"  Keywords:    {', '.join(self.SEARCH_KEYWORDS)}\n"
            f"  Firestore:   collection='{self.FIRESTORE_COLLECTION}' (leads_<state> auto-named)\n"
            f"  Headless:    {self.HEADLESS}\n"
            f"  Delays:      scroll={self.SCROLL_PAUSE_SEC}s, action={self.ACTION_DELAY_SEC}s"
        )
