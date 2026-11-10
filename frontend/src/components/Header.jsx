import { useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useCart } from "../context/CartContext";
import usePendingOrdersCount from "../hooks/usePendingOrdersCount";

/**
 * Cabeçalho usado na Home pública, na Home do cliente logado e na consulta
 * de itens. As telas de login/cadastro continuam com o card centralizado
 * sem cabeçalho, como já estava.
 */
function Header() {
    const { dadosAutenticacao, autenticado, sair } = useAuth();
    const { quantidadeTotal } = useCart();
    const [contaAberta, setContaAberta] = useState(false);
    const logado =
        autenticado && dadosAutenticacao?.tipo_conta === "PERSONAL";
    const pagamentosPendentes = usePendingOrdersCount(Boolean(logado));

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

                    {logado && (
                        <Link to="/cart" className="cart-link">
                            🛒 Carrinho
                            {quantidadeTotal > 0 && (
                                <span className="cart-badge">{quantidadeTotal}</span>
                            )}
                        </Link>
                    )}

                    {logado ? (
                        <>
                            {primeiroNome && (
                                <span className="site-saudacao">
                                    Olá, {primeiroNome}
                                </span>
                            )}

                            <div className="site-account-menu">
                                <button
                                    type="button"
                                    className="site-account-trigger"
                                    aria-expanded={contaAberta}
                                    aria-haspopup="true"
                                    onClick={() => setContaAberta((aberta) => !aberta)}
                                >
                                    Minha conta
                                    {pagamentosPendentes > 0 && (
                                        <span className="cart-badge" aria-label={`${pagamentosPendentes} pedidos aguardando pagamento`}>
                                            {pagamentosPendentes}
                                        </span>
                                    )}
                                </button>
                                {contaAberta && (
                                    <div className="site-account-dropdown" role="menu">
                                        <Link role="menuitem" to="/minha-conta/dados-pessoais" onClick={() => setContaAberta(false)}>Dados pessoais</Link>
                                        <Link role="menuitem" to="/minha-conta/historico-compras" onClick={() => setContaAberta(false)}>Histórico de compras</Link>
                                        <Link role="menuitem" to="/minha-conta/pagamentos-pendentes" onClick={() => setContaAberta(false)}>
                                            <span>Pedidos e pagamentos pendentes</span>
                                            {pagamentosPendentes > 0 && <span className="cart-badge">{pagamentosPendentes}</span>}
                                        </Link>
                                    </div>
                                )}
                            </div>
                            <button onClick={handleSair} className="btn-contorno">
                                Sair
                            </button>
                        </>
                    ) : (
                        <>
                            <Link to="/login" className="btn-contorno">
                                Entrar
                            </Link>
                            <Link to="/register" className="btn-principal">
                                Cadastrar
                            </Link>
                        </>
                    )}
                </nav>
            </div>
        </header>
    );
}

export default Header;