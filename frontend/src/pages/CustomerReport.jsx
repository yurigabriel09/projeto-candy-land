import { useCallback, useEffect, useState } from "react";
import Header from "../components/Header";
import { VisaoCliente } from "../components/RelatorioPartes";
import { getRelatorioCliente } from "../services/reportService";

function CustomerReport() {
    const [dados, setDados] = useState(null);
    const [carregando, setCarregando] = useState(true);
    const [erro, setErro] = useState("");

    const carregar = useCallback(async () => {
        setCarregando(true);
        setErro("");
        try {
            setDados(await getRelatorioCliente());
        } catch (error) {
            setErro(error.message || "Não foi possível carregar o seu relatório.");
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
            <main className="rl-pagina">
                <p className="pending-orders-eyebrow rl-no-print">MINHA CONTA</p>
                <div className="rl-pagina-topo">
                    <div>
                        <h1 className="titulo-secao">Meu relatório</h1>
                        <p>Resumo dos seus pedidos finalizados nos últimos 30 dias.</p>
                    </div>
                    <div className="rl-acoes rl-no-print">
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
                        <VisaoCliente dados={dados} />
                        <p className="rl-vazio">
                            Contam só os pedidos com status Finalizado.
                        </p>
                    </div>
                ) : null}
            </main>
        </>
    );
}

export default CustomerReport;
