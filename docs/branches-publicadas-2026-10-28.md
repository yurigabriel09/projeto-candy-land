# CandyLand — inventário das branches publicadas (28/10/2026)

Comparações abaixo usam `dev` como base. “Atrás” significa commits de `dev` que não estão no head antigo; `ahead=0` significa que a branch não contém commits únicos em relação a `dev`. Isso é uma leitura do grafo Git; antes de apagar, confirmar que não existe trabalho local não publicado e que a equipe não depende da branch.

| Branch | Ahead | Behind | Leitura / ação sugerida |
|---|---:|---:|---|
| `dev` | — | — | Branch de integração; HEAD `0f41cfb2` (26/10). |
| `feat/Autenticacao` | 0 | 22 | Antiga, sem commits únicos; candidato a limpeza após confirmação. |
| `feat/Autenticacao-v2` | 0 | 22 | Mesmo head da branch anterior; duplicata antiga, confirmar e limpar. |
| `feature/api-security-hardening` | 0 | 17 | PR #25 integrado; candidato a limpeza. |
| `feature/auth-email-celular` | 0 | 22 | Sem commits únicos em `dev`; confirmar e limpar. |
| `feature/auth-oauth` | 0 | 22 | PR #9 foi integrado em `main`; head ancestral, candidato a limpeza. |
| `feature/cardapio-restaurante` | 0 | 22 | PR #12 integrado; candidato a limpeza. |
| `feature/checkout-mvp` | 0 | 15 | PR #26 integrado; candidato a limpeza. |
| `feature/crud-produtos` | 0 | 22 | Branch antiga usada em PRs #6/#7; sem commits únicos em `dev`. |
| `feature/dados-pessoais` | 0 | 29 | PR #19 integrado em `main`; candidata a limpeza após confirmar dependências do grupo. |
| `feature/docker-config` | 0 | 27 | PR #20 integrado; candidato a limpeza. |
| `feature/google-maps-endereco` | 0 | 22 | Sem commits únicos em `dev`; confirmar se houve trabalho local antes de excluir. |
| `feature/home-restaurante` | 0 | 22 | PR #11 integrado em `main`; candidato a limpeza. |
| `feature/integracao-crud-produtos` | 0 | 22 | Sem commits únicos; confirmar e limpar. |
| `feature/mock-payment-flow` | 0 | 3 | PR #32 integrado; candidato a limpeza após confirmação. |
| `feature/oauth-validation` | 0 | 11 | PR #28 integrado; candidato a limpeza. |
| `feature/payment-provider-abstraction` | 0 | 5 | PR #31 integrado; candidato a limpeza. |
| `feature/payment-stock-integrity` | 0 | 7 | PR #30 integrado; candidato a limpeza. |
| `feature/paypal-mercadopago-pix` | **2** | **0** | **Manter.** Única branch com trabalho recente exclusivo; contém adapter PayPal, dispatch de provedores, histórico de compra/código de recebimento, testes e documentação. Abrir PR para `dev` depois das correções e validações. |
| `feature/persistencia-status-entrega` | 0 | 39 | PR #16 integrado; candidato a limpeza. |
| `feature/restaurant-configuration` | **1** | **20** | Divergida; o único delta observado contra `dev` é `backend/.env.example`, commit “Correção do .env” de 24/10 baseado em `main`. Não mesclar a branch inteira; comparar esse arquivo com o exemplo mais novo antes de excluir. |
| `feature/taxa-entrega-distancia` | 0 | 34 | PR #17 integrado; candidato a limpeza. |
| `feature/telas-mvp` | 0 | 22 | PR #8 integrado em `main`; candidato a limpeza. |
| `feature/tipo-entrega-pedido` | 0 | 42 | PR #13 integrado em `main`; candidato a limpeza. |
| `fix/TelaInicial` | 0 | 22 | Sem commits únicos em `dev`; candidato a limpeza após confirmação. |
| `fix/auth-account-resolution` | 0 | 19 | PR #23 integrado; candidato a limpeza. |
| `fix/estrutura-mvc` | 0 | 22 | PR #4 integrado; candidato a limpeza. |
| `fix/fluxo-cadastro-parceiros` | 0 | 9 | PR #29 integrado; candidato a limpeza. |
| `fix/teste-integracao-mvp` | 0 | 13 | PR #27 integrado; candidato a limpeza. |
| `main` | 0 | 20 | Entrega de sprint, HEAD de 21/10; está atrás de `dev`. Não atualizar `main` por cópia manual; promover `dev` → `main` apenas no fechamento aprovado da sprint. |
| `revert-8-feature/telas-mvp` | 0 | 22 | Sem commits únicos em `dev`; confirmar a história do revert e depois limpar se não for necessária. |

## Pull requests

Não havia PR aberto no momento da consulta. PRs #25–#32 foram fechados/mesclados em `dev`; #21 foi o último merge `dev` → `main` (20/10). PR #24 (também de `dev` para `main`) foi fechado sem merge. A nova branch `feature/paypal-mercadopago-pix` tem dois commits de 28/10 e não tinha PR aberto, então precisa de PR próprio.

## Política segura de limpeza

Não exclua branches automaticamente com base só no nome ou no número “behind”. Primeiro confirme working tree limpa, inexistência de commits locais/refs não publicados, conteúdo do PR integrado e concordância da equipe. Preserve `dev`, `main` e `feature/paypal-mercadopago-pix`. Reavalie a branch divergida `feature/restaurant-configuration` antes de remover.
