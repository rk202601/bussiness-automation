# 📁 Business Automation — Project Structure & Overview

> **Last Updated:** 2026-08-13
> **Status:** Active Development
> **Language:** Python 3.10+

---

## 🎯 Project Purpose

An end-to-end **business lead automation tool** that:
1. Scrapes Google Maps for business listings using configurable keywords × cities
2. Extracts **Name, Phone, Address** from each listing using Playwright (headless browser)
3. Deduplicates leads intelligently (by phone or name+area)
4. Stores all leads into **Google Firebase Firestore** (cloud NoSQL database)

The goal is to generate a clean, de-duplicated lead database for business outreach — fully automated, no manual effort needed.

---

## 🗂️ Directory Structure

```
d:\maps automation\
│
├── main.py                          # ← Entry point — orchestrates everything
├── scraper.py                       # ← Playwright-based Google Maps scraper
├── firestore.py                     # ← Firebase Firestore read/write manager
├── config.py                        # ← .env loader + validator
├── test_firebase.py                 # ← Standalone Firebase connection test
│
├── .env                             # ← Your active configuration (git-ignored)
├── .env.example                     # ← Configuration template (safe to commit)
├── requirements.txt                 # ← Python package dependencies
├── .gitignore                       # ← Git ignore rules
├── README.md                        # ← Public-facing readme
│
├── bussiness-automation-62605-firebase-adminsdk-fbsvc-5124e71a9e.json
│                                    # ← Firebase service account key (git-ignored)
│
├── logs/                            # ← Auto-created; one timestamped log per run
│   └── scraper_YYYY-MM-DD_HH-MM-SS.log
│
└── .venv/                           # ← Python virtual environment (git-ignored)
```

---

## 🧩 Module Breakdown

### `main.py` — Orchestrator / Entry Point

**Role:** Wires everything together and drives the full scrape-and-save loop.

| Responsibility | Detail |
|---|---|
| Logging setup | Console + timestamped file in `logs/` |
| Config loading | Instantiates `Config` from `.env` |
| Firestore init | Creates `FirestoreManager` connection |
| Scrape loop | Iterates every `city × keyword` combo |
| Live batching | Buffers leads, saves to Firestore every **10 leads** |
| Browser restart | Restarts Playwright every **20 leads** (frees RAM, kills zombies) |
| Graceful Ctrl+C | Flushes unsaved buffer before exiting |
| Final summary | Prints total found / added / duplicated / time elapsed |

**Key Constants:**
```python
BATCH_SIZE      = 10   # Save to Firestore every N leads
BROWSER_RESTART = 20   # Restart browser every N leads extracted
```

---

### `scraper.py` — Google Maps Playwright Scraper

**Role:** Launches a stealth browser, searches Google Maps, and extracts lead details.

#### Class: `Lead` (dataclass)

The data model for a single business lead.

| Field | Type | Default |
|---|---|---|
| `name` | str | required |
| `phone` | str | required |
| `area` | str | required |
| `state` | str | required |
| `source` | str | `"Google Map"` |
| `status` | str | `"Not Contacted"` |

#### Class: `GoogleMapsScraper`

Core scraper class with Playwright lifecycle management.

| Method | Purpose |
|---|---|
| `start()` | Launch Chromium with stealth + anti-bot flags |
| `stop()` | Close browser cleanly + kill zombie child processes |
| `scrape_all(keywords, cities, state)` | Iterate all city × keyword combos (public API) |
| `_search_and_extract(keyword, city, state, on_lead)` | Search one combo, scroll, extract all leads |
| `_scroll_results(page)` | Scroll sidebar until end-of-results or stale count |
| `_get_listing_hrefs(page)` | Collect unique listing URLs from the feed |
| `_extract_listing_by_url(page, href, ...)` | Navigate to a listing, extract name/phone/address |
| `_extract_name(page)` | Multi-strategy name extraction (h1, aria-label) |
| `_extract_phone(page)` | Multi-strategy phone extraction (button tooltip, aria, regex) |
| `_extract_address(page, city)` | Multi-strategy address extraction (button tooltip, aria, fallback) |
| `_dismiss_consent(page)` | Handle Google cookie/consent popups |
| `_human_delay(base)` | Sleep with randomized jitter to simulate human behavior |

**Anti-Detection Features:**
- `playwright-stealth` patches applied at browser start
- Randomized human delays (1–3s navigation, ±30% jitter on action delays)
- Random 1–10s pause every 10 listings
- Custom User-Agent string
- `--disable-blink-features=AutomationControlled` browser flag
- Zombie process cleanup after each browser restart

---

### `firestore.py` — Firebase Firestore Manager

**Role:** Manages all read/write interactions with Google Firestore.

#### Class: `FirestoreManager`

| Method | Purpose |
|---|---|
| `__init__(credentials_file, collection_name)` | Init Firebase app + connect to collection |
| `get_existing_keys()` | Stream all docs, return phone set + name/area set for dedup |
| `is_duplicate(...)` | Check against both dedup key sets |
| `add_leads(leads)` | Filter dupes, batch-write new leads, return summary dict |
| `_lead_to_dict(lead)` | Serialize Lead to Firestore document dict |
| `_normalize_phone(phone)` | Strip non-digits, normalize Indian numbers to last 10 digits |

**Firestore Document Schema:**
```json
{
  "Name":   "Business Name",
  "Phone":  "9876543210",
  "Area":   "Sector 14, Gurugram",
  "State":  "Haryana",
  "Source": "Google Map",
  "Status": "Not Contacted"
}
```

**Duplicate Detection Logic:**
1. **Primary:** Normalize phone → check against existing phone set
2. **Secondary (phone-less only):** `(name.lower(), area.lower())` tuple check
3. **Within-batch:** Updates local key sets on-the-fly to catch dupes in the same run

---

### `config.py` — Configuration Loader

**Role:** Reads `.env` and validates all required fields at startup.

| Config Key | Type | Required | Default |
|---|---|---|---|
| `TARGET_STATE` | str | ✅ | — |
| `TARGET_CITIES` | list[str] | ✅ | — |
| `SEARCH_KEYWORDS` | list[str] | ✅ | — |
| `FIREBASE_CREDENTIALS_FILE` | str | ✅ | — |
| `FIRESTORE_COLLECTION` | str | ❌ | `leads_<state>` (auto-derived) |
| `HEADLESS` | bool | ❌ | `true` |
| `SCROLL_PAUSE_SEC` | float | ❌ | `1.5` |
| `ACTION_DELAY_SEC` | float | ❌ | `2.0` |

> **Note:** `FIRESTORE_COLLECTION` is auto-named `leads_<state>` (e.g., `leads_haryana`) if not explicitly set.

---

### `test_firebase.py` — Firebase Connectivity Test

A standalone sanity-check script. Inserts 2 dummy leads and verifies they land in Firestore.

```bash
python test_firebase.py
```

---

## 🔗 Data Flow

```
.env (config)
     │
     ▼
 Config()
     │
     ├──────────────────────────────────┐
     │                                  │
     ▼                                  ▼
GoogleMapsScraper              FirestoreManager
  Playwright + Chromium         Firebase Admin SDK
     │                                  │
     │  (for each city × keyword)        │
     ▼                                  │
  Google Maps URL                       │
     ▼                                  │
  Scroll results                        │
     ▼                                  │
  Visit each listing                    │
     ▼                                  │
  Extract Lead (name, phone, area)      │
     ▼                                  │
  on_lead() ── every 10 leads ──────────▶ Firestore batch write
     └──────────── (repeat) ────────────┘
```

---

## 📦 Dependencies

| Package | Version | Purpose |
|---|---|---|
| `playwright` | 1.52.0 | Headless browser automation |
| `playwright-stealth` | 1.0.6 | Anti-bot detection patches |
| `firebase-admin` | 6.5.0 | Firestore read/write via Admin SDK |
| `python-dotenv` | 1.1.0 | `.env` file loading |
| `setuptools` | 69.5.1 | Build toolchain support |

---

## 🚀 How to Run

```bash
pip install -r requirements.txt
playwright install chromium
cp .env.example .env   # then edit .env with your values
python main.py
```

---

## ⚠️ Notes & Gotchas

- Firebase credentials JSON must **never** be committed to git (it is in `.gitignore`)
- `FIRESTORE_COLLECTION` auto-names to `leads_<state>` if not set — useful for multi-state runs
- Browser is restarted every 20 leads automatically to prevent memory bloat
- All logs are saved to `logs/scraper_YYYY-MM-DD_HH-MM-SS.log` — one file per run
- Google Maps may show CAPTCHA at high scrape volumes — reduce speed via `SCROLL_PAUSE_SEC` / `ACTION_DELAY_SEC`
