# CandyLand — o que manter, o que pode ser limpo (28/10/2026)

## Não apagar

| Item | Motivo |
|---|---|
| `backend/.env.example`, `frontend/.env.example` | Exemplos para inicialização segura e onboarding do grupo; manter sem segredos reais. |
| `backend/app/`, `frontend/src/`, `backend/tests/` | Código de aplicação e testes. |
| `scripts/gerar_zip_limpo.*` | Usado no fluxo de geração de ZIP limpo e referenciado no README. |
| `scripts/preparar_ambiente.*` | Automatiza setup do ambiente do projeto. |
| `scripts/gerenciar_pr.*` | Fluxo de PRs GitHub documentado pelo README. |
| `docs/modelo-dados.*`, `docs/regras-pedidos.md`, `docs/requisitos.md` | Artefatos de regra/arquitetura; manter sincronizados com código. |
| `docs/Credenciais/` | Contém instruções de configuração consultadas no texto, aparentemente com placeholders. Não inspecionei todas as imagens; revisar screenshots antes de compartilhá-las e rotacionar qualquer segredo que apareça nelas. O script de ZIP limpo já exclui essa pasta da distribuição. |
| `docs/Backlog_Funcionalidades_CandyLand_Atualizado_2026-10-25 (2).md` | Nome com `(2)` parece export/duplicata, mas não prova que é descartável; há referências ao conteúdo. Atualizar/renomear somente após checar uso pelo grupo. |

## Candidatos à limpeza, com confirmação

- **`limpar_e_gerar_zip.cmd` e `limpar_e_gerar_zip.ps1`:** são wrappers legados que encaminham para `scripts/gerar_zip_limpo.ps1`. Provavelmente redundantes, mas podem ter sido mantidos por compatibilidade. Faça `git grep -n "limpar_e_gerar_zip"` e pergunte ao grupo antes de removê-los.
- **Branches com `ahead=0`:** ver `candyland-branches-publicadas-2026-10-28.md`. São candidatas a exclusão remota/local após confirmar que não há mudanças locais ou trabalho que a equipe queira recuperar. Não delete `feature/paypal-mercadopago-pix`, `dev` ou `main`.
- **`feature/restaurant-configuration`:** possui um commit exclusivo antigo que muda `.env.example`; comparar com a versão mais recente antes de decidir excluir.
- **Artifacts temporários locais:** `.venv`, `venv`, `node_modules`, `dist`, `build`, `.pytest_cache`, `__pycache__`, logs e arquivos de cache não precisam ir para Git/ZIP de entrega. Não é necessário apagá-los do computador para limpar o repositório; o gerador de ZIP já os exclui.

## Nunca commitar / distribuir em ZIP de entrega

- `.env`, `.env.local`, tokens do Mercado Pago/PayPal, Facebook App Secret, chaves Google Maps, Brevo e Twilio.
- Banco local `.db`/`.sqlite`, credenciais privadas, certificados, tokens de webhook e executáveis de túnel locais.
- `node_modules`, virtualenv, cache e build gerado.

O script `scripts/gerar_zip_limpo.ps1` é projetado para fazer uma cópia temporária sem esses artefatos e não apagar os arquivos do repositório. Confira o ZIP antes de compartilhar.

## Estrutura que não existe ainda

Não encontrei módulo de Android/Kotlin, Gradle ou implementação completa de push/FCM. Não apague nem tente “limpar” uma pasta mobile inexistente; ela é trabalho futuro a ser criado separadamente.
