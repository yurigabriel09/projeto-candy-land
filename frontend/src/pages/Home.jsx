import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Header from "../components/Header";
import { useAuth } from "../context/AuthContext";
import { getRestaurants } from "../services/restaurantService";

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

function Home() {
    const { dadosAutenticacao, autenticado } = useAuth();
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

    const primeiroNome =
        dadosAutenticacao.nome_completo?.trim().split(/\s+/)[0] || "cliente";

    return (
        <div className="pagina-home">
            <Header />

            <section className="topo-saudacao">
                <div className="container">
                    <h1>Oi, {primeiroNome}! O que você quer comer hoje? 🍰</h1>
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
                                role="link"
                                tabIndex={0}
                                aria-label={`Ver produtos de ${loja.nome}`}
                                onClick={() => navigate(`/restaurantes/${loja.id}`)}
                                onKeyDown={(event) => {
                                    if (event.key === "Enter") navigate(`/restaurantes/${loja.id}`);
                                }}
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
        </div>
    );
}

export default Home;