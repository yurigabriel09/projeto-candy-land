package com.candyland.mobile.data

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import com.google.gson.Gson
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

private const val PREFS = "candyland_mobile_session"
private const val SESSION_KEY = "encrypted_session"
private const val KEY_ALIAS = "candyland_mobile_session_aes"
private const val ANDROID_KEYSTORE = "AndroidKeyStore"

object SessionManager {
    data class Session(
        val id: Int,
        val accountType: String,
        val token: String,
        val name: String,
        val email: String
    )

    private fun prefs(context: Context) =
        context.applicationContext.getSharedPreferences(PREFS, Context.MODE_PRIVATE)

    private fun key(): SecretKey {
        val keyStore = KeyStore.getInstance(ANDROID_KEYSTORE).apply { load(null) }
        val existing = keyStore.getKey(KEY_ALIAS, null) as? SecretKey
        if (existing != null) return existing

        val generator = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, ANDROID_KEYSTORE)
        generator.init(
            KeyGenParameterSpec.Builder(
                KEY_ALIAS,
                KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT
            )
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setRandomizedEncryptionRequired(true)
                .build()
        )
        return generator.generateKey()
    }

    private fun encrypt(plainText: String): String {
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.ENCRYPT_MODE, key())
        val encrypted = cipher.doFinal(plainText.toByteArray(Charsets.UTF_8))
        val payload = cipher.iv + encrypted
        return Base64.encodeToString(payload, Base64.NO_WRAP)
    }

    private fun decrypt(payload: String): String {
        val bytes = Base64.decode(payload, Base64.NO_WRAP)
        require(bytes.size > 12) { "Sessão criptografada inválida." }
        val iv = bytes.copyOfRange(0, 12)
        val encrypted = bytes.copyOfRange(12, bytes.size)
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.DECRYPT_MODE, key(), GCMParameterSpec(128, iv))
        return String(cipher.doFinal(encrypted), Charsets.UTF_8)
    }

    fun current(context: Context): Session? {
        val payload = prefs(context).getString(SESSION_KEY, null) ?: return null
        return runCatching { Gson().fromJson(decrypt(payload), Session::class.java) }
            .getOrNull()
            ?.takeIf { it.id > 0 && it.token.isNotBlank() && it.accountType == "PERSONAL" }
            ?: run { clear(context); null }
    }

    fun save(context: Context, session: Session) {
        require(session.id > 0 && session.token.isNotBlank()) { "Sessão inválida." }
        val encrypted = encrypt(Gson().toJson(session))
        prefs(context).edit().putString(SESSION_KEY, encrypted).apply()
    }

    fun clear(context: Context) {
        prefs(context).edit().clear().apply()
    }

    fun token(context: Context): String? = current(context)?.token
}
