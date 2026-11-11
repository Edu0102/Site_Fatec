# Foundation + Ferramentas Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **First step on approval:** copy this file to `docs/superpowers/plans/2026-11-10-foundation-ferramentas.md` (plan mode only allowed writing here). Do **not** commit anything until Eduardo reviews and says yes (standing rule); the "Commit" steps below mean "stage and show the diff, wait for a yes".

## Context

The frontend team delivered a new interface-only design. **Source of truth (latest version):** `C:\Users\eduar\Documents\EDUARDO\Academic\Projects\Site_FRCont\versao mega top\versao mega top\versao mega top\frcont\frcont\` (called `DESIGN` below). The team also sent a task list (`----!!TAREFAS!!---.pdf`) used as guidelines; F.R.Cont is the company name. Each page exposes a `renderizar(...)` entry point and fires DOM events (`ferramenta:salvar`, ...) but saves nothing. The Flask + SQLite backend in `backend/` already has auth, users, departments, POPs, checklists, feedback, photos, links and phones, but nothing for Ferramentas (tools), and several design pages expect fields the schema lacks.

This is plan 1 of 6. It puts the new design in `wwwroot`, wires everything the backend already supports (login, session header, logout, photo, change password, feedback, hub) and builds the Tools feature end to end. Later plans, one each: Funcionários/departments; Links + phone list (schema extensions); POPs with file upload; Checklist (personal tasks plus POP checklists on one page).

**Goal:** The new design is served by Flask with working login, header, feedback, hub and a complete Ferramentas page backed by new `Tool` / `ToolUsage` tables.

**Architecture:** Design files are copied into `wwwroot/` unchanged where possible. Each page gets a separate glue script `wwwroot/js/<page>-api.js` that translates between the design's Portuguese field names/events and the backend's JSON, using the existing `api()` helper in `wwwroot/js/api.js`. Keeping glue separate lets the team re-deliver design files without losing the wiring. Backend additions follow the existing `routes/` + `repositories/` + `tests/` pattern (model: `backend/routes/links.py`, `backend/repositories/links.py`, `backend/tests/test_links.py`).

**Tech Stack:** Flask, sqlite3, pytest; plain HTML/CSS/JS (no build step, no new dependencies).

**Spec:** this document's Context and decisions section (no separate spec file; decisions were taken in chat on 2026-11-10).

## Decisions (from Eduardo)

- Tools: any logged-in user can add; only the creator or an admin can edit/delete.
- Old pages not in the design (`guia`, `abaguia`, `cadastro`) are deleted.
- Checklist page will later show both personal tasks and POP checklists (not this plan).
- Glue stays in separate `*-api.js` files per page (chosen over the team's "bundling" guideline, so design re-deliveries don't wipe the wiring).
- Login title becomes "F.R.Cont WorkFlow" (team suggestion).
- Links and phone list search: free text over everything plus tag filters (what the design already does); the backend stores tags.
- Team guideline "funcionários → colaboradores": all visible labels change now; file/route names (`funcionarios.html`) change in the Colaboradores plan.

## Global Constraints

- No new Python or JS dependencies. No JS test framework: frontend steps are verified by hand in the browser.
- API JSON keys are English camelCase, error bodies are `{"error": "..."}` in English, like every existing route. UI text is Portuguese.
- Glue scripts must build DOM with `textContent` / `createElement`, never `innerHTML` with server data.
- All backend tests run from `backend/` with `.venv\Scripts\python -m pytest`; the whole suite must pass at the end of every task.
- Pages keep the design's relative asset paths; glue scripts are loaded with absolute paths (`/js/api.js`).
- Design pages not wired in this plan (centralpop, centrallink, checklist, listatelefonica, funcionarios) ship as the team's demo versions (browser-only data). This replaces the currently wired old pages on branch `feature-new-front` until their plans land.

## Review Focus

1. A tool URL of `javascript:alert(1)` or `data:...` is posted straight to the API (bypassing the form): expect 400, never stored. Test in Task 2.
2. A basic user sends `PUT`/`DELETE` for a tool someone else created: expect 403 and the row unchanged. Test in Task 2.
3. Deleting a tool that other users have opened (rows in `ToolUsage`, foreign keys ON): expect 200 and usage rows gone, not an IntegrityError 500. Test in Task 2.
4. An existing `backend/database.db` created before this change starts the app: expect the two new tables to appear and old data untouched. Test in Task 1.
5. A user with no photo loads any page: expect the default avatar icon, not an empty circle from a 404 background image. Manual check in Task 4.

---

### Task 1: Tool and ToolUsage tables

**Files:**
- Modify: `backend/schema.sql` (append)
- Test: `backend/tests/test_db.py` (append)

**Interfaces:**
- Produces tables:

```sql
CREATE TABLE IF NOT EXISTS "Tool" (
    "tool_id" INTEGER PRIMARY KEY AUTOINCREMENT,
    "created_by" INTEGER NOT NULL,
    "tool_name" TEXT NOT NULL,
    "tool_description" TEXT,
    "tool_url" TEXT NOT NULL,
    "tool_category" TEXT,
    "tool_icon" TEXT,
    "created_at_utc" TEXT,
    "updated_at_utc" TEXT,
    FOREIGN KEY ("created_by") REFERENCES "User"("user_id")
);
CREATE TABLE IF NOT EXISTS "ToolUsage" (
    "user_id" INTEGER NOT NULL,
    "tool_id" INTEGER NOT NULL,
    "open_count" INTEGER NOT NULL DEFAULT 0,
    "last_opened_at_utc" TEXT,
    PRIMARY KEY ("user_id", "tool_id"),
    FOREIGN KEY ("user_id") REFERENCES "User"("user_id"),
    FOREIGN KEY ("tool_id") REFERENCES "Tool"("tool_id")
);
```

- [ ] **Step 1:** Write failing tests in `test_db.py`: `test_tool_tables_exist` (both names in `sqlite_master` after `create_app`) and `test_tool_tables_added_to_old_database` (create a db file containing only a `"User"` table with one row, call `create_app` on it, assert both tables exist and the user row is still there).
- [ ] **Step 2:** Run `python -m pytest tests/test_db.py -v`; expect the two new tests to FAIL.
- [ ] **Step 3:** Append the SQL above to `schema.sql`.
- [ ] **Step 4:** Run the same command; expect PASS.
- [ ] **Step 5:** Stage; wait for review before committing (`feat: add Tool and ToolUsage tables`).

### Task 2: Tools repository and API

**Files:**
- Create: `backend/repositories/tools.py`, `backend/routes/tools.py`, `backend/tests/test_tools.py`
- Modify: `backend/app.py` (import `tools` and add it to the blueprint loop)

**Interfaces:**
- Consumes: `get_db`, `utc_now`, `login_required`, `current_user`, `json_field`, `to_http` (already handles `"forbidden"` → 403).
- Produces repository functions in `repositories/tools.py`:
  - `get_all(user_id) -> list[dict]`, ordered by `tool_id`, each dict `{"id", "name", "description", "url", "category", "icon", "createdBy", "opens", "lastOpenedAtUtc"}`; `opens`/`lastOpenedAtUtc` come from a LEFT JOIN on that user's `ToolUsage` row (`0` / `None` when absent).
  - `add(user_id, name, description, url, category, icon) -> int`
  - `update(tool_id, user_id, role, name, description, url, category, icon) -> "ok" | "not_found" | "forbidden"`
  - `delete(tool_id, user_id, role) -> "ok" | "not_found" | "forbidden"` (deletes the tool's `ToolUsage` rows first, same transaction)
  - `record_open(tool_id, user_id) -> "ok" | "not_found"` (upsert: `INSERT ... ON CONFLICT(user_id, tool_id) DO UPDATE SET open_count = open_count + 1, last_opened_at_utc = ?`)
  - Permission rule inside `update`/`delete`: allowed when `role == "admin"` or `created_by == user_id`.
- Produces routes (all `@login_required`, prefix `/api`):

| Route | Success body |
|---|---|
| `GET /tools` | list from `get_all`, each item plus `"canEdit": bool` |
| `POST /tools` | `{"message": "Tool created.", "id": n}` |
| `PUT /tools/<int:tool_id>` | `{"message": "Tool updated."}` |
| `DELETE /tools/<int:tool_id>` | `{"message": "Tool deleted."}` |
| `POST /tools/<int:tool_id>/open` | `{"message": "Open recorded."}` |

- Request body for POST/PUT: `{"name", "description", "url", "category", "icon"}`, strings, all stripped.
- Validation, shared by POST and PUT via one helper `_read_tool()` in the route file, first failure wins:
  - `name` empty or longer than 100 → 400 `{"error": "Name is required (max 100 characters)."}`
  - `url` not starting with `http://` or `https://` (case-insensitive), or longer than 2000 → 400 `{"error": "URL must start with http:// or https://."}`
  - `description` longer than 120 → 400 `{"error": "Description must have at most 120 characters."}`
  - `category` longer than 50 → 400 `{"error": "Category must have at most 50 characters."}`
  - `icon` not matching `^bi-[a-z0-9-]+$` is stored as `"bi-tools"` (no error).
- 404 body: `{"error": "Tool not found."}`; 403 body: `{"error": "Forbidden."}`.

- [ ] **Step 1:** Write `tests/test_tools.py` using `login_basic`, `login_admin`, `register`, `login`, `run_sql` from `tests/conftest.py`. Tests (names fixed):
  - `test_unauthenticated`: all five routes → 401.
  - `test_create_and_list`: basic user posts `{"name": "  Calc  ", "description": "d", "url": "https://a.com", "category": "Calculadoras", "icon": "bi-calculator"}` → `{"message": "Tool created.", "id": 1}`; list item equals those values trimmed, with `createdBy == 1`, `opens == 0`, `lastOpenedAtUtc is None`, `canEdit is True`; key set is exactly the nine repository keys plus `canEdit`.
  - `test_create_validation`: each rule above returns its exact error and 400, including `url` values `"javascript:alert(1)"`, `"data:text/html,x"`, `"ftp://a"`, `""`, `123`.
  - `test_bad_icon_falls_back`: icon `"x onclick=1"` → stored `"bi-tools"`.
  - `test_owner_can_update_and_delete`.
  - `test_other_basic_user_is_forbidden`: second basic client gets 403 on PUT and DELETE, sees `canEdit is False`, and the tool is unchanged in the list.
  - `test_admin_can_update_and_delete_any`.
  - `test_update_and_delete_missing`: id 999 → 404 `{"error": "Tool not found."}`.
  - `test_open_counts_per_user`: user A opens twice, user B once; A's list shows `opens == 2` and a non-null `lastOpenedAtUtc`, B's shows `1`; opening id 999 → 404.
  - `test_delete_tool_with_usage`: after another user opened it, owner DELETE → 200 and `SELECT COUNT(*) FROM "ToolUsage"` is 0.
- [ ] **Step 2:** Run `python -m pytest tests/test_tools.py -v`; expect FAIL (404s / import error).
- [ ] **Step 3:** Implement `repositories/tools.py` with the signatures above.
- [ ] **Step 4:** Implement `routes/tools.py` (`bp = Blueprint("tools", __name__)`) and register it in `app.py`.
- [ ] **Step 5:** Run `python -m pytest -v` (whole suite); expect PASS.
- [ ] **Step 6:** Stage; wait for review (`feat: add tools API`).

### Task 3: New design into wwwroot, logo, old pages removed

**Files:**
- Copy from `DESIGN` into `wwwroot/`: `index.html`, `login.html`, `css/style.css`, `css/paginas.css`, all of `html/`, and `js/` except `cadastro.js` (its page no longer exists).
- Delete from `wwwroot/`: `html/abaguia.html`, `html/cadastro.html`, `html/guia.html`, `js/abaguia.js`, `js/cadastro.js`, `js/guia.js`, and every old `css/*.css` (`abaguia`, `centrallink`, `centralpop`, `checklist`, `feedback`, `guia`, `header`, `index`).
- Keep: `wwwroot/js/api.js`, `wwwroot/assets/Logo.svg`.
- Modify: the 8 copied pages with the side menu, `wwwroot/login.html`, `wwwroot/css/paginas.css`, `backend/tests/test_pages.py`, `README.md` (page list and "how to run" only).

**Interfaces:**
- Produces: in every side menu, the brand block becomes

```html
<a class="header-logo menu-marca" href="..."><img class="logo-img" src="/assets/Logo.svg" alt="F.R.Cont"></a>
```

  (the `logo-circulo` and `logo-texto` spans are removed; the SVG already contains the name). CSS added to `paginas.css`: `.logo-img { height: 3.25rem; width: auto; }`. The SVG is solid black: if the menu or login background is dark, add `filter: invert(1)` for that context (and for `[data-tema="escuro"]` where the background flips). Check both themes by eye.
- Produces: every `<script src=".../js/header.js" defer>` gets `<script src="/js/api.js"></script>` before it; `login.html` gets the same before its inline script.
- Produces: the menu item for Funcionários gets the attribute `data-so-admin` on its `<li>` in all 8 pages (used in Task 4). Team guideline: collaborators don't see this module.
- Produces: every visible "Funcionário(s)"/"funcionário(s)" text in the copied HTML/JS becomes "Colaborador(es)"/"colaborador(es)" (menu, titles, placeholders, `Nome do funcionário`), keeping gender/number agreement. File names and ids unchanged.
- Produces: `login.html` `<h1>Bem-vindo!</h1>` becomes `<h1>F.R.Cont WorkFlow</h1>`.
- Produces: in `js/menu-usuario.js` the photo hint "JPEG, PNG or WebP, até 2 MB" becomes "JPEG, PNG ou WebP, até 2 MB" (matches the backend's 2 MB limit).

- [ ] **Step 1:** Update `test_pages.py::test_pages_and_assets_are_served` to check `/login.html`, `/html/ferramentas.html`, `/css/style.css`, `/js/header.js`, `/js/api.js`, and `/assets/Logo.svg` (mimetype `image/svg+xml`); add `test_old_pages_are_gone` asserting 404 for `/html/guia.html`, `/html/abaguia.html`, `/html/cadastro.html`.
- [ ] **Step 2:** Run `python -m pytest tests/test_pages.py -v`; expect FAIL.
- [ ] **Step 3:** Copy and delete the files listed above.
- [ ] **Step 4:** Apply the logo, `api.js`, `data-so-admin`, "colaborador", login title and photo-hint edits; add the CSS. Check with `grep -ri "funcion" wwwroot --include=*.html --include=*.js`: only file names, ids and code identifiers may remain.
- [ ] **Step 5:** Run the whole suite; expect PASS. Start the app (`python app.py` in `backend/`) and open `/login.html` and `/` in both themes: logo visible, no broken styles, no console 404s.
- [ ] **Step 6:** Update `README.md`. Stage; wait for review (`feat: adopt new frontend design`).

### Task 4: Login, session header, logout, photo, change password

**Files:**
- Modify: `wwwroot/login.html` (inline script), `wwwroot/js/header.js`, `wwwroot/js/menu-usuario.js`, `wwwroot/css/paginas.css`, the 8 pages' user menu (one new `<li>`).

**Interfaces:**
- Consumes: `POST /api/auth/login {email, password}`, `GET /api/auth/me -> {id, name, email, role}`, `POST /api/auth/logout`, `PUT /api/me/photo` (multipart field `photo`), `GET /api/users/<id>/photo`, `PUT /api/me/password {currentPassword, newPassword}` (min 8 characters).
- Produces: `window.usuario`: a Promise resolving to the `/api/auth/me` object, set by `header.js`. Later glue scripts `await window.usuario`.
- Produces: `document.documentElement.dataset.papel = user.role`, and CSS in `paginas.css`:

```css
[data-so-admin] { display: none; }
html[data-papel="admin"] [data-so-admin] { display: revert; }
```

- [ ] **Step 1: login.html.** Replace the "Login indisponível" stub with the commented block, rewritten to use `api("POST", "/api/auth/login", {email, password})`; on error show "E-mail ou senha inválidos." in `#mensagem`; on success go to `/`. Keep the existing show-password and remember-email code. Drop the unused `remember` field.
- [ ] **Step 2: header.js.** Set `window.usuario = api("GET", "/api/auth/me")` (the helper already redirects to login on 401). When it resolves: set `dataset.papel`, call `definirUsuario({nome: user.name})`, and load the photo by creating an `Image` with `src = "/api/users/" + user.id + "/photo"` and calling `definirFotoUsuario(src)` only in its `onload` (no photo means 404, `onerror`, default icon stays). Wire `#menu-sair` click: `preventDefault`, `api("POST", "/api/auth/logout")`, then go to `/login.html`.
- [ ] **Step 3: menu-usuario.js photo.** Remove `CHAVE_FOTO` and its `ler`/`gravar` uses. On "Salvar foto": `canvas.toBlob` as `image/jpeg` quality 0.85, send with `fetch("/api/me/photo", {method: "PUT", body: formData})` (field name `photo`; `api()` is JSON-only), show the backend's `error` text in `#modal-erro` on failure, otherwise `definirFotoUsuario` with the preview and close. Keep the canvas in a variable instead of only the data URL.
- [ ] **Step 4: change password.** Add `<li><button type="button" id="menu-senha">Alterar senha</button></li>` after the theme item in all 8 pages. In `menu-usuario.js`, build a `<dialog class="modal">` on first use, the same way `criarModal()` builds the photo dialog: two password inputs (current, new with `minlength="8"`), a `.form-message` paragraph with `role="alert"`, Cancelar / Salvar. Salvar calls `api("PUT", "/api/me/password", {currentPassword, newPassword})`; map errors to "Senha atual incorreta." / "A nova senha precisa de pelo menos 8 caracteres."; on success close and clear the inputs.
- [ ] **Step 5: verify by hand** with a seeded admin and a basic user (`python seed.py`): wrong password shows the message; login lands on the hub with the right name; Funcionários menu item visible only for the admin; photo upload survives reload and shows on another browser; user with no photo shows the default icon; change password works and the old password stops working; logout returns to login and `/` redirects back to login.
- [ ] **Step 6:** Run the whole backend suite (unchanged, must still pass). Stage; wait for review (`feat: wire login, session header and profile actions`).

### Task 5: Ferramentas page glue

**Files:**
- Create: `wwwroot/js/ferramentas-api.js`
- Modify: `wwwroot/html/ferramentas.html` (one script tag after `ferramentas.js`: `<script src="/js/ferramentas-api.js" defer></script>`), `wwwroot/js/ferramentas.js` (one condition).

**Interfaces:**
- Consumes: Task 2 routes; `window.ferramentas.renderizar(lista)`; events `ferramenta:abrir {id}`, `ferramenta:salvar {id, nome, descricao, link, categoria, icone}`, `ferramenta:excluir {id}`.
- Field mapping (API → design): `id→id, name→nome, description→descricao, url→link, category→categoria, icon→icone, opens→aberturas, lastOpenedAtUtc→ultimaAbertura, canEdit→podeEditar`.
- Change in `ferramentas.js` `card()`: the edit/delete buttons block runs only when `!compacto && f.podeEditar`.

- [ ] **Step 1:** Write `ferramentas-api.js`: a `carregar()` function that GETs `/api/tools`, maps the fields and calls `renderizar`; listeners that call POST (empty `id`) or PUT on `ferramenta:salvar`, DELETE on `ferramenta:excluir`, and POST `/open` on `ferramenta:abrir`, each followed by `carregar()`. Errors go to `alert(error.message)` (the design has no page-level message area; `shortcut:` comment saying so).
- [ ] **Step 2:** Apply the `podeEditar` condition and the script tag.
- [ ] **Step 3: verify by hand:** add a tool as a basic user; it lists with edit/delete buttons. Log in as another basic user: tool visible, no buttons. As admin: buttons visible, edit and delete work. Click a tool three times: it appears under "Recentes" after reload, and not for the other user. Search and category filter still work.
- [ ] **Step 4:** Stage; wait for review (`feat: connect Ferramentas page to the API`).

### Task 6: Feedback page and hub

**Files:**
- Create: `wwwroot/js/feedback-api.js`, `wwwroot/js/hub-api.js`
- Modify: `wwwroot/html/feedback.html`, `wwwroot/index.html` (script tags; feedback also gets one list section).

**Interfaces:**
- Consumes: `POST /api/feedback {description}`, `GET /api/feedback` (admins get all, others their own), `POST /api/feedback/<id>/answer {answer}`, `POST /api/feedback/<id>/close`, `GET /api/pops`, `GET /api/me/checklists`, `GET /api/me/departments`, `GET /api/tools`, `window.usuario`. Read `backend/repositories/feedback.py`, `pops.py`, `checklists.py` and `user_departments.py` `_to_dict` functions for the exact response keys before writing the glue.
- Feedback description sent as `assunto + "\n\n" + motivo` (the backend has one text field).

- [ ] **Step 1: feedback-api.js.** On form submit: POST, reset the form, show "Feedback enviado." in a `role="status"` paragraph added under the form. Below the form add `<section class="panel hub-bloco"><h3>Feedbacks enviados</h3><ul class="hub-lista" id="lista-feedback"></ul></section>`: each item shows the text, status (aberto / respondido / fechado) and the answer if any. For admins each open item also gets a textarea plus "Responder" and a "Fechar" button calling the two admin routes, then reloading the list.
- [ ] **Step 2: hub-api.js.** Fill `#hub-nome` (user name), `#hub-departamentos` (department names joined by " · ", or "Sem departamento"), `#stat-pops` (count of `/api/pops`), `#stat-checklists` (count of `/api/me/checklists` without a completion date), `#lista-pops-recentes` (5 most recently updated POPs), `#lista-continuar` (unfinished checklists), `#lista-ferramentas-recentes` (up to 4 tools with `opens > 0`, most opened first, as links with `rel="noopener noreferrer"` and `target="_blank"`). Leave `#stat-links` as "–": `GET /api/links` is admin-only until the Links plan. Each list keeps the design's "empty" `<li>` when there is nothing to show.
- [ ] **Step 3: verify by hand:** basic user sends feedback and sees it listed; admin sees it, answers, closes; basic user sees the answer. Hub shows real name, departments, counts and recent tools.
- [ ] **Step 4:** Run the whole backend suite. Stage; wait for review (`feat: connect feedback and hub pages`).

---

## Verification (end to end)

1. `cd backend; .venv\Scripts\python -m pytest -v`: all tests pass, including the new `test_tools.py` and updated `test_pages.py` / `test_db.py`.
2. `.venv\Scripts\python seed.py` then `.venv\Scripts\python app.py`; open `http://127.0.0.1:5000/`.
3. Walk the manual checks in Tasks 3 to 6 with one admin and two basic users, in light and dark theme, on a narrow window (mobile menu).
4. Copy an older `database.db` into place and start the app: it starts, old data intact, Ferramentas works.

## Not in this plan (roadmap, with the team's guidelines mapped)

- **Plan 2, Colaboradores:** rename page/file; cleaner layout; basic users see their own department(s); fix the broken line under the department filter; "delete" = deactivate (`is_active = 0`). Open team question: do collaborators have a phone number? (`User` has no phone column today.)
- **Plan 3, Central Links + Lista telefônica:** extend `Link`/`PhoneNumber` with the design's fields; shared tag storage for both pages; add/delete filters on both pages; who may create/delete filters (team: "tirar opções de adicionar filtros" for collaborators).
- **Plan 4, POPs:** file upload; add/archive; store and show the date a POP was added (`created_at_utc` exists); remove the category filter (Protocolo, Manual…) from the floating panel; feedback button under each POP (`POST /api/feedback` already takes `popId`); clear path for a collaborator with no POP: create one or request it via feedback. Also covers ER tables that no page uses yet: a "Links e contatos deste POP" section in the POP view/form, backed by `PopLink` and `PopPhone` (routes `/api/pop-links`, `/api/pop-phones` already exist; needs a layout from the front team), and admin management of the POP's standard checks (`StandardCheck`, routes `/api/pops/<id>/standard-checks` already exist) in the POP form, so POP checklists in plan 5 are not empty. Depends on plan 3's extended Link/PhoneNumber fields to show useful names.
- **Plan 5, Checklist:** remove the "visão administrativa" bar; personal tasks plus POP checklists, with the option to link a POP's checklist to the personal list.
- **Plan 6, Tutorial:** site-wide tutorial plus a tutorial POP (menu "Tutorial" link stays `#` until then).
- Cross-cutting team guidelines (icons and short words, page standardization) are applied page by page in the plan that touches each page.
- Updating the ER diagram image: add `Tool` (many-to-one to `User` via `created_by`) and `ToolUsage` (junction `User` × `Tool`) when you next edit it.

### Order and dependencies

Run the plans in order **2 → 3 → 4 → 5 → 6**:
- Plan 2 first: departments and users feed every other page (POP visibility, phone list departments, hub).
- Plan 3 before plan 4: the POP's "Links e contatos" section needs the extended Link/PhoneNumber fields (title, name) to show anything useful.
- Plan 4 before plan 5: POP checklists are built from `StandardCheck`, which plan 4 lets admins manage.
- Plan 4 is blocked on a layout from the front team for the "Links e contatos deste POP" section; ask for it before plan 4 starts.

### ER diagram changes per plan

Update the ER image as each plan lands:
- **Now (plan 1):** add `Tool` (FK `created_by` → `User`) and `ToolUsage` (PK `user_id` + `tool_id`, FKs to `User` and `Tool`, `open_count`, `last_opened_at_utc`). Also fix two old mismatches in the image: `User` lists `updated_at_utc` twice, and `user_session_version` is missing.
- **Plan 2:** none expected. If the team says collaborators have a phone, add a phone column to `User`.
- **Plan 3:** new columns on `Link` (title, description, subject) and `PhoneNumber` (contact name, department, extension, email); tag tables shared by both pages (e.g. `Tag`, `LinkTag`, `PhoneTag`).
- **Plan 4:** icon on `Department`; category on `Pop`; the uploaded file location in `pop_file_path` (existing column).
- **Plan 5:** a personal task table (e.g. `PersonalTask`, FK `user_id`), optionally linked to a `Checklist`.

### Plan 1 follow-ups (from the final review, deferred)

Small fixes to do at the start of plan 2 (or any time):
- `ferramentas.html`: `maxlength="100"` on the name and `maxlength="2000"` on the link, so the modal doesn't close and lose input on a 400.
- `login.html` and `menu-usuario.js`: show the specific Portuguese message only for wrong credentials / wrong current password; otherwise show the server's error text.
- `hub-api.js`: count only `status === 'published'` POPs.
- `hub-api.js`, `feedback-api.js`: add `.catch(function () {})` after `window.usuario.then(...)`.
- `paginas.css`: replace the two `[data-so-admin]` rules with `html:not([data-papel="admin"]) [data-so-admin] { display: none; }`.
- `routes/tools.py`: require a host after the scheme (`https?://[^\s/]+`), with a test.
- Tool category: limit to the form's options server-side, or keep unknown values when editing.
- Colaboradores page guard for non-admins (plan 2).
