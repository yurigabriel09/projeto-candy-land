package com.example.candyland.ui.profile

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
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateMapOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.candyland.data.FakeData
import com.example.candyland.data.SavedCard
import com.example.candyland.ui.checkout.PaymentMethodsSection
import com.example.candyland.ui.components.CandyCard
import com.example.candyland.ui.components.CandyChip
import com.example.candyland.ui.components.CandyLogo
import com.example.candyland.ui.components.CandyTextField
import com.example.candyland.ui.components.EyebrowText
import com.example.candyland.ui.components.GradientButton
import com.example.candyland.ui.components.OutlineCandyButton
import com.example.candyland.ui.components.ScreenTitle
import com.example.candyland.ui.theme.CandyColors

private enum class ProfileTab(val number: String, val title: String) {
    PERSONAL("01", "Dados pessoais"),
    SETTINGS("02", "Configurações"),
    PAYMENTS("03", "Pagamentos")
}

@Composable
fun ProfileScreen(
    cards: List<SavedCard>,
    onAddCard: (String, String, String, Boolean) -> Unit,
    onSetPrimary: (Int) -> Unit,
    onLogout: () -> Unit,
    modifier: Modifier = Modifier
) {
    var tab by remember { mutableStateOf(ProfileTab.PERSONAL) }

    LazyColumn(
        modifier = modifier.fillMaxSize().background(CandyColors.Cream),
        contentPadding = PaddingValues(start = 20.dp, end = 20.dp, bottom = 24.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        item {
            Column {
                Box(Modifier.padding(top = 12.dp)) { CandyLogo() }
                Spacer(Modifier.height(16.dp))
                ProfileHeaderCard(tab = tab, onTabChange = { tab = it }, onLogout = onLogout)
            }
        }

        when (tab) {
            ProfileTab.PERSONAL -> item { PersonalDataContent() }
            ProfileTab.SETTINGS -> item { SettingsContent() }
            ProfileTab.PAYMENTS -> item {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    EyebrowText("Carteira")
                    ScreenTitle("Métodos de pagamento")
                    Spacer(Modifier.height(4.dp))
                    PaymentMethodsSection(cards, onAddCard, onSetPrimary)
                }
            }
        }
    }
}

/** Equivalente ao menu lateral escuro dos protótipos (01 / 02 / 03 + Sair da conta). */
@Composable
private fun ProfileHeaderCard(tab: ProfileTab, onTabChange: (ProfileTab) -> Unit, onLogout: () -> Unit) {
    Column(
        Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(24.dp))
            .background(CandyColors.Brown)
            .padding(18.dp)
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Box(
                Modifier.size(48.dp).clip(CircleShape).background(CandyColors.Gradient),
                contentAlignment = Alignment.Center
            ) { Text("MS", color = Color.White, fontWeight = FontWeight.ExtraBold) }
            Column(Modifier.padding(start = 12.dp)) {
                Text(FakeData.USER_NAME, color = Color.White, fontWeight = FontWeight.ExtraBold, fontSize = 16.sp)
                Text("Cliente doce desde 2024", color = CandyColors.Peach, fontSize = 11.sp)
            }
        }
        HorizontalDivider(Modifier.padding(vertical = 14.dp), color = Color.White.copy(alpha = 0.12f))

        ProfileTab.entries.forEach { item ->
            val selected = item == tab
            Row(
                Modifier
                    .fillMaxWidth()
                    .padding(vertical = 3.dp)
                    .clip(RoundedCornerShape(16.dp))
                    .background(if (selected) Color.White else Color.Transparent)
                    .clickable { onTabChange(item) }
                    .padding(horizontal = 10.dp, vertical = 10.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Box(
                    Modifier
                        .size(28.dp)
                        .clip(RoundedCornerShape(8.dp))
                        .background(if (selected) CandyColors.Gradient else androidx.compose.ui.graphics.SolidColor(Color.White.copy(alpha = 0.1f))),
                    contentAlignment = Alignment.Center
                ) { Text(item.number, color = Color.White, fontSize = 10.sp, fontWeight = FontWeight.ExtraBold) }
                Text(
                    item.title,
                    modifier = Modifier.padding(start = 12.dp),
                    color = if (selected) CandyColors.Brown else CandyColors.Peach,
                    fontWeight = FontWeight.Bold,
                    fontSize = 14.sp
                )
            }
        }

        HorizontalDivider(Modifier.padding(vertical = 12.dp), color = Color.White.copy(alpha = 0.12f))
        Text(
            "Sair da conta",
            color = CandyColors.Peach,
            fontSize = 12.sp,
            modifier = Modifier.fillMaxWidth().clickable(onClick = onLogout),
            textAlign = androidx.compose.ui.text.style.TextAlign.Center
        )
    }
}

@Composable
private fun PersonalDataContent() {
    var name by remember { mutableStateOf(FakeData.USER_NAME) }
    var email by remember { mutableStateOf(FakeData.USER_EMAIL) }
    var phone by remember { mutableStateOf(FakeData.USER_PHONE) }
    var address by remember { mutableStateOf(FakeData.USER_ADDRESS) }
    var saved by remember { mutableStateOf(false) }

    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        EyebrowText("Minha conta")
        ScreenTitle("Dados pessoais")
        Text("Mantenha suas informações atualizadas para receber seus pedidos.", color = CandyColors.Muted, fontSize = 13.sp)
        Spacer(Modifier.height(4.dp))
        CandyCard(Modifier.fillMaxWidth()) {
            Column(Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
                CandyTextField(name, { name = it; saved = false }, "Nome completo", "Seu nome")
                CandyTextField(email, { email = it; saved = false }, "E-mail", "seu@email.com")
                CandyTextField(phone, { phone = it; saved = false }, "Telefone", "(00) 00000-0000")
                CandyTextField(address, { address = it; saved = false }, "Endereço de entrega", "Rua, número")
                GradientButton("Salvar alterações", { saved = true }, Modifier.fillMaxWidth())
                if (saved) Text("Dados salvos ✓", color = CandyColors.Green, fontSize = 12.sp)
            }
        }
    }
}

@Composable
private fun SettingsContent() {
    // Estado inicial igual ao protótipo
    val toggles = remember {
        mutableStateMapOf(
            "orders" to true,
            "offers" to true,
            "news" to false,
            "recommendations" to true
        )
    }
    var confirmDelete by remember { mutableStateOf(false) }

    Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            EyebrowText("Preferências")
            ScreenTitle("Configurações")
            Text(
                "Escolha como o Candyland conversa com você e personaliza sua experiência.",
                color = CandyColors.Muted, fontSize = 13.sp
            )
        }

        CandyCard(Modifier.fillMaxWidth()) {
            Column(Modifier.padding(20.dp)) {
                Text("Notificações", fontWeight = FontWeight.ExtraBold, fontSize = 18.sp, color = CandyColors.Brown)
                Text("Você pode alterar essas preferências quando quiser.", fontSize = 12.sp, color = CandyColors.Muted)
                Spacer(Modifier.height(8.dp))
                SettingRow("Atualizações de pedidos", "Status, entrega e mensagens da loja", toggles["orders"] == true) { toggles["orders"] = it }
                HorizontalDivider(color = CandyColors.Peach)
                SettingRow("Ofertas e cupons", "Promoções de lojas que combinam com você", toggles["offers"] == true) { toggles["offers"] = it }
                HorizontalDivider(color = CandyColors.Peach)
                SettingRow("Novidades do Candyland", "Uma seleção doce enviada por e-mail", toggles["news"] == true) { toggles["news"] = it }
                HorizontalDivider(color = CandyColors.Peach)
                SettingRow("Recomendações personalizadas", "Sugestões baseadas nos seus pedidos", toggles["recommendations"] == true) { toggles["recommendations"] = it }
            }
        }

        CandyCard(Modifier.fillMaxWidth()) {
            Column(Modifier.padding(20.dp)) {
                Text("Privacidade e acesso", fontWeight = FontWeight.ExtraBold, fontSize = 18.sp, color = CandyColors.Brown)
                Spacer(Modifier.height(12.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    OutlineCandyButton("Baixar meus dados", onClick = { /* TODO: exportar dados (LGPD) */ })
                    OutlineCandyButton(
                        "Excluir minha conta",
                        onClick = { confirmDelete = true },
                        color = CandyColors.Red,
                        borderColor = CandyColors.Pink
                    )
                }
            }
        }
    }

    if (confirmDelete) {
        AlertDialog(
            onDismissRequest = { confirmDelete = false },
            title = { Text("Excluir conta?", fontWeight = FontWeight.ExtraBold) },
            text = { Text("Essa ação não pode ser desfeita.") },
            confirmButton = {
                TextButton(onClick = { confirmDelete = false /* TODO: chamar API */ }) {
                    Text("Excluir", color = CandyColors.Red, fontWeight = FontWeight.Bold)
                }
            },
            dismissButton = {
                TextButton(onClick = { confirmDelete = false }) { Text("Cancelar", color = CandyColors.Brown) }
            }
        )
    }
}

@Composable
private fun SettingRow(title: String, subtitle: String, checked: Boolean, onChange: (Boolean) -> Unit) {
    Row(Modifier.fillMaxWidth().padding(vertical = 12.dp), verticalAlignment = Alignment.CenterVertically) {
        Column(Modifier.weight(1f)) {
            Text(title, fontWeight = FontWeight.Bold, fontSize = 14.sp, color = CandyColors.Brown)
            Text(subtitle, fontSize = 12.sp, color = CandyColors.Muted)
        }
        Switch(
            checked = checked,
            onCheckedChange = onChange,
            colors = SwitchDefaults.colors(
                checkedTrackColor = CandyColors.Pink,
                checkedThumbColor = Color.White,
                uncheckedTrackColor = CandyColors.Peach,
                uncheckedThumbColor = Color.White,
                uncheckedBorderColor = Color.Transparent,
                checkedBorderColor = Color.Transparent
            )
        )
    }
}
