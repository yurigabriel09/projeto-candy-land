import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { maskCep, maskCpf } from "../utils/masks";
import VerifiedPhoneInput from "../components/VerifiedPhoneInput";
import { isValidCep, isValidCpf, isValidEmail, isValidPhone } from "../utils/validators";
import { getAddressByCep } from "../services/addressService";
import AddressMap from "../components/AddressMap";
import { createUser } from "../services/userService";
import { useAuth } from "../context/AuthContext";

function PersonalRegister() {
    const navigate = useNavigate();
    const location = useLocation();
    const { entrar } = useAuth();
    const dadosAutenticacao = location.state || {};

    const [form, setForm] = useState({
        name: "",
        birthDate: "",
        cpf: "",
        email: dadosAutenticacao.email || "",
        phone: dadosAutenticacao.telefone || "",
        cep: "",
        address: "",
        number: "",
        complement: "",
        neighborhood: "",
        city: "",
        state: "",
        latitude: null,
        longitude: null
    });

    const [cepError, setCepError] = useState("");
    const [loadingCep, setLoadingCep] = useState(false);
    const [loading, setLoading] = useState(false);
    const [mapLocationKey, setMapLocationKey] = useState("");

    async function handleCepChange(event) {
        const value = maskCep(event.target.value);

        setForm((currentForm) => ({ ...currentForm, cep: value }));
        setCepError("");

        const cleanCep = value.replace(/\D/g, "");

        if (cleanCep.length !== 8) { return; }
        try {
            setLoadingCep(true);

            const address = await getAddressByCep(cleanCep);

            setForm((currentForm) => ({
                ...currentForm,
                cep: value,
                address: address.address,
                neighborhood: address.neighborhood,
                city: address.city,
                state: address.state,
                latitude: null,
                longitude: null
            }));
            setMapLocationKey(`${cleanCep}-${Date.now()}`);
        } catch (error) { setCepError("CEP não encontrado."); } finally { setLoadingCep(false); }
    }

    function handleChange(event) {
        const { name, value } = event.target;
        let formattedValue = value;

        if (name === "cpf") { formattedValue = maskCpf(value); }
        if (name === "cep") { formattedValue = maskCep(value); }

        setForm((currentForm) => ({ ...currentForm, [name]: formattedValue }));
    }

    function handleMapLocationChange(location) {
        setForm((currentForm) => ({
            ...currentForm,
            ...(location.address !== undefined ? { address: location.address } : {}),
            ...(location.number !== undefined && location.number ? { number: location.number } : {}),
            ...(location.cep !== undefined && location.cep ? { cep: location.cep } : {}),
            ...(location.neighborhood !== undefined && location.neighborhood ? { neighborhood: location.neighborhood } : {}),
            ...(location.city !== undefined && location.city ? { city: location.city } : {}),
            ...(location.state !== undefined && location.state ? { state: location.state } : {}),
            latitude: location.latitude,
            longitude: location.longitude
        }));
    }

    async function handleSubmit(event) {
        event.preventDefault();

        if (!form.name.trim()) { alert("Informe seu nome completo."); return; }
        if (!form.birthDate) { alert("Informe sua data de nascimento."); return; }
        if (!isValidCpf(form.cpf)) { alert("Informe um CPF válido."); return; }
        if (!isValidPhone(form.phone)) { alert("Informe um celular válido."); return; }
        if (!isValidEmail(form.email)) { alert("Informe um e-mail válido."); return; }
        if (!isValidCep(form.cep)) { alert("Informe um CEP válido."); return; }
        if (!form.address.trim()) { alert("Informe o endereço."); return; }
        if (!form.number.trim()) { alert("Informe o número."); return; }
        if (!form.neighborhood.trim()) { alert("Informe o bairro."); return; }
        if (!form.city.trim()) { alert("Informe a cidade."); return; }
        if (!form.state.trim()) { alert("Informe o estado."); return; }

        const dados = {
            nome_completo: form.name.trim(),
            cpf: form.cpf,
            telefone: form.phone,
            email: form.email.trim(),
            data_nascimento: form.birthDate,
            tentativa_id: dadosAutenticacao.tentativaId,
            endereco: {
                cep: form.cep,
                rua: form.address.trim(),
                numero: form.number.trim(),
                complemento: form.complement.trim() || null,
                bairro: form.neighborhood.trim(),
                cidade: form.city.trim(),
                estado: form.state.trim().toUpperCase(),
                latitude: form.latitude,
                longitude: form.longitude
            }
        };

        try {
            setLoading(true);

            const resultado = await createUser(dados);

            console.log("Cadastro realizado:", resultado);

            if (resultado.dados?.token) {
                entrar({
                    ...resultado.dados.usuario,
                    ...resultado.dados,
                    tipo_conta: "PERSONAL",
                    token: resultado.dados.token
                });
            }

            alert("Cadastro realizado com sucesso!");
            navigate("/home");
        } catch (error) {
            console.error("Erro no cadastro:", error);
            alert(error.message || "Erro ao realizar cadastro.");
        } finally { setLoading(false); }
    }

    return (
        <main className="auth-page">
            <section className="form-card">
                <header className="form-header">
                    <button type="button" className="back-button" onClick={() => navigate("/register", { state: dadosAutenticacao })}>
                        ← Voltar
                    </button>

                    <h1>CandyLand</h1>
                    <h2>Criar conta</h2>
                    <p>Preencha seus dados para continuar.</p>
                </header>

                <form onSubmit={handleSubmit}>
                    <div className="form-section">
                        <h3>Dados pessoais</h3>

                        <div className="form-field">
                            <label htmlFor="name">Nome completo</label>
                            <input id="name" name="name" type="text" value={form.name} onChange={handleChange} placeholder="Seu nome completo" />
                        </div>

                        <div className="form-field">
                            <label htmlFor="birthDate">Data de nascimento</label>
                            <input id="birthDate" name="birthDate" type="date" value={form.birthDate} onChange={handleChange} />
                        </div>

                        <div className="form-row">
                            <div className="form-field">
                                <label htmlFor="cpf">CPF</label>
                                <input id="cpf" name="cpf" type="text" value={form.cpf} onChange={handleChange} placeholder="000.000.000-00" inputMode="numeric" />
                            </div>

                            <div className="form-field">
                                <label htmlFor="phone">Celular</label>
                                <VerifiedPhoneInput value={form.phone} />
                            </div>
                        </div>

                        <div className="form-field">
                            <label htmlFor="email">E-mail</label>
                            <input id="email" name="email" type="email" value={form.email} disabled />
                        </div>
                    </div>

                    <div className="form-section">
                        <h3>Endereço</h3>

                        <div className="form-field">
                            <label htmlFor="cep">CEP</label>
                            <input id="cep" name="cep" type="text" value={form.cep} onChange={handleCepChange} placeholder="00000-000" inputMode="numeric" />

                            {loadingCep && (<small className="field-message">Buscando endereço...</small>)}
                            {cepError && (<small className="field-error">{cepError}</small>)}
                        </div>

                        <div className="form-field">
                            <label htmlFor="address">Endereço</label>
                            <input id="address" name="address" type="text" value={form.address} onChange={handleChange} placeholder="Rua, avenida..." />
                        </div>

                        <div className="form-row">
                            <div className="form-field">
                                <label htmlFor="number">Número</label>
                                <input id="number" name="number" type="text" value={form.number} onChange={handleChange} placeholder="123" />
                            </div>

                            <div className="form-field">
                                <label htmlFor="complement">Complemento</label>
                                <input id="complement" name="complement" type="text" value={form.complement} onChange={handleChange} placeholder="Apto, bloco..." />
                            </div>
                        </div>

                        <div className="form-field">
                            <label htmlFor="neighborhood">Bairro</label>
                            <input id="neighborhood" name="neighborhood" type="text" value={form.neighborhood} onChange={handleChange} placeholder="Seu bairro" />
                        </div>

                        <div className="form-row">
                            <div className="form-field">
                                <label htmlFor="city">Cidade</label>
                                <input id="city" name="city" type="text" value={form.city} onChange={handleChange} placeholder="Sua cidade" />
                            </div>

                            <div className="form-field">
                                <label htmlFor="state">Estado</label>
                                <input id="state" name="state" type="text" value={form.state} onChange={handleChange} placeholder="SP" maxLength="2" />
                            </div>
                        </div>

                        {form.address && (
                            <AddressMap
                                address={[form.address, form.number, form.neighborhood, form.city, form.state, form.cep].filter(Boolean).join(", ")}
                                latitude={form.latitude}
                                longitude={form.longitude}
                                autoLocateKey={mapLocationKey}
                                onLocationChange={handleMapLocationChange}
                            />
                        )}
                    </div>

                    <button type="submit" className="primary-button" disabled={loading}>
                        {loading ? "Criando conta..." : "Criar conta"}
                    </button>
                </form>
            </section>
        </main>
    );
}

export default PersonalRegister;