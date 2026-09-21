import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { maskCep, maskCpf, maskCnpj } from "../utils/masks";
import VerifiedPhoneInput from "../components/VerifiedPhoneInput";
import { isValidCep, isValidCnpj, isValidCpf, isValidEmail, isValidPhone } from "../utils/validators";
import { getAddressByCep } from "../services/addressService";
import { createRestaurant } from "../services/restaurantService";
import { useAuth } from "../context/AuthContext";

function BusinessRegister() {
    const navigate = useNavigate();
    const location = useLocation();
    const { entrar } = useAuth();
    const dadosAutenticacao = location.state || {};

    const [form, setForm] = useState({
        cnpj: "",
        companyName: "",
        tradeName: "",
        responsibleName: "",
        responsibleCpf: "",
        email: dadosAutenticacao.email || "",
        phone: dadosAutenticacao.telefone || "",
        cep: "",
        address: "",
        number: "",
        complement: "",
        neighborhood: "",
        city: "",
        state: ""
    });

    const [cepError, setCepError] = useState("");
    const [loadingCep, setLoadingCep] = useState(false);
    const [loading, setLoading] = useState(false);

    async function handleCepChange(event) {
        const value = maskCep(event.target.value);

        setForm((currentForm) => ({
            ...currentForm,
            cep: value
        }));

        setCepError("");

        const cleanCep = value.replace(/\D/g, "");

        if (cleanCep.length !== 8) {
            return;
        }

        try {
            setLoadingCep(true);

            const address = await getAddressByCep(cleanCep);

            setForm((currentForm) => ({
                ...currentForm,
                cep: value,
                address: address.address,
                neighborhood: address.neighborhood,
                city: address.city,
                state: address.state
            }));
        } catch (error) {
            setCepError("CEP não encontrado.");
        } finally {
            setLoadingCep(false);
        }
    }

    function handleChange(event) {
        const { name, value } = event.target;

        let formattedValue = value;

        if (name === "cnpj") {
            formattedValue = maskCnpj(value);
        }

        if (name === "responsibleCpf") {
            formattedValue = maskCpf(value);
        }

        setForm((currentForm) => ({
            ...currentForm,
            [name]: formattedValue
        }));
    }

    async function handleSubmit(event) {
        event.preventDefault();

        if (!isValidCnpj(form.cnpj)) {
            alert("Informe um CNPJ válido.");
            return;
        }

        if (!form.companyName.trim()) {
            alert("Informe a razão social.");
            return;
        }

        if (!form.tradeName.trim()) {
            alert("Informe o nome fantasia.");
            return;
        }

        if (!form.responsibleName.trim()) {
            alert("Informe o nome do responsável.");
            return;
        }

        if (!isValidCpf(form.responsibleCpf)) {
            alert("Informe um CPF válido para o responsável.");
            return;
        }

        if (!isValidPhone(form.phone)) {
            alert("Informe um celular válido.");
            return;
        }

        if (!isValidEmail(form.email)) {
            alert("Informe um e-mail válido.");
            return;
        }

        if (!isValidCep(form.cep)) {
            alert("Informe um CEP válido.");
            return;
        }

        if (!form.address.trim()) {
            alert("Informe o endereço.");
            return;
        }

        if (!form.number.trim()) {
            alert("Informe o número.");
            return;
        }

        if (!form.neighborhood.trim()) {
            alert("Informe o bairro.");
            return;
        }

        if (!form.city.trim()) {
            alert("Informe a cidade.");
            return;
        }

        if (!form.state.trim()) {
            alert("Informe o estado.");
            return;
        }

        const dados = {
            cnpj: form.cnpj,
            razao_social: form.companyName.trim(),
            nome: form.tradeName.trim(),
            nome_responsavel: form.responsibleName.trim(),
            email: form.email.trim(),
            telefone: form.phone,
            cpf_responsavel: form.responsibleCpf,
            tentativa_id: dadosAutenticacao.tentativaId,
            endereco: {
                cep: form.cep,
                rua: form.address.trim(),
                numero: form.number.trim(),
                complemento: form.complement.trim() || null,
                bairro: form.neighborhood.trim(),
                cidade: form.city.trim(),
                estado: form.state.trim().toUpperCase()
            }
        };

        try {
            setLoading(true);

            const resultado = await createRestaurant(dados);

            console.log("Cadastro empresarial realizado:", resultado);

            if (resultado.dados?.token) {
                entrar({
                    ...resultado.dados.restaurante,
                    ...resultado.dados,
                    tipo_conta: "BUSINESS",
                    token: resultado.dados.token
                });
            }

            alert("Cadastro empresarial realizado com sucesso!");
            navigate("/business");
        } catch (error) {
            console.error("Erro no cadastro empresarial:", error);
            alert(error.message || "Erro ao realizar cadastro empresarial.");
        } finally {
            setLoading(false);
        }
    }

    return (
        <main className="auth-page">
            <section className="form-card">
                <header className="form-header">
                    <button
                        type="button"
                        className="back-button"
                        onClick={() => navigate("/register", { state: dadosAutenticacao })}>
                        ← Voltar
                    </button>

                    <h1>CandyLand</h1>
                    <h2>Criar conta empresarial</h2>
                    <p>Cadastre sua empresa para começar.</p>
                </header>

                <form onSubmit={handleSubmit}>
                    <div className="form-section">
                        <h3>Dados da empresa</h3>

                        <div className="form-field">
                            <label htmlFor="cnpj">CNPJ</label>
                            <input
                                id="cnpj"
                                name="cnpj"
                                type="text"
                                value={form.cnpj}
                                onChange={handleChange}
                                placeholder="00.000.000/0000-00"
                                inputMode="numeric"
                            />
                        </div>

                        <div className="form-field">
                            <label htmlFor="companyName">Razão social</label>
                            <input
                                id="companyName"
                                name="companyName"
                                type="text"
                                value={form.companyName}
                                onChange={handleChange}
                                placeholder="Razão social"
                            />
                        </div>

                        <div className="form-field">
                            <label htmlFor="tradeName">Nome fantasia</label>
                            <input
                                id="tradeName"
                                name="tradeName"
                                type="text"
                                value={form.tradeName}
                                onChange={handleChange}
                                placeholder="Nome fantasia"
                            />
                        </div>
                    </div>

                    <div className="form-section">
                        <h3>Responsável</h3>

                        <div className="form-field">
                            <label htmlFor="responsibleName">
                                Nome do responsável
                            </label>
                            <input
                                id="responsibleName"
                                name="responsibleName"
                                type="text"
                                value={form.responsibleName}
                                onChange={handleChange}
                                placeholder="Nome completo"
                            />
                        </div>

                        <div className="form-field">
                            <label htmlFor="responsibleCpf">
                                CPF do responsável
                            </label>
                            <input
                                id="responsibleCpf"
                                name="responsibleCpf"
                                type="text"
                                value={form.responsibleCpf}
                                onChange={handleChange}
                                placeholder="000.000.000-00"
                                inputMode="numeric"
                            />
                        </div>

                        <div className="form-field">
                            <label htmlFor="phone">Celular</label>
                            <VerifiedPhoneInput value={form.phone} />
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
                            <input
                                id="cep"
                                name="cep"
                                type="text"
                                value={form.cep}
                                onChange={handleCepChange}
                                placeholder="00000-000"
                                inputMode="numeric"
                            />

                            {loadingCep && (
                                <small className="field-message">
                                    Buscando endereço...
                                </small>
                            )}

                            {cepError && (
                                <small className="field-error">
                                    {cepError}
                                </small>
                            )}
                        </div>

                        <div className="form-field">
                            <label htmlFor="address">Endereço</label>
                            <input
                                id="address"
                                name="address"
                                type="text"
                                value={form.address}
                                onChange={handleChange}
                                placeholder="Rua, avenida..."
                            />
                        </div>

                        <div className="form-row">
                            <div className="form-field">
                                <label htmlFor="number">Número</label>
                                <input
                                    id="number"
                                    name="number"
                                    type="text"
                                    value={form.number}
                                    onChange={handleChange}
                                    placeholder="123"
                                />
                            </div>

                            <div className="form-field">
                                <label htmlFor="complement">Complemento</label>
                                <input
                                    id="complement"
                                    name="complement"
                                    type="text"
                                    value={form.complement}
                                    onChange={handleChange}
                                    placeholder="Sala, loja..."
                                />
                            </div>
                        </div>

                        <div className="form-field">
                            <label htmlFor="neighborhood">Bairro</label>
                            <input
                                id="neighborhood"
                                name="neighborhood"
                                type="text"
                                value={form.neighborhood}
                                onChange={handleChange}
                                placeholder="Seu bairro"
                            />
                        </div>

                        <div className="form-row">
                            <div className="form-field">
                                <label htmlFor="city">Cidade</label>
                                <input
                                    id="city"
                                    name="city"
                                    type="text"
                                    value={form.city}
                                    onChange={handleChange}
                                    placeholder="Sua cidade"
                                />
                            </div>

                            <div className="form-field">
                                <label htmlFor="state">Estado</label>
                                <input
                                    id="state"
                                    name="state"
                                    type="text"
                                    value={form.state}
                                    onChange={handleChange}
                                    placeholder="SP"
                                    maxLength="2"
                                />
                            </div>
                        </div>
                    </div>

                    <button type="submit" className="primary-button" disabled={loading}>
                        {loading ? "Criando empresa..." : "Criar conta empresarial"}
                    </button>
                </form>
            </section>
        </main>
    );
}

export default BusinessRegister;