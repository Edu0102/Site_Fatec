/* colaboradores-api.js — liga a página Colaboradores (colaboradores.js) ao backend.
   Admin: lista, ficha, cadastro, edição, senha, desativar/reativar, departamentos e acesso temporário.
   Colaborador: só a aba Departamentos, com os próprios departamentos e colegas (/api/me/colleagues).
   Depende de api.js e de window.usuario (header.js). */
(function () {
    'use strict';

    var $ = function (s) { return document.querySelector(s); };
    var usuarios = [], departamentos = [], atual = null, alvo = null;

    function el(tag, classe, texto) {
        var e = document.createElement(tag);
        if (classe) e.className = classe;
        if (texto !== undefined && texto !== null) e.textContent = texto;
        return e;
    }

    function icone(nome) {
        var i = el('i', 'bi ' + nome);
        i.setAttribute('aria-hidden', 'true');
        return i;
    }

    function botao(texto, classe, dados) {
        var b = el('button', classe, texto);
        b.type = 'button';
        Object.keys(dados || {}).forEach(function (k) { b.dataset[k] = dados[k]; });
        return b;
    }

    function iniciais(nome) {
        var partes = (nome || '?').trim().split(/\s+/);
        return ((partes[0] || '')[0] + (partes.length > 1 ? partes[partes.length - 1][0] : '')).toUpperCase();
    }

    // Datas guardadas em UTC; mostradas no dia de São Paulo
    function dia(iso, comAno) {
        var o = { timeZone: 'America/Sao_Paulo', day: '2-digit', month: '2-digit' };
        if (comAno) o.year = 'numeric';
        return new Date(iso).toLocaleDateString('pt-BR', o);
    }

    function comecou(m) { return !m.validFromUtc || new Date(m.validFromUtc) <= new Date(); }
    function temporario(m) { return !!m.expiresAtUtc; }
    function porId(id) { return usuarios.filter(function (u) { return String(u.id) === String(id); })[0]; }
    function deptosAtivos() { return departamentos.filter(function (d) { return d.isActive; }); }

    // Erros do backend (em inglês) que esta página pode mostrar
    var TRADUCAO = {
        'Name, email and password are required.': 'Preencha nome, e-mail e senha.',
        'Password must have at least 8 characters.': 'A senha precisa de pelo menos 8 caracteres.',
        'This email is already registered.': 'Este e-mail já está cadastrado.',
        "Name can't be empty.": 'Informe o nome.',
        'Enter a valid email.': 'Informe um e-mail válido.',
        "You can't change your own role or active status.": 'Você não pode desativar a sua própria conta.',
        'This user is already assigned to the department.': 'O colaborador já tem acesso a este departamento.',
        "The end date can't be before the start date.": 'A data final não pode ser antes da inicial.',
        "The end date can't be in the past.": 'A data final já passou.',
        'Dates must be YYYY-MM-DD.': 'Confira as datas informadas.',
        'User not found.': 'Colaborador não encontrado.',
        'This user is not in the department.': 'O colaborador não está neste departamento.'
    };

    function falhou(alvoMensagem) {
        return function (erro) {
            var texto = TRADUCAO[erro.message] || erro.message;
            if (alvoMensagem) alvoMensagem.textContent = texto;
            else alert(texto); // shortcut: ações da ficha sem área de mensagem própria
        };
    }

    function opcoes(select, lista) {
        while (select.options.length > 1) select.remove(1);
        lista.forEach(function (d) { select.add(new Option(d.name, d.id)); });
    }

    function vazio() { return el('td', 'vazio-celula', '—'); }

    /* ---------- Tabela ---------- */
    function linha(u) {
        var tr = el('tr');
        tr.dataset.id = u.id;
        tr.dataset.setores = JSON.stringify(u.departments.map(function (m) { return m.name; }));
        if (!u.isActive) tr.dataset.inativo = '1';

        var pessoa = el('div', 'func-pessoa');
        var texto = el('div');
        texto.append(el('strong', null, u.name + (u.isActive ? '' : ' (inativo)')), el('small', null, u.email));
        pessoa.append(el('span', 'func-avatar', iniciais(u.name)), texto);
        var c1 = el('td');
        c1.appendChild(pessoa);

        var fixos = u.departments.filter(function (m) { return !temporario(m); });
        var c2 = fixos.length ? el('td') : vazio();
        fixos.forEach(function (m) { c2.appendChild(el('span', 'chip', m.name)); });

        var temps = u.departments.filter(temporario);
        var c3 = temps.length ? el('td') : vazio();
        temps.forEach(function (m) {
            var chip = el('span', 'chip chip--temp');
            chip.append(icone('bi-clock'), ' ' + m.name + ' · até ' + dia(m.expiresAtUtc));
            c3.appendChild(chip);
        });

        var c4 = el('td', 'func-acoes');
        c4.appendChild(botao('Ver ficha', 'button button-light button-pequeno', { ver: u.id }));
        var menu = el('details', 'menu-acoes');
        var resumo = el('summary');
        resumo.setAttribute('aria-label', 'Mais ações');
        resumo.appendChild(icone('bi-three-dots-vertical'));
        var ul = el('ul');
        var li1 = el('li'), li2 = el('li');
        li1.appendChild(botao('Redefinir senha', '', { abrir: 'modal-senha', alvo: u.id }));
        li2.appendChild(u.isActive
            ? botao('Desativar colaborador', 'menu-perigo', { abrir: 'modal-excluir', alvo: u.id })
            : botao('Reativar', '', { reativar: u.id }));
        ul.append(li1, li2);
        menu.append(resumo, ul);
        c4.appendChild(menu);

        tr.append(c1, c2, c3, c4);
        return tr;
    }

    /* ---------- Aba Departamentos ---------- */
    function cartao(nome, membros) {
        var art = el('article', 'setor-card');
        var topo = el('div', 'setor-card-topo');
        var ic = el('span', 'icone-setor');
        ic.appendChild(icone('bi-diagram-3'));
        var tit = el('div');
        tit.append(el('h3', null, nome), el('span', 'muted', membros.length + (membros.length === 1 ? ' colaborador' : ' colaboradores')));
        topo.append(ic, tit);
        var ul = el('ul', 'setor-membros');
        membros.forEach(function (m) {
            var li = el('li', null, m.name);
            if (m.temporary) li.append(' ', el('span', 'chip chip--temp', 'temporário'));
            ul.appendChild(li);
        });
        art.append(topo, ul);
        return art;
    }

    function membrosDe(deptoId) {
        var lista = [];
        usuarios.forEach(function (u) {
            if (!u.isActive) return;
            u.departments.forEach(function (m) {
                if (m.id === deptoId && comecou(m)) lista.push({ id: u.id, name: u.name, temporary: temporario(m) });
            });
        });
        return lista;
    }

    /* ---------- Ficha ---------- */
    function desenharFicha() {
        var u = porId(atual);
        if (!u) return;
        $('#ficha-iniciais').textContent = iniciais(u.name);
        $('#ficha-nome').textContent = u.name + (u.isActive ? '' : ' (inativo)');
        $('#ficha-email').textContent = u.email;
        $('#ficha-desativar').hidden = !u.isActive;
        $('#ficha-reativar').hidden = u.isActive;
        $('#ficha-reativar').dataset.reativar = u.id;

        var fixos = $('#ficha-setores-fixos');
        fixos.textContent = '';
        u.departments.filter(function (m) { return !temporario(m); }).forEach(function (m) {
            var chip = el('span', 'chip chip--remover', m.name + ' ');
            var x = botao('', '', { removerDepto: m.id });
            x.setAttribute('aria-label', 'Remover do departamento ' + m.name);
            x.appendChild(icone('bi-x-lg'));
            chip.appendChild(x);
            fixos.appendChild(chip);
        });
        if (!fixos.children.length) fixos.appendChild(el('span', 'muted', 'Nenhum departamento.'));

        var temp = $('#lista-temp');
        temp.textContent = '';
        u.departments.filter(temporario).forEach(function (m) {
            var li = el('li'), info = el('div');
            var periodo = (m.validFromUtc ? dia(m.validFromUtc, true) + ' até ' : 'Até ') + dia(m.expiresAtUtc, true);
            info.append(el('strong', null, m.name), el('span', 'muted', periodo));
            li.append(info, botao('Revogar', 'button button-light button-pequeno button-perigo-claro', { removerDepto: m.id }));
            temp.appendChild(li);
        });

        var ja = u.departments.map(function (m) { return m.id; });
        var livres = deptosAtivos().filter(function (d) { return ja.indexOf(d.id) < 0; });
        opcoes($('#atribuir-setor'), livres);
        opcoes($('#temp-setor'), livres);

        var colegas = $('#ficha-colegas');
        colegas.textContent = '';
        u.departments.filter(comecou).forEach(function (m) {
            var outros = membrosDe(m.id).filter(function (c) { return c.id !== u.id; });
            var g = el('div', 'colegas-grupo'), h = el('h4', null, m.name + ' ');
            h.appendChild(el('span', 'count-tag', String(outros.length)));
            var ul = el('ul');
            outros.forEach(function (c) { ul.appendChild(el('li', null, c.name)); });
            g.append(h, ul);
            colegas.appendChild(g);
        });
        if (!colegas.children.length) colegas.appendChild(el('p', 'muted', 'Sem colegas de departamento.'));
    }

    /* ---------- Desenho geral (admin) ---------- */
    function desenhar() {
        var corpo = $('#lista-funcionarios');
        corpo.textContent = '';
        usuarios.forEach(function (u) { corpo.appendChild(linha(u)); });

        var ativos = usuarios.filter(function (u) { return u.isActive; });
        $('#resumo-total').textContent = ativos.length;
        $('#resumo-temporarios').textContent = ativos.filter(function (u) { return u.departments.some(temporario); }).length;

        var filtro = $('#filtro-setor'), escolhido = filtro.value;
        while (filtro.options.length > 1) filtro.remove(1);
        deptosAtivos().forEach(function (d) { filtro.add(new Option(d.name, d.name)); });
        filtro.value = escolhido;

        var checks = $('#novo-setores');
        checks.textContent = '';
        deptosAtivos().forEach(function (d) {
            var lab = el('label', 'opcoes'), cb = el('input');
            cb.type = 'checkbox';
            cb.name = 'novo-setor';
            cb.value = d.id;
            lab.append(cb, ' ' + d.name);
            checks.appendChild(lab);
        });

        var grade = $('#lista-setores');
        grade.textContent = '';
        deptosAtivos().forEach(function (d) { grade.appendChild(cartao(d.name, membrosDe(d.id))); });

        window.colaboradores.filtrar();
        if (atual) desenharFicha();
    }

    function carregar() {
        return Promise.all([api('GET', '/api/admin/users'), api('GET', '/api/departments')]).then(function (r) {
            usuarios = r[0];
            departamentos = r[1];
            desenhar();
        }).catch(falhou());
    }

    function iniciarAdmin() {
        document.addEventListener('colaborador:ver', function (e) {
            atual = e.detail.id;
            desenharFicha();
        });

        // Guarda de quem é a ação antes de o modal abrir (linha da tabela ou ficha aberta)
        document.addEventListener('click', function (e) {
            var abrir = e.target.closest('[data-abrir]');
            if (abrir) {
                alvo = abrir.dataset.alvo || atual;
                if (abrir.dataset.abrir === 'modal-editar') {
                    var u = porId(alvo);
                    $('#edit-nome').value = u ? u.name : '';
                    $('#edit-email').value = u ? u.email : '';
                    $('#edit-mensagem').textContent = '';
                }
                if (abrir.dataset.abrir === 'modal-senha') { $('#senha-temporaria').value = ''; $('#senha-mensagem').textContent = ''; }
                if (abrir.dataset.abrir === 'modal-excluir') $('#desativar-mensagem').textContent = '';
                if (abrir.dataset.abrir === 'modal-adicionar') $('#novo-mensagem').textContent = '';
                return;
            }
            var reativar = e.target.closest('[data-reativar]');
            if (reativar) {
                api('PUT', '/api/users/' + reativar.dataset.reativar, { isActive: true }).then(carregar).catch(falhou());
                return;
            }
            var remover = e.target.closest('[data-remover-depto]');
            if (remover && atual) {
                api('DELETE', '/api/departments/' + remover.dataset.removerDepto + '/members/' + atual)
                    .then(carregar).catch(falhou());
            }
        });

        $('#atribuir-botao').addEventListener('click', function () {
            var depto = $('#atribuir-setor').value;
            if (!depto || !atual) return;
            api('POST', '/api/user-departments', { userId: Number(atual), departmentId: Number(depto), accessType: 'member' })
                .then(carregar).catch(falhou());
        });

        document.addEventListener('acesso:conceder', function (e) {
            var msg = $('#temp-mensagem');
            api('POST', '/api/user-departments', {
                userId: Number(atual), departmentId: Number(e.detail.departamento), accessType: 'temporary',
                validFrom: e.detail.inicio, expiresAt: e.detail.fim
            }).then(function () { msg.textContent = ''; return carregar(); }).catch(falhou(msg));
        });

        $('#novo-salvar').addEventListener('click', function () {
            var msg = $('#novo-mensagem');
            var email = $('#novo-email').value;
            var deptos = Array.prototype.map.call(document.querySelectorAll('input[name="novo-setor"]:checked'),
                function (c) { return Number(c.value); });
            api('POST', '/api/users', { name: $('#novo-nome').value, email: email, password: $('#novo-senha').value })
                .then(function (criado) {
                    // Daqui em diante o colaborador já existe: qualquer falha fecha o modal e recarrega a lista
                    ['#novo-nome', '#novo-email', '#novo-senha'].forEach(function (s) { $(s).value = ''; });
                    $('#modal-adicionar').close();
                    return Promise.all(deptos.map(function (d) {
                        return api('POST', '/api/user-departments', { userId: criado.id, departmentId: d, accessType: 'member' });
                    })).catch(function () {
                        alert('Colaborador criado, mas não foi possível atribuir todos os departamentos. Confira na ficha.');
                    }).then(carregar);
                }).catch(falhou(msg));
        });

        $('#edit-salvar').addEventListener('click', function () {
            api('PUT', '/api/users/' + alvo, { name: $('#edit-nome').value, email: $('#edit-email').value })
                .then(function () { $('#modal-editar').close(); return carregar(); }).catch(falhou($('#edit-mensagem')));
        });

        $('#senha-redefinir').addEventListener('click', function () {
            api('PUT', '/api/users/' + alvo, { password: $('#senha-temporaria').value })
                .then(function () { $('#modal-senha').close(); }).catch(falhou($('#senha-mensagem')));
        });

        $('#desativar-confirmar').addEventListener('click', function () {
            api('PUT', '/api/users/' + alvo, { isActive: false })
                .then(function () { $('#modal-excluir').close(); return carregar(); }).catch(falhou($('#desativar-mensagem')));
        });

        carregar();
    }

    /* ---------- Colaborador comum ---------- */
    function iniciarColaborador() {
        var painel = $('#painel-setores');
        painel.hidden = false;
        $('#vista-lista .subtitle').textContent = 'Seus departamentos e colegas.';
        api('GET', '/api/me/colleagues').then(function (deptos) {
            var grade = $('#lista-setores');
            grade.textContent = '';
            if (!deptos.length) grade.appendChild(el('p', 'muted', 'Você ainda não está em nenhum departamento.'));
            deptos.forEach(function (d) { grade.appendChild(cartao(d.name, d.members)); });
        }).catch(falhou());
    }

    window.usuario.then(function (user) {
        if (user.role === 'admin') iniciarAdmin();
        else iniciarColaborador();
    }).catch(function () {}); // sem sessão: api.js já levou para o login
})();
