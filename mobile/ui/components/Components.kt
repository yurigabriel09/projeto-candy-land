package com.candyland.app.ui.components

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material3.Icon
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.candyland.app.ui.theme.CandyColors

/** Logo "C" + "Candyland" do cabeçalho. */
@Composable
fun CandyLogo(modifier: Modifier = Modifier) {
    Row(modifier, verticalAlignment = Alignment.CenterVertically) {
        Box(
            Modifier
                .size(36.dp)
                .clip(RoundedCornerShape(10.dp))
                .background(CandyColors.Gradient),
            contentAlignment = Alignment.Center
        ) {
            Text("C", color = Color.White, fontWeight = FontWeight.ExtraBold, fontSize = 18.sp)
        }
        Text(
            "Candyland",
            modifier = Modifier.padding(start = 8.dp),
            color = CandyColors.Pink,
            fontFamily = FontFamily.Cursive,
            fontStyle = FontStyle.Italic,
            fontWeight = FontWeight.Bold,
            fontSize = 26.sp
        )
    }
}

/** Texto pequeno rosa em caixa alta ("SEU PEDIDO", "CARTEIRA"...). */
@Composable
fun EyebrowText(text: String, modifier: Modifier = Modifier) {
    Text(
        text.uppercase(),
        modifier = modifier,
        color = CandyColors.Pink,
        fontSize = 11.sp,
        fontWeight = FontWeight.ExtraBold,
        letterSpacing = 1.5.sp
    )
}

@Composable
fun ScreenTitle(text: String, modifier: Modifier = Modifier) {
    Text(
        text,
        modifier = modifier,
        color = CandyColors.Brown,
        fontSize = 28.sp,
        fontWeight = FontWeight.ExtraBold
    )
}

/** Cartão branco com borda pêssego e cantos bem arredondados. */
@Composable
fun CandyCard(
    modifier: Modifier = Modifier,
    content: @Composable () -> Unit
) {
    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(24.dp),
        color = Color.White,
        border = BorderStroke(1.dp, CandyColors.Peach),
        shadowElevation = 2.dp,
        content = content
    )
}

/** Botão principal com degradê rosa → laranja. */
@Composable
fun GradientButton(
    text: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    enabled: Boolean = true
) {
    val bg = if (enabled) Modifier.background(CandyColors.Gradient)
    else Modifier.background(CandyColors.Peach)
    Box(
        modifier = modifier
            .height(52.dp)
            .clip(RoundedCornerShape(16.dp))
            .then(bg)
            .clickable(enabled = enabled, onClick = onClick),
        contentAlignment = Alignment.Center
    ) {
        Text(text, color = Color.White, fontWeight = FontWeight.Bold, fontSize = 16.sp)
    }
}

/** Botão secundário (contorno). */
@Composable
fun OutlineCandyButton(
    text: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    color: Color = CandyColors.Brown,
    borderColor: Color = CandyColors.Peach
) {
    Box(
        modifier = modifier
            .height(44.dp)
            .clip(RoundedCornerShape(14.dp))
            .border(1.dp, borderColor, RoundedCornerShape(14.dp))
            .background(Color.White)
            .clickable(onClick = onClick)
            .padding(horizontal = 16.dp),
        contentAlignment = Alignment.Center
    ) {
        Text(text, color = color, fontWeight = FontWeight.Bold, fontSize = 14.sp)
    }
}

/** Seletor de quantidade [ - 1 + ] do carrinho. */
@Composable
fun QuantityStepper(
    quantity: Int,
    onMinus: () -> Unit,
    onPlus: () -> Unit,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier
            .clip(CircleShape)
            .border(1.dp, CandyColors.Peach, CircleShape)
            .padding(horizontal = 4.dp, vertical = 4.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Box(
            Modifier.size(28.dp).clip(CircleShape).clickable(onClick = onMinus),
            contentAlignment = Alignment.Center
        ) { Text("−", color = CandyColors.Pink, fontWeight = FontWeight.ExtraBold, fontSize = 20.sp) }

        Text(
            "$quantity",
            modifier = Modifier.padding(horizontal = 10.dp),
            fontWeight = FontWeight.Bold,
            color = CandyColors.Brown
        )

        Box(
            Modifier.size(28.dp).clip(CircleShape).background(CandyColors.Gradient).clickable(onClick = onPlus),
            contentAlignment = Alignment.Center
        ) { Icon(Icons.Default.Add, "Aumentar", tint = Color.White, modifier = Modifier.size(16.dp)) }
    }
}

/** Quadradinho com emoji (no lugar da foto do produto). */
@Composable
fun EmojiTile(emoji: String, size: Int = 64, modifier: Modifier = Modifier) {
    Box(
        modifier
            .size(size.dp)
            .clip(RoundedCornerShape(16.dp))
            .background(CandyColors.PeachSoft),
        contentAlignment = Alignment.Center
    ) { Text(emoji, fontSize = (size * 0.5).sp) }
}

/** Campo de texto no estilo dos protótipos (fundo pêssego, borda arredondada). */
@Composable
fun CandyTextField(
    value: String,
    onValueChange: (String) -> Unit,
    label: String,
    placeholder: String,
    modifier: Modifier = Modifier,
    keyboardOptions: KeyboardOptions = KeyboardOptions.Default,
    visualTransformation: VisualTransformation = VisualTransformation.None,
    isError: Boolean = false,
    errorText: String? = null,
    enabled: Boolean = true
) {
    Column(modifier) {
        Text(label, fontWeight = FontWeight.Bold, fontSize = 13.sp, color = CandyColors.Brown)
        OutlinedTextField(
            value = value,
            onValueChange = onValueChange,
            modifier = Modifier.fillMaxWidth().padding(top = 6.dp),
            placeholder = { Text(placeholder, color = CandyColors.Peach) },
            singleLine = true,
            enabled = enabled,
            isError = isError,
            keyboardOptions = keyboardOptions,
            visualTransformation = visualTransformation,
            shape = RoundedCornerShape(14.dp),
            textStyle = TextStyle(color = CandyColors.Brown, fontSize = 15.sp),
            colors = OutlinedTextFieldDefaults.colors(
                focusedContainerColor = CandyColors.Cream,
                unfocusedContainerColor = CandyColors.Cream,
                disabledContainerColor = CandyColors.Cream,
                focusedBorderColor = CandyColors.Pink,
                unfocusedBorderColor = CandyColors.Peach,
                errorBorderColor = CandyColors.Red,
                cursorColor = CandyColors.Pink
            )
        )
        if (isError && errorText != null) {
            Text(errorText, color = CandyColors.Red, fontSize = 12.sp, modifier = Modifier.padding(top = 4.dp))
        }
    }
}

/** Chip simples (categorias e abas). */
@Composable
fun CandyChip(
    text: String,
    selected: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    val shape = RoundedCornerShape(50)
    Box(
        modifier = modifier
            .clip(shape)
            .then(
                if (selected) Modifier.background(CandyColors.Gradient)
                else Modifier.background(Color.White).border(1.dp, CandyColors.Peach, shape)
            )
            .clickable(onClick = onClick)
            .padding(horizontal = 16.dp, vertical = 8.dp),
        contentAlignment = Alignment.Center
    ) {
        Text(
            text,
            color = if (selected) Color.White else CandyColors.Brown,
            fontWeight = FontWeight.Bold,
            fontSize = 13.sp
        )
    }
}

val ScreenPadding = PaddingValues(horizontal = 20.dp)
val SpaceBetween12 = Arrangement.spacedBy(12.dp)
