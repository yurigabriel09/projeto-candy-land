import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { apiUrl } from "../services/apiConfig";

async function postJson(path, body) {
    const response = await fetch(apiUrl(path), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
        throw new Error(data.erro || `Falha na comunicação com o CandyLand (${response.status}).`);
    }
    return data;
}

function Login({ audiencia = "PERSONAL" }) {
    const isBusiness = audiencia === "BUSINESS";
    const navigate = useNavigate();
    const { entrar } = useAuth();

    const [etapa, setEtapa] = useState("PRIMEIRO_CONTATO");
    const [canalInicial, setCanalInicial] = useState("EMAIL");
    const [identificadorInicial, setIdentificadorInicial] = useState("");
    const [canalSegundo, setCanalSegundo] = useState("WHATSAPP");
    const [identificadorSegundo, setIdentificadorSegundo] = useState("");
    const [email, setEmail] = useState("");
    const [celular, setCelular] = useState("");
    const [codigo, setCodigo] = useState("");
    const [tentativaId, setTentativaId] = useState("");
    const [erro, setErro] = useState("");
    const [mensagem, setMensagem] = useState("");
    const [carregando, setCarregando] = useState(false);

    function atualizarContatoInicial(valor) {
        setIdentificadorInicial(valor);
        if (canalInicial === "EMAIL") setEmail(valor);
        else setCelular(valor);
        setErro("");
    }

    function atualizarSegundoContato(valor) {
        setIdentificadorSegundo(valor);
        if (canalSegundo === "EMAIL") setEmail(valor);
        else setCelular(valor);
        setErro("");
    }

    function concluirSessao(dadosConta) {
        if (dadosConta?.novo_cadastro) {
            const destino = isBusiness ? "/register/business" : "/register/personal";
            navigate(destino, {
                state: {
                    email: dadosConta.email || email,
                    telefone: dadosConta.telefone || celular,
                    // As telas PersonalRegister e BusinessRegister consomem tentativaId (camelCase).
                    tentativaId: dadosConta.tentativa_id || tentativaId,
                },
            });
            return;
        }

        if (!dadosConta?.token) {
            setErro("O servidor não retornou uma sessão válida.");
            return;
        }

        entrar(dadosConta);
        // O tipo retornado pelo backend prevalece sobre a página em que o login começou.
        navigate(dadosConta.tipo_conta === "BUSINESS" ? "/business" : "/home");
    }

    async function handleEnviarPrimeiroCodigo(event) {
        event.preventDefault();
        setErro("");
        setMensagem("");

        const valor = identificadorInicial.trim();
        if (!valor) {
            setErro(canalInicial === "EMAIL" ? "Informe seu e-mail." : "Informe seu celular com DDD e país.");
            return;
        }
        if (canalInicial === "EMAIL" && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(valor)) {
            setErro("Informe um e-mail válido.");
            return;
        }

        setCarregando(true);
        try {
            const data = await postJson("auth/login", { canal: canalInicial, valor });
            if (!data.tentativa_id) throw new Error("O servidor não criou a tentativa de autenticação.");
            setTentativaId(data.tentativa_id);
            setEtapa("CODIGO_PRIMEIRO");
            setMensagem(data.mensagem || "Código solicitado. Confira seu e-mail ou WhatsApp.");
        } catch (error) {
            setErro(error.message || "Não foi possível iniciar o login.");
        } finally {
            setCarregando(false);
        }
    }

    async function handleVerificarPrimeiroCodigo(event) {
        event.preventDefault();
        if (!codigo.trim()) {
            setErro("Digite o código recebido.");
            return;
        }

        setCarregando(true);
        setErro("");
        setMensagem("");
        try {
            // Não enviar tipo_conta: o backend identifica PERSONAL/BUSINESS pelo contato verificado.
            const data = await postJson("auth/verify", {
                tentativa_id: tentativaId,
                codigo: codigo.trim(),
            });
            if (data.dados) {
                concluirSessao(data.dados);
                return;
            }

            const proximo = data.proximo_canal || (canalInicial === "EMAIL" ? "WHATSAPP" : "EMAIL");
            setCanalSegundo(proximo);
            setIdentificadorSegundo("");
            setCodigo("");
            setEtapa("SEGUNDO_CONTATO");
            setMensagem("O primeiro contato foi confirmado. Informe o outro contato para concluir um novo cadastro.");
        } catch (error) {
            setErro(error.message || "Não foi possível validar o código.");
        } finally {
            setCarregando(false);
        }
    }

    async function handleEnviarSegundoCodigo(event) {
        event.preventDefault();
        const valor = identificadorSegundo.trim();
        if (!valor) {
            setErro(canalSegundo === "EMAIL" ? "Informe o e-mail para concluir o cadastro." : "Informe o celular para concluir o cadastro.");
            return;
        }
        if (canalSegundo === "EMAIL" && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(valor)) {
            setErro("Informe um e-mail válido.");
            return;
        }

        setCarregando(true);
        setErro("");
        setMensagem("");
        try {
            const data = await postJson("auth/second-code", {
                tentativa_id: tentativaId,
                valor,
            });
            setCodigo("");
            setEtapa("CODIGO_SEGUNDO");
            setMensagem(data.mensagem || "Segundo código solicitado. Confira o contato informado.");
        } catch (error) {
            setErro(error.message || "Não foi possível enviar o segundo código.");
        } finally {
            setCarregando(false);
        }
    }

    async function handleVerificarSegundoCodigo(event) {
        event.preventDefault();
        if (!codigo.trim()) {
            setErro("Digite o segundo código recebido.");
            return;
        }

        setCarregando(true);
        setErro("");
        setMensagem("");
        try {
            const data = await postJson("auth/verify", {
                tentativa_id: tentativaId,
                codigo: codigo.trim(),
            });
            if (!data.dados) throw new Error(data.mensagem || "A autenticação ainda não foi concluída.");
            concluirSessao(data.dados);
        } catch (error) {
            setErro(error.message || "Não foi possível validar o segundo código.");
        } finally {
            setCarregando(false);
        }
    }

    function voltarInicio() {
        setEtapa("PRIMEIRO_CONTATO");
        setCodigo("");
        setTentativaId("");
        setErro("");
        setMensagem("");
        setIdentificadorSegundo("");
    }

    const titulo = {
        PRIMEIRO_CONTATO: isBusiness ? "Entrar no Portal" : "Entre na sua conta",
        CODIGO_PRIMEIRO: "Confirme seu contato",
        SEGUNDO_CONTATO: "Complete seus dados",
        CODIGO_SEGUNDO: "Confirme o segundo contato",
    }[etapa];

    const descricao = {
        PRIMEIRO_CONTATO: "Escolha como deseja receber o primeiro código de acesso.",
        CODIGO_PRIMEIRO: `Digite o código enviado para ${identificadorInicial}.`,
        SEGUNDO_CONTATO: `O primeiro contato foi confirmado. Agora informe seu ${canalSegundo === "EMAIL" ? "e-mail" : "celular"}.`,
        CODIGO_SEGUNDO: `Digite o código enviado para ${identificadorSegundo}.`,
    }[etapa];

    const campoClass = isBusiness ? "form-field partner-field" : "form-field";
    const botaoClass = isBusiness ? "primary-button btn-partner-submit" : "primary-button";

    const formulario = (
        <>
            {etapa === "PRIMEIRO_CONTATO" && (
                <form onSubmit={handleEnviarPrimeiroCodigo}>
                    <div className="login-type" role="group" aria-label="Canal do primeiro código">
                        <button
                            type="button"
                            className={canalInicial === "EMAIL" ? "active" : ""}
                            onClick={() => { setCanalInicial("EMAIL"); setIdentificadorInicial(""); setErro(""); }}
                        >E-mail</button>
                        <button
                            type="button"
                            className={canalInicial === "WHATSAPP" ? "active" : ""}
                            onClick={() => { setCanalInicial("WHATSAPP"); setIdentificadorInicial(""); setErro(""); }}
                        >Celular</button>
                    </div>
                    <div className={campoClass}>
                        <label htmlFor="login-identificador">{canalInicial === "EMAIL" ? "E-mail" : "Celular com DDD"}</label>
                        <input
                            id="login-identificador"
                            type={canalInicial === "EMAIL" ? "email" : "tel"}
                            autoComplete={canalInicial === "EMAIL" ? "email" : "tel"}
                            placeholder={canalInicial === "EMAIL" ? "seu@email.com" : "+55 11 99999-9999"}
                            value={identificadorInicial}
                            onChange={(event) => atualizarContatoInicial(event.target.value)}
                            required
                        />
                    </div>
                    {erro && <p className="auth-error" role="alert">{erro}</p>}
                    <button type="submit" className={botaoClass} disabled={carregando}>
                        {carregando ? "Enviando..." : "Enviar código →"}
                    </button>
                </form>
            )}

            {etapa === "CODIGO_PRIMEIRO" && (
                <form onSubmit={handleVerificarPrimeiroCodigo}>
                    <div className={campoClass}>
                        <label htmlFor="codigo-primeiro">Código de 6 dígitos</label>
                        <input
                            id="codigo-primeiro"
                            type="text"
                            inputMode="numeric"
                            autoComplete="one-time-code"
                            maxLength={6}
                            placeholder="000000"
                            value={codigo}
                            onChange={(event) => { setCodigo(event.target.value.replace(/\D/g, "").slice(0, 6)); setErro(""); }}
                            required
                        />
                    </div>
                    {erro && <p className="auth-error" role="alert">{erro}</p>}
                    <button type="submit" className={botaoClass} disabled={carregando}>
                        {carregando ? "Validando..." : "Validar código →"}
                    </button>
                </form>
            )}

            {etapa === "SEGUNDO_CONTATO" && (
                <form onSubmit={handleEnviarSegundoCodigo}>
                    <div className={campoClass}>
                        <label htmlFor="segundo-contato">{canalSegundo === "EMAIL" ? "E-mail" : "Celular com DDD"}</label>
                        <input
                            id="segundo-contato"
                            type={canalSegundo === "EMAIL" ? "email" : "tel"}
                            autoComplete={canalSegundo === "EMAIL" ? "email" : "tel"}
                            placeholder={canalSegundo === "EMAIL" ? "seu@email.com" : "+55 11 99999-9999"}
                            value={identificadorSegundo}
                            onChange={(event) => atualizarSegundoContato(event.target.value)}
                            required
                        />
                    </div>
                    {erro && <p className="auth-error" role="alert">{erro}</p>}
                    <button type="submit" className={botaoClass} disabled={carregando}>
                        {carregando ? "Enviando..." : "Enviar segundo código →"}
                    </button>
                </form>
            )}

            {etapa === "CODIGO_SEGUNDO" && (
                <form onSubmit={handleVerificarSegundoCodigo}>
                    <div className={campoClass}>
                        <label htmlFor="codigo-segundo">Código de 6 dígitos</label>
                        <input
                            id="codigo-segundo"
                            type="text"
                            inputMode="numeric"
                            autoComplete="one-time-code"
                            maxLength={6}
                            placeholder="000000"
                            value={codigo}
                            onChange={(event) => { setCodigo(event.target.value.replace(/\D/g, "").slice(0, 6)); setErro(""); }}
                            required
                        />
                    </div>
                    {erro && <p className="auth-error" role="alert">{erro}</p>}
                    <button type="submit" className={botaoClass} disabled={carregando}>
                        {carregando ? "Validando..." : "Concluir autenticação →"}
                    </button>
                </form>
            )}

            {mensagem && <p className="auth-success" role="status">{mensagem}</p>}
            {etapa !== "PRIMEIRO_CONTATO" && (
                <button type="button" className="auth-back" onClick={voltarInicio} disabled={carregando}>
                    ← Voltar ao início
                </button>
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
                        <h2 className="partner-login-title">{titulo}</h2>
                        <p className="partner-login-desc">{descricao}</p>
                        {formulario}
                        <div className="partner-login-footer">
                            Não tem conta parceira? <Link to="/register/business" className="partner-register-link">Cadastrar agora</Link>
                        </div>
                    </div>
                    <div className="partner-login-bottom-links">
                        <Link to="/login" className="partner-bottom-link">Sou cliente → Entrar como cliente</Link>
                        <Link to="/" className="partner-bottom-link">Voltar para o início</Link>
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
                <div className="auth-content">
                    <h2>{titulo}</h2>
                    <p className="auth-description">{descricao}</p>
                    {formulario}
                    <p className="auth-footer">
                        É parceiro? <Link to="/parceiros/login">Acessar portal de parceiros</Link>
                    </p>
                    <p className="auth-footer">
                        <Link to="/">Voltar para o início</Link>
                    </p>
                </div>
            </div>
        </div>
    );
}

export default Login;
