import { useState, useEffect } from "react";
import { getUsers, createUser, updateUser, deleteUser } from "../services/userService";

function Usuarios() {
  const [usuarios, setUsuarios] = useState([]);
  const [nome, setNome] = useState("");
  const [email, setEmail] = useState("");
  const [editandoId, setEditandoId] = useState(null);
  const [erro, setErro] = useState("");

  // Carrega a lista de usuários assim que a página abre
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

  async function handleSubmit(e) {
    e.preventDefault();
    setErro("");

    if (!nome || !email) {
      setErro("Preencha nome e email");
      return;
    }

    try {
      if (editandoId) {
        // Editando um usuário existente
        await updateUser(editandoId, nome, email);
      } else {
        // Criando um novo usuário
        await createUser(nome, email);
      }
      limparFormulario();
      carregarUsuarios();
    } catch (err) {
      setErro("Erro ao salvar usuário");
    }
  }

  function handleEditar(usuario) {
    setEditandoId(usuario.id);
    setNome(usuario.nome);
    setEmail(usuario.email);
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

  function limparFormulario() {
    setNome("");
    setEmail("");
    setEditandoId(null);
  }

  return (
    <div style={{ maxWidth: 600, margin: "40px auto", fontFamily: "sans-serif" }}>
      <h1>Usuários</h1>

      {erro && <p style={{ color: "red" }}>{erro}</p>}

      <form onSubmit={handleSubmit} style={{ marginBottom: 24 }}>
        <input
          type="text"
          placeholder="Nome"
          value={nome}
          onChange={(e) => setNome(e.target.value)}
          style={{ marginRight: 8 }}
        />
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          style={{ marginRight: 8 }}
        />
        <button type="submit">{editandoId ? "Salvar edição" : "Criar usuário"}</button>
        {editandoId && (
          <button type="button" onClick={limparFormulario} style={{ marginLeft: 8 }}>
            Cancelar
          </button>
        )}
      </form>

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
                <button onClick={() => handleEditar(u)}>Editar</button>
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

export default Usuarios;