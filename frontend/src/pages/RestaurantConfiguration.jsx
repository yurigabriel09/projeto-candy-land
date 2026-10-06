import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
// import AddressMap from "../components/AddressMap";
import {
    getRestaurantConfiguration,
    updateRestaurantConfiguration,
} from "../services/restaurantService";

const EMPTY_ADDRESS = {
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
};

const EMPTY_FORM = {
    nome: "",
    razao_social: "",
    nome_responsavel: "",
    descricao: "",
    valor_minimo_pedido: "0",
    taxa_entrega_base: "0",
    raio_entrega_km: "",
    horario_funcionamento: "",
};

function RestaurantConfiguration() {
    const navigate = useNavigate();
    const { dadosAutenticacao } = useAuth();
    const restauranteId = Number(dadosAutenticacao?.id);

    const [form, setForm] = useState(EMPTY_FORM);
    const [address, setAddress] = useState(EMPTY_ADDRESS);
    const [readonlyData, setReadonlyData] = useState({
        cnpj: "",
        email: "",
        telefone: "",
        cpf_responsavel: "",
    });
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState("");
    const [error, setError] = useState("");
    const [autoLocateKey, setAutoLocateKey] = useState(0);

    useEffect(() => {
        if (!restauranteId) return;

        async function carregarConfiguracao() {
            try {
                const dados = await getRestaurantConfiguration(restauranteId);
                const restaurante = dados.restaurante || {};
                const endereco = dados.endereco || {};

                setForm({
                    nome: restaurante.nome || "",
                    razao_social: restaurante.razao_social || "",
                    nome_responsavel: restaurante.nome_responsavel || "",
                    descricao: restaurante.descricao || "",
                    valor_minimo_pedido: restaurante.valor_minimo_pedido ?? 0,
                    taxa_entrega_base: restaurante.taxa_entrega_base ?? 0,
                    raio_entrega_km: restaurante.raio_entrega_km ?? "",
                    horario_funcionamento: restaurante.horario_funcionamento || "",
                });

                setReadonlyData({
                    cnpj: restaurante.cnpj || "",
                    email: restaurante.email || "",
                    telefone: restaurante.telefone || "",
                    cpf_responsavel: restaurante.cpf_responsavel || "",
                });

                setAddress({
                    ...EMPTY_ADDRESS,
                    ...endereco,
                });
            } catch (loadError) {
                setError(loadError.message || "Não foi possível carregar os dados do restaurante.");
            } finally {
                setLoading(false);
            }
        }

        carregarConfiguracao();
    }, [restauranteId]);

    function handleChange(event) {
        const { name, value } = event.target;
        setForm((current) => ({ ...current, [name]: value }));
    }

    function handleAddressChange(event) {
        const { name, value } = event.target;
        setAddress((current) => ({ ...current, [name]: value }));
    }

    function handleLocationChange({ latitude, longitude }) {
        setAddress((current) => ({
            ...current,
            latitude,
            longitude,
        }));
    }

    async function handleSubmit(event) {
        event.preventDefault();
        setSaving(true);
        setMessage("");
        setError("");

        try {
            const dados = await updateRestaurantConfiguration(restauranteId, {
                ...form,
                valor_minimo_pedido: Number(form.valor_minimo_pedido || 0),
                taxa_entrega_base: Number(form.taxa_entrega_base || 0),
                raio_entrega_km:
                    form.raio_entrega_km === ""
                        ? null
                        : Number(form.raio_entrega_km),
                endereco: address,
            });

            setForm((current) => ({
                ...current,
                ...dados.restaurante,
                valor_minimo_pedido: dados.restaurante?.valor_minimo_pedido ?? 0,
                taxa_entrega_base: dados.restaurante?.taxa_entrega_base ?? 0,
                raio_entrega_km: dados.restaurante?.raio_entrega_km ?? "",
            }));

            if (dados.endereco) {
                setAddress((current) => ({ ...current, ...dados.endereco }));
            }

            setMessage("Dados do restaurante atualizados com sucesso.");
        } catch (saveError) {
            setError(saveError.message || "Não foi possível salvar os dados.");
        } finally {
            setSaving(false);
        }
    }

    if (loading) {
        return <main className="auth-page"><p>Carregando configuração...</p></main>;
    }

    return (
        <main className="auth-page">
            <section className="form-card restaurant-config-card">
                <header className="form-header">
                    <button
                        type="button"
                        className="back-button"
                        onClick={() => navigate("/business")}
                    >
                        ← Voltar
                    </button>
                    <h1>CandyLand</h1>
                    <h2>Configuração do restaurante</h2>
                    <p>Atualize os dados e as informações de entrega da sua doceria.</p>
                </header>

                {error && <p className="field-error">{error}</p>}
                {message && <p className="field-message">{message}</p>}

                <form onSubmit={handleSubmit}>
                    <div className="form-section">
                        <h3>Dados da empresa</h3>

                        <div className="form-field">
                            <label htmlFor="nome">Nome fantasia</label>
                            <input id="nome" name="nome" value={form.nome} onChange={handleChange} required />
                        </div>

                        <div className="form-field">
                            <label htmlFor="razao_social">Razão social</label>
                            <input id="razao_social" name="razao_social" value={form.razao_social} onChange={handleChange} required />
                        </div>

                        <div className="form-field">
                            <label htmlFor="nome_responsavel">Responsável</label>
                            <input id="nome_responsavel" name="nome_responsavel" value={form.nome_responsavel} onChange={handleChange} />
                        </div>

                        <div className="form-field">
                            <label htmlFor="descricao">Descrição</label>
                            <textarea id="descricao" name="descricao" value={form.descricao} onChange={handleChange} rows="4" maxLength="255" />
                        </div>
                    </div>

                    <div className="form-section">
                        <h3>Dados de entrega</h3>

                        <div className="form-grid-two">
                            <div className="form-field">
                                <label htmlFor="valor_minimo_pedido">Valor mínimo do pedido</label>
                                <input id="valor_minimo_pedido" name="valor_minimo_pedido" type="number" min="0" step="0.01" value={form.valor_minimo_pedido} onChange={handleChange} />
                            </div>

                            <div className="form-field">
                                <label htmlFor="taxa_entrega_base">Taxa base de entrega</label>
                                <input id="taxa_entrega_base" name="taxa_entrega_base" type="number" min="0" step="0.01" value={form.taxa_entrega_base} onChange={handleChange} />
                            </div>
                        </div>

                        <div className="form-field">
                            <label htmlFor="raio_entrega_km">Raio de entrega (km)</label>
                            <input id="raio_entrega_km" name="raio_entrega_km" type="number" min="0" step="0.1" value={form.raio_entrega_km} onChange={handleChange} />
                        </div>

                        <div className="form-field">
                            <label htmlFor="horario_funcionamento">Horário de funcionamento</label>
                            <input id="horario_funcionamento" name="horario_funcionamento" value={form.horario_funcionamento} onChange={handleChange} placeholder="Ex.: Seg a Sex, 09:00 às 18:00" />
                        </div>
                    </div>

                    <div className="form-section">
                        <h3>Endereço comercial</h3>

                        <div className="form-grid-two">
                            <div className="form-field">
                                <label htmlFor="config-cep">CEP</label>
                                <input id="config-cep" name="cep" value={address.cep} onChange={handleAddressChange} />
                            </div>
                            <div className="form-field">
                                <label htmlFor="config-numero">Número</label>
                                <input id="config-numero" name="numero" value={address.numero} onChange={handleAddressChange} required />
                            </div>
                        </div>

                        <div className="form-field">
                            <label htmlFor="config-rua">Rua</label>
                            <input id="config-rua" name="rua" value={address.rua} onChange={handleAddressChange} required />
                        </div>

                        <div className="form-grid-two">
                            <div className="form-field">
                                <label htmlFor="config-complemento">Complemento</label>
                                <input id="config-complemento" name="complemento" value={address.complemento} onChange={handleAddressChange} />
                            </div>
                            <div className="form-field">
                                <label htmlFor="config-bairro">Bairro</label>
                                <input id="config-bairro" name="bairro" value={address.bairro} onChange={handleAddressChange} required />
                            </div>
                        </div>

                        <div className="form-grid-two">
                            <div className="form-field">
                                <label htmlFor="config-cidade">Cidade</label>
                                <input id="config-cidade" name="cidade" value={address.cidade} onChange={handleAddressChange} required />
                            </div>
                            <div className="form-field">
                                <label htmlFor="config-estado">Estado</label>
                                <input id="config-estado" name="estado" maxLength="2" value={address.estado} onChange={handleAddressChange} required />
                            </div>
                        </div>

                        <div className="form-field">
                            <label htmlFor="config-referencia">Referência</label>
                            <input id="config-referencia" name="referencia" value={address.referencia} onChange={handleAddressChange} />
                        </div>

                        <AddressMap
                            address={`${address.rua}, ${address.numero}, ${address.bairro}, ${address.cidade}, ${address.estado}`}
                            latitude={address.latitude}
                            longitude={address.longitude}
                            onLocationChange={handleLocationChange}
                            autoLocateKey={autoLocateKey}
                        />

                        <button
                            type="button"
                            className="secondary-button"
                            onClick={() => setAutoLocateKey((current) => current + 1)}
                        >
                            Atualizar localização no mapa
                        </button>
                    </div>

                    <div className="form-section">
                        <h3>Dados cadastrais</h3>
                        <div className="form-field">
                            <label>CNPJ</label>
                            <input value={readonlyData.cnpj} readOnly />
                        </div>
                        <div className="form-grid-two">
                            <div className="form-field">
                                <label>E-mail</label>
                                <input value={readonlyData.email} readOnly />
                            </div>
                            <div className="form-field">
                                <label>Telefone</label>
                                <input value={readonlyData.telefone} readOnly />
                            </div>
                        </div>
                        <div className="form-field">
                            <label>CPF do responsável</label>
                            <input value={readonlyData.cpf_responsavel} readOnly />
                        </div>
                    </div>

                    <button type="submit" className="primary-button" disabled={saving}>
                        {saving ? "Salvando..." : "Salvar alterações"}
                    </button>
                </form>
            </section>
        </main>
    );
}

export default RestaurantConfiguration;
