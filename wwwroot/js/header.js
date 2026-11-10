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

fetch("/api/auth/me")
    .then(function (response) {
        if (!response.ok) throw new Error("Sessão não encontrada");
        return response.json();
    })
    .then(function (user) {
        var area = header.querySelector("#usuario-logado");
        area.textContent = user.name;
        var logout = document.createElement("button");
        if (user.role === "admin") {
            var register = document.createElement("a");
            register.className = "botao-cadastrar-usuario";
            register.href = "/html/cadastro.html";
            register.textContent = "Cadastrar usuário";
            area.append(" ", register);
        }
        logout.type = "button";
        logout.className = "botao-sair";
        logout.textContent = "Sair";
        logout.onclick = async function () {
            await fetch("/api/auth/logout", { method: "POST" });
            window.location.href = "/login.html";
        };
        area.append(" ", logout);
    })
    .catch(function () { window.location.href = "/login.html"; });
