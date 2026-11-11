package com.example.candyland.ui.checkout

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.candyland.data.SavedCard
import com.example.candyland.data.formatBRL
import com.example.candyland.ui.CartUiState
import com.example.candyland.ui.components.CandyCard
import com.example.candyland.ui.components.CandyLogo
import com.example.candyland.ui.components.EyebrowText
import com.example.candyland.ui.components.GradientButton
import com.example.candyland.ui.components.ScreenTitle
import com.example.candyland.ui.theme.CandyColors

@Composable
fun CheckoutScreen(
    cart: CartUiState,
    cards: List<SavedCard>,
    onAddCard: (String, String, String, Boolean) -> Unit,
    onSetPrimary: (Int) -> Unit,
    onBack: () -> Unit,
    onOrderConfirmed: () -> Unit,
    modifier: Modifier = Modifier
) {
    var showSuccess by remember { mutableStateOf(false) }
    val hasCard = cards.isNotEmpty()

    LazyColumn(
        modifier = modifier.fillMaxSize().background(CandyColors.Cream),
        contentPadding = PaddingValues(start = 20.dp, end = 20.dp, bottom = 24.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        item {
            Column {
                Row(
                    Modifier.fillMaxWidth().padding(top = 12.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(
                        Icons.AutoMirrored.Filled.ArrowBack,
                        contentDescription = "Voltar",
                        tint = CandyColors.Brown,
                        modifier = Modifier.clickable(onClick = onBack).padding(end = 12.dp)
                    )
                    CandyLogo()
                }
                Spacer(Modifier.height(16.dp))
                // Etapas: Sacola — Pagamento — Confirmação
                Text(
                    "Sacola  —  Pagamento  —  Confirmação",
                    color = CandyColors.Muted,
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold
                )
                Spacer(Modifier.height(16.dp))
                EyebrowText("Carteira")
                ScreenTitle("Métodos de pagamento")
                Text(
                    "Cadastre seus cartões para finalizar os próximos pedidos com mais rapidez.",
                    color = CandyColors.Muted,
                    fontSize = 13.sp,
                    modifier = Modifier.padding(top = 4.dp)
                )
            }
        }

        item {
            PaymentMethodsSection(
                cards = cards,
                onAddCard = onAddCard,
                onSetPrimary = onSetPrimary
            )
        }

        item { OrderSummary(cart) }

        item {
            GradientButton(
                text = "Confirmar pedido · ${formatBRL(cart.totalCents)}",
                onClick = { showSuccess = true },
                enabled = hasCard && cart.items.isNotEmpty(),
                modifier = Modifier.fillMaxWidth()
            )
            if (!hasCard) {
                Text(
                    "Cadastre um cartão para confirmar o pedido.",
                    color = CandyColors.Muted,
                    fontSize = 12.sp,
                    modifier = Modifier.padding(top = 8.dp)
                )
            }
        }
    }

    if (showSuccess) {
        AlertDialog(
            onDismissRequest = {},
            title = { Text("Pedido confirmado! 🎉", fontWeight = FontWeight.ExtraBold) },
            text = { Text("A confeitaria já recebeu seu pedido. Acompanhe o andamento pelo app.") },
            confirmButton = {
                TextButton(onClick = {
                    showSuccess = false
                    onOrderConfirmed()
                }) { Text("Voltar para a loja", color = CandyColors.Pink, fontWeight = FontWeight.Bold) }
            }
        )
    }
}

@Composable
private fun OrderSummary(cart: CartUiState) {
    CandyCard(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(20.dp)) {
            Text("Resumo do pedido", fontWeight = FontWeight.ExtraBold, fontSize = 18.sp, color = CandyColors.Brown)
            Spacer(Modifier.height(10.dp))
            cart.items.forEach {
                Row(Modifier.fillMaxWidth().padding(vertical = 3.dp)) {
                    Text("${it.quantity}× ${it.product.name}", fontSize = 13.sp, color = CandyColors.Brown, modifier = Modifier.weight(1f))
                    Text(formatBRL(it.product.priceCents * it.quantity), fontSize = 13.sp, color = CandyColors.Muted)
                }
            }
            HorizontalDivider(Modifier.padding(vertical = 10.dp), color = CandyColors.Peach)
            Row(Modifier.fillMaxWidth()) {
                Text("Entrega", fontSize = 13.sp, color = CandyColors.Muted, modifier = Modifier.weight(1f))
                Text(cart.delivery.title, fontSize = 13.sp, color = CandyColors.Brown)
            }
            if (cart.discountCents > 0) {
                Row(Modifier.fillMaxWidth().padding(top = 4.dp)) {
                    Text("Desconto", fontSize = 13.sp, color = CandyColors.Muted, modifier = Modifier.weight(1f))
                    Text("- ${formatBRL(cart.discountCents)}", fontSize = 13.sp, color = CandyColors.Green)
                }
            }
            Row(Modifier.fillMaxWidth().padding(top = 10.dp), verticalAlignment = Alignment.CenterVertically) {
                Text("Total", fontWeight = FontWeight.ExtraBold, color = CandyColors.Brown, modifier = Modifier.weight(1f))
                Text(formatBRL(cart.totalCents), fontWeight = FontWeight.ExtraBold, fontSize = 22.sp, color = CandyColors.Pink)
            }
        }
    }
}
