# Plan 2: Colaboradores Implementation Plan

> **Status (2026-11-11):** done, reviewed and fixed; not yet committed. 205 backend tests passing.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (native, chosen for plan 1) to implement this plan task-by-task. Do **not** commit: Eduardo commits after review. "Stage" below means leave the changes in the working tree.

**Goal:** The Colaboradores page manages real users and department access for admins, and shows collaborators their own departments and colleagues.

**Architecture:** Same pattern as plan 1. The backend gets three small extensions in existing route/repository files plus one new read route. The page HTML loses its demo rows. A new glue script `wwwroot/js/colaboradores-api.js` renders the table, departments tab and profile ("ficha") from the API. The team's `funcionarios.js` keeps the UI behavior (tabs, modals, filters, period presets) and gets small changes so it works with rows created at runtime.

**Tech Stack:** Flask, sqlite3, pytest; plain JS. No new dependencies.

**Spec:** Decisions below plus plan 1 (`docs/superpowers/plans/2026-11-10-foundation-ferramentas.md`) Global Constraints, which still apply.

## Decisions (Eduardo, 2026-11-11)

- No phone for collaborators: remove the Telefone field and lines from the page (contacts stay in Lista telefônica). No schema change.
- Every logged-in user sees the "Colaboradores" menu item. Admins see the full page. Collaborators see only the Departamentos tab, filtered to their own current departments and colleagues, with no management buttons.
- "Excluir colaborador" becomes "Desativar" (`is_active = 0`). Inactive users disappear from the list; a "Mostrar inativos" checkbox shows them with a "Reativar" action. History (POPs, checklists, feedback) is kept.
- The profile's "Tarefas" section is removed until plan 5. Recorded for plan 5: on the Checklist page, checklists from a POP go in the **right** column with title = POP title + custom text; personal checklists go in the **left** column with their own title.
- Department create/rename stays out of this page (the design says it lives in POP's, plan 4).
- Files are renamed `funcionarios.*` → `colaboradores.*` (team guideline), including every menu link.

## Global Constraints

- Plan 1's constraints: English API JSON and errors, Portuguese UI text, no `innerHTML` with server data, full backend suite green at the end of each task.
- Dates from `<input type="date">` (`YYYY-MM-DD`) are São Paulo days (Eduardo: the system only runs in SP; fixed UTC-3, no DST since 2019), stored in the UTC text format `%Y-%m-%dT%H:%M:%S.%fZ`: start = `YYYY-MM-DDT03:00:00.000000Z`, end (inclusive) = next day `T02:59:59.999999Z`. End dates in the past are refused.
- An admin can't deactivate or change the role of their own account (already enforced by `PUT /users/<id>`).

## Review Focus

1. A temporary access with end date before the start date, or a malformed date: 400, nothing stored. Test in Task 2.
2. Giving a second, overlapping membership in the same department (fixed + temporary): 409, as today. Test in Task 2.
3. Changing a user's email to one another user has (any case/spaces): 409, both rows unchanged. Test in Task 1.
4. A collaborator calling the admin list or another department's members: 403. Collaborator colleagues route never returns emails of people outside their departments. Test in Task 3.
5. A deactivated user who still has an open browser session: next request is 401 (existing session check). Manual check in Task 6.

---

### Task 1: Edit name and email

**Files:** Modify `backend/routes/users.py`, `backend/repositories/users.py`. Test: `backend/tests/test_edits.py` (append; read it first for existing PUT /users cases).

**Interfaces:**
- `PUT /api/users/<id>` (admin) also accepts `"name"` and `"email"` (strings). The "Nothing to change." check now includes them.
- Validation: `name` given but blank after strip → 400 `{"error": "Name can't be empty."}`; `email` given but blank or without `@` → 400 `{"error": "Enter a valid email."}`; email stored `strip().lower()`; email used by another user → 409 `{"error": "This email is already registered."}`.
- New repository function `users.update_profile(user_id, name, email) -> "ok" | "not_found" | "conflict"` (None = keep the field; sets `updated_at_utc`). The route calls it before `users.update` for role/active/password, and returns the first error.

- [ ] Tests: `test_admin_edits_name_and_email` (both change, `GET /api/admin/users` shows them, login works with the new email), `test_edit_validation` (blank name, blank email, `"abc"` email → exact errors), `test_edit_email_conflict` (`" BIA@test.com "` when Bia exists → 409, both users unchanged), `test_edit_missing_user` (404 `{"error": "User not found."}`), `test_basic_cannot_edit` (403).
- [ ] Run, see them fail; implement; run the file, then the whole suite.

### Task 2: Temporary access dates

**Files:** Modify `backend/routes/user_departments.py`, `backend/repositories/user_departments.py`. Test: `backend/tests/test_user_departments.py` (append).

**Interfaces:**
- `POST /api/user-departments` also accepts optional `"validFrom"` and `"expiresAt"` (`YYYY-MM-DD`). Converted as in Global Constraints. When omitted: valid from now, no expiry (today's behavior).
- Validation: a value that isn't a real `YYYY-MM-DD` date → 400 `{"error": "Dates must be YYYY-MM-DD."}`; end before start → 400 `{"error": "The end date can't be before the start date."}`.
- `user_departments.assign(user_id, department_id, access_type, valid_from=None, expires_at=None)`; existing callers unchanged.

- [ ] Tests: `test_assign_with_dates_stores_range` (row has the converted values), `test_future_access_not_active_yet` (start tomorrow: `GET /api/me/departments` for that user is empty; start today: it lists the department), `test_expired_access_gone` (insert an already-expired row with `run_sql`: not listed), `test_date_validation` (`"2026-13-01"`, `"15/11/2026"`, `123`, end < start → exact errors, nothing inserted), `test_overlap_conflict` (fixed membership then a temporary one in the same department → 409).
- [ ] Red, green, whole suite.

### Task 3: Admin user list with departments, and collaborator colleagues

**Files:** Modify `backend/repositories/users.py` (`list_all`), `backend/repositories/user_departments.py`, `backend/routes/user_departments.py`. Tests: `backend/tests/test_admin_tools.py` (update `test_admin_user_list`), `backend/tests/test_user_departments.py` (append).

**Interfaces:**
- `GET /api/admin/users`: each item gains `"departments": [{"id", "name", "accessType", "validFromUtc", "expiresAtUtc"}]`, the user's not-revoked, not-expired memberships (future ones included so the admin sees scheduled access), ordered by department name. One query for all users (no query per user).
- New `GET /api/me/colleagues` (`@login_required`): `[{"id", "name", "members": [{"id", "name", "temporary": bool}]}]` for the caller's current departments (same rule as `/api/me/departments`), members = that department's current members (same rule as `members()`), `temporary` = membership has `expiresAtUtc`. No emails.

- [ ] Tests: update `test_admin_user_list` expected dicts with `"departments": []`; `test_admin_user_list_includes_departments` (one fixed, one temporary with dates, one revoked → only the first two, with dates); `test_colleagues` (Ana and Bia in Fiscal, Caio in Pessoal: Ana sees Fiscal with Ana and Bia only; keys exactly as above); `test_colleagues_no_department` (`[]`); `test_colleagues_unauthenticated` (401); basic user on `/api/admin/users` stays 403.
- [ ] Red, green, whole suite.

### Task 4: Page cleanup and rename

**Files:** Rename `wwwroot/html/funcionarios.html` → `colaboradores.html`, `wwwroot/js/funcionarios.js` → `colaboradores.js`; modify the 8 pages' menus, `wwwroot/js/menu-usuario.js`, `wwwroot/css/paginas.css` (only if the filter fix below needs it), `backend/tests/test_pages.py`.

- Menu: every link `funcionarios.html` → `colaboradores.html`; remove `data-so-admin` from that `<li>` (everyone sees it).
- `colaboradores.html`:
  - Delete the demo `<tr>` rows, demo `.setor-card` articles, demo chips/temp items/colleagues in the ficha, the hard-coded `<option>`s of `#filtro-setor`, `#atribuir-setor`, `#temp-setor` (keep the placeholder option), the fixed checkboxes in `#modal-adicionar` (container gets `id="novo-setores"`), and the demo numbers `24`/`2` (use `–`).
  - Remove every Telefone field and line (`novo-telefone`, `edit-telefone`, `ficha-telefone` `<li>`).
  - Remove the "Tarefas" `<section>` from the ficha.
  - Rename "Excluir colaborador" → "Desativar colaborador" (menu items, ficha button, modal title); modal text: "O colaborador não conseguirá mais entrar. Você pode reativá-lo depois."; modal button "Desativar".
  - Add `<label class="opcoes"><input type="checkbox" id="mostrar-inativos"> Mostrar inativos</label>` to `.filtros-func`.
  - Give modal action buttons ids: `novo-salvar`, `edit-salvar`, `senha-redefinir`, `desativar-confirmar`, and add a `<p class="form-message" role="alert">` to each modal (`novo-mensagem`, `edit-mensagem`, `senha-mensagem`); `#modal-senha` input id `senha-nova` → `senha-temporaria`.
  - Mark admin-only blocks `data-so-admin`: `.func-topo` add button, `.summary-grid`, `.abas`, `#painel-funcionarios`, `#vista-ficha`.
  - Fix the "linha bugada abaixo do filtro de departamentos" (team task list): look at it in the browser first; fix in CSS only.
- `menu-usuario.js`: the change-password modal ids `senha-atual`, `senha-nova`, `senha-erro`, `senha-salvar`, `senha-cancelar` → prefixed `minha-` (they clash with this page's ids).
- `test_pages.py`: `/html/colaboradores.html` served, `/html/funcionarios.html` 404.

- [ ] Update `test_pages.py`, see it fail, do the rename and edits, run it green; `grep -rn "funcionarios" wwwroot` returns only CSS class/ids the design uses (`pagina-funcionarios`, `painel-funcionarios`, `busca-funcionario`, `lista-funcionarios`).

### Task 5: Colaboradores glue

**Files:** Create `wwwroot/js/colaboradores-api.js` (script tag after `colaboradores.js`, `defer`). Modify `wwwroot/js/colaboradores.js`.

**Changes in `colaboradores.js` (team script), minimal:**
- `[data-ver]` and the filter loop must work for rows added later: use one delegated `click` listener for `[data-ver]` that dispatches `colaborador:ver` with `{id}` before switching views; `filtrar()` is exposed as `window.colaboradores.filtrar` and also reads `#mostrar-inativos` (rows with `data-inativo` hidden unless checked).
- `#temp-conceder`: after its validation passes, dispatch `acesso:conceder` with `{departamento, inicio, fim}` instead of the TODO.

**`colaboradores-api.js` (admin):**
- Load `GET /api/admin/users` and `GET /api/departments` (active ones only in selects); render `#lista-funcionarios` rows with `createElement` (initials avatar, name, email, fixed department chips, temporary chips "Depto · até dd/mm", actions: Ver ficha / Redefinir senha / Desativar or Reativar), each `<tr>` with `data-id`, `data-setores` (department names joined by `|`), `data-inativo` when inactive. Fill `#resumo-total` (active users) and `#resumo-temporarios` (active users with at least one temporary membership), `#filtro-setor`, `#novo-setores` checkboxes, `#atribuir-setor`, `#temp-setor`.
- Departamentos tab: one `.setor-card` per active department from the same data (member count, names, "temporário" chip).
- Ficha (`colaborador:ver`): name, initials, email; "Departamentos fixos" chips with remove (DELETE `/api/departments/<d>/members/<u>`); assign (POST `/api/user-departments`, accessType `"member"`); temporary list with "Revogar" (same DELETE); `acesso:conceder` → POST with `accessType: "temporary"`, `validFrom`, `expiresAt`; "Colegas dos mesmos departamentos" from the loaded list.
- Modals: add (POST `/api/users`, then one POST `/api/user-departments` per checked department; the new user's id comes from reloading `GET /api/admin/users` and matching the email), edit (PUT name/email), reset password (PUT `{password}`), deactivate/reactivate (PUT `{isActive}`). Errors in the modal's message paragraph; modal closes only on success. After every change reload and re-render (and keep the ficha open on the same user).

**`colaboradores-api.js` (collaborator):** `GET /api/me/colleagues`; show only `#painel-setores` (unhide it), render one card per department from that data; nothing else is requested.

- [ ] `node --check` both files.

### Task 6: Browser verification

Same approach as plan 1 (playwright-core driving the installed Chrome, temporary database in the scratchpad, never `backend/database.db`). Check: admin adds a collaborator with two departments, edits name/email, resets the password (new password logs in), grants a 7-day temporary access (shows in list chip, summary count, ficha), revokes it, removes a fixed department, deactivates (user can't log in; their open session gets 401), "Mostrar inativos" + Reativar; collaborator sees only their departments' cards and no admin controls; the department filter line looks right; light/dark and mobile screenshots; no console errors except expected 401/404s.

## Not in this plan

Department create/rename/icon (plan 4); role change admin↔basic in the UI (API exists; not in the design); the checklist summary in the profile (plan 5).
