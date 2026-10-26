import { useCallback, useEffect, useState } from "react";
import DashboardSidebar from "../components/DashboardSidebar";
import { useAuth } from "../context/AuthContext";
import { getOrders, updateOrderStatus } from "../services/orderService";

const LABEL = {
    PENDENTE_PAGAMENTO: "Aguardando pagamento",
    PAGAMENTO_CONFIRMADO: "Pagamento confirmado",
    RESTAURANTE_RECEBEU: "Pedido recebido",
    RESTAURANTE_ACEITOU: "Aceito pelo restaurante",
    PROCESSANDO: "Em preparo",
    PRONTO_PARA_ENTREGA: "Pronto para entrega/retirada",
    ENTREGUE: "Entregue",
    FINALIZADO: "Finalizado",
    CANCELADO: "Cancelado",
};
const PROXIMO_STATUS = {
    PAGAMENTO_CONFIRMADO: ["RESTAURANTE_RECEBEU"],
    RESTAURANTE_RECEBEU: ["RESTAURANTE_ACEITOU"],
    RESTAURANTE_ACEITOU: ["PROCESSANDO"],
    PROCESSANDO: ["PRONTO_PARA_ENTREGA"],
};
const moeda = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });

function BusinessOrders() {
    const { dadosAutenticacao } = useAuth();
    const [pedidos, setPedidos] = useState([]);
    const [carregando, setCarregando] = useState(true);
    const [erro, setErro] = useState("");
    const [atualizando, setAtualizando] = useState(null);

    const carregar = useCallback(async () => {
        setCarregando(true);
        setErro("");
        try { setPedidos(await getOrders()); }
        catch (error) { setErro(error.message || "Não foi possível carregar os pedidos."); }
        finally { setCarregando(false); }
    }, []);

    useEffect(() => { carregar(); }, [carregar]);

    async function mudarStatus(pedidoId, status) {
        setAtualizando(pedidoId);
        setErro("");
        try {
            await updateOrderStatus(pedidoId, status);
            await carregar();
        } catch (error) {
            setErro(error.message || "Não foi possível atualizar o pedido.");
        } finally { setAtualizando(null); }
    }

    return (
        <div className="dashboard-layout">
            <DashboardSidebar ativo="pedidos" nomeLoja={dadosAutenticacao?.nome_completo} />
            <div className="dashboard-content">
                <header className="dashboard-header">
                    <div><h2>Pedidos</h2><p className="dashboard-subtitulo">Pedidos vinculados ao seu restaurante</p></div>
                    <button className="btn-contorno" type="button" onClick={carregar} disabled={carregando}>Atualizar</button>
                </header>
                <main className="dashboard-body">
                    {erro && <p className="mensagem-erro" role="alert">{erro}</p>}
                    {carregando ? <p role="status">Carregando pedidos...</p> : pedidos.length === 0 ? (
                        <div className="empty-state"><h3>Nenhum pedido encontrado</h3><p>Os pedidos aparecerão aqui depois que um cliente concluir o checkout.</p></div>
                    ) : (
                        <div className="business-orders-list">
                            {pedidos.map((pedido) => {
                                const prox = PROXIMO_STATUS[pedido.status] || [];
                                const podeCancelar = !["PENDENTE_PAGAMENTO", "ENTREGUE", "FINALIZADO", "CANCELADO"].includes(pedido.status);
                                return (
                                    <article className="business-order-card" key={pedido.id}>
                                        <header><div><strong>{pedido.order_code}</strong><small>{pedido.created_at ? new Date(pedido.created_at).toLocaleString("pt-BR") : "Data indisponível"}</small></div><span className="business-order-status">{LABEL[pedido.status] || pedido.status}</span></header>
                                        <div className="business-order-meta"><span>{pedido.order_type === "PICKUP" ? "Retirada" : "Entrega"}</span><span>Pagamento: {pedido.payment_method}</span><strong>{moeda.format(pedido.total || 0)}</strong></div>
                                        <ul>{(pedido.items || []).map((item) => <li key={item.id}>Produto #{item.produto_id} × {item.quantidade} — {moeda.format((item.preco_unitario || 0) * (item.quantidade || 0))}</li>)}</ul>
                                        {pedido.status === "PENDENTE_PAGAMENTO" && <p className="cart-aviso-checkout">Não inicie o preparo antes da confirmação do pagamento.</p>}
                                        <footer>
                                            {prox.map((status) => <button key={status} className="btn-principal" type="button" disabled={atualizando === pedido.id} onClick={() => mudarStatus(pedido.id, status)}>{atualizando === pedido.id ? "Salvando..." : `Marcar: ${LABEL[status]}`}</button>)}
                                            {podeCancelar && <button className="btn-contorno" type="button" disabled={atualizando === pedido.id} onClick={() => mudarStatus(pedido.id, "CANCELADO")}>Cancelar pedido</button>}
                                        </footer>
                                    </article>
                                );
                            })}
                        </div>
                    )}
                </main>
            </div>
        </div>
    );
}
export default BusinessOrders;
