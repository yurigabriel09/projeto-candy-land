import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { createProduct, getProduct, updateProduct } from "../services/productService";
import { getCategories } from "../services/categoryService";

function ProductForm() {
    const navigate = useNavigate();
    const { produtoId } = useParams();
    const modoEdicao = Boolean(produtoId);

    const [categorias, setCategorias] = useState([]);
    const [loadingCategorias, setLoadingCategorias] = useState(true);
    const [loadingProduto, setLoadingProduto] = useState(modoEdicao);

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

    useEffect(() => {
        async function carregarCategorias() {
            try {
                const dados = await getCategories();
                setCategorias(dados.filter((c) => c.ativa));
            } catch (error) {
                setErro("Não foi possível carregar as categorias.");
            } finally {
                setLoadingCategorias(false);
            }
        }
        carregarCategorias();
    }, []);

    useEffect(() => {
        if (!modoEdicao) return;

        async function carregarProduto() {
            try {
                const produto = await getProduct(produtoId);
                setForm({
                    nome: produto.nome_produto || "",
                    descricao: produto.descricao_produto || "",
                    preco: String(produto.preco_produto ?? ""),
                    qtd_estoque: String(produto.qtd_estoque ?? "0"),
                    categoria_id: String(produto.id_categoria || ""),
                    disponivel: Boolean(produto.produto_disponivel)
                });
            } catch (error) {
                setErro("Não foi possível carregar o produto.");
            } finally {
                setLoadingProduto(false);
            }
        }
        carregarProduto();
    }, [modoEdicao, produtoId]);

    function handleChange(event) {
        const { name, value, type, checked } = event.target;
        setForm((current) => ({
            ...current,
            [name]: type === "checkbox" ? checked : value
        }));
    }

    async function handleSubmit(event) {
        event.preventDefault();
        setErro("");

        if (!form.nome.trim()) { setErro("Informe o nome do produto."); return; }
        if (!form.preco || Number(form.preco) <= 0) { setErro("Informe um preço válido."); return; }
        if (!form.categoria_id) { setErro("Selecione uma categoria."); return; }

        const dados = {
            categoria_id: Number(form.categoria_id),
            nome: form.nome.trim(),
            descricao: form.descricao.trim(),
            preco: Number(form.preco),
            qtd_estoque: Number(form.qtd_estoque),
            disponivel: form.disponivel
        };

        try {
            setLoading(true);
            if (modoEdicao) {
                await updateProduct(produtoId, dados);
            } else {
                await createProduct(dados);
            }
            navigate("/business");
        } catch (error) {
            setErro(error.message || "Erro ao salvar produto.");
        } finally {
            setLoading(false);
        }
    }

    if (!loadingCategorias && categorias.length === 0) {
        return (
            <main className="dashboard-page">
                <section className="form-card">
                    <header className="form-header">
                        <button type="button" className="back-button" onClick={() => navigate("/business")}>
                            ← Voltar
                        </button>
                        <h2>Cadastrar produto</h2>
                    </header>
                    <p className="field-error">Você ainda não tem categorias ativas.</p>
                    <button type="button" className="primary-button" onClick={() => navigate("/business/categories")}>
                        Criar categoria primeiro
                    </button>
                </section>
            </main>
        );
    }

    if (loadingProduto) {
        return (
            <main className="dashboard-page">
                <section className="form-card">
                    <p>Carregando produto...</p>
                </section>
            </main>
        );
    }

    return (
        <main className="dashboard-page">
            <section className="form-card">
                <header className="form-header">
                    <button type="button" className="back-button" onClick={() => navigate("/business")}>
                        ← Voltar
                    </button>
                    <h2>{modoEdicao ? "Editar produto" : "Cadastrar produto"}</h2>
                    <p>{modoEdicao ? "Atualize as informações do item." : "Adicione um novo item ao seu cardápio."}</p>
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
                        <label htmlFor="categoria_id">Categoria</label>
                        <select id="categoria_id" name="categoria_id" value={form.categoria_id} onChange={handleChange}>
                            <option value="">Selecione...</option>
                            {categorias.map((c) => (
                                <option key={c.id} value={c.id}>{c.nome}</option>
                            ))}
                        </select>
                    </div>

                    <div className="form-field form-checkbox">
                        <label htmlFor="disponivel">
                            <input id="disponivel" name="disponivel" type="checkbox" checked={form.disponivel} onChange={handleChange} />
                            Disponível para venda
                        </label>
                    </div>

                    {erro && <p className="field-error">{erro}</p>}

                    <button type="submit" className="primary-button" disabled={loading}>
                        {loading ? "Salvando..." : modoEdicao ? "Salvar alterações" : "Cadastrar produto"}
                    </button>
                </form>
            </section>
        </main>
    );
}

export default ProductForm;