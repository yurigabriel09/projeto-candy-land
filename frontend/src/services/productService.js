const API_URL = "http://127.0.0.1:5000/produtos";

export async function getProducts() {
  const response = await fetch(API_URL);
  const resultado = await response.json();
  if (!response.ok) throw new Error(resultado.erro || "Erro ao buscar produtos");
  return resultado.dados;
}

export async function getProduct(id) {
  const response = await fetch(`${API_URL}/${id}`);
  const resultado = await response.json();
  if (!response.ok) throw new Error(resultado.erro || "Produto não encontrado");
  return resultado.dados;
}