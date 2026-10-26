import { useCallback, useEffect, useState } from "react";
import DashboardSidebar from "../components/DashboardSidebar";
import { useAuth } from "../context/AuthContext";
import { getOrders } from "../services/orderService";

const moeda = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const PAGOS = new Set(["PAGAMENTO_CONFIRMADO", "RESTAURANTE_RECEBEU", "RESTAURANTE_ACEITOU", "PROCESSANDO", "PRONTO_PARA_ENTREGA", "ENTREGUE", "FINALIZADO"]);

function BusinessFinance() {
    const { dadosAutenticacao } = useAuth();
    const [pedidos, setPedidos] = useState([]);
    const [erro, setErro] = useState("");
    const [carregando, setCarregando] = useState(true);
    const carregar = useCallback(async () => {
        setCarregando(true);
        setErro("");
        try { setPedidos(await getOrders()); }
        catch (error) { setErro(error.message || "Não foi possível consultar os valores."); }
        finally { setCarregando(false); }
    }, []);
    useEffect(() => { carregar(); }, [carregar]);

    const pagos = pedidos.filter((pedido) => PAGOS.has(pedido.status));
    const totalConfirmado = pagos.reduce((soma, pedido) => soma + Number(pedido.total || 0), 0);
    const aguardando = pedidos.filter((pedido) => pedido.status === "PENDENTE_PAGAMENTO");
    const totalPendente = aguardando.reduce((soma, pedido) => soma + Number(pedido.total || 0), 0);

    return (
        <div className="dashboard-layout">
            <DashboardSidebar ativo="financeiro" nomeLoja={dadosAutenticacao?.nome_completo} />
            <div className="dashboard-content">
                <header className="dashboard-header"><div><h2>Financeiro</h2><p className="dashboard-subtitulo">Resumo calculado a partir dos pedidos</p></div><button className="btn-contorno" onClick={carregar} disabled={carregando}>Atualizar</button></header>
                <main className="dashboard-body">
                    {erro && <p className="mensagem-erro" role="alert">{erro}</p>}
                    {carregando ? <p role="status">Calculando resumo...</p> : <>
                        <p className="cart-aviso-checkout">Este é um resumo de pedidos com pagamento confirmado, não um extrato de repasses ou tarifas do Mercado Pago.</p>
                        <div className="stats-grid">
                            <div className="stat-card"><span className="stat-valor">{moeda.format(totalConfirmado)}</span><span className="stat-rotulo">Pedidos com pagamento confirmado</span></div>
                            <div className="stat-card"><span className="stat-valor">{pagos.length}</span><span className="stat-rotulo">Pedidos confirmados</span></div>
                            <div className="stat-card"><span className="stat-valor">{moeda.format(totalPendente)}</span><span className="stat-rotulo">Aguardando pagamento</span></div>
                            <div className="stat-card"><span className="stat-valor">{pedidos.length}</span><span className="stat-rotulo">Total de pedidos</span></div>
                        </div>
                    </>}
                </main>
            </div>
        </div>
    );
}
export default BusinessFinance;
