import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import Login from "./pages/Login";
import Register from "./pages/Register";
import PersonalRegister from "./pages/PersonalRegister";
import BusinessRegister from "./pages/BusinessRegister";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/login" replace />} />

        <Route path="/login" element={<Login />} />

        <Route path="/register" element={<Register />} />

        <Route
          path="/register/personal"
          element={<PersonalRegister />}
        />

        <Route
          path="/register/business"
          element={<BusinessRegister />}
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;