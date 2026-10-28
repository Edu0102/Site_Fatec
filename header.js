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

/*
fetch("/api/auth/me")
    .then(function (response) {
        if (!response.ok) throw new Error("Sessão não encontrada");
        return response.json();
    })
    .then(function (user) {
        definirUsuario({ nome: user.name });
    })
    .catch(function () { window.location.href = "/login.html"; });

var sair = document.getElementById("menu-sair");
if (sair) {
    sair.addEventListener("click", async function (evento) {
        evento.preventDefault();
        await fetch("/api/auth/logout", { method: "POST" });
        window.location.href = "/login.html";
    });
}
*/
