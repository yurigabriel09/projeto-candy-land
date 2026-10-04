const API_URL = "http://127.0.0.1:5000/restaurantes";

// Função já existente — usada pelo BusinessRegister.jsx. Não foi alterada.
export async function createRestaurant(dados) {
  const response = await fetch(API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(dados),
  });

  const resultado = await response.json();

  if (!response.ok) throw new Error(resultado.erro || "Erro ao criar empresa");

  return resultado.dados;
}

// Funções novas — necessárias para a Home e a tela de consulta de itens
// mostrarem as lojas cadastradas de verdade.
export async function getRestaurants() {
  const response = await fetch(API_URL);
  const resultado = await response.json();
  if (!response.ok) throw new Error(resultado.erro || "Erro ao buscar lojas");
  return resultado.dados;
}

export async function getRestaurant(id) {
  const response = await fetch(`${API_URL}/${id}`);
  const resultado = await response.json();
  if (!response.ok) throw new Error(resultado.erro || "Loja não encontrada");
  return resultado.dados;
}
export async function getRestaurantProducts(id) {
  const response = await fetch(`${API_URL}/${id}/produtos`);
  const resultado = await response.json();
  if (!response.ok) throw new Error(resultado.erro || "Erro ao buscar produtos do restaurante");
  return resultado.dados;
}
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

export async function getRestaurantConfiguration(id) {
  const response = await fetch(`${API_URL}/${id}/configuracao`, {
    headers: authHeaders(),
  });
  const resultado = await response.json();
  if (!response.ok) {
    throw new Error(resultado.erro || "Erro ao carregar configuração do restaurante");
  }
  return resultado.dados;
}

export async function updateRestaurantConfiguration(id, dados) {
  const response = await fetch(`${API_URL}/${id}/configuracao`, {
    method: "PUT",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(dados),
  });
  const resultado = await response.json();
  if (!response.ok) {
    throw new Error(resultado.erro || "Erro ao atualizar configuração do restaurante");
  }
  return resultado.dados;
}

