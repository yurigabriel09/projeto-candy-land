package com.candyland.app.data

/** Dados mockados enquanto o back-end não está integrado. */
object FakeData {
    val categories = listOf("Todos", "Bolos", "Brigadeiros", "Cupcakes", "Importados")

    val stores = listOf(
        Store(1, "Confeitaria Sweet Dreams", "Bolos e tortas", 4.9, "25–40 min", "🍰"),
        Store(2, "Brigadeiria da Vovó", "Brigadeiros", 4.8, "20–35 min", "🍫"),
        Store(3, "Cupcake Club", "Cupcakes", 4.7, "30–45 min", "🧁"),
        Store(4, "Doces do Mundo", "Importados", 4.9, "35–50 min", "🍭")
    )

    val products = listOf(
        Product(1, "Bolo de Chocolate Belga", "Tamanho médio · Serve até 12 pessoas", 8990, "🍰", "Bolos", "Confeitaria Sweet Dreams"),
        Product(2, "Brigadeiro Gourmet", "Caixa com 9 unidades sortidas", 3490, "🍫", "Brigadeiros", "Confeitaria Sweet Dreams"),
        Product(3, "Cupcake Red Velvet", "1 unidade · Cream cheese frosting", 1290, "🧁", "Cupcakes", "Confeitaria Sweet Dreams"),
        Product(4, "Torta de Morango", "Tamanho pequeno · Serve até 6 pessoas", 6490, "🍓", "Bolos", "Confeitaria Sweet Dreams"),
        Product(5, "Pirulito Arco-íris", "Importado · 1 unidade", 990, "🍭", "Importados", "Doces do Mundo"),
        Product(6, "Caixa de Macarons", "Caixa com 6 unidades", 4590, "🍬", "Importados", "Doces do Mundo")
    )

    // Itens iniciais do carrinho (iguais ao protótipo)
    val initialCart = listOf(
        CartItem(products[0], 1),
        CartItem(products[1], 1),
        CartItem(products[2], 2)
    )

    val initialCards = listOf(
        SavedCard(1, "MARINA SILVA", "4421", "08/29", isPrimary = true)
    )

    const val USER_NAME = "Marina Silva"
    const val USER_EMAIL = "marina.silva@email.com"
    const val USER_PHONE = "(11) 99999-0000"
    const val USER_ADDRESS = "Rua das Flores, 123"
}
