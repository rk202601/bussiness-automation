"""
firestore.py — Firebase Firestore integration via firebase-admin SDK.

Handles reading existing leads, duplicate detection, and batch insertion.
Each lead is stored as a document in a Firestore collection.
"""

import logging
import re
from datetime import datetime, timezone

import firebase_admin
from firebase_admin import credentials, firestore

logger = logging.getLogger(__name__)


class FirestoreManager:
    """Manages read/write access to a Firestore collection for lead storage."""

    def __init__(
        self,
        credentials_file: str,
        collection_name: str = "leads",
    ):
        logger.info(
            "Connecting to Firestore collection '%s'…",
            collection_name,
        )

        # Initialize Firebase app (only once per process)
        if not firebase_admin._apps:
            cred = credentials.Certificate(credentials_file)
            firebase_admin.initialize_app(cred)

        self.db = firestore.client()
        self.collection = self.db.collection(collection_name)
        self.collection_name = collection_name

        logger.info("[OK] Connected to Firestore successfully.")

    # ── Duplicate detection ──────────────────────────────────

    def get_existing_keys(self) -> tuple[set[str], set[tuple[str, str]]]:
        """
        Fetch all documents and return two sets for duplicate checking:
          - phone_keys:      set of normalized phone strings
          - name_area_keys:  set of (name_lower, area_lower) tuples
        """
        docs = self.collection.stream()
        phone_keys: set[str] = set()
        name_area_keys: set[tuple[str, str]] = set()
        count = 0

        for doc in docs:
            count += 1
            data = doc.to_dict()
            phone_val = data.get("Phone") if "Phone" in data else data.get("phone", "")
            name_val = data.get("Name") if "Name" in data else data.get("name", "")
            area_val = data.get("Area") if "Area" in data else data.get("area", "")

            phone = self._normalize_phone(str(phone_val or ""))
            name = str(name_val or "").strip().lower()
            area = str(area_val or "").strip().lower()

            if phone:
                phone_keys.add(phone)
            if name and area:
                name_area_keys.add((name, area))

        logger.info(
            "Loaded %d existing leads (%d phone keys, %d name+area keys).",
            count, len(phone_keys), len(name_area_keys),
        )
        return phone_keys, name_area_keys

    def is_duplicate(
        self,
        lead_phone: str,
        lead_name: str,
        lead_area: str,
        phone_keys: set[str],
        name_area_keys: set[tuple[str, str]],
    ) -> bool:
        """Check if a lead already exists in Firestore."""
        norm_phone = self._normalize_phone(lead_phone)

        # Primary check: phone number
        if norm_phone and norm_phone in phone_keys:
            return True

        # Secondary check: name + area (only if phone is missing)
        if not norm_phone:
            name_lower = lead_name.strip().lower()
            area_lower = lead_area.strip().lower()
            if name_lower and area_lower and (name_lower, area_lower) in name_area_keys:
                return True

        return False

    # ── Insertion ────────────────────────────────────────────

    def add_leads(self, leads: list) -> dict:
        """
        Filter duplicates and insert new leads into Firestore.

        Returns a summary dict: {total, duplicates, added}
        """
        if not leads:
            return {"total": 0, "duplicates": 0, "added": 0}

        phone_keys, name_area_keys = self.get_existing_keys()

        new_leads = []
        duplicates = 0

        for lead in leads:
            if self.is_duplicate(
                lead.phone, lead.name, lead.area, phone_keys, name_area_keys
            ):
                duplicates += 1
                logger.debug("  ↳ Duplicate skipped: %s", lead.name)
                continue

            new_leads.append(lead)

            # Update local keys to catch duplicates within the same batch
            norm_phone = self._normalize_phone(lead.phone)
            if norm_phone:
                phone_keys.add(norm_phone)
            else:
                name_lower = lead.name.strip().lower()
                area_lower = lead.area.strip().lower()
                if name_lower and area_lower:
                    name_area_keys.add((name_lower, area_lower))

        if new_leads:
            # Use a batched write for efficiency (Firestore batch limit = 500)
            batch = self.db.batch()
            for lead in new_leads:
                doc_ref = self.collection.document()  # auto-ID
                batch.set(doc_ref, self._lead_to_dict(lead))
            batch.commit()

            logger.info(
                "[OK] Added %d new leads to Firestore '%s' (%d duplicates skipped).",
                len(new_leads), self.collection_name, duplicates,
            )
        else:
            logger.info("No new leads to add (%d duplicates skipped).", duplicates)

        return {
            "total": len(leads),
            "duplicates": duplicates,
            "added": len(new_leads),
        }

    # ── Helpers ──────────────────────────────────────────────

    @staticmethod
    def _lead_to_dict(lead) -> dict:
        """Convert a Lead object to a dict containing ONLY Name, Phone, Area, State, Source, Status."""
        return {
            "Name": getattr(lead, "name", "") or "",
            "Phone": getattr(lead, "phone", "") or "",
            "Area": getattr(lead, "area", "") or "",
            "State": getattr(lead, "state", "") or "",
            "Source": getattr(lead, "source", "Google Map") or "Google Map",
            "Status": getattr(lead, "status", "Not Contacted") or "Not Contacted",
        }

    @staticmethod
    def _normalize_phone(phone: str) -> str:
        """Strip all non-digit chars for comparison, keep only digits."""
        digits = re.sub(r"\D", "", phone)
        # For Indian numbers, normalize to last 10 digits
        if len(digits) > 10:
            digits = digits[-10:]
        return digits if len(digits) >= 7 else ""
