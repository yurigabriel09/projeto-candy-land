import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { maskPhone } from "../utils/masks";

function Login() {
    const [tipo, setTipo] = useState("email");
    const [valor, setValor] = useState("");
    const navigate = useNavigate();

    function handleSubmit(event) {
        event.preventDefault();

        if (!valor.trim()) {
            return;
        }

        console.log({
            tipo,
            valor
        });
    }

    return (
        <main className="auth-page">
            <section className="auth-card">
                <header className="auth-header">
                    <h1>CandyLand</h1>
                    <p>Seu pedido, do seu jeito.</p>
                </header>

                <div className="auth-content">
                    <h2>Entrar</h2>

                    <p className="auth-description">
                        Entre usando seu e-mail ou celular.
                    </p>

                    <div className="login-type">
                        <button
                            type="button"
                            className={tipo === "email" ? "active" : ""}
                            onClick={() => setTipo("email")}
                        >
                            E-mail
                        </button>

                        <button
                            type="button"
                            className={tipo === "phone" ? "active" : ""}
                            onClick={() => setTipo("phone")}
                        >
                            Celular
                        </button>
                    </div>

                    <form onSubmit={handleSubmit}>
                        <label htmlFor="login-value">
                            {tipo === "email" ? "E-mail" : "Celular"}
                        </label>

                        <input
                            id="login-value"
                            type={tipo === "email" ? "email" : "tel"}
                            placeholder={
                                tipo === "email"
                                    ? "seu@email.com"
                                    : "(11) 91234-5678"
                            }
                            value={valor}
                            onChange={(event) => {
                                const value =
                                    tipo === "phone"
                                        ? maskPhone(event.target.value)
                                        : event.target.value;

                                setValor(value);
                            }}
                        />

                        <button type="submit" className="primary-button">
                            Continuar
                        </button>
                    </form>

                    <div className="divider">
                        <span>ou</span>
                    </div>

                    <div className="social-login">
                        <button type="button" disabled>
                            Continuar com Google
                        </button>

                        <button type="button" disabled>
                            Continuar com Facebook
                        </button>
                    </div>

                    <p className="auth-footer">
                        Ainda não possui uma conta?
                        <button
                            type="button"
                            onClick={() => navigate("/register")}
                        >
                            Criar conta
                        </button>
                    </p>
                </div>
            </section>
        </main>
    );
}

export default Login;