/* centrallink-api.js — liga a Central de Links (centrallink.js) ao backend (/api/links e /api/tags/link).
   Depende de api.js. Só admin escreve; para os outros os botões ficam escondidos ([data-so-admin]). */
(function () {
    'use strict';

    var AJUDA_LINK = 'Endereço inválido. No Chrome, abra o site, clique na barra de endereço no topo, copie o link (Ctrl+C) e cole aqui (Ctrl+V).';
    var idDoFiltro = {}; // nome -> id, para excluir filtros

    // shortcut: erros aparecem em alert(), como em Ferramentas. Recarrega para desfazer o que a página já mostrou.
    function avisar(erro) {
        alert(/web address/.test(erro.message) ? AJUDA_LINK : erro.message);
        carregar();
    }

    function data(utc) {
        return utc ? new Date(utc).toLocaleDateString('pt-BR', { timeZone: 'America/Sao_Paulo' }) : '';
    }

    var versao = 0; // só a recarga mais recente desenha (as respostas podem chegar fora de ordem)

    function carregar() {
        var minha = ++versao;
        return Promise.all([api('GET', '/api/links'), api('GET', '/api/tags/link')]).then(function (r) {
            if (minha !== versao) return;
            idDoFiltro = {};
            r[1].forEach(function (t) { idDoFiltro[t.name] = t.id; });
            window.centralLinks.definirFiltros(r[1].map(function (t) { return t.name; }));
            window.centralLinks.renderizar(r[0].map(function (l) {
                return { id: l.id, titulo: l.title, descricao: l.description, url: l.url, assunto: l.subject,
                         tags: l.tags, data: data(l.updatedAtUtc) };
            }));
        }).catch(function (erro) { alert(erro.message); });
    }

    document.addEventListener('link:salvar', function (e) {
        var l = e.detail;
        var corpo = { title: l.titulo, description: l.descricao, url: l.url, subject: l.assunto, tags: l.tags };
        (l.id ? api('PUT', '/api/links/' + l.id, corpo) : api('POST', '/api/links', corpo))
            .then(carregar).catch(avisar);
    });

    document.addEventListener('link:excluir', function (e) {
        api('DELETE', '/api/links/' + e.detail.id).then(carregar).catch(avisar);
    });

    document.addEventListener('filtro:salvar', function (e) {
        api('POST', '/api/tags/link', { name: e.detail.nome }).then(carregar).catch(avisar);
    });

    document.addEventListener('filtro:excluir', function (e) {
        var id = idDoFiltro[e.detail.nome];
        (id ? api('DELETE', '/api/tags/' + id) : Promise.resolve()).then(carregar).catch(avisar);
    });

    carregar();
})();
