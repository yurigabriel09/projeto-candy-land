import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Header from "../components/Header";
import { cancelOrder, createPayment, getOrders, getPayment } from "../services/orderService";

const moeda = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const CHECKOUT_REDIRECTED_KEY = "candyland_checkout_redirected_order_id";

function notificarAlteracaoDePedidos() {
    window.dispatchEvent(new Event("candyland:pending-orders-updated"));
}

function PendingPayments() {
    const [pedidos, setPedidos] = useState([]);
    const [carregando, setCarregando] = useState(true);
    const [atualizando, setAtualizando] = useState(false);
    const [erro, setErro] = useState("");
    const [mensagem, setMensagem] = useState("");
    const [pedidoEmOperacao, setPedidoEmOperacao] = useState(null);

    const carregar = useCallback(async (silencioso = false) => {
        if (silencioso) setAtualizando(true);
        else setCarregando(true);
        setErro("");
        try {
            const lista = await getOrders();
            setPedidos((lista || []).filter((pedido) => pedido.status === "PENDENTE_PAGAMENTO"));
        } catch (error) {
            setErro(error.message || "Não foi possível carregar seus pedidos pendentes.");
        } finally {
            setCarregando(false);
            setAtualizando(false);
        }
    }, []);

    useEffect(() => {
        carregar();
        const revalidar = () => carregar(true);
        window.addEventListener("focus", revalidar);
        window.addEventListener("pageshow", revalidar);
        window.addEventListener("candyland:pending-orders-updated", revalidar);
        return () => {
            window.removeEventListener("focus", revalidar);
            window.removeEventListener("pageshow", revalidar);
            window.removeEventListener("candyland:pending-orders-updated", revalidar);
        };
    }, [carregar]);

    async function pagarAgora(pedido) {
        setErro("");
        setMensagem("");
        setPedidoEmOperacao(pedido.id);
        try {
            // Confere se o gateway já reconhece uma aprovação antes de abrir outro checkout.
            try {
                const pagamentoAtual = await getPayment(pedido.id);
                if (pagamentoAtual?.status === "APPROVED") {
                    setMensagem(`O pagamento do pedido ${pedido.order_code} já foi aprovado.`);
                    await carregar(true);
                    notificarAlteracaoDePedidos();
                    return;
                }
                if (["REFUNDED", "ACTION_REQUIRED"].includes(pagamentoAtual?.status)) {
                    throw new Error("Este pagamento precisa de análise antes de uma nova tentativa. Consulte os detalhes do pedido.");
                }
            } catch (error) {
                if (error?.message?.includes("precisa de análise")) throw error;
                // A consulta pode falhar ou ainda não existir tentativa; a criação é tratada pelo backend.
            }

            const key = `candyland-order-${pedido.id}-retry-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
            const pagamento = await createPayment(pedido.id, key);
            if (!pagamento?.approval_url) {
                throw new Error(pagamento?.message || "O Mercado Pago não retornou a URL do checkout.");
            }
            const destino = new URL(pagamento.approval_url);
            if (destino.protocol !== "https:") throw new Error("A URL de pagamento não é HTTPS e não foi aberta.");
            sessionStorage.setItem(CHECKOUT_REDIRECTED_KEY, String(pedido.id));
            window.location.assign(destino.href);
        } catch (error) {
            setErro(`${pedido.order_code}: ${error.message || "Não foi possível reabrir o pagamento."}`);
            await carregar(true);
        } finally {
            setPedidoEmOperacao(null);
        }
    }

    async function desistir(pedido) {
        if (!window.confirm(`Deseja desistir do pedido ${pedido.order_code}? Ele será cancelado e não será enviado ao restaurante.`)) return;
        setErro("");
        setMensagem("");
        setPedidoEmOperacao(pedido.id);
        try {
            await cancelOrder(pedido.id);
            setMensagem(`Pedido ${pedido.order_code} cancelado.`);
            await carregar(true);
            notificarAlteracaoDePedidos();
        } catch (error) {
            setErro(error.message || "Não foi possível cancelar o pedido.");
        } finally {
            setPedidoEmOperacao(null);
        }
    }

    return (
        <>
            <Header />
            <main className="container secao pending-orders-page">
                <p className="pending-orders-eyebrow">MINHA CONTA</p>
                <h1 className="titulo-secao">Pedidos e pagamentos pendentes</h1>
                <p className="pending-orders-subtitle">
                    Aqui ficam somente os pedidos que ainda aguardam confirmação do pagamento. Seu carrinho para novas compras permanece separado.
                </p>

                <section className="cart-pedidos-pendentes" aria-labelledby="pending-orders-heading">
                    <div className="cart-pedidos-pendentes-heading">
                        <div>
                            <h2 id="pending-orders-heading">Aguardando pagamento <span className="pending-orders-count">{pedidos.length}</span></h2>
                            <p>Retome o checkout ou desista de um pedido que ainda não foi pago.</p>
                        </div>
                        <button type="button" className="btn-contorno" disabled={atualizando || carregando} onClick={() => carregar(true)}>
                            {atualizando ? "Atualizando..." : "Atualizar"}
                        </button>
                    </div>

                    {carregando && <p role="status">Carregando pedidos pendentes...</p>}
                    {erro && <p className="cart-checkout-erro" role="alert">{erro}</p>}
                    {mensagem && <p className="cart-endereco-validado" role="status">{mensagem}</p>}

                    {!carregando && pedidos.map((pedido) => (
                        <article className="cart-pedido-pendente" key={pedido.id}>
                            <div className="cart-pedido-pendente-info">
                                <strong>Pedido {pedido.order_code}</strong>
                                <span>{(pedido.items || []).map((item) => `${item.nome_produto || `Produto #${item.produto_id}`} × ${item.quantidade}`).join(", ") || "Itens do pedido"}</span>
                                <span>{pedido.order_type === "PICKUP" ? "Retirada no restaurante" : "Entrega no endereço"} · {pedido.payment_method === "PIX" ? "PIX" : "Cartão"}</span>
                                <small>Criado em {pedido.created_at ? new Date(pedido.created_at).toLocaleString("pt-BR") : "data não disponível"}</small>
                                <strong>{moeda.format(pedido.total || 0)}</strong>
                            </div>
                            <div className="cart-pedido-pendente-actions">
                                <button type="button" className="btn-principal" disabled={pedidoEmOperacao !== null} onClick={() => pagarAgora(pedido)}>
                                    {pedidoEmOperacao === pedido.id ? "Verificando..." : "Pagar agora"}
                                </button>
                                <button type="button" className="btn-contorno cart-pedido-cancelar" disabled={pedidoEmOperacao !== null} onClick={() => desistir(pedido)}>
                                    {pedidoEmOperacao === pedido.id ? "Aguarde..." : "🗑 Desistir do pedido"}
                                </button>
                                <Link to={`/pedidos/${pedido.id}/acompanhar`} className="btn-contorno">Detalhes</Link>
                            </div>
                        </article>
                    ))}

                    {!carregando && pedidos.length === 0 && !erro && (
                        <div className="pending-orders-empty">
                            <span aria-hidden="true">✓</span>
                            <strong>Você não tem pagamentos pendentes</strong>
                            <p>Quando criar um pedido e ainda não concluir o pagamento, ele aparecerá aqui.</p>
                            <div className="checkout-result-actions"><Link to="/minha-conta/historico-compras" className="btn-contorno">Ver histórico de compras</Link><Link to="/home" className="btn-principal">Continuar comprando</Link></div>
                        </div>
                    )}
                </section>
            </main>
        </>
    );
}

export default PendingPayments;
