import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import DashboardSidebar from "../components/DashboardSidebar";
import { resolverImagemUrl } from "../utils/imageUrl";
import {
    getRestaurant,
    getRestaurantProductsManagement,
    updateRestaurantStatus,
} from "../services/restaurantService";

const moeda = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const STATUS_LABEL = {
    EM_ANALISE: "Em análise",
    ABERTO: "Aberto",
    FECHADO: "Fechado",
    SUSPENSO: "Suspenso",
};
const PREVIA_MAXIMA = 4;

function BusinessHome() {
    const { dadosAutenticacao } = useAuth();
    const [restaurante, setRestaurante] = useState(null);
    const [produtos, setProdutos] = useState([]);
    const [carregando, setCarregando] = useState(true);
    const [erro, setErro] = useState("");
    const [statusVisual, setStatusVisual] = useState(null);
    const [salvandoStatus, setSalvandoStatus] = useState(false);
    const [erroStatus, setErroStatus] = useState("");
    const [mensagemSucesso, setMensagemSucesso] = useState("");
    const location = useLocation();
    const navigate = useNavigate();

    useEffect(() => {
        const mensagem = location.state?.successMessage;
        if (!mensagem) return;
        setMensagemSucesso(mensagem);
        navigate(location.pathname, { replace: true, state: null });
        const timeoutId = window.setTimeout(() => setMensagemSucesso(""), 4500);
        return () => window.clearTimeout(timeoutId);
    }, [location.key, location.pathname, location.state, navigate]);

    useEffect(() => {
        carregarDados();
        // O ID autenticado permanece fixo durante a vida desta tela.
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    async function carregarDados() {
        setCarregando(true);
        setErro("");
        try {
            const [loja, itens] = await Promise.all([
                getRestaurant(dadosAutenticacao.id),
                getRestaurantProductsManagement(dadosAutenticacao.id),
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

    async function alternarStatusLoja() {
        if (salvandoStatus || !restaurante || !["ABERTO", "FECHADO"].includes(statusVisual)) return;
        const novoStatus = statusVisual === "ABERTO" ? "FECHADO" : "ABERTO";
        setSalvandoStatus(true);
        setErroStatus("");
        try {
            const atualizado = await updateRestaurantStatus(restaurante.id, novoStatus);
            setStatusVisual(atualizado.status);
            setRestaurante((atual) => ({ ...atual, status: atualizado.status }));
        } catch (statusError) {
            setErroStatus(statusError.message || "Não foi possível atualizar o status da loja.");
        } finally {
            setSalvandoStatus(false);
        }
    }

    const totalProdutos = produtos.length;
    const disponiveis = produtos.filter((p) => p.produto_disponivel).length;
    const indisponiveis = totalProdutos - disponiveis;
    const precoMedio = totalProdutos > 0
        ? produtos.reduce((soma, p) => soma + Number(p.preco_produto || 0), 0) / totalProdutos
        : 0;

    if (carregando) {
        return <div className="dashboard-page"><p className="mensagem-carregando" role="status">Carregando painel...</p></div>;
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

    const primeiroNome = (restaurante.nome || "").split(" ")[0];
    const hoje = new Date().toLocaleDateString("pt-BR", {
        weekday: "long", day: "2-digit", month: "long",
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
                            type="button"
                            className={`toggle-loja ${statusVisual === "ABERTO" ? "toggle-loja-aberta" : ""}`}
                            onClick={alternarStatusLoja}
                            disabled={salvandoStatus || !["ABERTO", "FECHADO"].includes(statusVisual)}
                            title={
                                ["ABERTO", "FECHADO"].includes(statusVisual)
                                    ? "Alterar e salvar o status da loja"
                                    : "A loja precisa estar liberada pela administração antes de ser aberta ou fechada"
                            }
                        >
                            ● {salvandoStatus ? "Salvando..." : (STATUS_LABEL[statusVisual] || statusVisual)}
                        </button>
                        <button className="icon-button" title="Notificações" disabled>🔔</button>
                        <button type="button" className="icon-button" title="Configurações" onClick={() => navigate("/business/configuracao")}>⚙</button>
                        <button type="button" className="icon-button" title="Minha conta">👤</button>
                    </div>
                </header>

                {erroStatus && <p className="field-error" role="alert">{erroStatus}</p>}
                {mensagemSucesso && <p className="field-message dashboard-success-message" role="status">✓ {mensagemSucesso}</p>}

                <div className="dashboard-body">
                    <div className="stats-grid">
                        <div className="stat-card"><span className="stat-valor">{totalProdutos}</span><span className="stat-rotulo">📦 Produtos cadastrados</span></div>
                        <div className="stat-card"><span className="stat-valor">{disponiveis}</span><span className="stat-rotulo">✅ Disponíveis</span></div>
                        <div className="stat-card"><span className="stat-valor">{indisponiveis}</span><span className="stat-rotulo">🚫 Indisponíveis</span></div>
                        <div className="stat-card"><span className="stat-valor">{moeda.format(precoMedio)}</span><span className="stat-rotulo">💰 Preço médio</span></div>
                    </div>
                    <div className="dashboard-body-top">
                        <div className="dashboard-secao-cabecalho">
                            <h3>Seus produtos</h3>
                            <button className="primary-button dashboard-cta" onClick={() => navigate("/business/cardapio")}>Ver cardápio completo →</button>
                        </div>
                    </div>
                    {produtos.length === 0 ? (
                        <div className="empty-state">
                            <p>Você ainda não cadastrou nenhum produto.</p>
                            <button className="primary-button dashboard-cta" onClick={() => navigate("/business/products/new")}>Cadastrar o primeiro produto</button>
                        </div>
                    ) : (
                        <div className="product-grid">
                            {previa.map((produto) => (
                                <div className="product-card" key={produto.id_produto}>
                                    {produto.imagem_url && <img className="product-image-preview" src={resolverImagemUrl(produto.imagem_url)} alt={produto.nome_produto} />}
                                    <h3>{produto.nome_produto}</h3>
                                    <p className="product-price">{moeda.format(produto.preco_produto ?? 0)}</p>
                                    <span className={`badge ${produto.produto_disponivel ? "badge-available" : "badge-unavailable"}`}>
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
