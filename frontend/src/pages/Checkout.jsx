import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import Header from "../components/Header";
import { useAuth } from "../context/AuthContext";
import { useCart } from "../context/CartContext";

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

        if (metodoPagamento === "PAYPAL") {
            if (!emailPaypal.trim() || !emailPaypal.includes("@")) {
                setErro("Informe um e-mail válido da sua conta PayPal.");
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
            const backendPaymentMethod = metodoPagamento === "PAYPAL" ? "CARTAO_CREDITO" : metodoPagamento;

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

            const apiBase = import.meta.env.VITE_API_URL || "http://127.0.0.1:5000";

            const resposta = await fetch(`${apiBase}/pedidos`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify(payload)
            });

            const dados = await resposta.json();

            if (!resposta.ok || !dados.success) {
                throw new Error(dados.erro || dados.mensagem || "Erro ao gravar pedido.");
            }

            const idGerado = dados?.dados?.id || null;
            setPedidoCriadoId(idGerado);
            setSucesso(true);
            limparCarrinho();

        } catch (err) {
            setErro(err.message || "Ocorreu um erro ao processar seu pedido. Tente novamente.");
        } finally {
            setProcessando(false);
        }
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
                                onClick={() => { setMetodoPagamento("PAYPAL"); setErro(""); }}
                            >
                                <span className="payment-tab-icon">🅿️</span>
                                <span>PayPal</span>
                            </button>

                            <button
                                type="button"
                                className={`payment-tab-btn ${metodoPagamento === "CARTAO_CREDITO" ? "active" : ""}`}
                                onClick={() => { setMetodoPagamento("CARTAO_CREDITO"); setErro(""); }}
                            >
                                <span className="payment-tab-icon">💳</span>
                                <span>Cartão de Crédito</span>
                            </button>

                            <button
                                type="button"
                                className={`payment-tab-btn ${metodoPagamento === "PIX" ? "active" : ""}`}
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
                                    Conecte sua conta PayPal para pagar de forma simples e rápida.
                                </p>

                                <div className="form-field paypal-field">
                                    <label htmlFor="paypal-email">E-mail cadastrado no PayPal</label>
                                    <input
                                        id="paypal-email"
                                        type="email"
                                        placeholder="seu-email@exemplo.com"
                                        value={emailPaypal}
                                        onChange={(e) => setEmailPaypal(e.target.value)}
                                    />
                                </div>

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

                        {metodoPagamento === "CARTAO_CREDITO" && (
                            <div className="cartao-container-grid">
                                <div className="conta-card cartao-form-card">
                                    <div className="cartao-form-header">
                                        <h3>Adicionar novo cartão</h3>
                                        <span className="cartao-badge-seguro">Seguro</span>
                                    </div>

                                    <div className="form-field cartao-field">
                                        <label htmlFor="card-name">Nome no cartão</label>
                                        <input
                                            id="card-name"
                                            type="text"
                                            placeholder="Como aparece no cartão"
                                            value={nomeCartao}
                                            onChange={(e) => setNomeCartao(e.target.value)}
                                        />
                                    </div>

                                    <div className="form-field cartao-field">
                                        <label htmlFor="card-number">Número do cartão</label>
                                        <input
                                            id="card-number"
                                            type="text"
                                            placeholder="0000 0000 0000 0000"
                                            maxLength={19}
                                            value={numeroCartao}
                                            onChange={(e) => setNumeroCartao(e.target.value.replace(/\D/g, "").replace(/(.{4})/g, "$1 ").trim())}
                                        />
                                    </div>

                                    <div className="form-row cartao-form-row">
                                        <div className="form-field">
                                            <label htmlFor="card-expiry">Validade</label>
                                            <input
                                                id="card-expiry"
                                                type="text"
                                                placeholder="MM/AA"
                                                maxLength={5}
                                                value={validadeCartao}
                                                onChange={(e) => {
                                                    let val = e.target.value.replace(/\D/g, "");
                                                    if (val.length >= 3) val = `${val.slice(0, 2)}/${val.slice(2, 4)}`;
                                                    setValidadeCartao(val);
                                                }}
                                            />
                                        </div>
                                        <div className="form-field">
                                            <label htmlFor="card-cvv">Código de segurança (CVV)</label>
                                            <input
                                                id="card-cvv"
                                                type="text"
                                                placeholder="000"
                                                maxLength={3}
                                                value={cvvCartao}
                                                onChange={(e) => setCvvCartao(e.target.value.replace(/\D/g, ""))}
                                            />
                                        </div>
                                    </div>

                                    <label className="cartao-salvar-checkbox">
                                        <input
                                            type="checkbox"
                                            checked={salvarCartao}
                                            onChange={(e) => setSalvarCartao(e.target.checked)}
                                        />
                                        <span>Salvar para compras futuras</span>
                                    </label>
                                </div>

                                <div className="cartao-preview-col">
                                    <div className="cartao-preview-card">
                                        <div className="cartao-preview-header">
                                            <small>CARTÃO PRINCIPAL</small>
                                            <div className="cartao-preview-chip"></div>
                                        </div>
                                        <div className="cartao-preview-number">
                                            {numeroCartao ? numeroCartao.slice(-4).padStart(16, "• ") : "•••• •••• •••• 4421"}
                                        </div>
                                        <div className="cartao-preview-footer">
                                            <span>{nomeCartao || "MARINA SILVA"}</span>
                                            <span>{validadeCartao || "08/29"}</span>
                                        </div>
                                    </div>
                                    <button type="button" className="btn-contorno cartao-btn-principal">
                                        Definir como principal
                                    </button>
                                </div>
                            </div>
                        )}

                        {metodoPagamento === "PIX" && (
                            <div className="conta-card pix-box">
                                <span className="pix-emoji">⚡</span>
                                <h3 className="pix-title">Pagamento Instantâneo via Pix</h3>
                                <p className="pix-desc">
                                    Ao clicar no botão abaixo, a transação Pix será processada e confirmada.
                                </p>
                                <span className="pix-badge">Aprovação em segundos</span>
                            </div>
                        )}

                        <div className="conta-card checkout-summary-card">
                            <div className="checkout-summary-row">
                                <div>
                                    <span className="checkout-summary-label">
                                        Valor Total ({quantidadeTotal} {quantidadeTotal === 1 ? "item" : "itens"})
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
                                    : "Confirmar e Pagar"}
                            </button>
                        </div>
                    </section>
                </div>
            </main>
        </div>
    );
}

export default Checkout;