import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { GoogleLogin } from "@react-oauth/google";
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
    const [socialProvider, setSocialProvider] = useState("");
    const [socialCredential, setSocialCredential] = useState("");
    const [socialTicket, setSocialTicket] = useState("");
    const navigate = useNavigate();

    useEffect(() => {
        const parametros = new URLSearchParams(window.location.search);

        const facebookTicket = parametros.get("facebook_ticket");
        const facebookError = parametros.get("facebook_error");

        if (facebookError) {
            setErro(facebookError);
            window.history.replaceState({}, document.title, "/login");
            return;
        }

        if (facebookTicket) {
            window.history.replaceState({}, document.title, "/login");
            handleFacebookLogin(facebookTicket);
        }
    }, []);

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

    async function handleGoogleLogin(credential, telefone = null) {
        setErro("");
        setMensagem("");
        setLoading(true);

        try {
            const response = await fetch(`${API_URL}/google`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    credential,
                    ...(telefone ? { telefone } : {})
                })
            });

            const resultado = await response.json();

            /*
             * O Google validou a identidade, mas ainda precisamos
             * do celular para continuar o fluxo.
             */
            if (resultado.precisa_telefone) {
                setSocialProvider("GOOGLE");
                setSocialCredential(credential);

                setDadosAutenticacao(resultado);
                setEtapa("segundo-dado");
                setCanalAtual("WHATSAPP");
                setTentativaId(resultado.tentativa_id || "");
                setValor("");
                setMensagem("Informe seu celular para continuar.");

                return;
            }

            if (!response.ok) {
                throw new Error(
                    resultado.erro ||
                    "Não foi possível entrar com o Google."
                );
            }

            setSocialProvider("GOOGLE");
            setSocialCredential(credential);

            setDadosAutenticacao(resultado);
            setTentativaId(resultado.tentativa_id || "");

            if (resultado.mensagem) {
                setMensagem(resultado.mensagem);
            }

            if (resultado.dados?.token) {
                entrar(resultado.dados);
            }

            /*
             * Depois que o celular foi informado, o backend
             * criou a tentativa e enviou o código.
             */
            if (resultado.proximo_canal === "WHATSAPP") {
                setCanalAtual("WHATSAPP");
                setValor(resultado.telefone || telefone || "");
                setEtapa("codigo");
                return;
            }

            if (resultado.dados?.novo_cadastro) {
                navigate("/register", {
                    state: {
                        tentativaId:
                            resultado.dados.tentativa_id ||
                            resultado.tentativa_id,
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
            }

        } catch (error) {
            setErro(error.message);
        } finally {
            setLoading(false);
        }
    }

    async function handleFacebookLogin(ticket, telefone = null) {
        setErro("");
        setMensagem("");
        setLoading(true);

        try {
            const response = await fetch(`${API_URL}/facebook/complete`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    ticket,
                    ...(telefone ? { telefone } : {})
                })
            });

            const resultado = await response.json();

            if (resultado.precisa_telefone) {
                setSocialProvider("FACEBOOK");
                setSocialTicket(ticket);
                setDadosAutenticacao(resultado);
                setEtapa("segundo-dado");
                setCanalAtual("WHATSAPP");
                setTentativaId("");
                setValor("");
                setMensagem(
                    "Informe seu celular para continuar."
                );
                return;
            }

            if (!response.ok) {
                throw new Error(
                    resultado.erro ||
                    "Não foi possível entrar com o Facebook."
                );
            }

            setDadosAutenticacao(resultado);
            setTentativaId(resultado.tentativa_id || "");

            if (resultado.mensagem) {
                setMensagem(resultado.mensagem);
            }

            if (resultado.proximo_canal === "WHATSAPP") {
                setCanalAtual("WHATSAPP");
                setValor(resultado.telefone || "");
                setEtapa("codigo");
                return;
            }

            if (resultado.dados?.token) {
                entrar(resultado.dados);
            }

            if (resultado.dados?.novo_cadastro) {
                navigate("/register", {
                    state: {
                        tentativaId:
                            resultado.dados.tentativa_id ||
                            resultado.tentativa_id,
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
            const country = countries.find(
                (item) => item.code === pais
            );

            if (!country) {
                setErro("Selecione um país.");
                return;
            }

            const phone = parsePhoneNumberFromString(
                valor,
                country.code
            );

            if (!phone || !phone.isValid()) {
                setErro("Informe um celular válido.");
                return;
            }

            valorFormatado = phone.number;
        }

        /*
         * Fluxo social:
         *
         * Google -> celular -> código
         * Facebook -> celular -> código
         *
         * O segundo dado NÃO usa /second-code.
         * Ele precisa voltar ao endpoint do provedor
         * para criar a tentativa de autenticação.
         */
        if (socialProvider === "GOOGLE") {
            await handleGoogleLogin(
                socialCredential,
                valorFormatado
            );
            return;
        }

        if (socialProvider === "FACEBOOK") {
            await handleFacebookLogin(
                socialTicket,
                valorFormatado
            );
            return;
        }

        /*
         * Fluxo normal:
         *
         * E-mail/celular -> primeiro código -> segundo canal.
         */
        if (!tentativaId) {
            setErro("Não foi possível continuar a autenticação.");
            return;
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
                    resultado.erro ||
                    "Não foi possível enviar o código."
                );
            }

            setTentativaId(resultado.tentativa_id || tentativaId);
            setDadosAutenticacao(resultado);
            setCanalAtual(resultado.proximo_canal || canalAtual);
            setValor(
                resultado.telefone ||
                resultado.email ||
                valorFormatado
            );
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
        setSocialProvider("");
        setSocialCredential("");
        setSocialTicket("");
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
                                <div className="social-button google-button">
                                    <div className="google-login">
                                        <GoogleLogin
                                            onSuccess={(credentialResponse) =>
                                                handleGoogleLogin(credentialResponse.credential)
                                            }
                                            onError={() => setErro("Não foi possível entrar com o Google.")}
                                            size="large"
                                            shape="pill"
                                            width="358"
                                        />
                                    </div>
                                </div>

                                <button
                                    type="button"
                                    className="facebook-button"
                                    onClick={() => window.location.assign(`${API_URL}/facebook`)}
                                    disabled={loading}
                                >
                                    <svg
                                        className="facebook-icon"
                                        viewBox="0 0 24 24"
                                        aria-hidden="true"
                                    >
                                        <path
                                            d="M13.5 21v-8h2.7l.4-3h-3.1V8.1c0-.9.3-1.5 1.6-1.5h1.7V4a22 22 0 0 0-2.5-.1c-2.5 0-4.2 1.5-4.2 4.2V10H7.5v3h2.6v8h3.4z"
                                            fill="currentColor"
                                        />
                                    </svg>

                                    <span>Continuar com Facebook</span>
                                </button>
                            </div>
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