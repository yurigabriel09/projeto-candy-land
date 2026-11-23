package com.candyland.mobile.data

import com.google.gson.Gson
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import java.util.concurrent.TimeUnit

data class ViaCepAddress(
    val cep: String? = null,
    val logradouro: String? = null,
    val complemento: String? = null,
    val bairro: String? = null,
    val localidade: String? = null,
    val uf: String? = null,
    val erro: Boolean = false
)

object ViaCepClient {
    private val http = OkHttpClient.Builder()
        .connectTimeout(6, TimeUnit.SECONDS)
        .readTimeout(6, TimeUnit.SECONDS)
        .callTimeout(8, TimeUnit.SECONDS)
        .build()

    suspend fun buscar(cep: String): ViaCepAddress = withContext(Dispatchers.IO) {
        val digits = cep.filter(Char::isDigit)
        require(digits.length == 8) { "Informe um CEP com oito números." }
        val request = Request.Builder().url("https://viacep.com.br/ws/$digits/json/").get().build()
        http.newCall(request).execute().use { response ->
            if (!response.isSuccessful) throw IllegalStateException("ViaCEP respondeu HTTP ${response.code}.")
            val body = response.body?.string().orEmpty()
            val result = Gson().fromJson(body, ViaCepAddress::class.java)
                ?: throw IllegalStateException("Resposta inválida do ViaCEP.")
            if (result.erro) throw IllegalArgumentException("CEP não encontrado. Confira os números.")
            result
        }
    }
}
