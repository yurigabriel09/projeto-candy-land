import { BrowserRouter, Route, Routes } from "react-router-dom";
import Login from "./pages/Login";
import Register from "./pages/Register";
import PersonalRegister from "./pages/PersonalRegister";
import BusinessRegister from "./pages/BusinessRegister";
import Home from "./pages/Home";
import BusinessHome from "./pages/BusinessHome";
import Landing from "./pages/Landing";
import Itens from "./pages/Itens";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/itens" element={<Itens />} />

        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/register/personal" element={<PersonalRegister />} />
        <Route path="/register/business" element={<BusinessRegister />} />
        <Route path="/home" element={<Home />} />
        <Route path="/business" element={<BusinessHome />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;