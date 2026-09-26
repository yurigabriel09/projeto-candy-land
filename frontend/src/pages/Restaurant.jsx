import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import Header from "../components/Header";
import { getRestaurant, getRestaurantProducts } from "../services/restaurantService";

const moeda = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });

function Restaurant() {
    const { restauranteId } = useParams();
    const [restaurante, setRestaurante] = useState(null);
    const [produtos, setProdutos] = useState([]);
    const [carregando, setCarregando] = useState(true);
    const [erro, setErro] = useState("");
    const [tentativa, setTentativa] = useState(0);

    useEffect(() => {
        let ativo = true;
        setCarregando(true);
        setErro("");
        setRestaurante(null);
        setProdutos([]);

        Promise.all([getRestaurant(restauranteId), getRestaurantProducts(restauranteId)])
            .then(([loja, itens]) => {
                if (ativo) {
                    setRestaurante(loja);
                    setProdutos(itens);
                }
            })
            .catch((error) => {
                if (ativo) setErro(error.message || "Não foi possível carregar o restaurante.");
            })
            .finally(() => {
                if (ativo) setCarregando(false);
            });

        return () => { ativo = false; };
    }, [restauranteId, tentativa]);

    return (
        <>
            <Header />
            <main>
                <section className="container secao">
                    <Link to="/home" className="btn-contorno">← Voltar aos restaurantes</Link>
                </section>

                {carregando ? (
                    <p className="mensagem-carregando" role="status">Carregando restaurante e produtos...</p>
                ) : erro ? (
                    <section className="container secao">
                        <p className="mensagem-erro" role="alert">{erro}</p>
                        <button className="btn-principal" onClick={() => setTentativa((valor) => valor + 1)}>
                            Tentar novamente
                        </button>
                    </section>
                ) : restaurante && (
                    <>
                        <section className="topo-consulta">
                            <div className="container">
                                <h1>{restaurante.nome}</h1>
                                {restaurante.descricao && <p>{restaurante.descricao}</p>}
                                {restaurante.horario_funcionamento && <p>Horário: {restaurante.horario_funcionamento}</p>}
                            </div>
                        </section>
                        <section className="container secao">
                            <h2 className="titulo-secao">Produtos do restaurante</h2>
                            {produtos.length === 0 ? (
                                <p className="mensagem-vazia">Este restaurante ainda não tem produtos cadastrados.</p>
                            ) : (
                                <div className="grade-produtos">
                                    {produtos.map((produto) => (
                                        <article className="card-produto" key={produto.id_produto}>
                                            <div className="card-produto-capa">
                                                {produto.imagem_url ? (
                                                    <img src={produto.imagem_url} alt={produto.nome_produto} />
                                                ) : <span aria-hidden="true">🍰</span>}
                                                {!produto.produto_disponivel && <span className="selo-indisponivel">Indisponível</span>}
                                            </div>
                                            <div className="card-produto-corpo">
                                                <h3>{produto.nome_produto}</h3>
                                                {produto.descricao_produto && <p className="card-produto-descricao">{produto.descricao_produto}</p>}
                                                <div className="card-produto-rodape">
                                                    <strong>{moeda.format(produto.preco_produto ?? 0)}</strong>
                                                </div>
                                            </div>
                                        </article>
                                    ))}
                                </div>
                            )}
                        </section>
                    </>
                )}
            </main>
        </>
    );
}

export default Restaurant;
