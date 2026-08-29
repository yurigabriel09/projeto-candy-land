import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { maskCep, maskCpf, maskCnpj, maskPhone } from "../utils/masks";
import { isValidCep, isValidCnpj, isValidCpf, isValidEmail, isValidPhone } from "../utils/validators";

function BusinessRegister() {
    const navigate = useNavigate();

    const [form, setForm] = useState({
        cnpj: "",
        companyName: "",
        tradeName: "",
        responsibleName: "",
        responsibleCpf: "",
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

    function handleChange(event) {
        const { name, value } = event.target;

        let formattedValue = value;

        if (name === "cnpj") {
            formattedValue = maskCnpj(value);
        }

        if (name === "responsibleCpf") {
            formattedValue = maskCpf(value);
        }

        if (name === "phone") {
            formattedValue = maskPhone(value);
        }

        if (name === "cep") {
            formattedValue = maskCep(value);
        }

        setForm({
            ...form,
            [name]: formattedValue
        });
    }

    function handleSubmit(event) {
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

        console.log("Cadastro empresarial válido:", form);
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

                        <div className="form-field">
                            <label htmlFor="email">E-mail</label>
                            <input
                                id="email"
                                name="email"
                                type="email"
                                value={form.email}
                                onChange={handleChange}
                                placeholder="empresa@email.com"
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
                                onChange={handleChange}
                                placeholder="00000-000"
                                inputMode="numeric"
                            />
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

                    <button type="submit" className="primary-button">
                        Criar conta empresarial
                    </button>
                </form>
            </section>
        </main>
    );
}

export default BusinessRegister;