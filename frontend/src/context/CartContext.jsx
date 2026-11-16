import { createContext, useContext, useState } from "react";

const CartContext = createContext(null);
const CART_STORAGE_KEY = "candyland_cart";
// Limite de unidades de um mesmo produto no carrinho
const QUANTIDADE_MAXIMA = 99;
const CARRINHO_VAZIO = {
    restauranteId: null,
    restauranteNome: null,
    itens: [],
    orderType: "DELIVERY"
};

// Garante uma quantidade inteira entre 1 e o limite
function normalizarQuantidade(valor) {
    const numero = Math.floor(Number(valor));
    if (!Number.isFinite(numero)) return 1;
    return Math.min(Math.max(numero, 1), QUANTIDADE_MAXIMA);
}

// O id pode chegar como número ou como texto, dependendo da tela
function mesmoProduto(a, b) {
    return String(a) === String(b);
}

function carregarCarrinhoInicial() {
    const dadosSalvos = localStorage.getItem(CART_STORAGE_KEY);
    if (!dadosSalvos) return CARRINHO_VAZIO;

    try {
        const dados = JSON.parse(dadosSalvos);
        if (Array.isArray(dados?.itens)) {
            return {
                ...CARRINHO_VAZIO,
                ...dados,
                itens: dados.itens.map((i) => ({
                    ...i,
                    preco: Number(i.preco),
                    quantidade: normalizarQuantidade(i.quantidade)
                })),
                orderType: dados.orderType || "DELIVERY"
            };
        }
        return CARRINHO_VAZIO;
    } catch {
        localStorage.removeItem(CART_STORAGE_KEY);
        return CARRINHO_VAZIO;
    }
}

export function CartProvider({ children }) {
    const [carrinho, setCarrinho] = useState(carregarCarrinhoInicial);

    // Recebe uma função que calcula o novo carrinho a partir do atual.
    // Assim, cliques rápidos não perdem incrementos.
    function atualizar(calcular) {
        setCarrinho((atual) => {
            const novo = calcular(atual);
            try {
                localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(novo));
            } catch {
                // sem acesso ao armazenamento: o carrinho continua em memória
            }
            return novo;
        });
    }

    function adicionarItem(produto, restauranteId, restauranteNome) {
        // Captura qualquer propriedade de imagem enviada pelo objeto do produto
        const imagemUrl = produto.image_url || produto.imagem_url || produto.foto_url || produto.imagem || produto.foto || null;

        const itemNovo = {
            id_produto: produto.id_produto || produto.id,
            nome: produto.nome_produto || produto.nome || produto.name,
            preco: Number(produto.preco_produto || produto.preco || produto.price),
            imagem_url: imagemUrl,
            quantidade: 1
        };

        if (carrinho.restauranteId && String(carrinho.restauranteId) !== String(restauranteId)) {
            const confirmou = window.confirm(
                "Seu carrinho tem itens de outro restaurante. Deseja esvaziar e adicionar este novo item?"
            );
            if (!confirmou) return;

            atualizar(() => ({
                ...CARRINHO_VAZIO,
                restauranteId,
                restauranteNome,
                itens: [itemNovo],
            }));
            return;
        }

        atualizar((atual) => {
            const jaExiste = atual.itens.some((i) => mesmoProduto(i.id_produto, itemNovo.id_produto));

            const novosItens = jaExiste
                ? atual.itens.map((i) =>
                    mesmoProduto(i.id_produto, itemNovo.id_produto)
                        ? {
                            ...i,
                            quantidade: Math.min(i.quantidade + 1, QUANTIDADE_MAXIMA),
                            imagem_url: i.imagem_url || imagemUrl
                        }
                        : i
                )
                : [...atual.itens, itemNovo];

            return {
                ...atual,
                restauranteId,
                restauranteNome,
                itens: novosItens,
                orderType: atual.orderType || "DELIVERY",
            };
        });
    }

    function removerItem(idProduto) {
        atualizar((atual) => {
            const novosItens = atual.itens.filter((i) => !mesmoProduto(i.id_produto, idProduto));
            return novosItens.length === 0 ? CARRINHO_VAZIO : { ...atual, itens: novosItens };
        });
    }

    function atualizarQuantidade(idProduto, quantidade) {
        const numero = Number(quantidade);
        if (!Number.isFinite(numero)) return;

        if (numero <= 0) {
            removerItem(idProduto);
            return;
        }

        const novaQuantidade = normalizarQuantidade(numero);
        atualizar((atual) => ({
            ...atual,
            itens: atual.itens.map((i) =>
                mesmoProduto(i.id_produto, idProduto) ? { ...i, quantidade: novaQuantidade } : i
            )
        }));
    }

    function atualizarTipoPedido(orderType) {
        if (!["DELIVERY", "PICKUP"].includes(orderType)) return;
        atualizar((atual) => ({ ...atual, orderType }));
    }

    function limparCarrinho() {
        atualizar(() => ({ ...CARRINHO_VAZIO }));
    }

    const total = carrinho.itens.reduce((soma, i) => soma + i.preco * i.quantidade, 0);
    const quantidadeTotal = carrinho.itens.reduce((soma, i) => soma + i.quantidade, 0);

    return (
        <CartContext.Provider
            value={{
                carrinho,
                adicionarItem,
                atualizarQuantidade,
                removerItem,
                atualizarTipoPedido,
                limparCarrinho,
                total,
                quantidadeTotal,
                quantidadeMaxima: QUANTIDADE_MAXIMA
            }}
        >
            {children}
        </CartContext.Provider>
    );
}

export function useCart() {
    return useContext(CartContext);
}