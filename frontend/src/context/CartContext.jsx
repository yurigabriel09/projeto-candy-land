import { createContext, useContext, useState } from "react";

const CartContext = createContext(null);
const CART_STORAGE_KEY = "candyland_cart";
const CARRINHO_VAZIO = { restauranteId: null, restauranteNome: null, itens: [], orderType: "DELIVERY" };

function carregarCarrinhoInicial() {
    const dadosSalvos = localStorage.getItem(CART_STORAGE_KEY);
    if (!dadosSalvos) return CARRINHO_VAZIO;

    try {
        const dados = JSON.parse(dadosSalvos);
        if (!Array.isArray(dados?.itens)) return { ...CARRINHO_VAZIO };
        return {
            ...CARRINHO_VAZIO,
            ...dados,
            orderType: ["DELIVERY", "PICKUP"].includes(dados.orderType)
                ? dados.orderType
                : "DELIVERY",
        };
    } catch {
        localStorage.removeItem(CART_STORAGE_KEY);
        return CARRINHO_VAZIO;
    }
}

export function CartProvider({ children }) {
    const [carrinho, setCarrinho] = useState(carregarCarrinhoInicial);

    function aplicar(novoCarrinho) {
        localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(novoCarrinho));
        setCarrinho(novoCarrinho);
    }

    function adicionarItem(produto, restauranteId, restauranteNome) {
        const itemNovo = {
            id_produto: produto.id_produto,
            nome: produto.nome_produto,
            preco: Number(produto.preco_produto),
            quantidade: 1
        };

        // Trocar de restaurante esvazia o carrinho atual (a pergunta fica fora do setState)
        if (carrinho.restauranteId && carrinho.restauranteId !== restauranteId) {
            const confirmou = window.confirm(
                "Seu carrinho tem itens de outro restaurante. Deseja esvaziar e adicionar este novo item?"
            );
            if (!confirmou) return;

            aplicar({
                ...CARRINHO_VAZIO,
                restauranteId,
                restauranteNome,
                itens: [itemNovo],
            });
            return;
        }

        const itemExistente = carrinho.itens.find((i) => i.id_produto === produto.id_produto);

        const novosItens = itemExistente
            ? carrinho.itens.map((i) =>
                i.id_produto === produto.id_produto
                    ? { ...i, quantidade: i.quantidade + 1 }
                    : i
            )
            : [...carrinho.itens, itemNovo];

        aplicar({
            ...carrinho,
            restauranteId,
            restauranteNome,
            itens: novosItens,
            orderType: carrinho.orderType || "DELIVERY",
        });
    }

    function removerItem(idProduto) {
        const novosItens = carrinho.itens.filter((i) => i.id_produto !== idProduto);

        aplicar(
            novosItens.length === 0
                ? CARRINHO_VAZIO
                : { ...carrinho, itens: novosItens }
        );
    }

    function atualizarQuantidade(idProduto, quantidade) {
        if (quantidade <= 0) {
            removerItem(idProduto);
            return;
        }

        aplicar({
            ...carrinho,
            itens: carrinho.itens.map((i) =>
                i.id_produto === idProduto ? { ...i, quantidade } : i
            )
        });
    }

    function atualizarTipoPedido(orderType) {
        if (!["DELIVERY", "PICKUP"].includes(orderType)) return;
        aplicar({ ...carrinho, orderType });
    }

    function limparCarrinho() {
        aplicar({ ...CARRINHO_VAZIO });
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
                limparCarrinho,
                atualizarTipoPedido,
                total,
                quantidadeTotal
            }}
        >
            {children}
        </CartContext.Provider>
    );
}

export function useCart() {
    return useContext(CartContext);
}