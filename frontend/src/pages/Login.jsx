import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { maskPhone } from "../utils/masks";

const API_URL = "http://127.0.0.1:5000/auth";

function Login() {
    const [tipo, setTipo] = useState("email");
    const [valor, setValor] = useState("");
    const [codigo, setCodigo] = useState("");
    const [etapa, setEtapa] = useState("login");
    const [loading, setLoading] = useState(false);
    const [erro, setErro] = useState("");
    const [mensagem, setMensagem] = useState("");
    const navigate = useNavigate();

    async function handleSubmit(event) {
        event.preventDefault();
        setErro("");
        setMensagem("");

        if (!valor.trim()) {
            setErro("Informe seu e-mail.");
            return;
        }

        if (tipo !== "email") {
            setErro("Login por celular ainda não está disponível.");
            return;
        }

        setLoading(true);

        try {
            const response = await fetch(`${API_URL}/login`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    email: valor.trim().toLowerCase()
                })
            });

            const resultado = await response.json();

            if (!response.ok) {
                throw new Error(
                    resultado.erro || "Não foi possível enviar o código."
                );
            }

            setMensagem(resultado.mensagem);
            setEtapa("codigo");
        } catch (error) {
            setErro(error.message);
        } finally {
            setLoading(false);
        }
    }

    async function handleVerify(event) {
        event.preventDefault();
        setErro("");
        setMensagem("");

        if (!codigo.trim()) {
            setErro("Informe o código recebido por e-mail.");
            return;
        }

        setLoading(true);

        try {
            const response = await fetch(`${API_URL}/verify`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    email: valor.trim().toLowerCase(),
                    codigo: codigo.trim()
                })
            });

            const resultado = await response.json();

            if (!response.ok) {
                throw new Error(resultado.erro || "Código inválido.");
            }

            const { tipo_conta } = resultado.dados;

            if (tipo_conta === "PERSONAL") {
                navigate("/home");
                return;
            }

            if (tipo_conta === "BUSINESS") {
                navigate("/business");
                return;
            }
        } catch (error) {
            setErro(error.message);
        } finally {
            setLoading(false);
        }
    }

    function voltarParaLogin() {
        setEtapa("login");
        setCodigo("");
        setErro("");
        setMensagem("");
    }

    return (
        <main className="auth-page">
            <section className="auth-card">
                <header className="auth-header">
                    <h1>CandyLand</h1>
                    <p>Seu pedido, do seu jeito.</p>
                </header>

                <div className="auth-content">
                    {etapa === "login" ? (
                        <>
                            <h2>Entrar</h2>

                            <p className="auth-description">
                                Entre usando seu e-mail ou celular.
                            </p>

                            <div className="login-type">
                                <button
                                    type="button"
                                    className={tipo === "email" ? "active" : ""}
                                    onClick={() => {
                                        setTipo("email");
                                        setValor("");
                                        setErro("");
                                    }}
                                >
                                    E-mail
                                </button>

                                <button
                                    type="button"
                                    className={tipo === "phone" ? "active" : ""}
                                    onClick={() => {
                                        setTipo("phone");
                                        setValor("");
                                        setErro("");
                                    }}
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

                                {erro && (
                                    <p className="auth-error">{erro}</p>
                                )}

                                <button
                                    type="submit"
                                    className="primary-button"
                                    disabled={loading}
                                >
                                    {loading ? "Enviando..." : "Continuar"}
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
                        </>
                    ) : (
                        <>
                            <h2>Verifique seu e-mail</h2>

                            <p className="auth-description">
                                Digite o código que enviamos para:
                                <br />
                                <strong>{valor}</strong>
                            </p>

                            {mensagem && (
                                <p className="auth-success">{mensagem}</p>
                            )}

                            <form onSubmit={handleVerify}>
                                <label htmlFor="auth-code">Código</label>

                                <input
                                    id="auth-code"
                                    type="text"
                                    inputMode="numeric"
                                    maxLength="6"
                                    placeholder="000000"
                                    value={codigo}
                                    onChange={(event) =>
                                        setCodigo(
                                            event.target.value.replace(/\D/g, "")
                                        )
                                    }
                                />

                                {erro && (
                                    <p className="auth-error">{erro}</p>
                                )}

                                <button
                                    type="submit"
                                    className="primary-button"
                                    disabled={loading}
                                >
                                    {loading
                                        ? "Validando..."
                                        : "Validar código"}
                                </button>
                            </form>

                            <button
                                type="button"
                                className="auth-back"
                                onClick={voltarParaLogin}
                            >
                                Voltar
                            </button>
                        </>
                    )}
                </div>
            </section>
        </main>
    );
}

export default Login;