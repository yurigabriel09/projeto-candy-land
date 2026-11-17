import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import Header from "../components/Header";
import { getRestaurants } from "../services/restaurantService";

const moeda = new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
});

// Barra de categorias do protótipo. "busca" leva para /itens?busca=...
const CATEGORIAS = [
    { emoji: "🍰", nome: "Bolos", busca: "bolo" },
    { emoji: "🍫", nome: "Chocolates", busca: "chocolate" },
    { emoji: "🍭", nome: "Pirulitos", busca: "pirulito" },
    { emoji: "🧁", nome: "Cupcakes", busca: "cupcake" },
    { emoji: "🍮", nome: "Pudins", busca: "pudim" },
    { emoji: "🍬", nome: "Balas", busca: "bala" },
    { emoji: "🍩", nome: "Donuts", busca: "donut" },
    { emoji: "🎂", nome: "Aniversário", busca: "aniversario" },
    { emoji: "🍪", nome: "Cookies", busca: "cookie" },
    { emoji: "🍦", nome: "Sorvetes", busca: "sorvete" },
    { emoji: "✨", nome: "Promoções", busca: "promocao" },
];

const EMOJIS_LOJA = ["🍰", "🍫", "🍭", "🧁", "🍮", "🍪", "🍦", "🎂"];
const SELOS = ["Mais Pedido", "Novo", null, "Premium", "Rápido", null, "Destaque", null];

// PROVISÓRIO: o banco ainda não tem avaliação, distância nem tempo por loja.
// Estes valores de exemplo (fixos por loja) existem só para a tela ficar igual
// ao protótipo. Trocar pelos dados reais quando a avaliação (item 13) existir.
const AMOSTRAS = [
    { nota: 4.9, km: 1.2, tempo: "25-40 min" },
    { nota: 4.8, km: 0.8, tempo: "20-35 min" },
    { nota: 4.7, km: 2.1, tempo: "30-45 min" },
    { nota: 5.0, km: 1.5, tempo: "35-50 min" },
    { nota: 4.6, km: 0.5, tempo: "15-25 min" },
    { nota: 4.8, km: 1.8, tempo: "25-40 min" },
];

function textoFrete(loja) {
    const base = Number(loja.taxa_entrega_base || 0);
    const porKm = Number(loja.taxa_entrega_por_km || 0);
    if (base === 0 && porKm === 0) return "Grátis";
    return moeda.format(base);
}

const FILTROS_INICIAIS = {
    ordenar: "",
    gratis: false,
    melhores: false,
    distancia: "",
    super: false,
    status: "",
};

function Home() {
    const [lojas, setLojas] = useState([]);
    const [carregando, setCarregando] = useState(true);
    const [erro, setErro] = useState("");
    const [filtros, setFiltros] = useState(FILTROS_INICIAIS);
    const navigate = useNavigate();

    useEffect(() => {
        carregarLojas();
    }, []);

    async function carregarLojas() {
        setCarregando(true);
        setErro("");

        try {
            const dados = await getRestaurants();
            setLojas(dados.filter((loja) => loja.ativo));
        } catch {
            setErro("Não foi possível carregar as lojas agora.");
        } finally {
            setCarregando(false);
        }
    }

    function alterarFiltro(campo, valor) {
        setFiltros((atual) => ({ ...atual, [campo]: valor }));
    }

    const lojasEnriquecidas = useMemo(
        () =>
            lojas.map((loja) => ({
                ...loja,
                emoji: EMOJIS_LOJA[loja.id % EMOJIS_LOJA.length],
                selo: SELOS[loja.id % SELOS.length],
                amostra: AMOSTRAS[loja.id % AMOSTRAS.length],
                frete: textoFrete(loja),
                aberta: loja.status === "ABERTO",
            })),
        [lojas]
    );

    const lojasVisiveis = useMemo(() => {
        let lista = lojasEnriquecidas.filter((loja) => {
            if (filtros.gratis && loja.frete !== "Grátis") return false;
            if (filtros.super && loja.amostra.nota < 4.8) return false;
            if (filtros.status === "abertas" && !loja.aberta) return false;
            if (filtros.distancia && loja.amostra.km > Number(filtros.distancia)) {
                return false;
            }
            return true;
        });

        lista = [...lista];
        if (filtros.melhores || filtros.ordenar === "avaliacao") {
            lista.sort((a, b) => b.amostra.nota - a.amostra.nota);
        } else if (filtros.ordenar === "frete") {
            lista.sort(
                (a, b) =>
                    Number(a.taxa_entrega_base || 0) - Number(b.taxa_entrega_base || 0)
            );
        } else if (filtros.ordenar === "nome") {
            lista.sort((a, b) => a.nome.localeCompare(b.nome, "pt-BR"));
        }
        return lista;
    }, [lojasEnriquecidas, filtros]);

    const temFiltroAtivo = JSON.stringify(filtros) !== JSON.stringify(FILTROS_INICIAIS);

    return (
        <div className="pagina-home">
            <Header />

            <nav className="hm-categorias" aria-label="Categorias">
                <div className="hm-categorias-lista">
                    <button type="button" className="hm-cat hm-cat-ativa">
                        <span aria-hidden="true">🏠</span> Início
                    </button>
                    {CATEGORIAS.map((cat) => (
                        <button
                            key={cat.nome}
                            type="button"
                            className="hm-cat"
                            onClick={() => navigate(`/itens?busca=${cat.busca}`)}
                        >
                            <span aria-hidden="true">{cat.emoji}</span> {cat.nome}
                        </button>
                    ))}
                </div>
            </nav>

            <main className="hm-conteudo">
                <div className="hm-filtros">
                    <label className="hm-pilula hm-pilula-select">
                        <select
                            value={filtros.ordenar}
                            onChange={(e) => alterarFiltro("ordenar", e.target.value)}
                            aria-label="Ordenar"
                        >
                            <option value="">Ordenar</option>
                            <option value="avaliacao">Melhor avaliação</option>
                            <option value="frete">Menor frete</option>
                            <option value="nome">Nome (A-Z)</option>
                        </select>
                    </label>

                    <button
                        type="button"
                        className={`hm-pilula${filtros.gratis ? " hm-pilula-ativa" : ""}`}
                        aria-pressed={filtros.gratis}
                        onClick={() => alterarFiltro("gratis", !filtros.gratis)}
                    >
                        Entrega Grátis
                    </button>

                    <button
                        type="button"
                        className={`hm-pilula${filtros.melhores ? " hm-pilula-ativa" : ""}`}
                        aria-pressed={filtros.melhores}
                        onClick={() => alterarFiltro("melhores", !filtros.melhores)}
                    >
                        Mais Bem Avaliados
                    </button>

                    <label className="hm-pilula hm-pilula-select">
                        <select
                            value={filtros.distancia}
                            onChange={(e) => alterarFiltro("distancia", e.target.value)}
                            aria-label="Distância"
                        >
                            <option value="">Distância</option>
                            <option value="1">Até 1 km</option>
                            <option value="2">Até 2 km</option>
                            <option value="5">Até 5 km</option>
                        </select>
                    </label>

                    <button
                        type="button"
                        className={`hm-pilula${filtros.super ? " hm-pilula-ativa" : ""}`}
                        aria-pressed={filtros.super}
                        onClick={() => alterarFiltro("super", !filtros.super)}
                    >
                        Super Lojas
                    </button>

                    <label className="hm-pilula hm-pilula-select">
                        <select
                            value={filtros.status}
                            onChange={(e) => alterarFiltro("status", e.target.value)}
                            aria-label="Filtros"
                        >
                            <option value="">Filtros</option>
                            <option value="abertas">Abertas agora</option>
                        </select>
                    </label>

                    <button
                        type="button"
                        className="hm-pilula"
                        disabled={!temFiltroAtivo}
                        onClick={() => setFiltros(FILTROS_INICIAIS)}
                    >
                        Limpar
                    </button>
                </div>

                <section className="hm-banner" aria-label="Oferta especial">
                    <div className="hm-banner-texto">
                        <span className="hm-banner-selo">🎁 Oferta especial de hoje</span>
                        <h2>Frete grátis em qualquer doce!</h2>
                        <p>Use o cupom SWEET10 e ganhe frete grátis no seu próximo pedido</p>
                        <button
                            type="button"
                            className="hm-banner-botao"
                            onClick={() => navigate("/itens")}
                        >
                            Pegar cupom →
                        </button>
                    </div>
                    <span className="hm-banner-doce" aria-hidden="true">🍭</span>
                </section>

                <h2 className="hm-titulo">Lojas perto de você 🍬</h2>

                {carregando ? (
                    <p className="mensagem-carregando">Carregando lojas...</p>
                ) : erro ? (
                    <p className="mensagem-erro">{erro}</p>
                ) : lojasEnriquecidas.length === 0 ? (
                    <p className="mensagem-vazia">
                        Ainda não temos lojas cadastradas por aqui.
                    </p>
                ) : lojasVisiveis.length === 0 ? (
                    <p className="mensagem-vazia">
                        Nenhuma loja encontrada com esses filtros.
                    </p>
                ) : (
                    <div className="hm-grade">
                        {lojasVisiveis.map((loja, i) => (
                            <article
                                key={loja.id}
                                className="hm-card"
                                role="link"
                                tabIndex={0}
                                aria-label={`Ver produtos de ${loja.nome}`}
                                onClick={() => navigate(`/restaurantes/${loja.id}`)}
                                onKeyDown={(event) => {
                                    if (event.key === "Enter") navigate(`/restaurantes/${loja.id}`);
                                }}
                            >
                                <div className={`hm-card-capa hm-capa-${i % 2}`}>
                                    {loja.selo && (
                                        <span className={`hm-selo hm-selo-${i % 2}`}>{loja.selo}</span>
                                    )}
                                    {!loja.aberta && (
                                        <span className="hm-selo hm-selo-fechada">Fechada</span>
                                    )}
                                    <span className="hm-card-emoji" aria-hidden="true">
                                        {loja.emoji}
                                    </span>
                                </div>
                                <div className="hm-card-corpo">
                                    <h3>{loja.nome}</h3>
                                    <p className="hm-card-meta">
                                        <span className="hm-estrela">★ {loja.amostra.nota.toLocaleString("pt-BR", { minimumFractionDigits: 1 })}</span>
                                        <span>·</span>
                                        <span className="hm-card-desc">
                                            {loja.descricao || "Loja parceira Candyland"}
                                        </span>
                                        <span>·</span>
                                        <span>{loja.amostra.km.toLocaleString("pt-BR")} km</span>
                                    </p>
                                    <div className="hm-card-rodape">
                                        <span>{loja.amostra.tempo}</span>
                                        <span
                                            className={
                                                loja.frete === "Grátis"
                                                    ? "hm-frete hm-frete-gratis"
                                                    : "hm-frete"
                                            }
                                        >
                                            {loja.frete}
                                        </span>
                                    </div>
                                </div>
                            </article>
                        ))}
                    </div>
                )}
            </main>
        </div>
    );
}

export default Home;