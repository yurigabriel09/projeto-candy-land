package com.candyland.app.ui

import androidx.lifecycle.ViewModel
import com.candyland.app.data.CartItem
import com.candyland.app.data.DeliveryOption
import com.candyland.app.data.FakeData
import com.candyland.app.data.Product
import com.candyland.app.data.SavedCard
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update

data class CartUiState(
    val items: List<CartItem> = emptyList(),
    val delivery: DeliveryOption = DeliveryOption.HOME,
    val couponInput: String = "",
    val appliedCoupon: String? = null,
    val couponError: Boolean = false
) {
    val itemCount: Int get() = items.sumOf { it.quantity }
    val subtotalCents: Int get() = items.sumOf { it.product.priceCents * it.quantity }
    val discountCents: Int get() = if (appliedCoupon == "DOCE10") subtotalCents / 10 else 0
    val deliveryFeeCents: Int get() = 0 // entrega grátis, como no protótipo
    val totalCents: Int get() = subtotalCents - discountCents + deliveryFeeCents
}

class CartViewModel : ViewModel() {
    private val _state = MutableStateFlow(CartUiState(items = FakeData.initialCart))
    val state: StateFlow<CartUiState> = _state.asStateFlow()

    fun add(product: Product) = _state.update { s ->
        val existing = s.items.find { it.product.id == product.id }
        val items = if (existing == null) s.items + CartItem(product, 1)
        else s.items.map { if (it.product.id == product.id) it.copy(quantity = it.quantity + 1) else it }
        s.copy(items = items)
    }

    fun increment(productId: Int) = changeQuantity(productId, +1)
    fun decrement(productId: Int) = changeQuantity(productId, -1)

    private fun changeQuantity(productId: Int, delta: Int) = _state.update { s ->
        val items = s.items
            .map { if (it.product.id == productId) it.copy(quantity = it.quantity + delta) else it }
            .filter { it.quantity > 0 } // chegou a 0 → remove do carrinho
        s.copy(items = items)
    }

    fun setDelivery(option: DeliveryOption) = _state.update { it.copy(delivery = option) }

    fun onCouponChange(text: String) =
        _state.update { it.copy(couponInput = text.uppercase(), couponError = false) }

    fun applyCoupon() = _state.update { s ->
        if (s.couponInput.trim() == "DOCE10") s.copy(appliedCoupon = "DOCE10", couponError = false)
        else s.copy(appliedCoupon = null, couponError = s.couponInput.isNotBlank())
    }

    fun clear() = _state.update { CartUiState() }
}

class PaymentViewModel : ViewModel() {
    private val _cards = MutableStateFlow(FakeData.initialCards)
    val cards: StateFlow<List<SavedCard>> = _cards.asStateFlow()

    fun addCard(holder: String, number: String, validity: String, makePrimary: Boolean) =
        _cards.update { list ->
            val isPrimary = makePrimary || list.isEmpty()
            val base = if (isPrimary) list.map { it.copy(isPrimary = false) } else list
            base + SavedCard(
                id = (list.maxOfOrNull { it.id } ?: 0) + 1,
                holder = holder.uppercase(),
                last4 = number.takeLast(4),
                validity = validity,
                isPrimary = isPrimary
            )
        }

    fun setPrimary(id: Int) =
        _cards.update { list -> list.map { it.copy(isPrimary = it.id == id) } }
}
