# ADA Compliance Suite

## Cursor Cloud specific instructions

### Overview
Python-based ADA compliance checking suite with a CLI (`cli.py`), Flask web dashboard (`src/web_dashboard.py`), and autonomous background engine (`src/autonomous_engine.py`). Uses SQLite (embedded), no external database needed.

### Key commands
See `README.md` for full details. Quick reference:
- **Lint:** `python3 -m flake8 src/ --count --select=E9,F63,F7,F82 --show-source --statistics`
- **Tests:** `python3 -m pytest tests/ -v --cov=src`
- **Security scan:** `python3 -m bandit -r src/ -f txt`
- **CLI check:** `python3 cli.py check --url https://example.com --verbose`
- **Web dashboard:** `FLASK_DEBUG=true python3 src/web_dashboard.py` (serves on port 5000)

### Gotchas
- Tools like `flake8`, `pytest`, `bandit` are installed into user site-packages; invoke them via `python3 -m <tool>` rather than bare command names.
- The Flask dashboard's `template_folder` resolves relative to the `src/` module directory. The index route (`/`) will 500 because `/workspace/templates/` is not at `src/templates/`. The REST API endpoints (`/api/status`, `/api/sites`, etc.) work correctly.
- No environment variables are strictly required. The app runs in local/no-email mode without SMTP configuration. See `.env.example` for optional SMTP settings.
- The CI workflow (`.github/workflows/ci.yml`) targets Python 3.11, but the system Python 3.12 works fine with all dependencies.
