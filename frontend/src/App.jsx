import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import ListaUsuarios from "./pages/ListaUsuarios";
import UsuarioForm from "./pages/UsuarioForm";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/users" />} />
        <Route path="/users" element={<ListaUsuarios />} />
        <Route path="/users/novo" element={<UsuarioForm />} />
        <Route path="/users/:id/editar" element={<UsuarioForm />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;