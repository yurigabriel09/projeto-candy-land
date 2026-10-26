import DashboardSidebar from "../components/DashboardSidebar";
import { useAuth } from "../context/AuthContext";

function BusinessReviews() {
    const { dadosAutenticacao } = useAuth();
    return (
        <div className="dashboard-layout">
            <DashboardSidebar ativo="avaliacoes" nomeLoja={dadosAutenticacao?.nome_completo} />
            <div className="dashboard-content">
                <header className="dashboard-header"><div><h2>Avaliações</h2><p className="dashboard-subtitulo">Opiniões dos clientes</p></div></header>
                <main className="dashboard-body">
                    <div className="empty-state"><h3>Módulo de avaliações pendente</h3><p>A navegação está habilitada, mas o CandyLand ainda não possui entidade, API ou persistência de avaliações. Nenhuma avaliação fictícia será exibida.</p></div>
                </main>
            </div>
        </div>
    );
}
export default BusinessReviews;
