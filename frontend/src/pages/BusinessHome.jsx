import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { getProductsByRestaurant } from "../services/productService";

const menuItems = [
    { label: "Produtos", active: true },
    { label: "Pedidos", active: false },
    { label: "Cardápio", active: false },
    { label: "Financeiro", active: false }
];

function BusinessHome() {
    const navigate = useNavigate();
    const { dadosAutenticacao, autenticado, sair } = useAuth();
    const restauranteId = Number(dadosAutenticacao?.id);

    const [produtos, setProdutos] = useState([]);
    const [loading, setLoading] = useState(true);
    const [erro, setErro] = useState("");

    useEffect(() => {
        async function carregarProdutos() {
            try {
                const dados = await getProductsByRestaurant(restauranteId);
                setProdutos(dados);
            } catch (error) {
                setErro("Não foi possível carregar os produtos.");
            } finally {
                setLoading(false);
            }
        }

        carregarProdutos();
    }, [autenticado, dadosAutenticacao?.tipo_conta, navigate, restauranteId]);

    function handleLogout() {
        // Limpa a sessão e força a navegação para a área pública.
        window.localStorage.removeItem("candyland_auth");
        sair();
        window.location.replace("/");
    }

    return (
        <div className="dashboard-layout">
            <aside className="dashboard-sidebar">
                <Link to="/business" className="dashboard-logo dashboard-logo-link">
                    CandyLand
                </Link>

                <nav className="dashboard-nav">
                    {menuItems.map((item) => (
                        <button
                            key={item.label}
                            type="button"
                            className={item.active ? "dashboard-nav-item active" : "dashboard-nav-item"}
                        >
                            {item.label}
                        </button>
                    ))}
                </nav>

                <button type="button" className="dashboard-nav-item dashboard-logout" onClick={handleLogout}>
                    Sair
                </button>
            </aside>

            <div className="dashboard-content">
                <header className="dashboard-header">
                    <h2>Seu cardápio</h2>

                    <div className="dashboard-header-actions">
                        <button type="button" className="icon-button" title="Configurações">⚙</button>
                        <button type="button" className="icon-button" title="Minha conta">👤</button>
                    </div>
                </header>

                <main className="dashboard-body">

                    <div className="dashboard-body-top" style={{ display: "flex", gap: 12 }}>
                        <button type="button" className="primary-button dashboard-cta" onClick={() => navigate("/business/products/new")}>
                            + Cadastrar produto
                        </button>

                        <button type="button" className="auth-back" style={{ width: "auto", marginTop: 0, padding: "0 24px" }} onClick={() => navigate("/business/categories")}>
                            Gerenciar categorias
                        </button>
                    </div>

                    {loading && <p>Carregando produtos...</p>}
                    {erro && <p className="field-error">{erro}</p>}

                    {!loading && !erro && produtos.length === 0 && (
                        <div className="empty-state">
                            <p>Você ainda não cadastrou nenhum produto.</p>
                            <p>Use o botão acima para adicionar o primeiro item do seu cardápio.</p>
                        </div>
                    )}

                    {!loading && produtos.length > 0 && (
                        <div className="product-grid">
                            {produtos.map((produto) => (
                                <div key={produto.id_produto} className="product-card">
                                    <h3>{produto.nome_produto}</h3>
                                    <p className="product-price">R$ {Number(produto.preco_produto).toFixed(2)}</p>
                                    <span className={produto.produto_disponivel ? "badge badge-available" : "badge badge-unavailable"}>
                                        {produto.produto_disponivel ? "Disponível" : "Indisponível"}
                                    </span>

                                    <button
                                        type="button"
                                        className="product-edit-button"
                                        onClick={() => navigate(`/business/products/${produto.id_produto}/edit`)}
                                    >
                                        Editar
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}                    
                </main>
            </div>
        </div>
    );
}

export default BusinessHome;