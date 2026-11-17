import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import Header from "../components/Header";
import { getRestaurant, getRestaurantProducts } from "../services/restaurantService";
import { useCart } from "../context/CartContext";
import ProductRecommendations from "../components/ProductRecommendations";
import { resolverImagemUrl } from "../utils/imageUrl";

const moeda = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });

// PROVISÓRIO: iguais aos da Home (mesma regra: id da loja % tamanho da lista),
// para o banner da loja combinar com o card. O banco ainda não tem avaliação,
// distância nem tempo por loja. Trocar pelos dados reais (item 13).
const EMOJIS_LOJA = ["🍰", "🍫", "🍭", "🧁", "🍮", "🍪", "🍦", "🎂"];
const SELOS = ["Mais Pedida", "Nova", null, "Premium", "Rápida", null, "Destaque", null];
const AMOSTRAS = [
    { nota: 4.9, avaliacoes: 342, km: 1.2, tempo: "25-40 min" },
    { nota: 4.8, avaliacoes: 128, km: 0.8, tempo: "20-35 min" },
    { nota: 4.7, avaliacoes: 96, km: 2.1, tempo: "30-45 min" },
    { nota: 5.0, avaliacoes: 210, km: 1.5, tempo: "35-50 min" },
    { nota: 4.6, avaliacoes: 87, km: 0.5, tempo: "15-25 min" },
    { nota: 4.8, avaliacoes: 154, km: 1.8, tempo: "25-40 min" },
];

function textoFrete(loja) {
    const base = Number(loja.taxa_entrega_base || 0);
    const porKm = Number(loja.taxa_entrega_por_km || 0);
    if (base === 0 && porKm === 0) return "Frete Grátis";
    return `Frete ${moeda.format(base)}`;
}

function Restaurant() {
    const { restauranteId } = useParams();
    const navigate = useNavigate();
    const [restaurante, setRestaurante] = useState(null);
    const [produtos, setProdutos] = useState([]);
    const [carregando, setCarregando] = useState(true);
    const [erro, setErro] = useState("");
    const [tentativa, setTentativa] = useState(0);
    const [categoriaAtiva, setCategoriaAtiva] = useState("");
    const {
        adicionarItem,
        atualizarQuantidade,
        carrinho,
        total,
        quantidadeMaxima,
    } = useCart();

    useEffect(() => {
        let ativo = true;
        setCarregando(true);
        setErro("");
        setRestaurante(null);
        setProdutos([]);
        setCategoriaAtiva("");

        Promise.all([getRestaurant(restauranteId), getRestaurantProducts(restauranteId)])
            .then(([loja, itens]) => {
                if (ativo) {
                    setRestaurante(loja);
                    setProdutos(itens);
                }
            })
            .catch((error) => {
                if (ativo) setErro(error.message || "Não foi possível carregar o restaurante.");
            })
            .finally(() => {
                if (ativo) setCarregando(false);
            });

        return () => { ativo = false; };
    }, [restauranteId, tentativa]);

    const categorias = useMemo(() => {
        const nomes = [];
        produtos.forEach((p) => {
            if (p.nome_categoria && !nomes.includes(p.nome_categoria)) {
                nomes.push(p.nome_categoria);
            }
        });
        return nomes;
    }, [produtos]);

    const produtosVisiveis = categoriaAtiva
        ? produtos.filter((p) => p.nome_categoria === categoriaAtiva)
        : produtos;

    // O painel "Meu Pedido" só mostra o carrinho se ele for desta loja.
    const carrinhoEhDestaLoja =
        restaurante && String(carrinho.restauranteId) === String(restaurante.id);
    const itensDoPedido = carrinhoEhDestaLoja ? carrinho.itens : [];
    const totalDoPedido = carrinhoEhDestaLoja ? total : 0;
    const quantidadeNoPedido = itensDoPedido.reduce((soma, i) => soma + i.quantidade, 0);

    function quantidadeDoProduto(idProduto) {
        const item = itensDoPedido.find((i) => String(i.id_produto) === String(idProduto));
        return item ? item.quantidade : 0;
    }

    const amostra = restaurante ? AMOSTRAS[restaurante.id % AMOSTRAS.length] : null;
    const selo = restaurante ? SELOS[restaurante.id % SELOS.length] : null;
    const emojiLoja = restaurante ? EMOJIS_LOJA[restaurante.id % EMOJIS_LOJA.length] : "";

    return (
        <>
            <Header />
            <main className="lj-pagina">
                {carregando ? (
                    <p className="mensagem-carregando" role="status">Carregando restaurante e produtos...</p>
                ) : erro ? (
                    <section className="container secao">
                        <Link to="/home" className="btn-contorno">← Voltar aos restaurantes</Link>
                        <p className="mensagem-erro" role="alert">{erro}</p>
                        <button className="btn-principal" onClick={() => setTentativa((valor) => valor + 1)}>
                            Tentar novamente
                        </button>
                    </section>
                ) : restaurante && (
                    <>
                        <section className="lj-hero">
                            <div className="lj-hero-inner">
                                <Link to="/home" className="lj-voltar">← Voltar</Link>
                                <div className="lj-hero-linha">
                                    <div className="lj-hero-capa" aria-hidden="true">{emojiLoja}</div>
                                    <div className="lj-hero-info">
                                        <h1>{restaurante.nome}</h1>
                                        <p className="lj-hero-meta">
                                            <span>★ {amostra.nota.toLocaleString("pt-BR", { minimumFractionDigits: 1 })} ({amostra.avaliacoes} avaliações)</span>
                                            <span>·</span>
                                            <span>{restaurante.descricao || "Loja parceira Candyland"}</span>
                                            <span>·</span>
                                            <span>{amostra.km.toLocaleString("pt-BR")} km</span>
                                            <span>·</span>
                                            <span className="lj-hero-frete">{textoFrete(restaurante)}</span>
                                        </p>
                                        <div className="lj-hero-chips">
                                            <span className="lj-chip">🕐 {amostra.tempo}</span>
                                            {selo && <span className="lj-chip">✨ {selo}</span>}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </section>

                        <div className="lj-corpo">
                            <section className="lj-produtos">
                                {categorias.length > 0 && (
                                    <div className="lj-categorias">
                                        <button
                                            type="button"
                                            className={`lj-cat${categoriaAtiva === "" ? " lj-cat-ativa" : ""}`}
                                            onClick={() => setCategoriaAtiva("")}
                                        >
                                            Todos
                                        </button>
                                        {categorias.map((nome) => (
                                            <button
                                                key={nome}
                                                type="button"
                                                className={`lj-cat${categoriaAtiva === nome ? " lj-cat-ativa" : ""}`}
                                                onClick={() => setCategoriaAtiva(nome)}
                                            >
                                                {nome}
                                            </button>
                                        ))}
                                    </div>
                                )}

                                {produtos.length === 0 ? (
                                    <p className="mensagem-vazia">Este restaurante ainda não tem produtos cadastrados.</p>
                                ) : (
                                    <div className="lj-lista">
                                        {produtosVisiveis.map((produto) => {
                                            const quantidade = quantidadeDoProduto(produto.id_produto);
                                            return (
                                                <article className="lj-produto" key={produto.id_produto}>
                                                    <div className="lj-produto-capa">
                                                        {produto.imagem_url ? (
                                                            <img src={resolverImagemUrl(produto.imagem_url)} alt={produto.nome_produto} />
                                                        ) : <span aria-hidden="true">🍰</span>}
                                                    </div>
                                                    <div className="lj-produto-corpo">
                                                        <h3>{produto.nome_produto}</h3>
                                                        {produto.descricao_produto && (
                                                            <p className="lj-produto-desc">{produto.descricao_produto}</p>
                                                        )}
                                                        <strong className="lj-produto-preco">
                                                            {moeda.format(produto.preco_produto ?? 0)}
                                                        </strong>
                                                    </div>

                                                    {!produto.produto_disponivel ? (
                                                        <span className="selo-indisponivel">Indisponível</span>
                                                    ) : quantidade > 0 ? (
                                                        <div className="lj-qtd">
                                                            <button
                                                                type="button"
                                                                className="lj-qtd-menos"
                                                                aria-label={`Diminuir ${produto.nome_produto}`}
                                                                onClick={() => atualizarQuantidade(produto.id_produto, quantidade - 1)}
                                                            >−</button>
                                                            <span className="lj-qtd-valor">{quantidade}</span>
                                                            <button
                                                                type="button"
                                                                className="lj-qtd-mais"
                                                                aria-label={`Aumentar ${produto.nome_produto}`}
                                                                disabled={quantidade >= quantidadeMaxima}
                                                                onClick={() => adicionarItem(produto, restaurante.id, restaurante.nome)}
                                                            >+</button>
                                                        </div>
                                                    ) : (
                                                        <button
                                                            type="button"
                                                            className="lj-qtd-mais"
                                                            aria-label={`Adicionar ${produto.nome_produto}`}
                                                            onClick={() => adicionarItem(produto, restaurante.id, restaurante.nome)}
                                                        >+</button>
                                                    )}
                                                </article>
                                            );
                                        })}
                                    </div>
                                )}

                                {/* Sugestões a partir do que já está no carrinho deste restaurante */}
                                <ProductRecommendations
                                    produtoIds={carrinhoEhDestaLoja ? carrinho.itens.map((i) => i.id_produto) : []}
                                    restauranteId={restaurante.id}
                                    restauranteNome={restaurante.nome}
                                    titulo="Sugestões para o seu pedido"
                                />
                            </section>

                            <aside className="lj-pedido" aria-label="Meu pedido">
                                <div className="lj-pedido-topo">
                                    <span aria-hidden="true">🛒</span>
                                    <strong>Meu Pedido</strong>
                                    {quantidadeNoPedido > 0 && (
                                        <span className="lj-pedido-badge">{quantidadeNoPedido}</span>
                                    )}
                                </div>

                                {itensDoPedido.length === 0 ? (
                                    <div className="lj-pedido-vazio">
                                        <span aria-hidden="true">🍭</span>
                                        <p>Adicione itens para começar</p>
                                    </div>
                                ) : (
                                    <>
                                        <ul className="lj-pedido-itens">
                                            {itensDoPedido.map((item) => (
                                                <li key={item.id_produto}>
                                                    <span className="lj-pedido-nome">{item.nome}</span>
                                                    <span className="lj-pedido-qtd">×{item.quantidade}</span>
                                                    <span className="lj-pedido-valor">
                                                        {moeda.format(item.preco * item.quantidade)}
                                                    </span>
                                                </li>
                                            ))}
                                        </ul>
                                        <div className="lj-pedido-total">
                                            <span>Total</span>
                                            <strong>{moeda.format(totalDoPedido)}</strong>
                                        </div>
                                        <button
                                            type="button"
                                            className="lj-pedido-botao"
                                            onClick={() => navigate("/cart")}
                                        >
                                            Fazer Pedido 🍭
                                        </button>
                                    </>
                                )}
                            </aside>
                        </div>
                    </>
                )}
            </main>
        </>
    );
}

export default Restaurant;