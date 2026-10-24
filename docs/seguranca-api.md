# Segurança da API — primeira etapa

## Regras implementadas

- Tokens Bearer precisam ser JWTs válidos com `exp`, `sub` e `tipo_conta`; o ID deve ser positivo e o tipo deve ser `PERSONAL` ou `BUSINESS`.
- Dados pessoais em `/users/<id>` só podem ser lidos/alterados/excluídos pelo próprio usuário autenticado. A listagem global de usuários retorna `403` enquanto não existir um papel administrativo formal.
- Criação pública de clientes/restaurantes continua dependente da verificação de identidade por `tentativa_id` no serviço de cadastro.
- Atualizações e exclusões genéricas de restaurantes exigem token `BUSINESS` cujo ID corresponda ao recurso. Configuração do restaurante continua protegida por propriedade.
- Categorias são dados de gerenciamento e exigem uma conta `BUSINESS`.
- Listas públicas do catálogo de restaurantes e produtos omitem CPF do responsável, e-mail/telefone privados e a quantidade exata em estoque.
- Detalhes internos de produto e estoque são lidos por endpoints de gerenciamento autenticados e restritos ao restaurante proprietário.
- Alterações de e-mail/telefone não são aceitas pelo CRUD simples; devem ser implementadas em fluxos com verificação de identidade.

## Limitações ainda abertas

- A aplicação ainda não possui papel `ADMIN`; por isso, endpoints globais de administração devem permanecer indisponíveis até existir autorização administrativa explícita.
- O gateway/pagamento e os webhooks ainda precisam de autenticação e validação própria de assinatura/idempotência antes de serem habilitados.
- A configuração de segredo de produção e a política de CORS merecem validação de deploy independente antes da publicação externa.
- Esta entrega adiciona testes de autorização de rota; ela não substitui um teste de segurança ponta a ponta em ambiente publicado.
