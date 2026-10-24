from app.database.database import db
from app.models.restaurant import Restaurante
from app.models.user import Usuario


def email_esta_em_uso(
    email, *, usuario_id_ignorar=None, restaurante_id_ignorar=None
):
    """Verifica se o e-mail pertence a qualquer outra conta do CandyLand.

    A unicidade declarada nos modelos é individual por tabela. Esta verificação
    complementa essa restrição para que um mesmo e-mail não identifique uma conta
    pessoal e uma conta empresarial diferentes.
    """
    email_normalizado = (email or "").strip().lower()
    if not email_normalizado:
        return False

    usuarios = Usuario.query.filter(
        db.func.lower(Usuario.email) == email_normalizado
    )
    if usuario_id_ignorar is not None:
        usuarios = usuarios.filter(Usuario.id != usuario_id_ignorar)
    if usuarios.first() is not None:
        return True

    restaurantes = Restaurante.query.filter(
        db.func.lower(Restaurante.email) == email_normalizado
    )
    if restaurante_id_ignorar is not None:
        restaurantes = restaurantes.filter(Restaurante.id != restaurante_id_ignorar)
    return restaurantes.first() is not None


def telefone_esta_em_uso(
    telefone, *, usuario_id_ignorar=None, restaurante_id_ignorar=None
):
    """Retorna se um telefone normalizado já pertence a outra conta.

    A regra é global entre clientes e restaurantes; os IDs de exclusão são
    usados ao atualizar a própria conta.
    """
    telefone_normalizado = (telefone or "").strip()
    if not telefone_normalizado:
        return False

    usuarios = Usuario.query.filter_by(telefone=telefone_normalizado)
    if usuario_id_ignorar is not None:
        usuarios = usuarios.filter(Usuario.id != usuario_id_ignorar)
    if usuarios.first() is not None:
        return True

    restaurantes = Restaurante.query.filter_by(telefone=telefone_normalizado)
    if restaurante_id_ignorar is not None:
        restaurantes = restaurantes.filter(Restaurante.id != restaurante_id_ignorar)
    return restaurantes.first() is not None
