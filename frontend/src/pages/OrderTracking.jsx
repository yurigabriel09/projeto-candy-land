import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import Header from "../components/Header";
import LocationMap from "../components/LocationMap";
import { getOrder } from "../services/orderService";

const STATUS_PEDIDO = {
    PENDENTE_PAGAMENTO: "Aguardando pagamento",
    PAGAMENTO_CONFIRMADO: "Pagamento confirmado",
    RESTAURANTE_RECEBEU: "Pedido recebido pelo restaurante",
    RESTAURANTE_ACEITOU: "Pedido aceito",
    PROCESSANDO: "Preparando seu pedido",
    PRONTO_PARA_ENTREGA: "Pedido pronto para entrega",
    ENTREGUE: "Entrega concluída",
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

function OrderTracking() {
    const { orderId } = useParams();
    const [pedido, setPedido] = useState(null);
    const [erro, setErro] = useState("");
    const [carregando, setCarregando] = useState(true);
    const [ultimaAtualizacao, setUltimaAtualizacao] = useState(null);

    const atualizar = useCallback(async (inicial = false) => {
        if (inicial) setCarregando(true);
        setErro("");
        try {
            const dados = await getOrder(orderId);
            setPedido(dados);
            setUltimaAtualizacao(new Date());
        } catch (error) {
            setErro(error.message || "Não foi possível consultar o pedido.");
        } finally {
            if (inicial) setCarregando(false);
        }
    }, [orderId]);

    useEffect(() => {
        let ativo = true;
        const carregar = async (inicial = false) => {
            if (inicial) setCarregando(true);
            setErro("");
            try {
                const dados = await getOrder(orderId);
                if (ativo) {
                    setPedido(dados);
                    setUltimaAtualizacao(new Date());
                }
            } catch (error) {
                if (ativo) setErro(error.message || "Não foi possível consultar o pedido.");
            } finally {
                if (ativo && inicial) setCarregando(false);
            }
        };
        carregar(true);
        const timer = window.setInterval(() => carregar(false), 10000);
        return () => { ativo = false; window.clearInterval(timer); };
    }, [orderId]);

    const local = pedido?.delivery_location;
    const temCoordenadas = local?.latitude != null && local?.longitude != null;
    const pedidoTerminal = ["ENTREGUE", "FINALIZADO", "CANCELADO"].includes(pedido?.status);

    return (
        <>
            <Header />
            <main className="container secao order-tracking-page">
                <div className="order-tracking-heading">
                    <div>
                        <p className="conta-eyebrow">CANDYLAND · ACOMPANHAMENTO</p>
                        <h1 className="titulo-secao">Acompanhar pedido</h1>
                    </div>
                    <button type="button" className="btn-contorno" disabled={carregando} onClick={() => atualizar(true)}>Atualizar status</button>
                </div>
                {carregando && !pedido && <p role="status">Carregando pedido...</p>}
                {erro && <p className="cart-checkout-erro" role="alert">{erro}</p>}
                {pedido && (
                    <div className="order-tracking-grid">
                        <section className="cart-pedido-sucesso">
                            <p>Pedido <strong>{pedido.order_code}</strong></p>
                            <div className="order-tracking-status">
                                <span className="business-order-status">{STATUS_PEDIDO[pedido.status] || pedido.status}</span>
                            </div>
                            <dl>
                                <div><dt>Modalidade</dt><dd>{pedido.order_type === "PICKUP" ? "Retirada no restaurante" : "Entrega no endereço"}</dd></div>
                                <div><dt>Pagamento</dt><dd>{pedido.status === "PENDENTE_PAGAMENTO" ? "Pendente" : "Registrado no fluxo do pedido"}</dd></div>
                                {pedido.entrega && <div><dt>Status da entrega</dt><dd>{STATUS_ENTREGA[pedido.entrega.status] || pedido.entrega.status}</dd></div>}
                                <div><dt>Total</dt><dd><strong>{new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(pedido.total || 0)}</strong></dd></div>
                            </dl>
                            {ultimaAtualizacao && <small>Atualizado às {ultimaAtualizacao.toLocaleTimeString("pt-BR")}. Esta tela consulta o status a cada 10 segundos.</small>}
                            {pedidoTerminal && <p className="field-message">Este pedido chegou a um status final.</p>}
                            {pedido.order_type === "DELIVERY" && <p className="cart-aviso-checkout">O mapa mostra o endereço de entrega. A posição GPS do entregador em tempo real ainda depende da integração do aplicativo/logística.</p>}
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
