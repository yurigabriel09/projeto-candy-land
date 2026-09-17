import { Link, useNavigate } from "react-router-dom";
import { getSessao, encerrarSessao } from "../services/authService";

/**
 * Cabeçalho usado na Home pública, na Home do cliente logado e na consulta
 * de itens. As telas de login/cadastro continuam com o card centralizado
 * sem cabeçalho, como já estava.
 */
function Header() {
  const sessao = getSessao();
  const navigate = useNavigate();

  function handleSair() {
    encerrarSessao();
    navigate("/");
  }

  const logado = sessao && sessao.tipo === "PERSONAL";

  return (
    <header className="site-header">
      <div className="site-header-inner">
        <Link to={logado ? "/home" : "/"} className="site-logo">
          <span className="site-logo-icone">🍭</span>
          <span className="site-logo-texto">Candyland</span>
        </Link>

        <nav className="site-nav">
          <Link to="/itens">Doces</Link>

          {logado ? (
            <>
              <span className="site-saudacao">Olá, {sessao.nome_completo.split(" ")[0]}</span>
              <button onClick={handleSair} className="btn-contorno">
                Sair
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="btn-contorno">
                Entrar
              </Link>
              <Link to="/register" className="btn-principal">
                Cadastrar
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}

export default Header;