import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { getRestaurant, getRestaurantProducts } from "../services/restaurantService";
import { deleteProduct } from "../services/productService";

const moeda = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });

const STATUS_LABEL = {
    EM_ANALISE: "Em análise",
    ABERTO: "Aberto",
    FECHADO: "Fechado",
    SUSPENSO: "Suspenso",
};

function BusinessHome() {
    const { dadosAutenticacao, sair } = useAuth();
    const [restaurante, setRestaurante] = useState(null);
    const [produtos, setProdutos] = useState([]);
    const [carregando, setCarregando] = useState(true);
    const [erro, setErro] = useState("");
    const [statusVisual, setStatusVisual] = useState(null);
    const navigate = useNavigate();

    useEffect(() => {
        carregarDados();
    }, []);

    async function carregarDados() {
        setCarregando(true);
        setErro("");
        try {
            const [loja, itens] = await Promise.all([
                getRestaurant(dadosAutenticacao.id),
                getRestaurantProducts(dadosAutenticacao.id),
            ]);
            setRestaurante(loja);
            setStatusVisual(loja.status);
            setProdutos(itens);
        } catch (error) {
            setErro(error.message || "Não foi possível carregar os dados da loja.");
        } finally {
            setCarregando(false);
        }
    }

    async function handleDeletar(id) {
        if (!confirm("Remover este produto do cardápio?")) return;
        try {
            await deleteProduct(id);
            setProdutos((atual) => atual.filter((p) => p.id_produto !== id));
        } catch (error) {
            alert(error.message || "Erro ao remover produto.");
        }
    }

    function handleSair() {
        sair();
        navigate("/");
    }

    const totalProdutos = produtos.length;
    const disponiveis = produtos.filter((p) => p.produto_disponivel).length;
    const indisponiveis = totalProdutos - disponiveis;
    const precoMedio =
        totalProdutos > 0
            ? produtos.reduce((soma, p) => soma + Number(p.preco_produto || 0), 0) / totalProdutos
            : 0;

    if (carregando) {
        return (
            <div className="dashboard-page">
                <p className="mensagem-carregando" role="status">Carregando painel...</p>
            </div>
        );
    }

    if (erro) {
        return (
            <div className="dashboard-page">
                <div>
                    <p className="mensagem-erro" role="alert">{erro}</p>
                    <button className="btn-principal" onClick={carregarDados}>Tentar novamente</button>
                </div>
            </div>
        );
    }

    const primeiroNome = (restaurante.nome_responsavel || restaurante.nome || "").split(" ")[0];
    const hoje = new Date().toLocaleDateString("pt-BR", {
        weekday: "long",
        day: "2-digit",
        month: "long",
    });

    return (
        <div className="dashboard-layout">
            <aside className="dashboard-sidebar">
                <Link to="/business" className="dashboard-logo dashboard-logo-link">
                    {restaurante.nome}
                </Link>

                <nav className="dashboard-nav">
                    <button className="dashboard-nav-item active">🏠 Home</button>
                    <button className="dashboard-nav-item" disabled title="Em breve">
                        🧾 Pedidos
                    </button>
                    <button
                        className="dashboard-nav-item"
                        onClick={() => navigate("/business/categories")}
                    >
                        📋 Cardápio
                    </button>
                    <button className="dashboard-nav-item" disabled title="Em breve">
                        💰 Financeiro
                    </button>
                    <button className="dashboard-nav-item" disabled title="Em breve">
                        ⭐ Avaliações
                    </button>
                    <button className="dashboard-nav-item" disabled title="Em breve">
                        ⚙️ Config
                    </button>
                </nav>

                <button className="dashboard-logout" onClick={handleSair}>
                    ↪ Sair
                </button>
            </aside>

            <div className="dashboard-content">
                <header className="dashboard-header">
                    <div>
                        <h2>Olá, {primeiroNome}! 👋</h2>
                        <p className="dashboard-subtitulo">{hoje}</p>
                    </div>

                    <div className="dashboard-header-actions">
                        <button
                            className={`toggle-loja ${statusVisual === "ABERTO" ? "toggle-loja-aberta" : ""}`}
                            onClick={() =>
                                setStatusVisual((atual) => (atual === "ABERTO" ? "FECHADO" : "ABERTO"))
                            }
                            title="Alteração ainda não é salva — recurso em desenvolvimento"
                        >
                            ● {STATUS_LABEL[statusVisual] || statusVisual}
                        </button>
                        <button className="icon-button" title="Notificações" disabled>
                            🔔
                        </button>
                    </div>
                </header>

                <div className="dashboard-body">
                    <div className="stats-grid">
                        <div className="stat-card">
                            <span className="stat-valor">{totalProdutos}</span>
                            <span className="stat-rotulo">📦 Produtos cadastrados</span>
                        </div>
                        <div className="stat-card">
                            <span className="stat-valor">{disponiveis}</span>
                            <span className="stat-rotulo">✅ Disponíveis</span>
                        </div>
                        <div className="stat-card">
                            <span className="stat-valor">{indisponiveis}</span>
                            <span className="stat-rotulo">🚫 Indisponíveis</span>
                        </div>
                        <div className="stat-card">
                            <span className="stat-valor">{moeda.format(precoMedio)}</span>
                            <span className="stat-rotulo">💰 Preço médio</span>
                        </div>
                    </div>

                    <div className="dashboard-body-top">
                        <div className="dashboard-secao-cabecalho">
                            <h3>Meus produtos</h3>
                            <div style={{ display: "flex", gap: 12 }}>
                                <button
                                    className="primary-button dashboard-cta"
                                    onClick={() => navigate("/business/products/new")}
                                >
                                    + Novo produto
                                </button>
                                <button
                                    type="button"
                                    className="auth-back"
                                    style={{ width: "auto", marginTop: 0, padding: "0 24px" }}
                                    onClick={() => navigate("/business/categories")}
                                >
                                    Gerenciar categorias
                                </button>
                            </div>
                        </div>
                    </div>

                    {produtos.length === 0 ? (
                        <div className="empty-state">
                            <p>Você ainda não cadastrou nenhum produto.</p>
                            <button
                                className="primary-button dashboard-cta"
                                onClick={() => navigate("/business/products/new")}
                            >
                                Cadastrar o primeiro produto
                            </button>
                        </div>
                    ) : (
                        <div className="product-grid">
                            {produtos.map((produto) => (
                                <div className="product-card" key={produto.id_produto}>
                                    <h3>{produto.nome_produto}</h3>
                                    <p className="product-price">
                                        {moeda.format(produto.preco_produto ?? 0)}
                                    </p>
                                    <span
                                        className={`badge ${
                                            produto.produto_disponivel ? "badge-available" : "badge-unavailable"
                                        }`}
                                    >
                                        {produto.produto_disponivel ? "Disponível" : "Indisponível"}
                                    </span>

                                    <div className="product-card-acoes">
                                        <button
                                            className="btn-contorno"
                                            onClick={() => navigate(`/business/products/${produto.id_produto}/edit`)}
                                        >
                                            Editar
                                        </button>
                                        <button
                                            className="btn-contorno"
                                            onClick={() => handleDeletar(produto.id_produto)}
                                        >
                                            Remover
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default BusinessHome;