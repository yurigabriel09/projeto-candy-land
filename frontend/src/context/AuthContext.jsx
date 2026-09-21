import { createContext, useContext, useState } from "react";

const AuthContext = createContext(null);
const AUTH_STORAGE_KEY = "candyland_auth";

function carregarSessaoInicial() {
    const dadosSalvos = localStorage.getItem(AUTH_STORAGE_KEY);

    if (!dadosSalvos) {
        return null;
    }

    try {
        const dados = JSON.parse(dadosSalvos);
        return dados?.token ? dados : null;
    } catch {
        localStorage.removeItem(AUTH_STORAGE_KEY);
        return null;
    }
}

function AuthProvider({ children }) {
    const [dadosAutenticacao, setDadosAutenticacao] = useState(
        carregarSessaoInicial
    );

    function limparSessaoLegada() {
        localStorage.removeItem("candyland:sessao");
        localStorage.removeItem("tipoConta");
        localStorage.removeItem("contaId");
    }

    function entrar(dados) {
        if (!dados?.token) {
            return;
        }

        limparSessaoLegada();
        setDadosAutenticacao(dados);
        localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(dados));
    }

    function sair() {
        setDadosAutenticacao(null);
        localStorage.removeItem(AUTH_STORAGE_KEY);
        limparSessaoLegada();
    }

    const autenticado = Boolean(dadosAutenticacao?.token);

    return (
        <AuthContext.Provider
            value={{
                dadosAutenticacao,
                autenticado,
                entrar,
                sair
            }}
        >
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    return useContext(AuthContext);
}

export default AuthProvider;
