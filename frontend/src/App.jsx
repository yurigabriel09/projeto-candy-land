import { BrowserRouter, Route, Routes } from "react-router-dom";
import { GoogleOAuthProvider } from "@react-oauth/google";
import { CartProvider } from "./context/CartContext";

import Login from "./pages/Login";
import Register from "./pages/Register";
import PersonalRegister from "./pages/PersonalRegister";
import BusinessRegister from "./pages/BusinessRegister";
import Home from "./pages/Home";
import Restaurant from "./pages/Restaurant";
import BusinessHome from "./pages/BusinessHome";
import Landing from "./pages/Landing";
import Itens from "./pages/Itens";
import ProductForm from "./pages/ProductForm";
import CategoryManager from "./pages/CategoryManager";
import Cardapio from "./pages/Cardapio";
import PartnerLanding from "./pages/PartnerLanding";
import RestaurantConfiguration from "./pages/RestaurantConfiguration";
import Cart from "./pages/Cart";
import CheckoutResult from "./pages/CheckoutResult";
import OrderTracking from "./pages/OrderTracking";
import BusinessOrders from "./pages/BusinessOrders";
import BusinessFinance from "./pages/BusinessFinance";
import BusinessReviews from "./pages/BusinessReviews";

import AuthProvider from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import RegistrationGuard from "./components/RegistrationGuard";
import DadosPessoais from "./pages/DadosPessoais";
import PendingPayments from "./pages/PendingPayments";

function App() {
    const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;

    if (!googleClientId) {
        throw new Error("VITE_GOOGLE_CLIENT_ID não configurado.");
    }

    return (
        <GoogleOAuthProvider clientId={googleClientId}>
            <AuthProvider>
                <CartProvider>
                    <BrowserRouter>
                        <Routes>
                            <Route path="/" element={<Landing />} />
                            <Route path="/itens" element={<Itens />} />
                            <Route
                                path="/restaurantes/:restauranteId"
                                element={
                                    <ProtectedRoute tipoConta="PERSONAL">
                                        <Restaurant />
                                    </ProtectedRoute>
                                }
                            />

                            <Route path="/parceiros" element={<PartnerLanding />} />
                            <Route path="/parceiros/login" element={<Login audiencia="BUSINESS" />} />
                            <Route path="/login" element={<Login audiencia="PERSONAL" />} />

                            <Route
                                path="/register"
                                element={
                                    <RegistrationGuard>
                                        <Register />
                                    </RegistrationGuard>
                                }
                            />

                            <Route
                                path="/register/personal"
                                element={
                                    <RegistrationGuard>
                                        <PersonalRegister />
                                    </RegistrationGuard>
                                }
                            />

                            <Route
                                path="/register/business"
                                element={
                                    <RegistrationGuard>
                                        <BusinessRegister />
                                    </RegistrationGuard>
                                }
                            />

                            <Route
                                path="/home"
                                element={
                                    <ProtectedRoute tipoConta="PERSONAL">
                                        <Home />
                                    </ProtectedRoute>
                                }
                            />

                            <Route
                                path="/minha-conta/dados-pessoais"
                                element={
                                    <ProtectedRoute tipoConta="PERSONAL">
                                        <DadosPessoais />
                                    </ProtectedRoute>
                                }
/>

                            <Route
                                path="/minha-conta/pagamentos-pendentes"
                                element={
                                    <ProtectedRoute tipoConta="PERSONAL">
                                        <PendingPayments />
                                    </ProtectedRoute>
                                }
                            />

                            <Route
                                path="/business"
                                element={
                                    <ProtectedRoute tipoConta="BUSINESS">
                                        <BusinessHome />
                                    </ProtectedRoute>
                                }
                            />

                            <Route
                                path="/business/cardapio"
                                element={
                                    <ProtectedRoute tipoConta="BUSINESS">
                                        <Cardapio />
                                    </ProtectedRoute>
                                }
                            />

                            <Route
                                path="/business/pedidos"
                                element={
                                    <ProtectedRoute tipoConta="BUSINESS">
                                        <BusinessOrders />
                                    </ProtectedRoute>
                                }
                            />

                            <Route
                                path="/business/financeiro"
                                element={
                                    <ProtectedRoute tipoConta="BUSINESS">
                                        <BusinessFinance />
                                    </ProtectedRoute>
                                }
                            />

                            <Route
                                path="/business/avaliacoes"
                                element={
                                    <ProtectedRoute tipoConta="BUSINESS">
                                        <BusinessReviews />
                                    </ProtectedRoute>
                                }
                            />

                            <Route
                                path="/business/products/new"
                                element={
                                    <ProtectedRoute tipoConta="BUSINESS">
                                        <ProductForm />
                                    </ProtectedRoute>
                                }
                            />

                            <Route
                                path="/business/products/:produtoId/edit"
                                element={
                                    <ProtectedRoute tipoConta="BUSINESS">
                                        <ProductForm />
                                    </ProtectedRoute>
                                }
                            />

                            <Route
                                path="/business/configuracao"
                                element={
                                    <ProtectedRoute tipoConta="BUSINESS">
                                        <RestaurantConfiguration />
                                    </ProtectedRoute>
                                }
                            />

                            <Route
                                path="/business/categories"
                                element={
                                    <ProtectedRoute tipoConta="BUSINESS">
                                        <CategoryManager />
                                    </ProtectedRoute>
                                }
                            />

                            <Route
                                path="/cart"
                                element={
                                    <ProtectedRoute tipoConta="PERSONAL">
                                        <Cart />
                                    </ProtectedRoute>
                                }
                            />

                            <Route
                                path="/checkout/resultado"
                                element={
                                    <ProtectedRoute tipoConta="PERSONAL">
                                        <CheckoutResult />
                                    </ProtectedRoute>
                                }
                            />

                            <Route
                                path="/pedidos/:orderId/acompanhar"
                                element={
                                    <ProtectedRoute tipoConta="PERSONAL">
                                        <OrderTracking />
                                    </ProtectedRoute>
                                }
                            />
                        </Routes>
                    </BrowserRouter>
                </CartProvider>
            </AuthProvider>
        </GoogleOAuthProvider>
    );
}

export default App;
