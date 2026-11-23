export const moeda = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });

export function Card({ rotulo, valor, destaque }) {
    return (
        <div className={`rl-card${destaque ? " rl-card-destaque" : ""}`}>
            <span className="rl-card-rotulo">{rotulo}</span>
            <strong className="rl-card-valor">{valor}</strong>
        </div>
    );
}

export function Barras({ serie, campo, formatar }) {
    const maximo = Math.max(1, ...serie.map((d) => Number(d[campo] || 0)));
    return (
        <div className="rl-barras">
            {serie.map((dia) => {
                const valor = Number(dia[campo] || 0);
                return (
                    <div className="rl-barra-col" key={dia.data}>
                        <span className="rl-barra-valor">{valor > 0 ? formatar(valor) : ""}</span>
                        <div className="rl-barra-trilho">
                            <div className="rl-barra" style={{ height: `${(valor / maximo) * 100}%` }} />
                        </div>
                        <span className="rl-barra-dia">{dia.dia_semana}</span>
                    </div>
                );
            })}
        </div>
    );
}

export function Ranking({ itens, nome, detalhe }) {
    if (!itens || itens.length === 0) {
        return <p className="rl-vazio">Ainda não há vendas concluídas neste mês.</p>;
    }
    return (
        <ol className="rl-ranking">
            {itens.map((item) => (
                <li key={item.posicao}>
                    <span className="rl-posicao">{item.posicao}º</span>
                    <span className="rl-ranking-nome">{nome(item)}</span>
                    <span className="rl-ranking-detalhe">{detalhe(item)}</span>
                </li>
            ))}
        </ol>
    );
}

export function Bloco({ titulo, children }) {
    return (
        <section className="rl-bloco">
            <h3>{titulo}</h3>
            {children}
        </section>
    );
}

export function VisaoLoja({ dados }) {
    const { cards, vendas_semana, top_produtos, alertas_estoque } = dados;
    return (
        <>
            <div className="rl-cards">
                <Card destaque rotulo="Vendas do mês" valor={moeda.format(cards.vendas_mes)} />
                <Card rotulo="Média por dia" valor={moeda.format(cards.media_por_dia)} />
                <Card rotulo="Pedidos" valor={cards.pedidos} />
            </div>
            <div className="rl-grade">
                <Bloco titulo="Vendas dos últimos 7 dias">
                    <Barras serie={vendas_semana} campo="total" formatar={(v) => moeda.format(v)} />
                </Bloco>
                <Bloco titulo="Mais vendidos do mês">
                    <Ranking
                        itens={top_produtos}
                        nome={(i) => i.nome_produto}
                        detalhe={(i) => `${i.unidades} un. · ${moeda.format(i.receita)}`}
                    />
                </Bloco>
            </div>
            <Bloco titulo={`Alertas de estoque (${alertas_estoque.total})`}>
                {alertas_estoque.itens.length === 0 ? (
                    <p className="rl-vazio">Nenhum produto com estoque baixo. 🎉</p>
                ) : (
                    <ul className="rl-alertas">
                        {alertas_estoque.itens.map((item) => (
                            <li key={item.id_produto}>
                                <span>{item.nome_produto}</span>
                                <span className={`rl-selo ${item.status === "ESGOTADO" ? "rl-selo-erro" : "rl-selo-aviso"}`}>
                                    {item.status === "ESGOTADO" ? "Esgotado" : `Restam ${item.qtd_estoque}`}
                                </span>
                            </li>
                        ))}
                    </ul>
                )}
            </Bloco>
        </>
    );
}

export function VisaoAdmin({ dados }) {
    const { cards, top_lojas, top_produtos, evolucao_plataforma, resumo_estrategico } = dados;
    const taxa = cards.taxa_sucesso_pct;
    return (
        <>
            <div className="rl-cards rl-cards-5">
                <Card destaque rotulo="Faturamento mensal" valor={moeda.format(cards.faturamento_mensal)} />
                <Card rotulo="Faturamento anual" valor={moeda.format(cards.faturamento_anual)} />
                <Card rotulo="Média por dia" valor={moeda.format(cards.media_por_dia)} />
                <Card rotulo="Pedidos concluídos" valor={cards.pedidos_concluidos} />
                <Card
                    rotulo="Taxa de sucesso"
                    valor={taxa === null ? "—" : `${taxa.toLocaleString("pt-BR")}%`}
                />
            </div>
            <div className="rl-grade">
                <Bloco titulo="Pedidos da plataforma (7 dias)">
                    <Barras serie={evolucao_plataforma} campo="pedidos" formatar={(v) => String(v)} />
                </Bloco>
                <Bloco titulo="Resumo estratégico">
                    <ul className="rl-resumo">
                        <li><span>Lojas ativas</span><strong>{resumo_estrategico.lojas_ativas}</strong></li>
                        <li>
                            <span>Avaliação média</span>
                            <strong>
                                {resumo_estrategico.avaliacao_media === null
                                    ? "—"
                                    : resumo_estrategico.avaliacao_media.toLocaleString("pt-BR")}
                            </strong>
                        </li>
                    </ul>
                </Bloco>
            </div>
            <div className="rl-grade">
                <Bloco titulo="Top lojas do mês">
                    <Ranking
                        itens={top_lojas}
                        nome={(i) => i.nome}
                        detalhe={(i) => `${i.pedidos} pedidos · ${moeda.format(i.receita)}`}
                    />
                </Bloco>
                <Bloco titulo="Top produtos do mês">
                    <Ranking
                        itens={top_produtos}
                        nome={(i) => i.nome_produto}
                        detalhe={(i) => `${i.unidades} un. · ${moeda.format(i.receita)}`}
                    />
                </Bloco>
            </div>
        </>
    );
}

export function VisaoCliente({ dados }) {
    const { cards, periodo_dias } = dados;
    return (
        <div className="rl-cards rl-cards-4">
            <Card destaque rotulo={`Gasto total (${periodo_dias} dias)`} valor={moeda.format(cards.gasto_total)} />
            <Card rotulo="Pedidos finalizados" valor={cards.pedidos} />
            <Card rotulo="Ticket médio" valor={moeda.format(cards.ticket_medio)} />
            <Card rotulo="Economia com cupons" valor={moeda.format(cards.economia_cupons)} />
        </div>
    );
}
