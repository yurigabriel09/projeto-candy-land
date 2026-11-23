package com.candyland.mobile.ui

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.util.Base64
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.unit.dp
import com.candyland.mobile.model.PaymentDto
import com.google.zxing.BarcodeFormat
import com.google.zxing.EncodeHintType
import com.google.zxing.qrcode.QRCodeWriter
import com.google.zxing.qrcode.decoder.ErrorCorrectionLevel

private fun criarBitmapPix(payment: PaymentDto): Bitmap? {
    val encoded = payment.pix_qr_code_base64?.trim().orEmpty()
    if (encoded.isNotBlank()) {
        val raw = encoded.substringAfter("base64,", encoded)
        val bytes = runCatching { Base64.decode(raw, Base64.DEFAULT) }.getOrNull()
        val decoded = bytes?.let { BitmapFactory.decodeByteArray(it, 0, it.size) }
        if (decoded != null) return decoded
    }
    val payload = payment.pix_copy_paste?.trim().orEmpty()
    if (payload.isBlank()) return null
    return runCatching {
        val hints = mapOf(EncodeHintType.MARGIN to 1, EncodeHintType.ERROR_CORRECTION to ErrorCorrectionLevel.M)
        val matrix = QRCodeWriter().encode(payload, BarcodeFormat.QR_CODE, 720, 720, hints)
        Bitmap.createBitmap(720, 720, Bitmap.Config.ARGB_8888).also { bitmap ->
            for (y in 0 until 720) for (x in 0 until 720) {
                bitmap.setPixel(x, y, if (matrix[x, y]) android.graphics.Color.BLACK else android.graphics.Color.WHITE)
            }
        }
    }.getOrNull()
}

@Composable
fun PixQrCode(payment: PaymentDto) {
    val bitmap = remember(payment.pix_qr_code_base64, payment.pix_copy_paste) { criarBitmapPix(payment) }
    Box(Modifier.fillMaxWidth().padding(vertical = 8.dp), contentAlignment = Alignment.Center) {
        if (bitmap != null) {
            Image(bitmap.asImageBitmap(), contentDescription = "QR Code Pix para pagamento", modifier = Modifier.size(232.dp))
        } else {
            Text("O provedor não retornou QR Code nem código Pix válido. Atualize os dados do pagamento.", color = MaterialTheme.colorScheme.error)
        }
    }
}
