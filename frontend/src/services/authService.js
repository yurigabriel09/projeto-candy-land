import { getUser } from "./userService";
import { getRestaurant } from "./restaurantService";

const CHAVE = "candyland:sessao";

/** Chamado logo após o código ser validado com sucesso. */
export async function iniciarSessao(tipoConta, id) {
  const conta =
    tipoConta === "PERSONAL" ? await getUser(id) : await getRestaurant(id);

  const sessao = { tipo: tipoConta, ...conta };
  localStorage.setItem(CHAVE, JSON.stringify(sessao));
  return sessao;
}

/** Retorna a sessão atual, ou null se ninguém entrou. */
export function getSessao() {
  const salvo = localStorage.getItem(CHAVE);
  if (!salvo) return null;

  try {
    return JSON.parse(salvo);
  } catch {
    localStorage.removeItem(CHAVE);
    return null;
  }
}

export function encerrarSessao() {
  localStorage.removeItem(CHAVE);
}