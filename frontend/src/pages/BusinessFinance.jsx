import { useCallback, useEffect, useState } from "react";
import DashboardSidebar from "../components/DashboardSidebar";
import { VisaoLoja } from "../components/RelatorioPartes";
import { useAuth } from "../context/AuthContext";
import { getRelatorioLoja } from "../services/reportService";

function BusinessFinance() {
    const { dadosAutenticacao } = useAuth();
    const [dados, setDados] = useState(null);
    const [carregando, setCarregando] = useState(true);
    const [erro, setErro] = useState("");

    const carregar = useCallback(async () => {
        setCarregando(true);
        setErro("");
        try {
            setDados(await getRelatorioLoja());
        } catch (error) {
            setErro(error.message || "Não foi possível carregar o relatório da loja.");
        } finally {
            setCarregando(false);
        }
    }, []);

    useEffect(() => {
        carregar();
    }, [carregar]);

    return (
        <div className="dashboard-layout">
            <DashboardSidebar ativo="financeiro" nomeLoja={dadosAutenticacao?.nome_completo} />
            <div className="dashboard-content">
                <header className="dashboard-header rl-no-print">
                    <div>
                        <span className="rl-sobretitulo">CENTRAL DE RELATÓRIOS</span>
                        <h2>Relatório da loja</h2>
                        <p className="dashboard-subtitulo">Vendas, mais vendidos e alertas de estoque da sua loja</p>
                    </div>
                    <div className="rl-acoes">
                        <span className="rl-periodo">📅 Este mês</span>
                        <button className="btn-contorno" onClick={carregar} disabled={carregando}>
                            Atualizar
                        </button>
                        <button className="btn-principal" onClick={() => window.print()}>
                            🖨️ Imprimir
                        </button>
                    </div>
                </header>

                <main className="dashboard-body">
                    {erro && <p className="mensagem-erro" role="alert">{erro}</p>}
                    {carregando && !dados ? (
                        <p role="status">Carregando relatório...</p>
                    ) : dados ? (
                        <div className={carregando ? "rl-atualizando" : undefined}>
                            <VisaoLoja dados={dados} />
                        </div>
                    ) : null}
                </main>
            </div>
        </div>
    );
}

export default BusinessFinance;
