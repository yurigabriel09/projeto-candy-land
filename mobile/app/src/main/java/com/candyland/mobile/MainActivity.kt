package com.candyland.mobile

import android.Manifest
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import com.candyland.mobile.data.ApiProvider
import com.candyland.mobile.ui.CandyLandApp

class MainActivity : ComponentActivity() {
    private var oauthUri by mutableStateOf<Uri?>(null)
    private var paymentUri by mutableStateOf<Uri?>(null)

    private fun routeIncomingUri(uri: Uri?) {
        oauthUri = uri?.takeIf { it.scheme == "com.candyland.mobile" && it.host == "oauth" }
        paymentUri = uri?.takeIf { it.scheme == "com.candyland.mobile" && it.host == "payment" }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        ApiProvider.initialize(applicationContext)
        routeIncomingUri(intent?.data)
        solicitarPermissaoNotificacoes()
        setContent {
            CandyLandApp(
                applicationContext = applicationContext,
                oauthUri = oauthUri,
                onOAuthUriConsumed = { oauthUri = null },
                paymentUri = paymentUri,
                onPaymentUriConsumed = { paymentUri = null }
            )
        }
    }

    override fun onNewIntent(intent: android.content.Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        routeIncomingUri(intent.data)
    }

    private fun solicitarPermissaoNotificacoes() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU &&
            ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED
        ) {
            ActivityCompat.requestPermissions(this, arrayOf(Manifest.permission.POST_NOTIFICATIONS), 1001)
        }
    }
}
