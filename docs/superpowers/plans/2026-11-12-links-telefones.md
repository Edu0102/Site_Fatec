# Plan 3: Central de Links + Lista telefônica Implementation Plan

> **Status (2026-11-12):** done, browser-checked, reviewed and fixed; not yet committed.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (native, as in plans 1-2) to implement this plan task-by-task. Do **not** commit: Eduardo commits after review. "Stage" below means leave the changes in the working tree.

**Goal:** Central de Links and Lista telefônica read and write real data: every logged-in user reads and searches, admins add/edit/delete items and manage each page's filters (tags).

**Architecture:** Same pattern as plans 1-2. `Link` gains title/description/subject; `PhoneNumber` becomes a contact (name, department, extension, phone, email). A new `Tag` table holds each page's filters (`tag_scope` = `link` or `phone`) with join tables `LinkTag`/`PhoneTag`. Two glue scripts (`centrallink-api.js`, `listatelefonica-api.js`) connect the team's page scripts to the API; admin-only controls get `data-so-admin`.

**Tech Stack:** Flask, sqlite3 (3.49), pytest; plain JS. No new dependencies.

**Spec:** Decisions below + plan 1 (`docs/superpowers/plans/2026-11-10-foundation-ferramentas.md`) Global Constraints + `docs/superpowers/HANDOFF.md`.

## Decisions (Eduardo, 2026-11-12)

- All logged-in users read links and contacts. **Only admins** create, edit and delete them (buttons hidden for collaborators, routes return 403).
- Filters: only admins see "Novo filtro" and the "x". Since only admins save items, a new tag typed in a link/contact creates the filter (the design already does this).
- Separate filter lists per page (one `Tag` table with a scope column).
- Deleting a link/contact that a POP uses always works and removes it from those POPs (and from its tags).
- Free-text search + all-checked-tags filtering stay in the browser, as the design does.

## Global Constraints

- English API JSON and errors, Portuguese UI text, no `innerHTML` with server data, full backend suite green at the end of each backend task.
- Link URLs use the same validation as Ferramentas (`http(s)`, real host, no spaces); the error in the page shows the same Chrome copy-the-link help text.
- `database.db` is never touched by tests or the browser check (temp DB in the scratchpad).

## Review Focus

1. An old database with Link/PhoneNumber rows referenced by PopLink/PopPhone: migration keeps the rows and ids, POP lists still return them. Test in Task 1.
2. Saving a tag typed with other casing ("federal" when "Federal" exists): reuses the existing filter, no duplicate. Test in Task 2.
3. Deleting a link/contact that is in a POP and has tags: 200, POP list no longer shows it, its tag rows are gone, the filter itself stays. Tests in Tasks 3 and 4.
4. A link URL `javascript:alert(1)`, `http://a b` or missing scheme: 400 with the web-address error, nothing stored. Test in Task 3.
5. A contact with `departmentId` of a missing department, a string, or a bool: 400, nothing stored; `null` is allowed. Test in Task 4.

---

### Task 1: Schema and migration

**Files:**
- Modify: `backend/schema.sql` (Link, PhoneNumber; new Tag, LinkTag, PhoneTag)
- Modify: `backend/db.py` (`init_db`, `_add_missing_columns`)
- Test: `backend/tests/test_db.py`

**Interfaces:**
- Produces the tables every later task uses:
  - `Link(link_id, link_title TEXT NOT NULL, link_description TEXT NOT NULL DEFAULT '', link_path TEXT NOT NULL UNIQUE` (holds the URL, name kept to avoid a rebuild)`, link_subject TEXT NOT NULL DEFAULT '', created_at_utc, updated_at_utc)`
  - `PhoneNumber(phone_id, contact_name TEXT NOT NULL, department_id INTEGER NULL → Department, phone_extension TEXT NOT NULL DEFAULT '', phone_number TEXT NOT NULL DEFAULT ''` (no longer UNIQUE)`, contact_email TEXT NOT NULL DEFAULT '', created_at_utc, updated_at_utc)`
  - `Tag(tag_id PK AUTOINCREMENT, tag_scope TEXT NOT NULL CHECK (tag_scope IN ('link','phone')), tag_name TEXT NOT NULL COLLATE NOCASE, UNIQUE (tag_scope, tag_name))`
  - `LinkTag(link_id → Link, tag_id → Tag, PRIMARY KEY (link_id, tag_id))`, `PhoneTag(phone_id → PhoneNumber, tag_id → Tag, PRIMARY KEY (phone_id, tag_id))`

- [ ] **Step 1: Write the failing tests** in `tests/test_db.py`:
  - `test_new_tables_exist`: fresh DB has `{"Tag", "LinkTag", "PhoneTag"}`.
  - `test_old_link_and_phone_tables_migrated`: build an old DB with the old `User` table (reuse `OLD_USER_TABLE`), the old `Link (link_id, link_path UNIQUE, created_at_utc, updated_at_utc)` and `PhoneNumber (phone_id, phone_number UNIQUE, ...)` tables, plus `Pop`, `PopLink`, `PopPhone` copied from the current schema; insert link 7 `"https://a.com"`, phone 9 `"1234"`, a POP and PopLink(pop,7)/PopPhone(pop,9). After `create_app`:
    - `SELECT link_id, link_title, link_path FROM "Link"` == `[(7, "https://a.com", "https://a.com")]`
    - `SELECT phone_id, contact_name, phone_number, department_id FROM "PhoneNumber"` == `[(9, "1234", "1234", None)]`
    - `PRAGMA foreign_key_check` returns `[]`; PopPhone row still joins to phone 9.
    - Inserting a second phone with number `"1234"` succeeds (UNIQUE dropped).
  - Calling `create_app` twice on the same file is a no-op the second time (no error, same rows).

- [ ] **Step 2: Run** `pytest tests/test_db.py -v` → the new tests FAIL.

- [ ] **Step 3: Implement.** New shapes in `schema.sql`. In `db.py`, migrate **before** `executescript(schema)`:
  - Link (if the table exists and lacks `link_title`): `ALTER TABLE ADD COLUMN` for the three new columns (`NOT NULL DEFAULT ''`), then `UPDATE "Link" SET link_title = link_path`.
  - PhoneNumber (if it exists and lacks `contact_name`): with `PRAGMA foreign_keys = OFF` and `PRAGMA legacy_alter_table = ON` (so PopPhone's reference is not rewritten), `ALTER TABLE "PhoneNumber" RENAME TO "PhoneNumber_old"`; let `executescript(schema)` create the new table; then `INSERT INTO "PhoneNumber" (phone_id, contact_name, phone_number, created_at_utc, updated_at_utc) SELECT phone_id, phone_number, phone_number, created_at_utc, updated_at_utc FROM "PhoneNumber_old"`, `DROP TABLE "PhoneNumber_old"`, commit, both pragmas back. The old number becomes the name because the old table had no name.
  - Keep the existing `user_session_version` step.

- [ ] **Step 4: Run** `pytest tests/test_db.py -v` → PASS.

---

### Task 2: Tags (filters) backend

**Files:**
- Create: `backend/repositories/tags.py`, `backend/routes/tags.py`
- Modify: `backend/app.py` (register `tags`), `backend/routes/__init__.py` (`json_tags`)
- Test: `backend/tests/test_tags.py`

**Interfaces:**
- Consumes: Task 1 tables.
- Produces:
  - `routes.json_tags() -> list[str] | None`: body `"tags"` missing → `[]`; a list of strings → trimmed, empties dropped, duplicates removed case-insensitively (first spelling kept); `None` when not a list, an item isn't a string, a name is over 40 chars, or more than 20 tags.
  - `repositories.tags`, where `scope` is `"link"` or `"phone"`:
    - `get_all(scope) -> [{"id": int, "name": str}]` ordered by name (NOCASE).
    - `add(scope, name) -> int | "conflict"`.
    - `delete(tag_id) -> bool` (also deletes its LinkTag/PhoneTag rows).
    - `names_for(scope, item_ids) -> dict[int, list[str]]` (one query; names sorted; items without tags absent).
    - `set_for(scope, item_id, names) -> None`: creates missing tags (`INSERT OR IGNORE`, NOCASE match reuses existing), replaces the item's join rows. **Does not commit**; the caller commits with the item save.
    - `clear_for(scope, item_id) -> None`: deletes the item's join rows, no commit.
  - Routes (`/api` prefix):
    - `GET /tags/<any(link, phone):scope>`: login required → `get_all(scope)`.
    - `POST /tags/<scope>`: admin, body `{"name"}`, 1..40 chars after trim, else 400 `"Filter name is required (max 40 characters)."`; duplicate → 409 `"This filter already exists."`; ok → `{"message": "Filter created.", "id": id}`.
    - `DELETE /tags/<int:tag_id>`: admin → `"Filter deleted."` / 404 `"Filter not found."`.

- [ ] **Step 1: Write the failing tests** in `tests/test_tags.py`:
  - unauthenticated → 401 on all three routes; basic user → 403 on POST/DELETE, 200 on GET.
  - `GET /api/tags/other` → 404.
  - create `"Federal"` then `"federal"` in scope link → 409; `"Federal"` in scope phone → 200 (separate lists).
  - GET link returns `[{"id": 2, "name": "Débitos"}, {"id": 1, "name": "Federal"}]` after adding Federal then Débitos (sorted).
  - name validation: `{}`, `"  "`, 41 chars, `123` → 400.
  - delete an existing tag → 200 and gone from GET; again → 404.
  - `json_tags` unit test inside an app request context: `[" A ", "a", "", "B"]` → `["A", "B"]`; `"A"` → None; `[1]` → None; `["x"*41]` → None; 21 names → None; missing → `[]`.
  - `set_for("link", ...)` with `["federal"]` when `"Federal"` exists → `names_for` gives `["Federal"]` and `get_all("link")` still has one tag (Review Focus 2; drive it through `POST /api/links` in Task 3 if easier, keep one test here using `app.app_context()` + a raw Link row via `run_sql`).

- [ ] **Step 2: Run** `pytest tests/test_tags.py -v` → FAIL.
- [ ] **Step 3: Implement** the functions and routes above. A dict `{"link": ("LinkTag", "link_id"), "phone": ("PhoneTag", "phone_id")}` picks the join table; table names never come from user input.
  `shortcut: NOCASE folds ASCII only ("Débitos" vs "DÉBITOS" are two tags), fold in Python if that shows up.`
- [ ] **Step 4: Run** `pytest tests/test_tags.py tests/test_db.py -v` → PASS.

---

### Task 3: Links backend

**Files:**
- Modify: `backend/repositories/links.py`, `backend/routes/links.py`, `backend/repositories/pop_links.py` (`list_for_pop` uses the new loader)
- Modify: `backend/routes/__init__.py` (move `_valid_url` from `routes/tools.py` here as `valid_url`; `tools.py` imports it)
- Test: rewrite `backend/tests/test_links.py` (keep its PopLink tests, adapted)

**Interfaces:**
- Consumes: `tags.set_for/clear_for/names_for`, `json_tags`, `valid_url(url) -> bool`.
- Produces:
  - Link JSON: `{"id", "title", "description", "url", "subject", "tags": [str], "createdAtUtc", "updatedAtUtc"}`; lists ordered by title (NOCASE). `pop_links.list_for_pop` returns the same shape.
  - `links.get_all()`, `links.add(title, description, url, subject, tags) -> int | "conflict"`, `links.update(link_id, title, description, url, subject, tags) -> "ok" | "not_found" | "conflict"`, `links.delete(link_id) -> bool` (deletes PopLink + LinkTag rows, then the link, one commit).
  - Routes: `GET /links` login required; `POST /links`, `PUT /links/<id>`, `DELETE /links/<id>` admin.
  - Validation (in this order, 400): title 1..150 `"Title is required (max 150 characters)."`; url → `"Enter a valid web address starting with http:// or https://."` (same text as tools); description ≤ 500 `"Description must have at most 500 characters."`; subject ≤ 100 `"Subject must have at most 100 characters."`; tags via `json_tags` → `"Tags must be a list of names up to 40 characters (max 20)."`.
  - Messages: `"Link created."` (+ `id`), `"Link updated."`, `"Link deleted."`, 404 `"Link not found."`, 409 `"A link with this address already exists."`.

- [ ] **Step 1: Write the failing tests** (replace the old path-based ones):
  - 401 for every route unauthenticated; basic user: `GET /api/links` 200, POST/PUT/DELETE 403.
  - admin creates `{"title": "  Receita  ", "url": "https://www.gov.br/receitafederal/", "description": "d", "subject": "Cadastral", "tags": ["Federal", "Consulta Pública"]}` → GET returns one item with trimmed title, tags `["Consulta Pública", "Federal"]`, and keys exactly the set above; `GET /api/tags/link` now lists both tags.
  - URL rejects: `javascript:alert(1)`, `http://a b`, `www.gov.br`, `""` → 400, `GET /api/links` still `[]` (Review Focus 4).
  - other validations: missing title, 151-char title, 501-char description, `"tags": "Federal"` → 400.
  - duplicate URL on create and on update → 409.
  - update replaces tags (`["Federal"]` → `["Estadual"]`) and bumps `updatedAtUtc` (reuse the `run_sql` trick from the old test).
  - delete: link with tags and assigned to a POP (`make_pop` + `POST /api/pop-links`) → 200; `GET /api/pops/1/links` → `[]`; `SELECT COUNT(*) FROM "LinkTag"` → 0; tag still in `GET /api/tags/link`; second delete → 404 (Review Focus 3).
  - existing PopLink tests keep passing with the new body (create links with title+url).
- [ ] **Step 2: Run** `pytest tests/test_links.py -v` → FAIL.
- [ ] **Step 3: Implement.** One `_read_link()` like `tools._read_tool()`. Add/update write the row and call `tags.set_for` before the single commit; a UNIQUE error rolls back and returns `"conflict"`.
- [ ] **Step 4: Run** `pytest tests/test_links.py tests/test_tags.py tests/test_tools.py -v` → PASS.

---

### Task 4: Contacts (phones) backend

**Files:**
- Modify: `backend/repositories/phones.py`, `backend/routes/phones.py`, `backend/routes/pop_phones.py` (still `phones.get_for_pop`)
- Test: rewrite `backend/tests/test_phones.py` (keep PopPhone tests, adapted)

**Interfaces:**
- Consumes: Task 2 tags helpers, `json_int`.
- Produces:
  - Contact JSON: `{"id", "name", "departmentId": int|None, "department": str|None, "extension", "phoneNumber", "email", "tags": [str], "createdAtUtc", "updatedAtUtc"}` (department name via LEFT JOIN), ordered by name (NOCASE). `get_for_pop` returns the same shape.
  - `phones.get_all()`, `phones.get_for_pop(pop_id)`, `phones.add(name, department_id, extension, phone_number, email, tags) -> int | "bad_department"`, `phones.update(phone_id, ...same) -> "ok" | "not_found" | "bad_department"`, `phones.delete(phone_id) -> bool` (PopPhone + PhoneTag rows, then the contact).
  - Routes: `GET /phones` login required; `POST /phones`, `PUT /phones/<id>`, `DELETE /phones/<id>` admin.
  - Validation (400): name 1..100 `"Name is required (max 100 characters)."`; `departmentId` missing/`null` → None, else must be a `json_int` → `"Department id must be a whole number."`, unknown → `"Department not found."`; extension ≤ 20, phoneNumber ≤ 30 → `"Extension and phone number must have at most 20 and 30 characters."`; email empty or matches `[^@\s]+@[^@\s]+\.[^@\s]+` and ≤ 254 → `"Enter a valid email address."`; tags as in Task 3.
  - Messages: `"Contact created."` (+ `id`), `"Contact updated."`, `"Contact deleted."`, 404 `"Contact not found."`.

- [ ] **Step 1: Write the failing tests:**
  - 401/403 matrix as in Task 3.
  - admin creates `{"name": "Maria", "departmentId": 1, "extension": "204", "phoneNumber": "(11) 4000-0000", "email": "maria@empresa.com", "tags": ["Matriz"]}` (insert Department 1 "Fiscal" with `run_sql`) → GET returns `department: "Fiscal"`, tags `["Matriz"]`; a second contact with the same phone number → 200 (no uniqueness).
  - `departmentId` 999, `"1"`, `true` → 400, nothing stored; `null` → 200 with `department: None` (Review Focus 5).
  - bad email `"maria@"` → 400; empty email → 200.
  - delete a contact in a POP with tags → 200, `GET /api/pops/1/phones` → `[]`, PhoneTag empty (Review Focus 3).
- [ ] **Step 2: Run** `pytest tests/test_phones.py -v` → FAIL.
- [ ] **Step 3: Implement.** A foreign-key IntegrityError on insert/update → `"bad_department"` → route answers 400 `"Department not found."`.
- [ ] **Step 4: Run the full suite** `pytest -q` (≈ 9 min) → all PASS.

---

### Task 5: Central de Links page

**Files:**
- Modify: `wwwroot/js/centrallink.js`, `wwwroot/html/centrallink.html`, `wwwroot/js/hub-api.js`
- Create: `wwwroot/js/centrallink-api.js`
- Test: `backend/tests/test_pages.py` (add `/js/centrallink-api.js` to the served-files list)

**Interfaces:**
- Consumes: Task 2-3 routes.
- Produces: `window.centralLinks = { renderizar(lista), definirFiltros(nomes) }` in `centrallink.js`, where `lista` items are `{id, titulo, descricao, url, assunto, tags, data}` (`data` = `dd/mm/aaaa`).

- [ ] **Step 1: `centrallink.js` edits** (keep the team's structure): `links` starts `[]`; `filtrosPadrao` starts empty and `definirFiltros` refills it in place; remove the sample link; add `window.centralLinks`; set `data-so-admin` on the edit/delete `.acoes-icone` div and on each filter's "x" button.
- [ ] **Step 2: `centrallink.html`:** `data-so-admin` on the "Adicionar link" button and on `#form-filtro`; add `<script src="../js/centrallink-api.js" defer></script>` after `centrallink.js`.
- [ ] **Step 3: `centrallink-api.js`** (same shape as `ferramentas-api.js`): `carregar()` = `GET /api/links` + `GET /api/tags/link` → `renderizar` (`data` from `updatedAtUtc` with `toLocaleDateString('pt-BR', {timeZone: 'America/Sao_Paulo'})`) + `definirFiltros(names)`, and keep a name → id map for deletes. Events: `link:salvar` → POST/PUT `{title, description, url, subject, tags}`; `link:excluir` → DELETE; `filtro:salvar` → POST `/api/tags/link`; `filtro:excluir` → DELETE `/api/tags/<id>`. Every call `.then(carregar).catch(avisar)`; `avisar` alerts (Chrome help text for the web-address error) and reloads so the optimistic UI goes back to the truth.
- [ ] **Step 4: Hub:** in `hub-api.js` replace the "–" comment with `GET /api/links` → `stat-links` = count.
- [ ] **Step 5: Run** `pytest tests/test_pages.py -v` → PASS.

---

### Task 6: Lista telefônica page

**Files:**
- Modify: `wwwroot/js/listatelefonica.js`, `wwwroot/html/listatelefonica.html`
- Create: `wwwroot/js/listatelefonica-api.js`
- Test: `backend/tests/test_pages.py` (add `/js/listatelefonica-api.js`)

**Interfaces:**
- Consumes: Tasks 2 and 4 routes, `GET /api/departments` (`[{id, name, code, isActive}]`), the existing `window.listaTelefonica` (`renderizar`, `definirDepartamentos`, `definirFiltros`).

- [ ] **Step 1: `listatelefonica.js` edits:** drop the hard-coded department names (start `[]`); `atualizarSetores` puts `<option value="">Sem departamento</option>` first; `data-so-admin` on the card's `.acoes-icone` and each filter "x".
- [ ] **Step 2: `listatelefonica.html`:** `data-so-admin` on `#btn-adicionar-contato` and `#form-filtro-contato`; script tag for `listatelefonica-api.js` after `listatelefonica.js`.
- [ ] **Step 3: `listatelefonica-api.js`:** load phones, `tags/phone` and active departments; map API → `{id, nome, setor: department || '', ramal: extension, telefone: phoneNumber, email, tags}`. `contato:salvar` → `departmentId` = id of the department (from the **full** list, so a contact in a now-inactive department keeps it) whose name equals `setor`, else `null`; body `{name, departmentId, extension, phoneNumber, email, tags}`. `contato:excluir`, `filtro:salvar`, `filtro:excluir` as in Task 5 with scope `phone`. Same `avisar` (no Chrome help needed here).
- [ ] **Step 4: Run** `pytest tests/test_pages.py -v` → PASS.

---

### Task 7: Browser check, review, handoff

- [ ] **Step 1:** Temp DB in the scratchpad, `seed.py` against it, run the app, and drive Chrome with playwright-core:
  - admin: add a link with a new tag (filter appears), bad URL shows the Chrome help, edit, filter by tag + search, delete; add/remove a filter; same for a contact with and without department; Hub "Links cadastrados" shows the count.
  - basic user: both pages list the items, no add/edit/delete buttons, no "Novo filtro" or "x"; checking filters still works.
- [ ] **Step 2:** Fresh reviewer on the whole diff (superpowers:requesting-code-review); fix what holds up; full suite green.
- [ ] **Step 3:** Update `docs/superpowers/HANDOFF.md` (plan 3 done, test count, next = plan 4) and the status line at the top of this plan. Do not commit.
