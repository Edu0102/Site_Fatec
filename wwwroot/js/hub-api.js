/* hub-api.js — preenche o Hub Inicial (index.html) com dados do backend.
   Depende de api.js e de window.usuario (header.js). */
(function () {
    'use strict';

    var $ = function (id) { return document.getElementById(id); };

    function item(texto, href, novaAba) {
        var li = document.createElement('li');
        var a = document.createElement('a');
        a.textContent = texto;
        a.href = href;
        if (novaAba) { a.target = '_blank'; a.rel = 'noopener noreferrer'; }
        li.appendChild(a);
        return li;
    }

    // Troca o conteúdo da lista; sem itens, mantém o <li class="hub-vazio"> do design
    function preencher(lista, itens) {
        if (!itens.length) return;
        lista.textContent = '';
        itens.forEach(function (li) { lista.appendChild(li); });
    }

    function seguro(url) { return /^https?:\/\//i.test(url || '') ? url : '#'; }

    window.usuario.then(function (user) {
        $('hub-nome').textContent = user.name;
    }).catch(function () {}); // sem sessão: api.js já levou para o login

    api('GET', '/api/me/departments').then(function (deps) {
        $('hub-departamentos').textContent = deps.length
            ? deps.map(function (d) { return d.name; }).join(' · ') : 'Sem departamento';
    }).catch(function () {});

    api('GET', '/api/pops').then(function (pops) {
        var ativos = pops.filter(function (p) { return p.status === 'published'; }); // admin também recebe rascunhos
        $('stat-pops').textContent = ativos.length;
        var recentes = ativos.slice().sort(function (a, b) {
            return (b.updatedAtUtc || '').localeCompare(a.updatedAtUtc || '');
        }).slice(0, 5);
        preencher($('lista-pops-recentes'), recentes.map(function (p) { return item(p.title, 'html/centralpop.html'); }));
    }).catch(function () {});

    api('GET', '/api/me/checklists').then(function (lista) {
        var abertos = lista.filter(function (c) { return !c.completedAtUtc; });
        $('stat-checklists').textContent = abertos.length;
        preencher($('lista-continuar'), abertos.map(function (c) {
            return item(c.description || 'Checklist #' + c.id, 'html/checklist.html');
        }));
    }).catch(function () {});

    // Links cadastrados: GET /api/links ainda é só para admin; o número fica "–" até o plano da Central de Links.

    api('GET', '/api/tools').then(function (tools) {
        var usadas = tools.filter(function (t) { return t.opens > 0; })
            .sort(function (a, b) { return b.opens - a.opens; }).slice(0, 4);
        preencher($('lista-ferramentas-recentes'), usadas.map(function (t) { return item(t.name, seguro(t.url), true); }));
    }).catch(function () {});
})();
