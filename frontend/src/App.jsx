import { BrowserRouter, Route, Routes } from "react-router-dom";
import { GoogleOAuthProvider } from "@react-oauth/google";

import Login from "./pages/Login";
import Register from "./pages/Register";
import PersonalRegister from "./pages/PersonalRegister";
import BusinessRegister from "./pages/BusinessRegister";
import Home from "./pages/Home";
import BusinessHome from "./pages/BusinessHome";
import Landing from "./pages/Landing";
import Itens from "./pages/Itens";
import ProductForm from "./pages/ProductForm";

import AuthProvider from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import RegistrationGuard from "./components/RegistrationGuard";

function App() {
    const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;

    if (!googleClientId) {
        throw new Error("VITE_GOOGLE_CLIENT_ID não configurado.");
    }

    return (
        <GoogleOAuthProvider clientId={googleClientId}>
            <AuthProvider>
                <BrowserRouter>
                    <Routes>
                        <Route path="/" element={<Landing />} />
                        <Route path="/itens" element={<Itens />} />
                        <Route path="/login" element={<Login />} />

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
                            path="/business"
                            element={
                                <ProtectedRoute tipoConta="BUSINESS">
                                    <BusinessHome />
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
                    </Routes>
                </BrowserRouter>
            </AuthProvider>
        </GoogleOAuthProvider>
    );
}

export default App;