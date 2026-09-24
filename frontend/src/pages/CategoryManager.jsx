import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { CATEGORY_TYPES } from "../utils/categoryTypes";
import { getCategories, createCategory, updateCategory, deleteCategory } from "../services/categoryService";

function CategoryManager() {
    const navigate = useNavigate();
    const [categorias, setCategorias] = useState([]);
    const [loading, setLoading] = useState(true);
    const [erro, setErro] = useState("");
    const [processando, setProcessando] = useState(null);

    useEffect(() => {
        carregar();
    }, []);

    async function carregar() {
        try {
            setLoading(true);
            const dados = await getCategories();
            setCategorias(dados);
        } catch (error) {
            setErro(error.message);
        } finally {
            setLoading(false);
        }
    }

    function encontrarCategoria(nome) {
        return categorias.find((c) => c.nome === nome);
    }

    async function handleAdicionar(tipo) {
        setErro("");
        setProcessando(tipo.nome);
        try {
            await createCategory(tipo.nome);
            await carregar();
        } catch (error) {
            setErro(error.message);
        } finally {
            setProcessando(null);
        }
    }

    async function handleToggleAtiva(categoria) {
        setErro("");
        setProcessando(categoria.nome);
        try {
            await updateCategory(categoria.id, { ativa: !categoria.ativa });
            await carregar();
        } catch (error) {
            setErro(error.message);
        } finally {
            setProcessando(null);
        }
    }

    async function handleRemover(categoria) {
        if (!window.confirm(`Remover a categoria "${categoria.nome}"?`)) return;
        setErro("");
        setProcessando(categoria.nome);
        try {
            await deleteCategory(categoria.id);
            await carregar();
        } catch (error) {
            setErro(error.message);
        } finally {
            setProcessando(null);
        }
    }

    return (
        <main className="dashboard-page">
            <section className="form-card" style={{ maxWidth: 760 }}>
                <header className="form-header">
                    <button type="button" className="back-button" onClick={() => navigate("/business")}>
                        ← Voltar
                    </button>
                    <h2>Categorias do seu cardápio</h2>
                    <p>Escolha quais categorias sua loja vende. Clique para ativar ou desativar.</p>
                </header>

                {erro && <p className="field-error">{erro}</p>}
                {loading && <p>Carregando...</p>}

                {!loading && (
                    <div className="category-grid">
                        {CATEGORY_TYPES.map((tipo) => {
                            const existente = encontrarCategoria(tipo.nome);
                            const ocupado = processando === tipo.nome;

                            if (!existente) {
                                return (
                                    <button
                                        key={tipo.nome}
                                        type="button"
                                        className="category-card category-card-add"
                                        onClick={() => handleAdicionar(tipo)}
                                        disabled={ocupado}
                                    >
                                        <span className="category-emoji">{tipo.emoji}</span>
                                        <span>{tipo.nome}</span>
                                        <span className="category-add-label">+ Adicionar</span>
                                    </button>
                                );
                            }

                            return (
                                <div
                                    key={tipo.nome}
                                    className={existente.ativa ? "category-card category-card-active" : "category-card category-card-inactive"}
                                >
                                    <span className="category-emoji">{tipo.emoji}</span>
                                    <span>{tipo.nome}</span>

                                    <button
                                        type="button"
                                        className="category-toggle"
                                        onClick={() => handleToggleAtiva(existente)}
                                        disabled={ocupado}
                                    >
                                        {existente.ativa ? "Ativa" : "Inativa"}
                                    </button>

                                    <button
                                        type="button"
                                        className="category-remove"
                                        onClick={() => handleRemover(existente)}
                                        disabled={ocupado}
                                    >
                                        Remover
                                    </button>
                                </div>
                            );
                        })}
                    </div>
                )}
            </section>
        </main>
    );
}

export default CategoryManager;