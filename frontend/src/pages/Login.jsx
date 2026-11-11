import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

function Login({ audiencia = "PERSONAL" }) {
    const isBusiness = audiencia === "BUSINESS";
    
    // Estados do fluxo 2FA: "EMAIL" | "CODIGO_EMAIL" | "CELULAR" | "CODIGO_CELULAR"
    const [etapa, setEtapa] = useState("EMAIL");
    const [email, setEmail] = useState("");
    const [celular, setCelular] = useState("");
    const [codigo, setCodigo] = useState("");
    const [tentativaId, setTentativaId] = useState(null);
    const [erro, setErro] = useState("");
    const [carregando, setCarregando] = useState(false);

    const navigate = useNavigate();
    const { iniciarLogin } = useAuth();
    const apiBase = import.meta.env.VITE_API_URL || "http://127.0.0.1:5000";

    // 1. Enviar e-mail para receber o 1º código
    async function handleEnviarEmail(e) {
        e.preventDefault();
        setErro("");

        if (!email.trim() || !email.includes("@")) {
            setErro("Informe um e-mail válido.");
            return;
        }

        setCarregando(true);
        try {
            const resposta = await fetch(`${apiBase}/auth/login`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    canal: "EMAIL",
                    valor: email.trim(),
                    audiencia: audiencia
                })
            });

            const dados = await resposta.json();
            if (!resposta.ok) throw new Error(dados.erro || "Erro ao solicitar código.");

            setTentativaId(dados.tentativa_id);
            setEtapa("CODIGO_EMAIL");
        } catch (err) {
            setErro(err.message || "Falha ao conectar com o servidor.");
        } finally {
            setCarregando(false);
        }
    }

    // 2. Validar código recebido no E-mail
    async function handleVerificarCodigoEmail(e) {
        e.preventDefault();
        setErro("");

        if (!codigo.trim()) {
            setErro("Digite o código recebido no e-mail.");
            return;
        }

        setCarregando(true);
        try {
            const resposta = await fetch(`${apiBase}/auth/verify`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    tentativa_id: tentativaId,
                    codigo: codigo.trim(),
                    tipo_conta: audiencia
                })
            });

            const dados = await resposta.json();
            if (!resposta.ok) throw new Error(dados.erro || "Código inválido ou expirado.");

            setCodigo(""); // Limpa o input para o próximo código

            // Caso o backend já retorne autenticado (ex: usuário em ambiente dev)
            if (dados.dados) {
                concluirSessao(dados.dados);
                return;
            }

            // Se o próximo canal for WHATSAPP, avança para pedir o celular
            if (dados.proximo_canal === "WHATSAPP") {
                setEtapa("CELULAR");
            }
        } catch (err) {
            setErro(err.message || "Falha ao validar código do e-mail.");
        } finally {
            setCarregando(false);
        }
    }

    // 3. Enviar celular/WhatsApp para receber o 2º código
    async function handleEnviarCelular(e) {
        e.preventDefault();
        setErro("");

        if (!celular.trim()) {
            setErro("Informe o número de celular/WhatsApp.");
            return;
        }

        setCarregando(true);
        try {
            const resposta = await fetch(`${apiBase}/auth/second-code`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    tentativa_id: tentativaId,
                    valor: celular.trim()
                })
            });

            const dados = await resposta.json();
            if (!resposta.ok) throw new Error(dados.erro || "Erro ao enviar código para o WhatsApp.");

            setEtapa("CODIGO_CELULAR");
        } catch (err) {
            setErro(err.message || "Falha ao enviar código para o WhatsApp.");
        } finally {
            setCarregando(false);
        }
    }

    // 4. Validar 2º código recebido no WhatsApp e finalizar login
    async function handleVerificarCodigoCelular(e) {
        e.preventDefault();
        setErro("");

        if (!codigo.trim()) {
            setErro("Digite o código recebido no WhatsApp.");
            return;
        }

        setCarregando(true);
        try {
            const resposta = await fetch(`${apiBase}/auth/verify`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    tentativa_id: tentativaId,
                    codigo: codigo.trim(),
                    tipo_conta: audiencia
                })
            });

            const dados = await resposta.json();
            if (!resposta.ok) throw new Error(dados.erro || "Código do WhatsApp inválido.");

            if (dados.dados) {
                concluirSessao(dados.dados);
            } else {
                throw new Error("Não foi possível obter os dados de autenticação.");
            }
        } catch (err) {
            setErro(err.message || "Falha ao validar código do WhatsApp.");
        } finally {
            setCarregando(false);
        }
    }

    // Gravação da sessão e redirecionamento final
    function concluirSessao(dadosConta) {
        if (dadosConta.novo_cadastro) {
            const destino = isBusiness ? "/register/business" : "/register/personal";
            navigate(destino, { state: { email: email.trim(), tentativa_id: tentativaId } });
            return;
        }

        if (iniciarLogin) {
            iniciarLogin(dadosConta);
        }

        navigate(isBusiness ? "/business" : "/home");
    }

    if (isBusiness) {
        return (
            <div className="partner-login-page">
                <div className="partner-login-container">
                    
                    <div className="partner-login-header">
                        <span className="site-logo-icone">🍭</span>
                        <h1 className="partner-login-brand">Candyland</h1>
                        <span className="partner-login-subbrand">PORTAL DE PARCEIROS</span>
                    </div>

                    <div className="partner-login-card">
                        <h2 className="partner-login-title">
                            {etapa === "EMAIL" && "Entrar no Portal 🏪"}
                            {etapa === "CODIGO_EMAIL" && "Código do E-mail ✉️"}
                            {etapa === "CELULAR" && "WhatsApp / Celular 📱"}
                            {etapa === "CODIGO_CELULAR" && "Código do WhatsApp 🔑"}
                        </h2>
                        
                        <p className="partner-login-desc">
                            {etapa === "EMAIL" && "Acesse seu painel de loja ou entregador"}
                            {etapa === "CODIGO_EMAIL" && `Digite o código enviado para ${email}`}
                            {etapa === "CELULAR" && "Informe seu WhatsApp para o 2º fator de autenticação"}
                            {etapa === "CODIGO_CELULAR" && `Digite o código enviado para ${celular}`}
                        </p>

                        {/* Etapa 1: E-mail */}
                        {etapa === "EMAIL" && (
                            <form onSubmit={handleEnviarEmail}>
                                <div className="form-field partner-field">
                                    <label htmlFor="email">E-mail</label>
                                    <input
                                        id="email"
                                        type="email"
                                        placeholder="loja@email.com"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        required
                                    />
                                </div>
                                {erro && <p className="auth-error" role="alert">{erro}</p>}
                                <button type="submit" className="primary-button btn-partner-submit" disabled={carregando}>
                                    {carregando ? "Enviando..." : "Enviar código →"}
                                </button>
                            </form>
                        )}

                        {/* Etapa 2: Código E-mail */}
                        {etapa === "CODIGO_EMAIL" && (
                            <form onSubmit={handleVerificarCodigoEmail}>
                                <div className="form-field partner-field">
                                    <label htmlFor="codigo-email">Código do E-mail</label>
                                    <input
                                        id="codigo-email"
                                        type="text"
                                        placeholder="000000"
                                        maxLength={6}
                                        value={codigo}
                                        onChange={(e) => setCodigo(e.target.value)}
                                        required
                                        autoFocus
                                    />
                                </div>
                                {erro && <p className="auth-error" role="alert">{erro}</p>}
                                <button type="submit" className="primary-button btn-partner-submit" disabled={carregando}>
                                    {carregando ? "Verificando..." : "Validar E-mail →"}
                                </button>
                                <button
                                    type="button"
                                    className="auth-back"
                                    style={{ marginTop: "12px" }}
                                    onClick={() => { setEtapa("EMAIL"); setErro(""); }}
                                >
                                    ← Voltar
                                </button>
                            </form>
                        )}

                        {/* Etapa 3: Celular/WhatsApp */}
                        {etapa === "CELULAR" && (
                            <form onSubmit={handleEnviarCelular}>
                                <div className="form-field partner-field">
                                    <label htmlFor="celular">Celular com DDD</label>
                                    <input
                                        id="celular"
                                        type="tel"
                                        placeholder="(11) 99999-9999"
                                        value={celular}
                                        onChange={(e) => setCelular(e.target.value)}
                                        required
                                        autoFocus
                                    />
                                </div>
                                {erro && <p className="auth-error" role="alert">{erro}</p>}
                                <button type="submit" className="primary-button btn-partner-submit" disabled={carregando}>
                                    {carregando ? "Enviando..." : "Enviar código via WhatsApp →"}
                                </button>
                            </form>
                        )}

                        {/* Etapa 4: Código WhatsApp */}
                        {etapa === "CODIGO_CELULAR" && (
                            <form onSubmit={handleVerificarCodigoCelular}>
                                <div className="form-field partner-field">
                                    <label htmlFor="codigo-celular">Código do WhatsApp</label>
                                    <input
                                        id="codigo-celular"
                                        type="text"
                                        placeholder="000000"
                                        maxLength={6}
                                        value={codigo}
                                        onChange={(e) => setCodigo(e.target.value)}
                                        required
                                        autoFocus
                                    />
                                </div>
                                {erro && <p className="auth-error" role="alert">{erro}</p>}
                                <button type="submit" className="primary-button btn-partner-submit" disabled={carregando}>
                                    {carregando ? "Verificando..." : "Entrar no Painel →"}
                                </button>
                                <button
                                    type="button"
                                    className="auth-back"
                                    style={{ marginTop: "12px" }}
                                    onClick={() => { setEtapa("CELULAR"); setErro(""); setCodigo(""); }}
                                >
                                    ← Voltar
                                </button>
                            </form>
                        )}

                        <div className="partner-login-footer">
                            <span>Não tem conta parceira? </span>
                            <Link to="/register/business" className="partner-register-link">
                                Cadastrar agora
                            </Link>
                        </div>
                    </div>

                    <div className="partner-login-bottom-links">
                        <Link to="/login" className="partner-bottom-link">
                            Sou cliente → Entrar como cliente
                        </Link>
                        <a href="#admin" className="partner-admin-link">
                            Área administrativa
                        </a>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="auth-page">
            <div className="auth-card">
                <div className="auth-header">
                    <h1>Candyland</h1>
                    <p>Doces de todos os mundos</p>
                </div>
            </div>
        </div>
    );
}

export default Login;