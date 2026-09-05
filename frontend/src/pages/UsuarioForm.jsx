import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { getUser, createUser, updateUser } from "../services/userService";

function UsuarioForm() {
  const [nome, setNome] = useState("");
  const [email, setEmail] = useState("");
  const [erro, setErro] = useState("");
  const navigate = useNavigate();
  const { id } = useParams(); 
  const editando = Boolean(id);

  useEffect(() => {
    if (editando) {
      carregarUsuario();
    }
  }, [id]);

  async function carregarUsuario() {
    try {
      const usuario = await getUser(id);
      setNome(usuario.nome);
      setEmail(usuario.email);
    } catch (err) {
      setErro("Erro ao carregar usuário");
    }
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setErro("");

    if (!nome || !email) {
      setErro("Preencha nome e email");
      return;
    }

    try {
      if (editando) {
        await updateUser(id, nome, email);
      } else {
        await createUser(nome, email);
      }
      navigate("/users");
    } catch (err) {
      setErro("Erro ao salvar usuário");
    }
  }

  return (
    <div style={{ maxWidth: 400, margin: "40px auto", fontFamily: "sans-serif" }}>
      <h1>{editando ? "Editar usuário" : "Novo usuário"}</h1>

      {erro && <p style={{ color: "red" }}>{erro}</p>}

      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: 12 }}>
          <input
            type="text"
            placeholder="Nome"
            value={nome}
            onChange={(e) => setNome(e.target.value)}
            style={{ width: "100%", padding: 8 }}
          />
        </div>
        <div style={{ marginBottom: 12 }}>
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            style={{ width: "100%", padding: 8 }}
          />
        </div>
        <button type="submit">{editando ? "Salvar edição" : "Criar usuário"}</button>
        <button type="button" onClick={() => navigate("/users")} style={{ marginLeft: 8 }}>
          Cancelar
        </button>
      </form>
    </div>
  );
}

export default UsuarioForm;