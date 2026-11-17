package com.candyland.mobile.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Checkbox
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Divider
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
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
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.ui.unit.dp
import com.candyland.mobile.data.ApiProvider
import com.candyland.mobile.data.SessionManager
import com.candyland.mobile.model.CategoryCreateRequest
import com.candyland.mobile.model.CategoryDto
import com.candyland.mobile.model.OrderDto
import com.candyland.mobile.model.OrderStatusRequest
import com.candyland.mobile.model.ProductDto
import com.candyland.mobile.model.ProductUpsertRequest
import com.candyland.mobile.model.ReceiptCodeRequest
import com.candyland.mobile.model.RestaurantAddressUpdateRequest
import com.candyland.mobile.model.RestaurantConfigurationUpdateRequest
import com.candyland.mobile.model.RestaurantProfileDto
import com.candyland.mobile.model.RestaurantStatusRequest
import com.candyland.mobile.push.PushTokenManager
import kotlinx.coroutines.launch
import java.text.NumberFormat
import java.util.Locale

private val SELLER_NEXT_ORDER_STATUS = mapOf(
    "PAGAMENTO_CONFIRMADO" to "RESTAURANTE_RECEBEU",
    "RESTAURANTE_RECEBEU" to "RESTAURANTE_ACEITOU",
    "RESTAURANTE_ACEITOU" to "PROCESSANDO",
    "PROCESSANDO" to "PRONTO_PARA_ENTREGA"
)

private val SELLER_CATEGORY_OPTIONS = listOf(
    "Bolos", "Chocolates", "Pirulitos", "Cupcakes", "Pudins", "Balas", "Donuts", "Cookies"
)

private val SELLER_DELIVERY_NEXT_STATUS = mapOf(
    "NAO_SOLICITADO" to "PROCURANDO",
    "PROCURANDO" to "MOTORISTA_ENCONTRADO",
    "MOTORISTA_ENCONTRADO" to "MOTORISTA_A_CAMINHO",
    "MOTORISTA_A_CAMINHO" to "MOTORISTA_NO_RESTAURANTE",
    "MOTORISTA_NO_RESTAURANTE" to "PEDIDO_RETIRADO",
    "PEDIDO_RETIRADO" to "EM_ROTA",
    "EM_ROTA" to "ENTREGA_CONCLUIDA",
    "SEM_MOTORISTA" to "PROCURANDO"
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun BusinessSellerScreen(
    session: SessionManager.Session,
    onLogout: () -> Unit
) {
    val scope = rememberCoroutineScope()
    val context = LocalContext.current
    var tab by remember { mutableStateOf(0) }
    var restaurant by remember { mutableStateOf<RestaurantProfileDto?>(null) }
    var products by remember { mutableStateOf<List<ProductDto>>(emptyList()) }
    var categories by remember { mutableStateOf<List<CategoryDto>>(emptyList()) }
    var orders by remember { mutableStateOf<List<OrderDto>>(emptyList()) }
    var loading by remember { mutableStateOf(true) }
    var busy by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    var message by remember { mutableStateOf<String?>(null) }
    var receiptCodes by remember { mutableStateOf<Map<Int, String>>(emptyMap()) }
    var receiptInputs by remember { mutableStateOf<Map<Int, String>>(emptyMap()) }
    var productDialog by remember { mutableStateOf(false) }
    var categoryDialog by remember { mutableStateOf(false) }
    var categoryMenuExpanded by remember { mutableStateOf(false) }
    var newCategoryMenuExpanded by remember { mutableStateOf(false) }
    var editingProductId by remember { mutableStateOf<Int?>(null) }
    var selectedCategoryId by remember { mutableStateOf<Int?>(null) }
    var newCategoryName by remember { mutableStateOf(SELLER_CATEGORY_OPTIONS.first()) }
    var productName by remember { mutableStateOf("") }
    var productDescription by remember { mutableStateOf("") }
    var productPrice by remember { mutableStateOf("") }
    var productStock by remember { mutableStateOf("0") }
    var productAvailable by remember { mutableStateOf(true) }
    var productImported by remember { mutableStateOf(false) }
    var productCustomizable by remember { mutableStateOf(false) }

    // Configuration form mirrors the business web configuration.
    var storeName by remember { mutableStateOf("") }
    var companyName by remember { mutableStateOf("") }
    var managerName by remember { mutableStateOf("") }
    var description by remember { mutableStateOf("") }
    var minimumOrder by remember { mutableStateOf("0") }
    var baseFee by remember { mutableStateOf("0") }
    var feePerKm by remember { mutableStateOf("0") }
    var deliveryRadius by remember { mutableStateOf("") }
    var openingHours by remember { mutableStateOf("") }
    var postalCode by remember { mutableStateOf("") }
    var street by remember { mutableStateOf("") }
    var number by remember { mutableStateOf("") }
    var complement by remember { mutableStateOf("") }
    var district by remember { mutableStateOf("") }
    var city by remember { mutableStateOf("") }
    var state by remember { mutableStateOf("") }
    var reference by remember { mutableStateOf("") }

    suspend fun loadConfiguration() {
        val config = ApiProvider.unwrap(ApiProvider.api.restaurantConfiguration(session.id)).dados
            ?: throw IllegalStateException("O servidor não retornou a configuração da doceria.")
        val store = config.restaurante ?: throw IllegalStateException("Não foi possível identificar a doceria.")
        val address = config.endereco
        restaurant = store
        storeName = store.nome
        companyName = store.razao_social
        managerName = store.nome_responsavel.orEmpty()
        description = store.descricao.orEmpty()
        minimumOrder = (store.valor_minimo_pedido ?: 0.0).toString()
        baseFee = (store.taxa_entrega_base ?: 0.0).toString()
        feePerKm = (store.taxa_entrega_por_km ?: 0.0).toString()
        deliveryRadius = store.raio_entrega_km?.toString().orEmpty()
        openingHours = store.horario_funcionamento.orEmpty()
        postalCode = address?.cep.orEmpty()
        street = address?.rua.orEmpty()
        number = address?.numero.orEmpty()
        complement = address?.complemento.orEmpty()
        district = address?.bairro.orEmpty()
        city = address?.cidade.orEmpty()
        state = address?.estado.orEmpty()
        reference = address?.referencia.orEmpty()
    }

    suspend fun loadOrders() {
        orders = ApiProvider.unwrap(ApiProvider.api.orders()).pedidos
    }

    suspend fun loadProducts() {
        products = ApiProvider.unwrap(ApiProvider.api.managedProducts(session.id)).dados
    }

    suspend fun loadCategories() {
        categories = ApiProvider.unwrap(ApiProvider.api.categories()).categorias.filter { it.ativa }
    }

    suspend fun reloadAll() {
        loading = true
        error = null
        runCatching {
            loadConfiguration()
            loadOrders()
            loadProducts()
            loadCategories()
        }.onFailure { error = it.message ?: "Não foi possível carregar o painel da doceria." }
        loading = false
    }

    fun startProductEditor(product: ProductDto? = null) {
        if (categories.isEmpty()) {
            error = "Cadastre uma categoria antes de criar produtos."
            return
        }
        editingProductId = product?.id
        productName = product?.name.orEmpty()
        productDescription = product?.description.orEmpty()
        productPrice = product?.price?.let { if (it > 0) it.toString() else "" }.orEmpty()
        productStock = (product?.stock ?: 0).toString()
        productAvailable = product?.available ?: true
        // Preserve the flags already stored for a product when editing it.
        productImported = product?.imported ?: false
        productCustomizable = product?.allowsCustomization ?: false
        selectedCategoryId = product?.categoryId?.takeIf { id -> categories.any { it.id == id } }
            ?: categories.firstOrNull()?.id
        productDialog = true
    }

    fun saveProduct() {
        val price = productPrice.replace(",", ".").toDoubleOrNull()
        val stock = productStock.toIntOrNull()
        val categoryId = selectedCategoryId
        if (productName.isBlank() || price == null || price <= 0 || stock == null || stock < 0 || categoryId == null) {
            error = "Informe nome, categoria, preço maior que zero e estoque inteiro não negativo."
            return
        }
        scope.launch {
            busy = true; error = null; message = null
            runCatching {
                val request = ProductUpsertRequest(
                    categoria_id = categoryId,
                    nome = productName.trim(),
                    descricao = productDescription.trim().ifBlank { null },
                    preco = price,
                    qtd_estoque = stock,
                    disponivel = productAvailable,
                    importado = productImported,
                    permite_customizacao = productCustomizable
                )
                if (editingProductId == null) {
                    ApiProvider.unwrap(ApiProvider.api.createProduct(request))
                } else {
                    ApiProvider.unwrap(ApiProvider.api.updateProduct(editingProductId!!, request))
                }
                loadProducts()
            }.onSuccess {
                productDialog = false
                message = if (editingProductId == null) "Produto cadastrado no cardápio." else "Produto atualizado."
            }.onFailure { error = it.message ?: "Não foi possível salvar o produto." }
            busy = false
        }
    }

    fun saveCategory() {
        scope.launch {
            busy = true; error = null; message = null
            runCatching {
                ApiProvider.unwrap(ApiProvider.api.createCategory(CategoryCreateRequest(newCategoryName)))
                loadCategories()
            }.onSuccess {
                categoryDialog = false
                message = "Categoria adicionada ao seu cardápio."
            }.onFailure { error = it.message ?: "Não foi possível criar a categoria." }
            busy = false
        }
    }

    LaunchedEffect(session.id) {
        reloadAll()
        runCatching { PushTokenManager.registerCurrentDevice(context) }
    }

    if (productDialog) {
        AlertDialog(
            onDismissRequest = { if (!busy) productDialog = false },
            title = { Text(if (editingProductId == null) "Novo produto" else "Editar produto") },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedTextField(productName, { productName = it }, label = { Text("Nome do produto") }, singleLine = true)
                    TextButton(onClick = { categoryMenuExpanded = true }) {
                        Text(categories.firstOrNull { it.id == selectedCategoryId }?.nome ?: "Escolher categoria")
                    }
                    DropdownMenu(expanded = categoryMenuExpanded, onDismissRequest = { categoryMenuExpanded = false }) {
                        categories.forEach { category ->
                            DropdownMenuItem(
                                text = { Text(category.nome) },
                                onClick = { selectedCategoryId = category.id; categoryMenuExpanded = false }
                            )
                        }
                    }
                    OutlinedTextField(productDescription, { productDescription = it }, label = { Text("Descrição (opcional)") }, singleLine = false)
                    OutlinedTextField(productPrice, { productPrice = it }, label = { Text("Preço (R$)") }, singleLine = true, keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal))
                    OutlinedTextField(productStock, { productStock = it.filter(Char::isDigit).take(7) }, label = { Text("Estoque") }, singleLine = true, keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number))
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Checkbox(checked = productAvailable, onCheckedChange = { productAvailable = it })
                        Text("Produto disponível para venda")
                    }
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Checkbox(checked = productImported, onCheckedChange = { productImported = it })
                        Text("Produto importado")
                    }
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Checkbox(checked = productCustomizable, onCheckedChange = { productCustomizable = it })
                        Text("Permite personalização")
                    }
                }
            },
            confirmButton = {
                TextButton(onClick = { saveProduct() }, enabled = !busy) { Text(if (busy) "Salvando..." else "Salvar produto") }
            },
            dismissButton = { TextButton(onClick = { productDialog = false }, enabled = !busy) { Text("Cancelar") } }
        )
    }

    if (categoryDialog) {
        AlertDialog(
            onDismissRequest = { if (!busy) categoryDialog = false },
            title = { Text("Adicionar categoria") },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("Escolha uma das categorias disponíveis no CandyLand.")
                    TextButton(onClick = { newCategoryMenuExpanded = true }) { Text(newCategoryName) }
                    DropdownMenu(expanded = newCategoryMenuExpanded, onDismissRequest = { newCategoryMenuExpanded = false }) {
                        SELLER_CATEGORY_OPTIONS.filter { name -> categories.none { it.nome == name } }.forEach { name ->
                            DropdownMenuItem(text = { Text(name) }, onClick = { newCategoryName = name; newCategoryMenuExpanded = false })
                        }
                    }
                }
            },
            confirmButton = {
                TextButton(onClick = { saveCategory() }, enabled = !busy && categories.none { it.nome == newCategoryName }) { Text("Adicionar") }
            },
            dismissButton = { TextButton(onClick = { categoryDialog = false }, enabled = !busy) { Text("Cancelar") } }
        )
    }

    fun changeOrderStatus(orderId: Int, nextStatus: String) {
        scope.launch {
            busy = true; error = null; message = null
            runCatching {
                ApiProvider.unwrap(ApiProvider.api.updateOrderStatus(orderId, OrderStatusRequest(nextStatus)))
                loadOrders()
            }.onSuccess { message = "Pedido atualizado." }
                .onFailure { error = it.message ?: "Não foi possível atualizar o pedido." }
            busy = false
        }
    }

    fun changeDeliveryStatus(orderId: Int, nextStatus: String) {
        scope.launch {
            busy = true; error = null; message = null
            runCatching {
                ApiProvider.unwrap(ApiProvider.api.updateDeliveryStatus(orderId, OrderStatusRequest(nextStatus)))
                loadOrders()
            }.onSuccess { message = "Etapa de entrega atualizada." }
                .onFailure { error = it.message ?: "Não foi possível atualizar a entrega." }
            busy = false
        }
    }

    fun validateReceipt(orderId: Int) {
        val code = receiptInputs[orderId].orEmpty().filter(Char::isDigit).take(6)
        if (code.length != 6) {
            error = "Informe o código de recebimento com seis dígitos."
            return
        }
        scope.launch {
            busy = true; error = null; message = null
            runCatching {
                ApiProvider.unwrap(ApiProvider.api.confirmReceipt(orderId, ReceiptCodeRequest(code)))
                loadOrders()
            }.onSuccess {
                receiptInputs = receiptInputs - orderId
                message = "Recebimento confirmado. Pedido finalizado."
            }.onFailure { error = it.message ?: "O código não pôde ser validado." }
            busy = false
        }
    }

    fun saveConfiguration() {
        if (listOf(storeName, companyName, street, number, postalCode, district, city, state).any { it.isBlank() }) {
            error = "Preencha nome da loja, razão social e endereço completo."
            return
        }
        scope.launch {
            busy = true; error = null; message = null
            runCatching {
                val request = RestaurantConfigurationUpdateRequest(
                    nome = storeName.trim(),
                    razao_social = companyName.trim(),
                    nome_responsavel = managerName.trim().ifBlank { null },
                    descricao = description.trim().ifBlank { null },
                    valor_minimo_pedido = minimumOrder.toDoubleOrNull() ?: 0.0,
                    taxa_entrega_base = baseFee.toDoubleOrNull() ?: 0.0,
                    taxa_entrega_por_km = feePerKm.toDoubleOrNull() ?: 0.0,
                    raio_entrega_km = deliveryRadius.toDoubleOrNull(),
                    horario_funcionamento = openingHours.trim().ifBlank { null },
                    endereco = RestaurantAddressUpdateRequest(
                        cep = postalCode.trim(), rua = street.trim(), numero = number.trim(),
                        complemento = complement.trim().ifBlank { null }, bairro = district.trim(),
                        cidade = city.trim(), estado = state.trim().uppercase(),
                        referencia = reference.trim().ifBlank { null }
                    )
                )
                ApiProvider.unwrap(ApiProvider.api.updateRestaurantConfiguration(session.id, request))
                loadConfiguration()
            }.onSuccess { message = "Configuração salva. O endereço é geocodificado pelo servidor." }
                .onFailure { error = it.message ?: "Não foi possível salvar a configuração." }
            busy = false
        }
    }

    fun toggleStoreStatus() {
        val current = restaurant?.status ?: return
        if (current !in listOf("ABERTO", "FECHADO")) {
            error = "A doceria ainda aguarda a liberação administrativa e não pode abrir ou fechar."
            return
        }
        val next = if (current == "ABERTO") "FECHADO" else "ABERTO"
        scope.launch {
            busy = true; error = null; message = null
            runCatching {
                ApiProvider.unwrap(ApiProvider.api.updateRestaurantStatus(session.id, RestaurantStatusRequest(next)))
                loadConfiguration()
            }.onSuccess { message = if (next == "ABERTO") "Sua doceria está aberta." else "Sua doceria foi fechada." }
                .onFailure { error = it.message ?: "Não foi possível alterar o status da loja." }
            busy = false
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text(restaurant?.nome ?: "Portal do vendedor", fontWeight = FontWeight.Bold)
                        Text("CandyLand para parceiros", style = MaterialTheme.typography.labelSmall)
                    }
                },
                actions = {
                    TextButton(onClick = { scope.launch { reloadAll() } }, enabled = !busy && !loading) { Text("↻") }
                    TextButton(onClick = onLogout) { Text("Sair") }
                }
            )
        },
        bottomBar = {
            NavigationBar {
                NavigationBarItem(selected = tab == 0, onClick = { tab = 0 }, icon = { Text("🏪") }, label = { Text("Painel") })
                NavigationBarItem(selected = tab == 1, onClick = { tab = 1 }, icon = { Text("🍰") }, label = { Text("Cardápio") })
                NavigationBarItem(selected = tab == 2, onClick = { tab = 2 }, icon = { Text("🧾") }, label = { Text("Pedidos") })
                NavigationBarItem(selected = tab == 3, onClick = { tab = 3 }, icon = { Text("⚙") }, label = { Text("Configuração") })
            }
        }
    ) { insets ->
        if (loading) {
            Column(Modifier.fillMaxSize().padding(insets), verticalArrangement = Arrangement.Center, horizontalAlignment = Alignment.CenterHorizontally) {
                CircularProgressIndicator()
                Text("Carregando seu portal...")
            }
        } else {
            Column(
                Modifier.fillMaxSize().padding(insets).verticalScroll(rememberScrollState()).padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                error?.let { Text(it, color = MaterialTheme.colorScheme.error) }
                message?.let { Text(it, color = MaterialTheme.colorScheme.primary) }
                when (tab) {
                    0 -> {
                        val store = restaurant
                        Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer)) {
                            Column(Modifier.fillMaxWidth().padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                                Text("Bem-vindo, ${session.name}", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
                                Text("Acompanhe sua operação e mantenha sua vitrine atualizada.")
                                Text("Status: ${businessStatusLabel(store?.status)}", fontWeight = FontWeight.Bold)
                                Button(
                                    onClick = { toggleStoreStatus() },
                                    enabled = !busy && store?.status in listOf("ABERTO", "FECHADO"),
                                    modifier = Modifier.fillMaxWidth()
                                ) { Text(if (store?.status == "ABERTO") "Fechar minha doceria" else "Abrir minha doceria") }
                                if (store?.status == "EM_ANALISE") {
                                    Text("Seu cadastro está em análise. A loja aparece na vitrine como aguardando aprovação, mas ainda não pode receber pedidos.", style = MaterialTheme.typography.bodySmall)
                                }
                            }
                        }
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            SellerStatCard("${products.size}", "Produtos", Modifier.weight(1f))
                            SellerStatCard("${orders.size}", "Pedidos", Modifier.weight(1f))
                            SellerStatCard("${orders.count { it.status == "PAGAMENTO_CONFIRMADO" }}", "Novos", Modifier.weight(1f))
                        }
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text("Seus produtos", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold, modifier = Modifier.weight(1f))
                            TextButton(onClick = { tab = 1 }) { Text("Gerenciar") }
                        }
                        if (products.isEmpty()) {
                            SellerInfoCard("Seu cardápio ainda está vazio", "Cadastre seus produtos por aqui para publicar sua vitrine no CandyLand.")
                            Button(onClick = { startProductEditor() }, enabled = categories.isNotEmpty()) { Text("Cadastrar primeiro produto") }
                            if (categories.isEmpty()) Text("Adicione uma categoria na aba Cardápio para começar.", style = MaterialTheme.typography.bodySmall)
                        } else {
                            products.take(5).forEach { product ->
                                Card(Modifier.fillMaxWidth()) {
                                    Row(Modifier.padding(14.dp), verticalAlignment = Alignment.CenterVertically) {
                                        Column(Modifier.weight(1f)) {
                                            Text(product.name, fontWeight = FontWeight.SemiBold)
                                            Text(moneySeller(product.price), color = MaterialTheme.colorScheme.primary)
                                        }
                                        Text(if (product.available) "Disponível" else "Indisponível", style = MaterialTheme.typography.labelSmall)
                                    }
                                }
                            }
                        }
                    }
                    1 -> {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text("Cardápio da doceria", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold, modifier = Modifier.weight(1f))
                            TextButton(onClick = { categoryDialog = true }) { Text("Categorias") }
                        }
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            Button(onClick = { startProductEditor() }, enabled = categories.isNotEmpty() && !busy) { Text("+ Produto") }
                            TextButton(onClick = { scope.launch { runCatching { loadProducts(); loadCategories() }.onFailure { error = it.message } } }) { Text("Atualizar") }
                        }
                        if (categories.isEmpty()) {
                            SellerInfoCard("Nenhuma categoria cadastrada", "Adicione uma categoria para começar a organizar seus produtos.")
                            Button(onClick = { categoryDialog = true }) { Text("Adicionar categoria") }
                        } else {
                            Text("Categorias: ${categories.joinToString(" · ") { it.nome }}", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        }
                        if (products.isEmpty()) SellerInfoCard("Seu cardápio está vazio", "Use + Produto para cadastrar o primeiro item.")
                        products.forEach { product ->
                            Card(Modifier.fillMaxWidth()) {
                                Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(5.dp)) {
                                    Text(product.name, style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
                                    Text(categories.firstOrNull { it.id == product.categoryId }?.nome ?: "Categoria", style = MaterialTheme.typography.labelSmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                                    Text(moneySeller(product.price), color = MaterialTheme.colorScheme.primary, fontWeight = FontWeight.Bold)
                                    Text("Estoque: ${product.stock} · ${if (product.available) "Disponível" else "Indisponível"}", style = MaterialTheme.typography.bodySmall)
                                    TextButton(onClick = { startProductEditor(product) }, enabled = !busy) { Text("Editar produto") }
                                }
                            }
                        }
                    }
                    2 -> {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text("Pedidos da doceria", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold, modifier = Modifier.weight(1f))
                            TextButton(onClick = { scope.launch { runCatching { loadOrders() }.onFailure { error = it.message } } }) { Text("Atualizar") }
                        }
                        if (orders.isEmpty()) SellerInfoCard("Nenhum pedido ainda", "Os pedidos aparecem aqui após a confirmação do pagamento pelo gateway.")
                        orders.forEach { order ->
                            SellerOrderCard(
                                order = order,
                                busy = busy,
                                receiptValue = receiptInputs[order.id].orEmpty(),
                                onReceiptValue = { value -> receiptInputs = receiptInputs + (order.id to value.filter(Char::isDigit).take(6)) },
                                onChangeOrderStatus = { status -> changeOrderStatus(order.id, status) },
                                onChangeDeliveryStatus = { status -> changeDeliveryStatus(order.id, status) },
                                onConfirmReceipt = { validateReceipt(order.id) }
                            )
                        }
                    }
                    else -> {
                        Text("Configuração da doceria", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold)
                        Text("Os dados e o endereço são sincronizados com a mesma configuração usada no portal web.", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        SellerField("Nome fantasia", storeName, { storeName = it })
                        SellerField("Razão social", companyName, { companyName = it })
                        SellerField("Responsável", managerName, { managerName = it })
                        SellerField("Descrição", description, { description = it }, singleLine = false)
                        SellerField("Valor mínimo do pedido (R$)", minimumOrder, { minimumOrder = it }, keyboardType = KeyboardType.Decimal)
                        SellerField("Taxa base (R$)", baseFee, { baseFee = it }, keyboardType = KeyboardType.Decimal)
                        SellerField("Taxa por km (R$)", feePerKm, { feePerKm = it }, keyboardType = KeyboardType.Decimal)
                        SellerField("Raio de entrega (km)", deliveryRadius, { deliveryRadius = it }, keyboardType = KeyboardType.Decimal)
                        SellerField("Horário de funcionamento", openingHours, { openingHours = it })
                        Divider()
                        Text("Endereço comercial", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
                        SellerField("CEP", postalCode, { postalCode = it }, keyboardType = KeyboardType.Number)
                        SellerField("Rua / Avenida", street, { street = it })
                        SellerField("Número", number, { number = it })
                        SellerField("Complemento", complement, { complement = it })
                        SellerField("Bairro", district, { district = it })
                        SellerField("Cidade", city, { city = it })
                        SellerField("Estado (UF)", state, { state = it.uppercase().take(2) })
                        SellerField("Referência", reference, { reference = it })
                        Text("Latitude e longitude são calculadas automaticamente a partir do endereço pelo backend. Não é necessário preencher coordenadas.", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        Button(onClick = { saveConfiguration() }, enabled = !busy, modifier = Modifier.fillMaxWidth()) {
                            Text(if (busy) "Salvando..." else "Salvar configuração")
                        }
                    }
                }
                if (busy) CircularProgressIndicator()
            }
        }
    }
}

@Composable
private fun SellerStatCard(value: String, label: String, modifier: Modifier = Modifier) {
    Card(modifier) {
        Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(3.dp)) {
            Text(value, style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.Bold, color = MaterialTheme.colorScheme.primary)
            Text(label, style = MaterialTheme.typography.labelSmall)
        }
    }
}

@Composable
private fun SellerInfoCard(title: String, body: String) {
    Card(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Text(title, fontWeight = FontWeight.SemiBold)
            Text(body, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
    }
}

@Composable
private fun SellerField(
    label: String,
    value: String,
    onValueChange: (String) -> Unit,
    keyboardType: KeyboardType = KeyboardType.Text,
    singleLine: Boolean = true
) {
    OutlinedTextField(
        value = value,
        onValueChange = onValueChange,
        label = { Text(label) },
        singleLine = singleLine,
        modifier = Modifier.fillMaxWidth(),
        keyboardOptions = KeyboardOptions(keyboardType = keyboardType)
    )
}

@Composable
private fun SellerOrderCard(
    order: OrderDto,
    busy: Boolean,
    receiptValue: String,
    onReceiptValue: (String) -> Unit,
    onChangeOrderStatus: (String) -> Unit,
    onChangeDeliveryStatus: (String) -> Unit,
    onConfirmReceipt: () -> Unit
) {
    val nextOrder = SELLER_NEXT_ORDER_STATUS[order.status]
    val deliveryStatus = order.entrega?.status ?: "NAO_SOLICITADO"
    val nextDelivery = if (order.order_type == "DELIVERY" && order.status == "PRONTO_PARA_ENTREGA") SELLER_DELIVERY_NEXT_STATUS[deliveryStatus] else null
    val canConfirm = (order.order_type == "PICKUP" && order.status == "PRONTO_PARA_ENTREGA") ||
        (order.order_type == "DELIVERY" && order.status == "ENTREGUE")

    Card(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(14.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(order.order_code, style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.primary, fontWeight = FontWeight.Bold)
            Text(order.restaurant_name ?: "Pedido CandyLand", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
            Text("${businessStatusLabel(order.status)} · ${if (order.order_type == "PICKUP") "Retirada" else "Entrega"}")
            Text("Total: ${moneySeller(order.total)}", fontWeight = FontWeight.Bold)
            order.items.forEach { item ->
                Text("${item.quantidade} × ${item.productName ?: "Produto #${item.productId}"}", style = MaterialTheme.typography.bodySmall)
            }
            if (order.status == "PENDENTE_PAGAMENTO") {
                Text("Aguarde a confirmação do gateway antes de iniciar o preparo.", color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodySmall)
            }
            if (nextOrder != null) {
                Button(onClick = { onChangeOrderStatus(nextOrder) }, enabled = !busy, modifier = Modifier.fillMaxWidth()) {
                    Text("Marcar: ${businessStatusLabel(nextOrder)}")
                }
            }
            if (order.status == "PRONTO_PARA_ENTREGA" && order.order_type == "DELIVERY") {
                Text("Logística: ${deliveryStatusLabel(deliveryStatus)}", style = MaterialTheme.typography.bodySmall)
                if (nextDelivery != null) {
                    OutlinedButton(onClick = { onChangeDeliveryStatus(nextDelivery) }, enabled = !busy, modifier = Modifier.fillMaxWidth()) {
                        Text("Atualizar entrega: ${deliveryStatusLabel(nextDelivery)}")
                    }
                }
            }
            if (canConfirm) {
                Divider()
                Text("Confirme o recebimento com o código de 6 dígitos informado pelo cliente.", style = MaterialTheme.typography.bodySmall)
                OutlinedTextField(
                    value = receiptValue,
                    onValueChange = onReceiptValue,
                    label = { Text("Código de recebimento") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number)
                )
                Button(onClick = onConfirmReceipt, enabled = !busy && receiptValue.length == 6, modifier = Modifier.fillMaxWidth()) {
                    Text("Validar código e finalizar")
                }
            }
            if (order.status !in listOf("CANCELADO", "FINALIZADO", "ENTREGUE", "PENDENTE_PAGAMENTO")) {
                TextButton(onClick = { onChangeOrderStatus("CANCELADO") }, enabled = !busy) { Text("Cancelar pedido") }
            }
        }
    }
}

private fun businessStatusLabel(status: String?): String = when (status) {
    "EM_ANALISE" -> "Em análise"
    "ABERTO" -> "Aberta"
    "FECHADO" -> "Fechada"
    "SUSPENSO" -> "Suspensa"
    "PENDENTE_PAGAMENTO" -> "Aguardando pagamento"
    "PAGAMENTO_CONFIRMADO" -> "Pagamento confirmado"
    "RESTAURANTE_RECEBEU" -> "Pedido recebido"
    "RESTAURANTE_ACEITOU" -> "Aceito pela doceria"
    "PROCESSANDO" -> "Em preparo"
    "PRONTO_PARA_ENTREGA" -> "Pronto para entrega / retirada"
    "ENTREGUE" -> "Entregue"
    "FINALIZADO" -> "Finalizado"
    "CANCELADO" -> "Cancelado"
    else -> status ?: "Indisponível"
}

private fun deliveryStatusLabel(status: String): String = when (status) {
    "NAO_SOLICITADO" -> "Não iniciada"
    "PROCURANDO" -> "Procurando entregador"
    "MOTORISTA_ENCONTRADO" -> "Entregador encontrado"
    "MOTORISTA_A_CAMINHO" -> "Entregador a caminho"
    "MOTORISTA_NO_RESTAURANTE" -> "No estabelecimento"
    "PEDIDO_RETIRADO" -> "Pedido retirado"
    "EM_ROTA" -> "Em rota"
    "ENTREGA_CONCLUIDA" -> "Entrega concluída"
    "SEM_MOTORISTA" -> "Sem entregador disponível"
    "CANCELADO" -> "Cancelada"
    else -> status
}

private fun moneySeller(value: Double): String =
    NumberFormat.getCurrencyInstance(Locale("pt", "BR")).format(value)
