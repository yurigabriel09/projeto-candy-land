package com.candyland.app.data

import java.text.NumberFormat
import java.util.Locale

/** Preços em centavos para evitar erros de ponto flutuante. */
data class Product(
    val id: Int,
    val name: String,
    val description: String,
    val priceCents: Int,
    val emoji: String,
    val category: String,
    val storeName: String
)

data class Store(
    val id: Int,
    val name: String,
    val category: String,
    val rating: Double,
    val deliveryTime: String,
    val emoji: String
)

data class CartItem(val product: Product, val quantity: Int)

enum class DeliveryOption(val title: String, val subtitle: String) {
    HOME("Receber em casa", "Rua das Flores, 123"),
    PICKUP("Retirar na loja", "Pronto em 20–30 min")
}

data class SavedCard(
    val id: Int,
    val holder: String,
    val last4: String,
    val validity: String,
    val isPrimary: Boolean
)

private val brLocale = Locale("pt", "BR")

fun formatBRL(cents: Int): String =
    NumberFormat.getCurrencyInstance(brLocale).format(cents / 100.0).replace(' ', ' ')
