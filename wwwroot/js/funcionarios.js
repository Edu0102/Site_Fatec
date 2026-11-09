/* funcionarios.js — SOMENTE interface (abas, modais, filtros, períodos).
   Nenhum dado é salvo: as ações de salvar/excluir/redefinir ainda precisam
   ser ligadas ao banco. */
(function () {
    'use strict';

    var $ = function (s, r) { return (r || document).querySelector(s); };
    var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

    /* Abas Funcionários / Setores */
    $$('.aba').forEach(function (aba) {
        aba.addEventListener('click', function () {
            $$('.aba').forEach(function (a) {
                a.classList.toggle('aba--ativa', a === aba);
                a.setAttribute('aria-selected', a === aba ? 'true' : 'false');
                $('#' + a.dataset.aba).hidden = a !== aba;
            });
        });
    });

    /* Lista <-> Ficha */
    var vistaLista = $('#vista-lista'), vistaFicha = $('#vista-ficha');
    $$('[data-ver]').forEach(function (btn) {
        btn.addEventListener('click', function () {
            vistaLista.hidden = true;
            vistaFicha.hidden = false;
            window.scrollTo(0, 0);
        });
    });
    $('#voltar-lista').addEventListener('click', function () {
        vistaFicha.hidden = true;
        vistaLista.hidden = false;
    });

    /* Modais (<dialog>) */
    document.addEventListener('click', function (e) {
        var abrir = e.target.closest('[data-abrir]');
        if (abrir) {
            var det = abrir.closest('details');
            if (det) det.open = false;
            var dlg = document.getElementById(abrir.dataset.abrir);
            if (dlg) dlg.showModal();
            return;
        }
        if (e.target.closest('[data-fechar]')) {
            e.target.closest('dialog').close();
            return;
        }
        if (e.target.tagName === 'DIALOG') e.target.close(); /* clique no fundo */
        if (!e.target.closest('.menu-acoes')) {
            $$('.menu-acoes[open]').forEach(function (d) { d.open = false; });
        }
    });

    /* Filtros da lista */
    var busca = $('#busca-funcionario'), fSetor = $('#filtro-setor'), fStatus = $('#filtro-status');
    function filtrar() {
        var q = busca.value.trim().toLowerCase(), visiveis = 0;
        $$('#lista-funcionarios tr').forEach(function (tr) {
            var ok = (!q || tr.textContent.toLowerCase().indexOf(q) > -1) &&
                     (!fSetor.value || tr.dataset.setores.split('|').indexOf(fSetor.value) > -1) &&
                     (!fStatus.value || tr.dataset.status === fStatus.value);
            tr.hidden = !ok;
            if (ok) visiveis++;
        });
        $('#lista-vazia').hidden = visiveis > 0;
    }
    [busca, fSetor, fStatus].forEach(function (el) { el.addEventListener('input', filtrar); });

    /* Acesso temporário: atalhos de período */
    var inicio = $('#temp-inicio'), fim = $('#temp-fim'), msg = $('#temp-mensagem');
    function iso(d) {
        var m = ('0' + (d.getMonth() + 1)).slice(-2), dia = ('0' + d.getDate()).slice(-2);
        return d.getFullYear() + '-' + m + '-' + dia;
    }
    $$('input[name="temp-periodo"]').forEach(function (r) {
        r.addEventListener('change', function () {
            msg.textContent = '';
            if (r.value === 'custom') { inicio.focus(); return; }
            var hoje = new Date(), f = new Date();
            f.setDate(f.getDate() + Number(r.value));
            inicio.value = iso(hoje);
            fim.value = iso(f);
        });
    });
    $('#temp-conceder').addEventListener('click', function () {
        if (!$('#temp-setor').value) { msg.textContent = 'Escolha um setor.'; return; }
        if (!inicio.value || !fim.value) { msg.textContent = 'Defina o período do acesso.'; return; }
        if (fim.value < inicio.value) { msg.textContent = 'A data final não pode ser antes da inicial.'; return; }
        msg.textContent = '';
        /* TODO: gravar no banco */
    });
})();
