/* centralpop.js — Central de POP's
   Departamentos (criar, renomear, trocar ícone, excluir) e documentos
   (adicionar, editar, arquivar, excluir, abrir).

   shortcut: os dados ficam no IndexedDB deste navegador ("CentralPOPsFatec").
   Trocar as funções gravar() / apagar() / carregar() por chamadas ao servidor
   quando o banco estiver pronto. Os nomes dos campos foram mantidos:
   documento = { id, setor, nome, categoria, observacao, arquivo, nomeArquivo,
                 tipoArquivo, tamanho, data, arquivado }
   departamento = { nome, icone }   ("setor" do documento = nome do departamento) */
"use strict";

const DEPARTAMENTOS_INICIAIS = [
    { nome: "Fiscal", icone: "bi-receipt" },
    { nome: "Pessoal", icone: "bi-people" },
    { nome: "Financeiro", icone: "bi-currency-dollar" },
    { nome: "Contábil", icone: "bi-journal-text" },
    { nome: "Regularização", icone: "bi-patch-check" }
];
const CATEGORIAS = ["POP", "Protocolo", "Manual", "Formulário", "Outro documento"];

const $ = id => document.getElementById(id);
const grade = $("grade-setores");
const tituloSetor = $("titulo-setor");
const filtrosDocumento = $("filtros-documento");
const listaDocumentos = $("lista-documentos");
const mensagemVazia = $("mensagem-vazia");
const avisoPop = $("aviso-pop");
const pesquisaDocumento = $("pesquisa-documento");

const modalDocumento = $("modal-documento");
const formDocumento = $("form-documento");
const nomeDocumento = $("nome-documento");
const departamentoDocumento = $("departamento-documento");
const arquivoDocumento = $("arquivo-documento");
const observacaoDocumento = $("observacao-documento");
const modalDepartamento = $("modal-departamento");
const formDepartamento = $("form-departamento");

let banco = null;
let departamentos = [];
let documentos = [];
let setorAtual = null;
let filtroAtual = "";          // "" = todos, uma categoria, ou "arquivados"
let idParaExcluir = null;
let departamentoParaExcluir = null;

/* ---------- Armazenamento ---------- */
function abrirBanco() {
    if (!("indexedDB" in window)) {
        mostrarErro("Este navegador não oferece suporte ao armazenamento local necessário.");
        return;
    }

    const requisicao = indexedDB.open("CentralPOPsFatec", 2);

    requisicao.onupgradeneeded = function (evento) {
        const base = evento.target.result;
        if (!base.objectStoreNames.contains("documentos")) {
            const armazenamento = base.createObjectStore("documentos", { keyPath: "id", autoIncrement: true });
            armazenamento.createIndex("setor", "setor", { unique: false });
        }
        if (!base.objectStoreNames.contains("departamentos")) {
            const deps = base.createObjectStore("departamentos", { keyPath: "nome" });
            DEPARTAMENTOS_INICIAIS.forEach(d => deps.add(d));
        }
    };

    requisicao.onsuccess = function (evento) {
        banco = evento.target.result;
        banco.onversionchange = function () {
            banco.close();
            banco = null;
            mostrarErro("O armazenamento foi atualizado em outra aba. Recarregue esta página.");
        };
        carregar();
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

function avisar(mensagem) {
    avisoPop.textContent = mensagem;
    setTimeout(() => { avisoPop.textContent = ""; }, 5000);
}

function carregar() {
    if (!banco) return;
    const transacao = banco.transaction(["documentos", "departamentos"], "readonly");
    const reqDocs = transacao.objectStore("documentos").getAll();
    const reqDeps = transacao.objectStore("departamentos").getAll();

    transacao.oncomplete = function () {
        documentos = reqDocs.result || [];
        departamentos = (reqDeps.result || []).sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR"));
        if (!departamentos.some(d => d.nome === setorAtual)) {
            setorAtual = departamentos.length ? departamentos[0].nome : null;
        }
        desenhar();
    };
    transacao.onerror = function () {
        mostrarErro("Não foi possível carregar os documentos salvos.");
    };
}

// operacoes: [{ store, tipo: "put" | "delete", valor }]
function gravar(operacoes, aoTerminar) {
    if (!banco) {
        avisar("O armazenamento ainda não está disponível. Recarregue a página e tente novamente.");
        return;
    }
    const stores = Array.from(new Set(operacoes.map(o => o.store)));
    const transacao = banco.transaction(stores, "readwrite");
    operacoes.forEach(o => transacao.objectStore(o.store)[o.tipo](o.valor));
    transacao.oncomplete = function () {
        if (aoTerminar) aoTerminar();
        carregar();
    };
    transacao.onerror = function () {
        avisar("Não foi possível salvar. O armazenamento pode estar cheio ou indisponível.");
    };
}

/* ---------- Desenho ---------- */
function el(tag, classe, texto) {
    const e = document.createElement(tag);
    if (classe) e.className = classe;
    if (texto) e.textContent = texto;
    return e;
}

function icone(nome) {
    const i = el("i", "bi " + (/^bi-[a-z0-9-]+$/.test(nome || "") ? nome : "bi-folder"));
    i.setAttribute("aria-hidden", "true");
    return i;
}

// Menu ⋮ (details nativo); itens = [[rótulo, ação, perigo?]]
function menuAcoes(rotulo, id, itens) {
    const det = el("details", "menu-acoes");
    const sum = el("summary");
    sum.setAttribute("aria-label", rotulo);
    sum.appendChild(icone("bi-three-dots-vertical"));
    const ul = el("ul");
    itens.forEach(([texto, acao, perigo]) => {
        const b = el("button", perigo ? "menu-perigo" : "", texto);
        b.type = "button";
        b.dataset.acao = acao;
        b.dataset.id = id;
        const li = el("li");
        li.appendChild(b);
        ul.appendChild(li);
    });
    det.append(sum, ul);
    return det;
}

function plural(n, palavra) {
    return n + " " + palavra + (n === 1 ? "" : "s");
}

function desenhar() {
    renderizarSetores();
    renderizarFiltros();
    renderizarDocumentos();
    tituloSetor.textContent = setorAtual || "Nenhum departamento";
    $("btn-adicionar-documento").disabled = !setorAtual;
}

function renderizarSetores() {
    grade.replaceChildren();

    departamentos.forEach(dep => {
        const item = el("div", "setor-item");
        const botao = el("button", "setor" + (dep.nome === setorAtual ? " selecionado" : ""));
        botao.type = "button";
        botao.dataset.setor = dep.nome;
        botao.setAttribute("aria-pressed", String(dep.nome === setorAtual));

        const ic = el("span", "icone-setor");
        ic.appendChild(icone(dep.icone));
        const total = documentos.filter(d => d.setor === dep.nome && !d.arquivado).length;
        const contador = el("span", "contador", plural(total, "documento"));
        contador.dataset.contador = dep.nome;
        botao.append(ic, el("span", "nome-setor", dep.nome), contador);

        item.append(botao, menuAcoes("Ações do departamento " + dep.nome, dep.nome, [
            ["Editar", "editar-departamento"],
            ["Excluir", "excluir-departamento", true]
        ]));
        grade.appendChild(item);
    });

    const novo = el("button", "setor setor--novo");
    novo.type = "button";
    novo.id = "btn-novo-departamento";
    const ic = el("span", "icone-setor");
    ic.appendChild(icone("bi-plus-lg"));
    novo.append(ic, el("span", "nome-setor", "Novo departamento"));
    grade.appendChild(novo);
}

function renderizarFiltros() {
    const arquivados = documentos.filter(d => d.setor === setorAtual && d.arquivado).length;
    const opcoes = [["", "Todos"]].concat(CATEGORIAS.map(c => [c, c]), [["arquivados", "Arquivados (" + arquivados + ")"]]);

    filtrosDocumento.replaceChildren();
    opcoes.forEach(([valor, texto]) => {
        const b = el("button", "ferr-filtro" + (valor === "arquivados" ? " filtro-arquivados" : ""), texto);
        b.type = "button";
        b.dataset.filtro = valor;
        b.setAttribute("aria-pressed", String(valor === filtroAtual));
        filtrosDocumento.appendChild(b);
    });
}

function renderizarDocumentos() {
    const termo = pesquisaDocumento.value.trim().toLocaleLowerCase("pt-BR");
    const verArquivados = filtroAtual === "arquivados";

    const filtrados = documentos.filter(function (documento) {
        const texto = [
            documento.nome,
            documento.categoria,
            documento.observacao,
            documento.nomeArquivo
        ].join(" ").toLocaleLowerCase("pt-BR");

        return documento.setor === setorAtual &&
            !!documento.arquivado === verArquivados &&
            (verArquivados || !filtroAtual || documento.categoria === filtroAtual) &&
            texto.includes(termo);
    }).sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR"));

    listaDocumentos.replaceChildren();
    mensagemVazia.hidden = filtrados.length > 0;
    mensagemVazia.textContent = !setorAtual ? "Crie um departamento para começar."
        : termo ? "Nenhum documento corresponde à sua pesquisa."
        : verArquivados ? "Nenhum documento arquivado neste departamento."
        : "Ainda não há documentos aqui.";

    filtrados.forEach(documento => listaDocumentos.appendChild(criarLinhaDocumento(documento)));
}

function criarLinhaDocumento(documento) {
    const linha = el("article", "documento dado-js" + (documento.arquivado ? " documento--arquivado" : ""));

    const ic = el("div", "icone-arquivo");
    ic.appendChild(icone("bi-file-earmark-text"));

    const detalhes = el("div", "detalhes-documento");
    const descricao = el("p");
    descricao.append(el("span", "etiqueta-tipo", documento.categoria), document.createTextNode(
        documento.nomeArquivo + " · " + formatarTamanho(documento.tamanho) + " · Atualizado em " + documento.data
    ));
    detalhes.append(el("h3", "", documento.nome), descricao);
    if (documento.observacao) detalhes.appendChild(el("p", "", documento.observacao));

    const acoes = el("div", "acoes-documento");
    const abrir = el("button", "acao-documento", "Abrir / baixar");
    abrir.type = "button";
    abrir.dataset.acao = "abrir";
    abrir.dataset.id = documento.id;
    acoes.append(abrir, menuAcoes("Ações do documento " + documento.nome, documento.id, [
        ["Editar", "editar-documento"],
        [documento.arquivado ? "Desarquivar" : "Arquivar", "arquivar-documento"],
        ["Excluir", "excluir-documento", true]
    ]));

    linha.append(ic, detalhes, acoes);
    return linha;
}

function formatarTamanho(bytes) {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
}

/* ---------- Documentos ---------- */
function acharDocumento(id) {
    return documentos.find(d => String(d.id) === String(id));
}

function abrirModalDocumento(documento) {
    formDocumento.reset();
    $("documento-mensagem").textContent = "";
    $("modal-documento-titulo").textContent = documento ? "Editar documento" : "Adicionar documento";
    $("documento-id").value = documento ? documento.id : "";

    departamentoDocumento.replaceChildren();
    departamentos.forEach(d => {
        const o = el("option", "", d.nome);
        o.value = d.nome;
        departamentoDocumento.appendChild(o);
    });
    departamentoDocumento.value = documento ? documento.setor : setorAtual;

    if (documento) {
        nomeDocumento.value = documento.nome;
        formDocumento.elements.categoria.value = documento.categoria;
        observacaoDocumento.value = documento.observacao || "";
    }
    $("arquivo-nome").textContent = documento
        ? "Atual: " + documento.nomeArquivo + " (escolha outro só se quiser trocar)"
        : "Nenhum arquivo escolhido";

    modalDocumento.showModal();
    nomeDocumento.focus();
}

formDocumento.addEventListener("submit", function (evento) {
    evento.preventDefault();

    const anterior = acharDocumento($("documento-id").value);
    const arquivo = arquivoDocumento.files[0];
    const nome = nomeDocumento.value.trim();
    const mensagem = $("documento-mensagem");

    if (!nome) { mensagem.textContent = "Informe o nome do documento."; nomeDocumento.focus(); return; }
    if (!arquivo && !anterior) { mensagem.textContent = "Escolha o arquivo do documento."; return; }

    const documento = Object.assign({}, anterior, {
        setor: departamentoDocumento.value,
        nome: nome,
        categoria: formDocumento.elements.categoria.value,
        observacao: observacaoDocumento.value.trim(),
        data: new Date().toLocaleDateString("pt-BR"),
        arquivado: anterior ? !!anterior.arquivado : false
    });
    if (arquivo) {
        Object.assign(documento, {
            arquivo: arquivo,
            nomeArquivo: arquivo.name,
            tipoArquivo: arquivo.type || "application/octet-stream",
            tamanho: arquivo.size
        });
    }

    gravar([{ store: "documentos", tipo: "put", valor: documento }], function () {
        modalDocumento.close();
        avisar(anterior ? "Documento atualizado." : "Documento adicionado.");
    });
});

arquivoDocumento.addEventListener("change", function () {
    $("arquivo-nome").textContent = arquivoDocumento.files[0] ? arquivoDocumento.files[0].name : "Nenhum arquivo escolhido";
});

// Arrastar e soltar na área do arquivo
const zona = document.querySelector(".zona-arquivo");
zona.addEventListener("dragover", e => { e.preventDefault(); zona.classList.add("zona-arquivo--ativa"); });
zona.addEventListener("dragleave", () => zona.classList.remove("zona-arquivo--ativa"));
zona.addEventListener("drop", function (e) {
    e.preventDefault();
    zona.classList.remove("zona-arquivo--ativa");
    if (e.dataTransfer.files.length) {
        arquivoDocumento.files = e.dataTransfer.files;
        arquivoDocumento.dispatchEvent(new Event("change"));
    }
});

function baixarDocumento(documento) {
    if (!documento.arquivo) {
        avisar("O arquivo deste registro não está disponível no armazenamento local.");
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

$("documento-confirmar-exclusao").addEventListener("click", function () {
    gravar([{ store: "documentos", tipo: "delete", valor: Number(idParaExcluir) }], function () {
        $("modal-documento-excluir").close();
        avisar("Documento excluído.");
    });
});

/* ---------- Departamentos ---------- */
function acharDepartamento(nome) {
    return departamentos.find(d => d.nome === nome);
}

function abrirModalDepartamento(dep) {
    formDepartamento.reset();
    $("departamento-mensagem").textContent = "";
    $("modal-departamento-titulo").textContent = dep ? "Editar departamento" : "Novo departamento";
    $("departamento-original").value = dep ? dep.nome : "";
    $("departamento-nome").value = dep ? dep.nome : "";
    const ic = formDepartamento.elements["departamento-icone"];
    ic.value = dep ? dep.icone : "bi-briefcase";
    modalDepartamento.showModal();
    $("departamento-nome").focus();
}

formDepartamento.addEventListener("submit", function (evento) {
    evento.preventDefault();
    const original = $("departamento-original").value;
    const nome = $("departamento-nome").value.trim().replace(/\s+/g, " ");
    const mensagem = $("departamento-mensagem");

    if (!nome) { mensagem.textContent = "Informe o nome do departamento."; return; }
    if (departamentos.some(d => d.nome.toLowerCase() === nome.toLowerCase() && d.nome !== original)) {
        mensagem.textContent = "Já existe um departamento com esse nome.";
        return;
    }

    const operacoes = [{ store: "departamentos", tipo: "put",
        valor: { nome: nome, icone: formDepartamento.elements["departamento-icone"].value || "bi-folder" } }];

    // Renomear: a chave é o nome, então troca o registro e atualiza os documentos
    if (original && original !== nome) {
        operacoes.push({ store: "departamentos", tipo: "delete", valor: original });
        documentos.filter(d => d.setor === original).forEach(d => {
            operacoes.push({ store: "documentos", tipo: "put", valor: Object.assign({}, d, { setor: nome }) });
        });
    }

    gravar(operacoes, function () {
        if (!original || setorAtual === original) setorAtual = nome;
        modalDepartamento.close();
        avisar(original ? "Departamento atualizado." : "Departamento criado.");
    });
});

function pedirExclusaoDepartamento(nome) {
    departamentoParaExcluir = nome;
    const total = documentos.filter(d => d.setor === nome).length;
    $("departamento-excluir-titulo").textContent = 'Excluir "' + nome + '"?';
    $("departamento-excluir-aviso").textContent = total
        ? "Este departamento tem " + plural(total, "documento") + " (incluindo arquivados). Todos serão apagados junto. Esta ação não pode ser desfeita."
        : "O departamento será apagado. Esta ação não pode ser desfeita.";
    $("modal-departamento-excluir").showModal();
}

$("departamento-confirmar-exclusao").addEventListener("click", function () {
    const nome = departamentoParaExcluir;
    const operacoes = [{ store: "departamentos", tipo: "delete", valor: nome }];
    documentos.filter(d => d.setor === nome).forEach(d => operacoes.push({ store: "documentos", tipo: "delete", valor: d.id }));
    gravar(operacoes, function () {
        $("modal-departamento-excluir").close();
        avisar('Departamento "' + nome + '" excluído.');
    });
});

/* ---------- Cliques ---------- */
$("btn-adicionar-documento").addEventListener("click", () => abrirModalDocumento(null));

pesquisaDocumento.addEventListener("input", renderizarDocumentos);

filtrosDocumento.addEventListener("click", function (e) {
    const b = e.target.closest("button[data-filtro]");
    if (!b) return;
    filtroAtual = b.dataset.filtro;
    renderizarFiltros();
    renderizarDocumentos();
});

document.addEventListener("click", function (e) {
    // Fecha menus ⋮ abertos ao clicar fora
    document.querySelectorAll(".menu-acoes[open]").forEach(d => {
        if (!d.contains(e.target)) d.open = false;
    });

    const setor = e.target.closest("button.setor[data-setor]");
    if (setor) {
        setorAtual = setor.dataset.setor;
        filtroAtual = "";
        pesquisaDocumento.value = "";
        desenhar();
        return;
    }
    if (e.target.closest("#btn-novo-departamento")) { abrirModalDepartamento(null); return; }

    const b = e.target.closest("button[data-acao]");
    if (b) {
        const menu = b.closest("details");
        if (menu) menu.open = false;
        const id = b.dataset.id;
        const doc = acharDocumento(id);
        switch (b.dataset.acao) {
            case "abrir": if (doc) baixarDocumento(doc); break;
            case "editar-documento": if (doc) abrirModalDocumento(doc); break;
            case "arquivar-documento":
                if (doc) gravar([{ store: "documentos", tipo: "put", valor: Object.assign({}, doc, { arquivado: !doc.arquivado }) }],
                    () => avisar(doc.arquivado ? "Documento desarquivado." : "Documento arquivado."));
                break;
            case "excluir-documento": idParaExcluir = id; $("modal-documento-excluir").showModal(); break;
            case "editar-departamento": abrirModalDepartamento(acharDepartamento(id)); break;
            case "excluir-departamento": pedirExclusaoDepartamento(id); break;
        }
        return;
    }

    if (e.target.closest("[data-fechar]")) e.target.closest("dialog").close();
    else if (e.target.tagName === "DIALOG") e.target.close();
});

abrirBanco();
