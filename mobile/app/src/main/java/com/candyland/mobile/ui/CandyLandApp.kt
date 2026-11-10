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
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Divider
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
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.ui.unit.dp
import androidx.credentials.CredentialManager
import androidx.credentials.CustomCredential
import androidx.credentials.GetCredentialRequest
import com.google.android.libraries.identity.googleid.GetGoogleIdOption
import com.google.android.libraries.identity.googleid.GoogleIdTokenCredential
import com.candyland.mobile.BuildConfig
import com.candyland.mobile.data.ApiProvider
import com.candyland.mobile.data.SessionManager
import com.candyland.mobile.model.*
import com.candyland.mobile.push.PushTokenManager
import kotlinx.coroutines.launch
import java.util.UUID
import java.text.NumberFormat
import java.util.Locale

private data class RegistrationInfo(val attemptId: String, val email: String, val phone: String)
private data class CartEntry(val product: ProductDto, val quantity: Int)

@Composable
fun CandyLandApp(
    applicationContext: Context,
    oauthUri: Uri? = null,
    onOAuthUriConsumed: () -> Unit = {}
) {
    val appScope = rememberCoroutineScope()
    var session by remember { mutableStateOf(SessionManager.current(applicationContext)) }
    var showAuthentication by remember { mutableStateOf(oauthUri != null) }

    LaunchedEffect(oauthUri) {
        if (oauthUri != null) showAuthentication = true
    }

    MaterialTheme(
        colorScheme = MaterialTheme.colorScheme.copy(
            primary = Color(0xFF9C287B),
            secondary = Color(0xFFF09ACB),
            background = Color(0xFFFFF8FC),
            surface = Color.White
        )
    ) {
        Surface(modifier = Modifier.fillMaxSize(), color = MaterialTheme.colorScheme.background) {
            if (session == null) {
                if (showAuthentication) {
                    AuthenticationScreen(
                        oauthUri = oauthUri,
                        onOAuthUriConsumed = onOAuthUriConsumed,
                        onBack = { showAuthentication = false },
                        onAuthenticated = { newSession ->
                            SessionManager.save(applicationContext, newSession)
                            session = newSession
                        }
                    )
                } else {
                    WelcomeScreen(onLogin = { showAuthentication = true })
                }
            } else {
                ShopScreen(
                    session = session!!,
                    onLogout = {
                        appScope.launch {
                            runCatching { PushTokenManager.unregisterCurrentDevice(applicationContext) }
                            SessionManager.clear(applicationContext)
                            session = null
                            showAuthentication = false
                        }
                    }
                )
            }
        }
    }
}

@Composable
private fun WelcomeScreen(onLogin: () -> Unit) {
    var restaurants by remember { mutableStateOf<List<RestaurantDto>>(emptyList()) }
    var loading by remember { mutableStateOf(true) }
    var loadError by remember { mutableStateOf<String?>(null) }

    LaunchedEffect(Unit) {
        runCatching { ApiProvider.unwrap(ApiProvider.api.restaurants()) }
            .onSuccess { response -> restaurants = response.dados.filter { it.ativo && it.status == "ABERTO" } }
            .onFailure { loadError = it.message ?: "Não foi possível carregar as docerias agora." }
        loading = false
    }

    Column(
        modifier = Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
        horizontalAlignment = Alignment.Start
    ) {
        Text("🍬", style = MaterialTheme.typography.displayLarge)
        Text(
            "CandyLand",
            style = MaterialTheme.typography.headlineLarge,
            fontWeight = FontWeight.Bold,
            color = MaterialTheme.colorScheme.primary
        )
        Text(
            "Seu cantinho de doces, pedidos e momentos especiais.",
            style = MaterialTheme.typography.titleMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Button(onClick = onLogin, modifier = Modifier.fillMaxWidth()) {
            Text("Entrar")
        }
        Text(
            "Ainda não tem conta? O cadastro será iniciado depois da confirmação dos seus contatos.",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
        Divider(Modifier.padding(vertical = 6.dp))
        Text("Docerias abertas", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.SemiBold)
        when {
            loading -> Box(Modifier.fillMaxWidth().padding(20.dp), contentAlignment = Alignment.Center) { CircularProgressIndicator() }
            loadError != null -> Text(loadError!!, color = MaterialTheme.colorScheme.error)
            restaurants.isEmpty() -> Text("Ainda não há docerias abertas por aqui.", color = MaterialTheme.colorScheme.onSurfaceVariant)
            else -> restaurants.forEach { restaurant ->
                Card(Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                        Text(restaurant.nome, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
                        restaurant.descricao?.takeIf { it.isNotBlank() }?.let { Text(it, style = MaterialTheme.typography.bodySmall) }
                        Text("Loja parceira CandyLand · Aberta", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.primary)
                    }
                }
            }
        }
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
        if (data.tipo_conta != "PERSONAL") {
            error = "Esta versão do CandyLand é destinada a clientes. Entre pela versão de parceiros."
            return
        }
        onAuthenticated(
            SessionManager.Session(
                id = id,
                accountType = data.tipo_conta,
                token = token,
                name = data.nome_completo ?: data.nome ?: "Cliente",
                email = data.email ?: email
            )
        )
    }

    fun continueSocialAuthentication(response: SocialAuthResponse) {
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
        if (oauthUri != null) {
            onOAuthUriConsumed()
            val ticket = oauthUri.getQueryParameter("ticket")
            val oauthError = oauthUri.getQueryParameter("error")
            if (!oauthError.isNullOrBlank()) {
                error = oauthError
            } else if (!ticket.isNullOrBlank()) {
                socialProvider = "FACEBOOK"
                socialTicket = ticket
                busy = true
                runCatching {
                    ApiProvider.unwrap(ApiProvider.api.completeFacebook(FacebookCompleteRequest(ticket)))
                }.onSuccess { continueSocialAuthentication(it) }
                    .onFailure { error = it.message ?: "Não foi possível concluir o login com Facebook." }
                busy = false
            }
        }
    }

    fun startGoogleLogin() {
        if (BuildConfig.GOOGLE_WEB_CLIENT_ID.isBlank()) {
            error = "O login Google ainda não foi configurado. Informe CANDYLAND_GOOGLE_WEB_CLIENT_ID em mobile/local.properties e use o mesmo ID em GOOGLE_CLIENT_ID no backend."
            return
        }
        scope.launch {
            busy = true
            error = null
            info = null
            runCatching {
                val googleOption = GetGoogleIdOption.Builder()
                    .setServerClientId(BuildConfig.GOOGLE_WEB_CLIENT_ID)
                    .setFilterByAuthorizedAccounts(false)
                    .setAutoSelectEnabled(false)
                    .build()
                val request = GetCredentialRequest.Builder()
                    .addCredentialOption(googleOption)
                    .build()
                val result = credentialManager.getCredential(context, request)
                val credential = result.credential
                if (credential !is CustomCredential || credential.type != GoogleIdTokenCredential.TYPE_GOOGLE_ID_TOKEN_CREDENTIAL) {
                    throw IllegalStateException("O Google não retornou uma credencial de identidade válida.")
                }
                val idToken = GoogleIdTokenCredential.createFrom(credential.data).idToken
                socialProvider = "GOOGLE"
                socialCredential = idToken
                ApiProvider.unwrap(ApiProvider.api.authenticateGoogle(GoogleAuthRequest(credential = idToken)))
            }.onSuccess { continueSocialAuthentication(it) }
                .onFailure { error = it.message ?: "Não foi possível entrar com o Google." }
            busy = false
        }
    }

    fun startFacebookLogin() {
        runCatching {
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
                            runCatching {
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
                    "A confirmação da conta utiliza dois fatores: o contato escolhido agora e o segundo contato solicitado na próxima etapa.",
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
                            runCatching { ApiProvider.unwrap(ApiProvider.api.verifyCode(AuthVerifyRequest(attemptId, code))) }
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
                Text("Informe seu segundo contato", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.SemiBold)
                Text(info ?: "Para proteger sua conta, precisamos confirmar também seu $secondLabel.")
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
                            runCatching { ApiProvider.unwrap(ApiProvider.api.requestSecondCode(AuthSecondCodeRequest(attemptId, secondValue.trim()))) }
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
                            runCatching { ApiProvider.unwrap(ApiProvider.api.verifyCode(AuthVerifyRequest(attemptId, code))) }
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
                            runCatching {
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
                            runCatching { ApiProvider.unwrap(ApiProvider.api.registerUser(request)) }
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
                                            runCatching { ApiProvider.unwrap(ApiProvider.api.geocodeAddress(user.id, addressId)) }
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
private fun ShopScreen(session: SessionManager.Session, onLogout: () -> Unit) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var tab by remember { mutableStateOf(0) }
    var restaurants by remember { mutableStateOf<List<RestaurantDto>>(emptyList()) }
    var restaurantLoading by remember { mutableStateOf(false) }
    var restaurantError by remember { mutableStateOf<String?>(null) }
    var selectedRestaurant by remember { mutableStateOf<RestaurantDto?>(null) }
    var products by remember { mutableStateOf<List<ProductDto>>(emptyList()) }
    var productLoading by remember { mutableStateOf(false) }
    var productsError by remember { mutableStateOf<String?>(null) }
    var cart by remember { mutableStateOf<List<CartEntry>>(emptyList()) }
    var orders by remember { mutableStateOf<List<OrderDto>>(emptyList()) }
    var orderLoading by remember { mutableStateOf(false) }
    var orderError by remember { mutableStateOf<String?>(null) }
    var checkoutMessage by remember { mutableStateOf<String?>(null) }
    var paymentInfo by remember { mutableStateOf<PaymentDto?>(null) }
    var createdOrder by remember { mutableStateOf<OrderDto?>(null) }
    var paymentIdempotencyKey by remember { mutableStateOf<String?>(null) }
    var actionBusy by remember { mutableStateOf(false) }

    suspend fun loadRestaurants() {
        restaurantLoading = true; restaurantError = null
        runCatching { ApiProvider.unwrap(ApiProvider.api.restaurants()) }
            .onSuccess { restaurants = it.dados.filter { r -> r.ativo && r.status == "ABERTO" } }
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

    suspend fun initiatePayment(orderId: Int) {
        val idempotencyKey = paymentIdempotencyKey
            ?: "candyland-android-$orderId-${UUID.randomUUID()}".also { paymentIdempotencyKey = it }
        val payment = ApiProvider.unwrap(ApiProvider.api.createPayment(orderId, idempotencyKey)).pagamento
            ?: throw IllegalStateException("O servidor não retornou os dados do pagamento.")
        paymentInfo = payment
        when {
            !payment.approval_url.isNullOrBlank() -> {
                context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(payment.approval_url)))
                checkoutMessage = "Pedido criado. A autorização do pagamento foi aberta no navegador."
            }
            !payment.pix_copy_paste.isNullOrBlank() -> {
                checkoutMessage = "Pedido criado. Pix copia e cola disponível abaixo; aguarde a confirmação."
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
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text("CandyLand", fontWeight = FontWeight.Bold)
                        Text("Olá, ${session.name}", style = MaterialTheme.typography.labelSmall)
                    }
                },
                actions = { TextButton(onClick = onLogout) { Text("Sair") } }
            )
        },
        bottomBar = {
            NavigationBar {
                NavigationBarItem(selected = tab == 0, onClick = { tab = 0 }, icon = { Text("🍬") }, label = { Text("Docerias") })
                NavigationBarItem(selected = tab == 1, onClick = { tab = 1 }, icon = { Text("🛒") }, label = { Text("Carrinho (${cart.sumOf { it.quantity }})") })
                NavigationBarItem(selected = tab == 2, onClick = { tab = 2; scope.launch { loadOrders() } }, icon = { Text("📦") }, label = { Text("Pedidos") })
            }
        }
    ) { innerPadding ->
        when (tab) {
            0 -> {
                if (selectedRestaurant == null) {
                    RestaurantListScreen(
                        restaurants = restaurants,
                        loading = restaurantLoading,
                        error = restaurantError,
                        onRefresh = { scope.launch { loadRestaurants() } },
                        onSelect = { restaurant ->
                            selectedRestaurant = restaurant
                            productLoading = true; productsError = null
                            scope.launch {
                                runCatching { ApiProvider.unwrap(ApiProvider.api.products(restaurant.id)) }
                                    .onSuccess { products = it.dados }
                                    .onFailure { productsError = it.message ?: "Não foi possível carregar os produtos." }
                                productLoading = false
                            }
                        },
                        modifier = Modifier.padding(innerPadding)
                    )
                } else {
                    ProductListScreen(
                        restaurant = selectedRestaurant!!,
                        products = products,
                        loading = productLoading,
                        error = productsError,
                        onBack = { selectedRestaurant = null },
                        onAdd = { product ->
                            val base = if (cart.isNotEmpty() && cart.first().product.restaurantId != product.restaurantId) emptyList() else cart
                            val existing = base.firstOrNull { it.product.id == product.id }
                            cart = if (existing == null) base + CartEntry(product, 1)
                            else base.map { if (it.product.id == product.id) it.copy(quantity = it.quantity + 1) else it }
                        },
                        modifier = Modifier.padding(innerPadding)
                    )
                }
            }
            1 -> CartScreen(
                session = session,
                cart = cart,
                orderBusy = actionBusy,
                createdOrder = createdOrder,
                checkoutMessage = checkoutMessage,
                paymentInfo = paymentInfo,
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
                            initiatePayment(newOrder.id)
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
                onNewOrder = {
                    createdOrder = null; checkoutMessage = null; paymentInfo = null; paymentIdempotencyKey = null
                },
                modifier = Modifier.padding(innerPadding)
            )
            else -> OrderHistoryScreen(
                orders = orders,
                loading = orderLoading,
                error = orderError,
                onRefresh = { scope.launch { loadOrders() } },
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
        if (!loading && restaurants.isEmpty() && error == null) Text("Nenhuma doceria disponível neste momento.")
        restaurants.forEach { restaurant ->
            Card(
                modifier = Modifier.fillMaxWidth().padding(vertical = 6.dp),
                onClick = { onSelect(restaurant) },
                colors = CardDefaults.cardColors(containerColor = Color.White)
            ) {
                Column(Modifier.padding(16.dp)) {
                    Text(restaurant.nome, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
                    restaurant.descricao?.takeIf { it.isNotBlank() }?.let { Text(it, style = MaterialTheme.typography.bodyMedium) }
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
    products: List<ProductDto>,
    loading: Boolean,
    error: String?,
    onBack: () -> Unit,
    onAdd: (ProductDto) -> Unit,
    modifier: Modifier = Modifier
) {
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
                Row(Modifier.padding(14.dp), verticalAlignment = Alignment.CenterVertically) {
                    Column(Modifier.weight(1f)) {
                        Text(product.name, fontWeight = FontWeight.SemiBold)
                        product.description?.let { Text(it, style = MaterialTheme.typography.bodySmall) }
                        Text(money(product.price), color = MaterialTheme.colorScheme.primary, fontWeight = FontWeight.Bold)
                    }
                    Button(onClick = { onAdd(product) }, enabled = product.available) { Text(if (product.available) "Adicionar" else "Indisponível") }
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
    onQuantity: (Int, Int) -> Unit,
    onCheckout: (String, Int?, String) -> Unit,
    onRetryPayment: (Int) -> Unit,
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
                    Text("Total calculado pelo servidor: ${money(createdOrder.total)}", fontWeight = FontWeight.Bold)
                    checkoutMessage?.let { Text(it) }
                    paymentInfo?.pix_copy_paste?.let {
                        Divider()
                        Text("Pix copia e cola", fontWeight = FontWeight.SemiBold)
                        androidx.compose.foundation.text.selection.SelectionContainer { Text(it, style = MaterialTheme.typography.bodySmall) }
                        OutlinedButton(
                            onClick = {
                                val clipboard = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
                                clipboard.setPrimaryClip(ClipData.newPlainText("Pix CandyLand", it))
                            },
                            modifier = Modifier.fillMaxWidth()
                        ) { Text("Copiar código Pix") }
                    }
                    if (paymentInfo == null && createdOrder.status == "PENDENTE_PAGAMENTO") {
                        OutlinedButton(
                            onClick = { onRetryPayment(createdOrder.id) },
                            enabled = !orderBusy,
                            modifier = Modifier.fillMaxWidth()
                        ) { Text(if (orderBusy) "Iniciando pagamento..." else "Tentar iniciar pagamento novamente") }
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
    modifier: Modifier = Modifier
) {
    Column(modifier.fillMaxSize().padding(16.dp)) {
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
                }
            }
        }
    }
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
