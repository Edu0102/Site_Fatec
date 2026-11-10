// Um jeito só de chamar o backend. Inclua antes do script da página:
//   <script src="/js/api.js"></script>
// Uso: const pops = await api("GET", "/api/pops");
//      await api("POST", "/api/feedback", { description: "Texto", popId: 1 });
// Erros: lança Error com a mensagem do backend (data.error); 401 leva para o login.
async function api(method, url, body) {
    var options = { method: method, headers: {} };
    if (body !== undefined) {
        options.headers["Content-Type"] = "application/json";
        options.body = JSON.stringify(body);
    }
    var response = await fetch(url, options);
    var data = await response.json().catch(function () { return {}; });
    if (response.status === 401 && !location.pathname.endsWith("/login.html")) {
        window.location.href = "/login.html";
    }
    if (!response.ok) throw new Error(data.error || "Erro inesperado (" + response.status + ").");
    return data;
}
