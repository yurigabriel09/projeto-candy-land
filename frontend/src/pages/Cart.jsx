import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import Header from "../components/Header";
import LocationMap from "../components/LocationMap";
import { useAuth } from "../context/AuthContext";
import { useCart } from "../context/CartContext";
import { cancelOrder, createOrder, createPayment, getCustomerAddresses, getPayment, getOrder } from "../services/orderService";
import { geocodeCustomerAddress, saveAddressCoordinates } from "../services/userService";
import AddressCoordinates from "../components/AddressCoordinates";
import { getRestaurantPickupAddresses } from "../services/restaurantService";

const moeda = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });

// Helper para montar a URL completa da foto se for um caminho relativo
function obterUrlImagem(url) {
    if (!url) return null;
    if (url.startsWith("http://") || url.startsWith("https://")) return url;
    const apiBase = import.meta.env.VITE_API_URL || "http://127.0.0.1:5000";
    return `${apiBase}${url.startsWith("/") ? "" : "/"}${url}`;
}

function Cart() {
    const { carrinho, atualizarQuantidade, removerItem, atualizarTipoPedido, total, quantidadeTotal } = useCart();
    const navigate = useNavigate();
    const [cupom, setCupom] = useState("");
    const [cupomAplicado, setCupomAplicado] = useState(false);
    const [mensagemCupom, setMensagemCupom] = useState("");

    function handleAplicarCupom(e) {
        e.preventDefault();
        if (!cupom.trim()) return;
        if (cupom.toUpperCase() === "CANDY10") {
            setCupomAplicado(true);
            setMensagemCupom("Cupom CANDY10 aplicado!");
        } else {
            setCupomAplicado(false);
            setMensagemCupom("Cupom inválido");
        }
    }

    function handleIrParaPagamento() {
        if (!carrinho.itens || carrinho.itens.length === 0) return;
        navigate("/checkout");
    }

    return (
        <div className="cart-page-wrapper">
            <Header />

            <div className="cart-stepper-bar">
                <div className="container cart-stepper-inner">
                    <div className="cart-stepper">
                        <span className="step active">Sacola</span>
                        <span className="step-divider">—</span>
                        <span className="step">Pagamento</span>
                        <span className="step-divider">—</span>
                        <span className="step">Confirmação</span>
                    </div>
                    <Link to="/home" className="cart-continuar-link">
                        Continuar comprando
                    </Link>
                </div>
            </div>

            <main className="container secao cart-secao">
                <Link to="/home" className="cart-voltar-link">
                    ← Voltar para a loja
                </Link>

                <div className="cart-header-titulo">
                    <div>
                        <span className="cart-eyebrow">SEU PEDIDO</span>
                        <h1 className="cart-titulo">
                            Carrinho de doces
                            {quantidadeTotal > 0 && (
                                <span className="cart-badge-itens">
                                    {quantidadeTotal} {quantidadeTotal === 1 ? "item" : "itens"}
                                </span>
                            )}
                        </h1>
                    </div>
                </div>

                {carrinho.itens.length === 0 ? (
                    <div className="estado-vazio cart-vazio-box">
                        <span className="estado-vazio-emoji">🛒</span>
                        <h2>Seu carrinho está vazio</h2>
                        <p>Adicione deliciosos doces dos nossos restaurantes para continuar.</p>
                        <Link to="/home" className="btn-principal">
                            Ver lojas e produtos
                        </Link>
                    </div>
                ) : (
                    <div className="cart-grid-container">
                        <div className="cart-col-principal">
                            <div className="cart-restaurante-card">
                                <div className="cart-restaurante-info">
                                    <span className="cart-restaurante-icone">🍰</span>
                                    <div>
                                        <h3>{carrinho.restauranteNome || "Restaurante"}</h3>
                                        <p>Entrega estimada em 25–40 min</p>
                                    </div>
                                </div>
                                <Link
                                    to={carrinho.restauranteId ? `/restaurantes/${carrinho.restauranteId}` : "/home"}
                                    className="cart-adicionar-mais"
                                >
                                    Adicionar itens
                                </Link>
                            </div>

                            <div className="cart-itens-lista">
                                {carrinho.itens.map((item) => {
                                    const imgSrc = obterUrlImagem(item.imagem_url);
                                    return (
                                        <div className="cart-item-card" key={item.id_produto}>
                                            <div className="cart-item-thumb">
                                                {imgSrc ? (
                                                    <img
                                                        src={imgSrc}
                                                        alt={item.nome}
                                                        onError={(e) => {
                                                            e.currentTarget.style.display = "none";
                                                            const fallback = e.currentTarget.parentNode?.querySelector(".cart-item-emoji-fallback");
                                                            if (fallback) fallback.style.display = "inline";
                                                        }}
                                                    />
                                                ) : null}
                                                <span
                                                    className="cart-item-emoji-fallback"
                                                    style={{ display: imgSrc ? "none" : "inline" }}
                                                >
                                                    🧁
                                                </span>
                                            </div>
                                            <div className="cart-item-detalhes">
                                                <h4 className="cart-item-nome">{item.nome}</h4>
                                                <span className="cart-item-preco">
                                                    {moeda.format(item.preco)}
                                                </span>
                                            </div>

                                            <div className="cart-item-acoes">
                                                <div className="cart-qtd-seletor">
                                                    <button
                                                        type="button"
                                                        onClick={() => atualizarQuantidade(item.id_produto, item.quantidade - 1)}
                                                        aria-label="Diminuir quantidade"
                                                    >
                                                        -
                                                    </button>
                                                    <span>{item.quantidade}</span>
                                                    <button
                                                        type="button"
                                                        onClick={() => atualizarQuantidade(item.id_produto, item.quantidade + 1)}
                                                        aria-label="Aumentar quantidade"
                                                    >
                                                        +
                                                    </button>
                                                </div>
                                                <button
                                                    type="button"
                                                    className="cart-item-remover"
                                                    onClick={() => removerItem(item.id_produto)}
                                                    title="Remover item"
                                                >
                                                    ✕
                                                </button>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>

                            <div className="cart-entrega-secao">
                                <h3>Como você quer receber?</h3>
                                <div className="cart-entrega-grid">
                                    <button
                                        type="button"
                                        className={`cart-entrega-card ${carrinho.orderType === "DELIVERY" ? "active" : ""}`}
                                        onClick={() => atualizarTipoPedido("DELIVERY")}
                                    >
                                        <div className="cart-entrega-radio">
                                            <div className="radio-circle"></div>
                                        </div>
                                        <div className="cart-entrega-textos">
                                            <strong>Receber em casa</strong>
                                            <small>Informe seu endereço na finalização</small>
                                        </div>
                                    </button>

                                    <button
                                        type="button"
                                        className={`cart-entrega-card ${carrinho.orderType === "PICKUP" ? "active" : ""}`}
                                        onClick={() => atualizarTipoPedido("PICKUP")}
                                    >
                                        <div className="cart-entrega-radio">
                                            <div className="radio-circle"></div>
                                        </div>
                                        <div className="cart-entrega-textos">
                                            <strong>Retirar na loja</strong>
                                            <small>Sem taxa · Pronto em 20–30 min</small>
                                        </div>
                                    </button>
                                </div>
                            </div>
                        </div>

                        <aside className="cart-col-resumo">
                            <div className="cart-resumo-card">
                                <h2>Resumo do pedido</h2>

                                <form className="cart-cupom-box" onSubmit={handleAplicarCupom}>
                                    <input
                                        type="text"
                                        placeholder="Cupom de desconto"
                                        value={cupom}
                                        onChange={(e) => setCupom(e.target.value)}
                                    />
                                    <button type="submit" className="btn-aplicar-cupom">
                                        Aplicar
                                    </button>
                                </form>
                                {mensagemCupom && (
                                    <small className={`cupom-feedback ${cupomAplicado ? "sucesso" : "erro"}`}>
                                        {mensagemCupom}
                                    </small>
                                )}

                                <div className="cart-resumo-linhas">
                                    <div className="resumo-linha">
                                        <span>Subtotal</span>
                                        <strong>{moeda.format(total)}</strong>
                                    </div>
                                    <div className="resumo-linha">
                                        <span>Taxa de entrega</span>
                                        <strong className="texto-verde">
                                            {carrinho.orderType === "PICKUP" ? "Grátis" : "Grátis"}
                                        </strong>
                                    </div>

                                    <div className="resumo-divisor"></div>

                                    <div className="resumo-linha resumo-total">
                                        <span>Total</span>
                                        <div className="resumo-total-valor">
                                            <strong>{moeda.format(total)}</strong>
                                            <small>Pagamento na próxima etapa</small>
                                        </div>
                                    </div>
                                </div>

                                <button
                                    type="button"
                                    className="primary-button cart-btn-checkout"
                                    onClick={handleIrParaPagamento}
                                >
                                    Ir para pagamento
                                </button>

                                <p className="cart-seguranca-aviso">
                                    🔒 Compra segura e protegida pelo Candyland
                                </p>
                            </div>
                        </aside>
                    </div>
                )}
            </main>
        </div>
    );
}

export default Cart;
