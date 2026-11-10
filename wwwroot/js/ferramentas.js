/* ferramentas.js — SOMENTE interface (busca, filtro, "Recentes", modais, validação).
   Nada é salvo: o banco deve ser ligado pelos pontos abaixo.

   ENTRADA : window.ferramentas.renderizar([{
                 id, nome, descricao, link, categoria, icone,   // icone: classe bi-*, ex. "bi-calculator"
                 aberturas, ultimaAbertura                      // do USUÁRIO LOGADO (0 / null se nunca abriu)
             }])
   SAÍDAS  : eventos no document
             'ferramenta:abrir'   -> detail = { id }    (ao clicar numa ferramenta; registrar a abertura)
             'ferramenta:salvar'  -> detail = { id (vazio se nova), nome, descricao, link, categoria, icone }
             'ferramenta:excluir' -> detail = { id }

   RECENTES: até QTD_RECENTES ferramentas com mais aberturas; dentre elas, a última
   aberta vai em primeiro e as demais seguem por número de aberturas. */
(function () {
    'use strict';

    var QTD_RECENTES = 4;
    var $ = function (s) { return document.querySelector(s); };
    var itens = [], categoriaAtiva = '', idParaExcluir = null;

    var busca = $('#busca-ferramenta'), filtros = $('#filtros-categoria');
    var gradeTodas = $('#lista-ferramentas'), gradeRecentes = $('#lista-recentes');
    var modal = $('#modal-ferramenta'), modalExcluir = $('#modal-ferramenta-excluir');
    var mensagem = $('#ferramenta-mensagem');
    var campos = {
        id: $('#ferramenta-id'), nome: $('#ferramenta-nome'), descricao: $('#ferramenta-descricao'),
        link: $('#ferramenta-link'), categoria: $('#ferramenta-categoria'), icone: $('#ferramenta-icone')
    };

    function linkSeguro(url) {
        try {
            var u = new URL(url, window.location.href);
            return (u.protocol === 'http:' || u.protocol === 'https:') ? u.href : '#';
        } catch (e) { return '#'; }
    }

    function el(tag, classe, texto) {
        var e = document.createElement(tag);
        if (classe) e.className = classe;
        if (texto) e.textContent = texto;
        return e;
    }

    function iconeBi(nome) {
        var i = el('i', 'bi ' + (/^bi-[a-z0-9-]+$/.test(nome || '') ? nome : 'bi-tools'));
        i.setAttribute('aria-hidden', 'true');
        return i;
    }

    function botaoAcao(icone, rotulo, perigo, acao, id) {
        var b = el('button', 'ferr-botao' + (perigo ? ' ferr-botao--perigo' : ''));
        b.type = 'button';
        b.dataset.acao = acao;
        b.dataset.id = id;
        b.title = rotulo;
        b.setAttribute('aria-label', rotulo);
        b.appendChild(iconeBi(icone));
        return b;
    }

    function card(f, compacto) {
        var art = el('article', 'ferr-card' + (compacto ? ' ferr-card--compacto' : ''));
        var a = el('a', 'ferr-link');
        a.href = linkSeguro(f.link);
        a.target = '_blank';
        a.rel = 'noopener noreferrer';
        a.dataset.abrir = f.id;

        var ic = el('span', 'ferr-icone');
        ic.appendChild(iconeBi(f.icone));
        a.appendChild(ic);

        if (compacto) {
            a.appendChild(el('span', 'ferr-nome', f.nome));
        } else {
            a.appendChild(el('span', 'ferr-nome', f.nome));
            if (f.descricao) a.appendChild(el('span', 'ferr-descricao', f.descricao));
            var rodape = el('span', 'ferr-rodape');
            if (f.categoria) rodape.appendChild(el('span', 'count-tag', f.categoria));
            var abrir = el('span', 'ferr-abrir', 'Abrir ');
            abrir.appendChild(iconeBi('bi-arrow-up-right'));
            rodape.appendChild(abrir);
            a.appendChild(rodape);
        }
        art.appendChild(a);

        if (!compacto) {
            var acoes = el('div', 'ferr-acoes');
            acoes.appendChild(botaoAcao('bi-pencil', 'Editar ferramenta', false, 'editar', f.id));
            acoes.appendChild(botaoAcao('bi-trash', 'Excluir ferramenta', true, 'excluir', f.id));
            art.appendChild(acoes);
        }
        return art;
    }

    function categorias() {
        return Array.prototype.map.call(campos.categoria.options, function (o) { return o.value; });
    }

    function desenharFiltros() {
        filtros.innerHTML = '';
        ['Todas'].concat(categorias()).forEach(function (nome) {
            var valor = nome === 'Todas' ? '' : nome;
            var b = el('button', 'ferr-filtro', nome);
            b.type = 'button';
            b.dataset.categoria = valor;
            b.setAttribute('aria-pressed', valor === categoriaAtiva ? 'true' : 'false');
            filtros.appendChild(b);
        });
    }

    function recentes() {
        var usadas = itens.filter(function (f) { return f.aberturas > 0; })
            .sort(function (a, b) { return b.aberturas - a.aberturas; })
            .slice(0, QTD_RECENTES);
        var ultima = usadas.slice().sort(function (a, b) {
            return new Date(b.ultimaAbertura || 0) - new Date(a.ultimaAbertura || 0);
        })[0];
        if (ultima) usadas = [ultima].concat(usadas.filter(function (f) { return f !== ultima; }));
        return usadas;
    }

    function desenhar() {
        var q = busca.value.trim().toLowerCase();
        var lista = itens.filter(function (f) {
            var texto = [f.nome, f.descricao, f.categoria].join(' ').toLowerCase();
            return (!q || texto.indexOf(q) > -1) && (!categoriaAtiva || f.categoria === categoriaAtiva);
        }).sort(function (a, b) { return (a.nome || '').localeCompare(b.nome || '', 'pt-BR'); });

        gradeTodas.innerHTML = '';
        lista.forEach(function (f) { gradeTodas.appendChild(card(f, false)); });

        var rec = recentes();
        gradeRecentes.innerHTML = '';
        rec.forEach(function (f) { gradeRecentes.appendChild(card(f, true)); });
        $('#recentes-vazio').hidden = rec.length > 0;
        gradeRecentes.hidden = rec.length === 0;

        $('#total-ferramentas').textContent = itens.length + (itens.length === 1 ? ' ferramenta' : ' ferramentas');
        $('#ferramentas-vazio').hidden = itens.length > 0;
        $('#ferramentas-sem-resultado').hidden = itens.length === 0 || lista.length > 0;
    }

    /* Ponto de entrada para o banco */
    window.ferramentas = {
        renderizar: function (lista) {
            itens = Array.isArray(lista) ? lista : [];
            desenhar();
        }
    };

    function abrirModal(f) {
        mensagem.textContent = '';
        $('#modal-ferramenta-titulo').textContent = f ? 'Editar ferramenta' : 'Adicionar ferramenta';
        campos.id.value = f ? f.id : '';
        campos.nome.value = f ? f.nome || '' : '';
        campos.descricao.value = f ? f.descricao || '' : '';
        campos.link.value = f ? f.link || '' : '';
        campos.categoria.selectedIndex = 0;
        campos.icone.selectedIndex = 0;
        if (f && f.categoria) campos.categoria.value = f.categoria;
        if (f && f.icone) campos.icone.value = f.icone;
        modal.showModal();
        campos.nome.focus();
    }

    $('#btn-adicionar-ferramenta').addEventListener('click', function () { abrirModal(null); });

    filtros.addEventListener('click', function (e) {
        var b = e.target.closest('button[data-categoria]');
        if (!b) return;
        categoriaAtiva = b.dataset.categoria;
        desenharFiltros();
        desenhar();
    });

    function achar(id) {
        return itens.filter(function (f) { return String(f.id) === String(id); })[0];
    }

    document.addEventListener('click', function (e) {
        var link = e.target.closest('a[data-abrir]');
        if (link) {
            document.dispatchEvent(new CustomEvent('ferramenta:abrir', { detail: { id: link.dataset.abrir } }));
            return;
        }
        var b = e.target.closest('button[data-acao]');
        if (b) {
            if (b.dataset.acao === 'editar' && achar(b.dataset.id)) abrirModal(achar(b.dataset.id));
            if (b.dataset.acao === 'excluir') { idParaExcluir = b.dataset.id; modalExcluir.showModal(); }
            return;
        }
        if (e.target.closest('[data-fechar]')) e.target.closest('dialog').close();
        else if (e.target.tagName === 'DIALOG') e.target.close();
    });

    $('#ferramenta-salvar').addEventListener('click', function () {
        var nome = campos.nome.value.trim(), link = campos.link.value.trim();
        if (!nome) { mensagem.textContent = 'Informe o nome da ferramenta.'; campos.nome.focus(); return; }
        if (!link) { mensagem.textContent = 'Informe o endereço da ferramenta.'; campos.link.focus(); return; }
        if (!/^https?:\/\//i.test(link)) link = 'https://' + link;
        if (linkSeguro(link) === '#') { mensagem.textContent = 'Confira o endereço informado.'; campos.link.focus(); return; }
        mensagem.textContent = '';
        document.dispatchEvent(new CustomEvent('ferramenta:salvar', { detail: {
            id: campos.id.value, nome: nome, descricao: campos.descricao.value.trim(),
            link: link, categoria: campos.categoria.value, icone: campos.icone.value
        }}));
        modal.close();
    });

    $('#ferramenta-confirmar-exclusao').addEventListener('click', function () {
        document.dispatchEvent(new CustomEvent('ferramenta:excluir', { detail: { id: idParaExcluir } }));
        modalExcluir.close();
    });

    busca.addEventListener('input', desenhar);
    desenharFiltros();
    desenhar();
})();
