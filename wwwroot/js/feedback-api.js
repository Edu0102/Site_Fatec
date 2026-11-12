/* feedback-api.js — envia feedback e lista os enviados (/api/feedback).
   Admin vê todos e pode responder ou fechar. Depende de api.js e de window.usuario (header.js). */
(function () {
    'use strict';

    var form = document.querySelector('form.formulario');
    var aviso = document.getElementById('feedback-aviso');
    var lista = document.getElementById('lista-feedback');
    var STATUS = { open: 'Aberto', answered: 'Respondido', closed: 'Fechado' };
    var admin = false;

    function el(tag, classe, texto) {
        var e = document.createElement(tag);
        if (classe) e.className = classe;
        if (texto) e.textContent = texto;
        return e;
    }

    function botao(texto, classe, acao) {
        var b = el('button', 'button ' + classe, texto);
        b.type = 'button';
        b.addEventListener('click', acao);
        return b;
    }

    function cartao(f) {
        var li = el('li', 'panel');
        li.appendChild(el('p', 'count-tag', STATUS[f.status] || f.status));
        var texto = el('p', null, f.description);
        texto.style.whiteSpace = 'pre-line'; // assunto e motivo vêm separados por linha em branco
        li.appendChild(texto);
        if (f.answer) li.appendChild(el('p', 'muted', 'Resposta: ' + f.answer));
        if (admin && f.status !== 'closed') {
            var resposta = el('textarea');
            resposta.setAttribute('aria-label', 'Resposta');
            resposta.placeholder = 'Responder...';
            var erro = el('p', 'form-message');
            erro.setAttribute('role', 'alert');
            var falhou = function (e) { erro.textContent = e.message; };
            li.append(resposta,
                botao('Responder', 'button-primary', function () {
                    if (!resposta.value.trim()) { erro.textContent = 'Escreva a resposta.'; return; }
                    api('POST', '/api/feedback/' + f.id + '/answer', { answer: resposta.value }).then(carregar).catch(falhou);
                }),
                botao('Fechar', 'button-light', function () {
                    api('POST', '/api/feedback/' + f.id + '/close').then(carregar).catch(falhou);
                }),
                erro);
        }
        return li;
    }

    function carregar() {
        return api('GET', '/api/feedback').then(function (itens) {
            lista.textContent = '';
            if (!itens.length) lista.appendChild(el('li', 'hub-vazio', 'Nenhum feedback enviado.'));
            itens.forEach(function (f) { lista.appendChild(cartao(f)); });
        }).catch(function (e) { aviso.textContent = e.message; });
    }

    form.addEventListener('submit', function (e) {
        e.preventDefault();
        var texto = document.getElementById('assunto').value.trim() + '\n\n' + document.getElementById('motivo').value.trim();
        api('POST', '/api/feedback', { description: texto }).then(function () {
            form.reset();
            aviso.textContent = 'Feedback enviado.';
            return carregar();
        }).catch(function (erro) { aviso.textContent = erro.message; });
    });

    window.usuario.then(function (user) {
        admin = user.role === 'admin';
        carregar();
    }).catch(function () {}); // sem sessão: api.js já levou para o login
})();
