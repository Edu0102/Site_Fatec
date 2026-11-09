/* listatelefonica.js — SOMENTE interface (modais, filtros, validação básica).
   Nada é salvo: o banco deve ser ligado pelos pontos abaixo.

   ENTRADA  : window.listaTelefonica.renderizar([{ id, nome, setor, ramal, telefone, email }])
   SAÍDAS   : eventos no document
              'contato:salvar'  -> detail = { id (vazio se novo), nome, setor, ramal, telefone, email }
              'contato:excluir' -> detail = { id }
*/
(function () {
    'use strict';

    var $ = function (s) { return document.querySelector(s); };
    var contatos = [];
    var idParaExcluir = null;

    var corpo = $('#lista-contatos'), tabela = $('#tabela-contatos');
    var busca = $('#busca-contato'), filtroSetor = $('#filtro-setor-contato');
    var vazio = $('#contatos-vazio'), semResultado = $('#contatos-sem-resultado');
    var modal = $('#modal-contato'), modalExcluir = $('#modal-contato-excluir');
    var campos = {
        id: $('#contato-id'), nome: $('#contato-nome'), setor: $('#contato-setor'),
        ramal: $('#contato-ramal'), telefone: $('#contato-telefone'), email: $('#contato-email')
    };
    var mensagem = $('#contato-mensagem');

    function celula(texto, classe, rotulo) {
        var td = document.createElement('td');
        if (rotulo) td.dataset.label = rotulo;
        if (classe) td.className = classe;
        if (texto) { td.textContent = texto; }
        else { td.textContent = '—'; td.classList.add('tel-vazio'); }
        return td;
    }

    function botao(icone, rotulo, classe, acao, id) {
        var b = document.createElement('button');
        b.type = 'button';
        b.className = 'tel-icone ' + (classe || '');
        b.dataset.acao = acao;
        b.dataset.id = id;
        b.setAttribute('aria-label', rotulo);
        b.title = rotulo;
        b.innerHTML = '<i class="bi ' + icone + '" aria-hidden="true"></i>';
        return b;
    }

    function atualizarSetores() {
        var atual = filtroSetor.value;
        var setores = contatos.map(function (c) { return c.setor; })
            .filter(function (s, i, a) { return s && a.indexOf(s) === i; })
            .sort(function (a, b) { return a.localeCompare(b, 'pt-BR'); });
        filtroSetor.innerHTML = '<option value="">Todos os setores</option>';
        setores.forEach(function (s) {
            var o = document.createElement('option');
            o.value = o.textContent = s;
            filtroSetor.appendChild(o);
        });
        filtroSetor.value = setores.indexOf(atual) > -1 ? atual : '';
    }

    function desenhar() {
        var q = busca.value.trim().toLowerCase(), setor = filtroSetor.value;
        var lista = contatos.filter(function (c) {
            var texto = [c.nome, c.setor, c.ramal, c.telefone, c.email].join(' ').toLowerCase();
            return (!q || texto.indexOf(q) > -1) && (!setor || c.setor === setor);
        }).sort(function (a, b) { return (a.nome || '').localeCompare(b.nome || '', 'pt-BR'); });

        corpo.innerHTML = '';
        lista.forEach(function (c) {
            var tr = document.createElement('tr');
            tr.dataset.id = c.id;
            tr.appendChild(celula(c.nome, 'tel-nome', 'Nome'));
            tr.appendChild(celula(c.setor, '', 'Setor'));
            tr.appendChild(celula(c.ramal, 'tel-ramal', 'Ramal'));
            tr.appendChild(celula(c.telefone, '', 'Telefone'));
            tr.appendChild(celula(c.email, '', 'E-mail'));
            var td = document.createElement('td');
            td.className = 'tel-celula-acoes';
            var div = document.createElement('div');
            div.className = 'tel-acoes';
            div.appendChild(botao('bi-pencil', 'Editar contato', '', 'editar', c.id));
            div.appendChild(botao('bi-trash', 'Excluir contato', 'tel-icone--perigo', 'excluir', c.id));
            td.appendChild(div);
            tr.appendChild(td);
            corpo.appendChild(tr);
        });

        $('#total-contatos').textContent = contatos.length + (contatos.length === 1 ? ' contato' : ' contatos');
        tabela.hidden = contatos.length === 0 || lista.length === 0;
        vazio.hidden = contatos.length > 0;
        semResultado.hidden = contatos.length === 0 || lista.length > 0;
    }

    /* Ponto de entrada para o banco */
    window.listaTelefonica = {
        renderizar: function (lista) {
            contatos = Array.isArray(lista) ? lista : [];
            atualizarSetores();
            desenhar();
        }
    };

    function abrirModal(contato) {
        mensagem.textContent = '';
        $('#modal-contato-titulo').textContent = contato ? 'Editar contato' : 'Adicionar contato';
        campos.id.value = contato ? contato.id : '';
        ['nome', 'setor', 'ramal', 'telefone', 'email'].forEach(function (k) {
            campos[k].value = contato ? (contato[k] || '') : '';
        });
        modal.showModal();
        campos.nome.focus();
    }

    $('#btn-adicionar-contato').addEventListener('click', function () { abrirModal(null); });

    corpo.addEventListener('click', function (e) {
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
        document.dispatchEvent(new CustomEvent('contato:salvar', { detail: {
            id: campos.id.value,
            nome: campos.nome.value.trim(),
            setor: campos.setor.value.trim(),
            ramal: campos.ramal.value.trim(),
            telefone: campos.telefone.value.trim(),
            email: campos.email.value.trim()
        }}));
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

    busca.addEventListener('input', desenhar);
    filtroSetor.addEventListener('input', desenhar);
    desenhar();
})();
