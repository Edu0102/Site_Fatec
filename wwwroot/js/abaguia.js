(function () {
    "use strict";

    // Evita carregar duas vezes se o script for incluído repetido por engano.
    if (window.AbaGuia) return;

    /* ======================================================================
       1. CONFIGURAÇÃO — textos e passos de cada página
       ----------------------------------------------------------------------
       Cada passo:
         alvo   : lista de seletores CSS. Usa-se o primeiro que existir e estiver
                  visível. Sem "alvo" (ou nenhum visível) o passo aparece
                  centralizado. Passos com alvo ausente são ignorados.
         titulo : título curto do passo.
         texto  : explicação em linguagem simples.
         link   : (opcional) { texto, caminho } — caminho relativo à raiz do site.
       ====================================================================== */
    const PAGINAS = {
        /* ----- Hub principal ----- */
        index: {
            caixa: {
                titulo: "Precisa de ajuda?",
                texto: "Veja para onde cada botão do hub leva."
            },
            passos: [
                {
                    titulo: "Bem-vindo ao hub",
                    texto: "Este é o ponto de partida do portal. Vou mostrar para onde cada botão leva."
                },
                {
                    alvo: ['a[href$="checklist.html"]'],
                    titulo: "Checklist",
                    texto: "Organizador de tarefas. Mostra o que você já fez e o que ainda falta."
                },
                {
                    alvo: ['a[href$="centrallink.html"]'],
                    titulo: "Central Links",
                    texto: "Biblioteca de links úteis do dia a dia. Lá também dá para sugerir novos links."
                },
                {
                    alvo: ['a[href$="centralpop.html"]'],
                    titulo: "POP's",
                    texto: "Repositório com os Procedimentos Operacionais Padrão de uso habitual, separados por departamento."
                },
                {
                    alvo: ['a[href$="guia.html"]'],
                    titulo: "Guia",
                    texto: "Orientações aprofundadas sobre as funcionalidades específicas do site."
                },
                {
                    alvo: ['a[href$="feedback.html"]', ".btn-feedback"],
                    titulo: "Feedback",
                    texto: "Sugira adições ou mudanças para o portal. Para rever esta ajuda, use o botão ? no canto inferior esquerdo."
                }
            ]
        },

        /* ----- Feedback ----- */
        feedback: {
            caixa: {
                titulo: "Como enviar uma sugestão?",
                texto: "Entenda como sugerir adições ou mudanças."
            },
            passos: [
                {
                    alvo: [".formulario"],
                    titulo: "Espaço de feedback",
                    texto: "Aqui você sugere o que gostaria de ver adicionado ou alterado no portal."
                },
                {
                    alvo: ["#assunto"],
                    titulo: "Assunto",
                    texto: "Resuma a sua ideia em poucas palavras. Ex.: \"Novo link para a Central\"."
                },
                {
                    alvo: ["#motivo"],
                    titulo: "Motivo e função",
                    texto: "Explique por que a mudança é útil e como ela deveria funcionar."
                },
                {
                    alvo: [".formulario button[type=\"submit\"]", ".formulario button"],
                    titulo: "Enviar",
                    texto: "Quando terminar de preencher, clique em Enviar para registrar a sugestão."
                }
            ],
            // Se vier da Central Links com ?assunto=..., preenche o campo Assunto.
            aoMontar: function () {
                const assunto = new URLSearchParams(window.location.search).get("assunto");
                const campo = document.getElementById("assunto");
                if (assunto && campo && !campo.value) campo.value = assunto;
            }
        },

        /* ----- Checklist ----- */
        checklist: {
            caixa: {
                titulo: "Como usar o checklist?",
                texto: "Aprenda a acompanhar o que está feito e o que falta."
            },
            passos: [
                {
                    alvo: [".summary-grid"],
                    titulo: "Resumo",
                    texto: "Mostra quantas tarefas existem no total, quantas já foram concluídas e quantas estão pendentes."
                },
                {
                    alvo: ["#form-tarefa"],
                    titulo: "Nova tarefa",
                    texto: "Digite o nome da tarefa e clique em Adicionar tarefa para incluí-la na lista."
                },
                {
                    alvo: ["#lista-tarefas:not(:empty)", "#lista-vazia:not([hidden])"],
                    titulo: "Suas tarefas",
                    texto: "Marque cada item ao concluir. O que está marcado é o que já foi feito; o restante ainda falta."
                },
                {
                    alvo: [".progress-panel"],
                    titulo: "Seu progresso",
                    texto: "A barra mostra a porcentagem concluída das tarefas de hoje."
                },
                {
                    alvo: ["#desmarcar-todas"],
                    titulo: "Desmarcar todas",
                    texto: "Começando um novo dia? Este botão limpa as marcações e mantém as tarefas na lista."
                }
            ]
        },

        /* ----- Central Links ----- */
        centrallink: {
            caixa: {
                titulo: "Como achar um link?",
                texto: "Pesquise, filtre e sugira novos links.",
                link: { texto: "Sugerir um link", caminho: "html/feedback.html?assunto=Sugest%C3%A3o%20de%20novo%20link" }
            },
            passos: [
                {
                    alvo: [".pesquisa", "#pesquisa"],
                    titulo: "Pesquisa",
                    texto: "Digite parte do título, da descrição ou de uma tag para encontrar um link."
                },
                {
                    alvo: [".conteudo > aside", "#filtros"],
                    titulo: "Filtros padrões",
                    texto: "Clique em um assunto para ver só os links dele."
                },
                {
                    alvo: [".acoes button"],
                    titulo: "Adicionar link",
                    texto: "Abre o formulário para cadastrar um novo link na biblioteca."
                },
                {
                    alvo: ["#listaLinks"],
                    titulo: "Biblioteca de links",
                    texto: "Os links úteis e rotineiros ficam aqui. Clique em um deles para abrir."
                },
                {
                    titulo: "Não achou o que precisa?",
                    texto: "Envie um feedback sugerindo um novo link e ele poderá entrar na biblioteca.",
                    link: { texto: "Sugerir um link", caminho: "html/feedback.html?assunto=Sugest%C3%A3o%20de%20novo%20link" }
                }
            ]
        },

        /* ----- Central POP ----- */
        centralpop: {
            caixa: {
                titulo: "Como achar um POP?",
                texto: "Encontre os procedimentos de cada departamento."
            },
            passos: [
                {
                    alvo: [".cabecalho-pagina"],
                    titulo: "Central de POP's",
                    texto: "Repositório com os Procedimentos Operacionais Padrão (POPs) de uso habitual."
                },
                {
                    alvo: ["#grade-setores", ".grade-setores"],
                    titulo: "Departamentos",
                    texto: "Escolha um departamento. Cada botão mostra quantos documentos ele tem."
                },
                {
                    alvo: [".campo-pesquisa"],
                    titulo: "Buscar documento",
                    texto: "Digite o nome do documento para filtrar a lista do departamento escolhido."
                },
                {
                    alvo: ["#lista-documentos:not(:empty)", "#mensagem-vazia"],
                    titulo: "Documentos",
                    texto: "Os POPs e demais documentos do departamento aparecem aqui, prontos para consulta."
                },
                {
                    alvo: [".painel-admin"],
                    titulo: "Área de gerenciamento",
                    texto: "Ative esta opção para adicionar ou remover documentos."
                }
            ]
        },

        /* ----- Aba Guia ----- */
        guia: {
            caixa: {
                titulo: "Como usar os guias?",
                texto: "Conheça as orientações desta página."
            },
            passos: [
                {
                    alvo: [".page-heading"],
                    titulo: "Aba Guia",
                    texto: "Aqui ficam os guias aprofundados sobre as funcionalidades específicas do site."
                },
                {
                    alvo: ["#painel-adm:not([hidden])"],
                    titulo: "Adicionar guia",
                    texto: "Na visão administrativa, cadastre novos guias com título e conteúdo."
                },
                {
                    alvo: [".guias-panel .panel-heading"],
                    titulo: "Guias disponíveis",
                    texto: "O contador mostra quantos guias estão cadastrados."
                },
                {
                    alvo: ["#lista-guias:not(:empty)", "#guias-vazios:not([hidden])"],
                    titulo: "Lista de guias",
                    texto: "Abra um guia para ler o passo a passo. Quando houver novos guias, eles aparecem aqui."
                }
            ]
        }
    };

    /* ======================================================================
       2. LOCALIZAÇÃO — descobre caminhos e página atual
       ====================================================================== */
    const scriptTag = document.currentScript || document.querySelector('script[src*="abaguia.js"]');
    // Raiz do site (pasta que contém css/, js/, html/), deduzida a partir do próprio script.
    const RAIZ = new URL("../", scriptTag ? scriptTag.src : window.location.href);
    const url = function (caminho) { return new URL(caminho, RAIZ).href; };

    function detectarPagina() {
        if (scriptTag && scriptTag.dataset.pagina) return scriptTag.dataset.pagina;
        const arquivo = window.location.pathname.split("/").pop().replace(/\.html?$/i, "").toLowerCase();
        return arquivo === "" ? "index" : arquivo;
    }

    const PAGINA = detectarPagina();
    const CONFIG = PAGINAS[PAGINA];
    if (!CONFIG) return; // página sem guia configurado: não faz nada

    /* ======================================================================
       3. ESTADO e referências
       ====================================================================== */
    const CHAVE_ARMAZENAMENTO = "frcont-abaguia-v1";
    const MARGEM = 12;     // distância mínima do cartão às bordas da tela (px)
    const FOLGA = 14;      // distância entre o elemento destacado e o cartão (px)
    const RESPIRO = 6;     // folga da moldura ao redor do elemento (px)
    const reduzMovimento = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    // Espelha html/abaguia.html, pois navegadores bloqueiam fetch de arquivos file://.
    const HTML_LOCAL = `
        <div class="abaguia" id="abaguia">
            <section class="abaguia-caixa" id="abaguia-caixa" aria-labelledby="abaguia-caixa-titulo">
                <button type="button" class="abaguia-minimizar" data-abaguia-acao="minimizar"
                        aria-label="Minimizar ajuda">&times;</button>
                <h2 class="abaguia-caixa-titulo" id="abaguia-caixa-titulo">Precisa de ajuda?</h2>
                <p class="abaguia-caixa-texto" data-abaguia="caixa-texto">Faça um tour rápido por esta página.</p>
                <div class="abaguia-caixa-acoes">
                    <button type="button" class="abaguia-botao" data-abaguia-acao="iniciar">Iniciar tour</button>
                    <a class="abaguia-link" data-abaguia="caixa-link" href="#" hidden></a>
                </div>
            </section>
            <button type="button" class="abaguia-reabrir" id="abaguia-reabrir" data-abaguia-acao="abrir"
                    aria-label="Abrir ajuda desta página" hidden>?</button>
        </div>
        <div class="abaguia-tour" id="abaguia-tour" hidden>
            <div class="abaguia-bloqueio" data-abaguia-acao="bloqueio"></div>
            <div class="abaguia-destaque" id="abaguia-destaque" aria-hidden="true"></div>
            <div class="abaguia-popover" id="abaguia-popover" role="dialog" aria-modal="true"
                 aria-labelledby="abaguia-passo-titulo" aria-describedby="abaguia-passo-texto" tabindex="-1">
                <p class="abaguia-passo-contador" data-abaguia="contador" aria-live="polite">Passo 1 de 1</p>
                <h3 class="abaguia-passo-titulo" id="abaguia-passo-titulo">Título do passo</h3>
                <p class="abaguia-passo-texto" id="abaguia-passo-texto">Texto do passo.</p>
                <a class="abaguia-link abaguia-passo-link" data-abaguia="passo-link" href="#" hidden></a>
                <div class="abaguia-passo-acoes">
                    <button type="button" class="abaguia-texto-botao" data-abaguia-acao="pular">Pular tour</button>
                    <span class="abaguia-passo-navegacao">
                        <button type="button" class="abaguia-botao abaguia-botao--claro" data-abaguia-acao="voltar">Voltar</button>
                        <button type="button" class="abaguia-botao" data-abaguia-acao="proximo">Próximo</button>
                    </span>
                </div>
            </div>
        </div>`;

    const el = {};                 // referências aos elementos do componente
    let passos = [];               // passos válidos do tour atual
    let indice = 0;                // passo atual
    let ativo = false;             // tour aberto?
    let focoAnterior = null;       // quem tinha o foco antes do tour
    let quadro = 0;                // id do requestAnimationFrame de reposicionamento
    let timerAnimacao = 0;

    // Preferência "minimizado" guardada por página (try/catch: o storage pode estar bloqueado).
    function lerMinimizado() {
        try {
            const dados = JSON.parse(localStorage.getItem(CHAVE_ARMAZENAMENTO)) || {};
            return dados[PAGINA] === true;
        } catch (e) { return false; }
    }
    function salvarMinimizado(valor) {
        try {
            const dados = JSON.parse(localStorage.getItem(CHAVE_ARMAZENAMENTO)) || {};
            dados[PAGINA] = valor;
            localStorage.setItem(CHAVE_ARMAZENAMENTO, JSON.stringify(dados));
        } catch (e) { /* sem armazenamento: apenas não lembra */ }
    }

    /* ======================================================================
       4. MONTAGEM — injeta CSS e HTML
       ====================================================================== */
    function carregarCss() {
        if (document.querySelector('link[href*="abaguia.css"]')) return;
        const link = document.createElement("link");
        link.rel = "stylesheet";
        link.href = url("css/abaguia.css");
        document.head.appendChild(link);
    }

    async function montar() {
        carregarCss();

        let html;
        if (window.location.protocol === "file:") {
            html = HTML_LOCAL;
        } else {
            const resposta = await fetch(url("html/abaguia.html"));
            if (!resposta.ok) throw new Error("abaguia.html não encontrado (" + resposta.status + ")");
            html = await resposta.text();
        }

        const recipiente = document.createElement("div");
        recipiente.innerHTML = html;
        // Move os nós para o <body> (sem div extra, para não criar contexto de empilhamento).
        while (recipiente.firstChild) document.body.appendChild(recipiente.firstChild);

        el.raiz = document.getElementById("abaguia");
        el.caixa = document.getElementById("abaguia-caixa");
        el.reabrir = document.getElementById("abaguia-reabrir");
        el.tour = document.getElementById("abaguia-tour");
        el.destaque = document.getElementById("abaguia-destaque");
        el.popover = document.getElementById("abaguia-popover");
        el.caixaTitulo = document.getElementById("abaguia-caixa-titulo");
        el.caixaTexto = el.raiz.querySelector('[data-abaguia="caixa-texto"]');
        el.caixaLink = el.raiz.querySelector('[data-abaguia="caixa-link"]');
        el.contador = el.popover.querySelector('[data-abaguia="contador"]');
        el.passoTitulo = document.getElementById("abaguia-passo-titulo");
        el.passoTexto = document.getElementById("abaguia-passo-texto");
        el.passoLink = el.popover.querySelector('[data-abaguia="passo-link"]');
        el.btnVoltar = el.popover.querySelector('[data-abaguia-acao="voltar"]');
        el.btnProximo = el.popover.querySelector('[data-abaguia-acao="proximo"]');

        preencherCaixa();
        definirMinimizado(lerMinimizado(), false);
        if (typeof CONFIG.aoMontar === "function") CONFIG.aoMontar();
    }

    function configurarLink(a, dados) {
        if (dados && dados.caminho) {
            a.textContent = dados.texto;
            a.href = url(dados.caminho);
            a.hidden = false;
        } else {
            a.hidden = true;
            a.removeAttribute("href");
        }
    }

    function preencherCaixa() {
        el.caixaTitulo.textContent = CONFIG.caixa.titulo;
        el.caixaTexto.textContent = CONFIG.caixa.texto;
        configurarLink(el.caixaLink, CONFIG.caixa.link);
    }

    /* ======================================================================
       5. CAIXA FLUTUANTE — abrir / minimizar
       ====================================================================== */
    function definirMinimizado(minimizado, salvar) {
        el.caixa.hidden = minimizado;
        el.reabrir.hidden = !minimizado;
        if (salvar !== false) salvarMinimizado(minimizado);
    }

    function abrir() {
        definirMinimizado(false);
        const botao = el.caixa.querySelector('[data-abaguia-acao="iniciar"]');
        if (botao) botao.focus();
    }

    function minimizar() {
        definirMinimizado(true);
        el.reabrir.focus();
    }

    /* ======================================================================
       6. TOUR — controle dos passos
       ====================================================================== */

    // Elemento realmente visível (existe, ocupa espaço e não está em área [hidden]).
    function visivel(elemento) {
        return !!elemento && elemento.getClientRects().length > 0;
    }

    // Primeiro seletor da lista que existe e está visível.
    function resolverAlvo(seletores) {
        for (let i = 0; i < (seletores || []).length; i++) {
            let encontrado = null;
            try { encontrado = document.querySelector(seletores[i]); } catch (e) { /* seletor inválido */ }
            if (visivel(encontrado)) return encontrado;
        }
        return null;
    }

    // Monta a lista de passos válidos no momento em que o tour começa
    // (assim conteúdo criado por outros scripts, como tarefas, já existe).
    function prepararPassos() {
        const lista = [];
        CONFIG.passos.forEach(function (passo) {
            const alvo = resolverAlvo(passo.alvo);
            if (passo.alvo && !alvo) return; // alvo esperado mas ausente/oculto: pula o passo
            lista.push({ dados: passo, alvo: alvo });
        });
        return lista;
    }

    async function iniciarTour() {
        if (ativo) return;
        try { await pronto; } catch (e) { return; }

        passos = prepararPassos();
        if (!passos.length) return;

        ativo = true;
        indice = 0;
        focoAnterior = document.activeElement;

        el.tour.hidden = false;
        el.raiz.classList.add("abaguia--em-tour");

        window.addEventListener("resize", agendarReposicionamento);
        window.addEventListener("scroll", agendarReposicionamento, true);
        document.addEventListener("keydown", aoTeclar, true);

        mostrarPasso(0, true);
    }

    function encerrarTour() {
        if (!ativo) return;
        ativo = false;

        el.tour.hidden = true;
        el.raiz.classList.remove("abaguia--em-tour");
        window.removeEventListener("resize", agendarReposicionamento);
        window.removeEventListener("scroll", agendarReposicionamento, true);
        document.removeEventListener("keydown", aoTeclar, true);
        cancelAnimationFrame(quadro);

        // Após o tour, a caixa fica minimizada para não atrapalhar a página.
        definirMinimizado(true);
        el.reabrir.focus();
        focoAnterior = null;
    }

    function mostrarPasso(novoIndice, primeiro) {
        indice = Math.max(0, Math.min(novoIndice, passos.length - 1));
        const passo = passos[indice];
        const ultimo = indice === passos.length - 1;

        // Conteúdo do cartão
        el.contador.textContent = "Passo " + (indice + 1) + " de " + passos.length;
        el.passoTitulo.textContent = passo.dados.titulo;
        el.passoTexto.textContent = passo.dados.texto;
        configurarLink(el.passoLink, passo.dados.link);
        el.btnVoltar.disabled = indice === 0;
        el.btnProximo.textContent = ultimo ? "Concluir" : "Próximo";

        // Leva o elemento para a área visível antes de medir.
        if (passo.alvo) {
            const alto = passo.alvo.getBoundingClientRect().height > window.innerHeight * 0.6;
            passo.alvo.scrollIntoView({ block: alto ? "start" : "center", inline: "nearest", behavior: "auto" });
        }

        // Anima a moldura apenas na troca de passo.
        if (!primeiro && !reduzMovimento) {
            el.destaque.classList.add("abaguia-destaque--animar");
            clearTimeout(timerAnimacao);
            timerAnimacao = setTimeout(function () {
                el.destaque.classList.remove("abaguia-destaque--animar");
            }, 300);
        }

        posicionar();
        el.popover.focus();
    }

    function proximo() {
        if (indice >= passos.length - 1) encerrarTour();
        else mostrarPasso(indice + 1);
    }

    function anterior() {
        if (indice > 0) mostrarPasso(indice - 1);
    }

    /* ======================================================================
       7. POSICIONAMENTO — moldura e cartão
       ====================================================================== */
    function agendarReposicionamento() {
        cancelAnimationFrame(quadro);
        quadro = requestAnimationFrame(posicionar);
    }

    function limitar(valor, min, max) {
        return Math.max(min, Math.min(valor, max));
    }

    function posicionar() {
        if (!ativo) return;
        const passo = passos[indice];
        const vw = window.innerWidth;
        const vh = window.innerHeight;
        const pw = el.popover.offsetWidth;
        const ph = el.popover.offsetHeight;
        let topo, esquerda;

        if (!passo.alvo || !visivel(passo.alvo)) {
            // Passo sem alvo: tudo escurecido e cartão centralizado.
            el.destaque.classList.add("abaguia-destaque--centro");
            Object.assign(el.destaque.style, { top: "50%", left: "50%", width: "0px", height: "0px" });
            topo = (vh - ph) / 2;
            esquerda = (vw - pw) / 2;
        } else {
            const r = passo.alvo.getBoundingClientRect();
            el.destaque.classList.remove("abaguia-destaque--centro");
            Object.assign(el.destaque.style, {
                top: (r.top - RESPIRO) + "px",
                left: (r.left - RESPIRO) + "px",
                width: (r.width + RESPIRO * 2) + "px",
                height: (r.height + RESPIRO * 2) + "px"
            });

            const centroX = r.left + r.width / 2 - pw / 2;
            const centroY = r.top + r.height / 2 - ph / 2;
            // Ordem de preferência: abaixo, acima, à direita, à esquerda.
            const abaixo = r.bottom + RESPIRO + FOLGA;
            const acima = r.top - RESPIRO - FOLGA - ph;
            const direita = r.right + RESPIRO + FOLGA;
            const esquerdaPos = r.left - RESPIRO - FOLGA - pw;

            if (abaixo + ph <= vh - MARGEM) {
                topo = abaixo; esquerda = centroX;
            } else if (acima >= MARGEM) {
                topo = acima; esquerda = centroX;
            } else if (direita + pw <= vw - MARGEM) {
                topo = centroY; esquerda = direita;
            } else if (esquerdaPos >= MARGEM) {
                topo = centroY; esquerda = esquerdaPos;
            } else {
                // Elemento muito grande: cartão fixo na parte de baixo da tela.
                topo = vh - ph - MARGEM; esquerda = centroX;
            }
        }

        el.popover.style.top = limitar(topo, MARGEM, Math.max(MARGEM, vh - ph - MARGEM)) + "px";
        el.popover.style.left = limitar(esquerda, MARGEM, Math.max(MARGEM, vw - pw - MARGEM)) + "px";
    }

    /* ======================================================================
       8. TECLADO e CLIQUES
       ====================================================================== */
    function aoTeclar(evento) {
        if (!ativo) return;

        if (evento.key === "Escape") {
            evento.preventDefault();
            encerrarTour();
        } else if (evento.key === "ArrowRight") {
            evento.preventDefault();
            proximo();
        } else if (evento.key === "ArrowLeft") {
            evento.preventDefault();
            anterior();
        } else if (evento.key === "Tab") {
            // Mantém o foco dentro do cartão enquanto o tour está aberto.
            const focaveis = Array.prototype.filter.call(
                el.popover.querySelectorAll("button, a[href]"),
                function (item) { return !item.disabled && !item.hidden && visivel(item); }
            );
            if (!focaveis.length) { evento.preventDefault(); return; }
            const primeiro = focaveis[0];
            const ultimo = focaveis[focaveis.length - 1];
            const atual = document.activeElement;
            if (evento.shiftKey && (atual === primeiro || atual === el.popover)) {
                evento.preventDefault(); ultimo.focus();
            } else if (!evento.shiftKey && atual === ultimo) {
                evento.preventDefault(); primeiro.focus();
            } else if (!el.popover.contains(atual)) {
                evento.preventDefault(); primeiro.focus();
            }
        }
    }

    // Um único listener para todos os botões do componente e gatilhos externos.
    document.addEventListener("click", function (evento) {
        const gatilhoExterno = evento.target.closest("[data-abaguia-iniciar]");
        if (gatilhoExterno) {
            evento.preventDefault();
            iniciarTour();
            return;
        }

        const botao = evento.target.closest("[data-abaguia-acao]");
        if (!botao || !el.raiz || !(el.raiz.contains(botao) || el.tour.contains(botao))) return;

        switch (botao.dataset.abaguiaAcao) {
            case "iniciar":   iniciarTour(); break;
            case "minimizar": minimizar(); break;
            case "abrir":     abrir(); break;
            case "proximo":   proximo(); break;
            case "voltar":    anterior(); break;
            case "pular":     encerrarTour(); break;
            case "bloqueio":  break; // clique fora do cartão: ignorado de propósito
        }
    });

    /* ======================================================================
       9. INICIALIZAÇÃO e API pública
       ====================================================================== */
    const pronto = montar();
    pronto.catch(function (erro) {
        console.warn("[AbaGuia] Não foi possível montar o guia:", erro.message);
    });

    window.AbaGuia = {
        iniciarTour: iniciarTour,
        encerrarTour: encerrarTour,
        abrir: function () { return pronto.then(abrir); },
        minimizar: function () { return pronto.then(minimizar); }
    };
})();
