import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { parsePhoneNumberFromString } from "libphonenumber-js";
import PhoneInput from "../components/PhoneInput";
import { countries } from "../utils/countries";

const API_URL = "http://127.0.0.1:5000/auth";

function Login() {
    const { entrar } = useAuth();
    const [tipo, setTipo] = useState("email");
    const [valor, setValor] = useState("");
    const [codigo, setCodigo] = useState("");
    const [etapa, setEtapa] = useState("login");
    const [canalAtual, setCanalAtual] = useState("");
    const [tentativaId, setTentativaId] = useState("");
    const [dadosAutenticacao, setDadosAutenticacao] = useState({});
    const [loading, setLoading] = useState(false);
    const [erro, setErro] = useState("");
    const [mensagem, setMensagem] = useState("");
    const [pais, setPais] = useState("BR");
    const navigate = useNavigate();

    async function handleSubmit(event) {
        event.preventDefault();
        setErro("");
        setMensagem("");

        if (!valor.trim()) {
            setErro(tipo === "email" ? "Informe seu e-mail." : "Informe seu celular.");
            return;
        }

        setLoading(true);

        try {
            const canal = tipo === "email" ? "EMAIL" : "WHATSAPP";
            let valorFormatado = valor.trim().toLowerCase();

            if (tipo === "phone") {
                const country = countries.find((item) => item.code === pais);

                if (!country) {
                    setErro("Selecione um país.");
                    return;
                }

                const phone = parsePhoneNumberFromString(valor, country.code);

                if (!phone || !phone.isValid()) {
                    setErro("Informe um celular válido.");
                    return;
                }

                valorFormatado = phone.number;
            }

            const response = await fetch(`${API_URL}/login`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    canal,
                    valor: valorFormatado
                })
            });

            const resultado = await response.json();

            if (!response.ok) {
                throw new Error(resultado.erro || "Não foi possível enviar o código.");
            }

            setTentativaId(resultado.tentativa_id);
            setCanalAtual(canal);
            setDadosAutenticacao({
                [canal === "EMAIL" ? "email" : "telefone"]: valorFormatado
            });
            setCodigo("");
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
            setErro("Informe o código recebido.");
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
                    tentativa_id: tentativaId,
                    codigo: codigo.trim()
                })
            });

            const resultado = await response.json();

            if (!response.ok) {
                throw new Error(resultado.erro || "Código inválido.");
            }

            if (resultado.dados) {
                setDadosAutenticacao(resultado.dados);

                if (resultado.dados.token) {
                    entrar(resultado.dados);
                }
            }

            if (resultado.proximo_canal) {
                setCanalAtual(resultado.proximo_canal);
                setValor("");
                setCodigo("");
                setMensagem(resultado.mensagem);
                setEtapa("segundo-dado");
                return;
            }

            if (resultado.dados?.novo_cadastro) {
                navigate("/register", {
                    state: {
                        tentativaId: resultado.dados.tentativa_id || tentativaId,
                        email: resultado.dados.email,
                        telefone: resultado.dados.telefone
                    }
                });
                return;
            }

            if (resultado.dados?.tipo_conta === "PERSONAL") {
                navigate("/home");
                return;
            }

            if (resultado.dados?.tipo_conta === "BUSINESS") {
                navigate("/business");
                return;
            }
        } catch (error) {
            setErro(error.message);
        } finally {
            setLoading(false);
        }
    }

    async function handleSegundoDado(event) {
        event.preventDefault();
        setErro("");
        setMensagem("");

        if (!valor.trim()) {
            setErro(
                canalAtual === "EMAIL"
                    ? "Informe seu e-mail."
                    : "Informe seu celular."
            );
            return;
        }

        let valorFormatado = valor.trim().toLowerCase();

        if (canalAtual === "WHATSAPP") {
            const country = countries.find((item) => item.code === pais);

            if (!country) {
                setErro("Selecione um país.");
                return;
            }

            const phone = parsePhoneNumberFromString(valor, country.code);

            if (!phone || !phone.isValid()) {
                setErro("Informe um celular válido.");
                return;
            }

            valorFormatado = phone.number;
        }

        setLoading(true);

        try {
            const response = await fetch(`${API_URL}/second-code`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    tentativa_id: tentativaId,
                    valor: valorFormatado
                })
            });

            const resultado = await response.json();

            if (!response.ok) {
                throw new Error(
                    resultado.erro || "Não foi possível enviar o código."
                );
            }

            setDadosAutenticacao((dados) => ({
                ...dados,
                ...(canalAtual === "EMAIL"
                    ? { email: valorFormatado }
                    : { telefone: valorFormatado })
            }));

            setCodigo("");
            setMensagem(resultado.mensagem);
            setEtapa("codigo");
        } catch (error) {
            setErro(error.message);
        } finally {
            setLoading(false);
        }
    }

    function voltarParaLogin() {
        setEtapa("login");
        setCodigo("");
        setValor("");
        setTentativaId("");
        setCanalAtual("");
        setDadosAutenticacao({});
        setErro("");
        setMensagem("");
    }

    const nomeCanal = canalAtual === "EMAIL" ? "e-mail" : "WhatsApp";
    const segundoDado = canalAtual === "EMAIL" ? "seu e-mail" : "seu celular";

    return (
        <main className="auth-page">
            <section className="auth-card">
                <header className="auth-header">
                    <h1>CandyLand</h1>
                    <p>Seu pedido, do seu jeito.</p>
                </header>

                <div className="auth-content">
                    {etapa === "login" && (
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
                                        setMensagem("");
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
                                        setMensagem("");
                                    }}
                                >
                                    Celular
                                </button>
                            </div>

                            <form onSubmit={handleSubmit}>
                                <label htmlFor="login-value">
                                    {tipo === "email" ? "E-mail" : "Celular"}
                                </label>

                                {tipo === "email" ? (
                                    <input
                                        id="login-value"
                                        type="email"
                                        placeholder="seu@email.com"
                                        value={valor}
                                        onChange={(event) => setValor(event.target.value)}
                                    />
                                ) : (
                                    <PhoneInput
                                        value={valor}
                                        countryCode={pais}
                                        onChange={setValor}
                                        onCountryChange={setPais}
                                    />
                                )}

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
                    )}

                    {etapa === "segundo-dado" && (
                        <>
                            <h2>Agora vamos validar {segundoDado}</h2>

                            <p className="auth-description">
                                {mensagem}
                            </p>

                            <form onSubmit={handleSegundoDado}>
                                <label htmlFor="second-value">
                                    {canalAtual === "EMAIL" ? "E-mail" : "Celular"}
                                </label>

                                {canalAtual === "EMAIL" ? (
                                    <input
                                        id="second-value"
                                        type="email"
                                        placeholder="seu@email.com"
                                        value={valor}
                                        onChange={(event) => setValor(event.target.value)}
                                    />
                                ) : (
                                    <PhoneInput
                                        value={valor}
                                        countryCode={pais}
                                        onChange={setValor}
                                        onCountryChange={setPais}
                                    />
                                )}

                                {erro && (
                                    <p className="auth-error">{erro}</p>
                                )}

                                <button
                                    type="submit"
                                    className="primary-button"
                                    disabled={loading}
                                >
                                    {loading ? "Enviando..." : "Enviar código"}
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

                    {etapa === "codigo" && (
                        <>
                            <h2>Verifique seu {nomeCanal}</h2>

                            <p className="auth-description">
                                Digite o código que enviamos para:
                                <br />
                                <strong>
                                    {canalAtual === "EMAIL"
                                        ? dadosAutenticacao.email
                                        : dadosAutenticacao.telefone}
                                </strong>
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
                                    {loading ? "Validando..." : "Validar código"}
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