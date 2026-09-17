import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getProductsByRestaurant } from "../services/productService";

const menuItems = [
    { label: "Produtos", active: true },
    { label: "Pedidos", active: false },
    { label: "Cardápio", active: false },
    { label: "Financeiro", active: false }
];

function BusinessHome() {
    const navigate = useNavigate();
    const restauranteId = Number(localStorage.getItem("contaId"));

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
    }, [restauranteId]);

    function handleLogout() {
        localStorage.removeItem("tipoConta");
        localStorage.removeItem("contaId");
        navigate("/login");
    }

    return (
        <div className="dashboard-layout">
            <aside className="dashboard-sidebar">
                <h1 className="dashboard-logo">CandyLand</h1>

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
                    <div className="dashboard-body-top">
                        <button
                            type="button"
                            className="primary-button dashboard-cta"
                            onClick={() => navigate("/business/products/new")}
                        >
                            + Cadastrar produto
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
                                <div key={produto.id} className="product-card">
                                    <h3>{produto.nome}</h3>
                                    <p className="product-price">R$ {Number(produto.preco).toFixed(2)}</p>
                                    <span className={produto.disponivel ? "badge badge-available" : "badge badge-unavailable"}>
                                        {produto.disponivel ? "Disponível" : "Indisponível"}
                                    </span>
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