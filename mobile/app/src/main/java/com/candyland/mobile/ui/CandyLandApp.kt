package com.candyland.mobile.ui

import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.safeDrawingPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Divider
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.draw.clip
import androidx.compose.ui.unit.sp
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.ui.unit.dp
import androidx.credentials.CredentialManager
import androidx.credentials.CustomCredential
import androidx.credentials.GetCredentialRequest
import com.google.android.libraries.identity.googleid.GetSignInWithGoogleOption
import com.google.android.libraries.identity.googleid.GoogleIdTokenCredential
import com.candyland.mobile.BuildConfig
import com.candyland.mobile.data.ApiProvider
import com.candyland.mobile.data.CartStorage
import com.candyland.mobile.data.StoredCartItem
import com.candyland.mobile.data.SessionManager
import com.candyland.mobile.model.*
import com.candyland.mobile.push.PushTokenManager
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.launch
import java.util.UUID
import java.text.NumberFormat
import java.util.Locale

private inline fun <T> runCancellableCatching(block: () -> T): Result<T> {
    return try {
        Result.success(block())
    } catch (e: CancellationException) {
        throw e
    } catch (e: Throwable) {
        Result.failure(e)
    }
}

private data class RegistrationInfo(val attemptId: String, val email: String, val phone: String)
private data class CartEntry(val product: ProductDto, val quantity: Int)

private val RECEIPT_CODE_ELIGIBLE_STATUSES = setOf(
    "PAGAMENTO_CONFIRMADO", "RESTAURANTE_RECEBEU", "RESTAURANTE_ACEITOU",
    "PROCESSANDO", "PRONTO_PARA_ENTREGA", "ENTREGUE"
)

@Composable
fun CandyLandApp(
    applicationContext: Context,
    oauthUri: Uri? = null,
    onOAuthUriConsumed: () -> Unit = {},
    paymentUri: Uri? = null,
    onPaymentUriConsumed: () -> Unit = {}
) {
    val appScope = rememberCoroutineScope()
    var session by remember { mutableStateOf(SessionManager.current(applicationContext)) }
    var showAuthentication by remember { mutableStateOf(oauthUri != null) }
    var cart by remember { mutableStateOf(CartStorage.load(applicationContext)) }
    var checkoutAfterLogin by remember { mutableStateOf(false) }

    SideEffect {
        ApiProvider.sessionExpiredHandler = {
            SessionManager.clear(applicationContext)
            session = null
            showAuthentication = false
            checkoutAfterLogin = false
        }
    }

    LaunchedEffect(oauthUri) {
        if (oauthUri != null) showAuthentication = true
    }

    MaterialTheme(
        colorScheme = MaterialTheme.colorScheme.copy(
            primary = Color(0xFFF4356E),
            onPrimary = Color.White,
            primaryContainer = Color(0xFFFFDDE7),
            onPrimaryContainer = Color(0xFF4A1F1D),
            secondary = Color(0xFFFF7043),
            onSecondary = Color.White,
            secondaryContainer = Color(0xFFFFE0D5),
            onSecondaryContainer = Color(0xFF4A2420),
            tertiary = Color(0xFF9C287B),
            background = Color(0xFFFFF1E8),
            surface = Color(0xFFFFFBF8),
            surfaceVariant = Color(0xFFFFE7DE),
            outline = Color(0xFFF2CDBD),
            onSurface = Color(0xFF4A2420),
            onSurfaceVariant = Color(0xFF8D6C63),
            onBackground = Color(0xFF4A2420)
        )
    ) {
        Surface(modifier = Modifier.fillMaxSize().safeDrawingPadding(), color = MaterialTheme.colorScheme.background) {
            if (session == null) {
                if (showAuthentication) {
                    AuthenticationScreen(
                        oauthUri = oauthUri,
                        onOAuthUriConsumed = onOAuthUriConsumed,
                        onBack = { showAuthentication = false },
                        onAuthenticated = { newSession ->
                            SessionManager.save(applicationContext, newSession)
                            session = newSession
                            showAuthentication = false
                        }
                    )
                } else {
                    WelcomeScreen(
                        cart = cart,
                        onCartChanged = { updated ->
                            cart = updated
                            CartStorage.save(applicationContext, updated)
                        },
                        onLogin = { checkoutAfterLogin = false; showAuthentication = true },
                        onCheckout = { checkoutAfterLogin = true; showAuthentication = true }
                    )
                }
            } else {
                val authenticatedSession = session!!
                val logout: () -> Unit = {
                    appScope.launch {
                        runCatching { PushTokenManager.unregisterCurrentDevice(applicationContext) }
                        SessionManager.clear(applicationContext)
                        session = null
                        showAuthentication = false
                        checkoutAfterLogin = false
                    }
                }
                if (authenticatedSession.accountType == "BUSINESS") {
                    BusinessSellerScreen(session = authenticatedSession, onLogout = logout)
                } else {
                    ShopScreen(
                        session = authenticatedSession,
                        onLogout = logout,
                        onSessionUpdated = { updated ->
                            SessionManager.save(applicationContext, updated)
                            session = updated
                        },
                        paymentUri = paymentUri,
                        onPaymentUriConsumed = onPaymentUriConsumed,
                        initialCart = cart,
                        onCartChanged = { updated ->
                            cart = updated
                            CartStorage.save(applicationContext, updated)
                        },
                        startInCart = checkoutAfterLogin
                    )
                }
            }
        }
    }
}

@Composable
private fun WelcomeScreen(
    cart: List<StoredCartItem>,
    onCartChanged: (List<StoredCartItem>) -> Unit,
    onLogin: () -> Unit,
    onCheckout: () -> Unit,
    profilePhotoUrl: String? = null
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var restaurants by remember { mutableStateOf<List<RestaurantDto>>(emptyList()) }
    var products by remember { mutableStateOf<List<ProductDto>>(emptyList()) }
    var loading by remember { mutableStateOf(true) }
    var searching by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    var query by remember { mutableStateOf("") }
    var selectedRestaurant by remember { mutableStateOf<RestaurantDto?>(null) }
    var storeProducts by remember { mutableStateOf<List<ProductDto>>(emptyList()) }
    var cartVisible by remember { mutableStateOf(false) }
    var currentLocation by remember { mutableStateOf<Pair<Double, Double>?>(null) }
    var locationLoading by remember { mutableStateOf(false) }
    var locationMessage by remember { mutableStateOf("Use sua localização para ver docerias próximas.") }

    fun atualizarLocalizacao() {
        val hasFine = androidx.core.content.ContextCompat.checkSelfPermission(
            context, android.Manifest.permission.ACCESS_FINE_LOCATION
        ) == android.content.pm.PackageManager.PERMISSION_GRANTED
        val hasCoarse = androidx.core.content.ContextCompat.checkSelfPermission(
            context, android.Manifest.permission.ACCESS_COARSE_LOCATION
        ) == android.content.pm.PackageManager.PERMISSION_GRANTED
        if (!hasFine && !hasCoarse) {
            locationMessage = "Autorize o acesso à localização para continuar."
            return
        }

        locationLoading = true
        locationMessage = "Obtendo sua localização..."
        val client = com.google.android.gms.location.LocationServices.getFusedLocationProviderClient(context)
        fun aplicarLocalizacao(location: android.location.Location?) {
            locationLoading = false
            if (location != null) {
                currentLocation = location.latitude to location.longitude
                locationMessage = "Localização atualizada. Distâncias aproximadas em linha reta."
            } else {
                locationMessage = "Não recebemos uma posição do dispositivo. No emulador, abra os controles (⋮) > Location e defina uma localização."
            }
        }
        client.getCurrentLocation(
            com.google.android.gms.location.Priority.PRIORITY_BALANCED_POWER_ACCURACY,
            com.google.android.gms.tasks.CancellationTokenSource().token
        ).addOnSuccessListener { location ->
            if (location != null) {
                aplicarLocalizacao(location)
            } else {
                client.lastLocation
                    .addOnSuccessListener { lastLocation -> aplicarLocalizacao(lastLocation) }
                    .addOnFailureListener { aplicarLocalizacao(null) }
            }
        }.addOnFailureListener {
            aplicarLocalizacao(null)
        }
    }

    val locationPermissionLauncher = androidx.activity.compose.rememberLauncherForActivityResult(
        androidx.activity.result.contract.ActivityResultContracts.RequestMultiplePermissions()
    ) { permissions ->
        if (permissions.values.any { it }) atualizarLocalizacao()
        else locationMessage = "Permissão de localização não concedida. Você pode continuar sem ela."
    }

    fun adicionarAoCarrinho(product: ProductDto) {
        if (!product.available || product.restaurantId <= 0) return
        if (cart.isNotEmpty() && cart.first().product.restaurantId != product.restaurantId) {
            error = "O carrinho aceita produtos de uma doceria por vez. Finalize ou esvazie o carrinho atual primeiro."
            return
        }
        val existing = cart.firstOrNull { it.product.id == product.id }
        val updated = if (existing == null) cart + StoredCartItem(product, 1)
        else cart.map { if (it.product.id == product.id) it.copy(quantity = (it.quantity + 1).coerceAtMost(99)) else it }
        onCartChanged(updated)
        error = null
    }

    LaunchedEffect(Unit) {
        runCatching { ApiProvider.unwrap(ApiProvider.api.restaurants()) }
            .onSuccess { restaurants = it.dados.filter { store -> store.ativo && store.status != "SUSPENSO" } }
            .onFailure { error = it.message ?: "Não foi possível carregar as docerias." }
    }

    LaunchedEffect(query) {
        kotlinx.coroutines.delay(350)
        searching = true
        runCancellableCatching { ApiProvider.unwrap(ApiProvider.api.searchProducts(query.trim())) }
            .onSuccess { products = it.dados; if (error?.contains("pesquisar") == true) error = null }
            .onFailure { error = it.message ?: "Não foi possível pesquisar os produtos." }
        searching = false
        loading = false
    }

    fun distanciaAproximada(restaurant: RestaurantDto): Double? {
        val user = currentLocation ?: return null
        val lat = restaurant.latitude ?: return null
        val lng = restaurant.longitude ?: return null
        val earth = 6371.0088
        val dLat = Math.toRadians(lat - user.first)
        val dLng = Math.toRadians(lng - user.second)
        val a = kotlin.math.sin(dLat / 2).let { it * it } +
            kotlin.math.cos(Math.toRadians(user.first)) * kotlin.math.cos(Math.toRadians(lat)) *
            kotlin.math.sin(dLng / 2).let { it * it }
        return 2 * earth * kotlin.math.asin(kotlin.math.sqrt(a.coerceIn(0.0, 1.0)))
    }

    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Column(Modifier.weight(1f)) {
                Text("🍭 CandyLand", style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.ExtraBold, color = MaterialTheme.colorScheme.primary)
                Text("Doces de todos os mundos", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
            TextButton(onClick = onLogin) {
                if (!profilePhotoUrl.isNullOrBlank()) {
                    coil3.compose.AsyncImage(
                        model = mobileImageUrl(profilePhotoUrl), contentDescription = "Minha conta",
                        modifier = Modifier.size(38.dp).clip(androidx.compose.foundation.shape.CircleShape),
                        contentScale = androidx.compose.ui.layout.ContentScale.Crop
                    )
                } else Text("👤", fontSize = 25.sp)
            }
            TextButton(onClick = { cartVisible = !cartVisible; selectedRestaurant = null }) {
                Text("🛒 ${cart.sumOf { it.quantity }}")
            }
        }

        if (cartVisible) {
            Text("Seu carrinho", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
            if (cart.isEmpty()) Text("Seu carrinho está vazio. Explore produtos e adicione seus doces favoritos.")
            cart.forEach { entry ->
                Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                    androidx.compose.foundation.layout.Column(Modifier.weight(1f)) {
                        Text(entry.product.name, fontWeight = FontWeight.SemiBold)
                        Text("${entry.quantity} × ${money(entry.product.price)}", style = MaterialTheme.typography.bodySmall)
                    }
                    TextButton(onClick = {
                        val next = if (entry.quantity <= 1) cart.filterNot { it.product.id == entry.product.id }
                        else cart.map { if (it.product.id == entry.product.id) it.copy(quantity = it.quantity - 1) else it }
                        onCartChanged(next)
                    }) { Text("−") }
                    TextButton(onClick = { adicionarAoCarrinho(entry.product) }) { Text("+") }
                }
                Divider()
            }
            Text("Subtotal estimado: ${money(cart.sumOf { it.product.price * it.quantity })}", fontWeight = FontWeight.Bold)
            Text("Frete e prazo serão calculados pelo servidor antes de abrir o pagamento.", style = MaterialTheme.typography.bodySmall)
            Button(onClick = onCheckout, enabled = cart.isNotEmpty(), modifier = Modifier.fillMaxWidth()) {
                Text("Continuar para identificação e finalizar")
            }
            TextButton(onClick = { cartVisible = false }) { Text("Continuar comprando") }
        } else if (selectedRestaurant != null) {
            TextButton(onClick = { selectedRestaurant = null }) { Text("← Voltar ao catálogo") }
            Text(selectedRestaurant!!.nome, style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
            selectedRestaurant!!.descricao?.let { Text(it) }
            storeProducts.forEach { product ->
                Card(Modifier.fillMaxWidth()) {
                    Row(Modifier.padding(10.dp), verticalAlignment = Alignment.CenterVertically) {
                        coil3.compose.AsyncImage(
                            model = mobileImageUrl(product.imageUrl),
                            contentDescription = product.name,
                            modifier = Modifier.size(92.dp).clip(androidx.compose.foundation.shape.RoundedCornerShape(12.dp)),
                            contentScale = androidx.compose.ui.layout.ContentScale.Crop
                        )
                        Column(Modifier.weight(1f).padding(start = 10.dp)) {
                            Text(product.name, fontWeight = FontWeight.SemiBold)
                            product.description?.let { Text(it, style = MaterialTheme.typography.bodySmall, maxLines = 2) }
                            Text(money(product.price), color = MaterialTheme.colorScheme.primary, fontWeight = FontWeight.Bold)
                            Button(onClick = { adicionarAoCarrinho(product) }, enabled = product.available && selectedRestaurant!!.status == "ABERTO") { Text("Adicionar") }
                        }
                    }
                }
            }
        } else {
            androidx.compose.material3.OutlinedTextField(
                value = query,
                onValueChange = { query = it },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
                label = { Text("Buscar doces, produtos e docerias") },
                leadingIcon = { Text("⌕") }
            )
            androidx.compose.material3.OutlinedButton(
                enabled = !locationLoading,
                onClick = {
                    val hasLocation = androidx.core.content.ContextCompat.checkSelfPermission(context, android.Manifest.permission.ACCESS_FINE_LOCATION) == android.content.pm.PackageManager.PERMISSION_GRANTED ||
                        androidx.core.content.ContextCompat.checkSelfPermission(context, android.Manifest.permission.ACCESS_COARSE_LOCATION) == android.content.pm.PackageManager.PERMISSION_GRANTED
                    if (hasLocation) atualizarLocalizacao()
                    else locationPermissionLauncher.launch(arrayOf(android.Manifest.permission.ACCESS_FINE_LOCATION, android.Manifest.permission.ACCESS_COARSE_LOCATION))
                }, modifier = Modifier.fillMaxWidth()
            ) { Text(if (locationLoading) "Obtendo localização..." else "📍 ${if (currentLocation == null) "Usar minha localização" else "Atualizar localização"}") }
            Text(locationMessage, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)

            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(if (query.isBlank()) "Produtos para você 🍬" else "Resultados da pesquisa", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold, modifier = Modifier.weight(1f))
                if (searching || loading) CircularProgressIndicator(Modifier.size(18.dp), strokeWidth = 2.dp)
            }
            if (products.isEmpty() && !searching && !loading) Text("Nenhum produto encontrado. Tente outro termo.")
            products.forEach { product ->
                Card(Modifier.fillMaxWidth()) {
                    Row(Modifier.padding(10.dp), verticalAlignment = Alignment.CenterVertically) {
                        coil3.compose.AsyncImage(
                            model = mobileImageUrl(product.imageUrl),
                            contentDescription = product.name,
                            modifier = Modifier.size(92.dp).clip(androidx.compose.foundation.shape.RoundedCornerShape(12.dp)),
                            contentScale = androidx.compose.ui.layout.ContentScale.Crop
                        )
                        Column(Modifier.weight(1f).padding(start = 10.dp), verticalArrangement = Arrangement.spacedBy(3.dp)) {
                            Text(product.name, fontWeight = FontWeight.SemiBold)
                            product.description?.let { Text(it, style = MaterialTheme.typography.bodySmall, maxLines = 2) }
                            Text(money(product.price), color = MaterialTheme.colorScheme.primary, fontWeight = FontWeight.Bold)
                            Text(restaurants.firstOrNull { it.id == product.restaurantId }?.nome ?: "Doceria parceira", style = MaterialTheme.typography.labelSmall)
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                TextButton(onClick = {
                                    val store = restaurants.firstOrNull { it.id == product.restaurantId }
                                    if (store == null) error = "Doceria não encontrada. Atualize o catálogo."
                                    else {
                                        selectedRestaurant = store
                                        searching = true
                                        scope.launch {
                                            runCancellableCatching { ApiProvider.unwrap(ApiProvider.api.products(store.id)) }
                                                .onSuccess { storeProducts = it.dados }
                                                .onFailure { error = it.message ?: "Não foi possível abrir o cardápio." }
                                            searching = false
                                        }
                                    }
                                }) { Text("Ver loja") }
                                Button(onClick = { adicionarAoCarrinho(product) }, enabled = product.available) { Text("Adicionar") }
                            }
                        }
                    }
                }
            }

            Text("Docerias próximas 🍰", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
            restaurants.forEach { store ->
                val distance = distanciaAproximada(store)
                Card(onClick = {
                    selectedRestaurant = store
                    searching = true
                    scope.launch {
                        runCancellableCatching { ApiProvider.unwrap(ApiProvider.api.products(store.id)) }
                            .onSuccess { storeProducts = it.dados }
                            .onFailure { error = it.message ?: "Não foi possível abrir o cardápio." }
                        searching = false
                    }
                }, modifier = Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(3.dp)) {
                        Text(store.nome, fontWeight = FontWeight.SemiBold)
                        Text("Loja parceira CandyLand · ${mobileStoreStatusLabel(store.status)}", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.primary)
                        if (distance != null) {
                            val distanceLabel = "A ${"%.1f".format(java.util.Locale("pt", "BR"), distance)} km em linha reta"
                            val outsideRadius = store.raio_entrega_km?.let { distance > it } == true
                            if (outsideRadius) {
                                Text("$distanceLabel · fora do raio aproximado de entrega", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.error)
                            } else {
                                val min = kotlin.math.ceil((20 + distance / 25.0 * 60) / 5.0).toInt() * 5
                                val estimatedFee = (store.taxa_entrega_base ?: 0.0) + distance * (store.taxa_entrega_por_km ?: 0.0)
                                val feeText = if (estimatedFee <= 0.0) "Grátis" else "${money(estimatedFee)} aprox."
                                Text("$distanceLabel · ${min}–${min + 10} min · frete $feeText", style = MaterialTheme.typography.bodySmall)
                            }
                        } else Text("Distância e frete disponíveis após informar um endereço.", style = MaterialTheme.typography.bodySmall)
                    }
                }
            }
        }

        error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
    }
}

internal fun mobileImageUrl(path: String?): String? {
    val value = path?.trim()?.takeIf { it.isNotEmpty() } ?: return null
    if (value.startsWith("https://", ignoreCase = true) || value.startsWith("http://", ignoreCase = true)) return value

    // Uploads ficam na raiz do domínio; a API pode usar prefixo /api/.
    val apiUri = Uri.parse(BuildConfig.API_BASE_URL)
    val authority = apiUri.encodedAuthority ?: return null
    val origin = "${apiUri.scheme}://$authority"
    val normalized = value.trimStart('/')
    return if (value.startsWith("/") || normalized.startsWith("uploads/")) {
        "$origin/$normalized"
    } else {
        apiUri.buildUpon().appendEncodedPath(normalized).build().toString()
    }
}


@Composable
private fun AuthenticationScreen(
    oauthUri: Uri?,
    onOAuthUriConsumed: () -> Unit,
    onBack: () -> Unit,
    onAuthenticated: (SessionManager.Session) -> Unit
) {
    val scope = rememberCoroutineScope()
    val context = LocalContext.current
    val credentialManager = remember(context) { CredentialManager.create(context) }

    var identifier by remember { mutableStateOf("") }
    var firstChannel by remember { mutableStateOf("EMAIL") }
    var firstIdentifier by remember { mutableStateOf("") }
    var email by remember { mutableStateOf("") }
    var phone by remember { mutableStateOf("") }
    var secondValue by remember { mutableStateOf("") }
    var attemptId by remember { mutableStateOf("") }
    var code by remember { mutableStateOf("") }
    // 0: escolher e-mail/celular; 1: primeiro código; 2: informar segundo contato;
    // 3: segundo código; 4: informar celular do login social; 5: completar cadastro.
    var stage by remember { mutableStateOf(0) }
    var secondChannel by remember { mutableStateOf("WHATSAPP") }
    var registration by remember { mutableStateOf<RegistrationInfo?>(null) }
    var socialProvider by remember { mutableStateOf("") }
    var socialCredential by remember { mutableStateOf("") }
    var socialTicket by remember { mutableStateOf("") }
    var busy by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    var info by remember { mutableStateOf<String?>(null) }

    fun acceptAuth(data: AuthFinalData) {
        if (data.novo_cadastro) {
            val verifiedAttempt = data.tentativa_id ?: attemptId
            val verifiedEmail = data.email ?: email
            val verifiedPhone = data.telefone ?: phone
            if (verifiedAttempt.isBlank() || verifiedEmail.isBlank() || verifiedPhone.isBlank()) {
                error = "A autenticação foi validada, mas faltam dados para concluir o cadastro. Tente entrar por e-mail ou celular."
                return
            }
            registration = RegistrationInfo(verifiedAttempt, verifiedEmail, verifiedPhone)
            stage = 5
            return
        }

        val token = data.token
        val id = data.id
        if (token.isNullOrBlank() || id == null || data.tipo_conta.isNullOrBlank()) {
            error = "O servidor não retornou uma sessão válida."
            return
        }
        if (data.tipo_conta !in setOf("PERSONAL", "BUSINESS")) {
            error = "O tipo desta conta não é compatível com o aplicativo. Entre novamente ou use o portal web."
            return
        }
        onAuthenticated(
            SessionManager.Session(
                id = id,
                accountType = data.tipo_conta,
                token = token,
                name = data.nome_completo ?: data.nome ?: if (data.tipo_conta == "BUSINESS") "Parceiro" else "Cliente",
                email = data.email ?: email
            )
        )
    }

    fun continueSocialAuthentication(response: SocialAuthResponse) {
        // Login social de conta já existente retorna a sessão diretamente.
        response.dados?.let {
            acceptAuth(it)
            return
        }

        email = response.email ?: email
        phone = response.telefone ?: phone
        attemptId = response.tentativa_id.orEmpty()
        if (response.precisa_telefone) {
            stage = 4
            info = response.erro ?: "Informe seu celular com DDD para receber o código pelo WhatsApp."
            return
        }
        if (attemptId.isBlank()) {
            error = response.erro ?: "O provedor não iniciou a confirmação por WhatsApp."
            return
        }
        secondChannel = response.proximo_canal ?: "WHATSAPP"
        secondValue = response.telefone.orEmpty()
        code = ""
        stage = 3
        info = response.mensagem ?: "Enviamos um código para o seu WhatsApp."
    }

    LaunchedEffect(oauthUri) {
        val callbackUri = oauthUri ?: return@LaunchedEffect
        scope.launch {
            busy = true
            error = null
            val ticket = callbackUri.getQueryParameter("ticket")
            val oauthError = callbackUri.getQueryParameter("error")
            if (!oauthError.isNullOrBlank()) {
                error = oauthError
            } else if (!ticket.isNullOrBlank()) {
                socialProvider = "FACEBOOK"
                socialTicket = ticket
                runCancellableCatching {
                    ApiProvider.unwrap(ApiProvider.api.completeFacebook(FacebookCompleteRequest(ticket)))
                }.onSuccess { continueSocialAuthentication(it) }
                    .onFailure { error = it.message ?: "Não foi possível concluir o login com Facebook." }
            } else {
                error = "O Facebook retornou sem um código de autenticação. Inicie o acesso novamente."
            }
            busy = false
        }
        onOAuthUriConsumed()
    }

    
    fun startGoogleLogin() {
        if (BuildConfig.GOOGLE_WEB_CLIENT_ID.isBlank()) {
            error = "O login Google não está configurado. Confira CANDYLAND_GOOGLE_WEB_CLIENT_ID em mobile/local.properties."
            return
        }

        scope.launch {
            busy = true
            error = null
            info = null

            runCancellableCatching {
                // Fluxo próprio do botão "Continuar com Google".
                val googleOption = GetSignInWithGoogleOption.Builder(
                    BuildConfig.GOOGLE_WEB_CLIENT_ID
                ).build()

                val request = GetCredentialRequest.Builder()
                    .addCredentialOption(googleOption)
                    .build()

                val result = credentialManager.getCredential(context, request)
                val credential = result.credential

                if (
                    credential !is CustomCredential ||
                    credential.type != GoogleIdTokenCredential.TYPE_GOOGLE_ID_TOKEN_CREDENTIAL
                ) {
                    throw IllegalStateException(
                        "O Google não retornou uma credencial de identidade válida."
                    )
                }

                val idToken = GoogleIdTokenCredential
                    .createFrom(credential.data)
                    .idToken

                socialProvider = "GOOGLE"
                socialCredential = idToken

                ApiProvider.unwrap(
                    ApiProvider.api.authenticateGoogle(
                        GoogleAuthRequest(credential = idToken)
                    )
                )
            }.onSuccess { response ->
                continueSocialAuthentication(response)
            }.onFailure { cause ->
                error = cause.message ?: "Não foi possível entrar com o Google."
            }

            busy = false
        }
    }


    fun startFacebookLogin() {
        runCancellableCatching {
            val authUri = Uri.parse(BuildConfig.API_BASE_URL).buildUpon()
                .appendPath("auth")
                .appendPath("facebook")
                .appendQueryParameter("audiencia", "PERSONAL")
                .appendQueryParameter("platform", "ANDROID")
                .build()
            context.startActivity(Intent(Intent.ACTION_VIEW, authUri))
        }.onFailure { error = it.message ?: "Não foi possível abrir o login do Facebook." }
    }

    Column(
        modifier = Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(24.dp),
        verticalArrangement = Arrangement.Center
    ) {
        TextButton(onClick = onBack, enabled = !busy) { Text("← Voltar para início") }
        Text("CandyLand", style = MaterialTheme.typography.headlineLarge, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.primary)
        Text("Doces, pedidos e acompanhamento em um só lugar.", color = MaterialTheme.colorScheme.onSurfaceVariant)
        Spacer(Modifier.height(24.dp))

        when (stage) {
            0 -> {
                Text("Entre na sua conta", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.SemiBold)
                Spacer(Modifier.height(12.dp))
                Text("Escolha como deseja receber o primeiro código:", fontWeight = FontWeight.Medium)
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
                    if (firstChannel == "EMAIL") {
                        Button(onClick = { firstChannel = "EMAIL"; identifier = ""; error = null }) { Text("E-mail") }
                    } else {
                        OutlinedButton(onClick = { firstChannel = "EMAIL"; identifier = ""; error = null }) { Text("E-mail") }
                    }
                    if (firstChannel == "WHATSAPP") {
                        Button(onClick = { firstChannel = "WHATSAPP"; identifier = ""; error = null }) { Text("Celular") }
                    } else {
                        OutlinedButton(onClick = { firstChannel = "WHATSAPP"; identifier = ""; error = null }) { Text("Celular") }
                    }
                }
                OutlinedTextField(
                    value = identifier,
                    onValueChange = { identifier = it; error = null },
                    label = { Text(if (firstChannel == "EMAIL") "E-mail" else "Celular com DDD e país (+55)") },
                    placeholder = { Text(if (firstChannel == "EMAIL") "seu@email.com" else "+55 11 99999-9999") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                    keyboardOptions = KeyboardOptions(keyboardType = if (firstChannel == "EMAIL") KeyboardType.Email else KeyboardType.Phone)
                )
                Spacer(Modifier.height(10.dp))
                Button(
                    onClick = {
                        scope.launch {
                            busy = true; error = null; info = null
                            firstIdentifier = identifier.trim()
                            if (firstChannel == "EMAIL") email = firstIdentifier else phone = firstIdentifier
                            runCancellableCatching {
                                ApiProvider.unwrap(ApiProvider.api.startAuthentication(AuthStartRequest(firstChannel, firstIdentifier)))
                            }.onSuccess { response ->
                                attemptId = response.tentativa_id.orEmpty()
                                if (attemptId.isBlank()) error = "O servidor não criou a tentativa de autenticação."
                                else { stage = 1; info = response.mensagem ?: "Código enviado." }
                            }.onFailure { error = it.message ?: "Não foi possível iniciar o login." }
                            busy = false
                        }
                    },
                    enabled = !busy && identifier.isNotBlank(),
                    modifier = Modifier.fillMaxWidth()
                ) { if (busy) CircularProgressIndicator(Modifier.size(18.dp), strokeWidth = 2.dp) else Text("Enviar código") }

                Spacer(Modifier.height(20.dp))
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Divider(Modifier.weight(1f))
                    Text("  ou entre com  ", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    Divider(Modifier.weight(1f))
                }
                Spacer(Modifier.height(12.dp))
                OutlinedButton(onClick = { startGoogleLogin() }, enabled = !busy, modifier = Modifier.fillMaxWidth()) {
                    Text("G  Continuar com Google")
                }
                Spacer(Modifier.height(8.dp))
                OutlinedButton(onClick = { error = null; startFacebookLogin() }, enabled = !busy, modifier = Modifier.fillMaxWidth()) {
                    Text("f  Continuar com Facebook")
                }
                Spacer(Modifier.height(10.dp))
                Text(
                    "Para entrar em uma conta existente, basta confirmar o canal escolhido. Se ainda não tiver cadastro, vamos solicitar os dados de contato que faltarem.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
            1 -> {
                Text("Confirme o primeiro código", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.SemiBold)
                Text(if (firstChannel == "EMAIL") "Digite o código enviado ao e-mail $firstIdentifier." else "Digite o código enviado ao WhatsApp $firstIdentifier.")
                Spacer(Modifier.height(12.dp))
                OutlinedTextField(code, { code = it.filter(Char::isDigit).take(6); error = null }, label = { Text("Código de 6 dígitos") }, singleLine = true, modifier = Modifier.fillMaxWidth(), keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number))
                Button(
                    onClick = {
                        scope.launch {
                            busy = true; error = null; info = null
                            runCancellableCatching { ApiProvider.unwrap(ApiProvider.api.verifyCode(AuthVerifyRequest(attemptId, code))) }
                                .onSuccess { response ->
                                    if (response.dados != null) acceptAuth(response.dados)
                                    else {
                                        secondChannel = response.proximo_canal ?: if (firstChannel == "EMAIL") "WHATSAPP" else "EMAIL"
                                        secondValue = ""
                                        code = ""
                                        stage = 2
                                        info = "Primeiro contato confirmado. Agora informe o segundo contato para receber outro código."
                                    }
                                }.onFailure { error = it.message ?: "Não foi possível validar o código." }
                            busy = false
                        }
                    }, enabled = !busy && code.length == 6, modifier = Modifier.fillMaxWidth()
                ) { if (busy) CircularProgressIndicator(Modifier.size(18.dp), strokeWidth = 2.dp) else Text("Validar código") }
            }
            2 -> {
                val secondLabel = if (secondChannel == "EMAIL") "e-mail" else "celular"
                Text("Complete seus dados de contato", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.SemiBold)
                Text(info ?: "Como esta conta ainda não existe, informe seu $secondLabel para concluir o cadastro.")
                OutlinedTextField(
                    value = secondValue,
                    onValueChange = { secondValue = it; error = null },
                    label = { Text(if (secondChannel == "EMAIL") "E-mail" else "Celular com DDD e país (+55)") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                    keyboardOptions = KeyboardOptions(keyboardType = if (secondChannel == "EMAIL") KeyboardType.Email else KeyboardType.Phone)
                )
                Button(
                    onClick = {
                        scope.launch {
                            busy = true; error = null
                            runCancellableCatching { ApiProvider.unwrap(ApiProvider.api.requestSecondCode(AuthSecondCodeRequest(attemptId, secondValue.trim()))) }
                                .onSuccess { response ->
                                    if (secondChannel == "EMAIL") email = secondValue.trim() else phone = secondValue.trim()
                                    code = ""
                                    stage = 3
                                    info = response.mensagem ?: "Segundo código enviado."
                                }.onFailure { error = it.message ?: "Não foi possível enviar o segundo código." }
                            busy = false
                        }
                    }, enabled = !busy && secondValue.isNotBlank(), modifier = Modifier.fillMaxWidth()
                ) { if (busy) CircularProgressIndicator(Modifier.size(18.dp), strokeWidth = 2.dp) else Text("Enviar segundo código") }
            }
            3 -> {
                val destination = if (secondChannel == "EMAIL") email else phone
                Text("Confirme o segundo código", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.SemiBold)
                Text(info ?: "Digite o código enviado para $destination.")
                Spacer(Modifier.height(12.dp))
                OutlinedTextField(code, { code = it.filter(Char::isDigit).take(6); error = null }, label = { Text("Código de 6 dígitos") }, singleLine = true, modifier = Modifier.fillMaxWidth(), keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number))
                Button(
                    onClick = {
                        scope.launch {
                            busy = true; error = null
                            runCancellableCatching { ApiProvider.unwrap(ApiProvider.api.verifyCode(AuthVerifyRequest(attemptId, code))) }
                                .onSuccess { response ->
                                    if (response.dados != null) acceptAuth(response.dados)
                                    else error = response.mensagem ?: "A autenticação ainda não foi concluída."
                                }.onFailure { error = it.message ?: "Não foi possível validar o segundo código." }
                            busy = false
                        }
                    }, enabled = !busy && code.length == 6, modifier = Modifier.fillMaxWidth()
                ) { if (busy) CircularProgressIndicator(Modifier.size(18.dp), strokeWidth = 2.dp) else Text("Validar e continuar") }
            }
            4 -> {
                Text("Confirme seu celular", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.SemiBold)
                Text(info ?: "Informe seu celular com DDD para vincular à conta e receber o código de confirmação pelo WhatsApp.")
                OutlinedTextField(
                    value = phone,
                    onValueChange = { phone = it; error = null },
                    label = { Text("Celular com DDD e país (+55)") },
                    placeholder = { Text("+55 11 99999-9999") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Phone)
                )
                Button(
                    onClick = {
                        scope.launch {
                            busy = true; error = null
                            runCancellableCatching {
                                when (socialProvider) {
                                    "GOOGLE" -> ApiProvider.unwrap(ApiProvider.api.authenticateGoogle(GoogleAuthRequest(socialCredential, phone.trim())))
                                    "FACEBOOK" -> ApiProvider.unwrap(ApiProvider.api.completeFacebook(FacebookCompleteRequest(socialTicket, phone.trim())))
                                    else -> throw IllegalStateException("Provedor social não identificado.")
                                }
                            }.onSuccess { continueSocialAuthentication(it) }
                                .onFailure { error = it.message ?: "Não foi possível validar o celular." }
                            busy = false
                        }
                    }, enabled = !busy && phone.isNotBlank(), modifier = Modifier.fillMaxWidth()
                ) { if (busy) CircularProgressIndicator(Modifier.size(18.dp), strokeWidth = 2.dp) else Text("Enviar código pelo WhatsApp") }
            }
            5 -> {
                RegistrationForm(
                    registration = registration!!,
                    busy = busy,
                    error = error,
                    onSubmit = { request ->
                        scope.launch {
                            busy = true; error = null
                            runCancellableCatching { ApiProvider.unwrap(ApiProvider.api.registerUser(request)) }
                                .onSuccess { result ->
                                    val user = result.dados?.usuario
                                    val token = result.dados?.token
                                    if (user == null || token.isNullOrBlank()) {
                                        error = "Cadastro concluído, mas a API não retornou a sessão."
                                    } else {
                                        val created = SessionManager.Session(
                                            id = user.id,
                                            accountType = "PERSONAL",
                                            token = token,
                                            name = user.nome_completo ?: request.nome_completo,
                                            email = user.email ?: request.email
                                        )
                                        onAuthenticated(created)
                                        result.dados.endereco?.id?.let { addressId ->
                                            runCancellableCatching { ApiProvider.unwrap(ApiProvider.api.geocodeAddress(user.id, addressId)) }
                                        }
                                    }
                                }.onFailure { error = it.message ?: "Não foi possível concluir o cadastro." }
                            busy = false
                        }
                    }
                )
            }
        }

        error?.let { Spacer(Modifier.height(12.dp)); Text(it, color = MaterialTheme.colorScheme.error) }
        if (stage in 1..5 && stage != 5) {
            TextButton(onClick = { stage = 0; attemptId = ""; code = ""; error = null; info = null; socialProvider = ""; socialCredential = ""; socialTicket = "" }) {
                Text("Voltar e escolher outra forma de acesso")
            }
        }
    }
}

@Composable
private fun RegistrationForm(
    registration: RegistrationInfo,
    busy: Boolean,
    error: String?,
    onSubmit: (UserRegistrationRequest) -> Unit
) {
    var name by remember { mutableStateOf("") }
    var cpf by remember { mutableStateOf("") }
    var birth by remember { mutableStateOf("") }
    var cep by remember { mutableStateOf("") }
    var street by remember { mutableStateOf("") }
    var number by remember { mutableStateOf("") }
    var complement by remember { mutableStateOf("") }
    var district by remember { mutableStateOf("") }
    var city by remember { mutableStateOf("") }
    var state by remember { mutableStateOf("") }

    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text("Complete seu cadastro", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.SemiBold)
        Text("E-mail e celular já foram confirmados. Preencha seus dados para criar a conta.")
        Text("${registration.email} · ${registration.phone}", style = MaterialTheme.typography.bodySmall)
        OutlinedTextField(name, { name = it }, label = { Text("Nome completo") }, modifier = Modifier.fillMaxWidth(), singleLine = true)
        OutlinedTextField(cpf, { cpf = it.filter(Char::isDigit).take(11) }, label = { Text("CPF (somente números)") }, modifier = Modifier.fillMaxWidth(), singleLine = true, keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number))
        OutlinedTextField(birth, { birth = it }, label = { Text("Nascimento (AAAA-MM-DD, opcional)") }, modifier = Modifier.fillMaxWidth(), singleLine = true)
        Divider()
        Text("Endereço principal", fontWeight = FontWeight.SemiBold)
        OutlinedTextField(cep, { cep = it.filter(Char::isDigit).take(8) }, label = { Text("CEP") }, modifier = Modifier.fillMaxWidth(), singleLine = true, keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number))
        OutlinedTextField(street, { street = it }, label = { Text("Rua") }, modifier = Modifier.fillMaxWidth(), singleLine = true)
        OutlinedTextField(number, { number = it }, label = { Text("Número") }, modifier = Modifier.fillMaxWidth(), singleLine = true)
        OutlinedTextField(complement, { complement = it }, label = { Text("Complemento (opcional)") }, modifier = Modifier.fillMaxWidth(), singleLine = true)
        OutlinedTextField(district, { district = it }, label = { Text("Bairro") }, modifier = Modifier.fillMaxWidth(), singleLine = true)
        OutlinedTextField(city, { city = it }, label = { Text("Cidade") }, modifier = Modifier.fillMaxWidth(), singleLine = true)
        OutlinedTextField(state, { state = it.uppercase().take(2) }, label = { Text("UF") }, modifier = Modifier.fillMaxWidth(), singleLine = true)
        Button(
            onClick = {
                onSubmit(
                    UserRegistrationRequest(
                        nome_completo = name.trim(),
                        email = registration.email,
                        telefone = registration.phone,
                        cpf = cpf,
                        tentativa_id = registration.attemptId,
                        data_nascimento = birth.trim().takeIf { it.isNotEmpty() },
                        endereco = AddressRegistration(
                            cep = cep,
                            rua = street.trim(),
                            numero = number.trim(),
                            complemento = complement.trim().ifBlank { null },
                            bairro = district.trim(),
                            cidade = city.trim(),
                            estado = state.trim()
                        )
                    )
                )
            },
            enabled = !busy && name.isNotBlank() && cpf.length == 11 && cep.length == 8 && street.isNotBlank() && number.isNotBlank() && district.isNotBlank() && city.isNotBlank() && state.length == 2,
            modifier = Modifier.fillMaxWidth()
        ) { if (busy) CircularProgressIndicator(Modifier.size(18.dp), strokeWidth = 2.dp) else Text("Criar conta") }
        error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun ShopScreen(
    session: SessionManager.Session,
    onLogout: () -> Unit,
    onSessionUpdated: (SessionManager.Session) -> Unit,
    paymentUri: Uri?,
    onPaymentUriConsumed: () -> Unit,
    initialCart: List<StoredCartItem>,
    onCartChanged: (List<StoredCartItem>) -> Unit,
    startInCart: Boolean
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var tab by remember { mutableStateOf(if (startInCart) 1 else 0) }
    var restaurants by remember { mutableStateOf<List<RestaurantDto>>(emptyList()) }
    var restaurantLoading by remember { mutableStateOf(false) }
    var restaurantError by remember { mutableStateOf<String?>(null) }
    var selectedRestaurant by remember { mutableStateOf<RestaurantDto?>(null) }
    var products by remember { mutableStateOf<List<ProductDto>>(emptyList()) }
    var productLoading by remember { mutableStateOf(false) }
    var productsError by remember { mutableStateOf<String?>(null) }
    var cart by remember { mutableStateOf(initialCart.map { CartEntry(it.product, it.quantity) }) }
    LaunchedEffect(cart) { onCartChanged(cart.map { StoredCartItem(it.product, it.quantity) }) }
    LaunchedEffect(session.id, startInCart) { if (startInCart) tab = 1 }
    var orders by remember { mutableStateOf<List<OrderDto>>(emptyList()) }
    var orderLoading by remember { mutableStateOf(false) }
    var orderError by remember { mutableStateOf<String?>(null) }
    var checkoutMessage by remember { mutableStateOf<String?>(null) }
    var paymentInfo by remember { mutableStateOf<PaymentDto?>(null) }
    var createdOrder by remember { mutableStateOf<OrderDto?>(null) }
    var paymentIdempotencyKey by remember { mutableStateOf<String?>(null) }
    var actionBusy by remember { mutableStateOf(false) }
    var cancellingOrderId by remember { mutableStateOf<Int?>(null) }
    var receiptCodes by remember { mutableStateOf<Map<Int, String>>(emptyMap()) }
    var receiptCodeErrors by remember { mutableStateOf<Map<Int, String>>(emptyMap()) }
    var receiptCodeLoadingOrderId by remember { mutableStateOf<Int?>(null) }
    var settingsExpanded by remember { mutableStateOf(false) }
    var showPendingOnly by remember { mutableStateOf(false) }

    suspend fun loadRestaurants() {
        restaurantLoading = true; restaurantError = null
        runCatching { ApiProvider.unwrap(ApiProvider.api.restaurants()) }
            .onSuccess { restaurants = it.dados.filter { r -> r.ativo && r.status != "SUSPENSO" } }
            .onFailure { restaurantError = it.message ?: "Não foi possível consultar as docerias." }
        restaurantLoading = false
    }
    suspend fun loadOrders() {
        orderLoading = true; orderError = null
        runCatching { ApiProvider.unwrap(ApiProvider.api.orders()) }
            .onSuccess { orders = it.pedidos }
            .onFailure { orderError = it.message ?: "Não foi possível carregar os pedidos." }
        orderLoading = false
    }

    fun generateReceiptCode(orderId: Int) {
        if (receiptCodeLoadingOrderId != null) return
        receiptCodeLoadingOrderId = orderId
        receiptCodeErrors = receiptCodeErrors - orderId
        scope.launch {
            runCancellableCatching { ApiProvider.unwrap(ApiProvider.api.generateReceiptCode(orderId)) }
                .onSuccess { response ->
                    response.codigo?.let { code ->
                        receiptCodes = receiptCodes + (orderId to code)
                    }
                }
                .onFailure { err ->
                    receiptCodeErrors = receiptCodeErrors + (orderId to (err.message ?: "Não foi possível gerar o código."))
                }
            receiptCodeLoadingOrderId = null
        }
    }

    suspend fun initiatePayment(orderId: Int) {
        val idempotencyKey = paymentIdempotencyKey
            ?: "candyland-android-$orderId-${UUID.randomUUID()}".also { paymentIdempotencyKey = it }
        val payment = ApiProvider.unwrap(ApiProvider.api.createPayment(orderId, idempotencyKey, "ANDROID")).pagamento            ?: throw IllegalStateException("O servidor não retornou os dados do pagamento.")
        paymentInfo = payment
        when {
            !payment.pix_copy_paste.isNullOrBlank() -> {
                checkoutMessage = "Pix gerado. Escaneie o QR Code ou copie o código e pague no app do seu banco/Mercado Pago."
            }
            !payment.approval_url.isNullOrBlank() -> {
                context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(payment.approval_url)))
                checkoutMessage = "A autorização segura do PayPal foi aberta. Ao concluir, você retornará ao CandyLand."
            }
            else -> {
                checkoutMessage = payment.message ?: "Pedido criado. Aguardando instruções do provedor de pagamento."
            }
        }
    }

    LaunchedEffect(session.id) {
        loadRestaurants()
        loadOrders()
        runCatching { PushTokenManager.registerCurrentDevice(context) }
        runCatching { ApiProvider.unwrap(ApiProvider.api.userProfile(session.id)).dados }
            .onSuccess { profile ->
                val foto = profile?.foto_perfil_url
                if (foto != session.fotoPerfilUrl) onSessionUpdated(session.copy(fotoPerfilUrl = foto))
            }
    }

    LaunchedEffect(paymentUri) {
        val returnedUri = paymentUri ?: return@LaunchedEffect
        val orderId = returnedUri.getQueryParameter("order_id")?.toIntOrNull()
        tab = 1
        paymentInfo = null
        checkoutMessage = "Retorno do pagamento recebido. Conferindo seu pedido..."

        if (orderId == null) {
            checkoutMessage = "O aplicativo foi reaberto pelo pagamento, mas não recebeu o número do pedido. Consulte Meus pedidos."
        } else {
            createdOrder = null
            val provider = returnedUri.getQueryParameter("provider").orEmpty().lowercase()
            val cancelled = returnedUri.path.orEmpty().endsWith("/cancel")
            runCatching {
                when (provider) {
                    "paypal" -> {
                        val paypalToken = returnedUri.getQueryParameter("token").orEmpty()
                        val response = if (cancelled) {
                            ApiProvider.unwrap(ApiProvider.api.cancelPayPalPayment(orderId, PayPalOrderActionRequest(paypalToken)))
                        } else {
                            ApiProvider.unwrap(ApiProvider.api.capturePayPalPayment(orderId, PayPalOrderActionRequest(paypalToken)))
                        }
                        paymentInfo = response.pagamento
                        createdOrder = response.pedido
                    }
                    "mercadopago" -> {
                        // GET /pagamento consulta a API oficial do Mercado Pago e
                        // reconcilia o pedido; nunca confiamos no status da URL.
                        paymentInfo = ApiProvider.unwrap(ApiProvider.api.getPayment(orderId)).pagamento
                    }
                    else -> throw IllegalStateException("O retorno não identificou um provedor de pagamento válido.")
                }

                val pedidoAtualizado = ApiProvider.unwrap(ApiProvider.api.order(orderId)).pedido
                    ?: createdOrder
                    ?: throw IllegalStateException("O servidor não retornou o pedido após o pagamento.")
                createdOrder = pedidoAtualizado
                loadOrders()
                checkoutMessage = when {
                    pedidoAtualizado.status in RECEIPT_CODE_ELIGIBLE_STATUSES ->
                        "Pagamento confirmado e pedido criado! Gere seu código de recebimento e apresente-o quando retirar ou receber o pedido."
                    pedidoAtualizado.status == "CANCELADO" ->
                        "Este pedido foi cancelado. Consulte o histórico para ver os detalhes."
                    cancelled ->
                        "O checkout foi cancelado. O pedido continua aguardando pagamento e não foi enviado à doceria."
                    paymentInfo?.status == "REJECTED" || paymentInfo?.status == "CANCELLED" ->
                        "O provedor não aprovou o pagamento. O pedido continua pendente e não foi enviado à doceria."
                    else ->
                        "O pedido foi localizado, mas o pagamento ainda está em confirmação. Atualize Meus pedidos em instantes."
                }
            }.onFailure { error ->
                checkoutMessage = error.message ?: "Não foi possível consultar o resultado do pagamento. Atualize Meus pedidos."
                runCatching { ApiProvider.unwrap(ApiProvider.api.order(orderId)).pedido }
                    .onSuccess { createdOrder = it }
                loadOrders()
            }
        }
        onPaymentUriConsumed()
    }

    Scaffold(
        topBar = {
            if (tab != 0) TopAppBar(
                title = {
                    Column {
                        Text("CandyLand", fontWeight = FontWeight.Bold)
                        Text("Olá, ${session.name}", style = MaterialTheme.typography.labelSmall)
                    }
                },
                actions = {
                    TextButton(onClick = { settingsExpanded = true }) {
                        if (!session.fotoPerfilUrl.isNullOrBlank()) {
                            coil3.compose.AsyncImage(
                                model = mobileImageUrl(session.fotoPerfilUrl), contentDescription = "Foto do perfil",
                                modifier = Modifier.size(38.dp).clip(androidx.compose.foundation.shape.CircleShape),
                                contentScale = androidx.compose.ui.layout.ContentScale.Crop
                            )
                        } else Text("👤", fontSize = 25.sp)
                    }
                    DropdownMenu(expanded = settingsExpanded, onDismissRequest = { settingsExpanded = false }) {
                        DropdownMenuItem(text = { Text("Minha conta e endereços") }, onClick = { settingsExpanded = false; tab = 3 })
                        DropdownMenuItem(text = { Text("Histórico de pedidos") }, onClick = { settingsExpanded = false; showPendingOnly = false; tab = 2; scope.launch { loadOrders() } })
                        DropdownMenuItem(text = { Text("Pagamentos pendentes") }, onClick = { settingsExpanded = false; showPendingOnly = true; tab = 2; scope.launch { loadOrders() } })
                        Divider()
                        DropdownMenuItem(text = { Text("Sair") }, onClick = { settingsExpanded = false; onLogout() })
                    }
                }
            )
        },
        bottomBar = {
            NavigationBar {
                NavigationBarItem(selected = tab == 0, onClick = { tab = 0 }, icon = { Text("🍬") }, label = { Text("Docerias") })
                NavigationBarItem(selected = tab == 1, onClick = { tab = 1 }, icon = { Text("🛒") }, label = { Text("Carrinho (${cart.sumOf { it.quantity }})") })
                NavigationBarItem(selected = tab == 2, onClick = { showPendingOnly = false; tab = 2; scope.launch { loadOrders() } }, icon = { Text("📦") }, label = { Text("Pedidos") })
            }
        }
    ) { innerPadding ->
        when (tab) {
            0 -> Box(Modifier.padding(innerPadding)) {
                WelcomeScreen(
                    cart = cart.map { StoredCartItem(it.product, it.quantity) },
                    onCartChanged = { updated -> cart = updated.map { CartEntry(it.product, it.quantity) } },
                    onLogin = { tab = 3 },
                    onCheckout = { tab = 1 },
                    profilePhotoUrl = session.fotoPerfilUrl
                )
            }
            1 -> CartScreen(
                session = session,
                cart = cart,
                orderBusy = actionBusy,
                createdOrder = createdOrder,
                checkoutMessage = checkoutMessage,
                paymentInfo = paymentInfo,
                receiptCode = createdOrder?.let { receiptCodes[it.id] },
                receiptCodeLoading = createdOrder?.let { receiptCodeLoadingOrderId == it.id } ?: false,
                receiptCodeError = createdOrder?.let { receiptCodeErrors[it.id] },
                onGenerateReceiptCode = { generateReceiptCode(it) },
                onQuantity = { productId, quantity -> cart = if (quantity <= 0) cart.filterNot { it.product.id == productId } else cart.map { if (it.product.id == productId) it.copy(quantity = quantity) else it } },
                onCheckout = { orderType, addressId, paymentMethod ->
                    if (cart.isEmpty() || cart.firstOrNull() == null) return@CartScreen
                    scope.launch {
                        actionBusy = true; checkoutMessage = null; paymentInfo = null; createdOrder = null
                        val restaurantId = cart.first().product.restaurantId
                        runCatching {
                            if (orderType == "DELIVERY") {
                                val userAddresses = ApiProvider.unwrap(ApiProvider.api.addresses(session.id)).dados
                                val selected = userAddresses.firstOrNull { it.id == addressId }
                                    ?: throw IllegalStateException("Selecione um endereço válido para a entrega.")
                                if (selected.latitude == null || selected.longitude == null) {
                                    ApiProvider.unwrap(ApiProvider.api.geocodeAddress(session.id, selected.id))
                                }
                            }
                            val newOrder = ApiProvider.unwrap(
                                ApiProvider.api.createOrder(
                                    CreateOrderRequest(
                                        restaurant_id = restaurantId,
                                        order_type = orderType,
                                        payment_method = paymentMethod,
                                        items = cart.map { OrderItemRequest(it.product.id, it.quantity) },
                                        delivery_address_id = if (orderType == "DELIVERY") addressId else null
                                    )
                                )
                            ).pedido ?: throw IllegalStateException("O backend não retornou o pedido criado.")
                            createdOrder = newOrder
                            paymentIdempotencyKey = "candyland-android-${newOrder.id}-${UUID.randomUUID()}"
                            cart = emptyList()
                            loadOrders()
                            checkoutMessage = "Confira o frete e o total acima. Nenhuma cobrança foi iniciada ainda. Toque em 'Confirmar e pagar' para continuar."
                        }.onFailure {
                            checkoutMessage = it.message ?: "Não foi possível finalizar o pedido."
                        }
                        actionBusy = false
                    }
                },
                onRetryPayment = { orderId ->
                    scope.launch {
                        actionBusy = true
                        runCatching { initiatePayment(orderId) }
                            .onFailure { checkoutMessage = it.message ?: "Não foi possível iniciar o pagamento." }
                        actionBusy = false
                    }
                },
                onRefreshPayment = { orderId ->
                    scope.launch {
                        actionBusy = true
                        runCatching {
                            paymentInfo = ApiProvider.unwrap(ApiProvider.api.getPayment(orderId)).pagamento
                            createdOrder = ApiProvider.unwrap(ApiProvider.api.order(orderId)).pedido
                            loadOrders()
                        }.onSuccess {
                            checkoutMessage = if (createdOrder?.status?.let { it in RECEIPT_CODE_ELIGIBLE_STATUSES } == true) {
                                "Pagamento confirmado pelo provedor. Seu pedido foi atualizado."
                            } else "Ainda aguardando confirmação do pagamento. Confira novamente em instantes."
                        }.onFailure { checkoutMessage = it.message ?: "Não foi possível consultar o pagamento." }
                        actionBusy = false
                    }
                },
                onManageAddresses = { tab = 3 },
                onNewOrder = {
                    createdOrder = null; checkoutMessage = null; paymentInfo = null; paymentIdempotencyKey = null
                },
                modifier = Modifier.padding(innerPadding)
            )
            2 -> OrderHistoryScreen(
                orders = if (showPendingOnly) orders.filter { it.status == "PENDENTE_PAGAMENTO" } else orders,
                receiptCodes = receiptCodes,
                receiptCodeErrors = receiptCodeErrors,
                receiptCodeLoadingOrderId = receiptCodeLoadingOrderId,
                loading = orderLoading,
                error = orderError,
                onRefresh = { scope.launch { loadOrders() } },
                onGenerateReceiptCode = { orderId -> generateReceiptCode(orderId) },
                onContinuePayment = { order ->
                    createdOrder = order
                    paymentInfo = null
                    paymentIdempotencyKey = null
                    checkoutMessage = "Pedido pendente. Confira os dados e toque em Confirmar e pagar para retomar a compra."
                    tab = 1
                },
                onCancelOrder = { orderId ->
                    if (cancellingOrderId == null) scope.launch {
                        cancellingOrderId = orderId
                        runCatching { ApiProvider.unwrap(ApiProvider.api.cancelOrder(orderId)) }
                            .onSuccess {
                                if (createdOrder?.id == orderId) {
                                    createdOrder = createdOrder?.copy(status = "CANCELADO")
                                    paymentInfo = null
                                }
                                loadOrders()
                            }
                            .onFailure { orderError = it.message ?: "Não foi possível cancelar o pedido." }
                        cancellingOrderId = null
                    }
                },
                cancellingOrderId = cancellingOrderId,
                modifier = Modifier.padding(innerPadding)
            )
            else -> CustomerSettingsScreen(
                session = session,
                onSessionUpdated = onSessionUpdated,
                onBack = { tab = 0 },
                onOpenOrders = {
                    showPendingOnly = false
                    tab = 2
                    scope.launch { loadOrders() }
                },
                modifier = Modifier.padding(innerPadding)
            )
        }
    }
}

@Composable
private fun RestaurantListScreen(
    restaurants: List<RestaurantDto>,
    loading: Boolean,
    error: String?,
    onRefresh: () -> Unit,
    onSelect: (RestaurantDto) -> Unit,
    modifier: Modifier = Modifier
) {
    Column(modifier.fillMaxSize().padding(16.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text("Docerias disponíveis", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold, modifier = Modifier.weight(1f))
            TextButton(onClick = onRefresh) { Text("Atualizar") }
        }
        if (loading) Box(Modifier.fillMaxWidth().padding(24.dp), contentAlignment = Alignment.Center) { CircularProgressIndicator() }
        error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
        if (!loading && restaurants.isEmpty() && error == null) Text("Nenhuma doceria cadastrada neste momento.")
        restaurants.forEach { restaurant ->
            Card(
                modifier = Modifier.fillMaxWidth().padding(vertical = 6.dp),
                onClick = { onSelect(restaurant) },
                colors = CardDefaults.cardColors(containerColor = Color.White)
            ) {
                Column(Modifier.padding(16.dp)) {
                    Text(restaurant.nome, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
                    restaurant.descricao?.takeIf { it.isNotBlank() }?.let { Text(it, style = MaterialTheme.typography.bodyMedium) }
                    Text(mobileStoreStatusLabel(restaurant.status), style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.primary)
                    Spacer(Modifier.height(6.dp))
                    Text("Pedido mínimo: ${money(restaurant.valor_minimo_pedido ?: 0.0)}", style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.primary)
                    Text("Ver cardápio  →", style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.primary)
                }
            }
        }
    }
}

@Composable
private fun ProductListScreen(
    restaurant: RestaurantDto,
    restaurantCanReceiveOrders: Boolean,
    products: List<ProductDto>,
    loading: Boolean,
    error: String?,
    onBack: () -> Unit,
    onAdd: (ProductDto) -> Unit,
    modifier: Modifier = Modifier
) {
    val lojaDisponivel = restaurant.ativo && restaurant.status == "ABERTO"
    Column(modifier.fillMaxSize().padding(16.dp)) {
        TextButton(onClick = onBack) { Text("← Docerias") }
        Text(restaurant.nome, style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
        restaurant.descricao?.let { Text(it) }
        Spacer(Modifier.height(12.dp))
        if (loading) Box(Modifier.fillMaxWidth().padding(24.dp), contentAlignment = Alignment.Center) { CircularProgressIndicator() }
        error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
        if (!loading && products.isEmpty() && error == null) Text("Esta doceria ainda não publicou produtos.")
        products.forEach { product ->
            Card(Modifier.fillMaxWidth().padding(vertical = 5.dp)) {
                Row(Modifier.padding(10.dp), verticalAlignment = Alignment.CenterVertically) {
                    coil3.compose.AsyncImage(
                        model = mobileImageUrl(product.imageUrl),
                        contentDescription = product.name,
                        modifier = Modifier.size(88.dp).clip(androidx.compose.foundation.shape.RoundedCornerShape(12.dp)),
                        contentScale = androidx.compose.ui.layout.ContentScale.Crop
                    )
                    Column(Modifier.weight(1f).padding(start = 10.dp)) {
                        Text(product.name, fontWeight = FontWeight.SemiBold)
                        product.description?.let { Text(it, style = MaterialTheme.typography.bodySmall) }
                        Text(money(product.price), color = MaterialTheme.colorScheme.primary, fontWeight = FontWeight.Bold)
                    }
                    val purchaseLabel = when (restaurant.status) {
                        "EM_ANALISE" -> "Aguardando aprovação"
                        "SUSPENSO" -> "Indisponível"
                        "FECHADO" -> "Loja fechada"
                        else -> if (product.available) "Adicionar" else "Indisponível"
                    }
                    Button(onClick = { onAdd(product) }, enabled = product.available && restaurantCanReceiveOrders) { Text(purchaseLabel) }
                }
            }
        }
    }
}

@Composable
private fun CartScreen(
    session: SessionManager.Session,
    cart: List<CartEntry>,
    orderBusy: Boolean,
    createdOrder: OrderDto?,
    checkoutMessage: String?,
    paymentInfo: PaymentDto?,
    receiptCode: String?,
    receiptCodeLoading: Boolean,
    receiptCodeError: String?,
    onGenerateReceiptCode: (Int) -> Unit,
    onQuantity: (Int, Int) -> Unit,
    onCheckout: (String, Int?, String) -> Unit,
    onRetryPayment: (Int) -> Unit,
    onRefreshPayment: (Int) -> Unit,
    onManageAddresses: () -> Unit,
    onNewOrder: () -> Unit,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current
    var addresses by remember { mutableStateOf<List<AddressDto>>(emptyList()) }
    var addressError by remember { mutableStateOf<String?>(null) }
    var orderType by remember { mutableStateOf("PICKUP") }
    var paymentMethod by remember { mutableStateOf("PIX") }
    var selectedAddress by remember { mutableStateOf<Int?>(null) }

    LaunchedEffect(session.id) {
        runCatching { ApiProvider.unwrap(ApiProvider.api.addresses(session.id)) }
            .onSuccess { list -> addresses = list.dados; selectedAddress = list.dados.firstOrNull { it.principal }?.id ?: list.dados.firstOrNull()?.id }
            .onFailure { addressError = it.message }
    }

    Column(modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp)) {
        Text("Seu carrinho", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
        if (createdOrder != null) {
            Card(Modifier.fillMaxWidth().padding(vertical = 12.dp)) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(7.dp)) {
                    Text("Pedido criado!", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.primary)
                    Text(createdOrder.order_code)
                    Text("Status: ${createdOrder.status}")
                    Text("Produtos: ${money(createdOrder.subtotal)}")
                    if (createdOrder.discount > 0.0) Text("Desconto: -${money(createdOrder.discount)}")
                    val freightLabel = if (createdOrder.delivery_fee <= 0.0) "Grátis" else money(createdOrder.delivery_fee)
                    Text("Frete: $freightLabel", fontWeight = FontWeight.SemiBold)
                    createdOrder.delivery_quote?.let { quote ->
                        val distance = quote.distance_km
                        val eta = quote.tempo_estimado
                        if (distance != null) {
                            val distanceLabel = if (quote.source == "GOOGLE_ROUTES_ESSENTIALS") "Distância pela rota" else "Distância aproximada (linha reta)"
                            Text("$distanceLabel: ${String.format(java.util.Locale("pt", "BR"), "%.1f", distance)} km")
                        }
                        if (eta != null) Text("Previsão aproximada: ${eta.minimo}–${eta.maximo} min")
                        if (quote.source == "GOOGLE_ROUTES_ESSENTIALS") {
                            // Atribuição textual da Routes API quando o conteúdo é mostrado fora de um Google Map.
                            Text("Google Maps", color = Color(0xFF5E5E5E), fontSize = 12.sp)
                        }
                    }
                    Text("Total a pagar: ${money(createdOrder.total)}", fontWeight = FontWeight.Bold)
                    checkoutMessage?.let { Text(it) }
                    if (createdOrder.status in RECEIPT_CODE_ELIGIBLE_STATUSES) {
                        Divider()
                        Text("Código de recebimento", fontWeight = FontWeight.SemiBold)
                        if (receiptCode == null) {
                            OutlinedButton(
                                onClick = { onGenerateReceiptCode(createdOrder.id) },
                                enabled = !receiptCodeLoading,
                                modifier = Modifier.fillMaxWidth()
                            ) { Text(if (receiptCodeLoading) "Gerando código..." else "Gerar código de recebimento") }
                        } else {
                            Text(receiptCode, style = MaterialTheme.typography.headlineMedium, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.primary)
                            Text("Apresente este código ao restaurante quando receber ou retirar o pedido.", style = MaterialTheme.typography.bodySmall)
                            OutlinedButton(
                                onClick = {
                                    val clipboard = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
                                    clipboard.setPrimaryClip(ClipData.newPlainText("Código de recebimento", receiptCode))
                                },
                                modifier = Modifier.fillMaxWidth()
                            ) { Text("Copiar código de recebimento") }
                        }
                        receiptCodeError?.let { Text(it, color = MaterialTheme.colorScheme.error) }
                    }
                    paymentInfo?.takeIf { !it.pix_copy_paste.isNullOrBlank() }?.let { pixPayment ->
                        val pixCopyPaste = pixPayment.pix_copy_paste.orEmpty()
                        Divider()
                        Text("Pague com Pix", fontWeight = FontWeight.SemiBold)
                        Text("Escaneie o QR Code com o app do seu banco ou do Mercado Pago. Confira o destinatário e o valor antes de confirmar.")
                        PixQrCode(pixPayment)
                        Text("Pix copia e cola", fontWeight = FontWeight.SemiBold)
                        androidx.compose.foundation.text.selection.SelectionContainer { Text(pixCopyPaste, style = MaterialTheme.typography.bodySmall) }
                        OutlinedButton(
                            onClick = {
                                val clipboard = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
                                clipboard.setPrimaryClip(ClipData.newPlainText("Pix CandyLand", pixCopyPaste))
                            },
                            modifier = Modifier.fillMaxWidth()
                        ) { Text("Copiar código Pix") }
                        OutlinedButton(
                            onClick = { onRefreshPayment(createdOrder.id) }, enabled = !orderBusy,
                            modifier = Modifier.fillMaxWidth()
                        ) { Text(if (orderBusy) "Consultando..." else "Já paguei — atualizar status") }
                    }
                    if (paymentInfo == null && createdOrder.status == "PENDENTE_PAGAMENTO") {
                        OutlinedButton(
                            onClick = { onRetryPayment(createdOrder.id) },
                            enabled = !orderBusy,
                            modifier = Modifier.fillMaxWidth()
                        ) { Text(if (orderBusy) "Iniciando pagamento..." else if (paymentInfo == null) "Confirmar e pagar" else "Tentar iniciar pagamento novamente") }
                    }
                    OutlinedButton(onClick = onNewOrder, modifier = Modifier.fillMaxWidth()) { Text("Voltar ao carrinho") }
                }
            }
        }
        if (cart.isEmpty()) {
            Text("Seu carrinho está vazio. Escolha uma doceria e adicione produtos.")
            return@Column
        }

        cart.forEach { entry ->
            Row(Modifier.fillMaxWidth().padding(vertical = 7.dp), verticalAlignment = Alignment.CenterVertically) {
                Column(Modifier.weight(1f)) {
                    Text(entry.product.name, fontWeight = FontWeight.SemiBold)
                    Text("${entry.quantity} × ${money(entry.product.price)}")
                }
                TextButton(onClick = { onQuantity(entry.product.id, entry.quantity - 1) }) { Text("−") }
                Text(entry.quantity.toString())
                TextButton(onClick = { onQuantity(entry.product.id, entry.quantity + 1) }) { Text("+") }
            }
            Divider()
        }
        Text("Subtotal estimado: ${money(cart.sumOf { it.product.price * it.quantity })}", fontWeight = FontWeight.Bold)
        Spacer(Modifier.height(16.dp))
        Text("Como deseja receber?", fontWeight = FontWeight.SemiBold)
        Row(verticalAlignment = Alignment.CenterVertically) {
            RadioButton(orderType == "PICKUP", onClick = { orderType = "PICKUP" })
            Text("Retirada")
            Spacer(Modifier.width(20.dp))
            RadioButton(orderType == "DELIVERY", onClick = { orderType = "DELIVERY" }, enabled = addresses.isNotEmpty())
            Text("Entrega")
        }
        if (orderType == "DELIVERY") {
            addressError?.let { Text("Endereços indisponíveis: $it", color = MaterialTheme.colorScheme.error) }
            if (addresses.isEmpty()) Text("Cadastre um endereço no seu perfil antes de solicitar entrega.")
            addresses.forEach { address ->
                Row(Modifier.fillMaxWidth().selectable(selectedAddress == address.id, onClick = { selectedAddress = address.id }), verticalAlignment = Alignment.CenterVertically) {
                    RadioButton(selectedAddress == address.id, onClick = { selectedAddress = address.id })
                    Text(address.label(), style = MaterialTheme.typography.bodySmall)
                }
            }
            addresses.firstOrNull { it.id == selectedAddress }?.let { destino ->
                Card(Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(12.dp)) {
                        Text("Endereço de entrega selecionado", fontWeight = FontWeight.SemiBold)
                        Text(destino.label(), style = MaterialTheme.typography.bodySmall)
                        TextButton(onClick = onManageAddresses) { Text("Alterar ou cadastrar endereço") }
                    }
                }
            }
        }
        Spacer(Modifier.height(10.dp))
        Text("Forma de pagamento", fontWeight = FontWeight.SemiBold)
        Row(verticalAlignment = Alignment.CenterVertically) {
            RadioButton(paymentMethod == "PIX", onClick = { paymentMethod = "PIX" })
            Text("Pix")
            Spacer(Modifier.width(18.dp))
            RadioButton(paymentMethod == "MERCADO_PAGO", onClick = { paymentMethod = "MERCADO_PAGO" })
            Text("Mercado Pago")
            Spacer(Modifier.width(18.dp))
            RadioButton(paymentMethod == "PAYPAL", onClick = { paymentMethod = "PAYPAL" })
            Text("PayPal")
        }
        Spacer(Modifier.height(12.dp))
        Button(
            onClick = { onCheckout(orderType, if (orderType == "DELIVERY") selectedAddress else null, paymentMethod) },
            enabled = !orderBusy && !(orderType == "DELIVERY" && selectedAddress == null),
            modifier = Modifier.fillMaxWidth()
        ) { if (orderBusy) CircularProgressIndicator(Modifier.size(18.dp), strokeWidth = 2.dp) else Text("Criar pedido e iniciar pagamento") }
        checkoutMessage?.takeIf { createdOrder == null }?.let { Text(it, color = MaterialTheme.colorScheme.error, modifier = Modifier.padding(top = 10.dp)) }
        Text("O valor final, a taxa e o estoque são validados pelo backend.", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}

@Composable
private fun OrderHistoryScreen(
    orders: List<OrderDto>,
    loading: Boolean,
    error: String?,
    onRefresh: () -> Unit,
    receiptCodes: Map<Int, String>,
    receiptCodeErrors: Map<Int, String>,
    receiptCodeLoadingOrderId: Int?,
    onGenerateReceiptCode: (Int) -> Unit,
    onContinuePayment: (OrderDto) -> Unit,
    onCancelOrder: (Int) -> Unit,
    cancellingOrderId: Int?,
    modifier: Modifier = Modifier
) {
    var orderAwaitingCancellation by remember { mutableStateOf<OrderDto?>(null) }
    Column(modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(16.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text("Meus pedidos", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold, modifier = Modifier.weight(1f))
            TextButton(onClick = onRefresh) { Text("Atualizar") }
        }
        if (loading) Box(Modifier.fillMaxWidth().padding(24.dp), contentAlignment = Alignment.Center) { CircularProgressIndicator() }
        error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
        if (!loading && orders.isEmpty() && error == null) Text("Você ainda não realizou pedidos.")
        orders.forEach { order ->
            Card(Modifier.fillMaxWidth().padding(vertical = 6.dp)) {
                Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(5.dp)) {
                    Text(order.restaurant_name ?: "Pedido CandyLand", fontWeight = FontWeight.SemiBold)
                    Text(order.order_code, style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.primary)
                    Text("Status: ${statusLabel(order.status)}")
                    Text(if (order.order_type == "PICKUP") "Retirada" else "Entrega")
                    Text(money(order.total), fontWeight = FontWeight.Bold)
                    order.created_at?.let { Text(it.replace("T", " ").take(16), style = MaterialTheme.typography.bodySmall) }
                    val code = receiptCodes[order.id]
                    if (code != null) {
                        Text("Código de recebimento: $code", color = MaterialTheme.colorScheme.primary, fontWeight = FontWeight.Bold)
                        Text("Apresente este código ao parceiro quando receber o pedido.", style = MaterialTheme.typography.bodySmall)
                    } else if (order.status in setOf("PAGAMENTO_CONFIRMADO", "RESTAURANTE_RECEBEU", "RESTAURANTE_ACEITOU", "PROCESSANDO", "PRONTO_PARA_ENTREGA", "ENTREGUE")) {
                        val isGenerating = receiptCodeLoadingOrderId == order.id
                        OutlinedButton(onClick = { onGenerateReceiptCode(order.id) }, enabled = !isGenerating, modifier = Modifier.fillMaxWidth()) {
                            Text(if (isGenerating) "Gerando código..." else "Gerar código de recebimento")
                        }
                        receiptCodeErrors[order.id]?.let {
                            Text(it, color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall)
                        }
                    }
                    if (order.status == "PENDENTE_PAGAMENTO") {
                        Spacer(Modifier.height(6.dp))
                        OutlinedButton(
                            onClick = { onContinuePayment(order) },
                            enabled = cancellingOrderId == null,
                            modifier = Modifier.fillMaxWidth()
                        ) { Text("Continuar pagamento") }
                        TextButton(
                            onClick = { orderAwaitingCancellation = order },
                            enabled = cancellingOrderId == null,
                            modifier = Modifier.fillMaxWidth()
                        ) { Text(if (cancellingOrderId == order.id) "Cancelando..." else "Cancelar pedido") }
                    }
                }
            }
        }
    }
    orderAwaitingCancellation?.let { order ->
        AlertDialog(
            onDismissRequest = { if (cancellingOrderId == null) orderAwaitingCancellation = null },
            title = { Text("Cancelar pedido?") },
            text = { Text("O pedido ${order.order_code} ainda aguarda pagamento. Deseja realmente cancelá-lo?") },
            confirmButton = {
                TextButton(
                    onClick = {
                        orderAwaitingCancellation = null
                        onCancelOrder(order.id)
                    },
                    enabled = cancellingOrderId == null
                ) { Text("Sim, cancelar") }
            },
            dismissButton = {
                TextButton(onClick = { orderAwaitingCancellation = null }) { Text("Manter pedido") }
            }
        )
    }
}

private fun mobileStoreStatusLabel(status: String?): String = when (status) {
    "ABERTO" -> "Aberta"
    "FECHADO" -> "Fechada"
    "EM_ANALISE" -> "Em análise"
    "SUSPENSO" -> "Suspensa"
    else -> status ?: "Indisponível"
}

private fun money(value: Double): String =
    NumberFormat.getCurrencyInstance(Locale("pt", "BR")).format(value)

private fun statusLabel(status: String): String = when (status) {
    "PENDENTE_PAGAMENTO" -> "Aguardando pagamento"
    "PAGAMENTO_CONFIRMADO" -> "Pagamento confirmado"
    "RESTAURANTE_RECEBEU" -> "Recebido pela doceria"
    "RESTAURANTE_ACEITOU" -> "Pedido aceito"
    "PROCESSANDO" -> "Em preparo"
    "PRONTO_PARA_ENTREGA" -> "Pronto"
    "ENTREGUE" -> "Entregue"
    "FINALIZADO" -> "Finalizado"
    "CANCELADO" -> "Cancelado"
    else -> status
}
