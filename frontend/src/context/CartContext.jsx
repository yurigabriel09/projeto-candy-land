import { createContext, useContext, useState } from "react";

const CartContext = createContext(null);
const CART_STORAGE_KEY = "candyland_cart";

function carregarCarrinhoInicial() {
    const dadosSalvos = localStorage.getItem(CART_STORAGE_KEY);
    if (!dadosSalvos) return { restauranteId: null, restauranteNome: null, itens: [] };

    try {
        return JSON.parse(dadosSalvos);
    } catch {
        localStorage.removeItem(CART_STORAGE_KEY);
        return { restauranteId: null, restauranteNome: null, itens: [] };
    }
}

function salvar(carrinho) {
    localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(carrinho));
}

export function CartProvider({ children }) {
    const [carrinho, setCarrinho] = useState(carregarCarrinhoInicial);

    function adicionarItem(produto, restauranteId, restauranteNome) {
        setCarrinho((atual) => {
            // Trocar de restaurante limpa o carrinho atual
            if (atual.restauranteId && atual.restauranteId !== restauranteId) {
                const confirmou = window.confirm(
                    "Seu carrinho tem itens de outro restaurante. Deseja esvaziar e adicionar este novo item?"
                );
                if (!confirmou) return atual;

                const novoCarrinho = {
                    restauranteId,
                    restauranteNome,
                    itens: [{
                        id_produto: produto.id_produto,
                        nome: produto.nome_produto,
                        preco: Number(produto.preco_produto),
                        quantidade: 1
                    }]
                };
                salvar(novoCarrinho);
                return novoCarrinho;
            }

            const itemExistente = atual.itens.find((i) => i.id_produto === produto.id_produto);
            let novosItens;

            if (itemExistente) {
                novosItens = atual.itens.map((i) =>
                    i.id_produto === produto.id_produto ? { ...i, quantidade: i.quantidade + 1 } : i
                );
            } else {
                novosItens = [...atual.itens, {
                    id_produto: produto.id_produto,
                    nome: produto.nome_produto,
                    preco: Number(produto.preco_produto),
                    quantidade: 1
                }];
            }

            const novoCarrinho = { restauranteId, restauranteNome, itens: novosItens };
            salvar(novoCarrinho);
            return novoCarrinho;
        });
    }

    function atualizarQuantidade(idProduto, quantidade) {
        setCarrinho((atual) => {
            if (quantidade <= 0) {
                return removerItem(idProduto);
            }
            const novosItens = atual.itens.map((i) =>
                i.id_produto === idProduto ? { ...i, quantidade } : i
            );
            const novoCarrinho = { ...atual, itens: novosItens };
            salvar(novoCarrinho);
            return novoCarrinho;
        });
    }

    function removerItem(idProduto) {
        setCarrinho((atual) => {
            const novosItens = atual.itens.filter((i) => i.id_produto !== idProduto);
            const novoCarrinho = novosItens.length === 0
                ? { restauranteId: null, restauranteNome: null, itens: [] }
                : { ...atual, itens: novosItens };
            salvar(novoCarrinho);
            return novoCarrinho;
        });
    }

    function limparCarrinho() {
        const vazio = { restauranteId: null, restauranteNome: null, itens: [] };
        setCarrinho(vazio);
        salvar(vazio);
    }

    const total = carrinho.itens.reduce((soma, i) => soma + i.preco * i.quantidade, 0);
    const quantidadeTotal = carrinho.itens.reduce((soma, i) => soma + i.quantidade, 0);

    return (
        <CartContext.Provider value={{ carrinho, adicionarItem, atualizarQuantidade, removerItem, limparCarrinho, total, quantidadeTotal }}>
            {children}
        </CartContext.Provider>
    );
}

export function useCart() {
    return useContext(CartContext);
}