import { Link } from "react-router-dom";
import Header from "../components/Header";
import { useCart } from "../context/CartContext";

const moeda = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });

function Cart() {
    const { carrinho, atualizarQuantidade, removerItem, atualizarTipoPedido, total } = useCart();

    return (
        <>
            <Header />
            <main className="container secao">
                <h1 className="titulo-secao">Seu carrinho</h1>

                {carrinho.itens.length === 0 ? (
                    <p className="mensagem-vazia">Seu carrinho está vazio.</p>
                ) : (
                    <>
                        <p>Pedido em: <strong>{carrinho.restauranteNome}</strong></p>

                        <div className="cart-lista">
                            {carrinho.itens.map((item) => (
                                <div className="cart-item" key={item.id_produto}>
                                    <span className="cart-item-nome">{item.nome}</span>
                                    <div className="cart-item-qtd">
                                        <button onClick={() => atualizarQuantidade(item.id_produto, item.quantidade - 1)}>-</button>
                                        <span>{item.quantidade}</span>
                                        <button onClick={() => atualizarQuantidade(item.id_produto, item.quantidade + 1)}>+</button>
                                    </div>
                                    <span className="cart-item-preco">{moeda.format(item.preco * item.quantidade)}</span>
                                    <button className="cart-item-remover" onClick={() => removerItem(item.id_produto)}>✕</button>
                                </div>
                            ))}
                        </div>

                        <fieldset className="cart-tipo-pedido">
                            <legend>Como deseja receber?</legend>
                            <label>
                                <input
                                    type="radio"
                                    name="orderType"
                                    value="DELIVERY"
                                    checked={carrinho.orderType === "DELIVERY"}
                                    onChange={() => atualizarTipoPedido("DELIVERY")}
                                />
                                <span>
                                    <strong>Receber no endereço</strong>
                                    <small>Informe seu endereço na finalização do pedido.</small>
                                </span>
                            </label>
                            <label>
                                <input
                                    type="radio"
                                    name="orderType"
                                    value="PICKUP"
                                    checked={carrinho.orderType === "PICKUP"}
                                    onChange={() => atualizarTipoPedido("PICKUP")}
                                />
                                <span>
                                    <strong>Retirar no restaurante</strong>
                                    <small>Sem taxa de entrega; a retirada será no endereço cadastrado pelo restaurante.</small>
                                </span>
                            </label>
                        </fieldset>

                        <div className="cart-total">
                            <span>Total</span>
                            <strong>{moeda.format(total)}</strong>
                        </div>

                        <p className="cart-aviso-checkout">A opção escolhida fica salva no carrinho. A finalização e o pagamento ainda estão em desenvolvimento.</p>
                        <button className="btn-principal" disabled title="Checkout ainda em desenvolvimento">
                            Finalizar pedido (em breve)
                        </button>
                    </>
                )}

                <Link to="/home" className="btn-contorno">← Continuar comprando</Link>
            </main>
        </>
    );
}

export default Cart;