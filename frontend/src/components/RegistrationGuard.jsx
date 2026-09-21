import { Navigate, useLocation } from "react-router-dom";

function RegistrationGuard({ children }) {
    const location = useLocation();

    const tentativaId = location.state?.tentativaId;

    if (!tentativaId) {
        return <Navigate to="/login" replace />;
    }

    return children;
}

export default RegistrationGuard;