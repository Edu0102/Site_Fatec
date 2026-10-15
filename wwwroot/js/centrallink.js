let links = [
    {
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

function criarFiltros() {
    document.getElementById("filtros").innerHTML =
        filtrosPadrao.map(filtro => `
            <label class="filtro">
                <input type="checkbox" value="${filtro}" onchange="filtrarLinks()">
                ${filtro}
            </label>
        `).join("");
}

function mostrarLinks(lista) {
    const area = document.getElementById("listaLinks");

    if (lista.length === 0) {
        area.innerHTML = "<p>Nenhum link encontrado.</p>";
        return;
    }

    area.innerHTML = lista.map(link => `
        <div class="card">
            <div class="informacoes">
                <h3>
                    <a href="${link.url}" target="_blank" rel="noopener noreferrer">${link.titulo}</a>
                </h3>
                <p>${link.descricao}</p>
                <p><strong>Assunto:</strong> ${link.assunto}</p>
            </div>

            <div class="detalhes">
                <div class="data">
                    Atualizado em:<br>${link.data}
                </div>

                <div class="tags">
                    ${link.tags.map(tag => `<span class="tag">${tag}</span>`).join("")}
                </div>
            </div>
        </div>
    `).join("");
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

function mostrarFormulario() {
    const formulario = document.getElementById("formulario");

    formulario.style.display =
        formulario.style.display === "block" ? "none" : "block";
}

document.getElementById("formulario").addEventListener("submit", function(event) {
    event.preventDefault();

    const novoLink = {
        titulo: document.getElementById("titulo").value.trim(),
        descricao: document.getElementById("descricao").value.trim(),
        url: document.getElementById("url").value.trim(),
        assunto: document.getElementById("assunto").value.trim(),
        tags: document.getElementById("tags").value
            .split(",")
            .map(tag => tag.trim())
            .filter(tag => tag !== ""),
        data: new Date().toLocaleDateString("pt-BR")
    };

    links.push(novoLink);

    novoLink.tags.forEach(tag => {
        if (!filtrosPadrao.includes(tag)) {
            filtrosPadrao.push(tag);
        }
    });

    criarFiltros();
    filtrarLinks();

    this.reset();
    this.style.display = "none";

    document.getElementById("mensagem").textContent = "Link adiconado com sucesso!";
});

criarFiltros();
mostrarLinks(links);