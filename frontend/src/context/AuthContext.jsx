import { createContext, useContext, useState } from "react";

const AuthContext = createContext(null);

function AuthProvider({ children }) {
    const [dadosAutenticacao, setDadosAutenticacao] = useState(() => {
        const dadosSalvos = localStorage.getItem("candyland_auth");
        return dadosSalvos ? JSON.parse(dadosSalvos) : null;
    });

    function entrar(dados) {
        setDadosAutenticacao(dados);
        localStorage.setItem("candyland_auth", JSON.stringify(dados));
    }

    function sair() {
        setDadosAutenticacao(null);
        localStorage.removeItem("candyland_auth");
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