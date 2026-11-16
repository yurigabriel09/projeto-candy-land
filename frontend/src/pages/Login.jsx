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
    const { entrar } = useAuth();
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
            // O RegistrationGuard e as telas de cadastro esperam: email, telefone e tentativaId.
            navigate(destino, {
                state: {
                    email: dadosConta.email || email.trim(),
                    telefone: dadosConta.telefone || celular.trim(),
                    tentativaId,
                },
            });
            return;
        }

        // Grava a sessão (token) no AuthContext e no localStorage.
        entrar(dadosConta);

        navigate(isBusiness ? "/business" : "/home");
    }

    const titulos = {
        EMAIL: isBusiness ? "Entrar no Portal 🏪" : "Bem-vindo de volta! 🍬",
        CODIGO_EMAIL: "Código do E-mail ✉️",
        CELULAR: "WhatsApp / Celular 📱",
        CODIGO_CELULAR: "Código do WhatsApp 🔑",
    };
    const descricoes = {
        EMAIL: isBusiness ? "Acesse seu painel de loja ou entregador" : "Entre na sua conta e peça seus doces favoritos",
        CODIGO_EMAIL: `Digite o código enviado para ${email}`,
        CELULAR: "Informe seu WhatsApp para o 2º fator de autenticação",
        CODIGO_CELULAR: `Digite o código enviado para ${celular}`,
    };

    // O login com Google ainda não está ligado nesta tela.
    function handleGoogle() {
        setErro("O login com Google ainda não está disponível nesta tela.");
    }

    // Classes mudam conforme o layout (cliente x parceiro); o fluxo é o mesmo.
    const classeCampo = isBusiness ? "form-field partner-field" : "form-field lg-field";
    const classeBotao = isBusiness ? "primary-button btn-partner-submit" : "primary-button lg-btn";

    const formulario = (
        <>
            {/* Etapa 1: E-mail */}
            {etapa === "EMAIL" && (
                <form onSubmit={handleEnviarEmail}>
                    <div className={classeCampo}>
                        <label htmlFor="email">E-mail</label>
                        <input
                            id="email"
                            type="email"
                            placeholder={isBusiness ? "loja@email.com" : "seu@email.com"}
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            required
                        />
                    </div>
                    {erro && <p className="auth-error" role="alert">{erro}</p>}
                    <button type="submit" className={classeBotao} disabled={carregando}>
                        {carregando ? "Enviando..." : "Enviar código →"}
                    </button>
                </form>
            )}

            {/* Etapa 2: Código E-mail */}
            {etapa === "CODIGO_EMAIL" && (
                <form onSubmit={handleVerificarCodigoEmail}>
                    <div className={classeCampo}>
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
                    <button type="submit" className={classeBotao} disabled={carregando}>
                        {carregando ? "Verificando..." : "Validar E-mail →"}
                    </button>
                    <button
                        type="button"
                        className="auth-back"
                        style={{ marginTop: "12px" }}
                        onClick={() => { setEtapa("EMAIL"); setErro(""); setCodigo(""); }}
                    >
                        ← Voltar
                    </button>
                </form>
            )}

            {/* Etapa 3: Celular/WhatsApp */}
            {etapa === "CELULAR" && (
                <form onSubmit={handleEnviarCelular}>
                    <div className={classeCampo}>
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
                    <button type="submit" className={classeBotao} disabled={carregando}>
                        {carregando ? "Enviando..." : "Enviar código via WhatsApp →"}
                    </button>
                </form>
            )}

            {/* Etapa 4: Código WhatsApp */}
            {etapa === "CODIGO_CELULAR" && (
                <form onSubmit={handleVerificarCodigoCelular}>
                    <div className={classeCampo}>
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
                    <button type="submit" className={classeBotao} disabled={carregando}>
                        {carregando ? "Verificando..." : isBusiness ? "Entrar no Painel →" : "Entrar →"}
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
        </>
    );

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
                        <h2 className="partner-login-title">{titulos[etapa]}</h2>
                        <p className="partner-login-desc">{descricoes[etapa]}</p>

                        {formulario}

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
        <div className="lg-page">
            {/* Painel ilustrado (lado esquerdo) */}
            <aside className="lg-lado" aria-hidden="true">
                <span className="lg-deco lg-deco-1">🍭</span>
                <span className="lg-deco lg-deco-2">✨</span>
                <span className="lg-deco lg-deco-3">🍬</span>
                <span className="lg-deco lg-deco-4">🌟</span>

                <div className="lg-arco">
                    <span className="lg-lua">🌙</span>
                    <div className="lg-caminho" />
                    <span className="lg-castelo">🏰</span>
                    <span className="lg-pirulito lg-pirulito-e">🍭</span>
                    <span className="lg-pirulito lg-pirulito-d">🍭</span>
                    <i className="lg-gota lg-gota-1" />
                    <i className="lg-gota lg-gota-2" />
                    <i className="lg-gota lg-gota-3" />
                    <i className="lg-gota lg-gota-4" />
                </div>

                <h2 className="lg-marca">Candyland</h2>
                <p className="lg-slogan">DOCES DE TODOS OS MUNDOS</p>
                <p className="lg-convite">
                    Entre pela porta e descubra um universo inteiro de doces esperando por você ✨
                </p>
            </aside>

            {/* Formulário (lado direito) */}
            <main className="lg-form-lado">
                <div className="lg-form-box">
                    <h1 className="lg-titulo">{titulos[etapa]}</h1>
                    <p className="lg-desc">{descricoes[etapa]}</p>

                    {formulario}

                    {etapa === "EMAIL" && (
                        <>
                            <div className="lg-ou"><span>ou</span></div>

                            <button type="button" className="lg-google" onClick={handleGoogle}>
                                <span className="lg-google-g" aria-hidden="true">G</span>
                                Continuar com Google
                            </button>

                            <p className="lg-cadastro">
                                Não tem conta?{" "}
                                <button type="button" onClick={() => document.getElementById("email")?.focus()}>
                                    Criar conta grátis
                                </button>
                            </p>
                            <p className="lg-dica">Digite seu e-mail acima. Se ainda não houver conta, vamos criar uma para você.</p>

                            <div className="lg-parceiro">
                                <small>Você é parceiro ou entregador?</small>
                                <Link to="/parceiros/login">Acesse o Portal de Parceiros →</Link>
                            </div>
                        </>
                    )}
                </div>
            </main>
        </div>
    );
}

export default Login;