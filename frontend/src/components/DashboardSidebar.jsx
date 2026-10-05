import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const ITENS_NAV = [
    { chave: "home", rotulo: "🏠 Home", para: "/business" },
    { chave: "pedidos", rotulo: "🧾 Pedidos", disabled: true },
    { chave: "cardapio", rotulo: "📋 Cardápio", para: "/business/cardapio" },
    { chave: "financeiro", rotulo: "💰 Financeiro", disabled: true },
    { chave: "avaliacoes", rotulo: "⭐ Avaliações", disabled: true },
    { chave: "config", rotulo: "⚙️ Config", disabled: true },
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
                {ITENS_NAV.map((item) =>
                    item.disabled ? (
                        <button
                            key={item.chave}
                            className="dashboard-nav-item"
                            disabled
                            title="Em breve"
                        >
                            {item.rotulo}
                        </button>
                    ) : (
                        <button
                            key={item.chave}
                            className={`dashboard-nav-item ${ativo === item.chave ? "active" : ""}`}
                            onClick={() => navigate(item.para)}
                        >
                            {item.rotulo}
                        </button>
                    )
                )}
            </nav>

            <button className="dashboard-logout" onClick={handleSair}>
                ↪ Sair
            </button>
        </aside>
    );
}

export default DashboardSidebar;