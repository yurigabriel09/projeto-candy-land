import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Header from "../components/Header";
import { useAuth } from "../context/AuthContext";
import { useCart } from "../context/CartContext";
import { createOrder, getCustomerAddresses } from "../services/orderService";

const moeda = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });

function formatarEndereco(endereco) {
    const linha = [endereco.rua, endereco.numero].filter(Boolean).join(", ");
    const local = [endereco.bairro, endereco.cidade, endereco.estado].filter(Boolean).join(" — ");
    return [linha, local, endereco.cep].filter(Boolean).join(" | ");
}

function Cart() {
    const { dadosAutenticacao } = useAuth();
    const {
        carrinho,
        atualizarQuantidade,
        removerItem,
        atualizarTipoPedido,
        limparCarrinho,
        total,
    } = useCart();

    const [enderecos, setEnderecos] = useState([]);
    const [enderecoId, setEnderecoId] = useState("");
    const [carregandoEnderecos, setCarregandoEnderecos] = useState(false);
    const [erroEnderecos, setErroEnderecos] = useState("");
    const [metodoPagamento, setMetodoPagamento] = useState("PIX");
    const [enviando, setEnviando] = useState(false);
    const [erroCheckout, setErroCheckout] = useState("");
    const [pedidoCriado, setPedidoCriado] = useState(null);

    useEffect(() => {
        let ativo = true;
        if (!dadosAutenticacao?.id) {
            setErroEnderecos("Não foi possível identificar a conta autenticada. Entre novamente.");
            return () => { ativo = false; };
        }

        setCarregandoEnderecos(true);
        setErroEnderecos("");
        getCustomerAddresses(dadosAutenticacao.id)
            .then((lista) => {
                if (!ativo) return;
                setEnderecos(lista);
                const preferido = lista.find((endereco) => endereco.principal) || lista[0];
                setEnderecoId(preferido ? String(preferido.id) : "");
            })
            .catch((error) => {
                if (ativo) setErroEnderecos(error.message || "Não foi possível carregar seus endereços.");
            })
            .finally(() => {
                if (ativo) setCarregandoEnderecos(false);
            });

        return () => { ativo = false; };
    }, [dadosAutenticacao?.id]);

    const enderecoSelecionado = enderecos.find(
        (endereco) => endereco.id === Number(enderecoId)
    );

    async function handleFinalizarPedido(event) {
        event.preventDefault();
        setErroCheckout("");

        if (!carrinho.restauranteId || carrinho.itens.length === 0) {
            setErroCheckout("Adicione pelo menos um produto antes de finalizar o pedido.");
            return;
        }
        if (!["PIX", "CARTAO_CREDITO"].includes(metodoPagamento)) {
            setErroCheckout("Selecione uma forma de pagamento válida.");
            return;
        }
        if (carrinho.orderType === "DELIVERY" && !enderecoId) {
            setErroCheckout("Selecione um endereço ativo para receber o pedido.");
            return;
        }

        const payload = {
            restaurant_id: Number(carrinho.restauranteId),
            order_type: carrinho.orderType,
            payment_method: metodoPagamento,
            items: carrinho.itens.map((item) => ({
                produto_id: Number(item.id_produto),
                quantidade: Number(item.quantidade),
            })),
        };
        if (carrinho.orderType === "DELIVERY") {
            payload.delivery_address_id = Number(enderecoId);
        }

        setEnviando(true);
        try {
            const pedido = await createOrder(payload);
            setPedidoCriado(pedido);
            limparCarrinho();
        } catch (error) {
            setErroCheckout(error.message || "Não foi possível finalizar o pedido.");
        } finally {
            setEnviando(false);
        }
    }

    return (
        <>
            <Header />
            <main className="container secao">
                <h1 className="titulo-secao">Seu carrinho</h1>

                {pedidoCriado ? (
                    <section className="cart-pedido-sucesso" role="status">
                        <h2>Pedido criado com sucesso!</h2>
                        <p>Seu pedido <strong>{pedidoCriado.order_code}</strong> foi registrado e aguarda pagamento.</p>
                        <dl>
                            <div><dt>Status</dt><dd>{pedidoCriado.status}</dd></div>
                            <div><dt>Modalidade</dt><dd>{pedidoCriado.order_type === "PICKUP" ? "Retirada no restaurante" : "Entrega no endereço"}</dd></div>
                            <div><dt>Subtotal</dt><dd>{moeda.format(pedidoCriado.subtotal || 0)}</dd></div>
                            <div><dt>Taxa de entrega</dt><dd>{moeda.format(pedidoCriado.delivery_fee || 0)}</dd></div>
                            <div><dt>Total calculado pelo servidor</dt><dd><strong>{moeda.format(pedidoCriado.total || 0)}</strong></dd></div>
                        </dl>
                        <p className="cart-aviso-checkout">O pedido está pendente de pagamento. Nenhuma cobrança foi realizada nesta etapa.</p>
                        <Link to="/home" className="btn-principal">Continuar comprando</Link>
                    </section>
                ) : carrinho.itens.length === 0 ? (
                    <>
                        <p className="mensagem-vazia">Seu carrinho está vazio.</p>
                        <Link to="/home" className="btn-contorno">← Continuar comprando</Link>
                    </>
                ) : (
                    <>
                        <p>Pedido em: <strong>{carrinho.restauranteNome}</strong></p>

                        <div className="cart-lista">
                            {carrinho.itens.map((item) => (
                                <div className="cart-item" key={item.id_produto}>
                                    <span className="cart-item-nome">{item.nome}</span>
                                    <div className="cart-item-qtd">
                                        <button type="button" aria-label={`Diminuir ${item.nome}`} onClick={() => atualizarQuantidade(item.id_produto, item.quantidade - 1)}>-</button>
                                        <span>{item.quantidade}</span>
                                        <button type="button" aria-label={`Aumentar ${item.nome}`} onClick={() => atualizarQuantidade(item.id_produto, item.quantidade + 1)}>+</button>
                                    </div>
                                    <span className="cart-item-preco">{moeda.format(item.preco * item.quantidade)}</span>
                                    <button type="button" className="cart-item-remover" aria-label={`Remover ${item.nome}`} onClick={() => removerItem(item.id_produto)}>✕</button>
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
                                    <small>O servidor validará endereço, coordenadas e raio de entrega.</small>
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
                                    <small>Sem taxa de entrega; será usado o endereço ativo do restaurante.</small>
                                </span>
                            </label>
                        </fieldset>

                        {carrinho.orderType === "DELIVERY" && (
                            <div className="cart-checkout-campo">
                                <label htmlFor="checkout-endereco">Endereço de entrega</label>
                                {carregandoEnderecos ? (
                                    <p role="status">Carregando endereços...</p>
                                ) : enderecos.length > 0 ? (
                                    <select id="checkout-endereco" value={enderecoId} onChange={(event) => setEnderecoId(event.target.value)} required>
                                        <option value="">Selecione um endereço</option>
                                        {enderecos.map((endereco) => (
                                            <option key={endereco.id} value={endereco.id}>
                                                {endereco.principal ? "Principal — " : ""}{formatarEndereco(endereco)}
                                            </option>
                                        ))}
                                    </select>
                                ) : (
                                    <p className="cart-aviso-checkout">Nenhum endereço ativo foi encontrado. Você pode escolher retirada ou cadastrar um endereço pela área de conta quando o gerenciamento de endereços estiver disponível.</p>
                                )}
                                {erroEnderecos && <p className="cart-checkout-erro" role="alert">{erroEnderecos}</p>}
                                {enderecoSelecionado && (enderecoSelecionado.latitude == null || enderecoSelecionado.longitude == null) && (
                                    <p className="cart-aviso-checkout">Este endereço não possui coordenadas. O servidor recusará a entrega até que o endereço seja completado.</p>
                                )}
                            </div>
                        )}

                        <div className="cart-checkout-campo">
                            <label htmlFor="checkout-pagamento">Forma de pagamento</label>
                            <select id="checkout-pagamento" value={metodoPagamento} onChange={(event) => setMetodoPagamento(event.target.value)}>
                                <option value="PIX">PIX</option>
                                <option value="CARTAO_CREDITO">Cartão de crédito</option>
                            </select>
                            <small>Esta etapa registra a preferência. A integração de pagamento acontecerá em outra entrega.</small>
                        </div>

                        <div className="cart-total">
                            <span>Subtotal estimado</span>
                            <strong>{moeda.format(total)}</strong>
                        </div>
                        <p className="cart-aviso-checkout">Os preços, o estoque e a taxa de entrega serão recalculados/validados no backend. O subtotal acima é apenas uma estimativa local.</p>
                        {erroCheckout && <p className="cart-checkout-erro" role="alert">{erroCheckout}</p>}
                        <button className="btn-principal" type="button" disabled={enviando || carregandoEnderecos} onClick={handleFinalizarPedido}>
                            {enviando ? "Criando pedido..." : "Confirmar pedido"}
                        </button>
                    </>
                )}
            </main>
        </>
    );
}

export default Cart;
