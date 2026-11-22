import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import Header from "../components/Header";
import "./OrderTracking.css";
import LocationMap from "../components/LocationMap";
import { getOrder } from "../services/orderService";

const moeda = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const INTERVALO_MS = 10000;

const STATUS_PEDIDO = {
    PENDENTE_PAGAMENTO: "Aguardando pagamento",
    PAGAMENTO_CONFIRMADO: "Pagamento confirmado",
    RESTAURANTE_RECEBEU: "Pedido recebido pelo restaurante",
    RESTAURANTE_ACEITOU: "Pedido aceito",
    PROCESSANDO: "Preparando seu pedido",
    PRONTO_PARA_ENTREGA: "Pedido pronto",
    ENTREGUE: "Pedido entregue",
    FINALIZADO: "Pedido finalizado",
    CANCELADO: "Pedido cancelado",
};
const STATUS_ENTREGA = {
    NAO_SOLICITADO: "Aguardando início da entrega",
    PROCURANDO: "Procurando entregador",
    MOTORISTA_ENCONTRADO: "Entregador encontrado",
    MOTORISTA_A_CAMINHO: "Entregador a caminho do restaurante",
    MOTORISTA_NO_RESTAURANTE: "Entregador no restaurante",
    PEDIDO_RETIRADO: "Pedido retirado para entrega",
    EM_ROTA: "Pedido em rota de entrega",
    ENTREGA_CONCLUIDA: "Entrega concluída",
    SEM_MOTORISTA: "Ainda não foi possível encontrar entregador",
    CANCELADO: "Entrega cancelada",
};

// Etapas da linha do tempo, na ordem em que o pedido avança.
const ETAPAS = [
    { status: "PAGAMENTO_CONFIRMADO", titulo: "Pagamento confirmado", icone: "💳" },
    { status: "RESTAURANTE_RECEBEU", titulo: "Restaurante recebeu", icone: "🏪" },
    { status: "RESTAURANTE_ACEITOU", titulo: "Pedido aceito", icone: "👍" },
    { status: "PROCESSANDO", titulo: "Em preparo", icone: "🧁" },
    { status: "PRONTO_PARA_ENTREGA", titulo: "Pedido pronto", icone: "📦", tituloRetirada: "Pronto para retirada" },
    { status: "ENTREGUE", titulo: "Entregue", icone: "🎉", tituloRetirada: "Retirado" },
];
const STATUS_FINAIS = ["ENTREGUE", "FINALIZADO", "CANCELADO"];

function indiceDaEtapa(status) {
    if (status === "FINALIZADO") return ETAPAS.length - 1;
    return ETAPAS.findIndex((e) => e.status === status);
}

function nomeDoItem(item) {
    return item?.nome || item?.produto_nome || item?.name || item?.produto?.nome || "";
}

function LinhaDoTempo({ pedido }) {
    const retirada = pedido.order_type === "PICKUP";
    const atual = indiceDaEtapa(pedido.status);
    const concluido = pedido.status === "ENTREGUE" || pedido.status === "FINALIZADO";
    const aguardandoPagamento = pedido.status === "PENDENTE_PAGAMENTO";
    const statusEntrega = pedido.entrega?.status;

    return (
        <ol className="track-timeline" aria-label="Etapas do pedido">
            {ETAPAS.map((etapa, i) => {
                let estado = "pendente";
                if (concluido || i < atual) estado = "feito";
                else if (i === atual) estado = "atual";
                else if (aguardandoPagamento && i === 0) estado = "atual";
                const titulo = retirada && etapa.tituloRetirada ? etapa.tituloRetirada : etapa.titulo;
                const mostrarEntrega = !retirada && estado === "atual" && statusEntrega
                    && ["PRONTO_PARA_ENTREGA", "ENTREGUE"].includes(etapa.status) && STATUS_ENTREGA[statusEntrega];
                return (
                    <li key={etapa.status} className={`track-etapa track-${estado}`} aria-current={estado === "atual" ? "step" : undefined}>
                        <span className="track-bolinha" aria-hidden="true">{estado === "feito" ? "✓" : etapa.icone}</span>
                        <div className="track-texto">
                            <strong>{aguardandoPagamento && i === 0 ? "Aguardando pagamento" : titulo}</strong>
                            {estado === "atual" && <small>Etapa atual</small>}
                            {mostrarEntrega && <small>{STATUS_ENTREGA[statusEntrega]}</small>}
                        </div>
                    </li>
                );
            })}
        </ol>
    );
}

function OrderTracking() {
    const { orderId } = useParams();
    const [pedido, setPedido] = useState(null);
    const [erro, setErro] = useState("");
    const [carregando, setCarregando] = useState(true);
    const [atualizando, setAtualizando] = useState(false);
    const [ultimaAtualizacao, setUltimaAtualizacao] = useState(null);

    const carregar = useCallback(async ({ inicial = false, manual = false } = {}) => {
        if (inicial) setCarregando(true);
        if (manual) setAtualizando(true);
        try {
            const dados = await getOrder(orderId);
            setPedido(dados);
            setUltimaAtualizacao(new Date());
            setErro("");
        } catch (error) {
            setErro(error.message || "Não foi possível consultar o pedido.");
        } finally {
            if (inicial) setCarregando(false);
            if (manual) setAtualizando(false);
        }
    }, [orderId]);

    useEffect(() => { carregar({ inicial: true }); }, [carregar]);

    // Consulta automática, parando quando o pedido chega a um status final.
    const pedidoTerminal = STATUS_FINAIS.includes(pedido?.status);
    useEffect(() => {
        if (!pedido || pedidoTerminal) return undefined;
        const timer = window.setInterval(() => carregar(), INTERVALO_MS);
        return () => window.clearInterval(timer);
    }, [pedido, pedidoTerminal, carregar]);

    const local = pedido?.delivery_location;
    const temCoordenadas = local?.latitude != null && local?.longitude != null;
    const cancelado = pedido?.status === "CANCELADO";
    const itens = (pedido?.itens || pedido?.items || []).filter((i) => nomeDoItem(i));

    return (
        <>
            <Header />
            <main className="container secao order-tracking-page">
                <div className="order-tracking-heading">
                    <div>
                        <p className="conta-eyebrow">CANDYLAND · ACOMPANHAMENTO</p>
                        <h1 className="titulo-secao">Acompanhar pedido</h1>
                    </div>
                    <button type="button" className="btn-contorno" disabled={carregando || atualizando} onClick={() => carregar({ manual: true })}>
                        {atualizando ? "Atualizando..." : "Atualizar status"}
                    </button>
                </div>
                {carregando && !pedido && <p role="status">Carregando pedido...</p>}
                {erro && <p className="cart-checkout-erro" role="alert">{erro}</p>}
                {pedido && (
                    <div className="order-tracking-grid">
                        <section className="cart-pedido-sucesso">
                            <p>Pedido <strong>{pedido.order_code}</strong></p>
                            <div className="order-tracking-status">
                                <span className={`business-order-status ${cancelado ? "track-status-cancelado" : ""}`}>
                                    {STATUS_PEDIDO[pedido.status] || pedido.status}
                                </span>
                            </div>

                            {cancelado ? (
                                <p className="cart-checkout-erro">Este pedido foi cancelado. Se precisar de ajuda, fale com o restaurante.</p>
                            ) : (
                                <LinhaDoTempo pedido={pedido} />
                            )}

                            {pedido.status === "PENDENTE_PAGAMENTO" && (
                                <p className="cart-aviso-checkout">
                                    O restaurante só recebe o pedido depois da confirmação do pagamento.{" "}
                                    <Link to="/minha-conta/historico-compras">Ver meus pedidos</Link>
                                </p>
                            )}

                            <dl className="track-resumo">
                                <div><dt>Modalidade</dt><dd>{pedido.order_type === "PICKUP" ? "Retirada no restaurante" : "Entrega no endereço"}</dd></div>
                                <div><dt>Pagamento</dt><dd>{pedido.status === "PENDENTE_PAGAMENTO" ? "Pendente" : cancelado ? "Pedido cancelado" : "Confirmado"}</dd></div>
                                {pedido.entrega && <div><dt>Status da entrega</dt><dd>{STATUS_ENTREGA[pedido.entrega.status] || pedido.entrega.status}</dd></div>}
                                <div className="track-resumo-total"><dt>Total</dt><dd><strong>{moeda.format(pedido.total || 0)}</strong></dd></div>
                            </dl>

                            {itens.length > 0 && (
                                <div className="track-itens">
                                    <h2>Itens do pedido</h2>
                                    <ul>
                                        {itens.map((item, i) => (
                                            <li key={item.id ?? i}>
                                                <span>{item.quantidade ?? item.quantity ?? 1}x {nomeDoItem(item)}</span>
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}

                            {ultimaAtualizacao && (
                                <small>
                                    Atualizado às {ultimaAtualizacao.toLocaleTimeString("pt-BR")}.{" "}
                                    {pedidoTerminal ? "Este pedido chegou a um status final." : "Esta tela consulta o status a cada 10 segundos."}
                                </small>
                            )}
                            {pedido.order_type === "DELIVERY" && !pedidoTerminal && (
                                <p className="cart-aviso-checkout">O mapa mostra o endereço de entrega. A posição GPS do entregador em tempo real ainda depende da integração do aplicativo/logística.</p>
                            )}
                            <div className="checkout-result-actions">
                                <Link to="/home" className="btn-contorno">Voltar às lojas</Link>
                                <Link to="/cart" className="btn-principal">Novo pedido</Link>
                            </div>
                        </section>
                        {pedido.order_type === "DELIVERY" && (
                            <section className="order-tracking-map-card">
                                <h2>Local de entrega</h2>
                                {temCoordenadas ? (
                                    <LocationMap latitude={local.latitude} longitude={local.longitude} label={local.endereco || "Endereço de entrega"} height={360} />
                                ) : (
                                    <div className="location-map location-map-empty"><span className="location-map-empty-icon" aria-hidden="true">📍</span><p>Este pedido não possui coordenadas de entrega válidas. Abra o checkout e localize o endereço antes de criar um novo pedido.</p></div>
                                )}
                                {pedido.restaurant_location?.latitude != null && pedido.restaurant_location?.longitude != null && (
                                    <p className="cart-aviso-checkout">A doceria possui localização cadastrada. A rota por ruas não é exibida nesta versão; a taxa foi calculada por distância em linha reta.</p>
                                )}
                            </section>
                        )}
                    </div>
                )}
            </main>
        </>
    );
}

export default OrderTracking;