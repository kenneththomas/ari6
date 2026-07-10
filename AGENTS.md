# Project guidance

## Repository overview

- This is a Python Discord bot. The main bot entry point is `ari6.py`.
- Shared bot functionality lives in `modules/`; supporting scripts and web features live in their existing top-level directories.
- Read `README.md` for local setup and startup instructions before changing environment or deployment behavior.

## Setup and verification

- Install the main dependencies with `python -m pip install -r requirements.txt` inside a virtual environment.
- Run the full test suite with `python -m unittest discover -s test -p "*test*.py"`.
- After changing Python files, run `python -m compileall -q -x ".venv|__pycache__" .` and the relevant unit tests.
- Add or update tests when changing behavior that is practical to cover.

## Working conventions

- Preserve existing bot behavior unless the task explicitly requests a behavior change.
- Keep changes focused and avoid reformatting or modernizing unrelated legacy code.
- Reuse existing modules and helpers before adding new abstractions or dependencies.
- Keep network calls mocked in unit tests; tests should not require live Discord or API credentials.
- Update the relevant README when setup, configuration, or user-facing commands change.

## Secrets and local data

- Never commit, print, or expose API keys, Discord tokens, credential files, or other secrets.
- Treat `*.secret`, `maricon.py`, and `personality.py` as sensitive local files. Do not inspect or modify them unless the task explicitly requires it.
- Prefer environment variables for credentials. Preserve the existing `.gitignore` protections.
