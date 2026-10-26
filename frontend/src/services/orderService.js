const API_BASE = (import.meta.env.VITE_API_URL || "http://127.0.0.1:5000").replace(/\/+$/, "");

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
    if (!response.ok) throw new Error(resultado.erro || mensagemPadrao);
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
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify(dados),
    });
    const resultado = await lerResposta(response, "Não foi possível criar o pedido.");
    return resultado.pedido;
}

export async function createPayment(orderId, idempotencyKey) {
    const key = idempotencyKey || `candyland-order-${orderId}-payment-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    const response = await fetch(`${API_BASE}/pedidos/${encodeURIComponent(orderId)}/pagamento`, {
        method: "POST",
        headers: {
            ...authHeaders(),
            // Uma chave por tentativa, permitindo recuperar uma tentativa no servidor
            // sem criar duplicatas por cliques/requisições concorrentes.
            "Idempotency-Key": key,
        },
    });
    const resultado = await lerResposta(response, "Não foi possível iniciar o pagamento no Mercado Pago.");
    return resultado.pagamento;
}

export async function getPayment(orderId) {
    const response = await fetch(`${API_BASE}/pedidos/${encodeURIComponent(orderId)}/pagamento`, {
        headers: authHeaders(),
        cache: "no-store",
    });
    const resultado = await lerResposta(response, "Não foi possível consultar o pagamento.");
    return resultado.pagamento;
}

export async function getOrder(orderId) {
    const response = await fetch(`${API_BASE}/pedidos/${encodeURIComponent(orderId)}`, {
        headers: authHeaders(),
        cache: "no-store",
    });
    const resultado = await lerResposta(response, "Não foi possível consultar o pedido.");
    return resultado.pedido;
}

export async function getOrders() {
    const response = await fetch(`${API_BASE}/pedidos`, {
        headers: authHeaders(),
        cache: "no-store",
    });
    const resultado = await lerResposta(response, "Não foi possível carregar os pedidos.");
    return resultado.pedidos || [];
}


export async function cancelOrder(orderId) {
    const response = await fetch(`${API_BASE}/pedidos/${encodeURIComponent(orderId)}/cancelar`, {
        method: "POST",
        headers: authHeaders(),
    });
    const resultado = await lerResposta(response, "Não foi possível cancelar o pedido.");
    return resultado;
}

export async function updateOrderStatus(orderId, status) {
    const response = await fetch(`${API_BASE}/pedidos/${encodeURIComponent(orderId)}/status`, {
        method: "PUT",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify({ status }),
    });
    const resultado = await lerResposta(response, "Não foi possível atualizar o status do pedido.");
    return resultado.pedido;
}
