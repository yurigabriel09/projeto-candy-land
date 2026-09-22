import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import Header from "../components/Header";
import { getRestaurants } from "../services/restaurantService";
import AddressAutocomplete from "../components/AddressAutocomplete";
import { saveSelectedLocation } from "../services/locationService";

const ATALHOS = [
  { emoji: "🍰", nome: "Bolos", busca: "bolo" },
  { emoji: "🍫", nome: "Chocolates", busca: "chocolate" },
  { emoji: "🍭", nome: "Pirulitos", busca: "pirulito" },
  { emoji: "🧁", nome: "Cupcakes", busca: "cupcake" },
  { emoji: "🍮", nome: "Pudins", busca: "pudim" },
  { emoji: "🍬", nome: "Balas", busca: "bala" },
  { emoji: "🍩", nome: "Donuts", busca: "donut" },
  { emoji: "🍪", nome: "Cookies", busca: "cookie" },
];

const EMOJIS_LOJA = ["🍰", "🍫", "🍭", "🧁", "🍮", "🍪"];

function Landing() {
  const [endereco, setEndereco] = useState("");
  const [localizacaoSelecionada, setLocalizacaoSelecionada] = useState(null);
  const [lojas, setLojas] = useState([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState("");
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

  const handleSelecionarEndereco = useCallback((localizacao) => {
    setEndereco(localizacao.address);
    setLocalizacaoSelecionada(localizacao);
  }, []);

  function handleEnderecoChange(e) {
    setEndereco(e.target.value);
    setLocalizacaoSelecionada(null);
  }

  function handleBuscar(e) {
    e.preventDefault();

    if (!localizacaoSelecionada) {
      alert("Selecione um endereço entre as sugestões para continuar.");
      return;
    }

    saveSelectedLocation(localizacaoSelecionada);
    navigate("/itens", { state: { localizacao: localizacaoSelecionada } });
  }

  return (
    <div className="pagina-inicial">
      <Header />

      <section className="hero">
        <div className="container hero-conteudo">
          <span className="selo">🍭 Doces de Todos os Mundos</span>

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
            <AddressAutocomplete
              value={endereco}
              onChange={handleEnderecoChange}
              onSelect={handleSelecionarEndereco}
              placeholder="Digite seu endereço de entrega e número"
            />
            <button type="submit" className="btn-principal" disabled={!localizacaoSelecionada}>
              Buscar 🔍
            </button>
          </form>
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
      </section>

      <section className="container secao">
        <h2 className="titulo-secao">Lojas perto de você 🍭</h2>

        {carregando ? (
          <p className="mensagem-carregando">Carregando lojas...</p>
        ) : erro ? (
          <p className="mensagem-erro">{erro}</p>
        ) : lojas.length === 0 ? (
          <p className="mensagem-vazia">
            Ainda não temos lojas cadastradas por aqui.
          </p>
        ) : (
          <div className="grade-lojas">
            {lojas.map((loja, i) => (
              <article
                key={loja.id}
                className="card-loja"
                onClick={() => navigate(`/itens?loja=${loja.id}`)}
              >
                <div className="card-loja-capa">
                  {EMOJIS_LOJA[i % EMOJIS_LOJA.length]}
                </div>
                <div className="card-loja-corpo">
                  <h3>{loja.nome}</h3>
                  <p className="card-loja-tipo">Loja parceira Candyland</p>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>

      <section className="container secao">
        <div className="banners">
          <div className="banner banner-rosa">
            <span className="banner-emoji">🍰</span>
            <h3>Sua doceria no Candyland</h3>
            <p>
              Cadastre sua confeitaria ou doceria e alcance milhares de
              amantes de doce.
            </p>
            <button onClick={() => navigate("/login")} className="btn-branco">
              Saiba mais
            </button>
          </div>
        </div>
      </section>

      <footer className="rodape">
        <div className="container rodape-conteudo">
          <span>🍭 Candyland — Doces de todos os mundos</span>
        </div>
      </footer>
    </div>
  );
}

export default Landing;