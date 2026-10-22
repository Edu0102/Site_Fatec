document.getElementById("formCadastro").onsubmit = async function (event) {
    event.preventDefault();

    var name = document.getElementById("nome").value.trim();
    var email = document.getElementById("email").value.trim();
    var password = document.getElementById("senha").value;
    var confirmation = document.getElementById("confirmar").value;
    var message = document.getElementById("mensagem");

    if (password !== confirmation) {
        message.style.color = "#d93025";
        message.textContent = "As senhas não são iguais.";
        return;
    }

    message.style.color = "#555";
    message.textContent = "Criando usuário...";
    try {
        var response = await fetch("/api/users", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name: name, email: email, password: password })
        });
        var data = await response.json().catch(function () { return {}; });
        if (!response.ok) throw new Error(data.message || "Não foi possível criar o usuário.");
        message.style.color = "#188038";
        message.textContent = "Usuário cadastrado com sucesso.";
        event.target.reset();
    } catch (error) {
        message.style.color = "#d93025";
        message.textContent = error.message;
    }
};
