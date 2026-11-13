/* listatelefonica-api.js — liga a Lista telefônica (listatelefonica.js) ao backend
   (/api/phones, /api/tags/phone, /api/departments). Depende de api.js. Só admin escreve. */
(function () {
    'use strict';

    var idDoFiltro = {};      // nome -> id, para excluir filtros
    var idDoDepartamento = {}; // nome -> id (todos, até inativos, para não perder o departamento ao editar)

    // shortcut: erros aparecem em alert(), como em Ferramentas. Recarrega para desfazer o que a página já mostrou.
    function avisar(erro) {
        alert(erro.message);
        carregar();
    }

    var versao = 0; // só a recarga mais recente desenha (as respostas podem chegar fora de ordem)

    function carregar() {
        var minha = ++versao;
        return Promise.all([api('GET', '/api/phones'), api('GET', '/api/tags/phone'), api('GET', '/api/departments')])
            .then(function (r) {
                if (minha !== versao) return;
                idDoFiltro = {};
                r[1].forEach(function (t) { idDoFiltro[t.name] = t.id; });
                idDoDepartamento = {};
                // ativos por último: com nome repetido, vale o ativo
                r[2].slice().sort(function (a, b) { return a.isActive - b.isActive; })
                    .forEach(function (d) { idDoDepartamento[d.name] = d.id; });
                window.listaTelefonica.definirDepartamentos(r[2].filter(function (d) { return d.isActive; })
                    .map(function (d) { return d.name; }));
                window.listaTelefonica.definirFiltros(r[1].map(function (t) { return t.name; }));
                window.listaTelefonica.renderizar(r[0].map(function (c) {
                    return { id: c.id, nome: c.name, setor: c.department || '', ramal: c.extension,
                             telefone: c.phoneNumber, email: c.email, tags: c.tags };
                }));
            }).catch(function (erro) { alert(erro.message); });
    }

    document.addEventListener('contato:salvar', function (e) {
        var c = e.detail;
        var corpo = { name: c.nome, departmentId: idDoDepartamento[c.setor] || null, extension: c.ramal,
                      phoneNumber: c.telefone, email: c.email, tags: c.tags };
        (c.id ? api('PUT', '/api/phones/' + c.id, corpo) : api('POST', '/api/phones', corpo))
            .then(carregar).catch(avisar);
    });

    document.addEventListener('contato:excluir', function (e) {
        api('DELETE', '/api/phones/' + e.detail.id).then(carregar).catch(avisar);
    });

    document.addEventListener('filtro:salvar', function (e) {
        // Tag nova digitada num contato também dispara este evento; o salvamento do contato já a cria.
        api('POST', '/api/tags/phone', { name: e.detail.nome }).then(carregar).catch(function () { carregar(); });
    });

    document.addEventListener('filtro:excluir', function (e) {
        var id = idDoFiltro[e.detail.nome];
        (id ? api('DELETE', '/api/tags/' + id) : Promise.resolve()).then(carregar).catch(avisar);
    });

    carregar();
})();
