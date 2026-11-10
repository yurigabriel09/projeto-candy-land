package com.candyland.mobile.push

import android.content.Context
import com.candyland.mobile.data.ApiProvider
import com.candyland.mobile.data.SessionManager
import com.candyland.mobile.model.DeviceTokenRequest
import com.google.firebase.FirebaseApp
import com.google.firebase.messaging.FirebaseMessaging
import kotlinx.coroutines.tasks.await
import kotlinx.coroutines.withContext
import kotlinx.coroutines.Dispatchers

object PushTokenManager {
    suspend fun registerCurrentDevice(context: Context) {
        SessionManager.current(context) ?: return
        if (FirebaseApp.getApps(context).isEmpty()) return
        val token = withContext(Dispatchers.IO) { FirebaseMessaging.getInstance().token.await() }
        ApiProvider.unwrap(
            ApiProvider.api.registerDevice(
                DeviceTokenRequest(token = token, platform = "ANDROID", device_id = androidId(context))
            )
        )
    }

    suspend fun unregisterCurrentDevice(context: Context) {
        SessionManager.current(context) ?: return
        if (FirebaseApp.getApps(context).isEmpty()) return
        val token = withContext(Dispatchers.IO) { FirebaseMessaging.getInstance().token.await() }
        ApiProvider.unwrap(
            ApiProvider.api.removeDevice(
                DeviceTokenRequest(token = token, platform = "ANDROID", device_id = androidId(context))
            )
        )
    }

    private fun androidId(context: Context): String? =
        android.provider.Settings.Secure.getString(context.contentResolver, android.provider.Settings.Secure.ANDROID_ID)
}
