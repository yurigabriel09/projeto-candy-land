# CandyLand — Backlog de Funcionalidades Atualizado

**Data da revisão:** 25/10/2026  
**Base:** repositório GitHub `yurigabriel09/projeto-candy-land`, branch `dev`, e validações locais informadas pelo responsável.

## Evidências de validação mais recentes

- **115 testes de backend passaram** (`python.exe -m pytest -q`), com 3 avisos de depreciação do SQLAlchemy relacionados a `Query.get()`; não houve falhas.
- **24 testes focados em pagamento/provedores/integridade de estoque passaram**.
- **Build do frontend passou** com Vite 8.2.2.
- O usuário confirmou login local real via **Google e Facebook**, tanto em conta de cliente quanto em conta de restaurante.
- O checkout MVP registra pedidos como `PENDENTE_PAGAMENTO`; **isso não representa cobrança real**.
- Os PRs de segurança, checkout, smoke test, OAuth, integridade de estoque, contrato de provedores e pagamento mock estão integrados em `dev`. O trabalho recente ainda precisa ser promovido para `main` no momento planejado pela equipe.

> **Como interpretar os percentuais:** são estimativas de entrega funcional, não cobertura de testes. “Código existe”, “testes automatizados passaram”, “validado manualmente” e “pronto para produção” são estados diferentes. Os percentuais não substituem os critérios de aceite.

| **#** | **Funcionalidade** | **Prioridade** | **Detalhe** | **%** | **OBS** |
|---:|---|:---:|---|:---:|---|
| 1 | Funcionalidades iFood | 1 | Explicação detalhada de todas as funcionalidades | 100% | Documento-base existente; revisar continuamente para refletir mudanças aprovadas na esteira de pedidos. |
| 2 | Funcionalidades iFood | 1 | Diagrama de Arquitetura | 50% | Não identifiquei no repositório consultado um diagrama de arquitetura separado do modelo de dados. Localizar/confirmar a versão oficial e atualizar se necessário. |
| 3 | Funcionalidades iFood | 1 | Diagrama do Modelo de Dados Físico | 95% | docs/modelo-dados.md, .dot e .png existem. Modelo atual documentado; redesign/migrações futuras ainda pendentes. |
| 4 | Funcionalidades iFood | 1 | Documento do Projeto | 80% | README, requisitos, regras de pedidos e plano priorizado existem; alinhar documentação com checkout, pagamento mock, estado atual e decisões futuras. |
| 5 | Autenticação | 2 | Cadastro de Usuários | 100% | Fluxo existente; manter testes de regressão após alterações no login. |
| 6 | Autenticação | 2 | Login por Celular | 95% | Implementação existente. Confirmar fluxo real de envio/validação no ambiente publicado, além dos testes automatizados. |
| 7 | Autenticação | 2 | Login por Email | 95% | Serviços/rotas existentes; validar entrega real de mensagens e expiração/limite de tentativas. |
| 8 | Autenticação | 2 | Código de Validação no login/cadastro | 85% | Modelos e rotas existem. Falta completar/confirmar cobertura para código expirado, reutilizado, incorreto e limite de tentativas. |
| 9 | Autenticação | 2 | Login/integração Google OAuth | 95% | Usuário confirmou login local real como cliente e restaurante. Manter pendente a validação específica do ambiente publicado/produção. |
| 10 | Autenticação | 2 | Login/integração Facebook OAuth | 95% | Usuário confirmou login local real como cliente e restaurante. Validar também callback, permissões e URLs no ambiente publicado. |
| 11 | Autenticação | 2 | Cadastro de Locais + Maps | 35% | Modelo de endereço, coordenadas e consulta de CEP existem; autocomplete/geocodificação/mapa Google completo não ficou comprovado. Não declarar o Maps completo sem teste específico. |
| 12 | Restaurante | 2 | Cadastro (CRUD) Restaurante | 95% | CRUD e endpoints existem. Revisar autorização, validação dos dados e teste de ponta a ponta no ambiente local. |
| 13 | Restaurante | 2 | Configuração dos dados do Restaurante | 75% | A tela existe em dev em /business/configuracao e contém taxa base, taxa/km e raio. Usuário relata que não consegue usar/configurar; próxima tarefa é reproduzir o acesso e testar salvar/recarregar. |
| 14 | Catálogo | 2 | Cadastro (CRUD) Produto | 95% | CRUD existente. Manter testes de autorização BUSINESS, disponibilidade, estoque e persistência de imagem/URL. |
| 15 | Escolha Itens Cesta | 3 | Lista de Restaurantes | 95% | Listagem existe; filtros por proximidade/localização e comportamento em estados vazios/erro devem ser validados se fizerem parte do escopo. |
| 16 | Escolha Itens Cesta | 3 | Lista e Seleção de Produto | 90% | Tela e botão Adicionar com handler existem em dev. Confirmar manualmente seleção, disponibilidade e encaminhamento correto ao carrinho. |
| 17 | Cesta de Produtos | 4 | Inclusão de Produto na Cesta | 95% | CartContext e integração com a tela de produtos existem. Confirmar no navegador que todas as entradas do catálogo adicionam ao carrinho corretamente. |
| 18 | Cesta de Produtos | 4 | Exclusão de Produto na Cesta | 95% | Função de remoção existe; falta evidência de teste de interface e cenário completo no navegador. |
| 19 | Cesta de Produtos | 4 | Alteração de quantidade | 95% | Controles existem. API valida quantidades/estoque no checkout; registrar teste manual de limites e atualização do total. |
| 20 | Fechar Pedido | 5 | Escolha do Tipo de Pagamento | 90% | Checkout permite selecionar PIX ou CARTAO_CREDITO e registra a preferência no pedido. Ainda não realiza cobrança real. |
| 21 | Fechar Pedido | 5 | Integração Cartão - Pagamento | 20% | Base neutra de provedores e pagamento mock existem; nenhum gateway de cartão real integrado. Definir provedor e implementar sandbox/webhook. |
| 22 | Fechar Pedido | 5 | Seleção de Tipo de Entrega | 90% | DELIVERY/PICKUP implementados no backend e integrados ao checkout. Falta registrar teste manual de ponta a ponta; cálculo usa distância Haversine em linha reta. |
| 23 | Fechar Pedido | 5 | Notificação PUSH de solicitação | 0% | Não foi comprovado fluxo de notificação de novo pedido ligado ao evento de criação do pedido. |
| 24 | Fechar Pedido | 5 | Envio de NF em PDF por email | 0% | Implementação pendente; separar PDF de pedido/recibo de uma NF-e fiscal autorizada. |
| 25 | Pedidos | 5 | CRUD + validações + testes + integração com estoque + persistência do estado da entrega | 90% | 115 testes do backend passaram localmente e 24 testes focados em pagamento/estoque passaram. Falta validar fluxo completo no navegador e operação integrada. |
| 26 | Acompanhamento Entrega | 6 | PUSH a cada mudança de status | 0% | Ainda falta publicar evento por transição confirmada e garantir que retries não gerem notificação duplicada. |
| 27 | Acompanhamento Entrega | 6 | Alteração de status do pedido | 85% | Máquina de estados, persistência e autorização estão implementadas com testes. Falta integrar e validar o fluxo com o painel/ator operacional. |
| 28 | Acompanhamento Entrega | 6 | Tela de acompanhamento | 0% | Interface do cliente para consultar estado comercial e logístico ainda não comprovada. |
| 29 | Acompanhamento Entrega | 6 | Código de validação do entregador | 0% | Não implementado; depende das regras e do perfil operacional do entregador. |
| 30 | Restaurante | — | Painel restaurante | 55% | Home/área de parceiros, catálogo e configuração básica existem. Gestão completa de pedidos, notificações, relatórios e operação ainda precisa ser concluída/validada. |
| 31 | Infraestrutura | — | AWS (IA/Lambda/BD) | 0% | Não há implantação AWS/IA comprovada neste escopo. Definir arquitetura e prioridade antes de implementar. |
| 32 | Fiscal | — | NFe / SEFAZ | 0% | Integração fiscal não implementada; requer regras fiscais, certificado/provedor e homologação. |
| 33 | Relatórios | — | Esboço de 3 relatórios | 0% | Definir requisitos, métricas, filtros, permissões e layouts para vendas, estoque e pedidos. |
| 34 | Relatórios | — | Implementação de 3 relatórios | 0% | Depende da aprovação da especificação e da estabilidade dos dados de pedidos/estoque. |
| 35 | Notificações | — | SMS/WhatsApp/email automáticos | 15% | Serviços de e-mail/WhatsApp existem para autenticação; notificações operacionais de pedido/status ainda não estão integradas. |
| 36 | Integrações | — | Integração automática com redes sociais | 0% | Não implementado; definir o objetivo e o escopo antes de escolher APIs externas. |
| 37 | Mapas e Entrega | — | Cálculo de caminho mínimo Google Maps | 15% | Há cálculo Haversine para distância em linha reta; não equivale a rota por ruas/caminho mínimo via Google Maps Routes. |
| 38 | Pagamento | — | Pagamento cartões / Mercado Pago | 20% | Contrato/fábrica de provedores e mock estão no código; integração Mercado Pago real, sandbox e webhook ainda pendentes. |
| 39 | Mobile | — | App mobile | 0% | Frontend atual é web React; aplicativo mobile dedicado ainda não comprovado. |
| 40 | Estoque/Leitura | — | Leitor de código de barras | 0% | Não implementado. |
| 41 | Retirada | — | Painel/dispositivo de chamada para retirada | 0% | Não implementado; depende da operação de retirada e da gestão de pedidos. |
| 42 | Pagamento | — | Pagamento com Pix | 20% | O checkout registra PIX como preferência e o mock permite testes locais; geração real de cobrança, Copia e Cola, QR e webhook não estão integrados. |
| 43 | Leitura | — | Leitor de QR Code | 0% | Não implementado. |
| 44 | Estoque | — | Estoque de produto; baixa após pagamento e reposição em cancelamento | 95% | Baixa/restauração transacionais e idempotentes estão implementadas; os 6 testes focados passaram. Falta integração com gateway/webhook real e validação no banco de implantação. |
| 45 | Produto | — | Sugestão de Produtos | 0% | Definir regras de cross-sell/upsell antes de desenvolver API e componente visual. |
| 46 | Entrega | — | Taxa de entrega por distância | 85% | Cálculo backend e campos de taxa base/taxa por km/raio existem em dev. Investigar por que a configuração não está acessível/funcional no ambiente local; validar salvar, recarregar e cálculo no checkout. Distância atual é linha reta Haversine. |


## Próximas ações prioritárias

1. **P0 — Validar o MVP no navegador:** fazer login, abrir catálogo, adicionar produto, finalizar com `DELIVERY`, repetir com `PICKUP`, confirmar pedido pendente e testar acesso ao pedido. Registrar evidências sem expor tokens ou dados pessoais.
2. **P0 — Diagnosticar configuração de entrega:** na branch `dev`, a tela `frontend/src/pages/RestaurantConfiguration.jsx` está registrada na rota `/business/configuracao` e inclui os campos de taxa base, taxa por km e raio. Reproduzir o problema no ambiente local antes de implementar uma correção; validar acesso, carregamento dos dados, salvamento, recarga e efeito no checkout. Não criar uma segunda tela antes desse diagnóstico.
3. **P1 — Pagamento real:** decidir com o grupo qual provedor será usado; criar adaptador em sandbox, verificar webhook autêntico e idempotente, testar aprovação/recusa/retry e garantir baixa de estoque uma única vez. Não habilitar o mock em produção.
4. **P1 — Documentação:** sincronizar README, documentos de endpoints, regras de pedidos e backlog com as alterações integradas e registrar o teste manual do smoke test.
5. **P2 — Operação do restaurante:** detalhar e priorizar gestão de pedidos, notificações, histórico/acompanhamento de entrega e relatórios antes de iniciar os extras (mobile, fiscal, leitores e recomendação).

## Limitações ainda explícitas

- Os testes e o build foram executados no ambiente local informado pelo usuário; não comprovam, por si só, o comportamento do navegador em todos os cenários nem a implantação de produção.
- OAuth foi testado manualmente localmente pelo usuário; produção/homologação ainda exige conferência própria de URLs, callbacks, client IDs e segredos.
- O pagamento atual é de desenvolvimento/mock. Nenhum provedor real foi confirmado como conectado.
- O cálculo de distância usa Haversine em linha reta, não rota rodoviária do Google Maps.
- O campo de configuração de taxa está no código de `dev`, mas seu acesso e salvamento no ambiente do usuário precisam ser reproduzidos antes de considerar a tarefa encerrada.
