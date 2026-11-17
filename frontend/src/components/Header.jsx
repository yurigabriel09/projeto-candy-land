import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useCart } from "../context/CartContext";
import usePendingOrdersCount from "../hooks/usePendingOrdersCount";
import { getCustomerAddresses } from "../services/orderService";

/**
 * Cabeçalho usado na Home pública, na Home do cliente logado e na consulta
 * de itens. As telas de login/cadastro continuam com o card centralizado
 * sem cabeçalho, como já estava.
 *
 * Logado: logo + busca + endereço + carrinho + avatar (layout do protótipo).
 * Não logado: logo + Seja Parceiro / Entrar / Cadastrar.
 */
function Header({ variant = "default" }) {
    const { dadosAutenticacao, autenticado, sair } = useAuth();
    const { quantidadeTotal } = useCart();
    const navigate = useNavigate();
    const [contaAberta, setContaAberta] = useState(false);
    const [termoBusca, setTermoBusca] = useState("");
    const [enderecoTexto, setEnderecoTexto] = useState("");
    const logado =
        autenticado && dadosAutenticacao?.tipo_conta === "PERSONAL";
    const pagamentosPendentes = usePendingOrdersCount(Boolean(logado));

    // Endereço principal do cliente, mostrado ao lado da busca.
    useEffect(() => {
        if (!logado) return undefined;
        let cancelado = false;

        async function carregarEndereco() {
            try {
                const lista = await getCustomerAddresses();
                if (cancelado || !Array.isArray(lista)) return;
                const principal = lista.find((e) => e.principal) || lista[0];
                if (principal) {
                    setEnderecoTexto(
                        [principal.rua, principal.numero].filter(Boolean).join(", ")
                    );
                }
            } catch {
                // sem endereço no cabeçalho não atrapalha o uso da tela
            }
        }

        carregarEndereco();
        return () => {
            cancelado = true;
        };
    }, [logado]);

    function handleSair() {
        // Limpa a sessão e força a navegação completa para a área pública.
        // Isso evita que o ProtectedRoute faça um redirect intermediário para /login.
        sair();
        window.location.replace("/");
    }

    function handleBuscar(event) {
        event.preventDefault();
        const termo = termoBusca.trim();
        navigate(termo ? `/itens?busca=${encodeURIComponent(termo)}` : "/itens");
    }

    const primeiroNome =
        dadosAutenticacao?.nome_completo?.trim().split(/\s+/)[0] || "";
    const inicial = (primeiroNome[0] || "C").toUpperCase();

    return (
        <header className={`site-header${logado ? " site-header-logado" : ""}`}>
            <div className="site-header-inner">
                <Link to={logado ? "/home" : "/"} className="site-logo">
                    <span className="site-logo-icone">🍭</span>
                    <span className="site-logo-texto">Candyland</span>
                </Link>

                {logado && (
                    <form className="hd-busca" onSubmit={handleBuscar} role="search">
                        <span className="hd-busca-icone" aria-hidden="true">🔍</span>
                        <input
                            type="search"
                            value={termoBusca}
                            onChange={(event) => setTermoBusca(event.target.value)}
                            placeholder="Busque por item ou loja"
                            aria-label="Buscar item ou loja"
                        />
                    </form>
                )}

                <nav className="site-nav">
                    {!logado && (
                        <Link to={variant === "landing" ? "/itens" : "/parceiros"}>
                            {variant === "landing" ? "Seja Cliente" : "Seja Parceiro"}
                        </Link>
                    )}

                    {logado ? (
                        <>
                            {enderecoTexto && (
                                <Link
                                    to="/minha-conta/dados-pessoais"
                                    className="hd-endereco"
                                    title="Alterar endereço"
                                >
                                    <span aria-hidden="true">📍</span>
                                    <span className="hd-endereco-texto">{enderecoTexto}</span>
                                </Link>
                            )}

                            <Link
                                to="/cart"
                                className="hd-carrinho"
                                aria-label={`Carrinho, ${quantidadeTotal} itens`}
                            >
                                🛒
                                {quantidadeTotal > 0 && (
                                    <span className="hd-carrinho-badge">{quantidadeTotal}</span>
                                )}
                            </Link>

                            <div className="site-account-menu">
                                <button
                                    type="button"
                                    className="hd-avatar"
                                    aria-expanded={contaAberta}
                                    aria-haspopup="true"
                                    aria-label="Minha conta"
                                    onClick={() => setContaAberta((aberta) => !aberta)}
                                >
                                    {inicial}
                                    {pagamentosPendentes > 0 && (
                                        <span
                                            className="hd-avatar-badge"
                                            aria-label={`${pagamentosPendentes} pedidos aguardando pagamento`}
                                        >
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
                                        <button
                                            type="button"
                                            role="menuitem"
                                            className="hd-sair"
                                            onClick={handleSair}
                                        >
                                            Sair
                                        </button>
                                    </div>
                                )}
                            </div>
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