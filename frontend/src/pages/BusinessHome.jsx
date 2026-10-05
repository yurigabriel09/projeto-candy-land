import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import DashboardSidebar from "../components/DashboardSidebar";
import { getRestaurant, getRestaurantProducts } from "../services/restaurantService";

const moeda = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });

const STATUS_LABEL = {
    EM_ANALISE: "Em análise",
    ABERTO: "Aberto",
    FECHADO: "Fechado",
    SUSPENSO: "Suspenso",
};

const PREVIA_MAXIMA = 4;

/**
 * Home do painel do restaurante — visão geral.
 *
 * O gerenciamento completo do cardápio (busca, filtro por categoria,
 * editar/remover, toggle de disponibilidade) agora vive em /business/cardapio.
 * Aqui fica só um resumo: estatísticas e uma prévia dos produtos.
 */
function BusinessHome() {
    const { dadosAutenticacao } = useAuth();
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
    const previa = produtos.slice(0, PREVIA_MAXIMA);

    return (
        <div className="dashboard-layout">
            <DashboardSidebar ativo="home" nomeLoja={restaurante.nome} />

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
                            <h3>Seus produtos</h3>
                            <button
                                className="primary-button dashboard-cta"
                                onClick={() => navigate("/business/cardapio")}
                            >
                                Ver cardápio completo →
                            </button>
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
                            {previa.map((produto) => (
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