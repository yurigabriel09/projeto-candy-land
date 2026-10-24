const API_URL = "http://127.0.0.1:5000/users";

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

export async function getUsers() {
    const response = await fetch(API_URL, { headers: authHeaders() });
    if (!response.ok) throw new Error("Consulta global de usuários não está disponível");
    const resultado = await response.json();
    return resultado.dados;
}

export async function getUser(id) {
    const response = await fetch(`${API_URL}/${id}`, { headers: authHeaders() });
    const resultado = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(resultado.erro || "Usuário não encontrado");
    return resultado.dados;
}

export async function createUser(dados) {
    const response = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(dados),
    });
    const resultado = await response.json();
    if (!response.ok) throw new Error(resultado.erro || "Erro ao criar usuário");
    return resultado.dados;
}

export async function updateUser(id, dados) {
    const response = await fetch(`${API_URL}/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify(dados),
    });
    const resultado = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(resultado.erro || "Erro ao atualizar usuário");
    return resultado.dados;
}

export async function deleteUser(id) {
    const response = await fetch(`${API_URL}/${id}`, {
        method: "DELETE",
        headers: authHeaders(),
    });
    const resultado = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(resultado.erro || "Erro ao deletar usuário");
    return true;
}
