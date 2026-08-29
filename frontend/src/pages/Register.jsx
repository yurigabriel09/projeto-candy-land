import { useNavigate } from "react-router-dom";

function Register() {
  const navigate = useNavigate();

  return (
    <main className="auth-page">
      <section className="auth-card">
        <header className="auth-header">
          <h1>CandyLand</h1>
          <p>Seu pedido, do seu jeito.</p>
        </header>

        <div className="auth-content">
          <h2>Criar conta</h2>

          <p className="auth-description">
            Escolha o tipo de conta que deseja criar.
          </p>

          <div className="register-options">
            <button
              type="button"
              onClick={() => navigate("/register/personal")}
            >
              <strong>Pessoa Física</strong>
              <span>
                Para pedir suas comidas favoritas.
              </span>
            </button>

            <button
              type="button"
              onClick={() => navigate("/register/business")}
            >
              <strong>Empresa</strong>
              <span>
                Para vender seus produtos e receber pedidos.
              </span>
            </button>
          </div>

          <p className="auth-footer">
            Já possui uma conta?
            <button
              type="button"
              onClick={() => navigate("/login")}
            >
              Entrar
            </button>
          </p>
        </div>
      </section>
    </main>
  );
}

export default Register;