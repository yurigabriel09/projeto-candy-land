package com.candyland.mobile.data

import android.content.Context
import com.candyland.mobile.model.ProductDto
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken

/** Carrinho local, temporário e sem dados pessoais. O servidor recalcula preços/estoque no checkout. */
data class StoredCartItem(val product: ProductDto, val quantity: Int)

object CartStorage {
    private const val PREFS = "candyland_public_cart"
    private const val CART_KEY = "items"
    private val gson = Gson()

    fun load(context: Context): List<StoredCartItem> {
        val raw = context.applicationContext.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .getString(CART_KEY, null) ?: return emptyList()
        val type = object : TypeToken<List<StoredCartItem>>() {}.type
        return runCatching { gson.fromJson<List<StoredCartItem>>(raw, type).orEmpty() }
            .getOrDefault(emptyList())
            .filter { it.product.id > 0 && it.product.restaurantId > 0 && it.quantity in 1..99 }
    }

    fun save(context: Context, items: List<StoredCartItem>) {
        val safeItems = items.filter { it.product.id > 0 && it.product.restaurantId > 0 && it.quantity in 1..99 }
        context.applicationContext.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .edit().putString(CART_KEY, gson.toJson(safeItems)).apply()
    }
}
