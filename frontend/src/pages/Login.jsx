import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { GoogleLogin } from "@react-oauth/google";
import { useAuth } from "../context/AuthContext";
import { apiUrl } from "../services/apiConfig";

async function postJson(path, body) {
    const response = await fetch(apiUrl(path), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        cache: "no-store",
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.erro || `Falha na comunicação com o CandyLand (${response.status}).`);
    return data;
}

function Login({ audiencia = "PERSONAL" }) {
    const isBusiness = audiencia === "BUSINESS";
    const navigate = useNavigate();
    const [searchParams, setSearchParams] = useSearchParams();
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
    const [socialProvider, setSocialProvider] = useState("");
    const [socialCredential, setSocialCredential] = useState("");
    const [socialTicket, setSocialTicket] = useState("");
    const [erro, setErro] = useState("");
    const [mensagem, setMensagem] = useState("");
    const [carregando, setCarregando] = useState(false);

    useEffect(() => {
        const ticket = searchParams.get("facebook_ticket");
        const oauthError = searchParams.get("facebook_error");
        if (ticket) {
            setSocialProvider("FACEBOOK");
            setSocialTicket(ticket);
            setEtapa("SOCIAL_TELEFONE");
            setMensagem("Facebook confirmado. Agora confirme seu celular para concluir o acesso.");
            setSearchParams({}, { replace: true });
        } else if (oauthError) {
            setErro(oauthError);
            setSearchParams({}, { replace: true });
        }
    }, [searchParams, setSearchParams]);

    function concluirSessao(dadosConta) {
        if (dadosConta?.novo_cadastro) {
            navigate(isBusiness ? "/register/business" : "/register/personal", {
                state: {
                    email: dadosConta.email || email,
                    telefone: dadosConta.telefone || celular,
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
        navigate(dadosConta.tipo_conta === "BUSINESS" ? "/business" : "/home");
    }

    async function handleEnviarPrimeiroCodigo(event) {
        event.preventDefault();
        setErro(""); setMensagem("");
        const valor = identificadorInicial.trim();
        if (!valor) return setErro(canalInicial === "EMAIL" ? "Informe seu e-mail." : "Informe seu celular com DDD e país.");
        setCarregando(true);
        try {
            const data = await postJson("auth/login", { canal: canalInicial, valor });
            if (!data.tentativa_id) throw new Error("O servidor não criou a tentativa de autenticação.");
            setTentativaId(data.tentativa_id);
            setEtapa("CODIGO_PRIMEIRO");
            setMensagem(data.mensagem || "Código enviado. Confira seu contato.");
            if (canalInicial === "EMAIL") setEmail(valor); else setCelular(valor);
        } catch (error) { setErro(error.message || "Não foi possível iniciar o login."); }
        finally { setCarregando(false); }
    }

    async function handleVerificarPrimeiroCodigo(event) {
        event.preventDefault();
        if (!codigo.trim()) return setErro("Digite o código recebido.");
        setCarregando(true); setErro(""); setMensagem("");
        try {
            const data = await postJson("auth/verify", { tentativa_id: tentativaId, codigo: codigo.trim() });
            if (data.dados) throw new Error("O servidor tentou concluir o login antes do segundo fator. A tentativa foi interrompida.");
            const proximo = data.proximo_canal || (canalInicial === "EMAIL" ? "WHATSAPP" : "EMAIL");
            setCanalSegundo(proximo); setIdentificadorSegundo(""); setCodigo("");
            setEtapa("SEGUNDO_CONTATO");
            setMensagem("Primeiro fator confirmado. Informe o outro contato associado à sua conta.");
        } catch (error) { setErro(error.message || "Não foi possível validar o primeiro código."); }
        finally { setCarregando(false); }
    }

    async function handleEnviarSegundoCodigo(event) {
        event.preventDefault();
        const valor = identificadorSegundo.trim();
        if (!valor) return setErro(canalSegundo === "EMAIL" ? "Informe o e-mail da conta." : "Informe o celular da conta.");
        setCarregando(true); setErro(""); setMensagem("");
        try {
            const data = await postJson("auth/second-code", { tentativa_id: tentativaId, valor });
            if (canalSegundo === "EMAIL") setEmail(valor); else setCelular(valor);
            setCodigo(""); setEtapa("CODIGO_SEGUNDO");
            setMensagem(data.mensagem || "Segundo código enviado.");
        } catch (error) { setErro(error.message || "Não foi possível enviar o segundo código."); }
        finally { setCarregando(false); }
    }

    async function handleVerificarSegundoCodigo(event) {
        event.preventDefault();
        if (!codigo.trim()) return setErro("Digite o segundo código recebido.");
        setCarregando(true); setErro(""); setMensagem("");
        try {
            const data = await postJson("auth/verify", { tentativa_id: tentativaId, codigo: codigo.trim() });
            if (!data.dados) throw new Error(data.mensagem || "A autenticação ainda não foi concluída.");
            concluirSessao(data.dados);
        } catch (error) { setErro(error.message || "Não foi possível validar o segundo código."); }
        finally { setCarregando(false); }
    }

    async function handleGoogleSuccess(credential) {
        if (!credential) return setErro("O Google não retornou uma credencial válida.");
        setCarregando(true); setErro(""); setMensagem("");
        try {
            const data = await postJson("auth/google", { credential });
            setSocialProvider("GOOGLE"); setSocialCredential(credential); setEmail(data.email || "");
            setEtapa("SOCIAL_TELEFONE");
            setMensagem(data.mensagem || "E-mail confirmado pelo Google. Informe seu celular para o segundo fator.");
        } catch (error) { setErro(error.message || "Não foi possível iniciar o login Google."); }
        finally { setCarregando(false); }
    }

    async function handleEnviarTelefoneSocial(event) {
        event.preventDefault();
        const phone = celular.trim();
        if (!phone) return setErro("Informe o celular com DDD e país.");
        setCarregando(true); setErro(""); setMensagem("");
        try {
            const data = socialProvider === "GOOGLE"
                ? await postJson("auth/google", { credential: socialCredential, telefone: phone })
                : await postJson("auth/facebook/complete", { ticket: socialTicket, telefone: phone });
            if (!data.tentativa_id) throw new Error(data.erro || "O servidor não iniciou o segundo fator por celular.");
            setTentativaId(data.tentativa_id); setCanalSegundo("WHATSAPP");
            setIdentificadorSegundo(data.telefone || phone); setCodigo("");
            setEtapa("SOCIAL_CODIGO"); setMensagem(data.mensagem || "Código enviado por WhatsApp.");
        } catch (error) { setErro(error.message || "Não foi possível enviar o código para o celular."); }
        finally { setCarregando(false); }
    }

    async function handleVerificarCodigoSocial(event) {
        event.preventDefault();
        if (!codigo.trim()) return setErro("Digite o código recebido no WhatsApp.");
        setCarregando(true); setErro("");
        try {
            const data = await postJson("auth/verify", { tentativa_id: tentativaId, codigo: codigo.trim() });
            if (!data.dados) throw new Error(data.mensagem || "O segundo fator ainda não foi confirmado.");
            concluirSessao(data.dados);
        } catch (error) { setErro(error.message || "Não foi possível concluir o login social."); }
        finally { setCarregando(false); }
    }

    function iniciarFacebook() {
        const url = apiUrl(`auth/facebook?platform=WEB&audiencia=${isBusiness ? "BUSINESS" : "PERSONAL"}`);
        window.location.assign(url);
    }

    function voltarInicio() {
        setEtapa("PRIMEIRO_CONTATO"); setCodigo(""); setTentativaId("");
        setIdentificadorSegundo(""); setSocialProvider(""); setSocialCredential(""); setSocialTicket("");
        setErro(""); setMensagem("");
    }

    const titulo = {
        PRIMEIRO_CONTATO: isBusiness ? "Entrar no Portal" : "Entre na sua conta",
        CODIGO_PRIMEIRO: "Confirme o primeiro contato",
        SEGUNDO_CONTATO: "Confirme o outro contato",
        CODIGO_SEGUNDO: "Confirme o segundo contato",
        SOCIAL_TELEFONE: "Confirme seu celular",
        SOCIAL_CODIGO: "Digite o código do celular",
    }[etapa];
    const descricao = {
        PRIMEIRO_CONTATO: "Escolha o primeiro fator de acesso. Depois confirmaremos o outro contato cadastrado.",
        CODIGO_PRIMEIRO: `Digite o código enviado para ${identificadorInicial}.`,
        SEGUNDO_CONTATO: `Informe o ${canalSegundo === "EMAIL" ? "e-mail" : "celular"} que pertence à mesma conta do primeiro contato.`,
        CODIGO_SEGUNDO: `Digite o código enviado para ${identificadorSegundo}.`,
        SOCIAL_TELEFONE: "O provedor confirmou seu e-mail. Informe o celular para receber o segundo fator.",
        SOCIAL_CODIGO: `Digite o código enviado por WhatsApp para ${identificadorSegundo}.`,
    }[etapa];
    const campoClass = isBusiness ? "form-field partner-field" : "form-field";
    const botaoClass = isBusiness ? "primary-button btn-partner-submit" : "primary-button";
    const formulario = (
        <>
            {etapa === "PRIMEIRO_CONTATO" && <>
                <form onSubmit={handleEnviarPrimeiroCodigo}>
                    <div className="login-type" role="group" aria-label="Primeiro fator">
                        <button type="button" className={canalInicial === "EMAIL" ? "active" : ""} onClick={() => { setCanalInicial("EMAIL"); setIdentificadorInicial(""); setErro(""); }}>E-mail</button>
                        <button type="button" className={canalInicial === "WHATSAPP" ? "active" : ""} onClick={() => { setCanalInicial("WHATSAPP"); setIdentificadorInicial(""); setErro(""); }}>Celular</button>
                    </div>
                    <div className={campoClass}>
                        <label htmlFor="login-identificador">{canalInicial === "EMAIL" ? "E-mail" : "Celular com DDD"}</label>
                        <input id="login-identificador" type={canalInicial === "EMAIL" ? "email" : "tel"} autoComplete={canalInicial === "EMAIL" ? "email" : "tel"} placeholder={canalInicial === "EMAIL" ? "seu@email.com" : "+55 11 99999-9999"} value={identificadorInicial} onChange={e => setIdentificadorInicial(e.target.value)} required />
                    </div>
                    {erro && <p className="auth-error" role="alert">{erro}</p>}
                    <button type="submit" className={botaoClass} disabled={carregando}>{carregando ? "Enviando..." : "Enviar primeiro código →"}</button>
                </form>
                <div className="social-login-divider"><span>ou entre com</span></div>
                <div className="social-login-buttons">
                    <GoogleLogin onSuccess={response => handleGoogleSuccess(response.credential)} onError={() => setErro("Não foi possível autenticar com Google.")} text="continue_with" shape="pill" width="320" />
                    <button type="button" className="btn-contorno social-facebook-button" disabled={carregando} onClick={iniciarFacebook}>f&nbsp; Continuar com Facebook</button>
                </div>
            </>}
            {etapa === "CODIGO_PRIMEIRO" && <form onSubmit={handleVerificarPrimeiroCodigo}>
                <div className={campoClass}><label htmlFor="codigo-primeiro">Código de 6 dígitos</label><input id="codigo-primeiro" type="text" inputMode="numeric" autoComplete="one-time-code" maxLength={6} value={codigo} onChange={e => setCodigo(e.target.value.replace(/\D/g, "").slice(0, 6))} required /></div>
                {erro && <p className="auth-error" role="alert">{erro}</p>}
                <button type="submit" className={botaoClass} disabled={carregando}>{carregando ? "Validando..." : "Validar primeiro fator →"}</button>
            </form>}
            {etapa === "SEGUNDO_CONTATO" && <form onSubmit={handleEnviarSegundoCodigo}>
                <div className={campoClass}><label htmlFor="segundo-contato">{canalSegundo === "EMAIL" ? "E-mail" : "Celular com DDD"}</label><input id="segundo-contato" type={canalSegundo === "EMAIL" ? "email" : "tel"} autoComplete={canalSegundo === "EMAIL" ? "email" : "tel"} placeholder={canalSegundo === "EMAIL" ? "seu@email.com" : "+55 11 99999-9999"} value={identificadorSegundo} onChange={e => setIdentificadorSegundo(e.target.value)} required /></div>
                {erro && <p className="auth-error" role="alert">{erro}</p>}
                <button type="submit" className={botaoClass} disabled={carregando}>{carregando ? "Enviando..." : "Enviar segundo código →"}</button>
            </form>}
            {etapa === "CODIGO_SEGUNDO" && <form onSubmit={handleVerificarSegundoCodigo}>
                <div className={campoClass}><label htmlFor="codigo-segundo">Código de 6 dígitos</label><input id="codigo-segundo" type="text" inputMode="numeric" autoComplete="one-time-code" maxLength={6} value={codigo} onChange={e => setCodigo(e.target.value.replace(/\D/g, "").slice(0, 6))} required /></div>
                {erro && <p className="auth-error" role="alert">{erro}</p>}
                <button type="submit" className={botaoClass} disabled={carregando}>{carregando ? "Validando..." : "Validar segundo fator →"}</button>
            </form>}
            {etapa === "SOCIAL_TELEFONE" && <form onSubmit={handleEnviarTelefoneSocial}>
                <div className={campoClass}><label htmlFor="social-phone">Celular com DDD e país</label><input id="social-phone" type="tel" autoComplete="tel" placeholder="+55 11 99999-9999" value={celular} onChange={e => setCelular(e.target.value)} required /></div>
                {email && <p className="auth-success">E-mail confirmado: {email}</p>}
                {erro && <p className="auth-error" role="alert">{erro}</p>}
                <button type="submit" className={botaoClass} disabled={carregando}>{carregando ? "Enviando..." : "Enviar código pelo WhatsApp →"}</button>
            </form>}
            {etapa === "SOCIAL_CODIGO" && <form onSubmit={handleVerificarCodigoSocial}>
                <div className={campoClass}><label htmlFor="social-code">Código de 6 dígitos</label><input id="social-code" type="text" inputMode="numeric" autoComplete="one-time-code" maxLength={6} value={codigo} onChange={e => setCodigo(e.target.value.replace(/\D/g, "").slice(0, 6))} required /></div>
                {erro && <p className="auth-error" role="alert">{erro}</p>}
                <button type="submit" className={botaoClass} disabled={carregando}>{carregando ? "Validando..." : "Confirmar celular →"}</button>
            </form>}
            {mensagem && <p className="auth-success" role="status">{mensagem}</p>}
            {etapa !== "PRIMEIRO_CONTATO" && <button type="button" className="auth-back" onClick={voltarInicio} disabled={carregando}>← Voltar e escolher outra forma de acesso</button>}
        </>
    );

    if (isBusiness) return (
        <div className="partner-login-page"><div className="partner-login-container">
            <div className="partner-login-header"><span className="site-logo-icone">🍭</span><h1 className="partner-login-brand">Candyland</h1><span className="partner-login-subbrand">PORTAL DE PARCEIROS</span></div>
            <div className="partner-login-card"><h2 className="partner-login-title">{titulo}</h2><p className="partner-login-desc">{descricao}</p>{formulario}
                <div className="partner-login-footer">Ainda não tem conta parceira? <Link to="/register/business" className="partner-register-link">Cadastrar agora</Link></div>
            </div><div className="partner-login-bottom-links"><Link to="/login" className="partner-bottom-link">Sou cliente → Entrar como cliente</Link><Link to="/parceiros" className="partner-bottom-link">Conhecer o CandyLand para parceiros</Link></div>
        </div></div>
    );

    return <div className="auth-page"><div className="auth-card">
        <div className="auth-header"><h1>Candyland</h1><p>Doces de todos os mundos</p></div>
        <div className="auth-content"><h2>{titulo}</h2><p className="auth-description">{descricao}</p>{formulario}
            <p className="auth-footer">É parceiro? <Link to="/parceiros">Conheça o portal de parceiros</Link></p>
            <p className="auth-footer"><Link to="/">Voltar para o início</Link></p>
        </div>
    </div></div>;
}

export default Login;
