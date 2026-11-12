# Handoff: F.R.Cont WorkFlow (atualizado 2026-11-11)

Ponto de partida para a próxima sessão. Detalhes em `docs/superpowers/plans/`.

## Sistema em 4 linhas
- Flask (`backend/app.py`) serve as páginas de `wwwroot/` e a API `/api/...`; SQLite em `backend/database.db`.
- Padrão do backend: `routes/` valida (erros em inglês), `repositories/` faz o SQL, `tests/` em pytest (suíte completa ≈ 9 min, hash de senha é lento de propósito).
- Front do time de design + um script de ligação nosso por página (`wwwroot/js/<pagina>-api.js`) usando `api.js`; `header.js` expõe `window.usuario` e marca `data-papel` (itens `[data-so-admin]` só para admin).
- Rodar local: `.env` com `SECRET_KEY`, `python seed.py` (usuários de teste, senha `mypassword123`), `python app.py` → http://127.0.0.1:5000.

## Estado
| Plano | Situação |
|---|---|
| 1 Fundação + Ferramentas | ✅ commitado (`b3990d2`) |
| Ajustes pendentes do plano 1 | ✅ feitos, **sem commit** |
| 2 Colaboradores (`plans/2026-11-11-colaboradores.md`) | ✅ feito + revisado + correções, **sem commit** (205 testes passando) |
| 3 Central de Links + Lista telefônica | ⏭️ próximo: escrever o plano |
| 4 POPs (+ PopLink/PopPhone, StandardCheck) | depois do 3 |
| 5 Checklist | depois do 4 |
| 6 Tutorial | por último |

Primeiro passo da próxima sessão: confirmar que o Eduardo commitou o plano 2; então escrever o plano 3.

## Decisões já tomadas (não perguntar de novo)
- Ferramentas: qualquer um cria; só criador ou admin edita/exclui. "Recentes" por usuário.
- Ligação em arquivos `*-api.js` separados (não fazer bundling por enquanto).
- Login com título "F.R.Cont WorkFlow"; "funcionário" → "colaborador" em todo texto visível.
- Colaboradores: sem telefone; todos veem o item do menu, colaborador comum só vê os próprios departamentos e colegas; "Excluir" = desativar (reativar na tabela com "Mostrar inativos" ou na ficha).
- Datas = dias de São Paulo (UTC-3 fixo; sistema só roda em SP); data final inclusiva; datas passadas recusadas.
- Um acesso por departamento por vez (sem períodos múltiplos).
- URLs de ferramentas validadas por completo; erro mostra o passo a passo de copiar o link no Chrome.
- Busca em Links e Lista telefônica: texto livre + filtros por tag (o backend guarda as tags).
- Ordem dos planos 2 → 3 → 4 → 5 → 6.

## Pendências e decisões em aberto
- Plano 3: estender `Link` (título, descrição, assunto) e `PhoneNumber` (nome, departamento, ramal, e-mail); tags compartilhadas; decidir quem cria/apaga filtros (o time pediu tirar isso do colaborador comum); liberar leitura de links para todos (Hub mostra "–" hoje).
- Plano 4: pedir ao time o layout da seção "Links e contatos deste POP".
- Plano 5 (layout definido pelo Eduardo): checklists de POP na coluna da direita (título do POP + texto personalizado), pessoais na esquerda.
- Imagem do ER: adicionar Tool/ToolUsage, tirar o `updated_at_utc` duplicado de User, incluir `user_session_version`.
- Minors aceitos (não corrigir sem pedido): página Colaboradores só escondida para quem digitar a URL não-admin (as APIs são protegidas); contagem/ filtro contam acessos agendados.

## Como trabalhar com o Eduardo
- Nunca commitar/push; ele revisa e commita.
- Perguntas de decisão em múltipla escolha; respostas em português.
- Fluxo por plano: perguntas → plano escrito → implementação (eu mesmo; grunt para trabalho mecânico) → testes no navegador (playwright-core + Chrome, banco temporário no scratchpad, nunca `database.db`) → revisão final por um revisor novo → resumo.
