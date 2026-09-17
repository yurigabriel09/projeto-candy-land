const API_URL = "http://127.0.0.1:5000/produtos";

export async function getProducts() {
  const response = await fetch(API_URL);
  const resultado = await response.json();
  if (!response.ok) throw new Error(resultado.erro || "Erro ao buscar produtos");
  return resultado.dados;
}

export async function getProductsByRestaurant(restauranteId) {
  const produtos = await getProducts();
  return produtos.filter((p) => p.id_restaurante === restauranteId);
}

export async function getProduct(id) {
  const response = await fetch(`${API_URL}/${id}`);
  const resultado = await response.json();
  if (!response.ok) throw new Error(resultado.erro || "Produto não encontrado");
  return resultado.dados;
}

export async function createProduct(dados) {
  const response = await fetch(API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(dados),
  });
  const resultado = await response.json();
  if (!response.ok) throw new Error(resultado.erro || "Erro ao criar produto");
  return resultado.dados;
}

export async function updateProduct(id, dados) {
  const response = await fetch(`${API_URL}/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(dados),
  });
  const resultado = await response.json();
  if (!response.ok) throw new Error(resultado.erro || "Erro ao atualizar produto");
  return resultado.dados;
}