import { Link } from "react-router-dom";

function PartnerLanding() {
    return (
        <div className="partner-page">
            <header className="site-header">
                <div className="site-header-inner">
                    <Link to="/" className="site-logo" aria-label="CandyLand - início">
                        <span className="site-logo-icone">🍭</span>
                        <span className="site-logo-texto">Candyland</span>
                    </Link>
                    <nav className="site-nav" aria-label="Navegação de parceiros">
                        <Link to="/">Área do cliente</Link>
                        <Link to="/parceiros/login" className="btn-contorno">
                            Entrar
                        </Link>
                    </nav>
                </div>
            </header>

            <main>
                <section className="partner-hero">
                    <div className="container partner-hero-conteudo">
                        <span className="partner-selo">🍰 CandyLand para negócios</span>
                        <h1>
                            Sua doceria merece
                            <span> chegar mais longe.</span>
                        </h1>
                        <p>
                            Cadastre sua confeitaria ou doceria, apresente seus produtos
                            e conecte seus doces a novos clientes.
                        </p>
                        <div className="partner-hero-acoes">
                            <Link to="/parceiros/login" className="btn-principal">
                                Entrar ou cadastrar minha doceria
                            </Link>
                            <Link to="/" className="partner-link-secundario">
                                Conhecer a CandyLand como cliente
                            </Link>
                        </div>
                    </div>
                </section>

                <section className="container partner-beneficios">
                    <div className="partner-secao-intro">
                        <span className="partner-selo partner-selo-claro">Feito para quem cria doces</span>
                        <h2>Transforme suas receitas em novas oportunidades</h2>
                        <p>Um espaço para sua doceria começar a vender pelo CandyLand.</p>
                    </div>

                    <div className="partner-beneficios-grade">
                        <article className="partner-beneficio-card">
                            <span aria-hidden="true">🧁</span>
                            <h3>Mostre seu cardápio</h3>
                            <p>Organize seus produtos para que os clientes descubram o que você prepara.</p>
                        </article>
                        <article className="partner-beneficio-card">
                            <span aria-hidden="true">🛍️</span>
                            <h3>Receba pedidos</h3>
                            <p>Tenha sua loja presente em uma experiência pensada para amantes de doces.</p>
                        </article>
                        <article className="partner-beneficio-card">
                            <span aria-hidden="true">🍬</span>
                            <h3>Comece pelo cadastro</h3>
                            <p>Use e-mail, celular, Google ou Facebook para iniciar sua conta de parceiro.</p>
                        </article>
                    </div>
                </section>

                <section className="partner-cta-wrap">
                    <div className="container partner-cta">
                        <div>
                            <h2>Vamos colocar sua doceria no CandyLand?</h2>
                            <p>Entre na área de parceiros ou comece o cadastro da sua empresa.</p>
                        </div>
                        <Link to="/parceiros/login" className="btn-branco">
                            Seja um parceiro!
                        </Link>
                    </div>
                </section>
            </main>

            <footer className="rodape partner-rodape">
                <div className="container rodape-conteudo">
                    <span>🍭 Candyland — Doces de todos os mundos</span>
                    <Link to="/">Voltar para a área do cliente</Link>
                </div>
            </footer>
        </div>
    );
}

export default PartnerLanding;
