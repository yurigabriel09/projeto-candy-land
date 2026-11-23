import { API_BASE_URL } from "./apiConfig";

function getToken() {
    try {
        const raw = localStorage.getItem("candyland_auth");
        return raw ? JSON.parse(raw).token : null;
    } catch {
        return null;
    }
}

async function buscarRelatorio(caminho, mensagemPadrao) {
    const token = getToken();
    const response = await fetch(`${API_BASE_URL}/relatorios/${caminho}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        cache: "no-store",
    });
    const resultado = await response.json().catch(() => ({}));
    if (!response.ok) {
        const erro = new Error(resultado.erro || mensagemPadrao);
        erro.status = response.status;
        throw erro;
    }
    return resultado.relatorio;
}

export function getRelatorioLoja() {
    return buscarRelatorio("loja", "Não foi possível carregar o relatório da loja.");
}

export function getRelatorioAdmin() {
    return buscarRelatorio("admin", "Não foi possível carregar o relatório administrativo.");
}

export function getRelatorioCliente() {
    return buscarRelatorio("cliente", "Não foi possível carregar o relatório do cliente.");
}
