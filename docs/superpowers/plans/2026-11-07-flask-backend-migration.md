# Flask Backend Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Port the auth, users and department endpoints of the C# minimal API in `database/` to a Flask app in `backend/`, with the same routes, JSON fields, status codes and messages.

**Architecture:** `create_app()` factory registers one Blueprint per area (`auth`, `users`, `departments`). Each table gets one repository module of plain parameterized `sqlite3` functions. Auth uses Flask's signed session cookie; access checks are the `login_required` / `role_required` decorators, plus a check against the database for department writes (same as the C# `AccessGuard`).

**Tech Stack:** Python 3.13 (`py -3.13`; Flask is not installed yet), Flask 3, python-dotenv, stdlib `sqlite3`, `hashlib`, `hmac`, pytest.

**Spec:** the user's migration prompt (in the conversation) + C# source: `database/program.cs`, `database/Data/UserRepository.cs`, `database/Data/DepartmentRepository.cs`, `database/Data/AccessGuard.cs`, `database/Security/PasswordHasher.cs`, `database/schema.sql`. `WriteResult.ToHttp` is no longer in the tree (it was deleted; `.gitignore` pattern `*Endpoints` hides it). Its behavior, from commit `9c75f1c:database/Endpoints/EndpointsExtensions.cs`: Ok→200 `{message}`, NotFound→404 `{error}`, Conflict→409 `{error}` (default `"Conflict."`), Forbidden→403.

## Global Constraints

- Python 3.11+, Flask, stdlib `sqlite3`, no ORM. Parameterized SQL only (`?` placeholders), never f-strings or `%` in SQL.
- `backend/schema.sql` is a byte-for-byte copy of `database/schema.sql`. Run it on startup with `executescript`. Do not change tables or column names.
- SQLite file `database.db` in `backend/` (`app.root_path`). Every connection runs `PRAGMA foreign_keys = ON` (C# used `Foreign Keys=True`).
- Session cookie: `SESSION_COOKIE_NAME="site_auth"`, `SESSION_COOKIE_HTTPONLY=True`, `PERMANENT_SESSION_LIFETIME=timedelta(hours=8)`, `SESSION_REFRESH_EACH_REQUEST=True`, `session.permanent = True` at login.
- `SECRET_KEY` read from the environment after `load_dotenv()`. If it is missing, raise `RuntimeError("SECRET_KEY environment variable is required.")`.
- Password hash format: `"{iterations}.{b64(salt)}.{b64(hash)}"`, PBKDF2-HMAC-SHA256, 600000 iterations, 16-byte salt, 32-byte hash, standard base64 with padding, password encoded UTF-8, compared with `hmac.compare_digest`.
- Exact response bodies and messages (copied from program.cs):
  - `GET /` → 200, plain text `Server is running`
  - register: `{"error": "Name, email and password are required."}` 400 · `{"error": "Password must have at least 8 characters."}` 400 · `{"message": "User registered."}` 200 · `{"error": "This email is already registered."}` 409
  - login: `{"message": "Logged in."}` 200; every failure is 401 with the same body
  - logout: `{"message": "Logged out."}` 200 (no login required)
  - `/me` → `{"name", "email", "role"}` · `/users` → JSON list of active user names (strings) · `/admin-only` → `{"secret": "admins only"}`
  - `GET /departments` → list of `{"id", "name", "code", "isActive"}` (camelCase, the way System.Text.Json writes it)
  - `POST /departments`: `{"error": "Name and code are required."}` 400 · `{"message": "Department created."}` 200 · `{"error": "This department code already exists."}` 409
- Unauthenticated → 401 `{"error": "Not authenticated."}`; wrong role or not an active admin → 403 `{"error": "Forbidden."}`. No redirects. (C# sent these with empty bodies; the user asked for JSON.)
- New users get `user_role='basic'`, `is_active=1`. Name is trimmed, email is trimmed and lowercased, department code is trimmed and uppercased. The password is never trimmed, and its length check uses the raw value.
- Timestamps: `datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")`, which is close to the C# `"o"` format.
- One-line comment on each function. Do not touch `database/`. No features beyond this list.

## Review Focus

1. **Missing/non-JSON body or non-string fields** (`{"email": 123}`, `name: null`, plain text body): register → 400 with the required-fields message, login → 401. Never a 500. *Test in Task 3.*
2. **Email case and whitespace:** registering `"  Ana@Test.COM "` stores `ana@test.com`; registering `ana@test.com` afterwards → 409; logging in with `ANA@test.com` works. *Test in Task 3.*
3. **Stale admin cookie:** a user is demoted in the DB after logging in as admin. `POST /departments` must return 403 because it checks the DB. `/admin-only` still returns 200 because it trusts the cookie role, the same as the C# version. *Test in Task 5.*
4. **Code case on duplicates:** creating `"ti"` when `"TI"` exists → 409. Whitespace-only name/code → 400. *Test in Task 5.*
5. **Malformed stored hash** (`""`, `"abc"`, bad base64, NULL): `verify_password` returns False and login returns 401, not 500. *Test in Task 2.*

---

## File Structure

```
backend/
  app.py                  create_app(), config, blueprint registration, GET /
  db.py                   get_db(), close_db(), init_db()
  security.py             hash_password(), verify_password()
  auth.py                 login_required, role_required(role)
  schema.sql              copy of database/schema.sql
  repositories/__init__.py  (empty)
  repositories/users.py
  repositories/departments.py
  routes/__init__.py      to_http()
  routes/auth.py          /register /login /logout /me
  routes/users.py         /users /admin-only
  routes/departments.py   GET/POST /departments
  tests/conftest.py       app/client fixtures + helpers
  tests/test_security.py
  tests/test_api.py
  requirements.txt  README.md
.gitignore                (modify: add .env, database.db)
```

---

### Task 1: App skeleton, config, database init

**Files:**
- Create: `backend/app.py`, `backend/db.py`, `backend/schema.sql` (copy), `backend/repositories/__init__.py`, `backend/routes/__init__.py` (empty for now), `backend/requirements.txt`, `backend/tests/conftest.py`, `backend/tests/test_api.py`
- Modify: `.gitignore` (append `.env` and `database.db`)

**Interfaces:**
- Produces: `create_app(test_config: dict | None = None) -> Flask`. `test_config` is applied *before* the SECRET_KEY check, and it can set `DATABASE`. The default `DATABASE` is `os.path.join(app.root_path, "database.db")`.
- Produces: `db.get_db() -> sqlite3.Connection` (one per request, stored in `flask.g`, `row_factory = sqlite3.Row`, foreign keys on), `db.close_db(e=None)` registered as `teardown_appcontext`, `db.init_db(app) -> None` (runs `schema.sql` inside an app context, called from `create_app`).
- Produces fixtures in `conftest.py`: `app` (`create_app({"TESTING": True, "SECRET_KEY": "test", "DATABASE": str(tmp_path / "test.db")})`) and `client`.
- `app.py` ends with `if __name__ == "__main__": create_app().run(debug=True)`.

- [ ] **Step 1: Set up the environment.** Run `cd backend; py -3.13 -m venv .venv; .venv\Scripts\pip install -r requirements.txt`. `requirements.txt` contains `Flask>=3.0`, `python-dotenv>=1.0`, `pytest>=8.0`. Copy `database/schema.sql` to `backend/schema.sql`.
- [ ] **Step 2: Write failing tests** in `tests/test_api.py`:

```python
def test_root(client):
    r = client.get("/")
    assert r.status_code == 200 and r.get_data(as_text=True) == "Server is running"

def test_schema_created(app):
    with app.app_context():
        names = {r[0] for r in get_db().execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"User", "Department", "UserDepartment", "Pop", "Link", "PhoneNumber",
            "PopLink", "PopPhone", "PopDepartment"} <= names

def test_missing_secret_key(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app({"DATABASE": ":memory:"})
```

Note: `load_dotenv()` must not override this. Call it with its defaults, so it does not overwrite env vars that are already set, and put no `.env` in the test working directory.

- [ ] **Step 3: Run** `.venv\Scripts\python -m pytest -q`. Expected: FAIL (import error).
- [ ] **Step 4: Implement** `app.py` and `db.py` to the interfaces above, with the cookie config from Global Constraints.
- [ ] **Step 5: Run** `.venv\Scripts\python -m pytest -q`. Expected: 3 passed.
- [ ] **Step 6: Commit** `git add .gitignore backend && git commit -m "feat(backend): Flask app skeleton with SQLite init"`. Before committing, check that `.venv/` is not staged; if it is, add `.venv/` to `.gitignore`.

### Task 2: Password hashing

**Files:** Create `backend/security.py`, `backend/tests/test_security.py`

**Interfaces:**
- Produces: `hash_password(password: str) -> str` and `verify_password(password: str, stored: str | None) -> bool`. `verify_password` returns False on any malformed input (wrong part count, non-int iterations, bad base64, None).

- [ ] **Step 1: Write failing tests:**

```python
CSHARP_HASH = "600000.GVWNQ53JXqJrOvdWLNTc6Q==.50BJhQqB+D9Zqs+LP4hAiHEV+cc7uNQTQDYHpCgLcw8="  # made by PasswordHasher.cs for agatinho@test.com

def test_verifies_hash_made_by_csharp():
    assert verify_password("mypassword123", CSHARP_HASH)
    assert not verify_password("mypassword124", CSHARP_HASH)

def test_format_and_roundtrip():
    h = hash_password("secret123")
    it, salt, digest = h.split(".")
    assert it == "600000" and len(base64.b64decode(salt)) == 16 and len(base64.b64decode(digest)) == 32
    assert verify_password("secret123", h) and not verify_password("Secret123", h)
    assert hash_password("secret123") != h  # random salt

@pytest.mark.parametrize("bad", ["", "abc", "x.y.z", "600000.!!!.???", None])
def test_malformed_hash_is_false(bad):
    assert verify_password("whatever1", bad) is False
```

- [ ] **Step 2: Run** `.venv\Scripts\python -m pytest tests/test_security.py -q`. Expected: FAIL (ImportError).
- [ ] **Step 3: Implement** with `hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations, dklen=len(expected))`, `os.urandom(16)`, `base64.b64encode/b64decode(..., validate=True)`, and `hmac.compare_digest`.
- [ ] **Step 4: Run.** Expected: all pass.
- [ ] **Step 5: Commit** `feat(backend): PBKDF2 password hashing compatible with C#`.

### Task 3: Users repository, auth routes, decorators

**Files:** Create `backend/repositories/users.py`, `backend/auth.py`, `backend/routes/auth.py`. Modify `backend/app.py` (register blueprint), `backend/tests/conftest.py` (helpers), `backend/tests/test_api.py`.

**Interfaces:**
- Consumes: `get_db()`, `hash_password`, `verify_password`.
- Produces `repositories/users.py`:
  - `get_by_email(email: str) -> sqlite3.Row | None` (columns `user_id, user_name, user_email, user_password_hash, user_role, is_active`)
  - `add(name: str, email: str, password_hash: str) -> bool` (False on `sqlite3.IntegrityError`, which matches C# catching every constraint error)
  - `active_names() -> list[str]` (skip NULL names)
  - `is_active_admin(user_id: int) -> bool` (port of AccessGuard: `user_role = 'admin' AND is_active = 1`)
- Produces `auth.py`: `login_required(view)` (checks `"user_id" in session`, else 401 JSON) and `role_required(role: str)` (401 if not logged in, 403 if `session["role"] != role`). Both use `functools.wraps`.
- Session keys set at login: `user_id` (int), `name`, `email`, `role`. NULL handling is the same as C# `GetByEmail`: name/email default to `""`, role defaults to `"user"`.
- Request JSON: `data = request.get_json(silent=True) or {}`. A field counts only if it is a `str` (anything else is treated as `""`), which covers Review Focus #1.
- Helpers in `conftest.py`: `register(client, email="ana@test.com", password="mypassword123", name="Ana")`, `login(client, email=..., password=...)`, and `set_user(app, email, **cols)`, which runs a parameterized `UPDATE "User" SET <col>=?` for `user_role` / `is_active`. The column names come from a fixed allow-list.

- [ ] **Step 1: Write failing tests:**
  - `test_register_ok`: 200 `{"message": "User registered."}`
  - `test_register_duplicate`: second register → 409 `{"error": "This email is already registered."}`
  - `test_register_short_password`: `"1234567"` → 400 `{"error": "Password must have at least 8 characters."}`. `"       x"` (8 chars with spaces) → 200.
  - `test_register_missing_fields`: `{"name": " ", ...}`, `{}`, a non-JSON body, and `{"email": 123}` → each 400 `{"error": "Name, email and password are required."}`
  - `test_email_normalized`: register `"  Ana@Test.COM "` → then register `ana@test.com` → 409; login `ANA@test.com` → 200
  - `test_login_ok`: 200 `{"message": "Logged in."}`, and the `Set-Cookie` header contains `site_auth=`, `HttpOnly` and `Expires`
  - `test_login_failures_identical`: wrong password, unknown email, inactive user (`set_user(app, email, is_active=0)`), empty body, `{"email": 1}`, and a user whose stored hash is `"abc"` → all 401 with identical bodies
  - `test_me`: without a cookie → 401 `{"error": "Not authenticated."}`; after login → 200 `{"name": "Ana", "email": "ana@test.com", "role": "basic"}`
  - `test_logout`: after logout, `/me` → 401. Logout without a session → 200 `{"message": "Logged out."}`
- [ ] **Step 2: Run** `.venv\Scripts\python -m pytest -q`. Expected: the new tests FAIL (404s).
- [ ] **Step 3: Implement** the repository, the decorators, and Blueprint `auth` (routes `/register`, `/login`, `/logout`, `/me`) to the interfaces above. Logout calls `session.clear()`.
- [ ] **Step 4: Run.** Expected: all pass.
- [ ] **Step 5: Commit** `feat(backend): register, login, logout, me`.

### Task 4: /users and /admin-only

**Files:** Create `backend/routes/users.py`. Modify `backend/app.py` and `backend/tests/test_api.py`.

**Interfaces:** Consumes `login_required`, `role_required`, and `users.active_names()`. Blueprint `users`.

- [ ] **Step 1: Write failing tests:**
  - `test_users_list`: unauthenticated → 401; register Ana and Bob, deactivate Bob, then log in as Ana → 200 `["Ana"]`
  - `test_admin_only`: unauthenticated → 401; basic user → 403 `{"error": "Forbidden."}`; then `set_user(app, email, user_role="admin")` and **log in again** (the role is read at login, same as C# claims) → 200 `{"secret": "admins only"}`
- [ ] **Step 2: Run.** Expected: FAIL.
- [ ] **Step 3: Implement** the two routes (`/admin-only` uses `@role_required("admin")`).
- [ ] **Step 4: Run.** Expected: all pass.
- [ ] **Step 5: Commit** `feat(backend): users list and admin-only`.

### Task 5: Departments

**Files:** Create `backend/repositories/departments.py`, `backend/routes/departments.py`. Modify `backend/routes/__init__.py`, `backend/app.py`, `backend/tests/test_api.py`.

**Interfaces:**
- Produces `routes/__init__.py`: `to_http(result: str, ok_message: str, not_found_message: str, conflict_message: str = "Conflict.")`. `result` is one of `"ok" | "not_found" | "conflict" | "forbidden"`, and the return value is a `(dict, status)` tuple: 200 `{message}` / 404 `{error}` / 409 `{error}` / 403 `{"error": "Forbidden."}`. Later tables reuse this function.
- Produces `repositories/departments.py`:
  - `get_all() -> list[dict]` with keys `id, name, code, isActive` (bool). NULL name/code become `""`.
  - `add(actor_user_id: int, name: str, code: str) -> str`: returns `"forbidden"` if `not users.is_active_admin(actor_user_id)`. Catches only the UNIQUE violation (`e.sqlite_errorcode == sqlite3.SQLITE_CONSTRAINT_UNIQUE`) → `"conflict"`, and re-raises anything else, the same as C# `IsUnique()`.
- Route `POST /departments` is `@login_required` only (no role decorator). Order: validate → uppercase code → `to_http(add(...), "Department created.", "Department not found.", "This department code already exists.")`. As in C#, validation runs before the admin check, so a basic user with an empty body gets 400.

- [ ] **Step 1: Write failing tests:**
  - `test_departments_list`: unauthenticated → 401. Logged in on a fresh DB → 200 `[]`. After an admin creates `{"name": " IT ", "code": " ti "}` → `[{"id": 1, "name": "IT", "code": "TI", "isActive": True}]`
  - `test_department_create`: admin → 200 `{"message": "Department created."}`. Same code again, or `"Ti"` → 409 `{"error": "This department code already exists."}`. `{"name": "  ", "code": "X"}` and `{}` → 400 `{"error": "Name and code are required."}`
  - `test_department_create_forbidden`: basic user → 403 `{"error": "Forbidden."}`. Unauthenticated → 401
  - `test_stale_admin_cookie`: log in as admin, then `set_user(app, email, user_role="basic")` → `POST /departments` 403, and `/admin-only` still 200
- [ ] **Step 2: Run.** Expected: FAIL.
- [ ] **Step 3: Implement** `to_http`, the repository, and the Blueprint `departments`.
- [ ] **Step 4: Run** the full suite. Expected: all pass.
- [ ] **Step 5: Commit** `feat(backend): departments list and create`.

### Task 6: README, live-server check, report

**Files:** Create `backend/README.md` (5 lines: create the venv, `pip install -r requirements.txt`, create `.env` with `SECRET_KEY=...`, `python app.py`, `python -m pytest`).

- [ ] **Step 1: Write README.md.**
- [ ] **Step 2: Live smoke test against the real data.** Copy (do not move) `database/database.db` to `backend/database.db`. Create `backend/.env` with a random `SECRET_KEY` (`py -c "import secrets;print(secrets.token_hex(32))"`). Start `python app.py` in the background. Then run these with `curl -s -i -c jar -b jar`:
  - `GET /` → 200
  - `POST /login {"email":"agatinho@test.com","password":"mypassword123"}` → 200 (a C#-created user logs in)
  - `GET /me` → 200 `role: basic`
  - `GET /admin-only` → 403
  - log in as `ana@test.com` / `mypassword123` (admin in the DB) → `GET /admin-only` 200; `GET /departments` returns TI and FS; `POST /departments {"name":"Fiscal","code":"fs"}` → 409
  - `POST /logout` → `GET /me` 401

  Expected: every status matches. Stop the server.
- [ ] **Step 3: Confirm** that `git status` does not show `.env` or `backend/database.db`.
- [ ] **Step 4: Commit** `docs(backend): README`.
- [ ] **Step 5: Report to the user:** the pytest output, the curl output, and this list of differences from C#:
  - 401/403 now have JSON bodies (C# sent them empty). Login failure has a 401 JSON body.
  - Missing or invalid JSON: C# returned a framework 400. Flask returns register 400 (required-fields message) and login 401.
  - JSON keys are case-sensitive (`Email` is ignored; C# accepted any case). The frontend sends lowercase.
  - Existing ASP.NET cookies are invalid, so everyone has to log in once more. The Flask cookie is signed but not encrypted, so the client can read name/email/role, but cannot change them.
  - Sliding expiration renews on every request (ASP.NET renewed after half the lifetime had passed).
  - Timestamps have 6 fractional digits instead of 7.
  - Not ported (out of scope): `/user-departments`, `/me/departments`, `/pops*`, `/links*`, `/phones*`, `/pop-links`, `/pop-phones`, `/pop-departments`.
  - Already true before this migration: the commented-out frontend calls `/api/auth/login`, `/api/auth/me`, `/api/auth/logout` and `/api/users`, which match neither backend. Neither backend serves `wwwroot/`. The C# tree no longer builds because `Endpoints/EndpointsExtensions.cs` is missing (hidden by `.gitignore` `*Endpoints`).
