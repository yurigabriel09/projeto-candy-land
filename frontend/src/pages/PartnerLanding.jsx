import { Link } from "react-router-dom";

function PartnerLanding() {
    return (
        <main>
            <h1>CandyLand Parceiros</h1>
            <p>Área exclusiva para restaurantes e confeitarias parceiras.</p>

            <nav>
                <Link to="/parceiros/login">Entrar</Link>
                {" | "}
                <Link to="/parceiros/login">Cadastrar</Link>
            </nav>

            <p>
                É cliente? <Link to="/">Voltar para a área do cliente</Link>
            </p>
        </main>
    );
}

export default PartnerLanding;