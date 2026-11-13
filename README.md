# F.R.Cont WorkFlow (Site Fatec)

Portal interno da equipe: POPs, checklists, central de links, lista telefônica, ferramentas e colaboradores, com login e dados guardados no servidor.

## Sumário

- [Como rodar](#como-rodar)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Páginas e situação](#páginas-e-situação)
- [Permissões](#permissões)
- [Como o front fala com o backend](#como-o-front-fala-com-o-backend)
- [Testes](#testes)
- [Tecnologias](#tecnologias)

## Como rodar

Passo a passo completo em [backend/README.md](backend/README.md). Resumo:

1. Em `backend/`, crie o ambiente virtual e instale `requirements.txt`.
2. Crie `backend/.env` com `SECRET_KEY=<texto aleatório>`.
3. `python seed.py` cria os logins de teste (só em desenvolvimento; senha `mypassword123`):
   - `admin@test.com`: administrador
   - `basic@test.com`: colaborador comum
4. `python app.py` sobe o servidor em http://127.0.0.1:5000.

O Flask serve as páginas de `wwwroot/` e a API em `/api/...`. O banco é SQLite (`backend/database.db`). Ele é criado a partir de `schema.sql` e, ao subir, um banco antigo é atualizado automaticamente (colunas e tabelas novas).

## Estrutura do projeto

```text
Site_Fatec/
├── backend/
│   ├── app.py              # cria o app Flask e registra as rotas
│   ├── schema.sql          # tabelas do banco
│   ├── db.py               # conexão SQLite e migração de bancos antigos
│   ├── auth.py / security.py  # sessão, papéis (admin/colaborador) e hash de senha
│   ├── routes/             # validação de entrada e respostas HTTP (erros em inglês)
│   ├── repositories/       # SQL
│   ├── tests/              # pytest
│   └── seed.py             # logins e dados de teste
├── wwwroot/
│   ├── index.html          # Hub inicial
│   ├── login.html          # Login "F.R.Cont WorkFlow"
│   ├── html/               # demais páginas
│   ├── css/                # paginas.css, style.css
│   ├── js/                 # <pagina>.js (interface do time de design) + <pagina>-api.js (ligação com o backend)
│   └── assets/             # logo
└── docs/superpowers/       # planos de implementação e HANDOFF.md (estado atual do trabalho)
```

## Páginas e situação

| Página | Arquivos | Situação |
|---|---|---|
| Login | `login.html` | Ligada ao backend (sessão no servidor) |
| Hub inicial | `index.html`, `hub-api.js` | Ligado: nome, departamentos, POPs recentes, checklists abertos, links cadastrados, ferramentas recentes |
| Ferramentas | `ferramentas.html`, `ferramentas-api.js` | Ligada |
| Colaboradores | `colaboradores.html`, `colaboradores-api.js` | Ligada (usuários, departamentos, acessos temporários) |
| Central de Links | `centrallink.html`, `centrallink-api.js` | Ligada: busca, filtros por tag, cadastro pelo admin |
| Lista telefônica | `listatelefonica.html`, `listatelefonica-api.js` | Ligada: contatos com departamento, ramal, telefone, e-mail e tags |
| Feedback | `feedback.html`, `feedback-api.js` | Ligado |
| Central de POPs | `centralpop.html` | **Ainda local** (IndexedDB do navegador). A API de POPs já existe; a ligação é o plano 4 |
| Checklist | `checklist.html` | **Ainda local** (`localStorage`). A API existe; a ligação é o plano 5 |

## Permissões

- **Todos os logados:** leem links, contatos e ferramentas; criam ferramentas; veem os próprios departamentos e colegas.
- **Admin:**
  - cria, edita e exclui links e contatos, e gerencia os filtros (tags) de cada página;
  - gerencia colaboradores e acessos.
- **Ferramentas:** só quem criou ou um admin pode editar ou excluir.
- **Na interface:** itens só de admin levam o atributo `data-so-admin` e ficam escondidos para os outros. A proteção de verdade está na API (403).

## Como o front fala com o backend

- `js/api.js` tem a função `api(método, url, corpo)`, que faz todas as chamadas. Erros viram `Error` com a mensagem do backend, e uma resposta 401 leva para o login.
- `js/header.js` expõe `window.usuario` e marca `data-papel` no `<html>`.
- Cada página tem o script do time de design (interface, eventos como `link:salvar`) e um `*-api.js` nosso, que carrega os dados e responde a esses eventos.

## Testes

Em `backend/`: `python -m pytest` (214 testes; a suíte completa leva alguns minutos porque o hash de senha é lento de propósito).

O GitHub roda a mesma suíte sozinho a cada push e pull request (`.github/workflows/tests.yml`); o resultado aparece na aba **Actions** e no PR.

## Tecnologias

- Python 3.13, Flask, SQLite
- HTML5, CSS3, JavaScript sem framework
- Bootstrap Icons via CDN
