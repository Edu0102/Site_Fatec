"use strict";

const CHAVE_GUIAS = "frcont-guias-v1";
const usuarioAtual = document.getElementById("usuario-atual");
const botaoAlternar = document.getElementById("btn-toggle-perfil");
const painelAdm = document.getElementById("painel-adm");
const formulario = document.getElementById("form-guia");
const campoTitulo = document.getElementById("titulo-guia");
const campoConteudo = document.getElementById("conteudo-guia");
const listaGuias = document.getElementById("lista-guias");
const guiasVazios = document.getElementById("guias-vazios");
const contadorGuias = document.getElementById("contador-guias");
const botaoCancelar = document.getElementById("cancelar-guia");

function carregarGuias() {
    try {
        const dados = JSON.parse(localStorage.getItem(CHAVE_GUIAS));
        return Array.isArray(dados) ? dados : [];
    } catch (erro) {
        return [];
    }
}

let guias = carregarGuias();

function salvarGuias() {
    try {
        localStorage.setItem(CHAVE_GUIAS, JSON.stringify(guias));
    } catch (erro) {
        alert("Não foi possível salvar os guias neste navegador.");
    }
}

function criarCartao(guia) {
    const cartao = document.createElement("article");
    cartao.className = "guia-card dado-js";

    const titulo = document.createElement("h3");
    titulo.textContent = guia.titulo;

    const conteudo = document.createElement("p");
    conteudo.textContent = guia.conteudo;

    cartao.append(titulo, conteudo);

    if (usuarioAtual.value === "adm") {
        const botaoExcluir = document.createElement("button");
        botaoExcluir.type = "button";
        botaoExcluir.className = "button button-light";
        botaoExcluir.textContent = "Excluir guia";
        botaoExcluir.addEventListener("click", function () {
            guias = guias.filter(item => item.id !== guia.id);
            salvarGuias();
            renderizarGuias();
        });
        cartao.appendChild(botaoExcluir);
    }

    return cartao;
}

function renderizarGuias() {
    listaGuias.replaceChildren();

    guias.forEach(function (guia) {
        listaGuias.appendChild(criarCartao(guia));
    });

    const total = guias.length;
    contadorGuias.textContent = total + (total === 1 ? " guia" : " guias");
    guiasVazios.hidden = total > 0;
    listaGuias.hidden = total === 0;
}

function alternarPerfil() {
    const administrador = usuarioAtual.value !== "adm";
    usuarioAtual.value = administrador ? "adm" : "funcionario";
    painelAdm.hidden = !administrador;
    botaoAlternar.textContent = administrador ? "Modo: Administrador" : "Modo: Funcionário";
    botaoAlternar.setAttribute("aria-pressed", String(administrador));
    renderizarGuias();

    if (administrador) {
        campoTitulo.focus();
    }
}

botaoAlternar.addEventListener("click", alternarPerfil);

botaoCancelar.addEventListener("click", function () {
    painelAdm.hidden = true;
    usuarioAtual.value = "funcionario";
    botaoAlternar.textContent = "Modo: Funcionário";
    botaoAlternar.setAttribute("aria-pressed", "false");
    renderizarGuias();
});

formulario.addEventListener("submit", function (evento) {
    evento.preventDefault();

    if (usuarioAtual.value !== "adm") return;

    const titulo = campoTitulo.value.trim();
    const conteudo = campoConteudo.value.trim();

    if (!titulo || !conteudo) {
        alert("Preencha o título e o conteúdo do guia.");
        return;
    }

    guias.unshift({
        id: Date.now(),
        titulo: titulo,
        conteudo: conteudo
    });

    salvarGuias();
    renderizarGuias();
    formulario.reset();
    campoTitulo.focus();
});

renderizarGuias();
