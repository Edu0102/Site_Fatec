/* ferramentas-api.js — liga a página Ferramentas (ferramentas.js) ao backend (/api/tools).
   Depende de api.js. A interface continua toda em ferramentas.js. */
(function () {
    'use strict';

    // shortcut: erros aparecem em alert(); a página não tem área de mensagem. Trocar se o design ganhar uma.
    var AJUDA_LINK = 'Endereço inválido. No Chrome, abra o site, clique na barra de endereço no topo, copie o link (Ctrl+C) e cole aqui (Ctrl+V).';
    function avisar(erro) {
        alert(/web address/.test(erro.message) ? AJUDA_LINK : erro.message);
    }

    function carregar() {
        return api('GET', '/api/tools').then(function (lista) {
            window.ferramentas.renderizar(lista.map(function (t) {
                return {
                    id: t.id, nome: t.name, descricao: t.description, link: t.url, categoria: t.category,
                    icone: t.icon, aberturas: t.opens, ultimaAbertura: t.lastOpenedAtUtc, podeEditar: t.canEdit
                };
            }));
        }).catch(avisar);
    }

    document.addEventListener('ferramenta:salvar', function (e) {
        var f = e.detail;
        var corpo = { name: f.nome, description: f.descricao, url: f.link, category: f.categoria, icon: f.icone };
        (f.id ? api('PUT', '/api/tools/' + f.id, corpo) : api('POST', '/api/tools', corpo))
            .then(carregar).catch(avisar);
    });

    document.addEventListener('ferramenta:excluir', function (e) {
        api('DELETE', '/api/tools/' + e.detail.id).then(carregar).catch(avisar);
    });

    // A ferramenta abre em nova aba; só registramos o uso (para "Recentes")
    document.addEventListener('ferramenta:abrir', function (e) {
        api('POST', '/api/tools/' + e.detail.id + '/open').then(carregar).catch(function () {});
    });

    carregar();
})();
