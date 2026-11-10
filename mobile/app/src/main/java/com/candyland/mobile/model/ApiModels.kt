package com.candyland.mobile.model

import com.google.gson.annotations.SerializedName

// Authentication API already exposed by the Flask backend.
data class AuthStartRequest(val canal: String, val valor: String)
data class AuthStartResponse(
    val success: Boolean = false,
    val mensagem: String? = null,
    val tentativa_id: String? = null,
    val proximo_canal: String? = null
)
data class AuthSecondCodeRequest(val tentativa_id: String, val valor: String)
data class AuthVerifyRequest(val tentativa_id: String, val codigo: String)
data class GoogleAuthRequest(val credential: String, val telefone: String? = null)
data class FacebookCompleteRequest(val ticket: String, val telefone: String? = null)
data class SocialAuthResponse(
    val success: Boolean = false,
    val mensagem: String? = null,
    val tentativa_id: String? = null,
    val proximo_canal: String? = null,
    val novo_cadastro: Boolean = false,
    val precisa_telefone: Boolean = false,
    val email: String? = null,
    val telefone: String? = null,
    val erro: String? = null
)
data class AuthVerifyResponse(
    val success: Boolean = false,
    val mensagem: String? = null,
    val proximo_canal: String? = null,
    val tentativa_id: String? = null,
    val dados: AuthFinalData? = null
)
data class AuthFinalData(
    val tipo_conta: String? = null,
    val id: Int? = null,
    val token: String? = null,
    val email: String? = null,
    val telefone: String? = null,
    val nome_completo: String? = null,
    val nome: String? = null,
    val novo_cadastro: Boolean = false,
    val tentativa_id: String? = null
)

data class UserRegistrationRequest(
    val nome_completo: String,
    val email: String,
    val telefone: String,
    val cpf: String,
    val tentativa_id: String,
    val data_nascimento: String?,
    val endereco: AddressRegistration
)
data class AddressRegistration(
    val cep: String,
    val rua: String,
    val numero: String,
    val complemento: String?,
    val bairro: String,
    val cidade: String,
    val estado: String,
    val referencia: String? = null
)
data class UserRegistrationResponse(val dados: RegisteredUserData? = null)
data class RegisteredUserData(
    val usuario: UserSummary? = null,
    val endereco: AddressDto? = null,
    val token: String? = null
)
data class UserSummary(
    val id: Int = 0,
    val nome_completo: String? = null,
    val email: String? = null,
    val telefone: String? = null
)

data class RestaurantDto(
    val id: Int = 0,
    val nome: String = "Doceria",
    val descricao: String? = null,
    val status: String? = null,
    val ativo: Boolean = true,
    val horario_funcionamento: String? = null,
    val valor_minimo_pedido: Double? = null
)
data class RestaurantListResponse(val dados: List<RestaurantDto> = emptyList())

data class ProductDto(
    @SerializedName("id_produto") val id: Int = 0,
    @SerializedName("id_restaurante") val restaurantId: Int = 0,
    @SerializedName("id_categoria") val categoryId: Int = 0,
    @SerializedName("nome_produto") val name: String = "Produto",
    @SerializedName("descricao_produto") val description: String? = null,
    @SerializedName("preco_produto") val price: Double = 0.0,
    @SerializedName("produto_disponivel") val available: Boolean = true,
    @SerializedName("produto_importado") val imported: Boolean = false,
    @SerializedName("permite_personalizacao") val allowsCustomization: Boolean = false,
    @SerializedName("imagem_url") val imageUrl: String? = null
)
data class ProductListResponse(val dados: List<ProductDto> = emptyList())

data class AddressDto(
    val id: Int = 0,
    val cep: String? = null,
    val rua: String? = null,
    val numero: String? = null,
    val complemento: String? = null,
    val bairro: String? = null,
    val cidade: String? = null,
    val estado: String? = null,
    val latitude: Double? = null,
    val longitude: Double? = null,
    val principal: Boolean = false
) {
    fun label(): String = listOfNotNull(
        listOfNotNull(rua, numero).joinToString(", ").takeIf { it.isNotBlank() },
        bairro,
        listOfNotNull(cidade, estado).joinToString(" - ").takeIf { it.isNotBlank() }
    ).joinToString(" · ")
}
data class AddressListResponse(val dados: List<AddressDto> = emptyList())

data class OrderItemRequest(val produto_id: Int, val quantidade: Int)
data class CreateOrderRequest(
    val restaurant_id: Int,
    val order_type: String,
    val payment_method: String,
    val items: List<OrderItemRequest>,
    val delivery_address_id: Int? = null,
    val pickup_address_id: Int? = null
)
data class CreateOrderResponse(val pedido: OrderDto? = null)
data class OrderListResponse(val pedidos: List<OrderDto> = emptyList())
data class OrderDto(
    val id: Int = 0,
    val order_code: String = "",
    val restaurant_name: String? = null,
    val status: String = "",
    val order_type: String = "",
    val total: Double = 0.0,
    val created_at: String? = null,
    val items: List<OrderItemDto> = emptyList()
)
data class OrderItemDto(
    @SerializedName("produto_id") val productId: Int = 0,
    @SerializedName("nome_produto") val productName: String? = null,
    val quantidade: Int = 0,
    val preco_unitario: Double = 0.0
)
data class PaymentCreateResponse(val pagamento: PaymentDto? = null)
data class PaymentDto(
    val status: String? = null,
    val approval_url: String? = null,
    val pix_copy_paste: String? = null,
    val pix_qr_code_base64: String? = null,
    val message: String? = null
)
data class DeviceTokenRequest(
    val token: String,
    val platform: String = "ANDROID",
    val device_id: String? = null
)
data class ApiError(val erro: String? = null, val mensagem: String? = null)
