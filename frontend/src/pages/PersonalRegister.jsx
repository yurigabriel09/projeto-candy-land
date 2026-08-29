import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { maskCep, maskCpf, maskPhone } from "../utils/masks";
import {
    isValidCep,
    isValidCpf,
    isValidEmail,
    isValidPhone
} from "../utils/validators";
import { getAddressByCep } from "../services/addressService";

function PersonalRegister() {
    const navigate = useNavigate();

    const [form, setForm] = useState({
        name: "",
        birthDate: "",
        cpf: "",
        phone: "",
        email: "",
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

        if (name === "cpf") {
            formattedValue = maskCpf(value);
        }

        if (name === "phone") {
            formattedValue = maskPhone(value);
        }

        if (name === "cep") {
            formattedValue = maskCep(value);
        }

        setForm((currentForm) => ({
            ...currentForm,
            [name]: formattedValue
        }));
    }

    function handleSubmit(event) {
        event.preventDefault();

        if (!form.name.trim()) {
            alert("Informe seu nome completo.");
            return;
        }

        if (!form.birthDate) {
            alert("Informe sua data de nascimento.");
            return;
        }

        if (!isValidCpf(form.cpf)) {
            alert("Informe um CPF válido.");
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

        console.log("Cadastro válido:", form);
    }

    return (
        <main className="auth-page">
            <section className="form-card">
                <header className="form-header">
                    <button
                        type="button"
                        className="back-button"
                        onClick={() => navigate("/register")}
                    >
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
                            <input
                                id="name"
                                name="name"
                                type="text"
                                value={form.name}
                                onChange={handleChange}
                                placeholder="Seu nome completo"
                            />
                        </div>

                        <div className="form-field">
                            <label htmlFor="birthDate">Data de nascimento</label>
                            <input
                                id="birthDate"
                                name="birthDate"
                                type="date"
                                value={form.birthDate}
                                onChange={handleChange}
                            />
                        </div>

                        <div className="form-row">
                            <div className="form-field">
                                <label htmlFor="cpf">CPF</label>
                                <input
                                    id="cpf"
                                    name="cpf"
                                    type="text"
                                    value={form.cpf}
                                    onChange={handleChange}
                                    placeholder="000.000.000-00"
                                    inputMode="numeric"
                                />
                            </div>

                            <div className="form-field">
                                <label htmlFor="phone">Celular</label>
                                <input
                                    id="phone"
                                    name="phone"
                                    type="tel"
                                    value={form.phone}
                                    onChange={handleChange}
                                    placeholder="(11) 91234-5678"
                                    inputMode="numeric"
                                />
                            </div>
                        </div>

                        <div className="form-field">
                            <label htmlFor="email">E-mail</label>
                            <input
                                id="email"
                                name="email"
                                type="email"
                                value={form.email}
                                onChange={handleChange}
                                placeholder="seu@email.com"
                            />
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
                                    placeholder="Apto, bloco..."
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

                    <button type="submit" className="primary-button">
                        Criar conta
                    </button>
                </form>
            </section>
        </main>
    );
}

export default PersonalRegister;