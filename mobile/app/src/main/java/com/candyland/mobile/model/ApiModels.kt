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
    val erro: String? = null,
    // Contas existentes podem concluir o login social sem abrir uma nova tentativa OTP.
    val dados: AuthFinalData? = null
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
    val valor_minimo_pedido: Double? = null,
    val taxa_entrega_base: Double? = null,
    val taxa_entrega_por_km: Double? = null,
    val raio_entrega_km: Double? = null,
    val latitude: Double? = null,
    val longitude: Double? = null
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
    @SerializedName("qtd_estoque") val stock: Int = 0,
    @SerializedName("produto_importado") val imported: Boolean = false,
    @SerializedName("permite_personalizacao") val allowsCustomization: Boolean = false,
    @SerializedName("imagem_url") val imageUrl: String? = null
)
data class ProductListResponse(val dados: List<ProductDto> = emptyList())
data class ProductSearchResponse(val dados: List<ProductDto> = emptyList())
data class ProductUpsertRequest(
    val categoria_id: Int,
    val nome: String,
    val descricao: String? = null,
    val preco: Double,
    val qtd_estoque: Int = 0,
    val disponivel: Boolean = true,
    val importado: Boolean = false,
    val permite_customizacao: Boolean = false
)
data class ProductMutationResponse(val produto: ProductDto? = null, val mensagem: String? = null)
data class CategoryDto(
    val id: Int = 0,
    val nome: String = "",
    val ativa: Boolean = true,
    val ordem_exibicao: Int = 0
)
data class CategoryListResponse(val categorias: List<CategoryDto> = emptyList())
data class CategoryCreateRequest(val nome: String, val ativa: Boolean = true)
data class CategoryMutationResponse(val categoria: CategoryDto? = null, val mensagem: String? = null)

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
    val principal: Boolean = false,
    val referencia: String? = null,
    val ativo: Boolean = true
) {
    fun label(): String = listOfNotNull(
        listOfNotNull(rua, numero).joinToString(", ").takeIf { it.isNotBlank() },
        bairro,
        listOfNotNull(cidade, estado).joinToString(" - ").takeIf { it.isNotBlank() }
    ).joinToString(" · ")
}
data class AddressListResponse(val dados: List<AddressDto> = emptyList())

data class UserProfileResponse(val dados: UserProfileDto? = null)
data class UserProfileDto(
    val id: Int = 0,
    val nome_completo: String = "",
    val email: String = "",
    val telefone: String = "",
    val cpf: String = "",
    val data_nascimento: String? = null,
    val foto_perfil_url: String? = null
)
data class UserProfileUpdateRequest(
    val nome_completo: String,
    val data_nascimento: String? = null
)
data class AddressUpsertRequest(
    val cep: String,
    val rua: String,
    val numero: String,
    val complemento: String? = null,
    val bairro: String,
    val cidade: String,
    val estado: String,
    val referencia: String? = null,
    val principal: Boolean = false
)
data class RestaurantConfigurationResponse(val dados: RestaurantConfigurationData? = null)
data class RestaurantConfigurationData(
    val restaurante: RestaurantProfileDto? = null,
    val endereco: AddressDto? = null
)
data class RestaurantProfileDto(
    val id: Int = 0,
    val nome: String = "",
    val razao_social: String = "",
    val nome_responsavel: String? = null,
    val cnpj: String = "",
    val cpf_responsavel: String = "",
    val email: String = "",
    val telefone: String = "",
    val descricao: String? = null,
    val valor_minimo_pedido: Double? = null,
    val taxa_entrega_base: Double? = null,
    val taxa_entrega_por_km: Double? = null,
    val raio_entrega_km: Double? = null,
    val horario_funcionamento: String? = null,
    val status: String = "EM_ANALISE",
    val ativo: Boolean = true
)
data class RestaurantAddressUpdateRequest(
    val cep: String,
    val rua: String,
    val numero: String,
    val complemento: String? = null,
    val bairro: String,
    val cidade: String,
    val estado: String,
    val referencia: String? = null
)
data class RestaurantConfigurationUpdateRequest(
    val nome: String,
    val razao_social: String,
    val nome_responsavel: String? = null,
    val descricao: String? = null,
    val valor_minimo_pedido: Double = 0.0,
    val taxa_entrega_base: Double = 0.0,
    val taxa_entrega_por_km: Double = 0.0,
    val raio_entrega_km: Double? = null,
    val horario_funcionamento: String? = null,
    val endereco: RestaurantAddressUpdateRequest
)
data class RestaurantStatusRequest(val status: String)
data class OrderStatusRequest(val status: String)
data class ReceiptCodeRequest(val codigo: String)
data class ReceiptCodeResponse(
    val codigo: String? = null,
    val mensagem: String? = null,
    val pedido_id: Int? = null,
    val tentativas_restantes: Int? = null
)

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
data class OrderDetailResponse(val pedido: OrderDto? = null)
data class OrderDto(
    val id: Int = 0,
    val order_code: String = "",
    val restaurant_name: String? = null,
    val restaurant_id: Int = 0,
    val delivery_address_id: Int? = null,
    val pickup_address_id: Int? = null,
    val payment_method: String? = null,
    val status: String = "",
    val order_type: String = "",
    val subtotal: Double = 0.0,
    val discount: Double = 0.0,
    val delivery_fee: Double = 0.0,
    val delivery_distance_km: Double? = null,
    val total: Double = 0.0,
    val delivery_quote: DeliveryQuoteDto? = null,
    val created_at: String? = null,
    val items: List<OrderItemDto> = emptyList(),
    val entrega: DeliveryDto? = null
)
data class DeliveryQuoteDto(
    val distance_km: Double? = null,
    val duration_seconds: Int? = null,
    val source: String? = null,
    val tempo_estimado: DeliveryEtaDto? = null
)
data class DeliveryEtaDto(val minimo: Int = 0, val maximo: Int = 0)
data class DeliveryDto(
    val id: Int? = null,
    val status: String? = null,
    val iniciado_em: String? = null,
    val concluida_em: String? = null,
    val cancelada_em: String? = null
)
data class OrderItemDto(
    @SerializedName("produto_id") val productId: Int = 0,
    @SerializedName("nome_produto") val productName: String? = null,
    val quantidade: Int = 0,
    val preco_unitario: Double = 0.0
)
data class PaymentCreateResponse(val pagamento: PaymentDto? = null)
data class PaymentActionResponse(
    val pagamento: PaymentDto? = null,
    val pedido: OrderDto? = null
)
data class PayPalOrderActionRequest(val token: String)
data class PaymentDto(
    val status: String? = null,
    val approval_url: String? = null,
    val pix_copy_paste: String? = null,
    val pix_qr_code_base64: String? = null,
    val message: String? = null,
    val payment_method: String? = null
)
data class DeviceTokenRequest(
    val token: String,
    val platform: String = "ANDROID",
    val device_id: String? = null
)
data class ApiError(val erro: String? = null, val mensagem: String? = null)
