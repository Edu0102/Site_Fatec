/*
 * menu-usuario.js — menu do funcionário no header.
 *
 *  - Clique no nome/foto: abre e fecha o menu.
 *  - Com o menu aberto, clique na FOTO: abre a janela para trocar a foto.
 *  - Clique fora do menu: fecha.
 *  - "Tema escuro" alterna o tema (guardado no navegador).
 *
 * Carregue SEM "defer" dentro do <head>, para o tema ser aplicado antes da
 * página aparecer (evita o "flash" de tema claro).
 */
(function () {
    "use strict";

    var CHAVE_TEMA = "frcont-tema";
    var CHAVE_FOTO = "frcont-foto-usuario";
    var ICONE_PESSOA = '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">' +
        '<path d="M12 12a5 5 0 1 0 0-10 5 5 0 0 0 0 10Zm0 2c-4.4 0-8 2.2-8 5v1h16v-1c0-2.8-3.6-5-8-5Z"/></svg>';

    function ler(chave) {
        try { return localStorage.getItem(chave); } catch (erro) { return null; }
    }

    function gravar(chave, valor) {
        try { localStorage.setItem(chave, valor); return true; } catch (erro) { return false; }
    }

    function fundo(url) {
        return 'url("' + String(url).replace(/"/g, "%22") + '")';
    }

    /* ---------- Tema ---------- */
    function aplicarTema(escuro) {
        if (escuro) document.documentElement.setAttribute("data-tema", "escuro");
        else document.documentElement.removeAttribute("data-tema");
    }

    aplicarTema(ler(CHAVE_TEMA) === "escuro");

    /* ---------- Foto (também usada pelo header.js) ---------- */
    window.definirFotoUsuario = function (url) {
        var avatar = document.getElementById("usuario-foto");
        if (!avatar) return;
        avatar.style.backgroundImage = url ? fundo(url) : "";
        avatar.classList.toggle("avatar--com-foto", !!url);
    };

    /* ---------- Menu e modal ---------- */
    function iniciar() {
        var area = document.getElementById("header-usuario");
        var botao = document.getElementById("usuario-botao");
        var menu = document.getElementById("usuario-menu");
        var botaoTema = document.getElementById("menu-tema");
        if (!area || !botao || !menu) return;

        var fotoSalva = ler(CHAVE_FOTO);
        if (fotoSalva) window.definirFotoUsuario(fotoSalva);

        function menuAberto() { return !menu.hidden; }

        function abrirMenu() {
            menu.hidden = false;
            botao.setAttribute("aria-expanded", "true");
        }

        function fecharMenu() {
            menu.hidden = true;
            botao.setAttribute("aria-expanded", "false");
        }

        botao.addEventListener("click", function (evento) {
            if (menuAberto() && evento.target.closest(".avatar")) {
                fecharMenu();
                abrirModalFoto();
            } else if (menuAberto()) {
                fecharMenu();
            } else {
                abrirMenu();
            }
        });

        document.addEventListener("click", function (evento) {
            if (menuAberto() && !area.contains(evento.target)) fecharMenu();
        });

        /* Tema escuro */
        function atualizarTextoTema() {
            var escuro = document.documentElement.getAttribute("data-tema") === "escuro";
            botaoTema.textContent = escuro ? "Tema claro" : "Tema escuro";
        }

        if (botaoTema) {
            atualizarTextoTema();
            botaoTema.addEventListener("click", function () {
                var escuro = document.documentElement.getAttribute("data-tema") !== "escuro";
                aplicarTema(escuro);
                gravar(CHAVE_TEMA, escuro ? "escuro" : "claro");
                atualizarTextoTema();
            });
        }

        /* Modal para trocar a foto (criado só quando precisa) */
        var modal = null;
        var previa = null;
        var campoArquivo = null;
        var erro = null;
        var botaoSalvar = null;
        var novaFoto = null;

        function criarModal() {
            modal = document.createElement("dialog");
            modal.className = "modal";
            modal.setAttribute("aria-labelledby", "modal-foto-titulo");
            modal.innerHTML =
                '<div class="modal-conteudo">' +
                    '<h2 id="modal-foto-titulo">Alterar foto</h2>' +
                    '<p class="muted">Escolha uma imagem para o seu perfil.</p>' +
                    '<div class="modal-previa" id="modal-previa">' + ICONE_PESSOA + '</div>' +
                    '<input type="file" id="modal-arquivo" accept="image/*" aria-label="Escolher imagem">' +
                    '<p class="form-message" id="modal-erro" role="alert"></p>' +
                    '<div class="modal-acoes">' +
                        '<button type="button" class="button button-light" id="modal-cancelar">Cancelar</button>' +
                        '<button type="button" class="button button-primary" id="modal-salvar" disabled>Salvar foto</button>' +
                    '</div>' +
                '</div>';
            document.body.appendChild(modal);

            previa = modal.querySelector("#modal-previa");
            campoArquivo = modal.querySelector("#modal-arquivo");
            erro = modal.querySelector("#modal-erro");
            botaoSalvar = modal.querySelector("#modal-salvar");

            modal.querySelector("#modal-cancelar").addEventListener("click", function () { modal.close(); });

            // Clique no fundo escurecido (fora do conteúdo) fecha o modal
            modal.addEventListener("click", function (evento) {
                if (evento.target === modal) modal.close();
            });

            modal.addEventListener("close", function () {
                campoArquivo.value = "";
                erro.textContent = "";
                novaFoto = null;
                botaoSalvar.disabled = true;
                previa.style.backgroundImage = "";
                previa.classList.remove("modal-previa--com-foto");
            });

            campoArquivo.addEventListener("change", escolherArquivo);

            botaoSalvar.addEventListener("click", function () {
                if (!novaFoto) return;
                window.definirFotoUsuario(novaFoto);
                if (!gravar(CHAVE_FOTO, novaFoto)) {
                    erro.textContent = "Não foi possível guardar a foto neste navegador.";
                    return;
                }
                modal.close();
            });
        }

        // Recorta a imagem em quadrado e reduz (256 px) para caber no navegador
        function escolherArquivo() {
            var arquivo = campoArquivo.files[0];
            erro.textContent = "";
            novaFoto = null;
            botaoSalvar.disabled = true;
            if (!arquivo) return;

            if (arquivo.type.indexOf("image/") !== 0) {
                erro.textContent = "Escolha um arquivo de imagem.";
                return;
            }

            var leitor = new FileReader();
            leitor.onload = function () {
                var imagem = new Image();
                imagem.onload = function () {
                    var tamanho = 256;
                    var lado = Math.min(imagem.width, imagem.height);
                    var tela = document.createElement("canvas");
                    tela.width = tamanho;
                    tela.height = tamanho;
                    tela.getContext("2d").drawImage(
                        imagem,
                        (imagem.width - lado) / 2, (imagem.height - lado) / 2, lado, lado,
                        0, 0, tamanho, tamanho
                    );
                    novaFoto = tela.toDataURL("image/jpeg", 0.85);
                    previa.style.backgroundImage = fundo(novaFoto);
                    previa.classList.add("modal-previa--com-foto");
                    botaoSalvar.disabled = false;
                };
                imagem.onerror = function () { erro.textContent = "Não foi possível ler esta imagem."; };
                imagem.src = leitor.result;
            };
            leitor.onerror = function () { erro.textContent = "Não foi possível ler este arquivo."; };
            leitor.readAsDataURL(arquivo);
        }

        function abrirModalFoto() {
            if (!modal) criarModal();
            modal.showModal();
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", iniciar);
    } else {
        iniciar();
    }
})();
