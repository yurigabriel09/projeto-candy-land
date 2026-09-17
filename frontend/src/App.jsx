import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import Login from "./pages/Login";
import Register from "./pages/Register";
import PersonalRegister from "./pages/PersonalRegister";
import BusinessRegister from "./pages/BusinessRegister";
import Home from "./pages/Home";
import BusinessHome from "./pages/BusinessHome";
import ProductForm from "./pages/ProductForm";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/register/personal" element={<PersonalRegister />} />
        <Route path="/register/business" element={<BusinessRegister />} />
        <Route path="/home" element={<Home />} />
        <Route path="/business" element={<BusinessHome />} />
        <Route path="/business/products/new" element={<ProductForm />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;