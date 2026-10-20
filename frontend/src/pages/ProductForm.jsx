import { useEffect, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { createProduct, getProduct, updateProduct, uploadProductImage } from "../services/productService";
import { getCategories } from "../services/categoryService";
import { resolverImagemUrl } from "../utils/imageUrl";

const TIPOS_ACEITOS = ["image/jpeg", "image/png", "image/webp"];
const TAMANHO_MAXIMO = 2 * 1024 * 1024;

function ProductForm() {
    const navigate = useNavigate();
    const location = useLocation();
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
    const [erro, setErro] = useState(location.state?.aviso || "");

    const [arquivoImagem, setArquivoImagem] = useState(null);
    const [previewUrl, setPreviewUrl] = useState("");
    const [imagemAtual, setImagemAtual] = useState(null);

    useEffect(() => {
        if (location.state?.aviso) setErro(location.state.aviso);
    }, [location.state]);

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
                setImagemAtual(produto.imagem_url || null);
            } catch (error) {
                setErro("Não foi possível carregar o produto.");
            } finally {
                setLoadingProduto(false);
            }
        }
        carregarProduto();
    }, [modoEdicao, produtoId]);

    useEffect(() => {
        if (!arquivoImagem) {
            setPreviewUrl("");
            return;
        }
        const url = URL.createObjectURL(arquivoImagem);
        setPreviewUrl(url);
        return () => URL.revokeObjectURL(url);
    }, [arquivoImagem]);

    function handleChange(event) {
        const { name, value, type, checked } = event.target;
        setForm((current) => ({
            ...current,
            [name]: type === "checkbox" ? checked : value
        }));
    }

    function handleImagemChange(event) {
        const arquivo = event.target.files?.[0];
        setErro("");

        if (!arquivo) {
            setArquivoImagem(null);
            return;
        }

        if (!TIPOS_ACEITOS.includes(arquivo.type)) {
            setErro("Formato inválido. Use JPG, PNG ou WEBP.");
            event.target.value = "";
            setArquivoImagem(null);
            return;
        }

        if (arquivo.size > TAMANHO_MAXIMO) {
            setErro("A imagem passa de 2 MB. Escolha um arquivo menor.");
            event.target.value = "";
            setArquivoImagem(null);
            return;
        }

        setArquivoImagem(arquivo);
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

            const produtoSalvo = modoEdicao
                ? await updateProduct(produtoId, dados)
                : await createProduct(dados);

            if (arquivoImagem) {
                try {
                    await uploadProductImage(produtoSalvo.id_produto, arquivoImagem);
                } catch (erroImagem) {
                    const aviso = `Produto salvo, mas a foto não foi enviada: ${erroImagem.message}`;

                    if (modoEdicao) {
                        setErro(aviso);
                    } else {
                        // O produto já existe: vai para a edição, para não criar um duplicado ao tentar de novo
                        setArquivoImagem(null);
                        navigate(`/business/products/${produtoSalvo.id_produto}/edit`, {
                            state: { aviso }
                        });
                    }
                    return;
                }
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

    const imagemExibida = previewUrl || resolverImagemUrl(imagemAtual);

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

                    <div className="form-field">
                        <label htmlFor="imagem">Foto do produto</label>
                        {imagemExibida && (
                            <img
                                className="product-image-preview"
                                src={imagemExibida}
                                alt="Pré-visualização do produto"
                            />
                        )}
                        <input
                            id="imagem"
                            type="file"
                            accept="image/jpeg,image/png,image/webp"
                            onChange={handleImagemChange}
                        />
                        <small className="field-message">JPG, PNG ou WEBP, até 2 MB.</small>
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