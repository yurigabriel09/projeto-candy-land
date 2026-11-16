import { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import Header from "../components/Header";
import { getRestaurants } from "../services/restaurantService";

const ATALHOS = [
  { emoji: "🍰", nome: "Bolos", busca: "bolo" },
  { emoji: "🍫", nome: "Chocolates", busca: "chocolate" },
  { emoji: "🍭", nome: "Pirulitos", busca: "pirulito" },
  { emoji: "🧁", nome: "Cupcakes", busca: "cupcake" },
  { emoji: "🍮", nome: "Pudins", busca: "pudim" },
  { emoji: "🍬", nome: "Balas", busca: "bala" },
  { emoji: "🍩", nome: "Donuts", busca: "donut" },
  { emoji: "🎂", nome: "Aniversário", busca: "aniversario" },
  { emoji: "🍪", nome: "Cookies", busca: "cookie" },
  { emoji: "✨", nome: "Promoções", busca: "promocao" },
];

const EMOJIS_LOJA = ["🍰", "🍫", "🍭", "🧁", "🍦", "🍪"];

// Valores de exemplo, só para o visual. O backend ainda não envia nota,
// distância, tempo de entrega nem taxa das lojas.
const EXEMPLOS = [
  { selo: "Mais Pedido", nota: 4.9, tipo: "Bolos & Tortas", km: 1.2, tempo: "25-40 min", taxa: 0 },
  { selo: "Novo", nota: 4.8, tipo: "Brigadeiros", km: 0.8, tempo: "20-35 min", taxa: 4.99 },
  { selo: "", nota: 4.7, tipo: "Pirulitos & Balas", km: 2.1, tempo: "30-45 min", taxa: 6.99 },
  { selo: "Premium", nota: 5, tipo: "Macarons", km: 1.5, tempo: "35-50 min", taxa: 8.99 },
  { selo: "Rápido", nota: 4.6, tipo: "Sorvetes", km: 0.5, tempo: "15-25 min", taxa: 0 },
  { selo: "", nota: 4.8, tipo: "Cookies & Brownies", km: 1.8, tempo: "25-40 min", taxa: 3.99 },
];

function formatarTaxa(taxa) {
  if (!taxa) return "Grátis";
  return `R$ ${taxa.toFixed(2).replace(".", ",")}`;
}

function Landing() {
  const [endereco, setEndereco] = useState("");
  const [lojas, setLojas] = useState([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState("");
  const [ordem, setOrdem] = useState("relevancia");
  const [soGratis, setSoGratis] = useState(false);
  const [soMelhores, setSoMelhores] = useState(false);
  const [soNovidades, setSoNovidades] = useState(false);
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

  function handleBuscar(e) {
    e.preventDefault();
    navigate("/itens");
  }

  const lojasExibidas = useMemo(() => {
    let lista = lojas.map((loja, i) => ({
      ...loja,
      ...EXEMPLOS[i % EXEMPLOS.length],
      emoji: EMOJIS_LOJA[i % EMOJIS_LOJA.length],
    }));
    if (soGratis) lista = lista.filter((l) => l.taxa === 0);
    if (soMelhores) lista = lista.filter((l) => l.nota >= 4.8);
    if (soNovidades) lista = lista.filter((l) => l.selo === "Novo");
    if (ordem === "distancia") lista = [...lista].sort((a, b) => a.km - b.km);
    if (ordem === "nota") lista = [...lista].sort((a, b) => b.nota - a.nota);
    return lista;
  }, [lojas, soGratis, soMelhores, soNovidades, ordem]);

  return (
    <div className="pagina-inicial">
      <Header />

      <section className="hero">
        <div className="container hero-conteudo">
          <span className="selo">✨ Doces de Todos os Mundos</span>

          <h1 className="hero-titulo">
            Um universo
            <br />
            <span className="hero-titulo-destaque">mais doce</span>
            <br />
            te espera
          </h1>

          <p className="hero-subtitulo">
            Descubra confeitarias, docerias e muito mais perto de você.
            <br />
            Peça e receba onde estiver.
          </p>

          <form onSubmit={handleBuscar} className="busca-endereco">
            <span>📍</span>
            <input
              type="text"
              placeholder="Seu endereço de entrega e número"
              value={endereco}
              onChange={(e) => setEndereco(e.target.value)}
            />
            <button type="submit" className="btn-principal">
              Buscar 🍭
            </button>
          </form>

          <p className="lp-confianca">
            <span>🛵 Entrega rápida</span>
            <span>·</span>
            <span>💝 Mais de 500 doçarias</span>
            <span>·</span>
            <span>⭐ Avaliados por você</span>
          </p>
        </div>
      </section>

      <section className="container secao">
        <div className="atalhos">
          {ATALHOS.map((atalho) => (
            <button
              key={atalho.nome}
              className="atalho"
              onClick={() => navigate(`/itens?busca=${atalho.busca}`)}
            >
              <span className="atalho-emoji">{atalho.emoji}</span>
              <span className="atalho-nome">{atalho.nome}</span>
            </button>
          ))}
        </div>

        <div className="lp-filtros">
          <label className="lp-chip lp-chip-select">
            <span className="lp-sr">Ordenar</span>
            <select value={ordem} onChange={(e) => setOrdem(e.target.value)}>
              <option value="relevancia">Ordenar</option>
              <option value="distancia">Menor distância</option>
              <option value="nota">Melhor nota</option>
            </select>
          </label>
          <button
            type="button"
            className={`lp-chip ${soGratis ? "lp-chip-ativo" : ""}`}
            onClick={() => setSoGratis((v) => !v)}
          >
            Entrega Grátis
          </button>
          <button
            type="button"
            className={`lp-chip ${soMelhores ? "lp-chip-ativo" : ""}`}
            onClick={() => setSoMelhores((v) => !v)}
          >
            Mais Bem Avaliados
          </button>
          <button
            type="button"
            className={`lp-chip ${ordem === "distancia" ? "lp-chip-ativo" : ""}`}
            onClick={() => setOrdem((o) => (o === "distancia" ? "relevancia" : "distancia"))}
          >
            Distância
          </button>
          <button
            type="button"
            className={`lp-chip ${soNovidades ? "lp-chip-ativo" : ""}`}
            onClick={() => setSoNovidades((v) => !v)}
          >
            Novidades
          </button>
        </div>
      </section>

      <section className="container secao">
        <h2 className="titulo-secao">Lojas perto de você 🍬</h2>

        {carregando ? (
          <p className="mensagem-carregando">Carregando lojas...</p>
        ) : erro ? (
          <p className="mensagem-erro">{erro}</p>
        ) : lojas.length === 0 ? (
          <p className="mensagem-vazia">
            Ainda não temos lojas cadastradas por aqui.
          </p>
        ) : lojasExibidas.length === 0 ? (
          <p className="mensagem-vazia">
            Nenhuma loja combina com esses filtros.
          </p>
        ) : (
          <div className="lp-grade">
            {lojasExibidas.map((loja) => (
              <article
                key={loja.id}
                className="lp-card"
                onClick={() => navigate(`/itens?loja=${loja.id}`)}
              >
                <div className="lp-card-capa">
                  {loja.selo && <span className="lp-card-selo">{loja.selo}</span>}
                  <span className="lp-card-emoji">{loja.emoji}</span>
                </div>
                <div className="lp-card-corpo">
                  <h3>{loja.nome}</h3>
                  <p className="lp-card-info">
                    <span className="lp-card-nota">★ {loja.nota}</span>
                    <span>·</span>
                    <span>{loja.tipo}</span>
                    <span>·</span>
                    <span>{loja.km.toString().replace(".", ",")} km</span>
                  </p>
                  <div className="lp-card-rodape">
                    <span>{loja.tempo}</span>
                    <strong className={loja.taxa === 0 ? "lp-gratis" : "lp-taxa"}>
                      {formatarTaxa(loja.taxa)}
                    </strong>
                  </div>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>

      <section className="container secao">
        <div className="lp-banners">
          <div className="lp-banner lp-banner-rosa">
            <span className="lp-banner-emoji">🍰</span>
            <h3>Sua doceria no Candyland</h3>
            <p>
              Cadastre sua confeitaria ou doceria e alcance milhares de amantes
              de doce.
            </p>
            <button onClick={() => navigate("/parceiros")} className="lp-btn-branco">
              Saiba mais →
            </button>
          </div>

          <div className="lp-banner lp-banner-escuro">
            <span className="lp-banner-emoji">🛵</span>
            <h3>Quer fazer entregas?</h3>
            <p>
              Seja um entregador Candyland e ganhe mais entregando felicidade em
              forma de doce.
            </p>
            <button
              type="button"
              className="lp-btn-rosa"
              disabled
              title="Em breve"
            >
              Cadastre-se →
            </button>
          </div>
        </div>
      </section>

      <footer className="lp-rodape">
        <div className="container">
          <div className="lp-rodape-topo">
            <div className="lp-rodape-marca">
              <span className="lp-rodape-logo">🍭</span>
              <div>
                <strong>Candyland</strong>
                <span>Doces de todos os mundos</span>
              </div>
            </div>
            <nav className="lp-rodape-links">
              <a
                href="/parceiros"
                onClick={(e) => {
                  e.preventDefault();
                  navigate("/parceiros");
                }}
              >
                Para Parceiros
              </a>
              <span>Seja Entregador</span>
              <span>Central de Ajuda</span>
              <span>Privacidade</span>
            </nav>
          </div>
          <p className="lp-rodape-copy">
            © 2026 Candyland — Doces de todos os mundos ✨
          </p>
        </div>
      </footer>
    </div>
  );
}

export default Landing;