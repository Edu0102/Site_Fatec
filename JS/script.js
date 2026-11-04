
const botaoMenu = document.getElementById("botaoMenu");
const menu = document.getElementById("menu");

botaoMenu.addEventListener("click", function () {

    menu.classList.toggle("ativo");

    const aberto = menu.classList.contains("ativo");

    botaoMenu.setAttribute("aria-expanded", aberto);

});

document.addEventListener("click", function (evento) {

    if (!evento.target.closest(".menu-container")) {

        menu.classList.remove("ativo");

        botaoMenu.setAttribute("aria-expanded", "false");

    }

});

document.addEventListener("keydown", function (evento) {

    if (evento.key === "Escape") {

        menu.classList.remove("ativo");

        botaoMenu.setAttribute("aria-expanded", "false");

        botaoMenu.focus();

    }

});
