import { Link } from "react-router-dom";

function PartnerLanding() {
    return (
        <div className="partner-page">
            {/* Cabeçalho para Parceiros */}
            <header className="partner-header">
                <div className="container partner-header-inner">
                    <Link to="/" className="partner-logo">
                        <span className="site-logo-icone">🍭</span>
                        <div className="partner-logo-textos">
                            <span className="partner-logo-brand">Candyland</span>
                            <span className="partner-logo-tag">PARA PARCEIROS</span>
                        </div>
                    </Link>

                    <div className="partner-header-acoes">
                        <span className="partner-header-duvida">Já vende com a gente?</span>
                        <Link to="/parceiros/login" className="btn-parceiro-entrar">
                            Entrar
                        </Link>
                    </div>
                </div>
            </header>

            <main>
                {/* Hero Principal */}
                <section className="partner-hero-dark">
                    <div className="container partner-hero-grid">
                        <div className="partner-hero-left">
                            <span className="partner-badge-top">
                                FEITO PARA QUEM CRIA MOMENTOS DOCES
                            </span>

                            <h1 className="partner-hero-titulo">
                                Sua confeitaria merece um <em>universo inteiro</em>
                            </h1>

                            <p className="partner-hero-subtitulo">
                                Venda seus doces, organize pedidos e conquiste novos clientes sem perder tempo com ferramentas complicadas.
                            </p>

                            <div className="partner-hero-botoes">
                                <Link to="/parceiros/login" className="btn-cadastrar-loja">
                                    Cadastrar minha loja
                                </Link>
                                <a href="#porque-ser-parceiro" className="btn-ver-funciona">
                                    Ver como funciona
                                </a>
                            </div>

                            <div className="partner-hero-metricas">
                                <div className="partner-metrica">
                                    <strong>+2 mil</strong>
                                    <small>lojas parceiras</small>
                                </div>
                                <div className="partner-metrica">
                                    <strong>4,9</strong>
                                    <small>nota média</small>
                                </div>
                                <div className="partner-metrica">
                                    <strong>24h</strong>
                                    <small>para começar</small>
                                </div>
                            </div>
                        </div>

                        <div className="partner-hero-right">
                            <div className="partner-card-frame">
                                <div className="partner-card-inner">
                                    <div className="partner-hero-img-wrapper">
                                        <img 
                                            src="../../public/logo.jpg" 
                                            alt="Ilustração Candyland Parceiros" 
                                            className="partner-hero-img" 
                                        />
                                    </div>

                                    <div className="partner-float-badge">
                                        <div className="partner-float-info">
                                            <span className="partner-float-eyebrow">TUDO EM UM SÓ LUGAR</span>
                                            <strong className="partner-float-title">Pedidos, cardápio e financeiro</strong>
                                        </div>
                                        <div className="partner-float-icon">
                                            <span>C</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>

                {/* Seção: Por Que Ser Parceiro */}
                <section id="porque-ser-parceiro" className="partner-why-section">
                    <div className="container">
                        <span className="partner-section-eyebrow">POR QUE SER PARCEIRO</span>
                        <h2 className="partner-section-title">
                            Você cuida das receitas. A gente ajuda o negócio a crescer.
                        </h2>

                        <div className="partner-why-grid">
                            <article className="partner-why-card">
                                <span className="partner-why-number">01</span>
                                <h3>Sua vitrine no ar</h3>
                                <p>
                                    Cardápio organizado, fotos dos produtos e uma página só sua dentro do Candyland.
                                </p>
                            </article>

                            <article className="partner-why-card">
                                <span className="partner-why-number">02</span>
                                <h3>Pedidos sem confusão</h3>
                                <p>
                                    Receba, confirme e acompanhe cada pedido em um painel simples e intuitivo.
                                </p>
                            </article>

                            <article className="partner-why-card">
                                <span className="partner-why-number">03</span>
                                <h3>Mais gente te encontra</h3>
                                <p>
                                    Apareça para clientes próximos que já estão procurando bolos, doces e presentes.
                                </p>
                            </article>
                        </div>
                    </div>
                </section>

                {/* Seção: Três Passos */}
                <section className="partner-steps-section">
                    <div className="container partner-steps-grid">
                        <div className="partner-steps-info">
                            <span className="partner-section-eyebrow">SIMPLES DESDE O COMEÇO</span>
                            <h2>Abra as portas da sua loja em três passos</h2>
                            <p>
                                Sem mensalidade no primeiro mês e com suporte para colocar seu cardápio no ar.
                            </p>
                        </div>

                        <div className="partner-steps-list">
                            <div className="partner-step-item">
                                <span className="partner-step-badge">01</span>
                                <strong>Conte um pouco sobre sua loja</strong>
                            </div>

                            <div className="partner-step-item">
                                <span className="partner-step-badge">02</span>
                                <strong>Monte seu cardápio</strong>
                            </div>

                            <div className="partner-step-item">
                                <span className="partner-step-badge">03</span>
                                <strong>Comece a receber pedidos</strong>
                            </div>
                        </div>
                    </div>
                </section>

                {/* Banner CTA Final */}
                <section className="partner-cta-final-wrap">
                    <div className="container">
                        <div className="partner-cta-final-card">
                            <span className="partner-cta-eyebrow">SEU PRÓXIMO PEDIDO PODE COMEÇAR AQUI</span>
                            <h2>Leve sua confeitaria para todos os mundos</h2>
                            <Link to="/parceiros/login" className="btn-cta-branco">
                                Quero ser parceiro
                            </Link>
                        </div>
                    </div>
                </section>
            </main>

            {/* Rodapé */}
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