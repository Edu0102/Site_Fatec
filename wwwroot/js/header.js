
const header = document.createElement("header");

header.className = "header-padrao";

header.innerHTML = `
    <div class="header-logo">
        <div class="logo-circulo">LOGO</div>
        <span>F.R.Cont<br>(logo)</span>
    </div>

    <h1></h1>

    <div class="header-funcionario dado-js" id="usuario-logado"></div>
`;

header.querySelector("h1").textContent = document.title;

document.body.prepend(header);

/*
fetch("/api/auth/me")
    .then(function (response) {
        if (!response.ok) throw new Error("Sessão não encontrada");
        return response.json();
    })
    .then(function (user) {
        var area = header.querySelector("#usuario-logado");
        area.textContent = user.name;
        var logout = document.createElement("button");
        if (user.isAdmin) {
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
*/
