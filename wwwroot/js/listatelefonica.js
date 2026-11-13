/* listatelefonica.js — SOMENTE interface (modais, filtros, validação básica).
   Nada é salvo: o banco deve ser ligado pelos pontos abaixo.

   ENTRADA  : window.listaTelefonica.renderizar([{ id, nome, setor, ramal, telefone, email, tags: ["..."] }])
              window.listaTelefonica.definirDepartamentos(["Fiscal", "Pessoal", ...])
              window.listaTelefonica.definirFiltros(["Matriz", "Suporte", ...])
              ("setor" guarda o nome do departamento; o nome do campo foi mantido por causa do banco)
   SAÍDAS   : eventos no document
              'contato:salvar'  -> detail = { id (vazio se novo), nome, setor, ramal, telefone, email, tags }
              'contato:excluir' -> detail = { id }
              'filtro:salvar'   -> detail = { nome }
              'filtro:excluir'  -> detail = { nome }

   Filtros (tags): iguais aos da Central de Links. Valem só para esta página e não
   alteram os departamentos. O contato precisa ter TODAS as tags marcadas. */
(function () {
    'use strict';

    var $ = function (s) { return document.querySelector(s); };
    var contatos = [];
    var departamentos = []; // vêm de listatelefonica-api.js
    var filtros = [];
    var idParaExcluir = null;

    var lista = $('#lista-contatos');
    var busca = $('#busca-contato');
    var vazio = $('#contatos-vazio'), semResultado = $('#contatos-sem-resultado');
    var modal = $('#modal-contato'), modalExcluir = $('#modal-contato-excluir');
    var campos = {
        id: $('#contato-id'), nome: $('#contato-nome'), setor: $('#contato-setor'),
        ramal: $('#contato-ramal'), telefone: $('#contato-telefone'), email: $('#contato-email'),
        tags: $('#contato-tags')
    };
    var areaFiltros = $('#filtros-contato'), formFiltro = $('#form-filtro-contato');
    var mensagem = $('#contato-mensagem');

    function el(tag, classe, texto) {
        var e = document.createElement(tag);
        if (classe) e.className = classe;
        if (texto) e.textContent = texto;
        return e;
    }

    function botao(icone, rotulo, perigo, acao, id) {
        var b = el('button', 'botao-icone' + (perigo ? ' botao-icone--perigo' : ''));
        b.type = 'button';
        b.dataset.acao = acao;
        b.dataset.id = id;
        b.setAttribute('aria-label', rotulo);
        b.title = rotulo;
        var i = el('i', 'bi ' + icone);
        i.setAttribute('aria-hidden', 'true');
        b.appendChild(i);
        return b;
    }

    // Departamentos cadastrados + os que já aparecem nos contatos
    function todosDepartamentos() {
        return departamentos.concat(contatos.map(function (c) { return c.setor; }))
            .filter(function (s, i, a) { return s && a.indexOf(s) === i; })
            .sort(function (a, b) { return a.localeCompare(b, 'pt-BR'); });
    }

    // Os departamentos agora só alimentam o campo "Departamento" do modal (não há mais filtro por departamento)
    function atualizarSetores() {
        campos.setor.innerHTML = '';
        var nenhum = el('option', '', 'Sem departamento');
        nenhum.value = '';
        campos.setor.appendChild(nenhum);
        todosDepartamentos().forEach(function (s) {
            var o = el('option', '', s);
            o.value = s;
            campos.setor.appendChild(o);
        });
    }

    function tagsMarcadas() {
        return Array.prototype.map.call(areaFiltros.querySelectorAll('input:checked'), function (i) { return i.value; });
    }

    // Filtros (tags): cada um com o "x" para remover, como na Central de Links
    function criarFiltros() {
        var antes = tagsMarcadas();
        areaFiltros.innerHTML = '';
        filtros.forEach(function (f) {
            var linha = el('div', 'filtro-linha');
            var label = el('label', 'filtro');
            var input = el('input');
            input.type = 'checkbox';
            input.value = f;
            input.checked = antes.indexOf(f) > -1;
            label.append(input, document.createTextNode(' ' + f));
            var remover = botao('bi-x-lg', 'Remover filtro ' + f, true, 'remover-filtro', f);
            remover.setAttribute('data-so-admin', '');
            linha.append(label, remover);
            areaFiltros.appendChild(linha);
        });
    }

    function tagsDe(c) { return Array.isArray(c.tags) ? c.tags : []; }

    function card(c) {
        var art = el('article', 'tel-card');
        art.dataset.id = c.id;

        var topo = el('div', 'tel-card-topo');
        topo.appendChild(el('h3', 'tel-nome', c.nome));
        if (c.ramal) topo.appendChild(el('span', 'tel-ramal', 'Ramal ' + c.ramal));
        var acoes = el('div', 'acoes-icone');
        acoes.setAttribute('data-so-admin', '');
        acoes.append(botao('bi-pencil', 'Editar contato', false, 'editar', c.id),
                     botao('bi-trash', 'Excluir contato', true, 'excluir', c.id));
        topo.appendChild(acoes);

        var info = el('p', 'tel-info');
        [c.telefone, c.email].filter(Boolean).forEach(function (t, i) {
            if (i) info.appendChild(document.createTextNode(' · '));
            info.appendChild(document.createTextNode(t));
        });

        art.append(topo, info);
        if (c.setor || tagsDe(c).length) {
            var tags = el('div', 'tags');
            if (c.setor) tags.appendChild(el('span', 'tag', c.setor));
            tagsDe(c).forEach(function (t) { tags.appendChild(el('span', 'tag', t)); });
            art.appendChild(tags);
        }
        return art;
    }

    function desenhar() {
        var q = busca.value.trim().toLowerCase(), selecionadas = tagsMarcadas();
        var visiveis = contatos.filter(function (c) {
            var texto = [c.nome, c.setor, c.ramal, c.telefone, c.email].concat(tagsDe(c)).join(' ').toLowerCase();
            var tagsOk = selecionadas.every(function (t) { return tagsDe(c).indexOf(t) > -1; });
            return (!q || texto.indexOf(q) > -1) && tagsOk;
        }).sort(function (a, b) { return (a.nome || '').localeCompare(b.nome || '', 'pt-BR'); });

        lista.innerHTML = '';
        visiveis.forEach(function (c) { lista.appendChild(card(c)); });

        $('#total-contatos').textContent = contatos.length + (contatos.length === 1 ? ' contato' : ' contatos');
        vazio.hidden = contatos.length > 0;
        semResultado.hidden = contatos.length === 0 || visiveis.length > 0;
    }

    /* Ponto de entrada para o banco */
    window.listaTelefonica = {
        renderizar: function (novaLista) {
            contatos = Array.isArray(novaLista) ? novaLista : [];
            atualizarSetores();
            desenhar();
        },
        definirDepartamentos: function (nomes) {
            departamentos = Array.isArray(nomes) ? nomes : [];
            atualizarSetores();
            desenhar();
        },
        definirFiltros: function (nomes) {
            filtros = Array.isArray(nomes) ? nomes : [];
            criarFiltros();
            desenhar();
        }
    };

    function abrirModal(contato) {
        mensagem.textContent = '';
        $('#modal-contato-titulo').textContent = contato ? 'Editar contato' : 'Adicionar contato';
        campos.id.value = contato ? contato.id : '';
        ['nome', 'ramal', 'telefone', 'email'].forEach(function (k) {
            campos[k].value = contato ? (contato[k] || '') : '';
        });
        campos.tags.value = contato ? tagsDe(contato).join(', ') : '';
        campos.setor.selectedIndex = 0;
        if (contato && contato.setor) campos.setor.value = contato.setor;
        modal.showModal();
        campos.nome.focus();
    }

    $('#btn-adicionar-contato').addEventListener('click', function () { abrirModal(null); });

    lista.addEventListener('click', function (e) {
        var b = e.target.closest('button[data-acao]');
        if (!b) return;
        var contato = contatos.filter(function (c) { return String(c.id) === b.dataset.id; })[0];
        if (b.dataset.acao === 'editar' && contato) abrirModal(contato);
        if (b.dataset.acao === 'excluir') { idParaExcluir = b.dataset.id; modalExcluir.showModal(); }
    });

    $('#contato-salvar').addEventListener('click', function () {
        if (!campos.nome.value.trim()) { mensagem.textContent = 'Informe o nome do contato.'; campos.nome.focus(); return; }
        if (campos.email.value && !campos.email.checkValidity()) { mensagem.textContent = 'Confira o e-mail informado.'; campos.email.focus(); return; }
        mensagem.textContent = '';
        var novasTags = campos.tags.value.split(',')
            .map(function (t) { return t.trim(); })
            .filter(function (t, i, a) { return t && a.indexOf(t) === i; });
        document.dispatchEvent(new CustomEvent('contato:salvar', { detail: {
            id: campos.id.value,
            nome: campos.nome.value.trim(),
            setor: campos.setor.value,
            ramal: campos.ramal.value.trim(),
            telefone: campos.telefone.value.trim(),
            email: campos.email.value.trim(),
            tags: novasTags
        }}));
        // Tag nova passa a aparecer na lista de filtros (como na Central de Links)
        var criouFiltro = false;
        novasTags.forEach(function (t) {
            var existe = filtros.some(function (f) { return f.toLowerCase() === t.toLowerCase(); });
            if (!existe) {
                filtros.push(t);
                criouFiltro = true;
                document.dispatchEvent(new CustomEvent('filtro:salvar', { detail: { nome: t } }));
            }
        });
        if (criouFiltro) criarFiltros();
        modal.close();
    });

    $('#contato-confirmar-exclusao').addEventListener('click', function () {
        document.dispatchEvent(new CustomEvent('contato:excluir', { detail: { id: idParaExcluir } }));
        modalExcluir.close();
    });

    /* Fechar modais: botão Cancelar e clique no fundo */
    document.addEventListener('click', function (e) {
        if (e.target.closest('[data-fechar]')) e.target.closest('dialog').close();
        else if (e.target.tagName === 'DIALOG') e.target.close();
    });

    /* Filtros (tags): adicionar e remover */
    formFiltro.addEventListener('submit', function (e) {
        e.preventDefault();
        var campo = $('#novo-filtro-contato'), nome = campo.value.trim();
        if (nome && !filtros.some(function (f) { return f.toLowerCase() === nome.toLowerCase(); })) {
            filtros.push(nome);
            document.dispatchEvent(new CustomEvent('filtro:salvar', { detail: { nome: nome } }));
            criarFiltros();
        }
        campo.value = '';
    });

    areaFiltros.addEventListener('click', function (e) {
        var b = e.target.closest('button[data-acao="remover-filtro"]');
        if (!b) return;
        filtros.splice(filtros.indexOf(b.dataset.id), 1);
        document.dispatchEvent(new CustomEvent('filtro:excluir', { detail: { nome: b.dataset.id } }));
        criarFiltros();
        desenhar();
    });

    busca.addEventListener('input', desenhar);
    areaFiltros.addEventListener('change', desenhar);
    atualizarSetores();
    criarFiltros();
    desenhar();
})();
