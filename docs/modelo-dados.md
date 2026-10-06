# Modelo de dados — CandyLand

Este documento é a visão textual/visual de referência do **modelo físico atual**. Ele deve ser atualizado sempre que uma alteração de regra de negócio exigir mudança de tabela, coluna, chave estrangeira ou relacionamento.

> **Importante:** o modelo ainda contém estruturas legadas que serão revistas em uma futura etapa de redesign físico. O diagrama abaixo representa o estado atual, não o modelo futuro ideal.

## Diagrama ER

```mermaid
erDiagram
    USERS ||--o{ ADDRESSES : possui
    RESTAURANTS ||--o| ADDRESSES : usa
    RESTAURANTS ||--o{ CATEGORIES : possui
    CATEGORIES ||--o{ PRODUCTS : organiza
    RESTAURANTS ||--o{ PRODUCTS : vende
    USERS ||--o{ ORDERS : cria
    RESTAURANTS ||--o{ ORDERS : recebe
    ADDRESSES ||--o{ ORDERS : entrega
    ORDERS ||--o{ ORDER_ITEMS : contem
    PRODUCTS ||--o{ ORDER_ITEMS : compoe

    USERS {
        int id PK
        int id_restaurante FK
        string nome_completo
        string email UK
        string telefone
        string cpf UK
        string status
    }

    ADDRESSES {
        int id PK
        int id_usuario FK
        int id_restaurante FK
        string cep
        string rua
        string numero
        string bairro
        string cidade
        string estado
        decimal latitude
        decimal longitude
        string tipo_endereco
        boolean principal
        boolean ativo
    }

    RESTAURANTS {
        int id PK
        int address_id FK UK
        string cnpj UK
        string razao_social
        string nome
        string email UK
        string telefone
        decimal valor_minimo_pedido
        decimal taxa_entrega_base
        decimal raio_entrega_km
        string status
        boolean ativo
    }

    CATEGORIES {
        int id PK
        int id_restaurante FK
        int id_categoria_pai FK
        string nome
        boolean ativa
    }

    PRODUCTS {
        int id PK
        int restaurant_id FK
        int category_id FK
        string name
        decimal price
        boolean is_available
        int current_stock
    }

    ORDERS {
        int id PK
        string order_code UK
        int user_id FK
        int restaurant_id FK
        int delivery_address_id FK
        decimal subtotal
        decimal discount
        decimal delivery_fee
        decimal platform_fee
        decimal total
        string order_type
        string status
        string payment_method
        datetime created_at
    }

    ORDER_ITEMS {
        int id PK
        int id_pedido FK
        int id_produto FK
        int quantidade
        decimal preco_unitario
        string observacoes
    }
```

## Alterações planejadas para o fluxo de pedidos

A nova regra de negócio introduz a necessidade de separar:

- estado comercial/operacional do pedido;
- estado logístico da entrega;
- histórico/auditoria das transições.

Antes da implementação final dessas estruturas, o modelo físico deve ser atualizado neste arquivo e validado junto ao grupo quando a mudança alterar tabelas/relacionamentos.

## Pagamentos — decisão atual

No checkout do cliente, a modalidade de pagamento é separada do provedor:

- modalidades: `PIX` e `CARTAO_CREDITO`;
- provedores planejados: `MERCADO_PAGO` e `PAYPAL`;
- a bandeira do cartão não será fixada no modelo como uma única bandeira;
- `BOLETO` fica fora do pedido do cliente e pode ser avaliado futuramente no escopo extra de fornecedor/abastecimento.

Quando o pagamento for implementado fisicamente, o modelo deverá distinguir `payment_method` de `payment_provider`. Dados sensíveis do cartão não devem ser armazenados pelo CandyLand; devem ser usados tokens/metadados retornados pelo provedor.
