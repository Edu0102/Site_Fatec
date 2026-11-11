/*
 * header.js — dados do funcionário no header.
 *
 * O header agora é HTML fixo em cada página (não é mais criado aqui).
 * Este arquivo só preenche o nome e a foto:
 *
 *   definirUsuario({ nome: "Maria Silva", foto: "https://..." });
 *
 * O menu, o modal da foto e o tema escuro ficam em menu-usuario.js.
 */
window.definirUsuario = function (usuario) {
    usuario = usuario || {};

    var nome = document.getElementById("usuario-nome");
    if (nome && usuario.nome) nome.textContent = usuario.nome;

    if (usuario.foto && window.definirFotoUsuario) {
        window.definirFotoUsuario(usuario.foto);
    }
};

// Quem está logado (api.js leva para o login se a sessão acabou). Outros scripts usam: window.usuario.then(...)
window.usuario = api("GET", "/api/auth/me");

window.usuario.then(function (user) {
    document.documentElement.dataset.papel = user.role; // mostra itens [data-so-admin] para admin
    definirUsuario({ nome: user.name });
    // Sem foto o backend responde 404: só troca o ícone padrão se a imagem carregar
    var foto = new Image();
    foto.onload = function () { window.definirFotoUsuario(foto.src); };
    foto.src = "/api/users/" + user.id + "/photo?v=" + Date.now();
}).catch(function () {});

var sair = document.getElementById("menu-sair");
if (sair) {
    sair.addEventListener("click", function (evento) {
        evento.preventDefault();
        api("POST", "/api/auth/logout").catch(function () {}).then(function () {
            window.location.href = "/login.html";
        });
    });
}
