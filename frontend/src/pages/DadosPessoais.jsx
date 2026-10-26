import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { getUser, updateUser } from "../services/userService";
import usePendingOrdersCount from "../hooks/usePendingOrdersCount";


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

function DadosPessoais() {
    const { dadosAutenticacao, entrar, sair } = useAuth();
    const pagamentosPendentes = usePendingOrdersCount(Boolean(dadosAutenticacao?.token && dadosAutenticacao?.tipo_conta === "PERSONAL"));

    const [usuario, setUsuario] = useState(null);
    const [nome, setNome] = useState("");
    const [nascimento, setNascimento] = useState("");
    const [carregando, setCarregando] = useState(true);
    const [salvando, setSalvando] = useState(false);
    const [erro, setErro] = useState("");
    const [sucesso, setSucesso] = useState("");

    useEffect(() => {
        carregar();
    }, []);

    function aplicar(dados) {
        setUsuario(dados);
        setNome(dados.nome_completo || "");
        setNascimento(dados.data_nascimento || "");
    }

    async function carregar() {
        setCarregando(true);
        setErro("");
        try {
            const dados = await getUser(dadosAutenticacao.id);
            aplicar(dados);
        } catch (error) {
            setErro(error.message || "Não foi possível carregar seus dados.");
        } finally {
            setCarregando(false);
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

        if (usuario.data_nascimento && !nascimento) {
            setErro("A data de nascimento não pode ficar vazia.");
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

            // A sessão guarda o nome de quando a pessoa entrou. Atualizamos
            // para o cabeçalho do site mostrar o nome novo, mantendo o token.
            entrar({ ...dadosAutenticacao, nome_completo: atualizado.nome_completo });

            setSucesso("Dados atualizados com sucesso.");
        } catch (error) {
            setErro(error.message || "Não foi possível salvar. Tente novamente.");
        } finally {
            setSalvando(false);
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
                        <button type="button" className="conta-menu-item" disabled title="Em breve">
                            <span className="conta-menu-numero">02</span>
                            Configurações
                        </button>
                        <Link to="/minha-conta/pagamentos-pendentes" className="conta-menu-item conta-menu-item-pendentes">
                            <span className="conta-menu-numero">03</span>
                            <span>Pedidos e pagamentos pendentes</span>
                            {pagamentosPendentes > 0 && <span className="cart-badge" aria-label={`${pagamentosPendentes} pedidos pendentes`}>{pagamentosPendentes}</span>}
                        </Link>
                    </nav>

                    <button type="button" className="conta-menu-sair" onClick={handleSair}>
                        Sair da conta
                    </button>
                </aside>

                <main className="conta-conteudo">
                    <p className="conta-eyebrow">MINHA CONTA</p>
                    <h1 className="conta-titulo">Dados pessoais</h1>
                    <p className="conta-subtitulo">
                        Mantenha seus dados atualizados para receber pedidos sem imprevistos.
                    </p>

                    <form className="conta-card" onSubmit={handleSubmit}>
                        <div className="conta-foto">
                            <span className="conta-avatar conta-avatar-grande">
                                {iniciais(usuario.nome_completo)}
                            </span>
                            <div className="conta-foto-textos">
                                <strong>Foto de perfil</strong>
                                <p>PNG ou JPG com até 5 MB</p>
                                <button
                                    type="button"
                                    className="btn-contorno"
                                    disabled
                                    title="Em breve: o envio de foto ainda não está disponível"
                                >
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
                                <small>Usado no login por WhatsApp. Alteração com verificação em breve.</small>
                            </div>

                            <div className="conta-campo conta-campo-cheio">
                                <label htmlFor="conta-email">E-mail</label>
                                <input
                                    id="conta-email"
                                    type="email"
                                    value={usuario.email || ""}
                                    readOnly
                                />
                                <small>Usado no login por código. Alteração com verificação em breve.</small>
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
                </main>
            </div>
        </div>
    );
}

export default DadosPessoais;