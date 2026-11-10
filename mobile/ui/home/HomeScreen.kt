package com.candyland.app.ui.home

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.filled.Star
import androidx.compose.material3.Icon
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.candyland.app.data.FakeData
import com.candyland.app.data.Product
import com.candyland.app.data.Store
import com.candyland.app.data.formatBRL
import com.candyland.app.ui.components.CandyCard
import com.candyland.app.ui.components.CandyChip
import com.candyland.app.ui.components.CandyLogo
import com.candyland.app.ui.components.EmojiTile
import com.candyland.app.ui.components.EyebrowText
import com.candyland.app.ui.theme.CandyColors

@Composable
fun HomeScreen(
    onAddToCart: (Product) -> Unit,
    modifier: Modifier = Modifier
) {
    var query by remember { mutableStateOf("") }
    var category by remember { mutableStateOf("Todos") }

    val products = FakeData.products.filter {
        (category == "Todos" || it.category == category) &&
            (query.isBlank() || it.name.contains(query, ignoreCase = true))
    }

    LazyColumn(
        modifier = modifier.fillMaxSize().background(CandyColors.Cream),
        verticalArrangement = Arrangement.spacedBy(16.dp),
        contentPadding = androidx.compose.foundation.layout.PaddingValues(bottom = 24.dp)
    ) {
        item { HomeHeader() }

        item {
            SearchField(
                value = query,
                onValueChange = { query = it },
                modifier = Modifier.padding(horizontal = 20.dp)
            )
        }

        item { HeroBanner(Modifier.padding(horizontal = 20.dp)) }

        item {
            LazyRow(
                contentPadding = androidx.compose.foundation.layout.PaddingValues(horizontal = 20.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                items(FakeData.categories) { c ->
                    CandyChip(text = c, selected = c == category, onClick = { category = c })
                }
            }
        }

        item {
            Column(Modifier.padding(horizontal = 20.dp)) {
                EyebrowText("Perto de você")
                Text("Lojas parceiras", fontSize = 22.sp, fontWeight = FontWeight.ExtraBold, color = CandyColors.Brown)
            }
        }

        item {
            LazyRow(
                contentPadding = androidx.compose.foundation.layout.PaddingValues(horizontal = 20.dp),
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                items(FakeData.stores) { StoreCard(it) }
            }
        }

        item {
            Column(Modifier.padding(horizontal = 20.dp)) {
                EyebrowText("Os queridinhos")
                Text("Doces populares", fontSize = 22.sp, fontWeight = FontWeight.ExtraBold, color = CandyColors.Brown)
            }
        }

        if (products.isEmpty()) {
            item {
                Text(
                    "Nenhum doce encontrado 🍬",
                    modifier = Modifier.padding(horizontal = 20.dp),
                    color = CandyColors.Muted
                )
            }
        } else {
            items(products, key = { it.id }) { product ->
                ProductRow(
                    product = product,
                    onAdd = { onAddToCart(product) },
                    modifier = Modifier.padding(horizontal = 20.dp)
                )
            }
        }
    }
}

@Composable
private fun HomeHeader() {
    Column(
        Modifier
            .fillMaxWidth()
            .background(Color.White)
            .padding(horizontal = 20.dp, vertical = 12.dp)
    ) {
        CandyLogo()
        Spacer(Modifier.height(8.dp))
        Text("Entregar em", fontSize = 11.sp, color = CandyColors.Muted)
        Text(FakeData.USER_ADDRESS, fontWeight = FontWeight.Bold, color = CandyColors.Brown)
    }
}

@Composable
private fun SearchField(value: String, onValueChange: (String) -> Unit, modifier: Modifier = Modifier) {
    OutlinedTextField(
        value = value,
        onValueChange = onValueChange,
        modifier = modifier.fillMaxWidth(),
        placeholder = { Text("Buscar doces e confeitarias", color = CandyColors.Muted) },
        leadingIcon = { Icon(Icons.Default.Search, null, tint = CandyColors.Pink) },
        singleLine = true,
        shape = RoundedCornerShape(16.dp),
        colors = OutlinedTextFieldDefaults.colors(
            focusedContainerColor = Color.White,
            unfocusedContainerColor = Color.White,
            focusedBorderColor = CandyColors.Pink,
            unfocusedBorderColor = CandyColors.Peach,
            cursorColor = CandyColors.Pink
        )
    )
}

@Composable
private fun HeroBanner(modifier: Modifier = Modifier) {
    Box(
        modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(24.dp))
            .background(CandyColors.Brown)
            .padding(20.dp)
    ) {
        Column {
            Text(
                "MAIS QUE DOCES,\nNOVAS EXPERIÊNCIAS",
                color = CandyColors.Peach,
                fontSize = 11.sp,
                fontWeight = FontWeight.ExtraBold,
                letterSpacing = 1.5.sp
            )
            Spacer(Modifier.height(8.dp))
            Text(
                "Peça seus doces",
                color = Color.White,
                fontSize = 26.sp,
                fontWeight = FontWeight.ExtraBold
            )
            Text(
                "favoritos",
                color = CandyColors.Peach,
                fontSize = 30.sp,
                fontFamily = FontFamily.Cursive,
                fontStyle = FontStyle.Italic,
                fontWeight = FontWeight.Bold
            )
            Spacer(Modifier.height(8.dp))
            Text("Caseiros · Importados · Exclusivos", color = CandyColors.Peach, fontSize = 12.sp)
        }
        Text("🍭", fontSize = 56.sp, modifier = Modifier.align(Alignment.CenterEnd))
    }
}

@Composable
private fun StoreCard(store: Store) {
    CandyCard(Modifier.width(220.dp)) {
        Row(Modifier.padding(14.dp), verticalAlignment = Alignment.CenterVertically) {
            EmojiTile(store.emoji, size = 52)
            Column(Modifier.padding(start = 12.dp)) {
                Text(store.name, fontWeight = FontWeight.Bold, color = CandyColors.Brown, fontSize = 14.sp, maxLines = 1)
                Text(store.category, color = CandyColors.Muted, fontSize = 12.sp)
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.Default.Star, null, tint = CandyColors.Orange, modifier = Modifier.size(14.dp))
                    Text(" ${store.rating} · ${store.deliveryTime}", fontSize = 11.sp, color = CandyColors.Muted)
                }
            }
        }
    }
}

@Composable
private fun ProductRow(product: Product, onAdd: () -> Unit, modifier: Modifier = Modifier) {
    CandyCard(modifier.fillMaxWidth()) {
        Row(Modifier.padding(14.dp), verticalAlignment = Alignment.CenterVertically) {
            EmojiTile(product.emoji, size = 68)
            Column(Modifier.weight(1f).padding(horizontal = 12.dp)) {
                Text(product.name, fontWeight = FontWeight.Bold, color = CandyColors.Brown)
                Text(product.description, fontSize = 12.sp, color = CandyColors.Muted)
                Text(
                    formatBRL(product.priceCents),
                    color = CandyColors.Pink,
                    fontWeight = FontWeight.ExtraBold,
                    modifier = Modifier.padding(top = 4.dp)
                )
            }
            Box(
                Modifier
                    .size(40.dp)
                    .clip(CircleShape)
                    .background(CandyColors.Gradient)
                    .clickable(onClick = onAdd),
                contentAlignment = Alignment.Center
            ) { Icon(Icons.Default.Add, "Adicionar ao carrinho", tint = Color.White) }
        }
    }
}
