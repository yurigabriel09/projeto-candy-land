import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import Header from "../components/Header";
import "./Landing.css";
import { geocodePublicAddress, getRestaurants } from "../services/restaurantService";

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

function valorNumerico(valor) {
  if (valor === null || valor === undefined || valor === "") return null;
  const numero = Number(valor);
  return Number.isFinite(numero) ? numero : null;
}

function formatarMoeda(valor) {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
  }).format(valor);
}

function obterResumoEntrega(loja) {
  const taxaBase = valorNumerico(loja.taxa_entrega_base);
  const taxaPorKm = valorNumerico(loja.taxa_entrega_por_km);

  if (taxaBase === null || taxaPorKm === null) {
    return { gratis: false, texto: "Taxa a consultar" };
  }

  if (taxaBase === 0 && taxaPorKm === 0) {
    return { gratis: true, texto: "Entrega grátis" };
  }

  return {
    gratis: false,
    texto: taxaBase > 0 ? `A partir de ${formatarMoeda(taxaBase)}` : "Taxa por distância",
  };
}

function dataCadastro(loja) {
  if (!loja.dt_cadastro) return 0;
  const data = new Date(loja.dt_cadastro).getTime();
  return Number.isFinite(data) ? data : 0;
}

function lerLocalizacaoSalva() {
  try {
    const salva = sessionStorage.getItem("candyland_delivery_location");
    if (!salva) return null;
    const localizacao = JSON.parse(salva);
    if (
      typeof localizacao?.latitude !== "number" ||
      typeof localizacao?.longitude !== "number" ||
      !localizacao.endereco
    ) return null;
    return localizacao;
  } catch {
    return null;
  }
}

function calcularDistanciaKm(origem, destino) {
  const latitude = Number(destino?.latitude);
  const longitude = Number(destino?.longitude);
  if (
    !origem || !Number.isFinite(latitude) || !Number.isFinite(longitude) ||
    destino.latitude == null || destino.longitude == null
  ) return null;

  const radianos = (graus) => (graus * Math.PI) / 180;
  const dLat = radianos(latitude - origem.latitude);
  const dLng = radianos(longitude - origem.longitude);
  const lat1 = radianos(origem.latitude);
  const lat2 = radianos(latitude);
  const a = Math.sin(dLat / 2) ** 2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLng / 2) ** 2;
  return 6371.0088 * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function formatarDistancia(distancia) {
  return distancia.toLocaleString("pt-BR", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  }) + " km";
}

function Landing() {
  const [lojas, setLojas] = useState([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState("");
  const [ordem, setOrdem] = useState("relevancia");
  const [soGratis, setSoGratis] = useState(false);
  const [somenteAbertas, setSomenteAbertas] = useState(false);
  const [filtrosAbertos, setFiltrosAbertos] = useState(false);
  const [enderecoBusca, setEnderecoBusca] = useState(() => lerLocalizacaoSalva()?.endereco || "");
  const [localizacaoCliente, setLocalizacaoCliente] = useState(() => lerLocalizacaoSalva());
  const [geocodificando, setGeocodificando] = useState(false);
  const [erroEndereco, setErroEndereco] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    let ativo = true;

    async function carregarLojas() {
      setCarregando(true);
      setErro("");
      try {
        const dados = await getRestaurants();
        if (ativo) {
          setLojas(
            dados.filter(
              (loja) =>
                loja.ativo && String(loja.status || "").toUpperCase() !== "SUSPENSO"
            )
          );
        }
      } catch {
        if (ativo) setErro("Não foi possível carregar as lojas agora.");
      } finally {
        if (ativo) setCarregando(false);
      }
    }

    carregarLojas();
    return () => {
      ativo = false;
    };
  }, []);

  const lojasExibidas = useMemo(() => {
    let lista = lojas.map((loja, indice) => ({
      ...loja,
      emoji: EMOJIS_LOJA[indice % EMOJIS_LOJA.length],
      entrega: obterResumoEntrega(loja),
      distancia_km: calcularDistanciaKm(localizacaoCliente, loja),
    }));

    if (soGratis) {
      lista = lista.filter((loja) => loja.entrega.gratis);
    }

    if (somenteAbertas) {
      lista = lista.filter(
        (loja) => String(loja.status || "").toUpperCase() === "ABERTO"
      );
    }

    if (ordem === "menor-taxa") {
      lista = [...lista].sort(
        (a, b) =>
          (valorNumerico(a.taxa_entrega_base) ?? Number.MAX_SAFE_INTEGER) -
          (valorNumerico(b.taxa_entrega_base) ?? Number.MAX_SAFE_INTEGER)
      );
    } else if (ordem === "nome") {
      lista = [...lista].sort((a, b) =>
        a.nome.localeCompare(b.nome, "pt-BR", { sensitivity: "base" })
      );
    } else if (ordem === "novidades") {
      lista = [...lista].sort((a, b) => dataCadastro(b) - dataCadastro(a));
    } else if (ordem === "distancia") {
      lista = [...lista].sort((a, b) =>
        (a.distancia_km ?? Number.MAX_SAFE_INTEGER) -
        (b.distancia_km ?? Number.MAX_SAFE_INTEGER)
      );
    }

    return lista;
  }, [lojas, soGratis, somenteAbertas, ordem, localizacaoCliente]);

  const possuiDistancias = Boolean(
    localizacaoCliente && lojas.some((loja) => calcularDistanciaKm(localizacaoCliente, loja) !== null)
  );

  useEffect(() => {
    if (localizacaoCliente && !carregando && possuiDistancias) {
      setOrdem("distancia");
    }
  }, [localizacaoCliente, carregando, possuiDistancias]);

  async function buscarDocerias(evento) {
    evento.preventDefault();
    const endereco = enderecoBusca.trim();
    if (endereco.length < 8) {
      setErroEndereco("Digite um endereço completo, incluindo número e cidade.");
      return;
    }

    setGeocodificando(true);
    setErroEndereco("");
    try {
      const resultado = await geocodePublicAddress(endereco);
      const localizacao = {
        endereco: resultado.endereco_localizado || endereco,
        latitude: Number(resultado.latitude),
        longitude: Number(resultado.longitude),
      };
      if (!Number.isFinite(localizacao.latitude) || !Number.isFinite(localizacao.longitude)) {
        throw new Error("O serviço de mapas não retornou coordenadas válidas.");
      }
      try {
        sessionStorage.setItem("candyland_delivery_location", JSON.stringify(localizacao));
      } catch {
        // O endereço continua funcionando durante esta visita mesmo sem storage.
      }
      setLocalizacaoCliente(localizacao);
    } catch (erro) {
      setErroEndereco(erro.message || "Não foi possível localizar esse endereço.");
    } finally {
      setGeocodificando(false);
    }
  }

  function abrirLoja(lojaId) {
    const parametros = new URLSearchParams({ loja: String(lojaId) });
    navigate(`/itens?${parametros.toString()}`);
  }

  return (
    <div className="pagina-inicial">
      <Header variant="landing" />

      <section className="hero">
        <span className="lp-decoracao lp-decoracao-1" aria-hidden="true">🍭</span>
        <span className="lp-decoracao lp-decoracao-2" aria-hidden="true">🍬</span>
        <span className="lp-decoracao lp-decoracao-3" aria-hidden="true">🌟</span>
        <span className="lp-decoracao lp-decoracao-4" aria-hidden="true">✨</span>

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

          <form className="lp-busca-endereco" onSubmit={buscarDocerias}>
            <label className="lp-busca-icone" htmlFor="lp-endereco-entrega" aria-hidden="true">📍</label>
            <input
              id="lp-endereco-entrega"
              type="text"
              value={enderecoBusca}
              onChange={(evento) => {
                setEnderecoBusca(evento.target.value);
                setErroEndereco("");
                if (localizacaoCliente) {
                  setLocalizacaoCliente(null);
                  try {
                    sessionStorage.removeItem("candyland_delivery_location");
                  } catch {
                    // A busca atual não depende do armazenamento do navegador.
                  }
                  setOrdem("relevancia");
                }
              }}
              placeholder="Seu endereço de entrega e número"
              aria-label="Endereço de entrega e número"
              autoComplete="street-address"
              maxLength={250}
              required
            />
            <button type="submit" disabled={geocodificando}>
              {geocodificando ? "Localizando..." : "Buscar 🍭"}
            </button>
          </form>
          {erroEndereco && <p className="lp-busca-erro" role="alert">{erroEndereco}</p>}
          {localizacaoCliente && !erroEndereco && (
            <p className="lp-busca-sucesso" role="status">
              <span aria-hidden="true">✓</span> Endereço localizado: {localizacaoCliente.endereco}
            </p>
          )}

          <p className="lp-confianca">
            <span>🚀 Entrega rápida</span>
            <span aria-hidden="true">·</span>
            <span>💝 Mais de 500 docerias</span>
            <span aria-hidden="true">·</span>
            <span>⭐ Avaliados por você</span>
          </p>
        </div>
      </section>

      <main className="lp-conteudo">
        <section className="container secao lp-secao-categorias" aria-label="Categorias de doces">
          <div className="atalhos">
            {ATALHOS.map((atalho) => (
              <button
                key={atalho.nome}
                type="button"
                className="atalho"
                onClick={() => navigate(`/itens?busca=${encodeURIComponent(atalho.busca)}`)}
                aria-label={`Ver ${atalho.nome.toLowerCase()}`}
              >
                <span className="atalho-emoji" aria-hidden="true">{atalho.emoji}</span>
                <span className="atalho-nome">{atalho.nome}</span>
              </button>
            ))}
          </div>

          <div className="lp-filtros" aria-label="Filtros de lojas">
            <label className="lp-chip lp-chip-select">
              <span className="lp-sr">Ordenar lojas</span>
              <select value={ordem} onChange={(e) => setOrdem(e.target.value)}>
                <option value="relevancia">Ordenar</option>
                <option value="menor-taxa">Menor taxa base</option>
                <option value="nome">Nome A–Z</option>
                <option value="distancia" disabled={!possuiDistancias}>Distância</option>
              </select>
            </label>

            <button
              type="button"
              className={`lp-chip ${soGratis ? "lp-chip-ativo" : ""}`}
              aria-pressed={soGratis}
              onClick={() => setSoGratis((valor) => !valor)}
            >
              Entrega Grátis
            </button>

            <button
              type="button"
              className="lp-chip lp-chip-indisponivel"
              disabled
              title="A API ainda não disponibiliza a média de avaliações das lojas."
            >
              Mais Bem Avaliados
            </button>

            <button
              type="button"
              className={`lp-chip ${ordem === "distancia" ? "lp-chip-ativo" : ""} ${!possuiDistancias ? "lp-chip-indisponivel" : ""}`}
              disabled={!possuiDistancias}
              aria-pressed={ordem === "distancia"}
              title={!localizacaoCliente
                ? "Informe seu endereço para ordenar as lojas por distância."
                : !possuiDistancias
                  ? "As lojas cadastradas ainda não possuem coordenadas para calcular a distância."
                  : "Ordenar lojas pela distância do endereço informado."}
              onClick={() => setOrdem((atual) => atual === "distancia" ? "relevancia" : "distancia")}
            >
              Distância
            </button>

            <button
              type="button"
              className={`lp-chip ${ordem === "novidades" ? "lp-chip-ativo" : ""}`}
              aria-pressed={ordem === "novidades"}
              onClick={() => setOrdem((atual) => atual === "novidades" ? "relevancia" : "novidades")}
            >
              Novidades
            </button>

            <div className="lp-filtros-extra">
              <button
                type="button"
                className={`lp-chip ${filtrosAbertos || somenteAbertas ? "lp-chip-ativo" : ""}`}
                aria-expanded={filtrosAbertos}
                aria-controls="lp-menu-filtros"
                onClick={() => setFiltrosAbertos((aberto) => !aberto)}
              >
                Filtros <span aria-hidden="true">▾</span>
              </button>

              {filtrosAbertos && (
                <div className="lp-filtros-menu" id="lp-menu-filtros">
                  <label>
                    <input
                      type="checkbox"
                      checked={somenteAbertas}
                      onChange={(e) => setSomenteAbertas(e.target.checked)}
                    />
                    <span>Somente lojas abertas</span>
                  </label>
                </div>
              )}
            </div>
          </div>

        </section>

        <section className="container secao lp-secao-lojas">
          <h2 className="titulo-secao">Lojas perto de você 🍬</h2>

          {carregando ? (
            <p className="mensagem-carregando">Carregando lojas...</p>
          ) : erro ? (
            <p className="mensagem-erro">{erro}</p>
          ) : lojas.length === 0 ? (
            <p className="mensagem-vazia">
              Ainda não temos lojas disponíveis por aqui.
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
                  role="link"
                  tabIndex={0}
                  aria-label={`Ver produtos de ${loja.nome}`}
                  onClick={() => abrirLoja(loja.id)}
                  onKeyDown={(evento) => {
                    if (evento.key === "Enter" || evento.key === " ") {
                      evento.preventDefault();
                      abrirLoja(loja.id);
                    }
                  }}
                >
                  <div className="lp-card-capa">
                    <span className="lp-card-emoji" aria-hidden="true">{loja.emoji}</span>
                  </div>
                  <div className="lp-card-corpo">
                    <h3>{loja.nome}</h3>
                    <p className="lp-card-descricao">
                      {loja.descricao || "Doceria parceira Candyland"}
                    </p>
                    <div className="lp-card-rodape">
                      <span className="lp-card-meta">
                        <span className={loja.entrega.gratis ? "lp-gratis" : "lp-taxa"}>
                          {loja.entrega.texto}
                        </span>
                        {loja.distancia_km !== null && localizacaoCliente && (
                          <span className="lp-card-distancia">📍 {formatarDistancia(loja.distancia_km)}</span>
                        )}
                      </span>
                      {["FECHADO", "EM_ANALISE"].includes(String(loja.status || "").toUpperCase()) && ( <strong className="lp-status-fechado">{String(loja.status).toUpperCase() === "EM_ANALISE" ? "Em anÃ¡lise" : "Fechada"}</strong> )}
                    </div>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>

        <section className="container secao lp-secao-banners">
          <div className="lp-banners">
            <article className="lp-banner lp-banner-rosa">
              <span className="lp-banner-emoji" aria-hidden="true">🍰</span>
              <h3>Sua doceria no Candyland</h3>
              <p>
                Cadastre sua confeitaria ou doceria e alcance milhares de amantes de doce.
              </p>
              <button
                type="button"
                onClick={() => navigate("/parceiros")}
                className="btn-branco"
              >
                Saiba mais <span aria-hidden="true">→</span>
              </button>
            </article>

            <article className="lp-banner lp-banner-escuro">
              <span className="lp-banner-emoji" aria-hidden="true">🛵</span>
              <h3>Quer fazer entregas?</h3>
              <p>
                Seja um entregador Candyland e ganhe mais entregando felicidade em forma de doce.
              </p>
              <button
                type="button"
                className="lp-btn-rosa"
                onClick={() => navigate("/parceiros")}
              >
                Seja Parceiro →
              </button>
            </article>
          </div>
        </section>
      </main>

      <footer className="lp-rodape">
        <div className="container">
          <div className="lp-rodape-topo">
            <div className="lp-rodape-marca">
              <span className="lp-rodape-logo" aria-hidden="true">🍭</span>
              <div>
                <strong>Candyland</strong>
                <span>Doces de todos os mundos</span>
              </div>
            </div>
            <nav className="lp-rodape-links" aria-label="Links institucionais">
              <button type="button" onClick={() => navigate("/parceiros")}>Para Parceiros</button>
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
