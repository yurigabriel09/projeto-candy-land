const API_URL = "http://127.0.0.1:5000/users";

export async function getUsers() {
  const response = await fetch(API_URL);
  if (!response.ok) throw new Error("Erro ao buscar usuários");
  return response.json();
}

export async function getUser(id) {
  const response = await fetch(`${API_URL}/${id}`);
  if (!response.ok) throw new Error("Usuário não encontrado");
  return response.json();
}

export async function createUser(nome, email) {
  const response = await fetch(API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ nome, email }),
  });
  if (!response.ok) throw new Error("Erro ao criar usuário");
  return response.json();
}

export async function updateUser(id, nome, email) {
  const response = await fetch(`${API_URL}/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ nome, email }),
  });
  if (!response.ok) throw new Error("Erro ao atualizar usuário");
  return response.json();
}

export async function deleteUser(id) {
  const response = await fetch(`${API_URL}/${id}`, {
    method: "DELETE",
  });
  if (!response.ok) throw new Error("Erro ao deletar usuário");
  return true;
}