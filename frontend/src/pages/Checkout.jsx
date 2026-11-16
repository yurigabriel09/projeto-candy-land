import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import Header from "../components/Header";
import { useAuth } from "../context/AuthContext";
import { useCart } from "../context/CartContext";
import PixPayment from "../components/PixPayment";
import { createOrder, createPayment, getCustomerAddresses } from "../services/orderService";

const moeda = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });

function Checkout() {
    const { carrinho, total, quantidadeTotal, limparCarrinho } = useCart();
    const { dadosAutenticacao } = useAuth();
    const navigate = useNavigate();

    // Método de pagamento: "PAYPAL", "MERCADO_PAGO" ou "PIX"
    const [metodoPagamento, setMetodoPagamento] = useState("PAYPAL");

    // Endereços do cliente
    const [enderecos, setEnderecos] = useState([]);
    const [enderecoId, setEnderecoId] = useState(null);
    const [carregandoEnderecos, setCarregandoEnderecos] = useState(false);

    // Estados de processamento e sucesso
    const [processando, setProcessando] = useState(false);
    const [erro, setErro] = useState("");
    const [sucesso, setSucesso] = useState(false);
    const [pedidoCriadoId, setPedidoCriadoId] = useState(null);

    // Pix: dados do pagamento gerado (QR Code + Copia e Cola)
    const [pixPagamento, setPixPagamento] = useState(null);

    const nomeUsuario = dadosAutenticacao?.nome_completo || "Cliente Candyland";
    const ano = new Date().getFullYear();

    // Redirecionamento automático gerenciado pelo ciclo de vida do React
    useEffect(() => {
        if (sucesso) {
            const timer = setTimeout(() => {
                if (pedidoCriadoId) {
                    navigate(`/checkout/resultado?order_id=${pedidoCriadoId}`);
                } else {
                    navigate("/minha-conta/historico-compras");
                }
            }, 2000);

            return () => clearTimeout(timer);
        }
    }, [sucesso, pedidoCriadoId, navigate]);

    function obterToken() {
        if (dadosAutenticacao?.token) return dadosAutenticacao.token;
        try {
            const raw = localStorage.getItem("candyland_auth");
            return raw ? JSON.parse(raw).token : null;
        } catch {
            return null;
        }
    }

    function obterUserId() {
        if (dadosAutenticacao?.id) return dadosAutenticacao.id;
        if (dadosAutenticacao?.user_id) return dadosAutenticacao.user_id;
        if (dadosAutenticacao?.usuario?.id) return dadosAutenticacao.usuario.id;
        try {
            const raw = localStorage.getItem("candyland_auth");
            if (!raw) return null;
            const parsed = JSON.parse(raw);
            return parsed?.id || parsed?.user_id || parsed?.usuario?.id || parsed?.dados?.id || null;
        } catch {
            return null;
        }
    }

    useEffect(() => {
        async function carregarEnderecos() {
            const userId = obterUserId();
            const token = obterToken();
            if (!userId || !token) return;
            setCarregandoEnderecos(true);
            try {
                const lista = await getCustomerAddresses(userId);
                setEnderecos(lista);
                const principal = lista.find((endereco) => endereco.principal) || lista[0];
                if (principal) setEnderecoId(Number(principal.id));
            } catch (error) {
                console.error("Erro ao carregar endereços do usuário:", error);
            } finally {
                setCarregandoEnderecos(false);
            }
        }
        carregarEnderecos();
    }, [dadosAutenticacao]);

    async function handleFinalizarPedido(e) {
        e.preventDefault();
        setErro("");

        if (!carrinho.itens || carrinho.itens.length === 0) {
            setErro("Seu carrinho está vazio.");
            return;
        }

        const eEntrega = (carrinho.orderType || "DELIVERY") === "DELIVERY";
        if (eEntrega && !enderecoId) {
            setErro("Selecione um endereço de entrega para continuar.");
            return;
        }

        const token = obterToken();
        if (!token) {
            setErro("Sua sessão expirou. Faça login novamente.");
            return;
        }

        setProcessando(true);
        try {
            const payload = {
                restaurant_id: Number(carrinho.restauranteId),
                order_type: carrinho.orderType || "DELIVERY",
                payment_method: metodoPagamento,
                delivery_address_id: eEntrega ? Number(enderecoId) : null,
                items: carrinho.itens.map((item) => ({
                    produto_id: Number(item.id_produto),
                    quantidade: Number(item.quantidade),
                    observacoes: "",
                })),
                general_note: "",
            };

            const pedido = await createOrder(payload);
            if (!pedido?.id) {
                throw new Error("O servidor não retornou o pedido criado.");
            }
            setPedidoCriadoId(pedido.id);

            try {
                const pagamento = await createPayment(
                    pedido.id,
                    `candyland-web-${pedido.id}-payment-v1`
                );

                // Pix permanece nesta tela para exibir QR Code e Copia e Cola.
                if (metodoPagamento === "PIX") {
                    setPixPagamento(pagamento);
                    return;
                }

                // PayPal e Mercado Pago usam checkout hospedado. O CandyLand não
                // recebe nem armazena número de cartão ou CVV.
                if (pagamento?.approval_url) {
                    sessionStorage.setItem(
                        "candyland_checkout_pending",
                        JSON.stringify({ pedido })
                    );
                    const urlPagamento = new URL(pagamento.approval_url);
                    if (urlPagamento.protocol !== "https:") {
                        throw new Error(
                            "O provedor retornou uma URL de pagamento insegura."
                        );
                    }
                    window.location.assign(urlPagamento.href);
                    return;
                }

                // Em modo de integração sem redirecionamento, a tela de resultado
                // consulta o estado real do pedido no backend.
                setSucesso(true);
            } catch (paymentError) {
                sessionStorage.setItem(
                    "candyland_checkout_pending",
                    JSON.stringify({ pedido })
                );
                setErro(
                    paymentError.message ||
                    "Pedido criado, mas não foi possível iniciar o pagamento. Consulte o status do pedido."
                );
                setSucesso(true);
            }
        } catch (err) {
            setErro(
                err.message ||
                "Ocorreu um erro ao processar seu pedido. Tente novamente."
            );
        } finally {
            setProcessando(false);
        }
    }

    function handlePixConfirmado() {
        limparCarrinho();
        setSucesso(true);
    }

    function handlePixVoltar() {
        setPixPagamento(null);
        navigate("/cart");
    }

    if (sucesso) {
        return (
            <div className="cart-page-wrapper">
                <Header />
                <main className="container secao checkout-success-container">
                    <div className="auth-card checkout-success-card">
                        <span className="checkout-success-emoji">🎉</span>
                        <h1 className="checkout-success-title">
                            Pedido realizado com sucesso!
                        </h1>
                        <p className="checkout-success-desc">
                            Seu pedido foi registrado e aguarda confirmação do provedor. A doceria só receberá o pedido depois da aprovação.
                        </p>
                        {erro && <p className="auth-error checkout-error" role="alert">{erro}</p>}
                        <div className="checkout-success-badge">
                            Status: Aguardando pagamento
                        </div>
                        <button 
                            type="button" 
                            className="btn-principal" 
                            onClick={() => {
                                if (pedidoCriadoId) {
                                    navigate(`/checkout/resultado?order_id=${pedidoCriadoId}`);
                                } else {
                                    navigate("/minha-conta/historico-compras");
                                }
                            }}
                        >
                            Consultar pagamento e pedido
                        </button>
                    </div>
                </main>
            </div>
        );
    }

    const isDelivery = (carrinho.orderType || "DELIVERY") === "DELIVERY";

    return (
        <div className="cart-page-wrapper">
            <Header />

            <div className="cart-stepper-bar">
                <div className="container cart-stepper-inner">
                    <div className="cart-stepper">
                        <span className="step">Sacola</span>
                        <span className="step-divider">—</span>
                        <span className="step active">Pagamento</span>
                        <span className="step-divider">—</span>
                        <span className="step">Confirmação</span>
                    </div>
                    <Link to="/cart" className="cart-continuar-link">
                        ← Voltar para o carrinho
                    </Link>
                </div>
            </div>

            <main className="container secao cart-secao">
                <div className="conta-layout checkout-layout">

                    <aside className="conta-menu checkout-menu-aside">
                        <div className="conta-menu-perfil">
                            <span className="conta-avatar">
                                {nomeUsuario.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase()}
                            </span>
                            <div>
                                <strong className="conta-menu-nome">{nomeUsuario}</strong>
                                <small className="conta-menu-sub">Cliente doce desde {ano}</small>
                            </div>
                        </div>

                        <nav className="conta-menu-nav">
                            <div className="conta-menu-item checkout-menu-disabled">
                                <span className="conta-menu-numero">01</span>
                                Dados pessoais
                            </div>
                            <div className="conta-menu-item checkout-menu-disabled">
                                <span className="conta-menu-numero">02</span>
                                Configurações
                            </div>
                            <div className="conta-menu-item conta-menu-item-ativo">
                                <span className="conta-menu-numero">03</span>
                                Pagamentos
                            </div>
                        </nav>

                        <button type="button" className="conta-menu-sair" onClick={() => navigate("/cart")}>
                            Voltar ao carrinho
                        </button>
                    </aside>

                    <section className="conta-conteudo">
                        {isDelivery && (
                            <div className="conta-card checkout-address-section">
                                <div className="checkout-address-header">
                                    <div>
                                        <p className="conta-eyebrow">DESTINO</p>
                                        <h3 className="checkout-address-title">Endereço de Entrega</h3>
                                    </div>
                                    <Link to="/minha-conta/dados-pessoais" className="cart-adicionar-mais">
                                        + Gerenciar endereços
                                    </Link>
                                </div>

                                {carregandoEnderecos ? (
                                    <p className="mensagem-carregando">Carregando seus endereços...</p>
                                ) : enderecos.length === 0 ? (
                                    <div className="mensagem-vazia">
                                        <p>Nenhum endereço cadastrado encontrado na sua conta.</p>
                                        <Link to="/minha-conta/dados-pessoais" className="btn-contorno btn-pequeno">
                                            Cadastrar novo endereço
                                        </Link>
                                    </div>
                                ) : (
                                    <div className="checkout-address-list">
                                        {enderecos.map((end) => {
                                            const selecionado = enderecoId === Number(end.id);
                                            return (
                                                <div
                                                    key={end.id}
                                                    onClick={() => setEnderecoId(Number(end.id))}
                                                    className={`checkout-address-card ${selecionado ? "selected" : ""}`}
                                                >
                                                    <div className="checkout-address-card-inner">
                                                        <div className="checkout-address-radio">
                                                            {selecionado && (
                                                                <div className="checkout-address-radio-inner" />
                                                            )}
                                                        </div>
                                                        <div>
                                                            <strong className="checkout-address-text-street">
                                                                {end.rua}, {end.numero} {end.complemento ? `(${end.complemento})` : ""}
                                                            </strong>
                                                            <small className="checkout-address-text-details">
                                                                {end.bairro} — {end.cidade}/{end.estado} · CEP {end.cep}
                                                            </small>
                                                        </div>
                                                    </div>
                                                    {end.principal && (
                                                        <span className="checkout-address-tag-principal">
                                                            Principal
                                                        </span>
                                                    )}
                                                </div>
                                            );
                                        })}
                                    </div>
                                )}
                            </div>
                        )}

                        <p className="conta-eyebrow">CARTEIRA</p>
                        <h1 className="conta-titulo checkout-titulo">Métodos de pagamento</h1>
                        <p className="conta-subtitulo checkout-subtitulo">
                            Escolha como deseja pagar o seu pedido para finalizar a compra.
                        </p>

                        <div className="payment-tabs-grid">
                            <button
                                type="button"
                                className={`payment-tab-btn ${metodoPagamento === "PAYPAL" ? "active" : ""}`}
                                disabled={Boolean(pixPagamento)}
                                onClick={() => { setMetodoPagamento("PAYPAL"); setErro(""); }}
                            >
                                <span className="payment-tab-icon">🅿️</span>
                                <span>PayPal</span>
                            </button>

                            <button
                                type="button"
                                className={`payment-tab-btn ${metodoPagamento === "MERCADO_PAGO" ? "active" : ""}`}
                                disabled={Boolean(pixPagamento)}
                                onClick={() => { setMetodoPagamento("MERCADO_PAGO"); setErro(""); }}
                            >
                                <span className="payment-tab-icon">💳</span>
                                <span>Mercado Pago</span>
                            </button>

                            <button
                                type="button"
                                className={`payment-tab-btn ${metodoPagamento === "PIX" ? "active" : ""}`}
                                disabled={Boolean(pixPagamento)}
                                onClick={() => { setMetodoPagamento("PIX"); setErro(""); }}
                            >
                                <span className="payment-tab-icon">⚡</span>
                                <span>Pix</span>
                            </button>
                        </div>

                        {erro && <p className="auth-error checkout-error" role="alert">{erro}</p>}

                        {metodoPagamento === "PAYPAL" && (
                            <div className="conta-card paypal-box">
                                <div className="paypal-header">
                                    <h3 className="paypal-title">Pagar com PayPal</h3>
                                    <span className="paypal-badge">Seguro & Rápido</span>
                                </div>

                                <p className="paypal-desc">
                                    Você será redirecionado ao PayPal para concluir o pagamento e, depois, volta ao Candyland.
                                </p>

                                <div className="paypal-protecao-card">
                                    <div className="paypal-protecao-header">
                                        <span>🛡️</span>
                                        <strong>Proteção ao Comprador PayPal</strong>
                                    </div>
                                    <small className="paypal-protecao-texto">
                                        Sua transação é 100% criptografada e protegida.
                                    </small>
                                </div>
                            </div>
                        )}

                        {metodoPagamento === "MERCADO_PAGO" && (
                            <div className="conta-card paypal-box">
                                <div className="paypal-header">
                                    <h3 className="paypal-title">Pagar com Mercado Pago</h3>
                                    <span className="paypal-badge">Cartão ou saldo</span>
                                </div>
                                <p className="paypal-desc">
                                    Você será redirecionado ao Mercado Pago para concluir o pagamento e depois retornará ao CandyLand.
                                </p>
                                <div className="paypal-protecao-card">
                                    <div className="paypal-protecao-header">
                                        <span>🛡️</span>
                                        <strong>Pagamento protegido pelo Mercado Pago</strong>
                                    </div>
                                    <small className="paypal-protecao-texto">
                                        Os dados do cartão são informados somente no ambiente seguro do provedor. O CandyLand não coleta nem armazena número do cartão ou CVV.
                                    </small>
                                </div>
                            </div>
                        )}

                        {metodoPagamento === "PIX" && pixPagamento && (
                            <PixPayment
                                pedidoId={pedidoCriadoId}
                                pagamento={pixPagamento}
                                total={total}
                                onConfirmado={handlePixConfirmado}
                                onVoltar={handlePixVoltar}
                            />
                        )}

                        {metodoPagamento === "PIX" && !pixPagamento && (
                            <div className="conta-card pix-box">
                                <span className="pix-emoji">⚡</span>
                                <h3 className="pix-title">Pagamento Instantâneo via Pix</h3>
                                <p className="pix-desc">
                                    Ao clicar no botão abaixo, geramos um QR Code e um código Pix Copia e Cola para você pagar no app do seu banco.
                                </p>
                                <span className="pix-badge">Aprovação em segundos</span>
                            </div>
                        )}

                        {!pixPagamento && (
                        <div className="conta-card checkout-summary-card">
                            <div className="checkout-summary-row">
                                <div>
                                    <span className="checkout-summary-label">
                                        Subtotal estimado ({quantidadeTotal} {quantidadeTotal === 1 ? "item" : "itens"})
                                    </span>
                                    <strong className="checkout-summary-total">{moeda.format(total)}</strong>
                                </div>
                                <div className="checkout-summary-delivery">
                                    <span className="checkout-summary-delivery-label">Entrega:</span>
                                    <strong className="checkout-summary-delivery-value">
                                        {carrinho.orderType === "PICKUP" ? "Retirada na loja" : "Entrega em casa"}
                                    </strong>
                                </div>
                            </div>

                            <button
                                type="button"
                                className={`primary-button checkout-btn-pay ${metodoPagamento === "PAYPAL" ? "paypal-theme" : ""}`}
                                onClick={handleFinalizarPedido}
                                disabled={processando}
                            >
                                {processando
                                    ? "Processando..."
                                    : metodoPagamento === "PAYPAL"
                                    ? "🔒 Pagar com PayPal"
                                    : metodoPagamento === "PIX"
                                    ? "Gerar QR Code Pix"
                                    : "Pagar com Mercado Pago"}
                            </button>
                        </div>
                        )}
                    </section>
                </div>
            </main>
        </div>
    );
}

export default Checkout;
