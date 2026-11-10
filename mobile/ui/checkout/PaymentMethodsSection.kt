package com.candyland.app.ui.checkout

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.Checkbox
import androidx.compose.material3.CheckboxDefaults
import androidx.compose.material3.Surface
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
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.OffsetMapping
import androidx.compose.ui.text.input.TransformedText
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.candyland.app.data.SavedCard
import com.candyland.app.ui.components.CandyCard
import com.candyland.app.ui.components.CandyTextField
import com.candyland.app.ui.components.GradientButton
import com.candyland.app.ui.components.OutlineCandyButton
import com.candyland.app.ui.theme.CandyColors

/**
 * Cartões salvos + formulário "Adicionar novo cartão".
 * Reutilizado no Checkout e na aba "Pagamentos" do Perfil.
 */
@Composable
fun PaymentMethodsSection(
    cards: List<SavedCard>,
    onAddCard: (holder: String, number: String, validity: String, makePrimary: Boolean) -> Unit,
    onSetPrimary: (Int) -> Unit,
    modifier: Modifier = Modifier
) {
    Column(modifier, verticalArrangement = Arrangement.spacedBy(16.dp)) {
        cards.forEach { card ->
            SavedCardView(card, onSetPrimary = { onSetPrimary(card.id) })
        }
        AddCardForm(onAddCard)
    }
}

@Composable
private fun SavedCardView(card: SavedCard, onSetPrimary: () -> Unit) {
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Box(
            Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(24.dp))
                .background(CandyColors.Brown)
                .padding(20.dp)
        ) {
            Column {
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text(
                        if (card.isPrimary) "CARTÃO PRINCIPAL" else "CARTÃO",
                        color = CandyColors.Peach,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.ExtraBold,
                        letterSpacing = 1.2.sp
                    )
                    Box(
                        Modifier
                            .size(width = 32.dp, height = 24.dp)
                            .clip(RoundedCornerShape(6.dp))
                            .background(CandyColors.Gradient)
                    )
                }
                Spacer(Modifier.height(24.dp))
                Text(
                    "••••  ••••  ••••  ${card.last4}",
                    color = Color.White,
                    fontSize = 18.sp,
                    fontWeight = FontWeight.ExtraBold,
                    letterSpacing = 2.sp
                )
                Spacer(Modifier.height(20.dp))
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text(card.holder, color = Color.White, fontSize = 12.sp, fontWeight = FontWeight.Bold)
                    Text(card.validity, color = Color.White, fontSize = 12.sp, fontWeight = FontWeight.Bold)
                }
            }
        }
        if (!card.isPrimary) {
            OutlineCandyButton(
                "Definir como principal",
                onClick = onSetPrimary,
                modifier = Modifier.fillMaxWidth(),
                color = CandyColors.Pink
            )
        }
    }
}

@Composable
private fun AddCardForm(onAddCard: (String, String, String, Boolean) -> Unit) {
    var holder by remember { mutableStateOf("") }
    var number by remember { mutableStateOf("") }   // só dígitos
    var validity by remember { mutableStateOf("") } // só dígitos (MMAA)
    var cvv by remember { mutableStateOf("") }
    var save by remember { mutableStateOf(true) }
    var submitted by remember { mutableStateOf(false) }

    val holderOk = holder.trim().length >= 3
    val numberOk = number.length == 16
    val validityOk = validity.length == 4 && validity.take(2).toIntOrNull() in 1..12
    val cvvOk = cvv.length in 3..4

    CandyCard(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
            Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                Column(Modifier.weight(1f)) {
                    Text("Adicionar novo cartão", fontWeight = FontWeight.ExtraBold, fontSize = 18.sp, color = CandyColors.Brown)
                    Text("Seus dados são protegidos e criptografados.", fontSize = 12.sp, color = CandyColors.Muted)
                }
                Surface(shape = RoundedCornerShape(50), color = CandyColors.PeachSoft) {
                    Text(
                        "Seguro",
                        modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp),
                        color = CandyColors.Pink,
                        fontWeight = FontWeight.Bold,
                        fontSize = 11.sp
                    )
                }
            }

            CandyTextField(
                value = holder,
                onValueChange = { holder = it },
                label = "Nome no cartão",
                placeholder = "Como aparece no cartão",
                isError = submitted && !holderOk,
                errorText = "Informe o nome impresso no cartão"
            )
            CandyTextField(
                value = number,
                onValueChange = { number = it.filter(Char::isDigit).take(16) },
                label = "Número do cartão",
                placeholder = "0000 0000 0000 0000",
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                visualTransformation = CardNumberTransformation,
                isError = submitted && !numberOk,
                errorText = "O número deve ter 16 dígitos"
            )
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                CandyTextField(
                    value = validity,
                    onValueChange = { validity = it.filter(Char::isDigit).take(4) },
                    label = "Validade",
                    placeholder = "MM/AA",
                    modifier = Modifier.weight(1f),
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                    visualTransformation = ValidityTransformation,
                    isError = submitted && !validityOk,
                    errorText = "Data inválida"
                )
                CandyTextField(
                    value = cvv,
                    onValueChange = { cvv = it.filter(Char::isDigit).take(4) },
                    label = "Código de segurança",
                    placeholder = "000",
                    modifier = Modifier.weight(1f),
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.NumberPassword),
                    isError = submitted && !cvvOk,
                    errorText = "Inválido"
                )
            }

            Row(
                Modifier.clickable { save = !save },
                verticalAlignment = Alignment.CenterVertically
            ) {
                Checkbox(
                    checked = save,
                    onCheckedChange = { save = it },
                    colors = CheckboxDefaults.colors(checkedColor = CandyColors.Pink)
                )
                Text("Salvar para compras futuras", fontSize = 13.sp, color = CandyColors.Brown)
            }

            GradientButton(
                text = "Cadastrar cartão",
                onClick = {
                    submitted = true
                    if (holderOk && numberOk && validityOk && cvvOk) {
                        val formatted = validity.take(2) + "/" + validity.takeLast(2)
                        onAddCard(holder.trim(), number, formatted, save)
                        holder = ""; number = ""; validity = ""; cvv = ""; submitted = false
                    }
                },
                modifier = Modifier.fillMaxWidth()
            )
        }
    }
}

/** 1234567812345678 → "1234 5678 1234 5678" */
private object CardNumberTransformation : VisualTransformation {
    override fun filter(text: AnnotatedString): TransformedText {
        val out = buildString {
            text.text.forEachIndexed { i, c ->
                if (i > 0 && i % 4 == 0) append(' ')
                append(c)
            }
        }
        val mapping = object : OffsetMapping {
            override fun originalToTransformed(offset: Int) = offset + (offset - 1).coerceAtLeast(0) / 4
            override fun transformedToOriginal(offset: Int) = offset - offset / 5
        }
        return TransformedText(AnnotatedString(out), mapping)
    }
}

/** 0829 → "08/29" */
private object ValidityTransformation : VisualTransformation {
    override fun filter(text: AnnotatedString): TransformedText {
        val t = text.text
        val out = if (t.length > 2) t.take(2) + "/" + t.drop(2) else t
        val mapping = object : OffsetMapping {
            override fun originalToTransformed(offset: Int) = if (offset > 2) offset + 1 else offset
            override fun transformedToOriginal(offset: Int) = if (offset > 2) offset - 1 else offset
        }
        return TransformedText(AnnotatedString(out), mapping)
    }
}
