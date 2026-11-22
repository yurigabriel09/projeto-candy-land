import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import Header from "../components/Header";
import LocationMap from "../components/LocationMap";
import PixPayment from "../components/PixPayment";
import { cancelPayPalPayment, capturePayPalPayment, createPayment, getOrder, getPayment } from "../services/orderService";
import { useCart } from "../context/CartContext";

const CHECKOUT_SESSION_KEY = "candyland_checkout_pending";

const moeda = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });

function rotuloFormaPagamento(metodo) {
    if (metodo === "PIX") return "Pix";
    if (metodo === "PAYPAL") return "PayPal";
    if (metodo === "MERCADO_PAGO") return "Mercado Pago";
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

const STATUS_PAGAMENTO_LABEL = {
    APPROVED: "Aprovado",
    PENDING: "Pendente",
    IN_PROCESS: "Em análise",
    REJECTED: "Recusado",
    CANCELLED: "Cancelado",
    ACTION_REQUIRED: "Ação necessária",
    REFUNDED: "Reembolsado",
};

function CheckoutResult() {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const { limparCarrinho } = useCart();
    const orderId = searchParams.get("order_id");
    const providerRetorno = searchParams.get("provider");
    const paypalToken = searchParams.get("token");
    const paypalCancelled = searchParams.get("cancel") === "1";
    const paypalCaptureStarted = useRef(false);
    const redirecionamentoIniciado = useRef(false);
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

    useEffect(() => {
        if (providerRetorno === "paypal" && paypalCancelled && orderId && paypalToken && !paypalCaptureStarted.current) {
            paypalCaptureStarted.current = true;
            let ativo = true;
            cancelPayPalPayment(orderId, paypalToken)
                .then((resultado) => { if (ativo && resultado.pagamento) setPagamento(resultado.pagamento); })
                .catch((error) => { if (ativo) setErroPagamento(error.message || "O checkout PayPal foi fechado; confira o status antes de tentar novamente."); });
            return () => { ativo = false; };
        }
        if (providerRetorno !== "paypal" || paypalCancelled || !orderId || !paypalToken || paypalCaptureStarted.current) return undefined;
        paypalCaptureStarted.current = true;
        let ativo = true;
        setCarregando(true);
        capturePayPalPayment(orderId, paypalToken)
            .then((resultado) => {
                if (!ativo) return;
                if (resultado.pagamento) setPagamento(resultado.pagamento);
                if (resultado.pedido) setPedido(resultado.pedido);
                setErroPagamento("");
                setAtualizacao((valor) => valor + 1);
            })
            .catch((error) => { if (ativo) setErroPagamento(error.message || "Não foi possível concluir a captura PayPal."); })
            .finally(() => { if (ativo) setCarregando(false); });
        return () => { ativo = false; };
    }, [providerRetorno, paypalCancelled, orderId, paypalToken]);

    async function tentarPagarNovamente() {
        if (!orderId) return;
        setErroNovaTentativa("");
        setIniciandoNovaTentativa(true);
        try {
            const chave = `candyland-order-${orderId}-retry-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
            const pagamentoNovo = await createPayment(orderId, chave);
            if (!pagamentoNovo?.approval_url) {
                throw new Error(pagamentoNovo?.message || "O provedor não retornou a URL de checkout.");
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

    useEffect(() => {
        // Somente um pedido confirmado pelo backend autoriza limpar a sacola.
        // A rota de resultado continua disponível para pendências/cancelamentos.
        if (!confirmado || !pedido?.id || redirecionamentoIniciado.current) return;
        redirecionamentoIniciado.current = true;
        limparCarrinho();
        sessionStorage.removeItem(CHECKOUT_SESSION_KEY);
        navigate(`/pedidos/${pedido.id}/acompanhar`, { replace: true });
    }, [confirmado, pedido?.id, limparCarrinho, navigate]);

    // Só visual: define o ícone e os textos do topo do cartão.
    let situacao = "pendente";
    if (confirmado) situacao = "ok";
    else if (pedido?.status === "CANCELADO" || pagamentoPrecisaAtencao) situacao = "erro";

    const TOPO = {
        ok: {
            icone: "✓",
            titulo: "Pagamento confirmado!",
            texto: "Seu pedido está registrado e você pode acompanhar o andamento.",
        },
        pendente: {
            icone: "⏳",
            titulo: "Aguardando pagamento",
            texto: "Estamos consultando o provedor. Não pague de novo enquanto esta tentativa estiver pendente.",
        },
        erro: {
            icone: "!",
            titulo: pedido?.status === "CANCELADO" ? "Pedido cancelado" : "Pagamento não aprovado",
            texto: "Confira os detalhes abaixo.",
        },
    }[situacao];

    const statusPagamento = pagamento?.status
        ? STATUS_PAGAMENTO_LABEL[pagamento.status] || pagamento.status
        : "Ainda sem confirmação";

    return (
        <>
            <Header />
            <main className="container secao checkout-result">
                <section className="rs-cartao">
                    <p className="rs-etiqueta">Resultado do pagamento</p>

                    {pedido && (
                        <div className={`rs-topo rs-topo-${situacao}`}>
                            <span className="rs-icone" aria-hidden="true">{TOPO.icone}</span>
                            <h1>{TOPO.titulo}</h1>
                            <p>{TOPO.texto}</p>
                        </div>
                    )}

                    {carregando && <p className="rs-carregando" role="status">Consultando o provedor de pagamento...</p>}
                    {erro && <p className="cart-checkout-erro" role="alert">{erro}</p>}

                    {pedido && (
                        <>
                            <p className="rs-codigo">Pedido <strong>{pedido.order_code}</strong></p>

                            <dl className="rs-info">
                                <div><dt>Status do pedido</dt><dd>{STATUS_LABEL[pedido.status] || pedido.status}</dd></div>
                                <div><dt>Status do pagamento</dt><dd>{statusPagamento}</dd></div>
                                <div><dt>Forma de pagamento</dt><dd>{rotuloFormaPagamento(pagamento?.payment_method || pedido.payment_method)}</dd></div>
                                <div><dt>Total</dt><dd className="rs-total">{moeda.format(pedido.total || 0)}</dd></div>
                            </dl>

                            {pedido.order_type === "DELIVERY" && (
                                <div className="rs-mapa">
                                    <h2>Endereço de entrega</h2>
                                    <LocationMap latitude={pedido.delivery_location?.latitude} longitude={pedido.delivery_location?.longitude} label={pedido.delivery_location?.endereco || "Endereço de entrega"} />
                                </div>
                            )}
                            {pedido.order_type === "PICKUP" && (
                                <div className="rs-mapa">
                                    <h2>Local de retirada</h2>
                                    <LocationMap latitude={pedido.pickup_location?.latitude} longitude={pedido.pickup_location?.longitude} label={pedido.pickup_location?.endereco || "Unidade de retirada"} />
                                </div>
                            )}

                            {erroPagamento && <p className="cart-aviso-checkout" role="status">Ainda não foi possível consultar uma transação no provedor de pagamento: {erroPagamento}</p>}

                            {confirmado ? (
                                <p className="rs-nota">Pagamento confirmado pelo provedor. Seu pedido está registrado no histórico.</p>
                            ) : pedido.status === "CANCELADO" ? (
                                <p className="cart-checkout-erro">Este pedido foi cancelado. Entre em contato com o restaurante se precisar de ajuda.</p>
                            ) : !pagamento ? (
                                <div>
                                    <p className="cart-aviso-checkout">
                                        Este pedido ainda não possui uma tentativa de pagamento.
                                        Você pode iniciar o pagamento agora.
                                    </p>

                                    {pedido.payment_method === "PAYPAL" && (
                                        <button
                                            className="btn-principal"
                                            type="button"
                                            disabled={iniciandoNovaTentativa}
                                            onClick={tentarPagarNovamente}
                                        >
                                            {iniciandoNovaTentativa
                                                ? "Iniciando pagamento..."
                                                : "Pagar com PayPal"}
                                        </button>
                                    )}
                                </div>
                            ) : pagamentoPrecisaAtencao ? (
                                <>
                                    <p className="cart-checkout-erro">O provedor informou <strong>{statusPagamento}</strong>. O pedido continua pendente no CandyLand e não será enviado ao restaurante até a aprovação.</p>
                                    {["REJECTED", "CANCELLED"].includes(pagamento?.status) && pagamento?.payment_method !== "PIX" && (
                                        <button className="btn-principal" type="button" disabled={iniciandoNovaTentativa} onClick={tentarPagarNovamente}>
                                            {iniciandoNovaTentativa ? "Reabrindo pagamento..." : "Tentar pagamento novamente"}
                                        </button>
                                    )}
                                </>
                            ) : pagamento?.payment_method === "PIX" && (pagamento.pix_copy_paste || pagamento.pix_qr_code_base64) ? (
                                <PixPayment
                                    pedidoId={pedido.id}
                                    pagamento={pagamento}
                                    total={pedido.total || 0}
                                    onConfirmado={() => setAtualizacao((n) => n + 1)}
                                    onVoltar={() => navigate("/home")}
                                />
                            ) : (
                                <p className="cart-aviso-checkout">Pagamento ainda não confirmado. A página consulta o estado periodicamente; não realize outro pagamento enquanto a tentativa estiver pendente.</p>
                            )}
                        </>
                    )}

                    {erroNovaTentativa && <p className="cart-checkout-erro" role="alert">{erroNovaTentativa}</p>}

                    <div className="rs-acoes">
                        {pedido && (
                            <Link to={`/pedidos/${pedido.id}/acompanhar`} className="btn-principal">Acompanhar pedido</Link>
                        )}
                        {confirmado ? (
                            <Link to="/minha-conta/historico-compras" className="btn-contorno">Ver histórico de compras</Link>
                        ) : (
                            <button className="btn-contorno" type="button" disabled={carregando || iniciandoNovaTentativa} onClick={() => { setCarregando(true); setAtualizacao((n) => n + 1); }}>
                                Consultar novamente
                            </button>
                        )}
                        <Link to="/home" className="rs-link">Voltar às lojas</Link>
                    </div>
                </section>
            </main>
        </>
    );
}

export default CheckoutResult;