import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import Header from "../components/Header";
import { useAuth } from "../context/AuthContext";
import { useCart } from "../context/CartContext";
import PixPayment from "../components/PixPayment";
import { createOrder, createPayment, getDeliveryQuote } from "../services/orderService";

const moeda = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });

function Checkout() {
    const { carrinho, total, quantidadeTotal, limparCarrinho } = useCart();
    const { dadosAutenticacao } = useAuth();
    const navigate = useNavigate();

    // Método de pagamento: "PAYPAL", "CARTAO_CREDITO" ou "PIX"
    const [metodoPagamento, setMetodoPagamento] = useState("PAYPAL");

    // Endereços do cliente
    const [enderecos, setEnderecos] = useState([]);
    const [enderecoId, setEnderecoId] = useState(null);
    const [carregandoEnderecos, setCarregandoEnderecos] = useState(false);

    // Dados do cartão de crédito
    const [nomeCartao, setNomeCartao] = useState(dadosAutenticacao?.nome_completo || "");
    const [numeroCartao, setNumeroCartao] = useState("");
    const [validadeCartao, setValidadeCartao] = useState("");
    const [cvvCartao, setCvvCartao] = useState("");
    const [salvarCartao, setSalvarCartao] = useState(true);

    // Dados do PayPal
    const [emailPaypal, setEmailPaypal] = useState(dadosAutenticacao?.email || "");

    // Estados de processamento e sucesso
    const [processando, setProcessando] = useState(false);
    const [erro, setErro] = useState("");
    const [sucesso, setSucesso] = useState(false);
    const [pedidoCriadoId, setPedidoCriadoId] = useState(null);

    // Pix: dados do pagamento gerado (QR Code + Copia e Cola)
    const [pixPagamento, setPixPagamento] = useState(null);

    // Taxa de entrega calculada pelo servidor (a mesma usada na criação do pedido)
    const [cotacao, setCotacao] = useState(null);
    const [erroCotacao, setErroCotacao] = useState("");
    const [calculandoTaxa, setCalculandoTaxa] = useState(false);

    const nomeUsuario = dadosAutenticacao?.nome_completo || "Cliente Candyland";
    const ano = new Date().getFullYear();

    // Redirecionamento automático gerenciado pelo ciclo de vida do React
    useEffect(() => {
        if (sucesso) {
            const timer = setTimeout(() => {
                if (pedidoCriadoId) {
                    navigate(`/pedidos/${pedidoCriadoId}/acompanhar`);
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
                const apiBase = import.meta.env.VITE_API_URL || "http://127.0.0.1:5000";
                const resposta = await fetch(`${apiBase}/users/${userId}/enderecos`, {
                    headers: {
                        "Authorization": `Bearer ${token}`
                    }
                });

                if (resposta.ok) {
                    const res = await resposta.json();
                    const lista = res.dados || [];
                    setEnderecos(lista);

                    const principal = lista.find((e) => e.principal) || lista[0];
                    if (principal) {
                        setEnderecoId(Number(principal.id));
                    }
                }
            } catch (e) {
                console.error("Erro ao carregar endereços do usuário:", e);
            } finally {
                setCarregandoEnderecos(false);
            }
        }

        carregarEnderecos();
    }, [dadosAutenticacao]);

    useEffect(() => {
        const entrega = (carrinho.orderType || "DELIVERY") === "DELIVERY";
        if (!carrinho.restauranteId || (entrega && !enderecoId)) {
            setCotacao(null);
            setErroCotacao("");
            return undefined;
        }

        let cancelado = false;
        setCalculandoTaxa(true);
        setErroCotacao("");
        getDeliveryQuote({
            restaurantId: carrinho.restauranteId,
            orderType: carrinho.orderType || "DELIVERY",
            addressId: entrega ? enderecoId : null,
        })
            .then((resultado) => {
                if (!cancelado) setCotacao(resultado);
            })
            .catch((error) => {
                if (!cancelado) {
                    setCotacao(null);
                    setErroCotacao(error.message || "Não foi possível calcular a taxa de entrega.");
                }
            })
            .finally(() => {
                if (!cancelado) setCalculandoTaxa(false);
            });

        return () => {
            cancelado = true;
        };
    }, [carrinho.restauranteId, carrinho.orderType, enderecoId]);

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

        if (metodoPagamento === "CARTAO_CREDITO") {
            if (!nomeCartao.trim()) {
                setErro("Informe o nome impresso no cartão.");
                return;
            }

            const numLimpo = numeroCartao.replace(/\D/g, "");
            if (numLimpo.length !== 16) {
                setErro("O número do cartão deve conter exatamente 16 dígitos.");
                return;
            }

            const matchValidade = validadeCartao.trim().match(/^(0[1-9]|1[0-2])\/(\d{2}|\d{4})$/);
            if (!matchValidade) {
                setErro("Informe a validade no formato MM/AA ou MM/AAAA.");
                return;
            }

            const mes = parseInt(matchValidade[1], 10);
            let anoValidade = parseInt(matchValidade[2], 10);
            if (matchValidade[2].length === 2) anoValidade += 2000;

            const agora = new Date();
            if (anoValidade < agora.getFullYear() || (anoValidade === agora.getFullYear() && mes < agora.getMonth() + 1)) {
                setErro("A data de validade do cartão expirou.");
                return;
            }

            const cvvLimpo = cvvCartao.replace(/\D/g, "");
            if (cvvLimpo.length !== 3) {
                setErro("O código de segurança (CVV) deve conter exatamente 3 dígitos.");
                return;
            }
        }

        const token = obterToken();
        if (!token) {
            setErro("Sua sessão expirou. Faça login novamente.");
            return;
        }

        setProcessando(true);

        try {
            const backendPaymentMethod = metodoPagamento;

            const payload = {
                restaurant_id: Number(carrinho.restauranteId) || 1,
                order_type: carrinho.orderType || "DELIVERY",
                payment_method: backendPaymentMethod,
                delivery_address_id: eEntrega ? Number(enderecoId) : null,
                items: carrinho.itens.map((i) => ({
                    produto_id: Number(i.id_produto),
                    quantidade: Number(i.quantidade),
                    observacoes: ""
                })),
                general_note: ""
            };

            // Cria o pedido e gera o pagamento no backend
            const pedido = await createOrder(payload);
            const pagamento = await createPayment(pedido.id);

            // Pix: mostra a tela de QR Code
            if (metodoPagamento === "PIX") {
                setPedidoCriadoId(pedido.id);
                setPixPagamento(pagamento);
                return;
            }

            // PayPal e Mercado Pago: abre o checkout do provedor
            if (!pagamento?.approval_url) {
                throw new Error(pagamento?.message || "O provedor não retornou o link de pagamento.");
            }
            const urlPagamento = new URL(pagamento.approval_url);
            if (urlPagamento.protocol !== "https:") {
                throw new Error("O link de pagamento não é HTTPS; o pagamento não foi aberto.");
            }
            window.location.assign(urlPagamento.href);

        } catch (err) {
            setErro(err.message || "Ocorreu um erro ao processar seu pedido. Tente novamente.");
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
                            Seu pagamento foi confirmado e o pedido foi enviado ao restaurante. Redirecionando...
                        </p>
                        <div className="checkout-success-badge">
                            Status: Pagamento confirmado
                        </div>
                        <button 
                            type="button" 
                            className="btn-principal" 
                            onClick={() => {
                                if (pedidoCriadoId) {
                                    navigate(`/pedidos/${pedidoCriadoId}/acompanhar`);
                                } else {
                                    navigate("/minha-conta/historico-compras");
                                }
                            }}
                        >
                            Ver meu pedido agora
                        </button>
                    </div>
                </main>
            </div>
        );
    }

    const isDelivery = (carrinho.orderType || "DELIVERY") === "DELIVERY";
    const taxaEntrega = cotacao?.taxa_entrega ?? 0;
    const totalComTaxa = total + taxaEntrega;

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
                                    <span className="paypal-badge">Cartão, Pix ou saldo</span>
                                </div>

                                <p className="paypal-desc">
                                    Você será redirecionado ao Mercado Pago para pagar com cartão, Pix ou saldo da conta e, depois, volta ao Candyland.
                                </p>

                                <div className="paypal-protecao-card">
                                    <div className="paypal-protecao-header">
                                        <span>🛡️</span>
                                        <strong>Pagamento protegido pelo Mercado Pago</strong>
                                    </div>
                                    <small className="paypal-protecao-texto">
                                        Seus dados de pagamento ficam com o Mercado Pago, não passam pelo Candyland.
                                    </small>
                                </div>
                            </div>
                        )}

                        {metodoPagamento === "PIX" && pixPagamento && (
                            <PixPayment
                                pedidoId={pedidoCriadoId}
                                pagamento={pixPagamento}
                                total={totalComTaxa}
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

                        {erroCotacao && !pixPagamento && (
                            <p className="auth-error checkout-error" role="alert">{erroCotacao}</p>
                        )}

                        {!pixPagamento && (
                        <div className="conta-card checkout-summary-card">
                            <div className="checkout-summary-row">
                                <div>
                                    <span className="checkout-summary-label">
                                        Valor Total ({quantidadeTotal} {quantidadeTotal === 1 ? "item" : "itens"})
                                    </span>
                                    <strong className="checkout-summary-total">{moeda.format(totalComTaxa)}</strong>
                                    <div className="checkout-breakdown">
                                        <div className="checkout-breakdown-row">
                                            <span>Subtotal</span>
                                            <span>{moeda.format(total)}</span>
                                        </div>
                                        <div className="checkout-breakdown-row">
                                            <span>{isDelivery ? "Taxa de entrega" : "Retirada na loja"}</span>
                                            {calculandoTaxa ? (
                                                <span className="checkout-breakdown-muted">Calculando...</span>
                                            ) : !isDelivery || (cotacao && taxaEntrega === 0) ? (
                                                <span className="checkout-breakdown-gratis">Grátis</span>
                                            ) : cotacao ? (
                                                <span>{moeda.format(taxaEntrega)}</span>
                                            ) : (
                                                <span className="checkout-breakdown-muted">Escolha o endereço</span>
                                            )}
                                        </div>
                                        {cotacao?.tempo_estimado && !calculandoTaxa && (
                                            <div className="checkout-breakdown-tempo">
                                                <span aria-hidden="true">{isDelivery ? "🛵" : "🛍️"}</span>
                                                <span>
                                                    {isDelivery ? "Entrega estimada em " : "Pronto para retirada em "}
                                                    <strong>{cotacao.tempo_estimado.minimo}{"–"}{cotacao.tempo_estimado.maximo} min</strong>
                                                </span>
                                            </div>
                                        )}
                                    </div>
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
                                disabled={processando || calculandoTaxa || Boolean(erroCotacao)}
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