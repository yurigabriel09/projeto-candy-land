import { useNavigate } from "react-router-dom";

function BusinessHome() {
    const navigate = useNavigate();

    return (
        <main className="auth-page">
            <section className="auth-card">
                <header className="auth-header">
                    <h1>CandyLand</h1>
                    <p>Seu pedido, do seu jeito.</p>
                </header>

                <div className="auth-content">
                    <h2>Login realizado! 🎉</h2>

                    <p className="auth-description">
                        Você entrou como <strong>empresa</strong>.
                    </p>

                    <button
                        type="button"
                        className="primary-button"
                        onClick={() => navigate("/login")}
                    >
                        Voltar para o login
                    </button>
                </div>
            </section>
        </main>
    );
}

export default BusinessHome;