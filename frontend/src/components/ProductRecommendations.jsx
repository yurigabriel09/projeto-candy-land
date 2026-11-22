import { useEffect, useRef, useState } from "react";
import { useCart } from "../context/CartContext";
import { getProductRecommendations } from "../services/recommendationService";
import { resolverImagemUrl } from "../utils/imageUrl";

const moeda = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });

const MOTIVOS = {
    COMPRADO_JUNTO: "Muito pedido junto",
    MESMA_CATEGORIA: "Combina com seu pedido",
    MAIS_PEDIDOS: "Mais pedidos",
    DESTAQUE: "Destaque da loja",
};

// O backend devolve o produto com chaves como id_produto, nome_produto e preco_produto.
// Os nomes alternativos ficam como segurança caso o formato mude.
function lerProduto(produto) {
    return {
        id: produto.id_produto ?? produto.id,
        nome: produto.nome_produto || produto.nome || produto.name || "Produto",
        preco: Number(produto.preco_produto ?? produto.preco ?? produto.price),
        imagem: produto.imagem_url || produto.image_url || null,
    };
}

// Carrossel de produtos sugeridos.
// produtoIds: ids base (um item selecionado ou todos os itens do carrinho).
function ProductRecommendations({ produtoIds, restauranteId, restauranteNome, titulo = "Você também pode gostar", limite = 8 }) {
    const { adicionarItem, carrinho } = useCart();
    const [produtos, setProdutos] = useState([]);
    const [carregando, setCarregando] = useState(true);
    const [adicionado, setAdicionado] = useState(null);
    const trilho = useRef(null);

    // Só refaz a busca quando o conjunto de ids muda (não a cada mudança de quantidade).
    const chave = [...new Set(produtoIds || [])].map(Number).sort((a, b) => a - b).join(",");

    useEffect(() => {
        if (!chave) {
            setProdutos([]);
            setCarregando(false);
            return undefined;
        }
        const controle = new AbortController();
        setCarregando(true);
        getProductRecommendations(chave.split(","), limite, controle.signal)
            .then((lista) => setProdutos(lista))
            .catch((erro) => {
                if (erro.name !== "AbortError") setProdutos([]); // sugestão é opcional: falhou, some
            })
            .finally(() => {
                if (!controle.signal.aborted) setCarregando(false);
            });
        return () => controle.abort();
    }, [chave, limite]);

    function rolar(direcao) {
        const el = trilho.current;
        if (!el) return;
        el.scrollBy({ left: direcao * Math.max(el.clientWidth * 0.8, 200), behavior: "smooth" });
    }

    function adicionar(produto) {
        const id = lerProduto(produto).id;
        const item = carrinho.itens.find(i => String(i.id_produto) === String(id));
        if (produto.qtd_estoque == null || Number(produto.qtd_estoque) <= (item?.quantidade || 0)) return;
        adicionarItem(produto, restauranteId, restauranteNome);
        setAdicionado(id);
        setTimeout(() => setAdicionado(null), 1800);
    }

    if (!carregando && produtos.length === 0) return null;

    return (
        <section className="recs" aria-label={titulo}>
            <div className="recs-cabecalho">
                <h3 className="recs-titulo">{titulo}</h3>
                {produtos.length > 2 && (
                    <div className="recs-setas">
                        <button type="button" onClick={() => rolar(-1)} aria-label="Ver anteriores">‹</button>
                        <button type="button" onClick={() => rolar(1)} aria-label="Ver próximos">›</button>
                    </div>
                )}
            </div>

            <div className="recs-trilho" ref={trilho}>
                {carregando
                    ? [0, 1, 2].map((i) => <div className="recs-card recs-esqueleto" key={i} aria-hidden="true" />)
                    : produtos.map((produto) => {
                        const { id, nome, preco, imagem: caminhoImagem } = lerProduto(produto);
                        const imagem = caminhoImagem ? resolverImagemUrl(caminhoImagem) : null;
                        const noCarrinho = String(carrinho.restauranteId) === String(restauranteId)
                            ? carrinho.itens.find(i => String(i.id_produto) === String(id)) : null;
                        const esgotado = produto.qtd_estoque == null || Number(produto.qtd_estoque) <= (noCarrinho?.quantidade || 0);
                        return (
                            <article className="recs-card" key={id}>
                                <div className="recs-imagem">
                                    {imagem ? <img src={imagem} alt={nome} loading="lazy" onError={(e) => { e.currentTarget.style.display = "none"; }} /> : null}
                                    <span className="recs-emoji" aria-hidden="true">🧁</span>
                                </div>
                                <span className="recs-motivo">{MOTIVOS[produto.motivo_recomendacao] || "Sugestão"}</span>
                                <h4 className="recs-nome">{nome}</h4>
                                <div className="recs-rodape">
                                    <strong className="recs-preco">{moeda.format(Number.isFinite(preco) ? preco : 0)}</strong>
                                    <button type="button" className="recs-add" disabled={esgotado} onClick={() => adicionar(produto)} aria-label={`Adicionar ${nome} ao carrinho`}>
                                        {adicionado === id ? "✓ Adicionado" : "+ Adicionar"}
                                    </button>
                                </div>
                            </article>
                        );
                    })}
            </div>
        </section>
    );
}

export default ProductRecommendations;