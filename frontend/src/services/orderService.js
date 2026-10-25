const API_BASE = "http://127.0.0.1:5000";

function getToken() {
    try {
        const raw = localStorage.getItem("candyland_auth");
        return raw ? JSON.parse(raw).token : null;
    } catch {
        return null;
    }
}

function authHeaders() {
    const token = getToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
}

async function lerResposta(response, mensagemPadrao) {
    const resultado = await response.json().catch(() => ({}));
    if (!response.ok) {
        throw new Error(resultado.erro || mensagemPadrao);
    }
    return resultado;
}

export async function getCustomerAddresses(userId) {
    const response = await fetch(`${API_BASE}/users/${encodeURIComponent(userId)}/enderecos`, {
        headers: authHeaders(),
    });
    const resultado = await lerResposta(response, "Não foi possível carregar seus endereços.");
    return resultado.dados || [];
}

export async function createOrder(dados) {
    const response = await fetch(`${API_BASE}/pedidos`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            ...authHeaders(),
        },
        body: JSON.stringify(dados),
    });
    const resultado = await lerResposta(response, "Não foi possível criar o pedido.");
    return resultado.pedido;
}
