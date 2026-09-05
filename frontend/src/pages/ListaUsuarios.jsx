import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { getUsers, deleteUser } from "../services/userService";

function ListaUsuarios() {
  const [usuarios, setUsuarios] = useState([]);
  const [erro, setErro] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    carregarUsuarios();
  }, []);

  async function carregarUsuarios() {
    try {
      const dados = await getUsers();
      setUsuarios(dados);
    } catch (err) {
      setErro("Erro ao carregar usuários");
    }
  }

  async function handleDeletar(id) {
    if (!confirm("Tem certeza que deseja deletar este usuário?")) return;
    try {
      await deleteUser(id);
      carregarUsuarios();
    } catch (err) {
      setErro("Erro ao deletar usuário");
    }
  }

  return (
    <div style={{ maxWidth: 600, margin: "40px auto", fontFamily: "sans-serif" }}>
      <h1>Usuários</h1>

      {erro && <p style={{ color: "red" }}>{erro}</p>}

      <button onClick={() => navigate("/users/novo")} style={{ marginBottom: 16 }}>
        Novo usuário
      </button>

      <table border="1" cellPadding="8" style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            <th>ID</th>
            <th>Nome</th>
            <th>Email</th>
            <th>Ativo</th>
            <th>Ações</th>
          </tr>
        </thead>
        <tbody>
          {usuarios.map((u) => (
            <tr key={u.id}>
              <td>{u.id}</td>
              <td>{u.nome}</td>
              <td>{u.email}</td>
              <td>{u.ativo ? "Sim" : "Não"}</td>
              <td>
                <button onClick={() => navigate(`/users/${u.id}/editar`)}>Editar</button>
                <button onClick={() => handleDeletar(u.id)} style={{ marginLeft: 8 }}>
                  Deletar
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default ListaUsuarios;