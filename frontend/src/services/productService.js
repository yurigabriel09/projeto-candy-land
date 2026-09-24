const API_URL = "http://127.0.0.1:5000/produtos";

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

export async function getProducts() {
    const response = await fetch(API_URL);
    if (!response.ok) throw new Error("Erro ao buscar produtos");
    const resultado = await response.json();
    return resultado.produtos;
}

export async function getProductsByRestaurant(restauranteId) {
    const produtos = await getProducts();
    return produtos.filter((p) => p.id_restaurante === restauranteId);
}

export async function getProduct(id) {
    const response = await fetch(`${API_URL}/${id}`);
    if (!response.ok) throw new Error("Produto não encontrado");
    const resultado = await response.json();
    return resultado.produto;
}

export async function createProduct(dados) {
    const response = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify(dados),
    });
    const resultado = await response.json();
    if (!response.ok) throw new Error(resultado.erro || "Erro ao criar produto");
    return resultado.produto;
}

export async function updateProduct(id, dados) {
    const response = await fetch(`${API_URL}/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify(dados),
    });
    const resultado = await response.json();  
    if (!response.ok) throw new Error(resultado.erro || "Erro ao atualizar produto");
    return resultado.produto;
}

export async function deleteProduct(id) {
    const response = await fetch(`${API_URL}/${id}`, {
        method: "DELETE",
        headers: { ...authHeaders() },
    });
    if (!response.ok) throw new Error("Erro ao remover produto");
    return true;
}