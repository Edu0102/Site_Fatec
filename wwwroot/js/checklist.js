/* Checklist Pessoal — JavaScript limpo e otimizado */
"use strict";

const CHAVE = "frcont-checklist-v1";
const tarefasIniciais = [
  { id: 1, texto: "Conferir e-mails e solicitações recebidas", concluida: false },
  { id: 2, texto: "Verificar prazos e atividades do dia", concluida: false },
  { id: 3, texto: "Atualizar os registros dos serviços em andamento", concluida: false },
  { id: 4, texto: "Conferir documentos antes de finalizar o atendimento", concluida: false }
];

// TODO banco: trocar pela chave (id) do usuário logado
const MINHA_CHAVE = "funcionario";
const funcionarioConsulta = document.getElementById("funcionario-consulta");
const formTarefa = document.getElementById("form-tarefa");
const campoTarefa = document.getElementById("nova-tarefa");
const listaTarefas = document.getElementById("lista-tarefas");
const listaVazia = document.getElementById("lista-vazia");
const mensagemForm = document.getElementById("mensagem-form");

function carregarDados() {
  try {
    return JSON.parse(localStorage.getItem(CHAVE)) || {};
  } catch (erro) {
    return {};
  }
}

let dados = carregarDados();

// O adm está consultando outro funcionário (só leitura)?
function consultando() {
  return !!(funcionarioConsulta && funcionarioConsulta.value);
}

function chaveFuncionario() {
  return consultando() ? funcionarioConsulta.value : MINHA_CHAVE;
}

function tarefasDoFuncionario() {
  const chave = chaveFuncionario();
  if (!Array.isArray(dados[chave])) {
    dados[chave] = chave === MINHA_CHAVE ? tarefasIniciais.map(t => ({ ...t })) : [];
  }
  return dados[chave];
}

function salvarDados() {
  try {
    localStorage.setItem(CHAVE, JSON.stringify(dados));
  } catch (erro) {
    console.error("Não foi possível salvar no localStorage", erro);
  }
}

function atualizarResumo(tarefas) {
  const total = tarefas.length;
  const concluidas = tarefas.filter(t => t.concluida).length;
  const pendentes = total - concluidas;
  const percentual = total ? Math.round(concluidas / total * 100) : 0;

  document.getElementById("total-tarefas").textContent = total;
  document.getElementById("tarefas-concluidas").textContent = concluidas;
  document.getElementById("tarefas-pendentes").textContent = pendentes;
  document.getElementById("percentual").textContent = percentual + "%";
  document.getElementById("total-tarefas").classList.add("dado-js");
  document.getElementById("tarefas-concluidas").classList.add("dado-js");
  document.getElementById("tarefas-pendentes").classList.add("dado-js");
  document.getElementById("percentual").classList.add("dado-js");
  document.getElementById("barra-preenchida").style.width = percentual + "%";
  document.getElementById("barra-progresso").setAttribute("aria-valuenow", percentual);
  
  document.getElementById("texto-progresso").textContent =
    total === 0 ? "Adicione tarefas para acompanhar seu progresso." :
    concluidas === total ? "Todas as tarefas foram concluídas. Bom trabalho!" :
    `${concluidas} de ${total} tarefas concluídas; faltam ${pendentes}.`;
    
  const btnDesmarcar = document.getElementById("desmarcar-todas");
  if (btnDesmarcar) {
    btnDesmarcar.disabled = concluidas === 0 || consultando();
  }
}

function renderizar() {
  const tarefas = tarefasDoFuncionario();
  const adminVisualizando = consultando();
  
  document.getElementById("titulo-lista").textContent = adminVisualizando
    ? "Checklist de " + funcionarioConsulta.options[funcionarioConsulta.selectedIndex].text
    : "Minhas tarefas";
    
  document.getElementById("subtitulo-lista").textContent = adminVisualizando
    ? "Modo de consulta: o administrador não altera as tarefas."
    : "Marque os itens conforme concluir.";
    
  campoTarefa.disabled = adminVisualizando;
  formTarefa.querySelector("button").disabled = adminVisualizando;
  listaTarefas.innerHTML = "";

  tarefas.forEach(tarefa => {
    const item = document.createElement("li");
    item.className = "task-item dado-js" + (tarefa.concluida ? " done" : "");

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.className = "task-check";
    checkbox.checked = tarefa.concluida;
    checkbox.disabled = adminVisualizando;
    checkbox.setAttribute("aria-label", "Concluir: " + tarefa.texto);
    checkbox.addEventListener("change", () => {
      tarefa.concluida = checkbox.checked;
      salvarDados();
      renderizar();
    });

    const nome = document.createElement("span");
    nome.className = "task-name";
    nome.textContent = tarefa.texto;

    const status = document.createElement("span");
    status.className = "status " + (tarefa.concluida ? "done" : "pending");
    status.textContent = tarefa.concluida ? "Concluída" : "Pendente";

    item.append(checkbox, nome, status);

    if (!adminVisualizando) {
      const remover = document.createElement("button");
      remover.type = "button";
      remover.className = "remove-task";
      remover.textContent = "×";
      remover.setAttribute("aria-label", "Remover tarefa");
      remover.title = "Remover tarefa";
      remover.addEventListener("click", () => {
        dados[chaveFuncionario()] = tarefasDoFuncionario().filter(t => t.id !== tarefa.id);
        salvarDados();
        renderizar();
      });
      item.append(remover);
    }

    listaTarefas.appendChild(item);
  });

  listaVazia.hidden = tarefas.length !== 0;
  atualizarResumo(tarefas);
}

formTarefa.addEventListener("submit", evento => {
  evento.preventDefault();
  if (consultando()) return;

  const texto = campoTarefa.value.trim().replace(/\s+/g, " ");
  if (!texto) {
    mensagemForm.textContent = "Digite uma descrição para a tarefa.";
    campoTarefa.focus();
    return;
  }

  mensagemForm.textContent = "";
  const tarefas = tarefasDoFuncionario();
  tarefas.push({ id: Date.now(), texto, concluida: false });
  campoTarefa.value = "";
  salvarDados();
  renderizar();
  campoTarefa.focus();
});

campoTarefa.addEventListener("input", () => { mensagemForm.textContent = ""; });

if (funcionarioConsulta) {
  funcionarioConsulta.addEventListener("change", () => {
    mensagemForm.textContent = "";
    renderizar();
  });
}

const btnDesmarcarTodas = document.getElementById("desmarcar-todas");
if (btnDesmarcarTodas) {
  btnDesmarcarTodas.addEventListener("click", () => {
    if (consultando()) return;
    tarefasDoFuncionario().forEach(t => { t.concluida = false; });
    salvarDados();
    renderizar();
  });
}

window.addEventListener("storage", evento => {
  if (evento.key === CHAVE) {
    dados = carregarDados();
    renderizar();
  }
});

renderizar();
