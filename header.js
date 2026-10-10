
const header = document.createElement("header");

header.className = "header-padrao";

header.innerHTML = `
    <div class="header-logo">
        <div class="logo-circulo">LOGO</div>
        <span>F.R.Cont<br>(logo)</span>
    </div>

    <h1></h1>

    <div class="header-funcionario">
        *Nome Funcionario
    </div>
`;

header.querySelector("h1").textContent = document.title;

document.body.prepend(header);
