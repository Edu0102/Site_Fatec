# Plano 3.5: GitHub Action com os testes do backend

> **Status (2026-11-12):** feito; não commitado. A Action só roda depois do push.

**Objetivo:** a cada push e a cada pull request, o GitHub roda a suíte do backend e mostra ✅ ou ❌ no commit e no PR.

**Decisões (Eduardo, 2026-11-12):** só os testes (sem checagem do front nem navegador); plano curto agora, antes do plano 4 (em espera).

## Tarefa única: `.github/workflows/tests.yml`

- Gatilhos: `push` (qualquer branch) e `pull_request`.
- `ubuntu-latest`, Python 3.13 (a mesma versão do `backend/README.md`), cache do pip a partir de `backend/requirements.txt`.
- Passos: checkout → setup-python → `pip install -r requirements.txt` → `python -m pytest -q`, tudo em `backend/`.
- Sem segredos: os testes criam o app com a própria `SECRET_KEY` e um banco temporário; `database.db` e `.env` não são usados.
- `timeout-minutes: 30` (a suíte leva de 5 a 12 min localmente, porque o hash de senha é lento de propósito).
- `concurrency` cancela a execução anterior da mesma branch quando chega um push novo.

## Verificação

- O YAML é lido sem erro (checagem local).
- Depois do push: aba **Actions** do repositório mostra "Backend tests" verde. Se falhar só no Linux, ver o log da etapa "Run tests".
