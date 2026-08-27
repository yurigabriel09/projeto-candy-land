import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import ListaUsuarios from "./pages/ListaUsuarios";
import UsuarioForm from "./pages/UsuarioForm";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/usuarios" />} />
        <Route path="/usuarios" element={<ListaUsuarios />} />
        <Route path="/usuarios/novo" element={<UsuarioForm />} />
        <Route path="/usuarios/:id/editar" element={<UsuarioForm />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;