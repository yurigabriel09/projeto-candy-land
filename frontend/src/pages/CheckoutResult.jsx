import { useCallback, useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import Header from "../components/Header";
import LocationMap from "../components/LocationMap";
import { createPayment, getOrder, getPayment } from "../services/orderService";

const CHECKOUT_SESSION_KEY = "candyland_checkout_pending";

function rotuloFormaPagamento(metodo) {
    if (metodo === "PIX") return "PIX";
    if (metodo === "CARTAO_CREDITO") return "Cartão de crédito";
    if (metodo === "CARTAO_DEBITO") return "Cartão de débito";
    if (metodo === "CARTAO") return "Cartão (aguardando identificação)";
    return metodo || "Não informado";
}

const STATUS_LABEL = {
    PENDENTE_PAGAMENTO: "Aguardando pagamento",
    PAGAMENTO_CONFIRMADO: "Pagamento confirmado",
    RESTAURANTE_RECEBEU: "Pedido recebido pelo restaurante",
    RESTAURANTE_ACEITOU: "Pedido aceito",
    PROCESSANDO: "Preparando seu pedido",
    PRONTO_PARA_ENTREGA: "Pedido pronto",
    ENTREGUE: "Entregue",
    FINALIZADO: "Finalizado",
    CANCELADO: "Cancelado",
};

function CheckoutResult() {
    const [searchParams] = useSearchParams();
    const orderId = searchParams.get("order_id");
    const [pedido, setPedido] = useState(null);
    const [pagamento, setPagamento] = useState(null);
    const [erro, setErro] = useState("");
    const [erroPagamento, setErroPagamento] = useState("");
    const [carregando, setCarregando] = useState(true);
    const [iniciandoNovaTentativa, setIniciandoNovaTentativa] = useState(false);
    const [erroNovaTentativa, setErroNovaTentativa] = useState("");
    const [atualizacao, setAtualizacao] = useState(0);

    const consultar = useCallback(async () => {
        if (!orderId || !/^\d+$/.test(orderId)) {
            setErro("Não foi possível identificar o pedido no retorno do Mercado Pago.");
            setCarregando(false);
            return;
        }
        setErro("");
        setErroPagamento("");
        try {
            // Primeiro carrega o pedido. Assim, mesmo se o provedor ainda não
            // reportar uma transação, a pessoa consegue consultar o pedido/mapa.
            const order = await getOrder(orderId);
            setPedido(order);
        } catch (error) {
            setErro(error.message || "Não foi possível consultar o pedido.");
            setCarregando(false);
            return;
        }
        try {
            // Os parâmetros da URL nunca são tratados como prova de pagamento.
            const payment = await getPayment(orderId);
            setPagamento(payment);
        } catch (error) {
            setPagamento(null);
            setErroPagamento(error.message || "O pagamento ainda não está disponível para consulta.");
        } finally {
            setCarregando(false);
        }
    }, [orderId]);

    useEffect(() => { consultar(); }, [consultar, atualizacao]);

    async function tentarPagarNovamente() {
        if (!orderId) return;
        setErroNovaTentativa("");
        setIniciandoNovaTentativa(true);
        try {
            const chave = `candyland-order-${orderId}-retry-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
            const pagamentoNovo = await createPayment(orderId, chave);
            if (!pagamentoNovo?.approval_url) {
                throw new Error(pagamentoNovo?.message || "O Mercado Pago não retornou a URL do checkout.");
            }
            const url = new URL(pagamentoNovo.approval_url);
            if (url.protocol !== "https:") throw new Error("A URL do checkout não é HTTPS; o pagamento não foi aberto.");
            window.location.assign(url.href);
        } catch (error) {
            setErroNovaTentativa(error.message || "Não foi possível reabrir o pagamento.");
        } finally {
            setIniciandoNovaTentativa(false);
        }
    }

    useEffect(() => {
        // A tela de resultado substitui a confirmação persistida na sessão; assim,
        // voltar ao carrinho depois do checkout não reapresenta uma compra antiga.
        try {
            const salvo = JSON.parse(sessionStorage.getItem(CHECKOUT_SESSION_KEY) || "null");
            if (salvo?.pedido?.id && String(salvo.pedido.id) === String(orderId)) {
                sessionStorage.removeItem(CHECKOUT_SESSION_KEY);
            }
        } catch {
            sessionStorage.removeItem(CHECKOUT_SESSION_KEY);
        }
    }, [orderId]);

    useEffect(() => {
        const statusTerminalPagamento = ["REJECTED", "CANCELLED", "ACTION_REQUIRED", "REFUNDED"];
        if (!pedido || pedido.status !== "PENDENTE_PAGAMENTO" || statusTerminalPagamento.includes(pagamento?.status)) {
            return undefined;
        }
        const timer = window.setTimeout(() => setAtualizacao((n) => n + 1), 5000);
        return () => window.clearTimeout(timer);
    }, [pedido, pagamento]);

    const confirmado = pedido && pedido.status !== "PENDENTE_PAGAMENTO" && pedido.status !== "CANCELADO";
    const pagamentoPrecisaAtencao = ["REJECTED", "CANCELLED", "ACTION_REQUIRED", "REFUNDED"].includes(pagamento?.status);

    return (
        <>
            <Header />
            <main className="container secao checkout-result">
                <section className="cart-pedido-sucesso">
                    <h1>Resultado do pagamento</h1>
                    {carregando && <p role="status">Consultando o Mercado Pago...</p>}
                    {erro && <p className="cart-checkout-erro" role="alert">{erro}</p>}
                    {pedido && (
                        <>
                            <p>Pedido <strong>{pedido.order_code}</strong></p>
                            <dl>
                                <div><dt>Status do pedido</dt><dd>{STATUS_LABEL[pedido.status] || pedido.status}</dd></div>
                                <div><dt>Status do pagamento</dt><dd>{pagamento?.status || "Ainda sem confirmação"}</dd></div>
                                <div><dt>Forma de pagamento</dt><dd>{rotuloFormaPagamento(pagamento?.payment_method || pedido.payment_method)}</dd></div>
                                <div><dt>Total</dt><dd><strong>{new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(pedido.total || 0)}</strong></dd></div>
                            </dl>
                            {pedido.order_type === "DELIVERY" && <LocationMap latitude={pedido.delivery_location?.latitude} longitude={pedido.delivery_location?.longitude} label={pedido.delivery_location?.endereco || "Endereço de entrega"} />}
                            {pedido.order_type === "PICKUP" && <LocationMap latitude={pedido.pickup_location?.latitude} longitude={pedido.pickup_location?.longitude} label={pedido.pickup_location?.endereco || "Unidade de retirada"} />}
                            {erroPagamento && <p className="cart-aviso-checkout" role="status">Ainda não foi possível consultar uma transação no Mercado Pago: {erroPagamento}</p>}
                            {confirmado ? (
                                <p className="field-message">O backend confirmou o pagamento e atualizou o estado do pedido.</p>
                            ) : pedido.status === "CANCELADO" ? (
                                <p className="cart-checkout-erro">Este pedido foi cancelado. Entre em contato com o restaurante se precisar de ajuda.</p>
                            ) : pagamentoPrecisaAtencao ? (
                                <>
                                    <p className="cart-checkout-erro">O Mercado Pago informou <strong>{pagamento.status}</strong>. O pedido continua pendente no CandyLand e não será enviado ao restaurante até a aprovação.</p>
                                    {["REJECTED", "CANCELLED"].includes(pagamento?.status) && (
                                        <button className="btn-principal" type="button" disabled={iniciandoNovaTentativa} onClick={tentarPagarNovamente}>
                                            {iniciandoNovaTentativa ? "Reabrindo pagamento..." : "Tentar pagamento novamente"}
                                        </button>
                                    )}
                                </>
                            ) : (
                                <p className="cart-aviso-checkout">Pagamento ainda não confirmado. A página consulta o estado periodicamente; não realize outro pagamento enquanto a tentativa estiver pendente.</p>
                            )}
                        </>
                    )}
                    {erroNovaTentativa && <p className="cart-checkout-erro" role="alert">{erroNovaTentativa}</p>}
                    <div className="checkout-result-actions">
                        <button className="btn-principal" type="button" disabled={carregando || iniciandoNovaTentativa} onClick={() => { setCarregando(true); setAtualizacao((n) => n + 1); }}>
                            Consultar novamente
                        </button>
                        {pedido && <Link to={`/pedidos/${pedido.id}/acompanhar`} className="btn-contorno">Acompanhar entrega</Link>}
                        <Link to="/home" className="btn-contorno">Voltar às lojas</Link>
                    </div>
                </section>
            </main>
        </>
    );
}

export default CheckoutResult;
