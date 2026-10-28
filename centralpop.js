"use strict";

const setores = document.querySelectorAll(".setor");
const tituloSetor = document.getElementById("titulo-setor");
const modoAdmin = document.getElementById("modo-admin");
const formDocumento = document.getElementById("form-documento");
const listaDocumentos = document.getElementById("lista-documentos");
const mensagemVazia = document.getElementById("mensagem-vazia");
const pesquisaDocumento = document.getElementById("pesquisa-documento");
const nomeDocumento = document.getElementById("nome-documento");
const categoriaDocumento = document.getElementById("categoria-documento");
const arquivoDocumento = document.getElementById("arquivo-documento");
const observacaoDocumento = document.getElementById("observacao-documento");

const nomesSetores = {
    Fiscal: "Departamento Fiscal",
    Pessoal: "Departamento Pessoal",
    Financeiro: "Departamento Financeiro",
    "Contábil": "Departamento Contábil",
    "Regularização": "Departamento de Regularização"
};

let setorAtual = "Fiscal";
let banco = null;

function abrirBanco() {
    if (!("indexedDB" in window)) {
        mostrarErro("Este navegador não oferece suporte ao armazenamento local necessário.");
        return;
    }

    const requisicao = indexedDB.open("CentralPOPsFatec", 1);

    requisicao.onupgradeneeded = function (evento) {
        const base = evento.target.result;

        if (!base.objectStoreNames.contains("documentos")) {
            const armazenamento = base.createObjectStore("documentos", {
                keyPath: "id",
                autoIncrement: true
            });
            armazenamento.createIndex("setor", "setor", { unique: false });
        }
    };

    requisicao.onsuccess = function (evento) {
        banco = evento.target.result;
        banco.onversionchange = function () {
            banco.close();
            banco = null;
            mostrarErro("O armazenamento foi atualizado em outra aba. Recarregue esta página.");
        };
        renderizarDocumentos();
        atualizarContadores();
    };

    requisicao.onerror = function () {
        mostrarErro("Não foi possível acessar o armazenamento local. Verifique as permissões do navegador.");
    };

    requisicao.onblocked = function () {
        mostrarErro("Feche outras abas desta página e tente novamente.");
    };
}

function mostrarErro(mensagem) {
    mensagemVazia.hidden = false;
    mensagemVazia.textContent = mensagem;
}

function obterDocumentos(callback) {
    if (!banco) return;

    const transacao = banco.transaction("documentos", "readonly");
    const requisicao = transacao.objectStore("documentos").getAll();

    requisicao.onsuccess = function () {
        callback(requisicao.result || []);
    };

    requisicao.onerror = function () {
        mostrarErro("Não foi possível carregar os documentos salvos.");
    };
}

setores.forEach(function (botao) {
    botao.addEventListener("click", function () {
        setorAtual = botao.dataset.setor;

        setores.forEach(function (item) {
            const selecionado = item === botao;
            item.classList.toggle("selecionado", selecionado);
            item.setAttribute("aria-pressed", String(selecionado));
        });

        tituloSetor.textContent = nomesSetores[setorAtual];
        pesquisaDocumento.value = "";
        renderizarDocumentos();
    });
});

modoAdmin.addEventListener("change", function () {
    formDocumento.hidden = !modoAdmin.checked;
    renderizarDocumentos();
});

pesquisaDocumento.addEventListener("input", renderizarDocumentos);

formDocumento.addEventListener("submit", function (evento) {
    evento.preventDefault();

    if (!banco) {
        alert("O armazenamento ainda não está disponível. Recarregue a página e tente novamente.");
        return;
    }

    const arquivo = arquivoDocumento.files[0];
    const nome = nomeDocumento.value.trim();

    if (!nome || !arquivo) {
        alert("Informe o nome do documento e selecione um arquivo.");
        return;
    }

    const documento = {
        setor: setorAtual,
        nome: nome,
        categoria: categoriaDocumento.value,
        observacao: observacaoDocumento.value.trim(),
        arquivo: arquivo,
        nomeArquivo: arquivo.name,
        tipoArquivo: arquivo.type || "application/octet-stream",
        tamanho: arquivo.size,
        data: new Date().toLocaleDateString("pt-BR")
    };

    const transacao = banco.transaction("documentos", "readwrite");
    transacao.objectStore("documentos").add(documento);

    transacao.oncomplete = function () {
        formDocumento.reset();
        formDocumento.hidden = !modoAdmin.checked;
        renderizarDocumentos();
        atualizarContadores();
    };

    transacao.onerror = function () {
        alert("Não foi possível salvar o documento. O armazenamento pode estar cheio ou indisponível.");
    };
});

function renderizarDocumentos() {
    obterDocumentos(function (documentos) {
        const termo = pesquisaDocumento.value.trim().toLocaleLowerCase("pt-BR");
        const filtrados = documentos.filter(function (documento) {
            const texto = [
                documento.nome,
                documento.categoria,
                documento.observacao,
                documento.nomeArquivo
            ].join(" ").toLocaleLowerCase("pt-BR");

            return documento.setor === setorAtual && texto.includes(termo);
        });

        listaDocumentos.replaceChildren();
        mensagemVazia.hidden = filtrados.length > 0;
        mensagemVazia.textContent = termo
            ? "Nenhum documento corresponde à sua pesquisa."
            : "Ainda não há documentos cadastrados neste departamento.";

        filtrados.forEach(function (documento) {
            listaDocumentos.appendChild(criarLinhaDocumento(documento));
        });
    });
}

function criarLinhaDocumento(documento) {
    const linha = document.createElement("article");
    linha.className = "documento dado-js";

    const icone = document.createElement("div");
    icone.className = "icone-arquivo";
    icone.setAttribute("aria-hidden", "true");
    icone.textContent = "▤";

    const detalhes = document.createElement("div");
    detalhes.className = "detalhes-documento";

    const titulo = document.createElement("h3");
    titulo.textContent = documento.nome;

    const descricao = document.createElement("p");
    const tipo = document.createElement("span");
    tipo.className = "etiqueta-tipo";
    tipo.textContent = documento.categoria;
    descricao.append(tipo, document.createTextNode(
        documento.nomeArquivo + " · " + formatarTamanho(documento.tamanho) + " · Adicionado em " + documento.data
    ));

    detalhes.append(titulo, descricao);

    if (documento.observacao) {
        const observacao = document.createElement("p");
        observacao.textContent = documento.observacao;
        detalhes.appendChild(observacao);
    }

    const acoes = document.createElement("div");
    acoes.className = "acoes-documento";

    const abrir = document.createElement("button");
    abrir.className = "acao-documento";
    abrir.type = "button";
    abrir.textContent = "Abrir / baixar";
    abrir.addEventListener("click", function () {
        baixarDocumento(documento);
    });
    acoes.appendChild(abrir);

    if (modoAdmin.checked) {
        const remover = document.createElement("button");
        remover.className = "acao-documento acao-remover";
        remover.type = "button";
        remover.textContent = "Remover";
        remover.addEventListener("click", function () {
            removerDocumento(documento.id);
        });
        acoes.appendChild(remover);
    }

    linha.append(icone, detalhes, acoes);
    return linha;
}

function baixarDocumento(documento) {
    if (!documento.arquivo) {
        alert("O arquivo deste registro não está disponível no armazenamento local.");
        return;
    }

    const url = URL.createObjectURL(documento.arquivo);
    const link = document.createElement("a");
    link.href = url;
    link.download = documento.nomeArquivo;
    link.rel = "noopener";
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(function () {
        URL.revokeObjectURL(url);
    }, 60000);
}

function removerDocumento(id) {
    if (!banco || !confirm("Deseja remover este documento deste navegador? Esta ação não pode ser desfeita.")) {
        return;
    }

    const transacao = banco.transaction("documentos", "readwrite");
    transacao.objectStore("documentos").delete(id);

    transacao.oncomplete = function () {
        renderizarDocumentos();
        atualizarContadores();
    };

    transacao.onerror = function () {
        alert("Não foi possível remover o documento. Tente novamente.");
    };
}

function atualizarContadores() {
    obterDocumentos(function (documentos) {
        document.querySelectorAll("[data-contador]").forEach(function (item) {
            const total = documentos.filter(function (documento) {
                return documento.setor === item.dataset.contador;
            }).length;

            item.textContent = total + (total === 1 ? " documento" : " documentos");
        });
    });
}

function formatarTamanho(bytes) {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
}

abrirBanco();
