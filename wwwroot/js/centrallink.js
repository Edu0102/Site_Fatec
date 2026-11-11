/* centrallink.js — Central de Links (interface + lista em memória).
   O banco deve ser ligado pelos eventos abaixo; enquanto isso, a lista vive só na página.

   SAÍDAS : eventos no document
            'link:salvar'    -> detail = { id (vazio se novo), titulo, descricao, url, assunto, tags, data }
            'link:excluir'   -> detail = { id }
            'filtro:salvar'  -> detail = { nome }
            'filtro:excluir' -> detail = { nome }

   Filtros marcados: o link precisa ter TODAS as tags marcadas. */
"use strict";

let links = [
    {
        id: 1,
        titulo: "Emissão de Comprovante de Inscrição e de Situação Cadastral",
        descricao: "Permite emitir o Comprovante de Inscrição e de Situação Cadastral de Pessoa Jurídica.",
        url: "https://www.gov.br/receitafederal/",
        assunto: "Cadastral",
        tags: ["Federal", "Consulta Pública"],
        data: "30/09/2026"
    }
];

const filtrosPadrao = [
    "Federal",
    "Estadual",
    "Municipal",
    "Cadastral",
    "Débitos",
    "Certidões",
    "Consulta Pública",
];

const modal = document.getElementById("modal-link");
const modalExcluir = document.getElementById("modal-link-excluir");
const formulario = document.getElementById("formulario");
let idParaExcluir = null;

function avisar(nome, detail) {
    document.dispatchEvent(new CustomEvent(nome, { detail: detail }));
}

function el(tag, classe, texto) {
    const e = document.createElement(tag);
    if (classe) e.className = classe;
    if (texto) e.textContent = texto;
    return e;
}

// Só aceita http/https: evita links "javascript:"
function linkSeguro(url) {
    try {
        const u = new URL(url, window.location.href);
        return (u.protocol === "http:" || u.protocol === "https:") ? u.href : "#";
    } catch (e) { return "#"; }
}

function botaoIcone(icone, rotulo, perigo, acao, id) {
    const b = el("button", "botao-icone" + (perigo ? " botao-icone--perigo" : ""));
    b.type = "button";
    b.dataset.acao = acao;
    b.dataset.id = id;
    b.title = rotulo;
    b.setAttribute("aria-label", rotulo);
    const i = el("i", "bi " + icone);
    i.setAttribute("aria-hidden", "true");
    b.appendChild(i);
    return b;
}

function criarFiltros() {
    const marcados = Array.from(document.querySelectorAll("#filtros input:checked")).map(i => i.value);
    const area = document.getElementById("filtros");
    area.replaceChildren();

    filtrosPadrao.forEach(filtro => {
        const linha = el("div", "filtro-linha");
        const label = el("label", "filtro");
        const input = document.createElement("input");
        input.type = "checkbox";
        input.value = filtro;
        input.checked = marcados.includes(filtro);
        input.addEventListener("change", filtrarLinks);
        label.append(input, document.createTextNode(" " + filtro));
        linha.append(label, botaoIcone("bi-x-lg", "Remover filtro " + filtro, true, "remover-filtro", filtro));
        area.appendChild(linha);
    });
}

function mostrarLinks(lista) {
    const area = document.getElementById("listaLinks");
    area.replaceChildren();

    if (lista.length === 0) {
        const vazio = el("div", "empty-state");
        vazio.append(el("strong", "", links.length ? "Nenhum link encontrado" : "Nenhum link cadastrado"),
                     el("p", "", links.length ? "Tente outra busca ou desmarque filtros." : "Os links adicionados aparecem aqui."));
        area.appendChild(vazio);
        return;
    }

    lista.forEach(link => {
        const card = el("article", "card dado-js");

        const info = el("div", "informacoes");
        const h3 = el("h3");
        const a = el("a", "", link.titulo);
        a.href = linkSeguro(link.url);
        a.target = "_blank";
        a.rel = "noopener noreferrer";
        h3.appendChild(a);
        const assunto = el("p");
        assunto.append(el("strong", "", "Assunto: "), document.createTextNode(link.assunto));
        info.append(h3, el("p", "", link.descricao), assunto);

        const detalhes = el("div", "detalhes");
        const acoes = el("div", "acoes-icone");
        acoes.append(botaoIcone("bi-pencil", "Editar link", false, "editar", link.id),
                     botaoIcone("bi-trash", "Excluir link", true, "excluir", link.id));
        const data = el("div", "data", "Atualizado em: " + link.data);
        const tags = el("div", "tags");
        link.tags.forEach(tag => tags.appendChild(el("span", "tag", tag)));
        detalhes.append(acoes, data, tags);

        card.append(info, detalhes);
        area.appendChild(card);
    });
}

function filtrarLinks() {
    const busca = document.getElementById("pesquisa").value.toLowerCase();

    const selecionados = Array.from(
        document.querySelectorAll("#filtros input:checked")
    ).map(input => input.value);

    const resultado = links.filter(link => {
        const texto = [
            link.titulo,
            link.descricao,
            link.assunto,
            ...link.tags
        ].join(" ").toLowerCase();

        const correspondeBusca = texto.includes(busca);

        const correspondeFiltro =
            selecionados.length === 0 ||
            selecionados.every(filtro => link.tags.includes(filtro));

        return correspondeBusca && correspondeFiltro;
    });

    mostrarLinks(resultado);
}

// Abre o modal: sem argumento = novo link; com link = edição
function mostrarFormulario(link) {
    formulario.reset();
    document.getElementById("modal-link-titulo").textContent = link ? "Editar link" : "Adicionar link";
    document.getElementById("link-id").value = link ? link.id : "";
    if (link) {
        ["titulo", "descricao", "url", "assunto"].forEach(k => { document.getElementById(k).value = link[k]; });
        document.getElementById("tags").value = link.tags.join(", ");
    }
    modal.showModal();
    document.getElementById("titulo").focus();
}

function achar(id) {
    return links.find(l => String(l.id) === String(id));
}

formulario.addEventListener("submit", function (event) {
    event.preventDefault();

    let url = document.getElementById("url").value.trim();
    if (!/^https?:\/\//i.test(url)) url = "https://" + url;

    const id = document.getElementById("link-id").value;
    const dados = {
        id: id || Date.now(),
        titulo: document.getElementById("titulo").value.trim(),
        descricao: document.getElementById("descricao").value.trim(),
        url: url,
        assunto: document.getElementById("assunto").value.trim(),
        tags: document.getElementById("tags").value
            .split(",")
            .map(tag => tag.trim())
            .filter(tag => tag !== ""),
        data: new Date().toLocaleDateString("pt-BR")
    };

    const existente = achar(id);
    if (existente) Object.assign(existente, dados);
    else links.push(dados);

    dados.tags.forEach(tag => {
        if (!filtrosPadrao.includes(tag)) filtrosPadrao.push(tag);
    });

    avisar("link:salvar", Object.assign({}, dados, { id: id }));
    criarFiltros();
    filtrarLinks();
    modal.close();

    const mensagem = document.getElementById("mensagem");
    mensagem.textContent = existente ? "Link atualizado com sucesso!" : "Link adicionado com sucesso!";
    setTimeout(() => { mensagem.textContent = ""; }, 4000);
});

document.getElementById("link-confirmar-exclusao").addEventListener("click", function () {
    links = links.filter(l => String(l.id) !== String(idParaExcluir));
    avisar("link:excluir", { id: idParaExcluir });
    filtrarLinks();
    modalExcluir.close();
});

document.getElementById("form-filtro").addEventListener("submit", function (event) {
    event.preventDefault();
    const campo = document.getElementById("novo-filtro");
    const nome = campo.value.trim();
    if (nome && !filtrosPadrao.some(f => f.toLowerCase() === nome.toLowerCase())) {
        filtrosPadrao.push(nome);
        avisar("filtro:salvar", { nome: nome });
        criarFiltros();
    }
    campo.value = "";
});

document.addEventListener("click", function (e) {
    const b = e.target.closest("button[data-acao]");
    if (b) {
        if (b.dataset.acao === "editar" && achar(b.dataset.id)) mostrarFormulario(achar(b.dataset.id));
        if (b.dataset.acao === "excluir") { idParaExcluir = b.dataset.id; modalExcluir.showModal(); }
        if (b.dataset.acao === "remover-filtro") {
            filtrosPadrao.splice(filtrosPadrao.indexOf(b.dataset.id), 1);
            avisar("filtro:excluir", { nome: b.dataset.id });
            criarFiltros();
            filtrarLinks();
        }
        return;
    }
    if (e.target.closest("[data-fechar]")) e.target.closest("dialog").close();
    else if (e.target.tagName === "DIALOG") e.target.close();
});

criarFiltros();
mostrarLinks(links);
