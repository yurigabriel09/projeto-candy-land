import { useCallback, useEffect, useState } from "react";
import Header from "../components/Header";
import { VisaoAdmin } from "../components/RelatorioPartes";
import { getRelatorioAdmin } from "../services/reportService";

function AdminReport() {
    const [dados, setDados] = useState(null);
    const [carregando, setCarregando] = useState(true);
    const [erro, setErro] = useState("");

    const carregar = useCallback(async () => {
        setCarregando(true);
        setErro("");
        try {
            setDados(await getRelatorioAdmin());
        } catch (error) {
            setErro(error.message || "Não foi possível carregar o relatório administrativo.");
        } finally {
            setCarregando(false);
        }
    }, []);

    useEffect(() => {
        carregar();
    }, [carregar]);

    return (
        <>
            <Header />
            <main className="rl-pagina rl-pagina-larga">
                <p className="pending-orders-eyebrow rl-no-print">ADMINISTRAÇÃO CANDYLAND</p>
                <div className="rl-pagina-topo">
                    <div>
                        <h1 className="titulo-secao">Relatório administrativo</h1>
                        <p>Visão geral da plataforma: faturamento, lojas e produtos que mais vendem.</p>
                    </div>
                    <div className="rl-acoes rl-no-print">
                        <span className="rl-periodo">📅 Este mês</span>
                        <button className="btn-contorno" onClick={carregar} disabled={carregando}>
                            Atualizar
                        </button>
                        <button className="btn-principal" onClick={() => window.print()}>
                            🖨️ Imprimir
                        </button>
                    </div>
                </div>
                {erro && <p className="mensagem-erro" role="alert">{erro}</p>}
                {carregando && !dados ? (
                    <p role="status">Carregando relatório...</p>
                ) : dados ? (
                    <div className={carregando ? "rl-atualizando" : undefined}>
                        <VisaoAdmin dados={dados} />
                    </div>
                ) : null}
            </main>
        </>
    );
}

export default AdminReport;
