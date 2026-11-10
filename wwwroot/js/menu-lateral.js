/* menu-lateral.js — menu lateral (todas as páginas)
   Faz só duas coisas, sem depender do banco de dados:
   1. Preenche a data de hoje em #hub-data, só no Hub (ex.: "Terça-feira 10.11.2026").
   2. Abre e fecha o menu no celular. */
(function () {
    'use strict';

    // 1. Data de hoje
    var campoData = document.getElementById('hub-data');
    if (campoData) {
        var hoje = new Date();
        var semana = hoje.toLocaleDateString('pt-BR', { weekday: 'long' });
        semana = semana.charAt(0).toUpperCase() + semana.slice(1);
        var dia = String(hoje.getDate()).padStart(2, '0');
        var mes = String(hoje.getMonth() + 1).padStart(2, '0');
        campoData.textContent = semana + ' ' + dia + '.' + mes + '.' + hoje.getFullYear();
    }

    // 2. Menu recolhível (celular)
    var menu = document.getElementById('menu-lateral');
    var botaoAbrir = document.getElementById('menu-abrir');
    var fundo = document.getElementById('menu-fundo');
    if (!menu || !botaoAbrir || !fundo) { return; }

    function definir(aberto) {
        menu.classList.toggle('aberto', aberto);
        fundo.hidden = !aberto;
        botaoAbrir.setAttribute('aria-expanded', String(aberto));
        botaoAbrir.setAttribute('aria-label', aberto ? 'Fechar menu' : 'Abrir menu');
    }

    botaoAbrir.addEventListener('click', function () {
        definir(!menu.classList.contains('aberto'));
    });

    fundo.addEventListener('click', function () { definir(false); });

    menu.querySelectorAll('.menu-link').forEach(function (link) {
        link.addEventListener('click', function () { definir(false); });
    });

    document.addEventListener('keydown', function (evento) {
        if (evento.key === 'Escape' && menu.classList.contains('aberto')) {
            definir(false);
            botaoAbrir.focus();
        }
    });

    // Ao voltar para tela grande, garante o estado fechado/limpo
    window.matchMedia('(min-width: 48.0625rem)').addEventListener('change', function (e) {
        if (e.matches) { definir(false); }
    });
})();
