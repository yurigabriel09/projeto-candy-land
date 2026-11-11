import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { getUser, updateUser } from "../services/userService";
import { getAddressByCep } from "../services/addressService";
import { maskCep } from "../utils/masks";

function iniciais(nome) {
    const partes = (nome || "").trim().split(/\s+/).filter(Boolean);
    if (partes.length === 0) return "?";
    const primeira = partes[0][0];
    const ultima = partes.length > 1 ? partes[partes.length - 1][0] : "";
    return (primeira + ultima).toUpperCase();
}

function formatarCelular(valor) {
    let digitos = (valor || "").replace(/\D/g, "");
    if ((digitos.length === 12 || digitos.length === 13) && digitos.startsWith("55")) {
        digitos = digitos.slice(2);
    }
    if (digitos.length === 11) {
        return `(${digitos.slice(0, 2)}) ${digitos.slice(2, 7)}-${digitos.slice(7)}`;
    }
    if (digitos.length === 10) {
        return `(${digitos.slice(0, 2)}) ${digitos.slice(2, 6)}-${digitos.slice(6)}`;
    }
    return valor || "";
}

function mascararCpf(valor) {
    const digitos = (valor || "").replace(/\D/g, "");
    if (digitos.length !== 11) return valor || "";
    return `***.${digitos.slice(3, 6)}.${digitos.slice(6, 9)}-**`;
}

const EMPTY_ADDRESS_FORM = {
    id: null,
    cep: "",
    rua: "",
    numero: "",
    complemento: "",
    bairro: "",
    cidade: "",
    estado: "",
    referencia: "",
    latitude: null,
    longitude: null,
    principal: false,
};

async function obterCoordenadasEmSegundoPlano(rua, numero, bairro, cidade, estado, cep) {
    try {
        const enderecoCompleto = encodeURIComponent(`${rua} ${numero}, ${bairro}, ${cidade} - ${estado}, Brasil`);
        const resposta = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${enderecoCompleto}`);
        if (resposta.ok) {
            const dados = await resposta.json();
            if (dados && dados.length > 0) {
                return {
                    latitude: Number(dados[0].lat),
                    longitude: Number(dados[0].lon)
                };
            }
        }
    } catch (e) {
        console.warn("Geocodificação por endereço falhou, tentando por CEP...", e);
    }

    try {
        const cepLimpo = cep.replace(/\D/g, "");
        const queryCep = encodeURIComponent(`${cepLimpo}, Brasil`);
        const respostaCep = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${queryCep}`);
        if (respostaCep.ok) {
            const dadosCep = await respostaCep.json();
            if (dadosCep && dadosCep.length > 0) {
                return {
                    latitude: Number(dadosCep[0].lat),
                    longitude: Number(dadosCep[0].lon)
                };
            }
        }
    } catch (e) {
        console.warn("Geocodificação por CEP falhou:", e);
    }

    return { latitude: null, longitude: null };
}

function DadosPessoais() {
    const { dadosAutenticacao, entrar, sair } = useAuth();
    const userId = dadosAutenticacao?.id;

    const [usuario, setUsuario] = useState(null);
    const [nome, setNome] = useState("");
    const [nascimento, setNascimento] = useState("");
    const [carregando, setCarregando] = useState(true);
    const [salvando, setSalvando] = useState(false);
    const [erro, setErro] = useState("");
    const [sucesso, setSucesso] = useState("");

    const [enderecos, setEnderecos] = useState([]);
    const [carregandoEnderecos, setCarregandoEnderecos] = useState(false);
    const [exibirFormEndereco, setExibirFormEndereco] = useState(false);
    const [formEndereco, setFormEndereco] = useState(EMPTY_ADDRESS_FORM);
    const [salvandoEndereco, setSalvandoEndereco] = useState(false);
    const [erroEndereco, setErroEndereco] = useState("");
    const [sucessoEndereco, setSucessoEndereco] = useState("");
    const [loadingCep, setLoadingCep] = useState(false);
    const cepLookupRequest = useRef(0);

    function obterToken() {
        if (dadosAutenticacao?.token) return dadosAutenticacao.token;
        try {
            const raw = localStorage.getItem("candyland_auth");
            return raw ? JSON.parse(raw).token : null;
        } catch {
            return null;
        }
    }

    const apiBase = import.meta.env.VITE_API_URL || "http://127.0.0.1:5000";

    useEffect(() => {
        carregar();
        carregarEnderecos();
    }, [userId]);

    function aplicar(dados) {
        setUsuario(dados);
        setNome(dados.nome_completo || "");
        setNascimento(dados.data_nascimento || "");
    }

    async function carregar() {
        if (!userId) return;
        setCarregando(true);
        setErro("");
        try {
            const dados = await getUser(userId);
            aplicar(dados);
        } catch (error) {
            setErro(error.message || "Não foi possível carregar seus dados.");
        } finally {
            setCarregando(false);
        }
    }

    async function carregarEnderecos() {
        const token = obterToken();
        if (!userId || !token) return;

        setCarregandoEnderecos(true);
        try {
            const resposta = await fetch(`${apiBase}/users/${userId}/enderecos`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            if (resposta.ok) {
                const res = await resposta.json();
                setEnderecos(res.dados || []);
            }
        } catch (e) {
            console.error("Erro ao carregar endereços:", e);
        } finally {
            setCarregandoEnderecos(false);
        }
    }

    function handleSair() {
        sair();
        window.location.replace("/");
    }

    const nomeAlterado = usuario && nome.trim() !== (usuario.nome_completo || "");
    const nascimentoAlterado = usuario && nascimento !== (usuario.data_nascimento || "");
    const alterado = Boolean(nomeAlterado || nascimentoAlterado);

    async function handleSubmit(event) {
        event.preventDefault();
        setErro("");
        setSucesso("");

        if (!nome.trim()) {
            setErro("Informe seu nome completo.");
            return;
        }

        const alteracoes = {};
        if (nomeAlterado) alteracoes.nome_completo = nome.trim();
        if (nascimentoAlterado && nascimento) alteracoes.data_nascimento = nascimento;

        if (Object.keys(alteracoes).length === 0) return;

        setSalvando(true);
        try {
            const atualizado = await updateUser(usuario.id, alteracoes);
            aplicar(atualizado);
            entrar({ ...dadosAutenticacao, nome_completo: atualizado.nome_completo });
            setSucesso("Dados atualizados com sucesso.");
        } catch (error) {
            setErro(error.message || "Não foi possível salvar. Tente novamente.");
        } finally {
            setSalvando(false);
        }
    }

    function handleNovoEndereco() {
        setFormEndereco(EMPTY_ADDRESS_FORM);
        setErroEndereco("");
        setSucessoEndereco("");
        setExibirFormEndereco(true);
    }

    function handleEditarEndereco(end) {
        setFormEndereco({
            id: end.id,
            cep: maskCep(end.cep || ""),
            rua: end.rua || "",
            numero: end.numero || "",
            complemento: end.complemento || "",
            bairro: end.bairro || "",
            cidade: end.cidade || "",
            estado: end.estado || "",
            referencia: end.referencia || "",
            latitude: end.latitude ?? null,
            longitude: end.longitude ?? null,
            principal: end.principal || false,
        });
        setErroEndereco("");
        setSucessoEndereco("");
        setExibirFormEndereco(true);
    }

    function handleAddressFormChange(e) {
        const { name, value, type, checked } = e.target;
        const val = type === "checkbox" ? checked : value;

        if (name === "cep") {
            const cepFormatado = maskCep(value);
            const cepLimpo = cepFormatado.replace(/\D/g, "");
            const requestId = ++cepLookupRequest.current;

            setFormEndereco((curr) => ({ ...curr, cep: cepFormatado }));

            if (cepLimpo.length !== 8) {
                setLoadingCep(false);
                return;
            }

            setLoadingCep(true);
            getAddressByCep(cepLimpo)
                .then((resultado) => {
                    if (requestId !== cepLookupRequest.current) return;
                    setFormEndereco((curr) => ({
                        ...curr,
                        rua: resultado.address || curr.rua,
                        bairro: resultado.neighborhood || curr.bairro,
                        cidade: resultado.city || curr.cidade,
                        estado: resultado.state || curr.estado,
                    }));
                })
                .catch(() => {})
                .finally(() => {
                    if (requestId === cepLookupRequest.current) setLoadingCep(false);
                });
            return;
        }

        setFormEndereco((curr) => ({ ...curr, [name]: val }));
    }

    async function handleSalvarEndereco(e) {
        e.preventDefault();
        setErroEndereco("");
        setSucessoEndereco("");

        const token = obterToken();
        if (!token) {
            setErroEndereco("Sessão expirada. Faça login novamente.");
            return;
        }

        setSalvandoEndereco(true);

        try {
            let lat = formEndereco.latitude;
            let lng = formEndereco.longitude;

            if (lat === null || lng === null) {
                const coordsAuto = await obterCoordenadasEmSegundoPlano(
                    formEndereco.rua,
                    formEndereco.numero,
                    formEndereco.bairro,
                    formEndereco.cidade,
                    formEndereco.estado,
                    formEndereco.cep
                );
                lat = coordsAuto.latitude;
                lng = coordsAuto.longitude;
            }

            const payload = {
                id: formEndereco.id || null,
                cep: formEndereco.cep.replace(/\D/g, ""),
                rua: formEndereco.rua,
                numero: formEndereco.numero,
                complemento: formEndereco.complemento,
                bairro: formEndereco.bairro,
                cidade: formEndereco.cidade,
                estado: formEndereco.estado.toUpperCase(),
                referencia: formEndereco.referencia,
                latitude: lat,
                longitude: lng,
                principal: formEndereco.principal,
            };

            const resposta = await fetch(`${apiBase}/users/${userId}/enderecos`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`,
                },
                body: JSON.stringify(payload),
            });

            const contentType = resposta.headers.get("content-type");
            if (!contentType || !contentType.includes("application/json")) {
                throw new Error(`Erro no servidor (${resposta.status} ${resposta.statusText}). O backend precisa aceitar o método POST na rota /users/${userId}/enderecos.`);
            }

            const dados = await resposta.json();
            if (!resposta.ok || (dados.success !== undefined && !dados.success)) {
                throw new Error(dados.erro || dados.mensagem || "Erro ao salvar endereço.");
            }

            setSucessoEndereco(formEndereco.id ? "Endereço atualizado com sucesso!" : "Endereço cadastrado com sucesso!");
            setExibirFormEndereco(false);
            setFormEndereco(EMPTY_ADDRESS_FORM);
            await carregarEnderecos();
        } catch (err) {
            setErroEndereco(err.message || "Erro ao salvar endereço.");
        } finally {
            setSalvandoEndereco(false);
        }
    }

    async function handleExcluirEndereco(id) {
        if (!window.confirm("Deseja realmente remover este endereço?")) return;
        const token = obterToken();
        try {
            const resposta = await fetch(`${apiBase}/users/${userId}/enderecos/${id}`, {
                method: "DELETE",
                headers: { Authorization: `Bearer ${token}` }
            });
            if (resposta.ok) {
                await carregarEnderecos();
            }
        } catch (e) {
            console.error("Erro ao excluir endereço:", e);
        }
    }

    if (carregando) {
        return (
            <div className="conta-page">
                <p className="mensagem-carregando" role="status">Carregando seus dados...</p>
            </div>
        );
    }

    if (!usuario) {
        return (
            <div className="conta-page">
                <div className="conta-layout">
                    <div>
                        <p className="mensagem-erro" role="alert">{erro}</p>
                        <button className="btn-principal" onClick={carregar}>Tentar novamente</button>
                    </div>
                </div>
            </div>
        );
    }

    const ano = usuario.criado_em ? new Date(usuario.criado_em).getFullYear() : NaN;
    const clienteDesde = Number.isNaN(ano) ? "Cliente doce" : `Cliente doce desde ${ano}`;
    const hoje = new Date().toISOString().slice(0, 10);

    return (
        <div className="conta-page">
            <header className="conta-topbar">
                <div className="conta-topbar-inner">
                    <Link to="/home" className="conta-logo">
                        <span className="conta-logo-icone">C</span>
                        <span className="conta-logo-texto">Candyland</span>
                    </Link>
                    <Link to="/home" className="conta-voltar">Voltar para as lojas</Link>
                </div>
            </header>

            <div className="conta-layout">
                <aside className="conta-menu">
                    <div className="conta-menu-perfil">
                        <span className="conta-avatar">{iniciais(usuario.nome_completo)}</span>
                        <div>
                            <strong className="conta-menu-nome">{usuario.nome_completo}</strong>
                            <small className="conta-menu-sub">{clienteDesde}</small>
                        </div>
                    </div>

                    <nav className="conta-menu-nav">
                        <button type="button" className="conta-menu-item conta-menu-item-ativo">
                            <span className="conta-menu-numero">01</span>
                            Dados pessoais
                        </button>
                    </nav>

                    <button type="button" className="conta-menu-sair" onClick={handleSair}>
                        Sair da conta
                    </button>
                </aside>

                <main className="conta-conteudo">
                    <p className="conta-eyebrow">MINHA CONTA</p>
                    <h1 className="conta-titulo">Dados pessoais</h1>
                    <p className="conta-subtitulo">
                        Mantenha seus dados e endereços atualizados para receber seus pedidos sem imprevistos.
                    </p>

                    <form className="conta-card" onSubmit={handleSubmit} style={{ marginBottom: "32px" }}>
                        <div className="conta-foto">
                            <span className="conta-avatar conta-avatar-grande">
                                {iniciais(usuario.nome_completo)}
                            </span>
                            <div className="conta-foto-textos">
                                <strong>Foto de perfil</strong>
                                <p>PNG ou JPG com até 5 MB</p>
                                <button type="button" className="btn-contorno" disabled>
                                    Alterar foto
                                </button>
                            </div>
                        </div>

                        {erro && <p className="auth-error" role="alert">{erro}</p>}
                        {sucesso && <p className="auth-success" role="status">{sucesso}</p>}

                        <div className="conta-grid">
                            <div className="conta-campo">
                                <label htmlFor="conta-nome">Nome completo</label>
                                <input
                                    id="conta-nome"
                                    type="text"
                                    value={nome}
                                    onChange={(e) => setNome(e.target.value)}
                                    autoComplete="name"
                                />
                            </div>

                            <div className="conta-campo">
                                <label htmlFor="conta-celular">Celular</label>
                                <input
                                    id="conta-celular"
                                    type="text"
                                    value={formatarCelular(usuario.telefone)}
                                    readOnly
                                />
                            </div>

                            <div className="conta-campo conta-campo-cheio">
                                <label htmlFor="conta-email">E-mail</label>
                                <input
                                    id="conta-email"
                                    type="email"
                                    value={usuario.email || ""}
                                    readOnly
                                />
                            </div>

                            <div className="conta-campo">
                                <label htmlFor="conta-nascimento">Data de nascimento</label>
                                <input
                                    id="conta-nascimento"
                                    type="date"
                                    value={nascimento}
                                    min="1900-01-01"
                                    max={hoje}
                                    onChange={(e) => setNascimento(e.target.value)}
                                />
                            </div>

                            <div className="conta-campo">
                                <label htmlFor="conta-cpf">CPF</label>
                                <input
                                    id="conta-cpf"
                                    type="text"
                                    value={mascararCpf(usuario.cpf)}
                                    readOnly
                                />
                            </div>
                        </div>

                        <div className="conta-acoes">
                            <button
                                type="submit"
                                className="primary-button conta-salvar"
                                disabled={!alterado || salvando}
                            >
                                {salvando ? "Salvando..." : "Salvar alterações"}
                            </button>
                        </div>
                    </form>

                    <div className="conta-card">
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
                            <div>
                                <p className="conta-eyebrow">ENTREGA</p>
                                <h2 style={{ margin: 0, fontSize: "22px" }}>Meus Endereços</h2>
                            </div>
                            {!exibirFormEndereco && (
                                <button type="button" className="btn-principal btn-pequeno" onClick={handleNovoEndereco}>
                                    + Adicionar Endereço
                                </button>
                            )}
                        </div>

                        {sucessoEndereco && <p className="auth-success" role="status">{sucessoEndereco}</p>}

                        {exibirFormEndereco && (
                            <form onSubmit={handleSalvarEndereco} style={{ background: "#fff5f2", padding: "20px", borderRadius: "16px", marginBottom: "24px", border: "1px solid var(--borda)" }}>
                                <h3 style={{ marginTop: 0, marginBottom: "16px" }}>
                                    {formEndereco.id ? "Editar Endereço" : "Novo Endereço de Entrega"}
                                </h3>

                                {erroEndereco && <p className="auth-error" role="alert">{erroEndereco}</p>}

                                <div className="form-grid-two">
                                    <div className="form-field">
                                        <label htmlFor="end-cep">CEP</label>
                                        <input
                                            id="end-cep"
                                            name="cep"
                                            value={formEndereco.cep}
                                            onChange={handleAddressFormChange}
                                            placeholder="00000-000"
                                            maxLength={9}
                                            required
                                        />
                                        {loadingCep && <small className="field-message">Buscando CEP...</small>}
                                    </div>
                                    <div className="form-field">
                                        <label htmlFor="end-numero">Número</label>
                                        <input
                                            id="end-numero"
                                            name="numero"
                                            value={formEndereco.numero}
                                            onChange={handleAddressFormChange}
                                            required
                                        />
                                    </div>
                                </div>

                                <div className="form-field">
                                    <label htmlFor="end-rua">Rua / Logradouro</label>
                                    <input
                                        id="end-rua"
                                        name="rua"
                                        value={formEndereco.rua}
                                        onChange={handleAddressFormChange}
                                        required
                                    />
                                </div>

                                <div className="form-grid-two">
                                    <div className="form-field">
                                        <label htmlFor="end-complemento">Complemento (opcional)</label>
                                        <input
                                            id="end-complemento"
                                            name="complemento"
                                            value={formEndereco.complemento}
                                            onChange={handleAddressFormChange}
                                        />
                                    </div>
                                    <div className="form-field">
                                        <label htmlFor="end-bairro">Bairro</label>
                                        <input
                                            id="end-bairro"
                                            name="bairro"
                                            value={formEndereco.bairro}
                                            onChange={handleAddressFormChange}
                                            required
                                        />
                                    </div>
                                </div>

                                <div className="form-grid-two">
                                    <div className="form-field">
                                        <label htmlFor="end-cidade">Cidade</label>
                                        <input
                                            id="end-cidade"
                                            name="cidade"
                                            value={formEndereco.cidade}
                                            onChange={handleAddressFormChange}
                                            required
                                        />
                                    </div>
                                    <div className="form-field">
                                        <label htmlFor="end-estado">UF</label>
                                        <input
                                            id="end-estado"
                                            name="estado"
                                            value={formEndereco.estado}
                                            onChange={handleAddressFormChange}
                                            maxLength={2}
                                            required
                                        />
                                    </div>
                                </div>

                                <div className="form-field">
                                    <label htmlFor="end-referencia">Ponto de referência (opcional)</label>
                                    <input
                                        id="end-referencia"
                                        name="referencia"
                                        value={formEndereco.referencia}
                                        onChange={handleAddressFormChange}
                                        placeholder="Ex.: Próximo à padaria"
                                    />
                                </div>

                                <div className="form-field" style={{ display: "flex", alignItems: "center", gap: "8px", marginTop: "12px" }}>
                                    <input
                                        type="checkbox"
                                        id="end-principal"
                                        name="principal"
                                        checked={formEndereco.principal}
                                        onChange={handleAddressFormChange}
                                        style={{ width: "18px", height: "18px" }}
                                    />
                                    <label htmlFor="end-principal" style={{ margin: 0, cursor: "pointer" }}>
                                        Definir como endereço principal
                                    </label>
                                </div>

                                <div style={{ display: "flex", gap: "10px", marginTop: "20px" }}>
                                    <button type="submit" className="primary-button" disabled={salvandoEndereco}>
                                        {salvandoEndereco ? "Salvando..." : "Salvar Endereço"}
                                    </button>
                                    <button
                                        type="button"
                                        className="btn-contorno"
                                        onClick={() => setExibirFormEndereco(false)}
                                    >
                                        Cancelar
                                    </button>
                                </div>
                            </form>
                        )}

                        {carregandoEnderecos ? (
                            <p className="mensagem-carregando">Carregando seus endereços...</p>
                        ) : enderecos.length === 0 ? (
                            <p className="mensagem-vazia">Nenhum endereço cadastrado. Adicione um para poder receber entregas em casa.</p>
                        ) : (
                            <div className="checkout-address-list">
                                {enderecos.map((end) => (
                                    <div key={end.id} className="checkout-address-card">
                                        <div className="checkout-address-card-inner">
                                            <div>
                                                <strong className="checkout-address-text-street">
                                                    {end.rua}, {end.numero} {end.complemento ? `(${end.complemento})` : ""}
                                                </strong>
                                                <small className="checkout-address-text-details">
                                                    {end.bairro} — {end.cidade}/{end.estado} · CEP {end.cep}
                                                </small>
                                            </div>
                                        </div>
                                        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                                            {end.principal && (
                                                <span className="checkout-address-tag-principal">Principal</span>
                                            )}
                                            <button
                                                type="button"
                                                className="btn-contorno btn-pequeno"
                                                onClick={() => handleEditarEndereco(end)}
                                            >
                                                Editar
                                            </button>
                                            <button
                                                type="button"
                                                className="btn-contorno btn-pequeno"
                                                style={{ borderColor: "var(--erro)", color: "var(--erro)" }}
                                                onClick={() => handleExcluirEndereco(end.id)}
                                            >
                                                Excluir
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </main>
            </div>
        </div>
    );
}

export default DadosPessoais;