import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

/**
 * Cabeçalho usado na Home pública, na Home do cliente logado e na consulta
 * de itens. As telas de login/cadastro continuam com o card centralizado
 * sem cabeçalho, como já estava.
 */
function Header() {
    const { dadosAutenticacao, autenticado, sair } = useAuth();
    const logado =
        autenticado && dadosAutenticacao?.tipo_conta === "PERSONAL";

    function handleSair() {
        // Limpa a sessão e força a navegação completa para a área pública.
        // Isso evita que o ProtectedRoute faça um redirect intermediário para /login.
        sair();
        window.location.replace("/");
    }

    const primeiroNome =
        dadosAutenticacao?.nome_completo?.trim().split(/\s+/)[0] || "";

    return (
        <header className="site-header">
            <div className="site-header-inner">
                <Link to={logado ? "/home" : "/"} className="site-logo">
                    <span className="site-logo-icone">🍭</span>
                    <span className="site-logo-texto">Candyland</span>
                </Link>

                <nav className="site-nav">
                    <Link to="/itens">Doces</Link>

                    {logado ? (
                        <>
                            {primeiroNome && (
                                <span className="site-saudacao">
                                    Olá, {primeiroNome}
                                </span>
                            )}
                            <button onClick={handleSair} className="btn-contorno">
                                Sair
                            </button>
                        </>
                    ) : (
                        <Link to="/login" className="btn-contorno">
                            Entrar
                        </Link>
                    )}
                </nav>
            </div>
        </header>
    );
}

export default Header;