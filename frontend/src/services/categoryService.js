const API_URL = "http://127.0.0.1:5000/categorias";

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

export async function getCategories() {
    const response = await fetch(API_URL, { headers: { ...authHeaders() } });
    const resultado = await response.json();
    if (!response.ok) throw new Error(resultado.erro || "Erro ao buscar categorias");
    return resultado.categorias;
}

export async function createCategory(nome) {
    const response = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify({ nome }),
    });
    const resultado = await response.json();
    if (!response.ok) throw new Error(resultado.erro || "Erro ao criar categoria");
    return resultado.categoria;
}

export async function updateCategory(id, dados) {
    const response = await fetch(`${API_URL}/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify(dados),
    });
    const resultado = await response.json();
    if (!response.ok) throw new Error(resultado.erro || "Erro ao atualizar categoria");
    return resultado.categoria;
}

export async function deleteCategory(id) {
    const response = await fetch(`${API_URL}/${id}`, { method: "DELETE", headers: { ...authHeaders() } });
    if (!response.ok) {
        const resultado = await response.json().catch(() => ({}));
        throw new Error(resultado.erro || "Erro ao remover categoria");
    }
    return true;
}