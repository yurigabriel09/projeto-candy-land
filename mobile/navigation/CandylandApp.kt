package com.candyland.app.navigation

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Home
import androidx.compose.material.icons.filled.Person
import androidx.compose.material.icons.filled.ShoppingCart
import androidx.compose.material3.Badge
import androidx.compose.material3.BadgedBox
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.NavigationBarItemDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.unit.dp
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavGraph.Companion.findStartDestination
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.candyland.app.ui.CartViewModel
import com.candyland.app.ui.PaymentViewModel
import com.candyland.app.ui.cart.CartScreen
import com.candyland.app.ui.checkout.CheckoutScreen
import com.candyland.app.ui.home.HomeScreen
import com.candyland.app.ui.profile.ProfileScreen
import com.candyland.app.ui.theme.CandyColors

object Routes {
    const val HOME = "home"
    const val CART = "cart"
    const val CHECKOUT = "checkout"
    const val PROFILE = "profile"
}

private data class BottomTab(val route: String, val label: String, val icon: ImageVector)

private val tabs = listOf(
    BottomTab(Routes.HOME, "Início", Icons.Default.Home),
    BottomTab(Routes.CART, "Carrinho", Icons.Default.ShoppingCart),
    BottomTab(Routes.PROFILE, "Perfil", Icons.Default.Person)
)

@Composable
fun CandylandApp(
    navController: NavHostController = rememberNavController(),
    cartViewModel: CartViewModel = viewModel(),
    paymentViewModel: PaymentViewModel = viewModel()
) {
    val cart by cartViewModel.state.collectAsState()
    val cards by paymentViewModel.cards.collectAsState()

    val currentRoute = navController.currentBackStackEntryAsState().value?.destination?.route
    val showBottomBar = currentRoute in tabs.map { it.route }

    Scaffold(
        containerColor = CandyColors.Cream,
        bottomBar = {
            if (showBottomBar) {
                NavigationBar(containerColor = Color.White, tonalElevation = 4.dp) {
                    tabs.forEach { tab ->
                        NavigationBarItem(
                            selected = currentRoute == tab.route,
                            onClick = {
                                navController.navigate(tab.route) {
                                    popUpTo(navController.graph.findStartDestination().id) { saveState = true }
                                    launchSingleTop = true
                                    restoreState = true
                                }
                            },
                            icon = {
                                if (tab.route == Routes.CART && cart.itemCount > 0) {
                                    BadgedBox(badge = {
                                        Badge(containerColor = CandyColors.Pink) { Text("${cart.itemCount}") }
                                    }) { Icon(tab.icon, tab.label) }
                                } else {
                                    Icon(tab.icon, tab.label)
                                }
                            },
                            label = { Text(tab.label) },
                            colors = NavigationBarItemDefaults.colors(
                                selectedIconColor = Color.White,
                                selectedTextColor = CandyColors.Pink,
                                indicatorColor = CandyColors.Pink,
                                unselectedIconColor = CandyColors.Muted,
                                unselectedTextColor = CandyColors.Muted
                            )
                        )
                    }
                }
            }
        }
    ) { padding ->
        NavHost(
            navController = navController,
            startDestination = Routes.HOME,
            modifier = Modifier.padding(padding)
        ) {
            composable(Routes.HOME) {
                HomeScreen(onAddToCart = cartViewModel::add)
            }

            composable(Routes.CART) {
                CartScreen(
                    state = cart,
                    onIncrement = cartViewModel::increment,
                    onDecrement = cartViewModel::decrement,
                    onDeliveryChange = cartViewModel::setDelivery,
                    onCouponChange = cartViewModel::onCouponChange,
                    onApplyCoupon = cartViewModel::applyCoupon,
                    onAddItems = { navController.navigate(Routes.HOME) { launchSingleTop = true } },
                    onCheckout = { navController.navigate(Routes.CHECKOUT) }
                )
            }

            composable(Routes.CHECKOUT) {
                CheckoutScreen(
                    cart = cart,
                    cards = cards,
                    onAddCard = paymentViewModel::addCard,
                    onSetPrimary = paymentViewModel::setPrimary,
                    onBack = { navController.popBackStack() },
                    onOrderConfirmed = {
                        cartViewModel.clear()
                        navController.navigate(Routes.HOME) {
                            popUpTo(Routes.HOME) { inclusive = true }
                        }
                    }
                )
            }

            composable(Routes.PROFILE) {
                ProfileScreen(
                    cards = cards,
                    onAddCard = paymentViewModel::addCard,
                    onSetPrimary = paymentViewModel::setPrimary,
                    onLogout = { /* TODO: limpar sessão e ir para a tela de login */ }
                )
            }
        }
    }
}
