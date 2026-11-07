# Backend (Flask)

1. `py -3.13 -m venv .venv` and activate it (`.venv\Scripts\activate`)
2. `pip install -r requirements.txt`
3. Create `.env` with `SECRET_KEY=<random text>` (e.g. `python -c "import secrets;print(secrets.token_hex(32))"`)
4. `python app.py` starts the server on http://127.0.0.1:5000 (creates `database.db` from `schema.sql`)
5. `python -m pytest` runs the tests
