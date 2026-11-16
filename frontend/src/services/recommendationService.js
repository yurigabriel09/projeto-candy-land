const API_BASE = (import.meta.env.VITE_API_URL || "http://127.0.0.1:5000").replace(/\/+$/, "");

function getToken() {
    try {
        const raw = localStorage.getItem("candyland_auth");
        return raw ? JSON.parse(raw).token : null;
    } catch {
        return null;
    }
}

// Busca produtos recomendados a partir de um item selecionado ou de todo o carrinho.
// produtoIds: array de ids de produto. Retorna a lista de produtos recomendados.
export async function getProductRecommendations(produtoIds, limite = 8, signal) {
    const ids = [...new Set((produtoIds || []).map(Number).filter((n) => Number.isInteger(n) && n > 0))];
    if (ids.length === 0) return [];

    const params = new URLSearchParams();
    ids.forEach((id) => params.append("produto_id", String(id)));
    params.set("limite", String(limite));

    const token = getToken();
    const response = await fetch(`${API_BASE}/produtos/recomendacoes?${params.toString()}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        signal,
    });
    const resultado = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(resultado.erro || "Não foi possível carregar as sugestões.");
    return resultado.recomendacoes || [];
}