const API_URL = "http://127.0.0.1:5000/restaurantes";

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