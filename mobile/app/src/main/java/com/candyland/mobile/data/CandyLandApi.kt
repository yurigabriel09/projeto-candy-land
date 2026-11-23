package com.candyland.mobile.data

import android.content.Context
import android.os.Handler
import android.os.Looper
import com.candyland.mobile.BuildConfig
import com.candyland.mobile.model.*
import com.google.gson.Gson
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Response
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.HTTP
import retrofit2.http.Header
import retrofit2.http.POST
import retrofit2.http.PATCH
import retrofit2.http.PUT
import retrofit2.http.Path
import retrofit2.http.Query

interface CandyLandApi {
    @POST("auth/login")
    suspend fun startAuthentication(@Body body: AuthStartRequest): Response<AuthStartResponse>

    @POST("auth/second-code")
    suspend fun requestSecondCode(@Body body: AuthSecondCodeRequest): Response<AuthStartResponse>

    @POST("auth/verify")
    suspend fun verifyCode(@Body body: AuthVerifyRequest): Response<AuthVerifyResponse>

    @POST("auth/google")
    suspend fun authenticateGoogle(@Body body: GoogleAuthRequest): Response<SocialAuthResponse>

    @POST("auth/facebook/complete")
    suspend fun completeFacebook(@Body body: FacebookCompleteRequest): Response<SocialAuthResponse>

    @POST("users")
    suspend fun registerUser(@Body body: UserRegistrationRequest): Response<UserRegistrationResponse>

    @GET("users/{userId}")
    suspend fun userProfile(@Path("userId") userId: Int): Response<UserProfileResponse>

    @PUT("users/{userId}")
    suspend fun updateUserProfile(@Path("userId") userId: Int, @Body body: UserProfileUpdateRequest): Response<Map<String, Any?>>

    @POST("users/{userId}/enderecos")
    suspend fun addUserAddress(@Path("userId") userId: Int, @Body body: AddressUpsertRequest): Response<Map<String, Any?>>

    @PUT("users/{userId}/enderecos/{addressId}")
    suspend fun updateUserAddress(@Path("userId") userId: Int, @Path("addressId") addressId: Int, @Body body: AddressUpsertRequest): Response<Map<String, Any?>>

    @DELETE("users/{userId}/enderecos/{addressId}")
    suspend fun deleteUserAddress(@Path("userId") userId: Int, @Path("addressId") addressId: Int): Response<Map<String, Any?>>

    @GET("restaurantes")
    suspend fun restaurants(): Response<RestaurantListResponse>

    @GET("produtos/busca")
    suspend fun searchProducts(@Query("q") query: String): Response<ProductSearchResponse>

    @GET("restaurantes/{restaurantId}/produtos")
    suspend fun products(@Path("restaurantId") restaurantId: Int): Response<ProductListResponse>

    @GET("restaurantes/{restaurantId}/configuracao")
    suspend fun restaurantConfiguration(@Path("restaurantId") restaurantId: Int): Response<RestaurantConfigurationResponse>

    @PUT("restaurantes/{restaurantId}/configuracao")
    suspend fun updateRestaurantConfiguration(@Path("restaurantId") restaurantId: Int, @Body body: RestaurantConfigurationUpdateRequest): Response<RestaurantConfigurationResponse>

    @PATCH("restaurantes/{restaurantId}/status")
    suspend fun updateRestaurantStatus(@Path("restaurantId") restaurantId: Int, @Body body: RestaurantStatusRequest): Response<Map<String, Any?>>

    @GET("restaurantes/{restaurantId}/produtos/gerenciamento")
    suspend fun managedProducts(@Path("restaurantId") restaurantId: Int): Response<ProductListResponse>

    @GET("categorias")
    suspend fun categories(): Response<CategoryListResponse>

    @POST("categorias")
    suspend fun createCategory(@Body body: CategoryCreateRequest): Response<CategoryMutationResponse>

    @POST("produtos")
    suspend fun createProduct(@Body body: ProductUpsertRequest): Response<ProductMutationResponse>

    @PUT("produtos/{productId}")
    suspend fun updateProduct(@Path("productId") productId: Int, @Body body: ProductUpsertRequest): Response<ProductMutationResponse>

    @GET("users/{userId}/enderecos")
    suspend fun addresses(@Path("userId") userId: Int): Response<AddressListResponse>

    @POST("users/{userId}/enderecos/{addressId}/geocodificar")
    suspend fun geocodeAddress(
        @Path("userId") userId: Int,
        @Path("addressId") addressId: Int
    ): Response<Map<String, Any>>

    @POST("pedidos")
    suspend fun createOrder(@Body body: CreateOrderRequest): Response<CreateOrderResponse>

    @POST("pedidos/{orderId}/pagamento")
    suspend fun createPayment(
        @Path("orderId") orderId: Int,
        @Header("Idempotency-Key") idempotencyKey: String,
        @Header("X-Client-Platform") clientPlatform: String
    ): Response<PaymentCreateResponse>

    @GET("pedidos/{orderId}")
    suspend fun order(@Path("orderId") orderId: Int): Response<OrderDetailResponse>

    @POST("pedidos/{orderId}/cancelar")
    suspend fun cancelOrder(@Path("orderId") orderId: Int): Response<Map<String, Any?>>

    @GET("pedidos/{orderId}/pagamento")
    suspend fun getPayment(@Path("orderId") orderId: Int): Response<PaymentCreateResponse>

    @POST("pedidos/{orderId}/pagamento/paypal-capture")
    suspend fun capturePayPalPayment(
        @Path("orderId") orderId: Int,
        @Body body: PayPalOrderActionRequest
    ): Response<PaymentActionResponse>

    @POST("pedidos/{orderId}/pagamento/paypal-cancel")
    suspend fun cancelPayPalPayment(
        @Path("orderId") orderId: Int,
        @Body body: PayPalOrderActionRequest
    ): Response<PaymentActionResponse>

    @POST("pedidos/{orderId}/codigo-recebimento")
    suspend fun generateReceiptCode(@Path("orderId") orderId: Int): Response<ReceiptCodeResponse>

    @GET("pedidos")
    suspend fun orders(): Response<OrderListResponse>

    @PUT("pedidos/{orderId}/status")
    suspend fun updateOrderStatus(@Path("orderId") orderId: Int, @Body body: OrderStatusRequest): Response<Map<String, Any?>>

    @PUT("pedidos/{orderId}/entrega/status")
    suspend fun updateDeliveryStatus(@Path("orderId") orderId: Int, @Body body: OrderStatusRequest): Response<Map<String, Any?>>

    @POST("pedidos/{orderId}/codigo-recebimento")
    suspend fun issueReceiptCode(@Path("orderId") orderId: Int): Response<ReceiptCodeResponse>

    @POST("pedidos/{orderId}/confirmar-recebimento")
    suspend fun confirmReceipt(@Path("orderId") orderId: Int, @Body body: ReceiptCodeRequest): Response<Map<String, Any?>>

    @POST("devices/fcm")
    suspend fun registerDevice(@Body body: DeviceTokenRequest): Response<Map<String, Any>>

    @HTTP(method = "DELETE", path = "devices/fcm", hasBody = true)
    suspend fun removeDevice(@Body body: DeviceTokenRequest): Response<Map<String, Any>>
}

object ApiProvider {
    lateinit var api: CandyLandApi
        private set

    @Volatile var sessionExpiredHandler: (() -> Unit)? = null

    fun initialize(context: Context) {
        if (::api.isInitialized) return
        val logging = HttpLoggingInterceptor().apply {
            level = if (BuildConfig.DEBUG) HttpLoggingInterceptor.Level.BASIC
            else HttpLoggingInterceptor.Level.NONE
        }
        val client = OkHttpClient.Builder()
            .addInterceptor { chain ->
                val token = SessionManager.token(context)
                val request = chain.request().newBuilder()
                token?.let { request.header("Authorization", "Bearer $it") }
                val response = chain.proceed(request.build())
                if (response.code == 401 && !token.isNullOrBlank()) {
                    SessionManager.clear(context)
                    Handler(Looper.getMainLooper()).post { sessionExpiredHandler?.invoke() }
                }
                response
            }
            .addInterceptor(logging)
            .build()
        api = Retrofit.Builder()
            .baseUrl(BuildConfig.API_BASE_URL)
            .client(client)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(CandyLandApi::class.java)
    }

    suspend fun <T> unwrap(response: Response<T>): T {
        if (response.isSuccessful) {
            return response.body() ?: throw ApiException("O servidor retornou uma resposta vazia.")
        }
        val raw = response.errorBody()?.string()
        val serverMessage = runCatching { Gson().fromJson(raw, ApiError::class.java)?.erro }.getOrNull()
        throw ApiException(serverMessage ?: "Falha na comunicação com o CandyLand (${response.code()}).")
    }
}

class ApiException(message: String) : Exception(message)
