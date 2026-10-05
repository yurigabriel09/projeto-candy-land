import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import DashboardSidebar from "../components/DashboardSidebar";
import { getRestaurant, getRestaurantProducts } from "../services/restaurantService";
import { getCategories } from "../services/categoryService";
import { updateProduct, deleteProduct } from "../services/productService";
import { CATEGORY_TYPES } from "../utils/categoryTypes";

const moeda = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });

const STATUS_LABEL = {
    EM_ANALISE: "Em análise",
    ABERTO: "Aberto",
    FECHADO: "Fechado",
    SUSPENSO: "Suspenso",
};

/** Acha o emoji cadastrado para o nome da categoria, com um genérico de reserva. */
function emojiDaCategoria(nome) {
    const tipo = CATEGORY_TYPES.find((t) => t.nome === nome);
    return tipo ? tipo.emoji : "🍬";
}

function Cardapio() {
    const { dadosAutenticacao } = useAuth();
    const navigate = useNavigate();

    const [restaurante, setRestaurante] = useState(null);
    const [categorias, setCategorias] = useState([]);
    const [produtos, setProdutos] = useState([]);
    const [carregando, setCarregando] = useState(true);
    const [erro, setErro] = useState("");
    const [statusVisual, setStatusVisual] = useState(null);

    const [busca, setBusca] = useState("");
    const [categoriaAtiva, setCategoriaAtiva] = useState(null); // null = "Todos"

    useEffect(() => {
        carregarDados();
    }, []);

    async function carregarDados() {
        setCarregando(true);
        setErro("");
        try {
            const [loja, cats, itens] = await Promise.all([
                getRestaurant(dadosAutenticacao.id),
                getCategories(),
                getRestaurantProducts(dadosAutenticacao.id),
            ]);
            setRestaurante(loja);
            setStatusVisual(loja.status);
            setCategorias(cats.filter((c) => c.ativa));
            setProdutos(itens);
        } catch (error) {
            setErro(error.message || "Não foi possível carregar o cardápio.");
        } finally {
            setCarregando(false);
        }
    }

    async function handleToggleDisponivel(produto) {
        const novoValor = !produto.produto_disponivel;

        // Atualização otimista: muda a tela na hora, desfaz se a API falhar.
        setProdutos((atual) =>
            atual.map((p) =>
                p.id_produto === produto.id_produto ? { ...p, produto_disponivel: novoValor } : p
            )
        );

        try {
            await updateProduct(produto.id_produto, { disponivel: novoValor });
        } catch (error) {
            setProdutos((atual) =>
                atual.map((p) =>
                    p.id_produto === produto.id_produto
                        ? { ...p, produto_disponivel: produto.produto_disponivel }
                        : p
                )
            );
            alert(error.message || "Não foi possível atualizar a disponibilidade.");
        }
    }

    async function handleDeletar(id) {
        if (!confirm("Remover este item do cardápio?")) return;
        try {
            await deleteProduct(id);
            setProdutos((atual) => atual.filter((p) => p.id_produto !== id));
        } catch (error) {
            alert(error.message || "Erro ao remover item.");
        }
    }

    if (carregando) {
        return (
            <div className="dashboard-layout">
                <p className="mensagem-carregando" role="status">Carregando cardápio...</p>
            </div>
        );
    }

    if (erro) {
        return (
            <div className="dashboard-layout">
                <div>
                    <p className="mensagem-erro" role="alert">{erro}</p>
                    <button className="btn-principal" onClick={carregarDados}>Tentar novamente</button>
                </div>
            </div>
        );
    }

    const termo = busca.trim().toLowerCase();
    const produtosFiltrados = produtos.filter((p) => {
        const combinaBusca = !termo || p.nome_produto.toLowerCase().includes(termo);
        const combinaCategoria = !categoriaAtiva || p.id_categoria === categoriaAtiva;
        return combinaBusca && combinaCategoria;
    });

    const totalAtivos = produtos.filter((p) => p.produto_disponivel).length;

    return (
        <div className="dashboard-layout">
            <DashboardSidebar ativo="cardapio" nomeLoja={restaurante.nome} />

            <div className="dashboard-content">
                <header className="dashboard-header">
                    <div>
                        <h2>📋 Cardápio</h2>
                        <p className="dashboard-subtitulo">
                            {produtos.length} {produtos.length === 1 ? "item" : "itens"} · {totalAtivos} ativos
                        </p>
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
                    <div className="dashboard-secao-cabecalho">
                        <div className="cardapio-busca">
                            <span>🔍</span>
                            <input
                                type="search"
                                placeholder="Buscar item..."
                                value={busca}
                                onChange={(e) => setBusca(e.target.value)}
                                aria-label="Buscar item do cardápio"
                            />
                        </div>

                        <button
                            className="primary-button dashboard-cta"
                            onClick={() => navigate("/business/products/new")}
                        >
                            + Novo Item
                        </button>
                    </div>

                    <div className="cardapio-filtros">
                        <button
                            className={`chip-loja ${!categoriaAtiva ? "chip-loja-ativa" : ""}`}
                            onClick={() => setCategoriaAtiva(null)}
                        >
                            Todos
                        </button>
                        {categorias.map((cat) => (
                            <button
                                key={cat.id}
                                className={`chip-loja ${categoriaAtiva === cat.id ? "chip-loja-ativa" : ""}`}
                                onClick={() => setCategoriaAtiva(cat.id)}
                            >
                                {cat.nome}
                            </button>
                        ))}
                        <Link to="/business/categories" className="cardapio-gerenciar-categorias">
                            Gerenciar categorias →
                        </Link>
                    </div>

                    {categorias.length === 0 && (
                        <p className="mensagem-vazia">
                            Você ainda não ativou nenhuma categoria.{" "}
                            <a href="/business/categories">Ative uma aqui</a> para organizar seu cardápio.
                        </p>
                    )}

                    {produtosFiltrados.length === 0 ? (
                        <div className="empty-state">
                            <p>
                                {produtos.length === 0
                                    ? "Você ainda não cadastrou nenhum item."
                                    : "Nenhum item encontrado com esse filtro."}
                            </p>
                            <button
                                className="primary-button dashboard-cta"
                                onClick={() => navigate("/business/products/new")}
                            >
                                {produtos.length === 0 ? "Cadastrar o primeiro item" : "Novo item"}
                            </button>
                        </div>
                    ) : (
                        <div className="cardapio-grid">
                            {produtosFiltrados.map((produto) => {
                                const categoria = categorias.find((c) => c.id === produto.id_categoria);
                                return (
                                    <div
                                        key={produto.id_produto}
                                        className={`cardapio-card ${
                                            !produto.produto_disponivel ? "cardapio-card-pausado" : ""
                                        }`}
                                    >
                                        <div className="cardapio-card-topo">
                                            <span className="cardapio-card-emoji">
                                                {produto.imagem_url ? (
                                                    <img src={produto.imagem_url} alt={produto.nome_produto} />
                                                ) : (
                                                    emojiDaCategoria(categoria?.nome)
                                                )}
                                            </span>

                                            <label className="switch" title="Disponível para venda">
                                                <input
                                                    type="checkbox"
                                                    checked={produto.produto_disponivel}
                                                    onChange={() => handleToggleDisponivel(produto)}
                                                />
                                                <span className="switch-slider"></span>
                                            </label>
                                        </div>

                                        <h3>{produto.nome_produto}</h3>
                                        {categoria && <p className="cardapio-card-categoria">{categoria.nome}</p>}

                                        {produto.descricao_produto && (
                                            <p className="cardapio-card-descricao">{produto.descricao_produto}</p>
                                        )}

                                        <p className="product-price">{moeda.format(produto.preco_produto ?? 0)}</p>
                                        <p className="cardapio-card-estoque">Estoque: {produto.qtd_estoque} un.</p>

                                        <div className="product-card-acoes">
                                            <button
                                                className="btn-contorno"
                                                onClick={() =>
                                                    navigate(`/business/products/${produto.id_produto}/edit`)
                                                }
                                            >
                                                ✏️ Editar
                                            </button>
                                            <button
                                                className="btn-contorno"
                                                onClick={() => handleDeletar(produto.id_produto)}
                                            >
                                                🗑️
                                            </button>
                                        </div>
                                    </div>
                                );
                            })}

                            <button
                                className="cardapio-card cardapio-card-adicionar"
                                onClick={() => navigate("/business/products/new")}
                            >
                                <span className="cardapio-card-adicionar-icone">+</span>
                                Adicionar novo item
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default Cardapio;