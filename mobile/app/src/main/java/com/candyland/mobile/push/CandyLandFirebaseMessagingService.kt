package com.candyland.mobile.push

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Intent
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import com.candyland.mobile.MainActivity
import com.candyland.mobile.data.ApiProvider
import com.candyland.mobile.data.SessionManager
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch

class CandyLandFirebaseMessagingService : FirebaseMessagingService() {
    override fun onNewToken(token: String) {
        super.onNewToken(token)
        CoroutineScope(SupervisorJob() + Dispatchers.IO).launch {
            runCatching {
                ApiProvider.initialize(applicationContext)
                if (SessionManager.current(applicationContext) != null) {
                    ApiProvider.unwrap(
                        ApiProvider.api.registerDevice(
                            com.candyland.mobile.model.DeviceTokenRequest(
                                token = token,
                                platform = "ANDROID",
                                device_id = android.provider.Settings.Secure.getString(
                                    contentResolver,
                                    android.provider.Settings.Secure.ANDROID_ID
                                )
                            )
                        )
                    )
                }
            }
        }
    }

    override fun onMessageReceived(message: RemoteMessage) {
        super.onMessageReceived(message)
        val title = message.notification?.title ?: "CandyLand"
        val body = message.notification?.body ?: "Seu pedido recebeu uma atualização."
        mostrarNotificacao(title, body, message.data["order_id"])
    }

    private fun mostrarNotificacao(title: String, body: String, orderId: String?) {
        val channelId = "candyland_orders"
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                channelId,
                "Atualizações de pedidos",
                NotificationManager.IMPORTANCE_HIGH
            ).apply { description = "Notificações sobre pedidos e entregas do CandyLand." }
            getSystemService(NotificationManager::class.java).createNotificationChannel(channel)
        }

        val intent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_SINGLE_TOP
            orderId?.let { putExtra("order_id", it) }
        }
        val pendingIntent = PendingIntent.getActivity(
            this,
            orderId?.hashCode() ?: 0,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        val notification = NotificationCompat.Builder(this, channelId)
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentTitle(title)
            .setContentText(body)
            .setStyle(NotificationCompat.BigTextStyle().bigText(body))
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setAutoCancel(true)
            .setContentIntent(pendingIntent)
            .build()
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU ||
            androidx.core.content.ContextCompat.checkSelfPermission(
                this,
                android.Manifest.permission.POST_NOTIFICATIONS
            ) == android.content.pm.PackageManager.PERMISSION_GRANTED
        ) {
            runCatching {
                NotificationManagerCompat.from(this).notify(
                    orderId?.hashCode() ?: System.currentTimeMillis().toInt(),
                    notification
                )
            }
        }
    }
}
