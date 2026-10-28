document.getElementById("formCadastro").onsubmit = async function (event) {
    event.preventDefault();

    var password = document.getElementById("senha").value;
    var confirmation = document.getElementById("confirmar").value;
    var message = document.getElementById("mensagem");

    if (password !== confirmation) {
        message.classList.remove("mensagem-sucesso");
        message.classList.add("mensagem-erro");
        message.textContent = "As senhas não são iguais.";
        return;
    }

    message.classList.remove("mensagem-sucesso");
    message.classList.add("mensagem-erro");
    message.textContent = "Cadastro indisponível: conexão com o servidor desativada.";

    /*
    try {
        var response = await fetch("/api/users", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                name: document.getElementById("nome").value.trim(),
                email: document.getElementById("email").value.trim(),
                password: password
            })
        });
        var data = await response.json().catch(function () { return {}; });
        if (!response.ok) throw new Error(data.message || "Não foi possível criar o usuário.");
        message.classList.remove("mensagem-erro");
        message.classList.add("mensagem-sucesso");
        message.textContent = "Usuário cadastrado com sucesso.";
        event.target.reset();
    } catch (error) {
        message.classList.remove("mensagem-sucesso");
        message.classList.add("mensagem-erro");
        message.textContent = error.message;
    }
    */
};
