import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Header from "../components/Header";
import { getOrders, issueReceiptCode } from "../services/orderService";

const moeda = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const STATUS = {
    PENDENTE_PAGAMENTO: "Aguardando pagamento",
    PAGAMENTO_CONFIRMADO: "Pagamento confirmado",
    RESTAURANTE_RECEBEU: "Pedido recebido pela doceria",
    RESTAURANTE_ACEITOU: "Pedido aceito",
    PROCESSANDO: "Em preparo",
    PRONTO_PARA_ENTREGA: "Pronto para entrega/retirada",
    ENTREGUE: "Entregue — aguardando confirmação",
    FINALIZADO: "Compra finalizada",
    CANCELADO: "Cancelado",
};
const METODOS = { PIX: "Pix", PAYPAL: "PayPal", MERCADO_PAGO: "Mercado Pago", CARTAO: "Cartão", CARTAO_CREDITO: "Cartão de crédito" };
const PEDIDOS_COM_PAGAMENTO = new Set(["PAGAMENTO_CONFIRMADO", "RESTAURANTE_RECEBEU", "RESTAURANTE_ACEITOU", "PROCESSANDO", "PRONTO_PARA_ENTREGA", "ENTREGUE"]);

function PurchaseHistory() {
    const [pedidos, setPedidos] = useState([]);
    const [codigos, setCodigos] = useState({});
    const [carregando, setCarregando] = useState(true);
    const [atualizando, setAtualizando] = useState(false);
    const [erro, setErro] = useState("");
    const [mensagens, setMensagens] = useState({});
    const [pedidoCodigo, setPedidoCodigo] = useState(null);

    const carregar = useCallback(async (silencioso = false) => {
        if (!silencioso) setCarregando(true);
        else setAtualizando(true);
        setErro("");
        try { setPedidos(await getOrders()); }
        catch (error) { setErro(error.message || "Não foi possível carregar o histórico de compras."); }
        finally { setCarregando(false); setAtualizando(false); }
    }, []);

    useEffect(() => { carregar(); }, [carregar]);

    async function mostrarCodigo(pedido) {
        setPedidoCodigo(pedido.id);
        setErro("");
        setMensagens((atuais) => ({ ...atuais, [pedido.id]: "" }));
        try {
            const resposta = await issueReceiptCode(pedido.id);
            setCodigos((atuais) => ({ ...atuais, [pedido.id]: resposta.codigo }));
            setMensagens((atuais) => ({ ...atuais, [pedido.id]: "Mostre este código à doceria no momento da entrega/retirada. Ele não é o código do pedido." }));
        } catch (error) { setErro(error.message || "Não foi possível gerar o código de recebimento."); }
        finally { setPedidoCodigo(null); }
    }

    return (
        <>
            <Header />
            <main className="container secao purchase-history-page">
                <p className="pending-orders-eyebrow">MINHA CONTA</p>
                <div className="purchase-history-heading">
                    <div><h1 className="titulo-secao">Histórico de compras</h1><p>Consulte pedidos pagos, acompanhe a entrega e obtenha seu código de recebimento.</p></div>
                    <button className="btn-contorno" type="button" disabled={carregando || atualizando} onClick={() => carregar(true)}>{atualizando ? "Atualizando..." : "Atualizar"}</button>
                </div>
                {erro && <p className="cart-checkout-erro" role="alert">{erro}</p>}
                {carregando ? <p role="status">Carregando histórico...</p> : pedidos.length === 0 ? (
                    <section className="purchase-history-empty"><strong>Você ainda não tem compras</strong><p>Seus pedidos aparecerão aqui depois que você finalizar um pedido.</p><Link className="btn-principal" to="/home">Explorar docerias</Link></section>
                ) : (
                    <div className="purchase-history-list">
                        {pedidos.map((pedido) => {
                            const codigoDisponivel = PEDIDOS_COM_PAGAMENTO.has(pedido.status);
                            const itens = (pedido.items || []).map((item) => `${item.nome_produto || `Produto #${item.produto_id}`} × ${item.quantidade}`).join(", ");
                            return (
                                <article className="purchase-history-card" key={pedido.id}>
                                    <header><div><strong>Pedido {pedido.order_code}</strong><small>{pedido.created_at ? new Date(pedido.created_at).toLocaleString("pt-BR") : "Data indisponível"}</small></div><span className={`purchase-history-status ${pedido.status === "FINALIZADO" ? "is-complete" : ""}`}>{STATUS[pedido.status] || pedido.status}</span></header>
                                    <p className="purchase-history-restaurant">{pedido.restaurant_name || `Doceria #${pedido.restaurant_id}`}</p>
                                    <p>{itens || "Itens do pedido"}</p>
                                    <div className="purchase-history-meta"><span>{pedido.order_type === "PICKUP" ? "Retirada" : "Entrega"}</span><span>{METODOS[pedido.payment_method] || pedido.payment_method}</span><strong>{moeda.format(pedido.total || 0)}</strong></div>
                                    {pedido.status === "PENDENTE_PAGAMENTO" && <p className="cart-aviso-checkout">O pagamento ainda não foi confirmado. Retome o checkout pela área de pagamentos pendentes.</p>}
                                    {codigoDisponivel && <div className="purchase-history-code">
                                        {codigos[pedido.id] ? <><span>Código de recebimento</span><strong aria-label="Código de recebimento" className="purchase-history-pin">{codigos[pedido.id]}</strong><p>{mensagens[pedido.id]}</p></> : <p>Quando for retirar ou receber o pedido, gere o código que será conferido pela doceria para encerrar a compra.</p>}
                                        <button className="btn-contorno" type="button" disabled={pedidoCodigo === pedido.id} onClick={() => mostrarCodigo(pedido)}>{pedidoCodigo === pedido.id ? "Gerando código..." : codigos[pedido.id] ? "Mostrar código novamente" : "Gerar código de recebimento"}</button>
                                    </div>}
                                    <footer className="purchase-history-actions">
                                        <Link className="btn-contorno" to={`/pedidos/${pedido.id}/acompanhar`}>Acompanhar pedido</Link>
                                        {pedido.status === "PENDENTE_PAGAMENTO" && <Link className="btn-principal" to="/minha-conta/pagamentos-pendentes">Continuar pagamento</Link>}
                                    </footer>
                                </article>
                            );
                        })}
                    </div>
                )}
            </main>
        </>
    );
}

export default PurchaseHistory;
