package com.candyland.app.ui.cart

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.candyland.app.data.CartItem
import com.candyland.app.data.DeliveryOption
import com.candyland.app.data.formatBRL
import com.candyland.app.ui.CartUiState
import com.candyland.app.ui.components.CandyCard
import com.candyland.app.ui.components.CandyLogo
import com.candyland.app.ui.components.EmojiTile
import com.candyland.app.ui.components.EyebrowText
import com.candyland.app.ui.components.GradientButton
import com.candyland.app.ui.components.QuantityStepper
import com.candyland.app.ui.components.ScreenTitle
import com.candyland.app.ui.theme.CandyColors

@Composable
fun CartScreen(
    state: CartUiState,
    onIncrement: (Int) -> Unit,
    onDecrement: (Int) -> Unit,
    onDeliveryChange: (DeliveryOption) -> Unit,
    onCouponChange: (String) -> Unit,
    onApplyCoupon: () -> Unit,
    onAddItems: () -> Unit,
    onCheckout: () -> Unit,
    modifier: Modifier = Modifier
) {
    LazyColumn(
        modifier = modifier.fillMaxSize().background(CandyColors.Cream),
        contentPadding = PaddingValues(start = 20.dp, end = 20.dp, bottom = 24.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        item {
            Column {
                Row(
                    Modifier.fillMaxWidth().padding(top = 12.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    CandyLogo()
                    // Indicador de etapas: Sacola — Pagamento — Confirmação
                    Text("Sacola", color = CandyColors.Pink, fontWeight = FontWeight.Bold, fontSize = 12.sp)
                }
                Spacer(Modifier.height(20.dp))
                EyebrowText("Seu pedido")
                Row(
                    Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    ScreenTitle("Carrinho de doces")
                }
                Surface(
                    shape = RoundedCornerShape(50),
                    color = CandyColors.PeachSoft,
                    modifier = Modifier.padding(top = 8.dp)
                ) {
                    Text(
                        "${state.itemCount} ${if (state.itemCount == 1) "item" else "itens"}",
                        modifier = Modifier.padding(horizontal = 14.dp, vertical = 6.dp),
                        fontWeight = FontWeight.Bold,
                        fontSize = 12.sp,
                        color = CandyColors.Brown
                    )
                }
            }
        }

        if (state.items.isEmpty()) {
            item { EmptyCart(onAddItems) }
        } else {
            item {
                CartItemsCard(
                    items = state.items,
                    onIncrement = onIncrement,
                    onDecrement = onDecrement,
                    onAddItems = onAddItems
                )
            }
            item { DeliveryCard(state.delivery, onDeliveryChange) }
            item {
                SummaryCard(
                    state = state,
                    onCouponChange = onCouponChange,
                    onApplyCoupon = onApplyCoupon,
                    onCheckout = onCheckout
                )
            }
        }
    }
}

@Composable
private fun EmptyCart(onAddItems: () -> Unit) {
    CandyCard(Modifier.fillMaxWidth()) {
        Column(
            Modifier.fillMaxWidth().padding(28.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text("🛍️", fontSize = 48.sp)
            Text("Sua sacola está vazia", fontWeight = FontWeight.ExtraBold, color = CandyColors.Brown, fontSize = 18.sp)
            Text(
                "Adicione alguns doces para começar.",
                color = CandyColors.Muted,
                fontSize = 13.sp,
                modifier = Modifier.padding(top = 4.dp, bottom = 16.dp)
            )
            GradientButton("Ver doces", onAddItems, Modifier.fillMaxWidth())
        }
    }
}

@Composable
private fun CartItemsCard(
    items: List<CartItem>,
    onIncrement: (Int) -> Unit,
    onDecrement: (Int) -> Unit,
    onAddItems: () -> Unit
) {
    CandyCard(Modifier.fillMaxWidth()) {
        Column {
            // Cabeçalho da loja
            Row(Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
                EmojiTile("🍰", size = 48)
                Column(Modifier.weight(1f).padding(horizontal = 12.dp)) {
                    Text(items.first().product.storeName, fontWeight = FontWeight.ExtraBold, color = CandyColors.Brown)
                    Text("Entrega estimada em 25–40 min", fontSize = 12.sp, color = CandyColors.Muted)
                }
                Text(
                    "Adicionar itens",
                    color = CandyColors.Pink,
                    fontWeight = FontWeight.Bold,
                    fontSize = 12.sp,
                    modifier = Modifier.clickable(onClick = onAddItems)
                )
            }
            items.forEach { item ->
                HorizontalDivider(color = CandyColors.Peach)
                CartItemRow(item, onIncrement, onDecrement)
            }
        }
    }
}

@Composable
private fun CartItemRow(item: CartItem, onIncrement: (Int) -> Unit, onDecrement: (Int) -> Unit) {
    Row(Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
        EmojiTile(item.product.emoji, size = 56)
        Column(Modifier.weight(1f).padding(horizontal = 12.dp)) {
            Text(item.product.name, fontWeight = FontWeight.Bold, color = CandyColors.Brown, fontSize = 14.sp)
            Text(item.product.description, fontSize = 11.sp, color = CandyColors.Muted, maxLines = 2)
            Text(
                formatBRL(item.product.priceCents),
                color = CandyColors.Pink,
                fontWeight = FontWeight.ExtraBold,
                fontSize = 14.sp,
                modifier = Modifier.padding(top = 2.dp)
            )
        }
        QuantityStepper(
            quantity = item.quantity,
            onMinus = { onDecrement(item.product.id) },
            onPlus = { onIncrement(item.product.id) }
        )
    }
}

@Composable
private fun DeliveryCard(selected: DeliveryOption, onChange: (DeliveryOption) -> Unit) {
    CandyCard(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp)) {
            Text("Como você quer receber?", fontWeight = FontWeight.ExtraBold, color = CandyColors.Brown)
            Spacer(Modifier.height(12.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                DeliveryOption.entries.forEach { option ->
                    val isSelected = option == selected
                    Surface(
                        modifier = Modifier.weight(1f).clickable { onChange(option) },
                        shape = RoundedCornerShape(14.dp),
                        color = Color.White,
                        border = BorderStroke(
                            if (isSelected) 1.5.dp else 1.dp,
                            if (isSelected) CandyColors.Pink else CandyColors.Peach
                        )
                    ) {
                        Column(Modifier.padding(12.dp)) {
                            Text(option.title, fontWeight = FontWeight.Bold, fontSize = 13.sp, color = CandyColors.Brown)
                            Text(option.subtitle, fontSize = 11.sp, color = CandyColors.Muted)
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun SummaryCard(
    state: CartUiState,
    onCouponChange: (String) -> Unit,
    onApplyCoupon: () -> Unit,
    onCheckout: () -> Unit
) {
    CandyCard(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(20.dp)) {
            Text("Resumo do pedido", fontWeight = FontWeight.ExtraBold, fontSize = 18.sp, color = CandyColors.Brown)
            Spacer(Modifier.height(14.dp))

            // Cupom
            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(
                    value = state.couponInput,
                    onValueChange = onCouponChange,
                    modifier = Modifier.weight(1f),
                    placeholder = { Text("Cupom de desconto", color = CandyColors.Peach, fontSize = 13.sp) },
                    singleLine = true,
                    isError = state.couponError,
                    shape = RoundedCornerShape(14.dp),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedContainerColor = CandyColors.Cream,
                        unfocusedContainerColor = CandyColors.Cream,
                        focusedBorderColor = CandyColors.Pink,
                        unfocusedBorderColor = CandyColors.Peach,
                        cursorColor = CandyColors.Pink
                    )
                )
                Box(
                    Modifier
                        .height(56.dp)
                        .clip(RoundedCornerShape(14.dp))
                        .background(CandyColors.Brown)
                        .clickable(onClick = onApplyCoupon)
                        .padding(horizontal = 18.dp),
                    contentAlignment = Alignment.Center
                ) { Text("Aplicar", color = Color.White, fontWeight = FontWeight.Bold) }
            }
            if (state.couponError) {
                Text("Cupom inválido", color = CandyColors.Red, fontSize = 12.sp, modifier = Modifier.padding(top = 4.dp))
            }
            if (state.appliedCoupon != null) {
                Text("Cupom ${state.appliedCoupon} aplicado ✓", color = CandyColors.Green, fontSize = 12.sp, modifier = Modifier.padding(top = 4.dp))
            }

            Spacer(Modifier.height(14.dp))
            SummaryLine("Subtotal", formatBRL(state.subtotalCents))
            if (state.discountCents > 0) {
                SummaryLine("Desconto", "- ${formatBRL(state.discountCents)}", valueColor = CandyColors.Green)
            }
            SummaryLine(
                "Taxa de entrega",
                if (state.deliveryFeeCents == 0) "Grátis" else formatBRL(state.deliveryFeeCents),
                valueColor = if (state.deliveryFeeCents == 0) CandyColors.Green else CandyColors.Brown,
                bold = state.deliveryFeeCents == 0
            )

            HorizontalDivider(Modifier.padding(vertical = 12.dp), color = CandyColors.Peach)

            Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                Text("Total", fontWeight = FontWeight.ExtraBold, color = CandyColors.Brown, modifier = Modifier.weight(1f))
                Text(formatBRL(state.totalCents), fontWeight = FontWeight.ExtraBold, fontSize = 22.sp, color = CandyColors.Pink)
            }
            Text(
                "Pagamento na próxima etapa",
                fontSize = 11.sp,
                color = CandyColors.Muted,
                modifier = Modifier.fillMaxWidth().padding(top = 2.dp, bottom = 16.dp),
                textAlign = androidx.compose.ui.text.style.TextAlign.End
            )
            GradientButton("Ir para pagamento", onCheckout, Modifier.fillMaxWidth())
            Text(
                "Compra segura e protegida pelo Candyland",
                fontSize = 11.sp,
                color = CandyColors.Muted,
                modifier = Modifier.fillMaxWidth().padding(top = 10.dp),
                textAlign = androidx.compose.ui.text.style.TextAlign.Center
            )
        }
    }
}

@Composable
private fun SummaryLine(
    label: String,
    value: String,
    valueColor: Color = CandyColors.Brown,
    bold: Boolean = false
) {
    Row(Modifier.fillMaxWidth().padding(vertical = 3.dp)) {
        Text(label, color = CandyColors.Muted, fontSize = 13.sp, modifier = Modifier.weight(1f))
        Text(value, color = valueColor, fontSize = 13.sp, fontWeight = if (bold) FontWeight.Bold else FontWeight.Normal)
    }
}
