# Google Maps → Google Sheets Lead Automation

Automatically scrapes business leads from Google Maps and pushes them to your Google Sheet — no manual effort, no duplicates.

## Features

- 🔍 Searches Google Maps for configurable **keywords × cities**
- 📞 Extracts **Name, Phone, Address** from each business listing
- 📊 Saves leads to an existing Google Sheet via **service account** (no password needed)
- 🔁 **Duplicate detection** by phone number (primary) or name+area (fallback)
- ⚙️ Fully configurable via `.env` — change state, cities, keywords without touching code
- 📝 Detailed logging to console and `scraper.log`
- 🛡️ Stealth mode + human-like delays to reduce detection risk

---

## Prerequisites

- **Python 3.10+**
- A **Google Cloud project** with:
  - Google Sheets API enabled
  - Google Drive API enabled
  - A Service Account with a JSON key file

---

## Setup

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Playwright browsers

```bash
playwright install chromium
```

### 3. Set up Google Cloud Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project (or use existing)
3. Enable **Google Sheets API** and **Google Drive API**
4. Go to **APIs & Services → Credentials**
5. Click **Create Credentials → Service account**
6. Fill in the name, click **Create and Continue → Done**
7. Click on the service account → **Keys** tab → **Add Key → Create new key → JSON**
8. Save the downloaded file as `credentials.json` in this project folder

### 4. Share your Google Sheet

1. Open your Google Sheet ("customer finder")
2. Click **Share**
3. Paste the `client_email` from your `credentials.json` file
4. Set permission to **Editor**
5. Click **Send**

### 5. Configure `.env`

Copy the template and fill in your values:

```bash
cp .env.example .env
```

Edit `.env`:

```env
TARGET_STATE=Haryana
TARGET_CITIES=Gurugram,Faridabad,Panipat,Hisar,Ambala
SEARCH_KEYWORDS=LCD LED Repair,LCD LED Spare Parts,LED TV Repair
GOOGLE_SHEET_NAME=customer finder
SHEET_NAME=Sheet1
GOOGLE_SERVICE_ACCOUNT_FILE=credentials.json
HEADLESS=true
```

---

## Usage

```bash
python main.py
```

The script will:

1. Load your configuration from `.env`
2. Connect to your Google Sheet
3. For each **city × keyword** combination:
   - Search Google Maps
   - Scroll to load all results
   - Click into each listing to extract details
   - Add new leads to the sheet (skip duplicates)
4. Print a final summary

### Change settings without touching code

| What to change | Where to change |
|---|---|
| Target state | `TARGET_STATE` in `.env` |
| Cities to search | `TARGET_CITIES` in `.env` (comma-separated) |
| Search keywords | `SEARCH_KEYWORDS` in `.env` (comma-separated) |
| Google Sheet name | `GOOGLE_SHEET_NAME` in `.env` |
| Worksheet tab | `SHEET_NAME` in `.env` |
| Show browser window | `HEADLESS=false` in `.env` |
| Adjust speed | `SCROLL_PAUSE_SEC` and `ACTION_DELAY_SEC` in `.env` |

---

## Google Sheet Format

Your sheet must have these column headers in the first row:

| Name | Phone | Area | State | Source | Status |
|---|---|---|---|---|---|

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `SpreadsheetNotFound` | Make sure the sheet name in `.env` matches exactly AND is shared with the service account email |
| `Service account file not found` | Check `GOOGLE_SERVICE_ACCOUNT_FILE` path in `.env` |
| CAPTCHA appears | The script does NOT bypass CAPTCHAs. Reduce scraping frequency or use `HEADLESS=false` to solve manually |
| No results found | Verify the keyword + city combination returns results on Google Maps manually |
| Missing phone numbers | Some businesses don't list phone numbers — these are saved with an empty phone field |

---

## Project Structure

```
├── main.py              # Entry point
├── scraper.py           # Playwright Google Maps scraper
├── sheets.py            # Google Sheets read/write
├── config.py            # .env configuration loader
├── .env                 # Your settings (git-ignored)
├── .env.example         # Settings template
├── requirements.txt     # Python dependencies
├── .gitignore           # Git ignore rules
└── README.md            # This file
```

---

## ⚠️ Disclaimer

This tool is for **personal lead generation** only. Google Maps scraping may violate Google's Terms of Service at scale. Use responsibly with reasonable delays. The tool does **not** bypass any CAPTCHA or security mechanisms.
