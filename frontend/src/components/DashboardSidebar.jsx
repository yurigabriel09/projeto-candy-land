import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const ITENS_NAV = [
    { chave: "home", rotulo: "🏠 Home", para: "/business" },
    { chave: "pedidos", rotulo: "🧾 Pedidos", para: "/business/pedidos" },
    { chave: "cardapio", rotulo: "📋 Cardápio", para: "/business/cardapio" },
    { chave: "financeiro", rotulo: "💰 Financeiro", para: "/business/financeiro" },
    { chave: "avaliacoes", rotulo: "⭐ Avaliações", para: "/business/avaliacoes" },
    { chave: "config", rotulo: "⚙️ Config", para: "/business/configuracao" },
];

function DashboardSidebar({ ativo, nomeLoja }) {
    const { sair } = useAuth();
    const navigate = useNavigate();

    function handleSair() {
        sair();
        window.location.replace("/");
    }

    return (
        <aside className="dashboard-sidebar">
            <Link to="/business" className="dashboard-marca">
                <span className="dashboard-marca-icone">🍰</span>
                <span className="dashboard-marca-texto">
                    <strong>{nomeLoja || "Minha loja"}</strong>
                    <small>Parceiro Candyland</small>
                </span>
            </Link>

            <nav className="dashboard-nav">
                {ITENS_NAV.map((item) => (
                    <button
                        key={item.chave}
                        type="button"
                        className={`dashboard-nav-item ${ativo === item.chave ? "active" : ""}`}
                        onClick={() => navigate(item.para)}
                        aria-current={ativo === item.chave ? "page" : undefined}
                    >
                        {item.rotulo}
                    </button>
                ))}
            </nav>

            <button className="dashboard-logout" onClick={handleSair}>
                ↪ Sair
            </button>
        </aside>
    );
}

export default DashboardSidebar;
