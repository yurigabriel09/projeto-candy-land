import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import Login from "./pages/Login";
import Register from "./pages/Register";
import PersonalRegister from "./pages/PersonalRegister";
import BusinessRegister from "./pages/BusinessRegister";
import Home from "./pages/Home";
import BusinessHome from "./pages/BusinessHome";
import AuthProvider from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";

function App() {
    return (
        <AuthProvider>
            <BrowserRouter>
                <Routes>
                    <Route path="/" element={<Navigate to="/login" replace />} />
                    <Route path="/login" element={<Login />} />
                    <Route path="/register" element={<Register />} />
                    <Route path="/register/personal" element={<PersonalRegister />} />
                    <Route path="/register/business" element={<BusinessRegister />} />

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
                </Routes>
            </BrowserRouter>
        </AuthProvider>
    );
}

export default App;