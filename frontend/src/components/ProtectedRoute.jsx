import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

function ProtectedRoute({ children, tipoConta }) {
    const { dadosAutenticacao, autenticado } = useAuth();

    if (!autenticado) {
        return <Navigate to="/login" replace />;
    }

    if (tipoConta && dadosAutenticacao.tipo_conta !== tipoConta) {
        const rotaCorreta = dadosAutenticacao.tipo_conta === "BUSINESS"
            ? "/business"
            : "/home";

        return <Navigate to={rotaCorreta} replace />;
    }

    return children;
}

export default ProtectedRoute;