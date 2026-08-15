# Business Automation Project

This repository is structured into backend and frontend applications:

## Project Structure

```text
maps automation/
├── backend/               # Python Google Maps & Business Scraper Backend
│   ├── scraper.py         # Google Maps Playwright Scraper
│   ├── firestore.py       # Firebase Firestore Database Sync
│   ├── main.py            # CLI Execution Entrypoint
│   ├── config.py          # Configuration Loader (.env)
│   ├── test_firebase.py   # Firebase Connection Tester
│   ├── requirements.txt   # Backend Dependencies
│   └── logs/              # Application Execution Logs
│
├── frontend/              # Frontend Application (Empty folder ready for frontend setup)
│
└── README.md              # Root Documentation
```

## Backend Quick Start

```bash
cd backend
python -m venv .venv
# On Windows PowerShell:
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```
