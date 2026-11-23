package com.candyland.mobile.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Divider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.OutlinedButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.candyland.mobile.data.ApiProvider
import com.candyland.mobile.data.SessionManager
import com.candyland.mobile.data.ViaCepClient
import com.candyland.mobile.model.AddressDto
import com.candyland.mobile.model.AddressUpsertRequest
import com.candyland.mobile.model.UserProfileUpdateRequest
import kotlinx.coroutines.launch

@Composable
fun CustomerSettingsScreen(
    session: SessionManager.Session,
    onBack: () -> Unit,
    onSessionUpdated: (SessionManager.Session) -> Unit,
    onOpenOrders: () -> Unit = {},
    modifier: Modifier = Modifier
) {
    val scope = rememberCoroutineScope()
    var name by remember { mutableStateOf(session.name) }
    var birthDate by remember { mutableStateOf("") }
    var email by remember { mutableStateOf(session.email) }
    var phone by remember { mutableStateOf("") }
    var cpf by remember { mutableStateOf("") }
    var profilePhotoUrl by remember { mutableStateOf(session.fotoPerfilUrl) }
    var cepBusy by remember { mutableStateOf(false) }
    var addresses by remember { mutableStateOf<List<AddressDto>>(emptyList()) }
    var loading by remember { mutableStateOf(true) }
    var busy by remember { mutableStateOf(false) }
    var message by remember { mutableStateOf<String?>(null) }
    var error by remember { mutableStateOf<String?>(null) }
    var addressDialog by remember { mutableStateOf(false) }
    var editingAddressId by remember { mutableStateOf<Int?>(null) }
    var cep by remember { mutableStateOf("") }
    var street by remember { mutableStateOf("") }
    var number by remember { mutableStateOf("") }
    var complement by remember { mutableStateOf("") }
    var district by remember { mutableStateOf("") }
    var city by remember { mutableStateOf("") }
    var state by remember { mutableStateOf("") }
    var reference by remember { mutableStateOf("") }
    var principal by remember { mutableStateOf(false) }
    suspend fun refreshAddresses() {
        addresses = ApiProvider.unwrap(ApiProvider.api.addresses(session.id)).dados
    }

    LaunchedEffect(session.id) {
        loading = true
        runCatching {
            val profile = ApiProvider.unwrap(ApiProvider.api.userProfile(session.id)).dados
                ?: throw IllegalStateException("O servidor não retornou os dados do cliente.")
            name = profile.nome_completo
            birthDate = profile.data_nascimento.orEmpty()
            email = profile.email
            phone = profile.telefone
            cpf = profile.cpf
            profilePhotoUrl = profile.foto_perfil_url
            onSessionUpdated(session.copy(fotoPerfilUrl = profile.foto_perfil_url))
            refreshAddresses()
        }.onFailure { error = it.message ?: "Não foi possível carregar seus dados." }
        loading = false
    }

    fun startNewAddress() {
        editingAddressId = null
        cep = ""; street = ""; number = ""; complement = ""
        district = ""; city = ""; state = ""; reference = ""
        principal = addresses.isEmpty()
        addressDialog = true
    }

    fun editAddress(address: AddressDto) {
        editingAddressId = address.id
        cep = address.cep.orEmpty()
        street = address.rua.orEmpty()
        number = address.numero.orEmpty()
        complement = address.complemento.orEmpty()
        district = address.bairro.orEmpty()
        city = address.cidade.orEmpty()
        state = address.estado.orEmpty()
        reference = address.referencia.orEmpty()
        principal = address.principal
        addressDialog = true
    }

    if (addressDialog) {
        AlertDialog(
            onDismissRequest = { if (!busy) addressDialog = false },
            title = { Text(if (editingAddressId == null) "Novo endereço" else "Editar endereço") },
            text = {
                Column(
                    modifier = Modifier.fillMaxWidth().height(430.dp).verticalScroll(rememberScrollState()),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Text("Informe o endereço. O CandyLand localiza as coordenadas automaticamente.", style = MaterialTheme.typography.bodySmall)
                    Row(verticalAlignment = androidx.compose.ui.Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        OutlinedTextField(cep, { cep = it.filter(Char::isDigit).take(8) }, label = { Text("CEP") }, singleLine = true, modifier = Modifier.weight(1f))
                        OutlinedButton(
                            enabled = !cepBusy && cep.filter(Char::isDigit).length == 8,
                            onClick = {
                                scope.launch {
                                    cepBusy = true; error = null
                                    runCatching { ViaCepClient.buscar(cep) }
                                        .onSuccess { endereco ->
                                            street = endereco.logradouro.orEmpty()
                                            district = endereco.bairro.orEmpty()
                                            city = endereco.localidade.orEmpty()
                                            state = endereco.uf.orEmpty()
                                            message = "Endereço preenchido pelo ViaCEP. Confira número e complemento."
                                        }
                                        .onFailure { error = it.message ?: "Não foi possível consultar o CEP." }
                                    cepBusy = false
                                }
                            }
                        ) { Text(if (cepBusy) "Buscando..." else "Buscar CEP") }
                    }
                    OutlinedTextField(street, { street = it }, label = { Text("Rua / Avenida") }, singleLine = true, modifier = Modifier.fillMaxWidth())
                    OutlinedTextField(number, { number = it }, label = { Text("Número") }, singleLine = true, modifier = Modifier.fillMaxWidth())
                    OutlinedTextField(complement, { complement = it }, label = { Text("Complemento") }, singleLine = true, modifier = Modifier.fillMaxWidth())
                    OutlinedTextField(district, { district = it }, label = { Text("Bairro") }, singleLine = true, modifier = Modifier.fillMaxWidth())
                    OutlinedTextField(city, { city = it }, label = { Text("Cidade") }, singleLine = true, modifier = Modifier.fillMaxWidth())
                    OutlinedTextField(state, { state = it.uppercase().take(2) }, label = { Text("UF") }, singleLine = true, modifier = Modifier.fillMaxWidth())
                    OutlinedTextField(reference, { reference = it }, label = { Text("Referência (opcional)") }, singleLine = true, modifier = Modifier.fillMaxWidth())
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        androidx.compose.material3.Checkbox(checked = principal, onCheckedChange = { principal = it })
                        Text("Endereço principal", modifier = Modifier.padding(top = 12.dp))
                    }
                }
            },
            confirmButton = {
                TextButton(
                    enabled = !busy && cep.isNotBlank() && street.isNotBlank() && number.isNotBlank() && district.isNotBlank() && city.isNotBlank() && state.length == 2,
                    onClick = {
                        scope.launch {
                            busy = true; error = null; message = null
                            runCatching {
                                val body = AddressUpsertRequest(
                                    cep = cep.trim(), rua = street.trim(), numero = number.trim(),
                                    complemento = complement.trim().ifBlank { null },
                                    bairro = district.trim(), cidade = city.trim(), estado = state.trim().uppercase(),
                                    referencia = reference.trim().ifBlank { null }, principal = principal
                                )
                                if (editingAddressId == null) {
                                    ApiProvider.unwrap(ApiProvider.api.addUserAddress(session.id, body))
                                } else {
                                    ApiProvider.unwrap(ApiProvider.api.updateUserAddress(session.id, editingAddressId!!, body))
                                }
                                refreshAddresses()
                                val savedAddress = addresses.firstOrNull {
                                    it.cep.orEmpty().filter(Char::isDigit) == cep.filter(Char::isDigit) && it.numero == number.trim()
                                }
                                if (savedAddress != null && (savedAddress.latitude == null || savedAddress.longitude == null)) {
                                    runCatching { ApiProvider.unwrap(ApiProvider.api.geocodeAddress(session.id, savedAddress.id)) }
                                    refreshAddresses()
                                }
                            }.onSuccess {
                                addressDialog = false
                                message = "Endereço salvo. O ViaCEP preencheu os dados e o servidor foi solicitado a geocodificar o endereço."
                            }.onFailure { error = it.message ?: "Não foi possível salvar o endereço." }
                            busy = false
                        }
                    }
                ) { Text(if (busy) "Salvando..." else "Salvar endereço") }
            },
            dismissButton = { TextButton(onClick = { addressDialog = false }, enabled = !busy) { Text("Cancelar") } }
        )
    }

    Column(
        modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(18.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            TextButton(onClick = onBack) { Text("← Voltar") }
            Text("Minha conta", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.Bold)
        }
        if (loading) {
            CircularProgressIndicator()
            return@Column
        }
        error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
        message?.let { Text(it, color = MaterialTheme.colorScheme.primary) }

        Card(Modifier.fillMaxWidth()) {
            Row(Modifier.padding(16.dp), verticalAlignment = androidx.compose.ui.Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(14.dp)) {
                if (!profilePhotoUrl.isNullOrBlank()) {
                    coil3.compose.AsyncImage(
                        model = mobileImageUrl(profilePhotoUrl), contentDescription = "Foto de perfil",
                        modifier = Modifier.size(76.dp).clip(androidx.compose.foundation.shape.CircleShape),
                        contentScale = androidx.compose.ui.layout.ContentScale.Crop
                    )
                } else Text("👤", fontSize = 42.sp)
                Column(Modifier.weight(1f)) {
                    Text("Foto de perfil", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
                    Text(
                        "O envio de novas fotos ficará disponível quando a API do servidor oferecer suporte a essa operação.",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
        }

        Card(Modifier.fillMaxWidth()) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(9.dp)) {
                Text("Dados pessoais", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
                OutlinedTextField(name, { name = it }, label = { Text("Nome completo") }, singleLine = true, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(birthDate, { birthDate = it }, label = { Text("Nascimento (AAAA-MM-DD)") }, singleLine = true, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(email, {}, label = { Text("E-mail verificado") }, readOnly = true, singleLine = true, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(phone, {}, label = { Text("Celular verificado") }, readOnly = true, singleLine = true, modifier = Modifier.fillMaxWidth())
                OutlinedTextField(cpf, {}, label = { Text("CPF") }, readOnly = true, singleLine = true, modifier = Modifier.fillMaxWidth())
                Text("Alterar e-mail ou celular exige uma nova verificação de segurança.", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                Button(
                    onClick = {
                        scope.launch {
                            busy = true; error = null; message = null
                            runCatching {
                                ApiProvider.unwrap(
                                    ApiProvider.api.updateUserProfile(
                                        session.id,
                                        UserProfileUpdateRequest(name.trim(), birthDate.trim().ifBlank { null })
                                    )
                                )
                            }.onSuccess {
                                onSessionUpdated(session.copy(name = name.trim()))
                                message = "Dados pessoais atualizados."
                            }.onFailure { error = it.message ?: "Não foi possível atualizar o perfil." }
                            busy = false
                        }
                    },
                    enabled = !busy && name.isNotBlank(),
                    modifier = Modifier.fillMaxWidth()
                ) { Text(if (busy) "Salvando..." else "Salvar dados pessoais") }
            }
        }

        Card(Modifier.fillMaxWidth()) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Row(verticalAlignment = androidx.compose.ui.Alignment.CenterVertically) {
                    Text("Meus endereços", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold, modifier = Modifier.weight(1f))
                    TextButton(onClick = { startNewAddress() }) { Text("Adicionar") }
                }
                if (addresses.isEmpty()) Text("Nenhum endereço cadastrado.", color = MaterialTheme.colorScheme.onSurfaceVariant)
                addresses.forEach { address ->
                    Divider()
                    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                        Text(address.label(), fontWeight = FontWeight.SemiBold)
                        if (address.principal) Text("Principal", color = MaterialTheme.colorScheme.primary, style = MaterialTheme.typography.labelSmall)
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            TextButton(onClick = { editAddress(address) }) { Text("Editar") }
                            TextButton(onClick = {
                                scope.launch {
                                    busy = true; error = null; message = null
                                    runCatching {
                                        ApiProvider.unwrap(ApiProvider.api.deleteUserAddress(session.id, address.id))
                                        refreshAddresses()
                                    }.onSuccess { message = "Endereço removido." }
                                        .onFailure { error = it.message ?: "Não foi possível remover o endereço." }
                                    busy = false
                                }
                            }, enabled = !busy) { Text("Excluir") }
                        }
                    }
                }
            }
        }

        Card(Modifier.fillMaxWidth()) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("Pedidos e recebimento", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
                Text("Consulte seus pedidos e gere o código de seis dígitos para apresentar à doceria na retirada ou entrega.")
                Button(onClick = onOpenOrders, modifier = Modifier.fillMaxWidth()) {
                    Text("Ver pedidos e códigos de recebimento")
                }
            }
        }

        Card(Modifier.fillMaxWidth()) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("Cartões", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
                Text("O checkout atual usa o ambiente seguro do Mercado Pago/PayPal. O cadastro de cartões salvos ainda depende da integração de tokenização do gateway e de uma API de cartões no backend.")
                Text("Não informe nem armazene número completo ou CVV neste aplicativo. Quando a tokenização estiver pronta, esta seção será habilitada com o token seguro do provedor.", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
        }

        Spacer(Modifier.height(12.dp))
        if (busy) CircularProgressIndicator()
    }
}
