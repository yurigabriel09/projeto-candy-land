import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import Header from "../components/Header";
import { getProducts } from "../services/productService";
import { getRestaurants } from "../services/restaurantService";

const EMOJIS_PRODUTO = ["🍰", "🍫", "🍭", "🧁", "🍮", "🍪", "🍩", "🍬"];

function formatarPreco(valor) {
  return valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function Itens() {
  const [parametros, setParametros] = useSearchParams();
  const lojaAtiva = parametros.get("loja");
  const buscaInicial = parametros.get("busca") || "";

  const [produtos, setProdutos] = useState([]);
  const [lojas, setLojas] = useState([]);
  const [busca, setBusca] = useState(buscaInicial);
  const [ordem, setOrdem] = useState("relevancia");
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState("");

  useEffect(() => {
    carregarDados();
  }, []);

  async function carregarDados() {
    setCarregando(true);
    setErro("");
    try {
      const [produtosApi, lojasApi] = await Promise.all([
        getProducts(),
        getRestaurants(),
      ]);
      setProdutos(produtosApi);
      setLojas(lojasApi);
    } catch {
      setErro("Não foi possível carregar os produtos agora.");
    } finally {
      setCarregando(false);
    }
  }

  function nomeDaLoja(idRestaurante) {
    const loja = lojas.find((l) => l.id === idRestaurante);
    return loja ? loja.nome : "Loja Candyland";
  }

  function trocarLoja(id) {
    if (lojaAtiva === String(id)) {
      parametros.delete("loja");
    } else {
      parametros.set("loja", id);
    }
    setParametros(parametros);
  }

  const termo = busca.trim().toLowerCase();

  let resultado = produtos.filter((produto) => {
    const daLoja = !lojaAtiva || produto.id_restaurante === Number(lojaAtiva);
    const combinaBusca =
      !termo ||
      produto.nome_produto.toLowerCase().includes(termo) ||
      (produto.descricao_produto || "").toLowerCase().includes(termo);
    return daLoja && combinaBusca;
  });

  if (ordem === "menor-preco") {
    resultado = [...resultado].sort((a, b) => a.preco_produto - b.preco_produto);
  } else if (ordem === "maior-preco") {
    resultado = [...resultado].sort((a, b) => b.preco_produto - a.preco_produto);
  }

  function limparFiltros() {
    setBusca("");
    setOrdem("relevancia");
    parametros.delete("loja");
    parametros.delete("busca");
    setParametros(parametros);
  }

  const lojasComProdutos = lojas.filter((loja) =>
    produtos.some((p) => p.id_restaurante === loja.id)
  );

  return (
    <>
      <Header />

      <section className="topo-consulta">
        <div className="container">
          <h1>Todos os doces 🍬</h1>
          <p>Busque pelo nome do doce ou filtre por loja</p>

          <div className="busca-endereco busca-itens">
            <span>🔍</span>
            <input
              type="search"
              placeholder="Buscar doces"
              value={busca}
              onChange={(e) => setBusca(e.target.value)}
              aria-label="Buscar doces"
            />
          </div>
        </div>
      </section>

      {lojasComProdutos.length > 0 && (
        <section className="container secao">
          <div className="atalhos">
            {lojasComProdutos.map((loja) => {
              const ativa = lojaAtiva === String(loja.id);
              return (
                <button
                  key={loja.id}
                  className={`chip-loja ${ativa ? "chip-loja-ativa" : ""}`}
                  onClick={() => trocarLoja(loja.id)}
                >
                  {loja.nome}
                </button>
              );
            })}
          </div>
        </section>
      )}

      <section className="container">
        <div className="barra-resultado">
          <span>
            {carregando
              ? "Carregando..."
              : `${resultado.length} ${
                  resultado.length === 1 ? "doce encontrado" : "doces encontrados"
                }`}
          </span>

          <label className="ordenar">
            Ordenar por
            <select value={ordem} onChange={(e) => setOrdem(e.target.value)}>
              <option value="relevancia">Relevância</option>
              <option value="menor-preco">Menor preço</option>
              <option value="maior-preco">Maior preço</option>
            </select>
          </label>
        </div>
      </section>

      <section className="container secao">
        {erro ? (
          <p className="mensagem-erro">{erro}</p>
        ) : !carregando && resultado.length === 0 ? (
          <div className="estado-vazio">
            <span className="estado-vazio-emoji">🔎</span>
            <p>Nenhum doce encontrado com esses filtros</p>
            <button onClick={limparFiltros} className="btn-principal">
              Limpar filtros
            </button>
          </div>
        ) : (
          <div className="grade-produtos">
            {resultado.map((produto, i) => (
              <article key={produto.id_produto} className="card-produto">
                <div className="card-produto-capa">
                  {produto.imagem_url ? (
                    <img src={produto.imagem_url} alt={produto.nome_produto} />
                  ) : (
                    EMOJIS_PRODUTO[i % EMOJIS_PRODUTO.length]
                  )}
                  {!produto.produto_disponivel && (
                    <span className="selo-indisponivel">Indisponível</span>
                  )}
                </div>
                <div className="card-produto-corpo">
                  <h3>{produto.nome_produto}</h3>
                  {produto.descricao_produto && (
                    <p className="card-produto-descricao">
                      {produto.descricao_produto}
                    </p>
                  )}
                  <p className="card-produto-loja">
                    {nomeDaLoja(produto.id_restaurante)}
                  </p>
                  <div className="card-produto-rodape">
                    <strong>{formatarPreco(produto.preco_produto)}</strong>
                    <button
                      className="btn-principal btn-pequeno"
                      disabled={!produto.produto_disponivel}
                    >
                      Adicionar
                    </button>
                  </div>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </>
  );
}

export default Itens;