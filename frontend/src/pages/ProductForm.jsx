import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { createProduct } from "../services/productService";
import { useAuth } from "../context/AuthContext";

function ProductForm() {
    const navigate = useNavigate();
    const { dadosAutenticacao, autenticado } = useAuth();
    const restauranteId = Number(dadosAutenticacao?.id);

    const [form, setForm] = useState({
        nome: "",
        descricao: "",
        preco: "",
        qtd_estoque: "0",
        categoria_id: "",
        disponivel: true
    });
    const [loading, setLoading] = useState(false);
    const [erro, setErro] = useState("");

    function handleChange(event) {
        const { name, value, type, checked } = event.target;
        setForm((current) => ({
            ...current,
            [name]: type === "checkbox" ? checked : value
        }));
    }

    async function handleSubmit(event) {
        event.preventDefault();

        if (!autenticado || dadosAutenticacao?.tipo_conta !== "BUSINESS" || !Number.isInteger(restauranteId) || restauranteId <= 0) {
            navigate("/business", { replace: true });
            return;
        }
        setErro("");

        if (!form.nome.trim()) { setErro("Informe o nome do produto."); return; }
        if (!form.preco || Number(form.preco) <= 0) { setErro("Informe um preço válido."); return; }
        if (!form.categoria_id) { setErro("Informe o ID da categoria."); return; }

        const dados = {
            restaurante_id: restauranteId,
            categoria_id: Number(form.categoria_id),
            nome: form.nome.trim(),
            descricao: form.descricao.trim(),
            preco: Number(form.preco),
            qtd_estoque: Number(form.qtd_estoque),
            disponivel: form.disponivel
        };

        try {
            setLoading(true);
            await createProduct(dados);
            navigate("/business");
        } catch (error) {
            setErro(error.message || "Erro ao cadastrar produto.");
        } finally {
            setLoading(false);
        }
    }

    return (
        <main className="dashboard-page">
            <section className="form-card">
                <header className="form-header">
                    <button type="button" className="back-button" onClick={() => navigate("/business")}>
                        ← Voltar
                    </button>
                    <h2>Cadastrar produto</h2>
                    <p>Adicione um novo item ao seu cardápio.</p>
                </header>

                <form onSubmit={handleSubmit}>
                    <div className="form-field">
                        <label htmlFor="nome">Nome do produto</label>
                        <input id="nome" name="nome" type="text" value={form.nome} onChange={handleChange} placeholder="Ex: Brigadeiro gourmet" />
                    </div>

                    <div className="form-field">
                        <label htmlFor="descricao">Descrição</label>
                        <input id="descricao" name="descricao" type="text" value={form.descricao} onChange={handleChange} placeholder="Descreva o produto" />
                    </div>

                    <div className="form-row">
                        <div className="form-field">
                            <label htmlFor="preco">Preço (R$)</label>
                            <input id="preco" name="preco" type="number" step="0.01" min="0" value={form.preco} onChange={handleChange} placeholder="0,00" />
                        </div>

                        <div className="form-field">
                            <label htmlFor="qtd_estoque">Estoque</label>
                            <input id="qtd_estoque" name="qtd_estoque" type="number" min="0" value={form.qtd_estoque} onChange={handleChange} />
                        </div>
                    </div>

                    <div className="form-field">
                        <label htmlFor="categoria_id">ID da categoria</label>
                        <input id="categoria_id" name="categoria_id" type="number" value={form.categoria_id} onChange={handleChange} placeholder="Ex: 1" />
                        <small className="field-message">Provisório até existir uma tela de categorias.</small>
                    </div>

                    <div className="form-field form-checkbox">
                        <label htmlFor="disponivel">
                            <input id="disponivel" name="disponivel" type="checkbox" checked={form.disponivel} onChange={handleChange} />
                            Disponível para venda
                        </label>
                    </div>

                    {erro && <p className="field-error">{erro}</p>}

                    <button type="submit" className="primary-button" disabled={loading}>
                        {loading ? "Cadastrando..." : "Cadastrar produto"}
                    </button>
                </form>
            </section>
        </main>
    );
}

export default ProductForm;